"""Daily value bets: soft-book prices that beat Pinnacle's fair line.

Run after the odds ingestion. Uses only the latest ingestion batch, pre-kickoff
prices, fresh soft-book prices (updated close to Pinnacle's), and recommends each
game at most once per label (the first sighting carries the closing-line value).
See optibet_lib.betting and research/backtest_sync.py for the validation.
"""
import datetime
import logging

import numpy as np
import pandas as pd
from sqlalchemy import text

from app._config import DB_TN_OPTIM_RESULTS, engine
from optibet_lib.betting import SIDES, compute_value_bets

logger = logging.getLogger("VB")

LATEST_ODDS_SQL = """
SELECT match_id, sport_key, commence_time, home_team_canonical AS home_team, away_team_canonical AS away_team,
       bookmaker_key AS book, bookmaker_last_update AS updated, outcome_price AS price,
       CASE WHEN outcome_name = home_team THEN 'home' WHEN outcome_name = away_team THEN 'away'
            WHEN outcome_name = 'Draw' THEN 'draw' END AS side
FROM mv_soccer_odds_normalized
WHERE market_key = 'h2h'
  AND datetime_insert = (SELECT max(datetime_insert) FROM soccer_odds)
  AND commence_time > :not_before
  AND bookmaker_last_update < commence_time
"""

MODEL_SQL = """
SELECT game, date_match, home_team, away_team, datetime_inference, prob_home_win, prob_draw, prob_away_win
FROM mv_models_results_last_inferred WHERE model = :model AND date_match >= :since
"""

ALREADY_SQL = f"SELECT DISTINCT match_id FROM {DB_TN_OPTIM_RESULTS} WHERE optim_label = :label"

# FBref game ids, so the backend can settle the bets (it joins optim_results.game to fbref_results.game).
FBREF_GAMES_SQL = """
SELECT game, date, home_team_canonical_name AS home_team, away_team_canonical_name AS away_team
FROM v_matches_fbref WHERE date >= :since
"""


def attach_fbref_game(bets: pd.DataFrame, fbref_games: pd.DataFrame) -> pd.Series:
    """FBref game id per bet (same canonical teams, kickoff date within a day), None if unknown."""
    kick = pd.to_datetime(bets["commence_time"]).dt.normalize()
    j = bets[["match_id", "home_team", "away_team"]].assign(kick=kick.values).merge(
        fbref_games.assign(date=pd.to_datetime(fbref_games["date"])), on=["home_team", "away_team"], how="left")
    j = j[(j["kick"] - j["date"]).abs() <= pd.Timedelta(days=1)]
    return bets["match_id"].map(j.drop_duplicates("match_id").set_index("match_id")["game"])


def find_value_bets(books, min_edge=0.02, max_price=3.5, kelly_fraction=0.25, max_stake=0.05, max_total=0.30,
                    blend_weight=0.1, fresh_hours=6.0, model="RSF_PR_LR", optim_label="value_pinnacle",
                    min_minutes_before_kickoff=15, dry_run=False):
    now = datetime.datetime.utcnow()
    with engine.begin() as conn:
        for mv in ("mv_soccer_odds_normalized", "mv_models_results_last_inferred"):
            conn.execute(text(f"REFRESH MATERIALIZED VIEW {mv}"))
        odds = pd.read_sql(text(LATEST_ODDS_SQL), conn,
                           params={"not_before": now + datetime.timedelta(minutes=min_minutes_before_kickoff)})
        model_df = pd.read_sql(text(MODEL_SQL), conn, params={"model": model, "since": now.date() - datetime.timedelta(days=1)})
        already = pd.read_sql(text(ALREADY_SQL), conn, params={"label": optim_label})["match_id"]
        fbref_games = pd.read_sql(text(FBREF_GAMES_SQL), conn, params={"since": now.date() - datetime.timedelta(days=1)})
    logger.info(f"latest batch: {odds['match_id'].nunique()} upcoming games, {odds['book'].nunique()} books; "
                f"{len(already)} games already recommended for {optim_label}")
    bets = compute_value_bets(odds, model_df, books, min_edge, max_price, kelly_fraction, max_stake, max_total,
                              blend_weight, fresh_hours, already)
    datetime_optim = datetime.datetime.utcnow()
    if bets.empty:
        logger.info("No value bet today")
        return datetime_optim, bets

    kickoff = pd.to_datetime(bets["commence_time"])
    rows = pd.DataFrame({
        "match_id": bets["match_id"], "sport_key": bets["sport_key"],
        "game": attach_fbref_game(bets, fbref_games).fillna(
            kickoff.dt.strftime("%Y-%m-%d ") + bets["home_team"] + "-" + bets["away_team"]),
        "date_match": kickoff.dt.date, "time_match": kickoff.dt.time,
        "home_team": bets["home_team"], "away_team": bets["away_team"],
        "model": model, "datetime_inference": datetime_optim,
        "prob_home_win": bets["fair_home"], "prob_draw": bets["fair_draw"], "prob_away_win": bets["fair_away"],
        "datetime_optim": datetime_optim, "utility_fn": "ValueKelly", "optim_label": optim_label,
    })
    for s in SIDES:
        chosen = bets["side"] == s
        rows[f"odds_{s}"] = np.where(chosen, bets["price"], np.nan)
        rows[f"bookmaker_{s}_key"] = np.where(chosen, bets["book"], None)
        rows[f"bookmaker_{s}"] = rows[f"bookmaker_{s}_key"]
        rows[f"f_{s}"] = np.where(chosen, bets["stake"], 0.0)
    logger.info(f"{len(rows)} value bets, total stake {rows[['f_home', 'f_draw', 'f_away']].to_numpy().sum():.3f} "
                f"of bankroll, mean edge {bets['edge'].mean():.3f}")
    if not dry_run:
        with engine.begin() as conn:
            rows.to_sql(DB_TN_OPTIM_RESULTS, conn, if_exists="append", index=False)
    return datetime_optim, rows
