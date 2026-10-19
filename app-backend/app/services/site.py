"""Database side of the public site payload (cached a few minutes)."""
import datetime
import threading
import time

import pandas as pd
from sqlalchemy import text

from app._config import engine
from app.services.site_payload import build_payload

BETS_SQL = """
SELECT b.*, f.league, f.home_g, f.away_g, f.notes
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
    closing["price"] = closing["price"].astype(float)
    payload = build_payload(bets, closing, datetime.datetime.utcnow())
    with _lock:
        _cache[label] = (time.monotonic(), payload)
    return payload
