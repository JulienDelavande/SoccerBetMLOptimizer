"""
Utility functions for the data ingestion service.
"""

import pandas as pd
import logging

from app.insert_data.fbref_results import insert_recent_fbref_matches
from app.insert_data.sofifa_teams_stats import insert_data_SOFIFA_teams_stats_table
from app.insert_data.the_odds_api_odds import ingest_odds_the_odds_api

logger = logging.getLogger("fbref_results")

def format_dataframe_summary(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """
    Format first and last row of a DataFrame for API response.
    
    Args:
        df: The DataFrame to summarize
        
    Returns:
        A tuple containing (first_row, last_row) as strings or None if empty
    """
    if df.empty:
        return None, None
        
    first_row = df.iloc[0].to_string(index=False)
    last_row = df.iloc[-1].to_string(index=False)
    
    return first_row, last_row

def fbref_background_task(get_current_season_only: bool, use_cache: bool, cutoff_days: int):
    """Background task for FBref data ingestion"""
    try:
        logger.info("Starting FBref data ingestion in background")
        df: pd.DataFrame = insert_recent_fbref_matches(
            get_current_season_only=get_current_season_only,
            use_cache=use_cache,
            cutoff_days=cutoff_days,
        )
        logger.info(f"FBref background task completed successfully. Inserted {len(df)} rows")
    except Exception as e:
        logger.error(f"FBref background task failed: {e}")


def sofifa_background_task(use_cache: bool, scrap_all: bool):
    """Background task for SOFIFA data ingestion"""
    try:
        logger.info("Starting SOFIFA data ingestion in background")
        insert_data_SOFIFA_teams_stats_table(
            use_cache=use_cache,
            scrap_all=scrap_all,
        )
        logger.info("SOFIFA background task completed successfully")
    except Exception as e:
        logger.error(f"SOFIFA background task failed: {e}")


def odds_background_task():
    """Background task for odds data ingestion"""
    try:
        logger.info("Starting odds data ingestion in background")
        ingest_odds_the_odds_api()
        logger.info("Odds background task completed successfully")
    except Exception as e:
        logger.error(f"Odds background task failed: {e}")
