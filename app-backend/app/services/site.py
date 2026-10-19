"""Database side of the public site payload (cached a few minutes)."""
import datetime
import threading
import time

import pandas as pd
from sqlalchemy import text

from app._config import engine
from app.services.match_detail import build_match_detail
from app.services.site_payload import build_payload

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

# Latest event link per bookmaker (stored since includeLinks was enabled on the odds ingestion).
LINKS_SQL = """
SELECT DISTINCT ON (match_id, bookmaker_key) match_id, bookmaker_key, bookmaker_link
FROM soccer_odds
WHERE bookmaker_link IS NOT NULL
  AND match_id IN (SELECT match_id FROM optim_results WHERE optim_label = :label)
ORDER BY match_id, bookmaker_key, datetime_insert DESC
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
SELECT game, date, league, home_team_canonical_name AS home, away_team_canonical_name AS away, home_g, away_g
FROM v_matches_fbref
WHERE (home_team_canonical_name IN (:home, :away) OR away_team_canonical_name IN (:home, :away))
  AND date < :before AND date > :since
"""

TTL_SECONDS = 300
_cache: dict[str, tuple[float, dict]] = {}
_lock = threading.Lock()


def site_payload(label: str) -> dict:
    with _lock:
        hit = _cache.get(label)
        if hit and time.monotonic() - hit[0] < TTL_SECONDS:
            return hit[1]
    with engine.connect() as conn:
        bets = pd.read_sql(text(BETS_SQL), conn, params={"label": label})
        closing = pd.read_sql(text(CLOSING_SQL), conn, params={"label": label})
        links = pd.read_sql(text(LINKS_SQL), conn, params={"label": label})
    closing["price"] = closing["price"].astype(float)
    payload = build_payload(bets, closing, datetime.datetime.utcnow(), links)
    with _lock:
        _cache[label] = (time.monotonic(), payload)
    return payload


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
        links = pd.read_sql(text(LINKS_SQL), conn, params={"label": label})
    links = links[links["match_id"] == match_id]
    for df in (pinnacle, books):
        df["price"] = df["price"].astype(float)
    matches["date"] = pd.to_datetime(matches["date"]).dt.date
    detail = build_match_detail(bet, pinnacle, books, matches, datetime.datetime.utcnow(), links)
    with _lock:
        _cache[f"{label}/{match_id}"] = (time.monotonic(), detail)
    return detail
