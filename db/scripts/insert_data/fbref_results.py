import soccerdata as sd
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
import os
import logging
import argparse
from pathlib import Path
import datetime
import hashlib


#### LOGGING ####
LOG_FOLDER = "logs/"
LOG_FILE_NAME = "fbref_results_table.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

DN_TN_TEMP_TABLE = 'temp_table'
KEY = 'game'
KEY_BIS = 'score'

filename = Path(__file__).resolve().parents[2] / LOG_FOLDER / LOG_FILE_NAME
logger = logging.getLogger("fbref_results_table__loger")
file_handler = logging.FileHandler(filename)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter(LOG_FORMAT)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def scrap_data_fbref(get_current_season_only=True, use_cache=True):
    """Recuperer les schedule et scores des matchs de fbref"""
    try:
        
        current_season = datetime.datetime.now().year

        logger.info(f"Chargement des donnees des matchs INT-World Cup")
        leagues = ["INT-World Cup"]
        seasons = [f"{str(year)}-{str(year+1)[2:]}" for year in range(1930, current_season+1, 4)]
        [seasons.remove(f"{str(year)}-{str(year+1)[2:]}") for year in range(1942, 1948, 4)]
        if get_current_season_only:
            current_season_int = f"{current_season}-{str(current_season+1)[2:]}"
            seasons = [current_season_int] if current_season_int in seasons else []
        fbref = sd.FBref(leagues=leagues, seasons=seasons)
        matches_wc = fbref.read_schedule(force_cache=use_cache) if seasons else None
        matches_wc = matches_wc.reset_index() if matches_wc is not None else None

        logger.info(f"Chargement des donnees des matchs INT-European Championships")
        leagues = ['INT-European Championships']
        seasons = list(range(2000, current_season+1, 4))
        if get_current_season_only:
            seasons = [current_season] if current_season in seasons else []
        fbref = sd.FBref(leagues=leagues, seasons=seasons)
        euro_schedule = fbref.read_schedule(force_cache=use_cache) if seasons else None
        euro_schedule = euro_schedule.reset_index() if euro_schedule is not None else None

        logger.info(f"Chargement des donnees des matchs Big 5 European Leagues Combined")
        leagues = ["Big 5 European Leagues Combined"]
        seasons = [f"{str(year)[2:]}-{str(year+1)[2:]}" for year in range(1930, current_season+1)]
        [seasons.remove(f"{str(year)[2:]}-{str(year+1)[2:]}") for year in range(1939, 1946)]
        if get_current_season_only:
            current_season_big5 = f"{str(current_season-1)[2:]}-{str(current_season)[2:]}"
            seasons = [current_season_big5] if current_season_big5 in seasons else []
        fbref = sd.FBref(leagues=leagues, seasons=seasons)
        big5 = fbref.read_schedule(force_cache=use_cache) if seasons else None
        big5 = big5.reset_index() if big5 is not None else None

        fbref_df = pd.concat([matches_wc, euro_schedule, big5], ignore_index=True)

        return fbref_df
    except Exception as e:
        logger.error(f"Erreur lors du chargement des donnees des matchs fbref: {e}")
        return


def convert_data_types_fbref(fbref_df):
    """Convertir les types de donnees"""
    logger.info("Conversion des types de donnees")
    try: 
        fbref_df             = fbref_df.reset_index()
        fbref_df['date']     = pd.to_datetime(fbref_df['date'])
        fbref_df['time']     = pd.to_datetime(fbref_df['time']).dt.time
        fbref_df['index']    = fbref_df['game'].apply(lambda x: int(hashlib.sha256(x.encode()).hexdigest()[:6], 16))
        fbref_df['home_g']   = fbref_df['score'].apply(lambda x: x.split('–')[0][-1] if not pd.isna(x) else x)
        fbref_df['away_g']   = fbref_df['score'].apply(lambda x: x.split('–')[1][0] if not pd.isna(x) else x)
        fbref_df['home_sat'] = fbref_df['score'].apply(lambda x: x.split('–')[0].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
        fbref_df['away_sat'] = fbref_df['score'].apply(lambda x: x.split('–')[1].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
        fbref_df['home_g']   = pd.to_numeric(fbref_df['home_g'], errors='coerce')
        fbref_df['away_g']   = pd.to_numeric(fbref_df['away_g'], errors='coerce')
        fbref_df['home_sat'] = pd.to_numeric(fbref_df['home_sat'], errors='coerce')
        fbref_df['away_sat'] = pd.to_numeric(fbref_df['away_sat'], errors='coerce')

        return fbref_df
    
    except Exception as e:
        logger.error(f"Erreur lors de la conversion des types de donnees: {e}")
        return


def insert_data_fbref_results_table(get_current_season_only=True, use_cache=True):
    """Inserer les donnees des matchs de fbref dans la table fbref_results"""

    logger.info(f"--- Debut de l'insertion des donnees dans la table fbref_results")

    #### VARIABLES ####
    load_dotenv()
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_TN_FBREF_RESULTS = os.getenv('DB_TN_FBREF_RESULTS')


    #### CONNECTION A LA BASE DE DONNEES ####
    logger.info("Connexion a la base de donnees")
    logger.info(f"DB_USER: {DB_USER}")
    try:
        connection_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        engine = create_engine(connection_url)
    except Exception as e:
        logger.error(f"Erreur lors de la connexion à la base de donnees: {e}")
        return


    #### SCRAPPING SOFIFA TEAMS DATA ####
    logger.info("Chargement des donnees de Fbref")
    logger.info(f"get_current_season_only: {get_current_season_only}")
    logger.info(f"use_cache: {use_cache}")
    fbref_df = scrap_data_fbref(get_current_season_only=get_current_season_only, use_cache=use_cache)


    #### CONVERSION DES TYPES DE DONNEES ####
    fbref_df = convert_data_types_fbref(fbref_df)


    #### INSERTION DES DONNEES DANS LA BASE DE DONNEES ####
    logger.info("Insertion des donnees dans la base de donnees")
    try:
        with engine.connect() as conn:
            fbref_df.to_sql(DN_TN_TEMP_TABLE, conn, if_exists='replace', index=False)

            # Liste des colonnes
            columns = ', '.join(fbref_df.columns)
            update_columns = ', '.join([f"{col} = EXCLUDED.{col}" for col in fbref_df.columns])
            
            # Inserer les donnees en evitant les doublons
            insert_query = f"""
            INSERT INTO {DB_TN_FBREF_RESULTS} ({columns})
            SELECT {columns}
            FROM {DN_TN_TEMP_TABLE}
            ON CONFLICT ("{KEY}") DO UPDATE SET {update_columns}
            """
            logger.info("Insertion des nouvelles donnees en cours...")
            conn.execute(text(insert_query))

            # Compter le nombre de nouvelles lignes inserees
            count_query = f"""
            SELECT COUNT(*) FROM {DN_TN_TEMP_TABLE}
            WHERE NOT EXISTS (
                SELECT 1 FROM {DB_TN_FBREF_RESULTS}
                WHERE {DB_TN_FBREF_RESULTS}."{KEY}" = {DN_TN_TEMP_TABLE}."{KEY}"
                AND {DB_TN_FBREF_RESULTS}.{KEY_BIS} = {DN_TN_TEMP_TABLE}.{KEY_BIS}
            )
            """
            result = conn.execute(text(count_query))
            inserted_rows = result.scalar()
            logger.info(f"Insertion des nouvelles donnees terminee avec succes, {inserted_rows} nouvelles lignes inserees")

            conn.execute(text(f"DROP TABLE {DN_TN_TEMP_TABLE}"))
            conn.commit()

    except Exception as e:
        logger.error(f"Erreur lors de l'insertion des donnees: {e}")
        return
    
    logger.info(f"Fin de l'insertion des donnees dans la table {DB_TN_FBREF_RESULTS}\n\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Insert fbref results into the database')
    parser.add_argument('--get_current_season_only', type=bool, default=True, help='Scrap only the last season')
    parser.add_argument('--use_cache', type=bool, default=False, help='Use cached data')

    args = parser.parse_args()
    get_current_season_only = args.get_current_season_only
    use_cache = args.use_cache

    insert_data_fbref_results_table(get_current_season_only=get_current_season_only, use_cache=use_cache)
    