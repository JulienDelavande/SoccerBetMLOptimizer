import datetime
from sqlalchemy import text
import pandas as pd
import logging

from app._config import engine

logger = logging.getLogger('fetch_cumulative_bankroll')

query = """
WITH last_optim AS (
    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (PARTITION BY game ORDER BY datetime_optim DESC) as rn
        FROM optim_results
        WHERE optim_label = :optim_label
          AND date_match BETWEEN :datetime_first_match AND :datetime_last_match
    ) t
    WHERE rn = 1
),
joined AS (
    SELECT o.*, f.date AS match_date, f.game_id, f.home_g, f.away_g,
           f.odds_home, f.odds_draw, f.odds_away
    FROM last_optim o
    JOIN fbref_results f ON o.game = f.game
    WHERE f.date BETWEEN :datetime_first_match AND :datetime_last_match
      AND f.game_id IS NOT NULL
),
match_with_gain AS (
    SELECT *,
        CASE
            WHEN home_g > away_g THEN f_home * odds_home - (f_draw + f_away)
            WHEN away_g > home_g THEN f_away * odds_away - (f_home + f_draw)
            ELSE f_draw * odds_draw - (f_home + f_away)
        END AS gain
    FROM joined
),
daily_gain AS (
    SELECT match_date::date AS day, SUM(gain) AS daily_gain
    FROM match_with_gain
    GROUP BY match_date::date
    ORDER BY match_date::date
),
cumulative_bankroll AS (
    SELECT
        day,
        daily_gain,
        EXP(SUM(LN(1 + daily_gain)) OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)) AS bankroll
    FROM daily_gain
)

SELECT * FROM cumulative_bankroll;
"""

def fetch_past_performances_gains_fn(optim_label='manual', datetime_first_match=None, datetime_last_match=None):
    try:
        if datetime_first_match:
            datetime_first_match = datetime.datetime.strptime(datetime_first_match, "%Y-%m-%d %H:%M:%S")
        else:
            datetime_first_match = datetime.datetime.now() - datetime.timedelta(days=30)

        if datetime_last_match:
            datetime_last_match = datetime.datetime.strptime(datetime_last_match, "%Y-%m-%d %H:%M:%S")
        else:
            datetime_last_match = datetime.datetime.now()

    except Exception as e:
        logger.error(f"Invalid datetime format: {str(e)}")
        raise ValueError(f"Invalid datetime format: {str(e)}")

    try:
        with engine.connect() as connection:
            df_bankroll = pd.read_sql(text(query), connection, params={
                "optim_label": optim_label,
                "datetime_first_match": datetime_first_match,
                "datetime_last_match": datetime_last_match
            })
            print(f"{df_bankroll.columns}")
            if df_bankroll.empty:
                logger.info(f"No data found for bankroll computation.")
                raise ValueError("No bankroll data found for the given parameters.")
            logger.info(f"Bankroll data fetched successfully.")

    except Exception as e:
        logger.error(f"Failed to fetch bankroll data: {str(e)}")
        raise e

    return df_bankroll
