from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from typing import Annotated
import pandas as pd

from app.insert_data.fbref_results import insert_recent_fbref_matches
from app.insert_data.sofifa_teams_stats import insert_data_SOFIFA_teams_stats_table
from app.insert_data.the_odds_api_odds import ingest_odds_the_odds_api

from app.models import (
    FbrefRequest,
    FbrefResponse,
    SofifaRequest,
    SofifaResponse,
    OddsRequest,
    OddsResponse,
)

from app.utils import (
    format_dataframe_summary,
    fbref_background_task,
    sofifa_background_task,
    odds_background_task,
)

import app._config  # Set up logging and env variables

app = FastAPI(
    title="Data Ingestion Service",
    description="Microservice for ingesting football data into a PostgreSQL database",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "meta",
            "description": "Service metadata and health checks",
        },
        {
            "name": "sources",
            "description": "Data ingestion from external football data providers",
        },
    ]
)

@app.get("/", tags=["meta"])
def root():
    return {
        "status": "ok",
        "message": "Microservice for ingesting football data into a PostgreSQL database",
    }

@app.post("/sources/fbref", response_model=FbrefResponse, tags=["sources"])
def ingest_fbref(request: Annotated[FbrefRequest, Body()], background_tasks: BackgroundTasks):
    try:
        if request.run_in_background:
            # Add the task to background tasks
            background_tasks.add_task(
                fbref_background_task,
                request.get_current_season_only,
                request.use_cache,
                request.cutoff_days
            )
            return FbrefResponse(
                status="accepted",
                message=f"FBref data ingestion started in background"
            )
        else:
            # Run synchronously
            df: pd.DataFrame = insert_recent_fbref_matches(
                get_current_season_only=request.get_current_season_only,
                use_cache=request.use_cache,
                cutoff_days=request.cutoff_days,
            )

            first_row, last_row = format_dataframe_summary(df)

            return FbrefResponse(
                status="success",
                inserted_rows=len(df),
                first_row=first_row,
                last_row=last_row,
                message=f"FBref data ingestion completed successfully. Processed {len(df)} items"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FBref ingestion failed: {e}")


@app.post("/sources/sofifa/team_stats", response_model=SofifaResponse, tags=["sources"])
def ingest_sofifa(request: SofifaRequest, background_tasks: BackgroundTasks):
    try:
        if request.run_in_background:
            # Add the task to background tasks
            background_tasks.add_task(
                sofifa_background_task,
                request.use_cache,
                request.scrap_all
            )
            return SofifaResponse(
                status="accepted",
                message=f"SOFIFA data ingestion started in background"
            )
        else:
            # Run synchronously
            insert_data_SOFIFA_teams_stats_table(
                use_cache=request.use_cache,
                scrap_all=request.scrap_all,
            )
            return SofifaResponse(
                status="success",
                message="SOFIFA data ingestion completed successfully"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SOFIFA ingestion failed: {e}")


@app.post("/sources/the_odds_api/odds", response_model=OddsResponse, tags=["sources"])
def ingest_odds(request: OddsRequest, background_tasks: BackgroundTasks):
    try:
        if request.run_in_background:
            # Add the task to background tasks
            background_tasks.add_task(odds_background_task)
            return OddsResponse(
                status="accepted",
                message=f"Odds data ingestion started in background"
            )
        else:
            # Run synchronously
            ingest_odds_the_odds_api()
            return OddsResponse(
                status="success",
                message="Odds data ingestion completed successfully"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Odds API ingestion failed: {e}")
