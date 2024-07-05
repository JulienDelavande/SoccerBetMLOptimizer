from fastapi import FastAPI, HTTPException
from scripts.insert_data.fbref_results import scrap_data_fbref
from scripts.insert_data.sofifa_teams_stats import insert_data_SOFIFA_teams_stats_table

app = FastAPI()

@app.get("/")
def read_root():
    return {"Info": "Microservice for data ingestion into postgres db"}

@app.get("/insert_data_fbref_results_table")
def insert_data_fbref_results_table(get_current_season_only: bool = True, use_cache: bool = False):
    try:
        scrap_data_fbref(get_current_season_only=get_current_season_only, use_cache=use_cache)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insert_data_sofifa_teams_stats_table")
def insert_data_fbref_results_table():
    try:
        insert_data_SOFIFA_teams_stats_table()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/creation_dummy_file")
def creation_dummy_file():
    try:
        with open("dummy_file.txt", "w") as f:
            f.write("This is a dummy file")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
