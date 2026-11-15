"""Database side of the public site payload (cached a few minutes)."""
import datetime
import threading
import time

import pandas as pd
from sqlalchemy import text

from app._config import engine
from app.services.match_detail import build_match_detail
from app.services.team_charts import elo_history
from app.services.site_payload import build_payload
from app.services.swr_cache import SWRCache

BETS_SQL = """
SELECT b.*, f.league, f.home_g, f.away_g, f.notes, f.home_xg, f.away_xg, f.venue, f.referee
FROM (
    SELECT DISTINCT ON (game) *
    FROM optim_results
    WHERE optim_label = :label
    ORDER BY game, datetime_optim
) b
LEFT JOIN fbref_results f ON f.game = b.game
"""

# Pinnacle's last pre-kickoff 1X2 prices for the recommended games (closing line).
CLOSING_SQL = """
SELECT DISTINCT ON (match_id, side) match_id, side, price
FROM (
    SELECT match_id, datetime_insert, outcome_price AS price,
           CASE WHEN outcome_name = home_team THEN 'home' WHEN outcome_name = away_team THEN 'away'
                WHEN outcome_name = 'Draw' THEN 'draw' END AS side
    FROM mv_soccer_odds_normalized
    WHERE market_key = 'h2h' AND bookmaker_key = 'pinnacle'
      AND bookmaker_last_update < commence_time
      AND match_id IN (SELECT match_id FROM optim_results WHERE optim_label = :label)
) p
WHERE side IS NOT NULL
ORDER BY match_id, side, datetime_insert DESC
"""

ODDS_SIDE = """CASE WHEN outcome_name = home_team THEN 'home' WHEN outcome_name = away_team THEN 'away'
                WHEN outcome_name = 'Draw' THEN 'draw' END"""

PINNACLE_SQL = f"""
SELECT datetime_insert, {ODDS_SIDE} AS side, outcome_price AS price
FROM soccer_odds
WHERE match_id = :match_id AND market_key = 'h2h' AND bookmaker_key = 'pinnacle'
  AND bookmaker_last_update < commence_time
ORDER BY datetime_insert
"""

# Each bookmaker's last pre-kickoff price known when the bet was recommended.
BOOKS_AT_BET_SQL = f"""
SELECT DISTINCT ON (bookmaker_key, side) bookmaker_key, bookmaker_title, side, price
FROM (
    SELECT bookmaker_key, bookmaker_title, datetime_insert, {ODDS_SIDE} AS side, outcome_price AS price
    FROM soccer_odds
    WHERE match_id = :match_id AND market_key = 'h2h' AND datetime_insert <= :at
      AND bookmaker_last_update < commence_time
) o
WHERE side IS NOT NULL
ORDER BY bookmaker_key, side, datetime_insert DESC
"""

TEAM_MATCHES_SQL = """
SELECT game, date, league, home_team_canonical_name AS home, away_team_canonical_name AS away, home_g, away_g,
       home_xg, away_xg
FROM v_matches_fbref
WHERE (home_team_canonical_name IN (:home, :away) OR away_team_canonical_name IN (:home, :away))
  AND date < :before AND date > :since
"""

# Every match since ELO_SINCE feeds the Elo ratings (same rating as the model features).
ELO_SINCE = datetime.date(2012, 7, 1)
ELO_SQL = """
SELECT date, home_team_canonical_name AS home, away_team_canonical_name AS away, home_g, away_g
FROM v_matches_fbref WHERE date >= :since
"""
ELO_TTL_SECONDS = 6 * 3600

TTL_SECONDS = 300
_cache: dict[str, tuple[float, dict]] = {}
_lock = threading.Lock()
_swr = SWRCache()


def site_payload(label: str) -> dict:
    """Public payload, refreshed in the background once older than TTL_SECONDS (stale-while-revalidate)."""
    return _swr.get(f"site/{label}", TTL_SECONDS, lambda: _build_site_payload(label))


def _build_site_payload(label: str) -> dict:
    with engine.connect() as conn:
        bets = pd.read_sql(text(BETS_SQL), conn, params={"label": label})
        closing = pd.read_sql(text(CLOSING_SQL), conn, params={"label": label})
    closing["price"] = closing["price"].astype(float)
    return build_payload(bets, closing, datetime.datetime.utcnow())


def elo_ratings() -> pd.DataFrame:
    """Pre-match Elo history of every team (a few seconds of work): recomputed in the background every
    few hours while the previous history keeps serving match pages."""
    return _swr.get("elo", ELO_TTL_SECONDS, _build_elo_history)


def _build_elo_history() -> pd.DataFrame:
    with engine.connect() as conn:
        matches = pd.read_sql(text(ELO_SQL), conn, params={"since": ELO_SINCE})
    matches["date"] = pd.to_datetime(matches["date"]).dt.date
    return elo_history(matches)


def match_detail(label: str, match_id: str) -> dict | None:
    with _lock:
        hit = _cache.get(f"{label}/{match_id}")
        if hit and time.monotonic() - hit[0] < TTL_SECONDS:
            return hit[1]
    with engine.connect() as conn:
        bet = pd.read_sql(text(BETS_SQL + " WHERE b.match_id = :match_id"), conn,
                          params={"label": label, "match_id": match_id})
        if bet.empty:
            return None
        at = pd.Timestamp(bet["datetime_optim"].iloc[0]).to_pydatetime()
        kickoff = pd.Timestamp(f"{bet['date_match'].iloc[0]} {bet['time_match'].iloc[0]}")
        pinnacle = pd.read_sql(text(PINNACLE_SQL), conn, params={"match_id": match_id})
        books = pd.read_sql(text(BOOKS_AT_BET_SQL), conn, params={"match_id": match_id, "at": at})
        matches = pd.read_sql(text(TEAM_MATCHES_SQL), conn, params={
            "home": bet["home_team"].iloc[0], "away": bet["away_team"].iloc[0],
            "before": kickoff.date(), "since": kickoff.date() - datetime.timedelta(days=6 * 365)})
    for df in (pinnacle, books):
        df["price"] = df["price"].astype(float)
    matches["date"] = pd.to_datetime(matches["date"]).dt.date
    detail = build_match_detail(bet, pinnacle, books, matches, datetime.datetime.utcnow(), None, elo_ratings())
    with _lock:
        _cache[f"{label}/{match_id}"] = (time.monotonic(), detail)
    return detail
