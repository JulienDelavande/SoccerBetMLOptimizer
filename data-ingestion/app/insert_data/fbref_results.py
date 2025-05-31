import soccerdata as sd
from sqlalchemy import text
import pandas as pd
import argparse
import datetime
import hashlib
import logging

from app._config import DB_TN_FBREF_RESULTS
from app._config import engine
from app.insert_data.utils import get_all_seasons_string


#### VARIABLES ####
KEY_1 = 'game'
DB_TN_TEMP_TABLE = 'temp_table_fbref_results'
logger = logging.getLogger("sofifa_teams_stats")
pd.set_option('display.max_columns', None)

def insert_recent_fbref_matches(get_current_season_only=True, use_cache=True, cutoff_days=7):
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

    cutoff_date = datetime.date.today() - datetime.timedelta(days=cutoff_days)
    
    try:
        with engine.begin() as conn:
            logger.info(f"Suppression des anciens matchs dans la table {DB_TN_FBREF_RESULTS} pour les dates ≥ {cutoff_date}")
            conn.execute(text(f"""
                DELETE FROM {DB_TN_FBREF_RESULTS}
                WHERE date >= :cutoff
            """), {"cutoff": cutoff_date})
        logger.info(f"Anciennes données supprimées avec succès pour les dates ≥ {cutoff_date}")
        logger.info(f"Insertion des nouveaux matchs dans la table {DB_TN_FBREF_RESULTS} pour les dates ≥ {cutoff_date}")

        # with engine.begin() as conn:
        #     fbref_df.to_sql(DB_TN_FBREF_RESULTS, con=conn, if_exists="append", index=False) ## TO MODIFY

        with engine.begin() as conn:
            fbref_df.to_sql(DB_TN_TEMP_TABLE, con=conn, index=False, if_exists="replace")

            columns = ', '.join(fbref_df.columns)
            insert_query = f"""
                WITH inserted_rows AS (
                    INSERT INTO {DB_TN_FBREF_RESULTS} ({columns})
                    SELECT {columns}
                    FROM {DB_TN_TEMP_TABLE}
                    WHERE game IS NOT NULL AND date IS NOT NULL
                    ON CONFLICT ({KEY_1}) DO NOTHING
                    RETURNING {KEY_1}
                )
                SELECT COUNT(*) AS inserted_rows_count FROM inserted_rows;
            """

            result = conn.execute(text(insert_query))
            inserted_rows = result.scalar()
            logger.info(f"{inserted_rows} nouvelles lignes insérées dans {DB_TN_FBREF_RESULTS}")
            conn.execute(text(f"DROP TABLE {DB_TN_TEMP_TABLE}"))
            logger.info(f"Table temporaire {DB_TN_TEMP_TABLE} supprimée avec succès")


        logger.info(f"Table {DB_TN_FBREF_RESULTS} mise à jour avec succès")

    except Exception as e:
        logger.error(f"Erreur lors de l'insertion des donnees: {e}")
        raise
    logger.info(f"Fin de l'insertion des donnees dans la table {DB_TN_FBREF_RESULTS}")

    return fbref_df


def scrap_data_fbref(get_current_season_only=True, use_cache=True):
    """Recuperer les schedule et scores des matchs de fbref"""
    try:
        fbref = sd.FBref()
        leagues = ["UEFA Champions League", "INT-World Cup", "INT-European Championships", "Big 5 European Leagues Combined"]
        first_seasons = ["9091", "3031", "0001", "3031"]
        skip_seasons = [['3940', '4041', '4142', '4243', '4344', '4546'], ['4243', '4344', '4647'], None, ['3940', '4041', '4142', '4243', '4344', '4546']]  # Seasons to skip due to WWII
        steps = [1, 4, 4, 1]  # Steps for each league to get the first season
        leagues_df = fbref.read_leagues()

        dfs_fbref = []
        for i, league in enumerate(leagues):
            logger.info(f"Chargement des donnees des matchs {league}")
            first_season = first_seasons[i]
            last_season = leagues_df.loc[league, 'last_season']
            seasons = get_all_seasons_string(first_season, last_season, step=steps[i], skip_seasons=skip_seasons[i])
            if get_current_season_only:
                seasons = [seasons[-1]]
            fbref = sd.FBref(leagues=[league], seasons=seasons)
            df = fbref.read_schedule(force_cache=use_cache) if seasons else None
            df = df.reset_index() if df is not None else None
            logger.info(f"Nombre de matchs recuperes pour {league}: {df.shape[0] if df is not None else 0}")
            dfs_fbref.append(df) if df is not None else None
        fbref_df = pd.concat(dfs_fbref, ignore_index=True) if dfs_fbref else pd.DataFrame()
        logger.info(f"Nombre de matchs recuperes: {fbref_df.shape[0]}")
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
        fbref_df['time']     = fbref_df['time'].apply(lambda x: None if pd.isna(x) else x)
        fbref_df['index']    = fbref_df['game'].apply(lambda x: int(hashlib.sha256(x.encode()).hexdigest()[:6], 16))
        fbref_df['home_g']   = fbref_df['score'].apply(lambda x: x.split('–')[0][-1] if not pd.isna(x) else x)
        fbref_df['away_g']   = fbref_df['score'].apply(lambda x: x.split('–')[1][0] if not pd.isna(x) else x)
        fbref_df['home_sat'] = fbref_df['score'].apply(lambda x: x.split('–')[0].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
        fbref_df['away_sat'] = fbref_df['score'].apply(lambda x: x.split('–')[1].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
        fbref_df['home_g']   = pd.to_numeric(fbref_df['home_g'], errors='coerce')
        fbref_df['away_g']   = pd.to_numeric(fbref_df['away_g'], errors='coerce')
        fbref_df['home_sat'] = pd.to_numeric(fbref_df['home_sat'], errors='coerce')
        fbref_df['away_sat'] = pd.to_numeric(fbref_df['away_sat'], errors='coerce')

        #logger.info(f"Head of fbref data after conversion: \n{fbref_df.head()}")
        logger.info(f"Number of rows: {fbref_df.shape[0]}")

        return fbref_df
    
    except Exception as e:
        logger.error(f"Erreur lors de la conversion des types de donnees: {e}")
        raise



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Insert fbref results into the database')
    parser.add_argument('--get_current_season_only', type=bool, default=True, help='Scrap only the last season')
    parser.add_argument('--use_cache', type=bool, default=True, help='Use cached data')
    parser.add_argument('--cutoff_days', type=int, default=7, help='Number of days to consider for recent matches')

    args = parser.parse_args()
    get_current_season_only = args.get_current_season_only
    use_cache = args.use_cache

    insert_recent_fbref_matches(get_current_season_only=get_current_season_only, use_cache=use_cache, cutoff_days=args.cutoff_days)
    