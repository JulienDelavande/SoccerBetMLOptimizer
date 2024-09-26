import os
import logging
import argparse
import datetime
import time

import pandas as pd
from sqlalchemy import text
import numpy as np

import mlflow
import mlflow.sklearn

from .utils.test_model_and_infer import test_model_and_infer
from .utils.insert_results_to_db import insert_results_to_db
from feature_eng.format_df import merge_sofifa_fbref_results, format_sofifa_fbref_data, add_signals
from app._config import DB_TN_FBREF_RESULTS, DB_TN_SOFIFA_TEAMS_STATS, DB_TN_MODELS_RESULTS, MLFLOW_TRACKING_URI
from app._config import engine


#### settings ####
MLFLOW_EXPERIMENT_NAME = "RSF_PR_LR"
logger = logging.getLogger("RSF_PR_LR")

def infer__RSF_PR_LR__pipeline(date_stop=None, mlflow=True):
    """
    Inference pipeline for LR model. Data is retrieved from the database, processed, the model is trained and tested, and the results are inserted back into the database.
    
    Parameters
    ----------
    date_stop : datetime.datetime, optional
        The date of the match to stop training and start the inference, by default None (today)
    mlflow : bool, optional
        If True, the pipeline will log the metrics and parameters to MLflow, by default True, Mlflow server must be set up and running
    
    Returns
    -------
    train_test_metrics : pd.DataFrame
        The metrics of the model on the train and test set
    fbref_results_df__sofifa_merged__data_formated__signals_added__infered : pd.DataFrame
        The results of the model on the inference set
     """
    
    start_pipeline = time.time()
    logger.info("---- Starting the inference pipeline")
    logger.info(f"date_stop: {date_stop}")
    logger.info(f"mlflow: {mlflow}")

    #### MLflow setup ####
    if mlflow:
        mlflow.set_tracking_uri(uri=MLFLOW_TRACKING_URI)
        if not mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME):
            mlflow.create_experiment(MLFLOW_EXPERIMENT_NAME)
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)


    #### Connection to the database and retrieve data ####

    start_data_retrieval = time.time()
    try:
        with engine.connect() as connection:
            logger.info("Database connection established")
            logger.info(f"DB_HOST: {engine.url.host}")
            logger.info(f"DB_PORT: {engine.url.port}")
            logger.info(f"DB_NAME: {engine.url.database}")

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
        if mlflow:
            with mlflow.start_run():
                train_test_metrics, fbref_results_df__sofifa_merged__data_formated__signals_added__infered = test_model_and_infer(
                    fbref_results_df__sofifa_merged__data_formated__signals_added__train, 
                    fbref_results_df__sofifa_merged__data_formated__signals_added__infer
                )
                mlflow.log_metrics({metric['metrics']: metric['values'] for metric in train_test_metrics.to_dict('records')})
                mlflow.log_param("date_stop", str(date_stop))

        else:
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
        return train_test_metrics, fbref_results_df__sofifa_merged__data_formated__signals_added__infered, nb_matches_infered, first_match_name, last_match_name, datetime_inference
    except Exception as e:
        logger.warning(f"Error calculating metrics: {e}")
        return train_test_metrics, fbref_results_df__sofifa_merged__data_formated__signals_added__infered, None, None, None, datetime_inference

if __name__ == "__main__":
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
        train_test_metrics, df_infered, nb_matches_infered, first_match_name, last_match_name = infer__RSF_PR_LR__pipeline(date_stop=date_stop)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Pipeline executed successfully in {duration:2f} seconds \n\n")
    except Exception as e:
        logger.error(f"Error executing the pipeline: {e} \n\n")
        raise
