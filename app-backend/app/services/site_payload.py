"""Public site payload: value bets, their results and track-record statistics.

Pure functions (no database) so they can be unit tested; app/services/site.py feeds them.
Stakes are fractions of the bankroll at bet time and gains compound per kickoff day,
like the /performance/gains endpoint.
"""
import datetime

import numpy as np
import pandas as pd

from optibet_lib.betting import devig

SIDES = ("home", "draw", "away")
START_BANKROLL = 1000.0
ODDS_BUCKETS = [(1.0, 2.0, "< 2.00"), (2.0, 2.5, "2.00 – 2.49"), (2.5, 3.0, "2.50 – 2.99"), (3.0, 99.0, "≥ 3.00")]
LEAGUES = {
    "ENG-Premier League": "Premier League", "ESP-La Liga": "LaLiga", "ITA-Serie A": "Serie A",
    "GER-Bundesliga": "Bundesliga", "FRA-Ligue 1": "Ligue 1", "UEFA Champions League": "Champions League",
    "soccer_epl": "Premier League", "soccer_spain_la_liga": "LaLiga", "soccer_italy_serie_a": "Serie A",
    "soccer_germany_bundesliga": "Bundesliga", "soccer_france_ligue_one": "Ligue 1",
    "soccer_uefa_champs_league": "Champions League",
}
VOID_NOTES = ("Extra Time", "Cancelled", "Abandoned", "Awarded")


def _none_if_nan(v):
    return None if v is None or (isinstance(v, float) and not np.isfinite(v)) else v


def closing_fair(closing: pd.DataFrame) -> pd.DataFrame:
    """Pinnacle last pre-kickoff prices (match_id, side, price) -> Shin fair probabilities per match_id."""
    if closing.empty:
        return pd.DataFrame(columns=list(SIDES))
    wide = closing.pivot_table(index="match_id", columns="side", values="price", aggfunc="last")
    wide = wide.reindex(columns=list(SIDES)).dropna()
    wide = wide[(wide > 1).all(axis=1)]
    if wide.empty:
        return pd.DataFrame(columns=list(SIDES))
    return pd.DataFrame(devig(wide.to_numpy(float)), index=wide.index, columns=list(SIDES))


def bet_table(bets: pd.DataFrame, closing: pd.DataFrame, now: datetime.datetime) -> pd.DataFrame:
    """One row per recommended bet with side, price, stake, status and result."""
    if bets.empty:
        return pd.DataFrame()
    stakes = bets[[f"f_{s}" for s in SIDES]].fillna(0).to_numpy(float)
    side_idx = stakes.argmax(axis=1)
    rows = np.arange(len(bets))
    price = bets[[f"odds_{s}" for s in SIDES]].to_numpy(float)[rows, side_idx]
    fair = bets[["prob_home_win", "prob_draw", "prob_away_win"]].to_numpy(float)[rows, side_idx]
    book = bets[[f"bookmaker_{s}_key" for s in SIDES]].to_numpy(object)[rows, side_idx]
    t = pd.DataFrame({
        "match_id": bets["match_id"].to_numpy(), "game": bets["game"].to_numpy(),
        "kickoff": pd.to_datetime(bets["date_match"].astype(str) + " " + bets["time_match"].astype(str)),
        "home": bets["home_team"].to_numpy(), "away": bets["away_team"].to_numpy(),
        "league": [LEAGUES.get(l) or LEAGUES.get(k) or (l or k or "") for l, k in zip(bets["league"], bets["sport_key"])],
        "side": [SIDES[i] for i in side_idx], "price": price, "fair_price": 1 / fair,
        "edge": fair * price - 1, "stake": stakes[rows, side_idx], "book": book,
        "home_g": bets["home_g"].to_numpy(), "away_g": bets["away_g"].to_numpy(),
        "notes": bets["notes"].fillna("").to_numpy(),
    })
    fair_close = closing_fair(closing)
    p_close = [fair_close.at[m, s] if m in fair_close.index else np.nan for m, s in zip(t["match_id"], t["side"])]
    t["clv"] = t["price"] * np.array(p_close, dtype=float) - 1

    scored = t["home_g"].notna() & t["away_g"].notna()
    void = t["notes"].str.contains("|".join(VOID_NOTES), case=False)
    outcome = np.select([t["home_g"] > t["away_g"], t["home_g"] < t["away_g"]], ["home", "away"], "draw")
    won = scored & ~void & (outcome == t["side"])
    t["status"] = np.select(
        [void, scored & won, scored, t["kickoff"] > now],
        ["void", "won", "lost", "upcoming"], "pending")
    t["gain"] = np.select([t["status"] == "won", t["status"] == "lost"], [t["stake"] * (t["price"] - 1), -t["stake"]], 0.0)
    return t.sort_values("kickoff").reset_index(drop=True)


def equity_curve(settled: pd.DataFrame) -> pd.DataFrame:
    """Bankroll per kickoff day, compounding the day's gains (stakes are bankroll fractions)."""
    daily = settled.groupby(settled["kickoff"].dt.normalize())["gain"].sum()
    bankroll = START_BANKROLL * np.cumprod(1 + daily.to_numpy())
    start = pd.DataFrame({"day": [daily.index[0] - pd.Timedelta(days=1)], "bankroll": [START_BANKROLL], "daily": [0.0]})
    return pd.concat([start, pd.DataFrame({"day": daily.index, "bankroll": bankroll, "daily": daily.to_numpy()})],
                     ignore_index=True)


def group_stats(settled: pd.DataFrame, key: pd.Series) -> list[dict]:
    out = []
    for name, g in settled.groupby(key, sort=False):
        flat = np.where(g["status"] == "won", g["price"] - 1, -1.0)
        out.append({"name": str(name), "bets": int(len(g)), "win_rate": float((g["status"] == "won").mean()),
                    "roi": float(flat.mean()), "clv": _none_if_nan(float(g["clv"].mean())),
                    "profit": float(g["gain"].sum() * START_BANKROLL)})
    return out


def build_payload(bets: pd.DataFrame, closing: pd.DataFrame, now: datetime.datetime) -> dict:
    t = bet_table(bets, closing, now)
    payload = {"generated_at": now.isoformat(timespec="seconds"), "start_bankroll": START_BANKROLL,
               "today": [], "history": [], "equity": [], "kpis": None, "monthly": [], "by_league": [], "by_odds": [],
               "clv_series": []}
    if t.empty:
        return payload

    def record(r):
        return {"kickoff": r.kickoff.isoformat(), "home": r.home, "away": r.away, "league": r.league, "side": r.side,
                "price": round(float(r.price), 2), "fair_price": round(float(r.fair_price), 3),
                "edge": float(r.edge), "stake": float(r.stake), "book": r.book, "status": r.status,
                "score": None if pd.isna(r.home_g) else f"{int(r.home_g)}-{int(r.away_g)}",
                "gain": float(r.gain), "clv": _none_if_nan(float(r.clv))}

    open_bets = t[t["status"].isin(["upcoming", "pending"])]
    payload["today"] = [record(r) for r in open_bets.itertuples()]
    settled = t[t["status"].isin(["won", "lost"])]
    payload["history"] = [record(r) for r in t[t["status"].isin(["won", "lost", "void"])].iloc[::-1].itertuples()]
    if settled.empty:
        return payload

    eq = equity_curve(settled)
    peak = np.maximum.accumulate(eq["bankroll"].to_numpy())
    dd = eq["bankroll"].to_numpy() / peak - 1
    flat = np.where(settled["status"] == "won", settled["price"] - 1, -1.0)
    payload["equity"] = [{"day": d.date().isoformat(), "bankroll": float(b)} for d, b in zip(eq["day"], eq["bankroll"])]
    payload["kpis"] = {
        "bankroll": float(eq["bankroll"].iloc[-1]),
        "return": float(eq["bankroll"].iloc[-1] / START_BANKROLL - 1),
        "bets": int(len(settled)), "win_rate": float((settled["status"] == "won").mean()),
        "roi": float(flat.mean()), "avg_price": float(settled["price"].mean()),
        "avg_stake": float(settled["stake"].mean()), "avg_edge": float(settled["edge"].mean()),
        "clv": _none_if_nan(float(settled["clv"].mean())), "clv_coverage": float(settled["clv"].notna().mean()),
        "max_drawdown": float(dd.min()), "max_drawdown_day": eq["day"].iloc[int(dd.argmin())].date().isoformat(),
        "since": settled["kickoff"].min().date().isoformat(),
    }
    month = eq.iloc[1:].groupby(eq["day"].iloc[1:].dt.to_period("M"))["daily"].apply(lambda d: float(np.prod(1 + d) - 1))
    payload["monthly"] = [{"month": str(m), "return": r} for m, r in month.items()]
    payload["by_league"] = sorted(group_stats(settled, settled["league"]), key=lambda x: -x["bets"])
    bucket = pd.Series([next(n for lo, hi, n in ODDS_BUCKETS if lo <= p < hi) for p in settled["price"]], index=settled.index)
    order = {n: i for i, (_, _, n) in enumerate(ODDS_BUCKETS)}
    payload["by_odds"] = sorted(group_stats(settled, bucket), key=lambda x: order[x["name"]])
    clv = settled.dropna(subset=["clv"])
    if len(clv):
        rolling = clv["clv"].rolling(30, min_periods=10).mean()
        payload["clv_series"] = [{"day": k.date().isoformat(), "clv": float(c), "rolling": _none_if_nan(float(r))}
                                 for k, c, r in zip(clv["kickoff"], clv["clv"], rolling)]
    return payload
