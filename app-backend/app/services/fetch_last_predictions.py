import datetime
from sqlalchemy import text
import pandas as pd
import requests
import time

from optim.functions.player_gain_expected_value import player_gain_expected_value
from optim.functions.player_gain_variance import player_gain_variance


from app._config import DB_TN_OPTIM_RESULTS, PIPELINES_PROTOCOL, PIPELINES_HOST, PIPELINES_PORT, PIPELINES_ENDPOINT_OPTIMIZATION
from app._config import engine

import logging

logger = logging.getLogger('fetch_last_predictions')
query = f"""
SELECT * 
FROM {DB_TN_OPTIM_RESULTS} 
WHERE optim_label = :optim_label 
AND datetime_optim = (
    SELECT MAX(datetime_optim)
    FROM {DB_TN_OPTIM_RESULTS}
    WHERE optim_label = :optim_label 
    AND datetime_optim <= :datetime_optim_last
)
"""

URL_OPTIM = f"{PIPELINES_PROTOCOL}://{PIPELINES_HOST}:{PIPELINES_PORT}/{PIPELINES_ENDPOINT_OPTIMIZATION}"

def fetch_last_predictions_fn(optim_label = 'manual', datetime_optim_last = None):
    try:
        if datetime_optim_last:
            datetime_optim_last = datetime.datetime.strptime(datetime_optim_last, "%Y-%m-%d %H:%M:%S")
        else:
            datetime_optim_last = datetime.datetime.now()
    except Exception as e:
        raise

    try:
        with engine.connect() as connection:
            df_optim_results = pd.read_sql(text(query), connection, params={"optim_label": optim_label, "datetime_optim_last": datetime_optim_last})
        if df_optim_results.empty:
            logger.info(f"No results found for datetime_optim_last: {datetime_optim_last} with optim_label: {optim_label}")
            return df_optim_results
        logger.info(f"Results found for datetime_optim_last: {datetime_optim_last} with optim_label: {optim_label}")
    except Exception as e:
        logger.error(f"Failed to get results from db: {str(e)}")
        raise
    
    return df_optim_results
