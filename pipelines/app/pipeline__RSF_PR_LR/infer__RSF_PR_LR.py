import logging
import argparse
import datetime
import time

import pandas as pd
from sqlalchemy import text
import numpy as np

from .utils.test_model_and_infer import test_model_and_infer
from .utils.insert_results_to_db import insert_results_to_db
from optibet_lib.feature_eng.format_df import merge_sofifa_fbref_results, format_sofifa_fbref_data, add_signals
from app._config import DB_TN_FBREF_RESULTS, DB_TN_SOFIFA_TEAMS_STATS, DB_TN_MODELS_RESULTS
from app._config import engine


#### settings ####
logger = logging.getLogger("RSF_PR_LR")

def infer__RSF_PR_LR__pipeline(datetime_stop=None):
    """
    Inference pipeline for LR model. Data is retrieved from the database, processed, the model is trained and tested, and the results are inserted back into the database.
    
    Parameters
    ----------
    datetime_stop : datetime.datetime, optional
        The date of the match to stop training and start the inference, by default None (today at 00:00:00)
    
    Returns
    -------
    train_test_metrics : pd.DataFrame
        The metrics of the model on the train and test set
    fbref_results_df__sofifa_merged__data_formated__signals_added__infered : pd.DataFrame
        The results of the model on the inference set
     """
    
    start_pipeline = time.time()
    logger.info("---- Starting the inference pipeline")
    datetime_stop = datetime_stop if datetime_stop else datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if datetime_stop.tzinfo is not None:
        datetime_stop = datetime_stop.replace(tzinfo=None)
    logger.info(f"datetime_stop: {datetime_stop}")


    #### Connection to the database and retrieve data ####
    start_data_retrieval = time.time()
    try:
        with engine.connect() as connection:
            logger.info("Database connection established")
            logger.info(f"DB_HOST: {engine.url.host}")
            logger.info(f"DB_PORT: {engine.url.port}")
            logger.info(f"DB_NAME: {engine.url.database}")

            # Refresh materialized view to get the latest data
            connection.execute(text("REFRESH MATERIALIZED VIEW mv_sofifa_stats_norm;"))
            connection.execute(text("REFRESH MATERIALIZED VIEW mv_sofifa_stats_filtered;"))
            connection.execute(text("REFRESH MATERIALIZED VIEW mv_fbref_matches_norm;"))
            connection.execute(text("REFRESH MATERIALIZED VIEW mv_fbref_matches_norm_2006;"))
            connection.execute(text("REFRESH MATERIALIZED VIEW mv_fbref_matches_filtered;"))

            query_mv_matchs_enriched = text(f"SELECT * FROM v_matches_enrichis;")
            fbref_results_df__sofifa_merged = pd.read_sql(query_mv_matchs_enriched, connection)
            logger.info(f"Data retrieved from database successfully in {time.time() - start_data_retrieval} seconds")
    except Exception as e:
        logger.error(f"Error retrieving data from the database: {e}")
        raise


    #### Data processing ####
    start_data_processing = time.time()
    try:
        if fbref_results_df__sofifa_merged.empty:
            logger.warning("No data retrieved from the database, exiting the pipeline")
            return pd.DataFrame(), pd.DataFrame(), 0, None, None, datetime.datetime.now()
        
        fbref_results_df__sofifa_merged['home_team'] = fbref_results_df__sofifa_merged['home_team_canonical_name']
        fbref_results_df__sofifa_merged['away_team'] = fbref_results_df__sofifa_merged['away_team_canonical_name']
        fbref_results_df__sofifa_merged__data_formated = format_sofifa_fbref_data(fbref_results_df__sofifa_merged, datetime_stop=datetime_stop)
        fbref_results_df__sofifa_merged__data_formated__signals_added = add_signals(fbref_results_df__sofifa_merged__data_formated, datetime_stop=datetime_stop)

        rule_is_before_datetime = fbref_results_df__sofifa_merged__data_formated__signals_added["datetime"] < datetime_stop
        fbref_results_df__sofifa_merged__data_formated__signals_added__train = fbref_results_df__sofifa_merged__data_formated__signals_added[rule_is_before_datetime]
        fbref_results_df__sofifa_merged__data_formated__signals_added__infer = fbref_results_df__sofifa_merged__data_formated__signals_added[~rule_is_before_datetime]

        logger.info(f"Data processing completed successfully in {time.time() - start_data_processing} seconds")
        logger.info(f"Number of matches in train set: {fbref_results_df__sofifa_merged__data_formated__signals_added__train.shape[0]}")
        logger.info(f"Number of matches in inference set: {fbref_results_df__sofifa_merged__data_formated__signals_added__infer.shape[0]}")
    except Exception as e:
        logger.error(f"Error during data processing: {e}")
        raise

    #### Train and test the model and infer the results ####
    start_train_test_inference = time.time()
    try:
        train_test_metrics, fbref_results_df__sofifa_merged__data_formated__signals_added__infered = test_model_and_infer(
            fbref_results_df__sofifa_merged__data_formated__signals_added__train, 
            fbref_results_df__sofifa_merged__data_formated__signals_added__infer
        )
        logger.info(f"Model training and inference completed successfully completed in {time.time() - start_train_test_inference} seconds, accuray on train test : {train_test_metrics}")
    except Exception as e:
        logger.error(f"Error during model training and inference: {e}")
        raise


    #### Insert the results into the database ####
    start_insert_results = time.time()
    try:
        datetime_inference = insert_results_to_db(engine, fbref_results_df__sofifa_merged__data_formated__signals_added__infered, DB_TN_MODELS_RESULTS)
        matchs_infered = fbref_results_df__sofifa_merged__data_formated__signals_added__infered.shape[0]
        logger.info(f"{matchs_infered} results inserted into the database successfully, completed in {time.time() - start_insert_results} seconds")
    except Exception as e:
        logger.error(f"Error inserting results into the database: {e}")
        raise

    #### Calculate some metrics ####
    try:
        df_infered = fbref_results_df__sofifa_merged__data_formated__signals_added__infered
        nb_matches_infered = df_infered.shape[0]
        df_infered['time_match'] = df_infered['time_match'].replace([None, np.nan], '00:00:00')
        df_infered['datetime_match'] = pd.to_datetime(df_infered['date_match'].astype(str) + ' ' + df_infered['time_match'].astype(str))
        first_match_name = df_infered[df_infered['datetime_match'] == df_infered['datetime_match'].min()].iloc[0]['game']
        last_match_name = df_infered[df_infered['datetime_match'] == df_infered['datetime_match'].max()].iloc[0]['game']
        logger.info(f"Pipeline completed in {time.time() - start_pipeline} seconds")
        train_test_metrics_dict = train_test_metrics.to_dict(orient="records") if hasattr(train_test_metrics, "to_dict") else train_test_metrics
        logger.info(f"--- OF pipeline completed in {time.time() - start_pipeline:.2f} seconds ---")
        return train_test_metrics_dict, fbref_results_df__sofifa_merged__data_formated__signals_added__infered, nb_matches_infered, first_match_name, last_match_name, datetime_inference
    except Exception as e:
        logger.warning(f"Error calculating metrics: {e}")
        return train_test_metrics, fbref_results_df__sofifa_merged__data_formated__signals_added__infered, None, None, None, datetime_inference
        

if __name__ == "__main__":
    start_time = time.time()

    args = argparse.ArgumentParser()
    args.add_argument("--datetime_stop", type=str, default="2025-09-11 00:00:00", 
                      help="Date to stop the training and start the inference, format: YYYY-MM-DD HH:MM:SS. Default is '2025-07-05 00:00:00'")
    args = args.parse_args()

    #datetime_stop = None
    if args.datetime_stop:
        try:
            datetime_stop = datetime.datetime.strptime(args.datetime_stop, "%Y-%m-%d %H:%M:%S")
            logger.info(f"datetime_stop parameter parsed successfully: {datetime_stop}")
        except ValueError as e:
            logger.error(f"Error parsing datetime_stop parameter: {e}")
            raise

    try:
        train_test_metrics, df_infered, nb_matches_infered, first_match_name, last_match_name, datetime_inference = infer__RSF_PR_LR__pipeline(datetime_stop=datetime_stop)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Pipeline executed successfully in {duration:2f} seconds \n\n")
    except Exception as e:
        logger.error(f"Error executing the pipeline: {e} \n\n")
        raise
