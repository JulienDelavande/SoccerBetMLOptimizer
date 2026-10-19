"""Team history charts for the match page: Elo ratings and rolling xG (FBref results)."""
import datetime

import numpy as np
import pandas as pd

from optibet_lib.feature_eng.team_stats import elo_scores

XG_WINDOW = 8


def elo_history(matches: pd.DataFrame) -> pd.DataFrame:
    """Pre-match Elo of both teams for every match, chronological (optibet_lib Elo, as in the model features).

    `matches`: date, home, away, home_g, away_g. Returns rows (date, team, elo) for played matches."""
    m = matches.sort_values("date", kind="stable").reset_index(drop=True).copy()
    elo_scores(m, home_team_id_col="home", away_team_id_col="away", home_team_goal_col="home_g",
               away_team_goal_col="away_g", datetime_col="date")
    played = m["home_g"].notna() & m["away_g"].notna()
    m = m[played]
    return pd.concat([
        pd.DataFrame({"date": m["date"], "team": m["home"], "elo": m["elo_home_before"]}),
        pd.DataFrame({"date": m["date"], "team": m["away"], "elo": m["elo_away_before"]}),
    ]).sort_values("date", kind="stable").reset_index(drop=True)


def elo_series(history: pd.DataFrame, team: str, since: datetime.date, before: datetime.date) -> list[dict]:
    h = history[(history["team"] == team) & (history["date"] >= since) & (history["date"] <= before)]
    return [{"d": d.isoformat(), "v": round(float(e), 1)} for d, e in zip(h["date"], h["elo"])]


def xg_series(matches: pd.DataFrame, team: str, before: datetime.date, window: int = XG_WINDOW, last: int = 40,
              max_age_days: int = 90) -> list[dict]:
    """Rolling mean of xG for / against over `window` matches, for the team's last `last` matches with xG.

    Empty when the team's latest xG is older than `max_age_days` (FBref has published no xG
    since late 2025): a stale curve would read as current form."""
    m = matches[((matches["home"] == team) | (matches["away"] == team)) & (matches["date"] < before)
                & matches["home_xg"].notna() & matches["away_xg"].notna()].sort_values("date")
    if m.empty or (before - m["date"].iloc[-1]).days > max_age_days:
        return []
    home = (m["home"] == team).to_numpy()
    xg_for = np.where(home, m["home_xg"], m["away_xg"]).astype(float)
    xg_against = np.where(home, m["away_xg"], m["home_xg"]).astype(float)
    f = pd.Series(xg_for).rolling(window, min_periods=3).mean()
    a = pd.Series(xg_against).rolling(window, min_periods=3).mean()
    out = [{"d": d.isoformat(), "for": round(float(x), 2), "against": round(float(y), 2)}
           for d, x, y in zip(m["date"], f, a) if not (np.isnan(x) or np.isnan(y))]
    return out[-last:]
