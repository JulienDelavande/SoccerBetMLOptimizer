import argparse
import datetime
import gc
import hashlib
import logging

import optibet_lib.soccerdata as sd
import pandas as pd
from sqlalchemy import text

from app._config import DB_TN_FBREF_RESULTS, engine
from app.insert_data.utils import get_all_seasons_string

#### VARIABLES ####
KEY_1 = "game"
DB_TN_TEMP_TABLE = "temp_table_fbref_results"
logger = logging.getLogger("sofifa_teams_stats")
pd.set_option("display.max_columns", None)
SLEEP_TIME = 5  # Default sleep time in seconds to avoid rate limiting

# Configuration des ligues
LEAGUES_CONFIG = [
    {
        "name": "FIFA Club World Cup",
        "first_season": "2526",
        "skip_seasons": None,
        "step": 1,
    },
    {
        "name": "UEFA Champions League",
        "first_season": "9091",
        "skip_seasons": ["3940", "4041", "4142", "4243", "4344", "4546"],
        "step": 1,
    },
    {
        "name": "INT-World Cup",
        "first_season": "3031",
        "skip_seasons": ["4243", "4344", "4647"],
        "step": 4,
    },
    {
        "name": "INT-European Championships",
        "first_season": "0001",
        "skip_seasons": None,
        "step": 4,
    },
    {
        "name": "Big 5 European Leagues Combined",
        "first_season": "3031",
        "skip_seasons": ["3940", "4041", "4142", "4243", "4344", "4445", "4546"],
        "step": 1,
    },
]


def insert_recent_fbref_matches(
    get_current_season_only=True, use_cache=True, cutoff_days=7, leagues=None
):
    """
    Insère les données FBref en traitant chaque ligue séparément pour optimiser la mémoire.
    Chaque ligue est scrappée, convertie et insérée avant de passer à la suivante.
    """
    logger.info("--- Debut de l'insertion des donnees dans la table fbref_results")
    logger.info(f"get_current_season_only: {get_current_season_only}")
    logger.info(f"use_cache: {use_cache}")
    logger.info(f"cutoff_days: {cutoff_days}")

    cutoff_date = datetime.date.today() - datetime.timedelta(days=cutoff_days)

    # Suppression des anciennes données une seule fois au début
    try:
        with engine.begin() as conn:
            logger.info(
                f"Suppression des anciens matchs dans la table {DB_TN_FBREF_RESULTS} pour les dates ≥ {cutoff_date}"
            )
            conn.execute(
                text(f"""
                DELETE FROM {DB_TN_FBREF_RESULTS}
                WHERE date >= :cutoff
            """),
                {"cutoff": cutoff_date},
            )
        logger.info(
            f"Anciennes données supprimées avec succès pour les dates ≥ {cutoff_date}"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des anciennes données: {e}")
        raise

    # Récupérer les infos des ligues une seule fois
    try:
        fbref_reader = sd.FBref()
        leagues_df = fbref_reader.read_leagues()
        del fbref_reader
        gc.collect()
    except Exception as e:
        logger.error(f"Erreur lors du chargement des infos de ligues: {e}")
        raise

    total_inserted = 0
    last_df = None  # Pour retourner le dernier DataFrame (compatibilité)

    # Traiter chaque ligue séparément pour économiser la mémoire
    for config in LEAGUES_CONFIG:
        league = config["name"]
        try:
            logger.info(f"=== Traitement de la ligue: {league} ===")

            # 1. Scrapper la ligue
            df = scrap_single_league(
                league=league,
                first_season=config["first_season"],
                skip_seasons=config["skip_seasons"],
                step=config["step"],
                leagues_df=leagues_df,
                get_current_season_only=get_current_season_only,
                use_cache=use_cache,
            )

            if df is None or df.empty:
                logger.info(f"Aucune donnée pour {league}, passage à la suivante")
                continue

            # 2. Convertir les types
            df = convert_data_types_fbref(df)

            # 3. Insérer dans la DB
            inserted = insert_dataframe_to_db(df)
            total_inserted += inserted

            last_df = df

            # 4. Libérer la mémoire
            del df
            gc.collect()
            logger.info(f"Mémoire libérée après traitement de {league}")

        except Exception as e:
            logger.error(f"Erreur lors du traitement de {league}: {e}")
            continue

    logger.info(
        f"=== Fin de l'insertion: {total_inserted} lignes insérées au total ==="
    )

    # Retourner le dernier DataFrame pour compatibilité avec l'API existante
    return last_df if last_df is not None else pd.DataFrame()


def scrap_single_league(
    league,
    first_season,
    skip_seasons,
    step,
    leagues_df,
    get_current_season_only=True,
    use_cache=True,
):
    """Scrapper une seule ligue pour économiser la mémoire"""
    try:
        logger.info(f"Chargement des donnees des matchs {league}")

        if league not in leagues_df.index:
            logger.warning(f"Ligue {league} non trouvée dans les données FBref")
            return None

        last_season = leagues_df.loc[league, "last_season"]
        seasons = get_all_seasons_string(
            first_season, last_season, step=step, skip_seasons=skip_seasons
        )

        if get_current_season_only:
            seasons = [seasons[-1]]

        if not seasons:
            return None

        fbref = sd.FBref(
            leagues=[league],
            seasons=seasons,
            no_cache=not use_cache,
            sleep_time=SLEEP_TIME,
        )
        df = fbref.read_schedule(force_cache=use_cache)

        if df is not None:
            df = df.reset_index()
            logger.info(f"Nombre de matchs recuperes pour {league}: {df.shape[0]}")

        # Libérer le reader
        del fbref
        gc.collect()

        return df

    except Exception as e:
        logger.error(
            f"Erreur lors du chargement des donnees des matchs pour {league}: {e}"
        )
        return None


def insert_dataframe_to_db(df):
    """Insérer un DataFrame dans la base de données"""
    if df is None or df.empty:
        return 0

    try:
        with engine.begin() as conn:
            df.to_sql(DB_TN_TEMP_TABLE, con=conn, index=False, if_exists="replace")

            columns = ", ".join(df.columns)
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
            logger.info(
                f"{inserted_rows} nouvelles lignes insérées dans {DB_TN_FBREF_RESULTS}"
            )
            conn.execute(text(f"DROP TABLE {DB_TN_TEMP_TABLE}"))

        return inserted_rows

    except Exception as e:
        logger.error(f"Erreur lors de l'insertion des donnees: {e}")
        raise


def convert_data_types_fbref(fbref_df):
    """Convertir les types de donnees"""
    logger.info("Conversion des types de donnees")
    try:
        fbref_df = fbref_df.reset_index()
        fbref_df["date"] = pd.to_datetime(fbref_df["date"])
        fbref_df["time"] = pd.to_datetime(fbref_df["time"], errors="coerce").dt.time
        fbref_df["time"] = fbref_df["time"].apply(lambda x: None if pd.isna(x) else x)
        fbref_df["index"] = fbref_df["game"].apply(
            lambda x: int(hashlib.sha256(x.encode()).hexdigest()[:6], 16)
        )
        fbref_df["home_g"] = fbref_df["score"].apply(
            lambda x: x.split("–")[0][-1] if not pd.isna(x) else x
        )
        fbref_df["away_g"] = fbref_df["score"].apply(
            lambda x: x.split("–")[1][0] if not pd.isna(x) else x
        )
        fbref_df["home_sat"] = fbref_df["score"].apply(
            lambda x: x.split("–")[0].split("(")[1][0]
            if not pd.isna(x) and "(" in x
            else pd.NA
        )
        fbref_df["away_sat"] = fbref_df["score"].apply(
            lambda x: x.split("–")[1].split("(")[1][0]
            if not pd.isna(x) and "(" in x
            else pd.NA
        )
        fbref_df["home_g"] = pd.to_numeric(fbref_df["home_g"], errors="coerce")
        fbref_df["away_g"] = pd.to_numeric(fbref_df["away_g"], errors="coerce")
        fbref_df["home_sat"] = pd.to_numeric(fbref_df["home_sat"], errors="coerce")
        fbref_df["away_sat"] = pd.to_numeric(fbref_df["away_sat"], errors="coerce")

        # logger.info(f"Head of fbref data after conversion: \n{fbref_df.head()}")
        logger.info(f"Number of rows: {fbref_df.shape[0]}")

        return fbref_df

    except Exception as e:
        logger.error(f"Erreur lors de la conversion des types de donnees: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Insert fbref results into the database"
    )
    parser.add_argument(
        "--get_current_season_only",
        type=bool,
        default=True,
        help="Scrap only the last season",
    )
    parser.add_argument("--use_cache", type=bool, default=False, help="Use cached data")
    parser.add_argument(
        "--cutoff_days",
        type=int,
        default=7,
        help="Number of days to consider for recent matches",
    )
    parser.add_argument(
        "--leagues",
        type=str,
        nargs="*",
        default=None,
        help="List of leagues to scrape (default: None, which scrapes all leagues)",
    )

    args = parser.parse_args()
    get_current_season_only = args.get_current_season_only
    use_cache = args.use_cache
    leagues = args.leagues
    get_current_season_only = False
    use_cache = True
    leagues = None
    cutoff_days = 60

    insert_recent_fbref_matches(
        get_current_season_only=get_current_season_only,
        use_cache=use_cache,
        cutoff_days=cutoff_days,
        leagues=leagues,
    )
