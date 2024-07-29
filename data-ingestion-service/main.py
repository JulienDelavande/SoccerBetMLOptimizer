from fastapi import FastAPI, HTTPException

from app.insert_data.fbref_results import scrap_data_fbref
from app.insert_data.sofifa_teams_stats import insert_data_SOFIFA_teams_stats_table
from app.insert_data.the_odds_api_odds import ingest_odds_the_odds_api
import app._config


app = FastAPI()

@app.get("/")
def read_root():
    return {"Info": "Microservice for data ingestion into postgres db"}

@app.get("/fbref")
def insert_data_fbref_results_table(get_current_season_only: bool = True, use_cache: bool = False):
    try:
        scrap_data_fbref(get_current_season_only=get_current_season_only, use_cache=use_cache)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sofifa/team_stats")
def insert_data_fbref_results_table():
    try:
        insert_data_SOFIFA_teams_stats_table()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/the_odds_api/odds")
def insert_data_the_odds_api_odds():
    try:
        ingest_odds_the_odds_api()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
