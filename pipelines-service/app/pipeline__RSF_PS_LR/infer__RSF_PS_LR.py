import logging
import argparse
import datetime
import time

import pandas as pd
from sqlalchemy import text
import mlflow

from .utils.test_model_and_infer import test_model_and_infer
from .utils.insert_results_to_db import insert_results_to_db
from feature_eng.format_df import merge_sofifa_fbref_results, format_sofifa_fbref_data, add_signals
from app._config import DB_TN_FBREF_RESULTS, DB_TN_SOFIFA_TEAMS_STATS, DB_TN_MODELS_RESULTS, MLFLOW_TRACKING_URI
from app._config import engine


#### settings ####
MLFLOW_EXPERIMENT_NAME = "RSF_PS_LR"
logger = logging.getLogger("RSF_PS_LR")


def infer__RSF_PS_LR__pipeline(date_stop=None):
    start_pipeline = time.time()
    logger.info("Starting the inference pipeline")
        
    #### MLflow setup ####
    mlflow.set_tracking_uri(uri=MLFLOW_TRACKING_URI)
    if not mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME):
        mlflow.create_experiment(MLFLOW_EXPERIMENT_NAME)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    #### Connection to the database and retrieve data ####
    start_data_retrieval = time.time()
    try:
        with engine.connect() as connection:
            logger.info("Database connection established")
            query_fbref_results = text(f"SELECT * FROM {DB_TN_FBREF_RESULTS}")
            fbref_results_df = pd.read_sql(query_fbref_results, connection)
            query_sofifa_team_stats = text(f'SELECT * FROM {DB_TN_SOFIFA_TEAMS_STATS}')
            sofifa_teams_stats_df = pd.read_sql(query_sofifa_team_stats, connection)
            logger.info(f"Data retrieved from database successfully in {time.time() - start_data_retrieval} seconds")
    except Exception as e:
        logger.error(f"Error retrieving data from the database: {e}")
        raise


    #### Data processing ####
    start_data_processing = time.time()
    try:
        date_stop = date_stop if date_stop else datetime.datetime.now()
        fbref_results_df__sofifa_merged = merge_sofifa_fbref_results(fbref_results_df, sofifa_teams_stats_df)
        fbref_results_df__sofifa_merged__data_formated = format_sofifa_fbref_data(fbref_results_df__sofifa_merged, date_stop=date_stop)
        fbref_results_df__sofifa_merged__data_formated__signals_added = add_signals(fbref_results_df__sofifa_merged__data_formated, date_stop=date_stop)

        rule_is_before_datetime = fbref_results_df__sofifa_merged__data_formated__signals_added["datetime"] < date_stop
        fbref_results_df__sofifa_merged__data_formated__signals_added__train = fbref_results_df__sofifa_merged__data_formated__signals_added[rule_is_before_datetime].copy()
        fbref_results_df__sofifa_merged__data_formated__signals_added__infer = fbref_results_df__sofifa_merged__data_formated__signals_added[~rule_is_before_datetime].copy()

        logger.info(f"Data processing completed successfully in {time.time() - start_data_processing} seconds")
    except Exception as e:
        logger.error(f"Error during data processing: {e}")
        raise
    

    #### Train and test the model and infer the results ####
    start_train_test_inference = time.time()
    try:
        with mlflow.start_run():
            metrics_train_set, fbref_results_df__sofifa_merged__data_formated__signals_added__infered = test_model_and_infer(
                fbref_results_df__sofifa_merged__data_formated__signals_added__train, 
                fbref_results_df__sofifa_merged__data_formated__signals_added__infer
            )
            mlflow.log_metrics({metric['metrics']: metric['values'] for metric in metrics_train_set.to_dict('records')})
            mlflow.log_param("date_stop", str(date_stop))
        logger.info(f"Model training and inference completed successfully completed in {time.time() - start_train_test_inference} seconds, accuray on train test : {metrics_train_set}")
    except Exception as e:
        logger.error(f"Error during model training and inference: {e}")
        raise


    #### Insert the results into the database ####
    start_insert_results = time.time()
    try:
        insert_results_to_db(engine, fbref_results_df__sofifa_merged__data_formated__signals_added__infered, DB_TN_MODELS_RESULTS)
        matchs_infered = fbref_results_df__sofifa_merged__data_formated__signals_added__infered.shape[0]
        logger.info(f"{matchs_infered} results inserted into the database successfully, completed in {time.time() - start_insert_results} seconds")
    except Exception as e:
        logger.error(f"Error inserting results into the database: {e}")
        raise
    logger.info(f"Pipeline completed in {time.time() - start_pipeline} seconds")
    return metrics_train_set, fbref_results_df__sofifa_merged__data_formated__signals_added__infered


if __name__ == "__main__":
    logging.info("-- Starting the RFS_PR_LR pipeline --")
    start_time = time.time()

    args = argparse.ArgumentParser()
    args.add_argument("--date_stop", type=str, default=None)
    args = args.parse_args()

    date_stop = None
    if args.date_stop:
        try:
            date_stop = datetime.datetime.strptime(args.date_stop, "%Y-%m-%d %H:%M:%S")
            logger.info(f"date_stop parameter parsed successfully: {date_stop}")
        except ValueError as e:
            logger.error(f"Error parsing date_stop parameter: {e}")
            raise

    try:
        metrics_train_set, fbref_results_df__sofifa_merged__data_formated__signals_added__infered = infer__RSF_PS_LR__pipeline(date_stop=date_stop)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Pipeline executed successfully in {duration:2f} seconds \n\n")
    except Exception as e:
        logger.error(f"Error executing the pipeline: {e} \n\n")
        raise
