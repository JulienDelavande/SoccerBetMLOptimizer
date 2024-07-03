import soccerdata as sd
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
import os
import logging
import argparse
import sys
from pathlib import Path


#### LOGGING ####
LOG_FOLDER = "logs/"
LOG_FILE_NAME = "SOFIFA_teams_stats_table.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

try:
    root_path = Path(__file__).resolve().parents[2]
    print(f'__file__ root file: {root_path}')
except NameError:
    root_path = Path(os.getcwd()).resolve().parents[1]
    print(f'os.getcwd() root file: {root_path}')

#print(f'__main__ {__main__})

filename = root_path / LOG_FOLDER / LOG_FILE_NAME
logger = logging.getLogger("SOFIFA_teams_stats_table__loger")
file_handler = logging.FileHandler(filename)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter(LOG_FORMAT)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def scrap_data_SOFIFA(teams='big 5', use_cache=False, scrap_all=False, KEY_1='team', KEY_2='update'):
    """Recuperer les donnees des equipes de SoFIFA"""
    try:
        logger.info(f"Chargement des donnees des equipes {teams} - latest")
        so_fifa_latest = sd.SoFIFA(versions="latest", no_cache=not use_cache)
        team_ratings = so_fifa_latest.read_team_ratings() if teams == 'big 5' else so_fifa_latest.read_team_ratings_nationals()
        if scrap_all:
            logger.info(f"Chargement des donnees des equipes {teams} - all")
            sofifa_all = sd.SoFIFA(versions="all", no_cache=True)
            team_ratings_all = sofifa_all.read_team_ratings() if teams == 'big 5' else sofifa_all.read_team_ratings_nationals()
            team_ratings = pd.concat([team_ratings_all, team_ratings], ignore_index=True)
            team_ratings = team_ratings.drop_duplicates(subset=[KEY_1, KEY_2], keep='last')
        team_ratings.reset_index(inplace=True)
        return team_ratings
    except Exception as e:
        logger.error(f"Erreur lors du chargement des donnees des equipes {teams} : {e}")
        return


def convert_data_types(team_ratings, team_ratings_nat):
    """Convertir les types de donnees"""
    logger.info("Conversion des types de donnees")
    try: 
        team_ratings_nat["league"] = "INT"
        team_ratings_nat.loc[team_ratings_nat["update"] == "World Cup 2022", "update"] = "Nov 20, 2022"
        team_ratings = pd.concat([team_ratings, team_ratings_nat], ignore_index=True)

        # Convertir les types de donnees
        team_ratings['update'] = pd.to_datetime(team_ratings['update'])
        team_ratings["overall"] = team_ratings["overall"].astype(int)
        team_ratings["attack"] = team_ratings["attack"].astype(int)
        team_ratings["midfield"] = team_ratings["midfield"].astype(int)
        team_ratings["defence"] = team_ratings["defence"].astype(int)
        team_ratings["transfer_budget"] = team_ratings["transfer_budget"].str.replace("€", "").str.replace("M", "0000").str.replace("K", "000").str.replace(".", "").astype(int)
        team_ratings["club_worth"] = team_ratings["club_worth"].str.replace("€", "").str.replace("M", "0000").str.replace("K", "000").str.replace("B", "000000000").str.replace(".", "").astype(float)
        team_ratings["defence_domestic_prestige"] = team_ratings["defence_domestic_prestige"].astype(int)
        team_ratings["international_prestige"] = team_ratings["international_prestige"].astype(int)
        team_ratings["players"] = team_ratings["players"].astype(int)
        team_ratings["starting_xi_average_age"] = team_ratings["starting_xi_average_age"].astype(float)
        team_ratings["whole_team_average_age"] = team_ratings["whole_team_average_age"].astype(float)
        team_ratings.sort_values('update', ascending=False)
        return team_ratings
    
    except Exception as e:
        logger.error(f"Erreur lors de la conversion des types de donnees: {e}")
        return


def insert_data_SOFIFA_teams_stats_table(use_cache=False, scrap_all=False):
    """Inserer les donnees des equipes de SoFIFA dans la table SOFIFA teams stats"""

    logger.info("--- Debut de l'insertion des donnees dans la table SOFIFA teams stats")

    #### VARIABLES ####
    load_dotenv()
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_TN_SOFIFA_TEAMS_STATS = os.getenv('DB_TN_SOFIFA_TEAMS_STATS')
    KEY_1 = 'team'
    KEY_2 = 'update'
    DN_TN_TEMP_TABLE = 'temp_table'


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
    logger.info("Chargement des donnees de SoFIFA")
    logger.info(f"use_cache: {use_cache}")
    logger.info(f"scrap_all: {scrap_all}")
    team_ratings = scrap_data_SOFIFA(teams='big 5', use_cache=use_cache, scrap_all=scrap_all, KEY_1=KEY_1, KEY_2=KEY_2)
    team_ratings_nat = scrap_data_SOFIFA(teams='international', use_cache=use_cache, scrap_all=scrap_all, KEY_1=KEY_1, KEY_2=KEY_2)


    #### CONVERSION DES TYPES DE DONNEES ####
    team_ratings = convert_data_types(team_ratings, team_ratings_nat)


    #### INSERTION DES DONNEES DANS LA BASE DE DONNEES ####
    logger.info("Insertion des donnees dans la base de donnees")
    try:
        with engine.connect() as conn:
            team_ratings.to_sql(DN_TN_TEMP_TABLE, conn, if_exists='replace', index=False)

            # Liste des colonnes
            columns = ', '.join(team_ratings.columns)
            
            # Inserer les donnees en evitant les doublons
            insert_query = f"""
            INSERT INTO {DB_TN_SOFIFA_TEAMS_STATS} ({columns})
            SELECT {columns}
            FROM {DN_TN_TEMP_TABLE}
            ON CONFLICT ({KEY_1}, {KEY_2}) DO NOTHING
            """
            logger.info("Insertion des nouvelles donnees en cours...")
            conn.execute(text(insert_query))

            # Compter le nombre de nouvelles lignes inserees
            count_query = f"""
            SELECT COUNT(*) FROM {DN_TN_TEMP_TABLE}
            WHERE NOT EXISTS (
                SELECT 1 FROM {DB_TN_SOFIFA_TEAMS_STATS}
                WHERE {DB_TN_SOFIFA_TEAMS_STATS}.{KEY_1} = {DN_TN_TEMP_TABLE}.{KEY_1}
                AND {DB_TN_SOFIFA_TEAMS_STATS}.{KEY_2} = {DN_TN_TEMP_TABLE}.{KEY_2}
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
    
    logger.info("Fin de l'insertion des donnees dans la table SOFIFA teams stats\n\n")

#if __name__ == "__main__":
parser = argparse.ArgumentParser(description='Insert SOFIFA teams stats into the database.')
parser.add_argument('--use_cache', type=bool, default=False, help='Use cache for the latest data')
parser.add_argument('--scrap_all', type=bool, default=False, help='Scrap all data versions')

args = parser.parse_args()
use_cache = args.use_cache
scrap_all = args.scrap_all

insert_data_SOFIFA_teams_stats_table(use_cache=use_cache, scrap_all=scrap_all)
    