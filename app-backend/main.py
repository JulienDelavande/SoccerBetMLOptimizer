from fastapi import FastAPI, HTTPException, Query
from app.services.get_optim_results import get_optim_results
from app.services.strategy_regular import strategy_regular
from app.services.fetch_last_predictions import fetch_last_predictions_fn
from app.models.optim_request import OptimRequest
import logging
from typing import Optional

app = FastAPI()

logger = logging.getLogger('app-backend')

@app.get("/")
def read_root():
    return {"Info": "App backend for monitoring and display of data"}

@app.get("/compute/predictions")
def get_optim_results_route(
    datetime_first_match: Optional[str] = Query(None, description="Datetime of the first match"),
    n_matches: Optional[int] = Query(None, ge=1, description="Number of matches"),
    bookmakers: Optional[str] = Query(None, description="Bookmaker"),
    bankroll: Optional[float] = Query(1, ge=0, description="Bankroll"),
    method: Optional[str] = Query('SLSQP', description="Optimization method"),
    utility_fn: Optional[str] = Query('Kelly', description="Utility function")
):
    try:
        params = OptimRequest(
            datetime_first_match=datetime_first_match,
            n_matches=n_matches,
            bookmakers=bookmakers,
            bankroll=bankroll,
            method=method,
            utility_fn=utility_fn
        )
        df_optim_results, metrics, durations = get_optim_results(**params.model_dump())
        logger.info(f"/optim_results route completed")
        return {"status": "success", 
                "df_optim_results": df_optim_results.to_dict(orient='records'), 
                "metrics": metrics, 
                "durations": durations}
    
    except Exception as e:
        logger.error(f"/optim_results route failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/strategy/regular")
def compute_regular_strategy_route(
    datetime_first_match: Optional[str] = Query(None, description="Datetime of the first match"),
    steps: Optional[int] = Query(None, ge=1, description="Number of steps"),
    n_matches: Optional[int] = Query(None, ge=1, description="Number of matches"),
    bet_days_timedelta: Optional[int] = Query(0, ge=0, description="Number of days to bet"),
    bet_one_time_per_match: Optional[bool] = Query(True, description="Bet one time per match"),
    bookmakers: Optional[str] = Query(None, description="Bookmaker"),
    method: Optional[str] = Query('SLSQP', description="Optimization method"),
    keely_fraction: Optional[float] = Query(0.5, ge=0, le=1, description="Kelly fraction")
):
    try:
        results = strategy_regular(datetime_first_match=datetime_first_match, steps=steps, n_matches=n_matches, 
                                   bet_days_timedelta=bet_days_timedelta, bet_one_time_per_match=bet_one_time_per_match, 
                                   bookmakers=bookmakers, method=method, keely_fraction=keely_fraction)
        logger.info(f"/compute_regular_strategy route completed")
        return {"status": "success", "results": results.to_dict(orient='records')}
    except Exception as e:
        logger.error(f"/compute_regular_strategy route failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/fetch/last_predictions")
def fetch_last_predictions(optim_label = 'manual', datetime_optim_last = None): 
    try:
        results = fetch_last_predictions_fn(optim_label=optim_label, datetime_optim_last=datetime_optim_last)
        logger.info(f"/fetch_last_predictions route completed")
        return {"status": "success", "results": results.to_dict(orient='records')}
    except Exception as e:
        logger.error(f"/fetch_last_predictions route failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))