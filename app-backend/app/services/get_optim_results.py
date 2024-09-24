import datetime
from sqlalchemy import text
import pandas as pd
import requests
import time

from optim.functions.player_gain_expected_value import player_gain_expected_value
from optim.functions.player_gain_variance import player_gain_variance


from app._config import DB_TN_OPTIM_RESULTS, PIPELINES_PROTOCOL, PIPELINES_HOST, PIPELINES_PORT, PIPELINES_ENDPOINT_OPTIMIZATION
from app._config import engine

import logging

bookmaker_keys = [
    "onexbet",
    "sport888",
    "betclic",
    "betanysports",
    "betfair_ex_eu",
    "betonlineag",
    "betsson",
    "betvictor",
    "coolbet",
    "everygame",
    "gtbets",
    "livescorebet_eu",
    "marathonbet",
    "matchbook",
    "mybookieag",
    "nordicbet",
    "pinnacle",
    "suprabets",
    "tipico_de",
    "unibet_eu",
    "williamhill"
]


logger = logging.getLogger('get_optim_results')
query = f"SELECT * FROM {DB_TN_OPTIM_RESULTS} WHERE datetime_optim = :datetime_optim"
URL_OPTIM = f"{PIPELINES_PROTOCOL}://{PIPELINES_HOST}:{PIPELINES_PORT}/{PIPELINES_ENDPOINT_OPTIMIZATION}"

def get_optim_results(datetime_first_match: str = None, n_matches: int = None, bookmakers: str = None, bankroll: float = 1, method: str = 'SLSQP', utility_fn: str = 'Kelly'):
    logger.info(f"Getting optim results for datetime_first_match: {datetime_first_match}, n_matches: {n_matches}, bookmakers: {bookmakers}")

    # validation
    logger.info("Validating input parameters")
    time_validation_start = time.time()
    datetime_first_match = verify_valid_datetime(datetime_first_match)
    n_matches = verify_valid_n_matches(n_matches)
    bookmakers = verify_valid_bookmakers(bookmakers)
    time_validation_end = time.time()

    # perform optim request
    time_optim_start = time.time()
    params = {"datetime_first_match": datetime_first_match, "n_matches": n_matches, "bookmakers": bookmakers, "bankroll": bankroll, "method": method, "utility_fn": utility_fn}
    logger.info(f"Requesting optim results from {URL_OPTIM} with params: {params}")
    results = requests.get(URL_OPTIM, params=params)
    datetime_optim = results.json().get("datetime_optim")
    time_request_end = time.time()
    
    # get results from db
    time_db_results_start = time.time()
    logger.info(f"Getting optim results from db for datetime_optim: {datetime_optim}")
    df_optim_results = get_optim_results_df_from_db(datetime_optim)
    time_db_results_end = time.time()

    # compute expected values and variance
    time_compute_metrics_start = time.time()
    o = df_optim_results[['odds_home', 'odds_draw', 'odds_away']].to_numpy()
    r = df_optim_results[['prob_home_win', 'prob_draw', 'prob_away_win']].to_numpy()
    f = df_optim_results[['f_home', 'f_draw', 'f_away']].to_numpy()

    metrics = {}
    metrics['expected_value'] = player_gain_expected_value(f, o, r, bankroll)
    metrics['variance'] = player_gain_variance(f, o, r, bankroll)
    metrics['total_invested'] = f.sum()*bankroll
    time_compute_metrics_end = time.time()

    # durations
    durations = {}
    durations['duration_validation'] = time_validation_end - time_validation_start
    durations['duration_request'] = time_request_end - time_optim_start
    durations['duration_db_results'] = time_db_results_end - time_db_results_start
    durations['duration_compute_metrics'] = time_compute_metrics_end - time_compute_metrics_start

    logger.info(f"Validation time: {durations['duration_validation']} seconds")
    logging.info(f"Optim request time: {durations['duration_request']} seconds")
    logging.info(f"DB results time: {durations['duration_db_results']} seconds")
    logging.info(f"Compute metrics time: {durations['duration_compute_metrics']} seconds")

    return df_optim_results, metrics, durations


def get_optim_results_df_from_db(datetime_optim: str = None):
    try:
        with engine.connect() as connection:
            df_optim_results = pd.read_sql(text(query), connection, params={"datetime_optim": datetime_optim})
        if df_optim_results.empty:
            logger.info(f"No results found for datetime_optim: {datetime_optim}")
            logger.error(f"No results found for datetime_optim: {datetime_optim}")
            raise ValueError
        max_datetime_optim = df_optim_results["datetime_optim"].max()
        df_optim_results = df_optim_results[df_optim_results["datetime_optim"] == max_datetime_optim]
        logger.info(f"Results found for datetime_optim: {datetime_optim}")
    except Exception as e:
        logging.info(f"Failed to get results from db: {str(e)}")
        logger.error(f"Failed to get results from db: {str(e)}")
        raise e
    return df_optim_results
    
     
def verify_valid_datetime(datetime_optim: str = None):
    """verify date_optim is a string and convert to datetime"""
    if not datetime_optim:
        datetime_optim = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        logger.info(f"Converting datetime_optim: {datetime_optim}")
        datetime_optim = datetime.datetime.strptime(datetime_optim, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.error(f"Invalid date format: {datetime_optim}")
        raise ValueError
    return datetime_optim

def verify_valid_n_matches(n_matches: int = None):
    """verify n_matches is an integer and positive, if string convert to int"""
    if n_matches:
        try:
            n_matches = int(n_matches)
            if n_matches < 0:
                logger.error(f"Invalid n_matches: {n_matches}")
                raise ValueError
        except ValueError:
            logger.error(f"Invalid n_matches: {n_matches}")
            raise ValueError
    return n_matches

def verify_valid_bookmakers(bookmakers: str = None):
    """verify bookmakers is a string, if not return None"""
    if bookmakers:
        try:
            bookmakers = str(bookmakers)
            bookmakers = bookmakers.split(",")
            for bookmaker in bookmakers:
                if bookmaker not in bookmaker_keys:
                    logger.error(f"Invalid bookmaker: {bookmaker}")
                    raise ValueError
            bookmakers = ",".join(bookmakers)
        except ValueError:
            logger.error(f"Invalid bookmakers: {bookmakers}")
            raise ValueError
    return bookmakers


if __name__ == "__main__":
    datetime_first_match = "2024-09-04 00:00:00"
    n_match = 10
    bookmakers = "onexbet,sport888,betclic"
    df = get_optim_results(datetime_first_match, n_match, bookmakers)
    print(df)