from fastapi import FastAPI, HTTPException

from app.insert_data.fbref_results import insert_recent_fbref_matches
from app.insert_data.sofifa_teams_stats import insert_data_SOFIFA_teams_stats_table
from app.insert_data.the_odds_api_odds import ingest_odds_the_odds_api
import app._config


app = FastAPI()

@app.get("/")
def read_root():
    return {"Info": "Microservice for data ingestion into postgres db"}

@app.get("/fbref")
def insert_data_fbref_results_table_root(get_current_season_only: bool = True, use_cache: bool = False, cutoff_days: int = 7):
    try:
        df_insert = insert_recent_fbref_matches(get_current_season_only=get_current_season_only, use_cache=use_cache, cutoff_days=cutoff_days)
        return {"status": "success", 
                "inserted_rows": len(df_insert), 
                "first_row": df_insert.iloc[0].to_string(index=False) if not df_insert.empty else None, 
                "last_row": df_insert.iloc[-1].to_string(index=False) if not df_insert.empty else None
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sofifa/team_stats")
def insert_data_SOFIFA_teams_stats_table_root(use_cache: bool = False, scrap_all: bool = False):
    try:
        insert_data_SOFIFA_teams_stats_table(use_cache=use_cache, scrap_all=scrap_all)
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
    
