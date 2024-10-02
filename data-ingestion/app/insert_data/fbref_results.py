import soccerdata as sd
from sqlalchemy import text
import pandas as pd
import argparse
import datetime
import hashlib
import logging

from app._config import DB_TN_FBREF_RESULTS
from app._config import engine


#### VARIABLES ####
DN_TN_TEMP_TABLE = 'temp_table'
KEY = 'game'
KEY_BIS = 'score'
logger = logging.getLogger("sofifa_teams_stats")
pd.set_option('display.max_columns', None)


def scrap_data_fbref(get_current_season_only=True, use_cache=True):
    """Recuperer les schedule et scores des matchs de fbref"""
    try:
        current_date = datetime.datetime.now()
        current_year = datetime.datetime.now().year

        logger.info(f"Chargement des donnees des matchs INT-World Cup")
        leagues = ["INT-World Cup"]
        seasons = [f"{str(year)}-{str(year+1)[2:]}" for year in range(1930, current_year+1, 4)]
        [seasons.remove(f"{str(year)}-{str(year+1)[2:]}") for year in range(1942, 1948, 4)]
        if get_current_season_only:
            current_season_int = f"{current_year}-{str(current_year+1)[2:]}"
            seasons = [current_season_int] if current_season_int in seasons else []
        fbref = sd.FBref(leagues=leagues, seasons=seasons)
        matches_wc = fbref.read_schedule(force_cache=use_cache) if seasons else None
        matches_wc = matches_wc.reset_index() if matches_wc is not None else None

        logger.info(f"Chargement des donnees des matchs INT-European Championships")
        leagues = ['INT-European Championships']
        seasons = list(range(2000, current_year+1, 4))
        if get_current_season_only:
            seasons = [current_year] if current_year in seasons else []
        fbref = sd.FBref(leagues=leagues, seasons=seasons)
        euro_schedule = fbref.read_schedule(force_cache=use_cache) if seasons else None
        euro_schedule = euro_schedule.reset_index() if euro_schedule is not None else None

        logger.info(f"Chargement des donnees des matchs Big 5 European Leagues Combined")
        leagues = ["Big 5 European Leagues Combined"]
        # Determine the correct season depending on the current date
        if current_date.month < 8:  # Before August
            current_season_big5 = f"{str(current_year-1)[2:]}-{str(current_year)[2:]}"
        else:  # August or later
            current_season_big5 = f"{str(current_year)[2:]}-{str(current_year+1)[2:]}"
        if get_current_season_only:
            seasons = [current_season_big5]
        else:
            seasons = [f"{str(year)[2:]}-{str(year+1)[2:]}" for year in range(1930, current_year+1)]
            [seasons.remove(f"{str(year)[2:]}-{str(year+1)[2:]}") for year in range(1939, 1946)]
        fbref = sd.FBref(leagues=leagues, seasons=seasons)
        big5 = fbref.read_schedule(force_cache=use_cache) if seasons else None
        big5 = big5.reset_index() if big5 is not None else None


        fbref_df = pd.concat([matches_wc, euro_schedule, big5], ignore_index=True)
        logger.info(f"Head of fbref scrapped data: \n{fbref_df.head()}")

        return fbref_df
    except Exception as e:
        logger.error(f"Erreur lors du chargement des donnees des matchs fbref: {e}")
        raise


def convert_data_types_fbref(fbref_df):
    """Convertir les types de donnees"""
    logger.info("Conversion des types de donnees")
    try: 
        fbref_df             = fbref_df.reset_index()
        fbref_df['date']     = pd.to_datetime(fbref_df['date'])
        fbref_df['time']     = pd.to_datetime(fbref_df['time'], errors='coerce').dt.time
        fbref_df['time'] = fbref_df['time'].apply(lambda x: None if pd.isna(x) else x)
        fbref_df['index']    = fbref_df['game'].apply(lambda x: int(hashlib.sha256(x.encode()).hexdigest()[:6], 16))
        fbref_df['home_g']   = fbref_df['score'].apply(lambda x: x.split('–')[0][-1] if not pd.isna(x) else x)
        fbref_df['away_g']   = fbref_df['score'].apply(lambda x: x.split('–')[1][0] if not pd.isna(x) else x)
        fbref_df['home_sat'] = fbref_df['score'].apply(lambda x: x.split('–')[0].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
        fbref_df['away_sat'] = fbref_df['score'].apply(lambda x: x.split('–')[1].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
        fbref_df['home_g']   = pd.to_numeric(fbref_df['home_g'], errors='coerce')
        fbref_df['away_g']   = pd.to_numeric(fbref_df['away_g'], errors='coerce')
        fbref_df['home_sat'] = pd.to_numeric(fbref_df['home_sat'], errors='coerce')
        fbref_df['away_sat'] = pd.to_numeric(fbref_df['away_sat'], errors='coerce')

        logger.info(f"Head of fbref data after conversion: \n{fbref_df.head()}")
        logger.info(f"Number of rows: {fbref_df.shape[0]}")

        return fbref_df
    
    except Exception as e:
        logger.error(f"Erreur lors de la conversion des types de donnees: {e}")
        raise


def insert_data_fbref_results_table(get_current_season_only=True, use_cache=True):
    """Inserer les donnees des matchs de fbref dans la table fbref_results"""

    logger.info(f"--- Debut de l'insertion des donnees dans la table fbref_results")


    #### SCRAPPING SOFIFA TEAMS DATA ####
    logger.info("Chargement des donnees de Fbref")
    logger.info(f"get_current_season_only: {get_current_season_only}")
    logger.info(f"use_cache: {use_cache}")
    fbref_df = scrap_data_fbref(get_current_season_only=get_current_season_only, use_cache=use_cache)


    #### CONVERSION DES TYPES DE DONNEES ####
    fbref_df = convert_data_types_fbref(fbref_df)


    #### INSERTION DES DONNEES DANS LA BASE DE DONNEES ####
    logger.info("Insertion des donnees dans la base de donnees")
    logger.info(f"BD_HOST: {engine.url.host}")
    logger.info(f"BD_PORT: {engine.url.port}")
    logger.info(f"BD_NAME: {engine.url.database}")
    try:
        with engine.begin() as conn:
            fbref_df.to_sql(DN_TN_TEMP_TABLE, conn, if_exists='replace', index=False)
            logger.info(f"Table {DN_TN_TEMP_TABLE} creee avec succes")

    # Première requête : Mise à jour des lignes existantes
        with engine.begin() as conn:
            # Liste des colonnes pour la mise à jour
            update_columns = ', '.join([f"{col} = temp.{col}" for col in fbref_df.columns])

            # Requête pour mettre à jour les lignes
            update_query = f"""
            WITH updated_rows AS (
                UPDATE {DB_TN_FBREF_RESULTS} t
                SET {update_columns}
                FROM {DN_TN_TEMP_TABLE} temp
                WHERE t.{KEY} = temp.{KEY}
                AND COALESCE(t.{KEY_BIS}, 'valeur_par_defaut') <> COALESCE(temp.{KEY_BIS}, 'valeur_par_defaut')
                RETURNING t.{KEY}
            )
            SELECT COUNT(*) AS updated_rows FROM updated_rows;
            """

            # Exécution de la requête de mise à jour
            result = conn.execute(text(update_query))
            updated_rows = result.scalar()  # Compte des lignes mises à jour

            logger.info(f"Update des lignes existantes dans la table {DB_TN_FBREF_RESULTS} avec succes")
            logger.info(f"{updated_rows} lignes mises à jour")

        # Deuxième requête : Insertion des nouvelles lignes
        with engine.begin() as conn:
            # Liste des colonnes pour l'insertion
            columns = ', '.join(fbref_df.columns)

            # Requête pour insérer les nouvelles lignes
            insert_query = f"""
            WITH inserted_rows AS (
                INSERT INTO {DB_TN_FBREF_RESULTS} ({columns})
                SELECT {columns}
                FROM {DN_TN_TEMP_TABLE} temp
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM {DB_TN_FBREF_RESULTS} t
                    WHERE t.{KEY} = temp.{KEY}
                )
                RETURNING {KEY}
            )
            SELECT COUNT(*) AS inserted_rows FROM inserted_rows;
            """

            # Exécution de la requête d'insertion
            result = conn.execute(text(insert_query))
            inserted_rows = result.scalar()  # Compte des lignes insérées

            logger.info(f"Insertion des nouvelles donnees en cours dans la table {DB_TN_FBREF_RESULTS} avec succes")
            logger.info(f"{inserted_rows} nouvelles lignes insérées")

        # Suppression de la table temporaire après les opérations
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE {DN_TN_TEMP_TABLE}"))
            logger.info(f"Table {DN_TN_TEMP_TABLE} supprimée avec succès")

    except Exception as e:
        logger.error(f"Erreur lors de l'insertion des donnees: {e}")
        raise
    
    logger.info(f"Fin de l'insertion des donnees dans la table {DB_TN_FBREF_RESULTS}\n\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Insert fbref results into the database')
    parser.add_argument('--get_current_season_only', type=bool, default=True, help='Scrap only the last season')
    parser.add_argument('--use_cache', type=bool, default=True, help='Use cached data')

    args = parser.parse_args()
    get_current_season_only = args.get_current_season_only
    use_cache = args.use_cache

    insert_data_fbref_results_table(get_current_season_only=get_current_season_only, use_cache=use_cache)
    