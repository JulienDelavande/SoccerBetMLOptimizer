import os
import logging
import argparse
import datetime
from pathlib import Path
import time

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from .utils.test_model_and_infer import test_model_and_infer
from .utils.insert_results_to_db import insert_results_to_db
from feature_eng.format_df import merge_sofifa_fbref_results, format_sofifa_fbref_data, add_signals

#### LOGGING ####
LOG_FOLDER = "logs/"
LOG_FILE_NAME = "pipeline_infer__RSF_PR_LR.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

filename = Path(__file__).resolve().parents[1] / LOG_FOLDER / LOG_FILE_NAME

logging.basicConfig(filename=filename, level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def infer__RSF_PR_LR__pipeline(date_stop=None):
    logger.info("Starting the inference pipeline")
    

    #### Load env var ####
    load_dotenv()
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')

    DB_TN_FBREF_RESULTS = os.getenv('DB_TN_FBREF_RESULTS')
    DB_TN_SOFIFA_TEAMS_STATS = os.getenv('DB_TN_SOFIFA_TEAMS_STATS')
    DB_TN_MODELS_RESULTS = os.getenv('DB_TN_MODELS_RESULTS')

    logger.info("Environment variables loaded successfully")


    #### Connection to the database and retrieve data ####
    connection_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(connection_url)

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
        fbref_results_df__sofifa_merged__data_formated__signals_added__train = fbref_results_df__sofifa_merged__data_formated__signals_added[rule_is_before_datetime]
        fbref_results_df__sofifa_merged__data_formated__signals_added__infer = fbref_results_df__sofifa_merged__data_formated__signals_added[~rule_is_before_datetime]

        logger.info(f"Data processing completed successfully in {time.time() - start_data_processing} seconds")
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
        insert_results_to_db(engine, fbref_results_df__sofifa_merged__data_formated__signals_added__infered, DB_TN_MODELS_RESULTS)
        matchs_infered = fbref_results_df__sofifa_merged__data_formated__signals_added__infered.shape[0]
        logger.info(f"{matchs_infered} results inserted into the database successfully, completed in {time.time() - start_insert_results} seconds")
    except Exception as e:
        logger.error(f"Error inserting results into the database: {e}")
        raise
    
    return train_test_metrics, fbref_results_df__sofifa_merged__data_formated__signals_added__infered


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
        train_test_metrics, fbref_results_df__sofifa_merged__data_formated__signals_added__infered = infer__RSF_PR_LR__pipeline(date_stop=date_stop)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Pipeline executed successfully in {duration:2f} seconds \n\n")
    except Exception as e:
        logger.error(f"Error executing the pipeline: {e} \n\n")
        raise
