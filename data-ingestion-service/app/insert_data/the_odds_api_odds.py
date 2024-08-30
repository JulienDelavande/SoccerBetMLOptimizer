import requests
from sqlalchemy import text
import logging
import pandas as pd

from app._config import DB_TN_ODDS_TEMP, DB_TN_ODDS, THE_ODDS_API_KEY, engine
from feature_eng.odds.odds_extraction import json_to_pandas_the_odds_api_get_odds


sports = ['soccer_france_ligue_one', 'soccer_spain_la_liga', 'soccer_italy_serie_a', 'soccer_germany_bundesliga', 'soccer_epl']
regions = 'eu'
markets = 'h2h'
urls = [f'https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={THE_ODDS_API_KEY}&regions={regions}&markets={markets}' for sport in sports]

logger = logging.getLogger("the_odds_api")

insert_query = f"""
INSERT INTO {DB_TN_ODDS} (match_id, sport_key, sport_title, commence_time, home_team, away_team,
    bookmaker_key, bookmaker_title, bookmaker_last_update, market_key,
    market_last_update, outcome_name, outcome_price)
SELECT match_id, sport_key, sport_title, commence_time, home_team, away_team,
    bookmaker_key, bookmaker_title, bookmaker_last_update, market_key,
    market_last_update, outcome_name, outcome_price
FROM {DB_TN_ODDS_TEMP}
ON CONFLICT (match_id, bookmaker_key, market_key, outcome_name, market_last_update) DO NOTHING;
"""

count_query = f"""
SELECT COUNT(*) FROM {DB_TN_ODDS_TEMP}
WHERE NOT EXISTS (
    SELECT 1 FROM {DB_TN_ODDS}
        WHERE {DB_TN_ODDS}.match_id = {DB_TN_ODDS_TEMP}.match_id
        AND {DB_TN_ODDS}.bookmaker_key = {DB_TN_ODDS_TEMP}.bookmaker_key
        AND {DB_TN_ODDS}.market_key = {DB_TN_ODDS_TEMP}.market_key
        AND {DB_TN_ODDS}.outcome_name = {DB_TN_ODDS_TEMP}.outcome_name
        AND {DB_TN_ODDS}.market_last_update = {DB_TN_ODDS_TEMP}.market_last_update
)
"""

drop_table_query = f"DROP TABLE IF EXISTS {DB_TN_ODDS_TEMP}"

def ingest_odds_the_odds_api():
    try:
        responses = [requests.get(url) for url in urls]
        dfs_odds = [json_to_pandas_the_odds_api_get_odds(response.json()) for response in responses]
        df_odds = pd.concat(dfs_odds, ignore_index=True)
        logger.info("Cotes récupérérées avec succces depuis l'API The Odds Api")
    except Exception as e:
        logger.error(f"Erreur lors de la recuperation des donnees: {e}")
        return

    try:
        with engine.begin() as conn:
            df_odds.to_sql(DB_TN_ODDS_TEMP, engine, if_exists='replace', index=False)
            conn.execute(text(insert_query))
            result = conn.execute(text(count_query))
            inserted_rows = result.scalar()
            conn.execute(text(drop_table_query))
            logger.info(f"Insertion des nouvelles donnees terminee avec succes, {inserted_rows} nouvelles lignes inserees")
    except Exception as e:
        logger.error(f"Erreur lors de l'insertion des donnees: {e}")
        return
    
    return

if __name__ == '__main__':
    ingest_odds_the_odds_api()

