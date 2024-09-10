import datetime
from fastapi import HTTPException
from sqlalchemy import text
import pandas as pd
import requests

from app._config import engine, DB_TN_OPTIM_RESULTS, PIPELINES_PROTOCOL, PIPELINES_HOST, PIPELINES_PORT, PIPELINES_ENDPOINT_OPTIMIZATION

query = f"SELECT * FROM {DB_TN_OPTIM_RESULTS} WHERE datetime_optim = :datetime_optim"
URL_OPTIM = f"{PIPELINES_PROTOCOL}://{PIPELINES_HOST}:{PIPELINES_PORT}/{PIPELINES_ENDPOINT_OPTIMIZATION}"

def get_optim_results(datetime_first_match: str = None, n_matchs: int = None, bookmakers: str = None):
    # validation
    datetime_first_match = verify_valid_datetime(datetime_first_match)
    n_matchs = verify_valid_n_matchs(n_matchs)
    bookmakers = verify_valid_bookmakers(bookmakers)

    # get results
    params = {"datetime_first_match": datetime_first_match, "n_match": n_matchs, "bookmakers": bookmakers}
    results = requests.get(URL_OPTIM, params=params)
    datetime_optim = results.json().get("datetime_optim")
    df_optim_results = get_optim_results_df_from_db(datetime_optim)

    return df_optim_results


def get_optim_results_df_from_db(datetime_optim: str = None):
    try:
        with engine.connect() as connection:
            df_optim_results = pd.read_sql(text(query), connection, params={"date_optim": datetime_optim})
        if df_optim_results.empty:
            raise HTTPException(status_code=404, detail="No results found for the given date")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving optim results: {str(e)}")
    max_datetime_optim = df_optim_results["datetime_optim"].max()
    df_optim_results = df_optim_results[df_optim_results["datetime_optim"] == max_datetime_optim]
    return df_optim_results
    
     
def verify_valid_datetime(date_optim: str = None):
    """verify date_optim is a string and convert to datetime"""
    if not date_optim:
        date_optim = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        date_optim = datetime.datetime.strptime(date_optim, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD HH:MM:SS")
    return date_optim

def verify_valid_n_matchs(n_matchs: int = None):
    """verify n_matchs is an integer and positive, if string convert to int"""
    if n_matchs:
        try:
            n_matchs = int(n_matchs)
            if n_matchs < 0:
                raise ValueError
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid n_matchs. Must be a positive integer")
    return n_matchs

def verify_valid_bookmakers(bookmakers: str = None):
    """verify bookmakers is a string, if not return None"""
    if bookmakers:
        try:
            bookmakers = str(bookmakers)
            bookmakers = bookmakers.split(",")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid bookmakers. Must be a string")
    return bookmakers


if __name__ == "__main__":
    df = get_optim_results("2024-09-04")
    print(df)