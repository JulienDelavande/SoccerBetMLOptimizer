import datetime
from sqlalchemy import text
import pandas as pd
import numpy as np


from app._config import PIPELINES_PROTOCOL, PIPELINES_HOST, PIPELINES_PORT, PIPELINES_ENDPOINT_OPTIMIZATION
from app._config import engine

import logging

logger = logging.getLogger('fetch_last_predictions')
query = f"""
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
)

SELECT o.*, f.*
FROM last_optim o
JOIN fbref_results f ON o.game = f.game
WHERE f.date BETWEEN :datetime_first_match AND :datetime_last_match
  AND f.game_id IS NOT NULL
"""

URL_OPTIM = f"{PIPELINES_PROTOCOL}://{PIPELINES_HOST}:{PIPELINES_PORT}/{PIPELINES_ENDPOINT_OPTIMIZATION}"

def fetch_past_performances_fn(optim_label = 'manual', datetime_first_match = None, datetime_last_match = None):
    try:
        if datetime_first_match:
            datetime_first_match = datetime.datetime.strptime(datetime_first_match, "%Y-%m-%d %H:%M:%S")
        else:
             # take last 30 days if no datetime_first_match is provided
            datetime_first_match = datetime.datetime.now() - datetime.timedelta(days=30)
        if datetime_last_match:
            datetime_last_match = datetime.datetime.strptime(datetime_last_match, "%Y-%m-%d %H:%M:%S")
        else:
            # take today if no datetime_last_match is provided
            datetime_last_match = datetime.datetime.now()   
    except Exception as e:
        logger.error(f"Invalid datetime format: {str(e)}")
        raise ValueError(f"Invalid datetime format: {str(e)}")
    
    try:
        with engine.connect() as connection:
            df_merged_predictions_results = pd.read_sql(text(query), connection, params={
                "optim_label": optim_label,
                "datetime_first_match": datetime_first_match,
                "datetime_last_match": datetime_last_match
            })
            if df_merged_predictions_results.empty:
                logger.info(f"No past performances found for optim_label: {optim_label}, datetime_first_match: {datetime_first_match}, datetime_last_match: {datetime_last_match}")
                return pd.DataFrame()  # Return empty DataFrame if no data found
            logger.info(f"Past performances fetched successfully for optim_label: {optim_label}, datetime_first_match: {datetime_first_match}, datetime_last_match: {datetime_last_match}")
            df_merged_predictions_results = df_merged_predictions_results.replace([np.inf, -np.inf], np.nan)
            df_merged_predictions_results = df_merged_predictions_results.fillna(value="")
            df_merged_predictions_results = df_merged_predictions_results.loc[:, ~df_merged_predictions_results.columns.duplicated()]
    except Exception as e:
        logger.error(f"Failed to fetch past performances from the database: {str(e)}")
        raise e

    return df_merged_predictions_results
