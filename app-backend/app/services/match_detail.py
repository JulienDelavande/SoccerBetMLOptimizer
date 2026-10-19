"""Detail of one recommended bet: Pinnacle line movement, every bookmaker's price at bet
time, team form and head-to-head. Pure functions; app/services/site.py runs the queries."""
import datetime

import numpy as np
import pandas as pd

from app.services.site_payload import SIDES, bet_table, closing_fair
from app.services.team_charts import elo_series, xg_series

ELO_YEARS = 2

FORM_GAMES = 5


def line_series(odds: pd.DataFrame) -> dict[str, list[dict]]:
    """Price per side over time (batches where the price changed), from (datetime_insert, side, price) rows."""
    out = {}
    for side in SIDES:
        s = odds[odds["side"] == side].sort_values("datetime_insert")
        s = s[s["price"].ne(s["price"].shift())]
        out[side] = [{"t": t.isoformat(timespec="seconds"), "price": float(p)} for t, p in zip(s["datetime_insert"], s["price"])]
    return out


def books_table(books: pd.DataFrame, bet_book: str) -> list[dict]:
    """Every bookmaker's 1X2 prices at bet time, lowest margin first; `ours` marks the bet's bookmaker."""
    if books.empty:
        return []
    wide = books.pivot_table(index=["bookmaker_key", "bookmaker_title"], columns="side", values="price", aggfunc="last")
    wide = wide.reindex(columns=list(SIDES)).dropna().reset_index()
    wide["margin"] = (1 / wide[list(SIDES)]).sum(axis=1) - 1
    wide = wide.sort_values("margin")
    return [{"key": r.bookmaker_key, "title": r.bookmaker_title, "home": float(r.home), "draw": float(r.draw),
             "away": float(r.away), "margin": float(r.margin), "ours": r.bookmaker_key == bet_book}
            for r in wide.itertuples()]


def team_form(matches: pd.DataFrame, team: str, before: datetime.date) -> list[dict]:
    """Last FORM_GAMES played matches of `team` before `before`, newest first, from the team's point of view."""
    m = matches[((matches["home"] == team) | (matches["away"] == team)) & (matches["date"] < before)
                & matches["home_g"].notna()].sort_values("date", ascending=False).head(FORM_GAMES)
    out = []
    for r in m.itertuples():
        home = r.home == team
        gf, ga = (r.home_g, r.away_g) if home else (r.away_g, r.home_g)
        out.append({"date": r.date.isoformat(), "opponent": r.away if home else r.home, "venue": "H" if home else "A",
                    "score": f"{int(r.home_g)}-{int(r.away_g)}", "result": "W" if gf > ga else "D" if gf == ga else "L",
                    "league": r.league})
    return out


def head_to_head(matches: pd.DataFrame, home: str, away: str, before: datetime.date, n: int = 5) -> list[dict]:
    pair = ((matches["home"] == home) & (matches["away"] == away)) | ((matches["home"] == away) & (matches["away"] == home))
    m = matches[pair & (matches["date"] < before) & matches["home_g"].notna()].sort_values("date", ascending=False).head(n)
    return [{"date": r.date.isoformat(), "home": r.home, "away": r.away, "score": f"{int(r.home_g)}-{int(r.away_g)}",
             "league": r.league} for r in m.itertuples()]


def build_match_detail(bet: pd.DataFrame, pinnacle: pd.DataFrame, books: pd.DataFrame, matches: pd.DataFrame,
                       now: datetime.datetime, links: pd.DataFrame | None = None,
                       elo: pd.DataFrame | None = None) -> dict | None:
    """`bet`: one optim_results row joined with fbref (league, scores, notes, xg, venue, referee).
    `pinnacle`: Pinnacle (datetime_insert, side, price) rows before kickoff.
    `books`: (bookmaker_key, bookmaker_title, side, price) at bet time. `matches`: FBref results
    with canonical team names (game, date, league, home, away, home_g, away_g, home_xg, away_xg).
    `elo`: pre-match Elo history (date, team, elo) from team_charts.elo_history."""
    if bet.empty:
        return None
    closing = pinnacle.sort_values("datetime_insert").groupby("side").tail(1).assign(match_id=bet["match_id"].iloc[0])
    t = bet_table(bet, closing[["match_id", "side", "price"]], now, links).iloc[0]
    row = bet.iloc[0]
    kickoff_day = t["kickoff"].date()
    fair_close = closing_fair(closing[["match_id", "side", "price"]])
    xg = [row.get("home_xg"), row.get("away_xg")]
    return {
        "id": t["match_id"], "home": t["home"], "away": t["away"], "league": t["league"], "league_key": t["league_key"],
        "kickoff": t["kickoff"].isoformat(), "odds_at": pd.Timestamp(t["odds_at"]).isoformat(timespec="seconds"),
        "status": t["status"], "score": None if pd.isna(t["home_g"]) else f"{int(t['home_g'])}-{int(t['away_g'])}",
        "xg": None if any(v is None or pd.isna(v) for v in xg) else [float(xg[0]), float(xg[1])],
        "venue": row.get("venue") or None, "referee": row.get("referee") or None,
        "bet": {"side": t["side"], "book": t["book"], "price": float(t["price"]), "fair_price": float(t["fair_price"]),
                "edge": float(t["edge"]), "stake": float(t["stake"]), "gain": float(t["gain"]),
                "clv": None if pd.isna(t["clv"]) else float(t["clv"]), "link": t["link"]},
        "probs": {s: float(t[f"p_{s}"]) for s in SIDES},
        "closing_probs": None if fair_close.empty else {s: float(fair_close.iloc[0][s]) for s in SIDES},
        "closing_fair_price": None if fair_close.empty else {s: float(1 / fair_close.iloc[0][s]) for s in SIDES},
        "pinnacle": line_series(pinnacle),
        "books": books_table(books, t["book"]),
        "form": {"home": team_form(matches, t["home"], kickoff_day), "away": team_form(matches, t["away"], kickoff_day)},
        "h2h": head_to_head(matches, t["home"], t["away"], kickoff_day),
        "elo": None if elo is None else {
            side: elo_series(elo, t[side], kickoff_day - datetime.timedelta(days=365 * ELO_YEARS), kickoff_day)
            for side in ("home", "away")},
        "xg_form": {side: xg_series(matches, t[side], kickoff_day) for side in ("home", "away")},
    }
