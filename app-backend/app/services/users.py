"""User profile, settings and personal bet ledger (raw SQL on the shared engine)."""
import datetime
import secrets

import numpy as np
import pandas as pd
from sqlalchemy import text


RISK_PRESETS = {"prudent": 0.25, "balanced": 0.5, "aggressive": 1.0}  # -> Kelly fraction
START_BANKROLL = 1000.0


def upsert_user(claims: dict) -> int:
    """Create or update the user from Google claims, ensure settings row, return user_id."""
    from app._config import engine
    with engine.begin() as conn:
        uid = conn.execute(text("""
            INSERT INTO users (google_sub, email, name, avatar_url)
            VALUES (:sub, :email, :name, :pic)
            ON CONFLICT (google_sub) DO UPDATE SET email = EXCLUDED.email, name = EXCLUDED.name,
                avatar_url = EXCLUDED.avatar_url
            RETURNING user_id
        """), {"sub": claims["sub"], "email": claims.get("email"), "name": claims.get("name"),
               "pic": claims.get("picture")}).scalar_one()
        conn.execute(text("INSERT INTO user_settings (user_id) VALUES (:uid) ON CONFLICT DO NOTHING"), {"uid": uid})
    return uid


def get_profile(uid: int) -> dict | None:
    from app._config import engine
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT u.user_id, u.email, u.name, u.avatar_url,
                   s.bankroll, s.risk_preset, s.books, s.min_edge, s.alerts_enabled,
                   (s.telegram_chat_id IS NOT NULL) AS telegram_linked
            FROM users u JOIN user_settings s USING (user_id) WHERE u.user_id = :uid
        """), {"uid": uid}).mappings().first()
    if row is None:
        return None
    d = dict(row)
    d["books"] = list(d["books"] or [])
    return d


def update_settings(uid: int, *, bankroll=None, risk_preset=None, books=None, min_edge=None, alerts_enabled=None) -> dict:
    from app._config import engine
    sets, params = [], {"uid": uid}
    if bankroll is not None:
        sets.append("bankroll = :bankroll"); params["bankroll"] = max(0.0, float(bankroll))
    if risk_preset is not None:
        if risk_preset not in RISK_PRESETS:
            raise ValueError("invalid risk_preset")
        sets.append("risk_preset = :risk"); params["risk"] = risk_preset
    if books is not None:
        sets.append("books = :books"); params["books"] = list(books)
    if min_edge is not None:
        sets.append("min_edge = :min_edge"); params["min_edge"] = float(min_edge)
    if alerts_enabled is not None:
        sets.append("alerts_enabled = :alerts"); params["alerts"] = bool(alerts_enabled)
    if sets:
        sets.append("updated_at = CURRENT_TIMESTAMP")
        with engine.begin() as conn:
            conn.execute(text(f"UPDATE user_settings SET {', '.join(sets)} WHERE user_id = :uid"), params)
    return get_profile(uid)


def confirm_bet(uid: int, match_id: str, side: str, recommended_price=None, placed_price=None, stake=None) -> None:
    """Record (or update) that the user placed a recommended bet."""
    from app._config import engine
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO user_bets (user_id, match_id, side, recommended_price, placed_price, stake, status)
            VALUES (:uid, :mid, :side, :rec, :placed, :stake, 'placed')
            ON CONFLICT (user_id, match_id, side) DO UPDATE SET
                recommended_price = EXCLUDED.recommended_price, placed_price = EXCLUDED.placed_price,
                stake = EXCLUDED.stake
        """), {"uid": uid, "mid": match_id, "side": side, "rec": recommended_price,
               "placed": placed_price, "stake": stake})


def remove_bet(uid: int, match_id: str, side: str) -> None:
    from app._config import engine
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM user_bets WHERE user_id = :uid AND match_id = :mid AND side = :side"),
                     {"uid": uid, "mid": match_id, "side": side})


def telegram_link_code(uid: int) -> str:
    """Generate (and store) a one-time code the user sends to the bot as /start <code>."""
    from app._config import engine
    code = secrets.token_urlsafe(9)
    with engine.begin() as conn:
        conn.execute(text("UPDATE user_settings SET telegram_link_code = :c WHERE user_id = :uid"),
                     {"c": code, "uid": uid})
    return code


def delete_account(uid: int) -> None:
    from app._config import engine
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE user_id = :uid"), {"uid": uid})  # cascades to settings + bets


# --- personal ledger + stats (settled bets are scored by the user's confirmed outcome) ---
LEDGER_SQL = """
SELECT b.match_id, b.side, b.recommended_price, b.placed_price, b.stake, b.status, b.settled_gain, b.created_at,
       f.league, f.home_g, f.away_g, f.notes,
       o.home_team, o.away_team,
       (o.date_match + COALESCE(o.time_match, time '00:00')) AS commence_time
FROM user_bets b
LEFT JOIN optim_results o ON o.match_id = b.match_id AND o.optim_label = 'value_pinnacle'
LEFT JOIN fbref_results f ON f.game = o.game
WHERE b.user_id = :uid
"""


def ledger_records(df: pd.DataFrame) -> list[dict]:
    """JSON-safe rows (NaN -> None, timestamps -> ISO strings) for the API."""
    out = []
    for r in df.to_dict(orient="records"):
        clean = {}
        for k, v in r.items():
            if isinstance(v, (pd.Timestamp, datetime.datetime, datetime.date)):
                clean[k] = v.isoformat()
            else:
                try:
                    clean[k] = None if pd.isna(v) else v
                except (TypeError, ValueError):
                    clean[k] = v
        out.append(clean)
    return out


def ledger(uid: int) -> pd.DataFrame:
    from app._config import engine
    with engine.connect() as conn:
        df = pd.read_sql(text(LEDGER_SQL), conn, params={"uid": uid})
    return df.drop_duplicates(subset=["match_id", "side"])


def personal_stats(uid: int) -> dict:
    """Bankroll curve and headline numbers from the user's settled bets (gains in euros)."""
    return stats_from_ledger(ledger(uid))


def stats_from_ledger(df: pd.DataFrame) -> dict:
    """Pure stats computation, separated from I/O for testing."""
    settled = df[df["status"].isin(["won", "lost"]) & df["settled_gain"].notna()].copy()
    out = {"bets": int(len(df)), "settled": int(len(settled))}
    if settled.empty:
        out.update({"bankroll_delta": 0.0, "roi": None, "win_rate": None, "equity": []})
        return out
    settled = settled.sort_values("created_at")
    gain = settled["settled_gain"].to_numpy(float)
    stake = settled["stake"].fillna(0).to_numpy(float)
    equity, running = [], 0.0
    for g, t in zip(gain, settled["created_at"]):
        running += g
        equity.append({"t": pd.Timestamp(t).isoformat(), "delta": round(running, 2)})
    out.update({
        "bankroll_delta": round(float(gain.sum()), 2),
        "roi": float(gain.sum() / stake.sum()) if stake.sum() > 0 else None,
        "win_rate": float((settled["status"] == "won").mean()),
        "equity": equity,
    })
    return out
