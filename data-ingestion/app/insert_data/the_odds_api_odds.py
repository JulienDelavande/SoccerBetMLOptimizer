import requests
from sqlalchemy import text
import logging
import pandas as pd

from app._config import DB_TN_ODDS, THE_ODDS_API_KEY, THE_ODDS_API_BASE_URL, THE_ODDS_API_SPORTS, THE_ODDS_API_REGIONS, THE_ODDS_API_MARKETS, engine
from app.insert_data.utils import json_to_pandas_the_odds_api_get_odds


sports = THE_ODDS_API_SPORTS.split(',')
urls = [f'{THE_ODDS_API_BASE_URL}/{sport}/odds/?apiKey={THE_ODDS_API_KEY}&regions={THE_ODDS_API_REGIONS}&markets={THE_ODDS_API_MARKETS}' for sport in sports]

### Variables ###
DB_TN_ODDS_TEMP = 'temp_table_odds_the_odds_api'  
logger = logging.getLogger("the_odds_api")
pd.set_option('display.max_columns', None)

insert_query = f"""
WITH inserted_rows AS (
    INSERT INTO {DB_TN_ODDS} (match_id, sport_key, sport_title, commence_time, home_team, away_team,
        bookmaker_key, bookmaker_title, bookmaker_last_update, market_key,
        market_last_update, outcome_name, outcome_price)
    SELECT match_id, sport_key, sport_title, commence_time, home_team, away_team,
        bookmaker_key, bookmaker_title, bookmaker_last_update, market_key,
        market_last_update, outcome_name, outcome_price
    FROM {DB_TN_ODDS_TEMP}
    ON CONFLICT (match_id, bookmaker_key, market_key, outcome_name, market_last_update) DO NOTHING
    RETURNING match_id
)
SELECT COUNT(*) AS inserted_rows_count FROM inserted_rows;
"""

drop_table_query = f"DROP TABLE IF EXISTS {DB_TN_ODDS_TEMP}"

def ingest_odds_the_odds_api():
    df_odds = get_odds()
    put_odds_in_db(df_odds)
    return

def get_odds():
    try:
        responses = [requests.get(url) for url in urls]
        for response in responses:
            if response.status_code != 200:
                logger.error(f"Erreur lors de la recuperation des donnees: {response.status_code} - {response.text}")
                raise Exception(f"Erreur lors de la recuperation des donnees: {response.status_code} - {response.text}")
        dfs_odds = [json_to_pandas_the_odds_api_get_odds(response.json()) for response in responses if response.json()]
        df_odds = pd.concat(dfs_odds, ignore_index=True) if dfs_odds else pd.DataFrame()
        df_odds['datetime_insert'] = pd.to_datetime('now')
        logger.info("Cotes récupérérées avec succces depuis l'API The Odds Api")
        logger.info(f'Nombre de lignes récupérées: {len(df_odds)}')
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des donnees: {e}")
        raise
    return df_odds
    
def put_odds_in_db(df_odds):
    try:
        logger.info("Insertion des donnees dans la base de donnees")
        logger.info(f"BD_HOST: {engine.url.host}")
        logger.info(f"BD_PORT: {engine.url.port}")
        logger.info(f"BD_NAME: {engine.url.database}")
        with engine.begin() as conn:
            df_odds.to_sql(DB_TN_ODDS_TEMP, engine, if_exists='replace', index=False)
            logger.info(f"Table {DB_TN_ODDS_TEMP} creee avec succes")

        with engine.begin() as conn:
            result = conn.execute(text(insert_query))
            logger.info(f"Insertion des nouvelles donnees terminee avec succes")
            
            inserted_rows = result.scalar()
            logger.info(f"{inserted_rows} nouvelles lignes inserees")
        
            conn.execute(text(drop_table_query))
            logger.info(f"Table {DB_TN_ODDS_TEMP} supprimee avec succes")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'insertion des donnees: {e}")
        raise

if __name__ == '__main__':
    ingest_odds_the_odds_api()
