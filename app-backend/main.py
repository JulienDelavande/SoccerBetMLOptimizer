from fastapi import FastAPI, HTTPException, Query
from app.services.get_optim_results import get_optim_results
from app.services.strategy_regular import strategy_regular
from app.services.fetch_last_predictions import fetch_last_predictions_fn
from app.services.fetch_past_performances import fetch_past_performances_fn
from app.services.fetch_past_performances_gains import fetch_past_performances_gains_fn
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
    if optim_label == 'test':
        return {
  "status": "success",
  "results": [
    {
      "match_id": "epl_liv_whu_20250713",
      "sport_key": "soccer_epl",
      "game": "Liverpool vs West Ham",
      "date_match": "2025-07-13",
      "time_match": "15:00",
      "home_team": "Liverpool",
      "away_team": "West Ham",
      "model": "RSF_PR_LR",
      "datetime_inference": "2025-07-13 10:00:00",
      "prob_home_win": 0.6,
      "prob_draw": 0.2,
      "prob_away_win": 0.2,
      "odds_home": 1.65,
      "odds_draw": 4.00,
      "odds_away": 5.00,
      "bookmaker_home": "1xbet",
      "bookmaker_draw": "Unibet",
      "bookmaker_away": "Unibet",
      "f_home": 0.55,
      "f_draw": 0.15,
      "f_away": 0.30,
      "datetime_optim": "2025-07-13 10:30:00",
      "utility_fn": "Kelly",
      "odds_home_datetime": "2025-07-13 10:00:00",
      "odds_draw_datetime": "2025-07-13 10:00:00",
      "odds_away_datetime": "2025-07-13 10:00:00",
      "optim_label": optim_label
    },
    {
      "match_id": "epl_mun_tot_20250719",
      "sport_key": "soccer_epl",
      "game": "Manchester United vs Tottenham",
      "date_match": "2025-07-19",
      "time_match": "17:30",
      "home_team": "Manchester United",
      "away_team": "Tottenham",
      "model": "RSF_PR_LR",
      "datetime_inference": "2025-07-19 11:00:00",
      "prob_home_win": 0.45,
      "prob_draw": 0.25,
      "prob_away_win": 0.30,
      "odds_home": 2.20,
      "odds_draw": 3.50,
      "odds_away": 3.00,
      "bookmaker_home": "Winamax",
      "bookmaker_draw": "Unibet",
      "bookmaker_away": "Winamax",
      "f_home": 0.40,
      "f_draw": 0.20,
      "f_away": 0.40,
      "datetime_optim": "2025-07-19 11:30:00",
      "utility_fn": "Kelly",
      "odds_home_datetime": "2025-07-19 11:00:00",
      "odds_draw_datetime": "2025-07-19 11:00:00",
      "odds_away_datetime": "2025-07-19 11:00:00",
      "optim_label": optim_label
    },
    {
      "match_id": "epl_che_ars_20250723",
      "sport_key": "soccer_epl",
      "game": "Chelsea vs Arsenal",
      "date_match": "2025-07-23",
      "time_match": "20:00",
      "home_team": "Chelsea",
      "away_team": "Arsenal",
      "model": "RSF_PR_LR",
      "datetime_inference": "2025-07-23 14:00:00",
      "prob_home_win": 0.48,
      "prob_draw": 0.27,
      "prob_away_win": 0.25,
      "odds_home": 2.05,
      "odds_draw": 3.20,
      "odds_away": 3.40,
      "bookmaker_home": "1xbet",
      "bookmaker_draw": "1xbet",
      "bookmaker_away": "Unibet",
      "f_home": 0.43,
      "f_draw": 0.22,
      "f_away": 0.35,
      "datetime_optim": "2025-07-23 14:30:00",
      "utility_fn": "Kelly",
      "odds_home_datetime": "2025-07-23 14:00:00",
      "odds_draw_datetime": "2025-07-23 14:00:00",
      "odds_away_datetime": "2025-07-23 14:00:00",
      "optim_label": optim_label
    }
  ]
}

    try:
        results = fetch_last_predictions_fn(optim_label=optim_label, datetime_optim_last=datetime_optim_last)
        logger.info(f"/fetch_last_predictions route completed")
        return {"status": "success", "results": results.to_dict(orient='records')}
    except Exception as e:
        logger.error(f"/fetch_last_predictions route failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/fetch/past_performances")
def fetch_past_performances(optim_label = 'manual', datetime_first_match = None, datetime_last_match = None):
    if optim_label == 'test':
        return {
  "status": "success",
  "results": [
    {
      "match_id": "cwc_qf_psg_bay_20250705",
      "sport_key": "soccer_cwc",
      "game": "Paris Saint‑Germain vs Bayern Munich",
      "date_match": "2025-07-05",
      "time_match": "12:00:00",
      "home_team": "Paris Saint‑Germain",
      "away_team": "Bayern Munich",
      "model": "RSF_PR_LR",
      "datetime_inference": "2025-07-05 08:00:00",
      "prob_home_win": 0.55,
      "prob_draw": 0.22,
      "prob_away_win": 0.23,
      "odds_home": 2.10,
      "odds_draw": 3.40,
      "odds_away": 3.20,
      "bookmaker_home": "Unibet",
      "bookmaker_draw": "Winamax",
      "bookmaker_away": "1xbet",
      "f_home": 0.12,
      "f_draw": 0.00,
      "f_away": 0.00,
      "datetime_optim": "2025-07-05 08:30:00",
      "utility_fn": "Kelly",
      "odds_home_datetime": "2025-07-05 08:00:00",
      "odds_draw_datetime": "2025-07-05 08:00:00",
      "odds_away_datetime": "2025-07-05 08:00:00",
      "optim_label": "cwckelly_0705",
      "date": "2025-07-05",
      "time": "12:00:00",
      "home_xg": 1.8,
      "score": "2-0",
      "away_xg": 1.1,
      "attendance": 71000,
      "venue": "Mercedes‑Benz Stadium",
      "referee": "Antonio Mateu Lahoz",
      "match_report": "PSG win 2–0 against Bayern with goals from Doué (78′) and Dembélé (90+6′).",
      "notes": "",
      "index": 0,
      "away_g": 0,
      "home_g": 2,
      "away_sat": None,
      "home_sat": None,
      "datetime_insert": "2025-07-05 14:00:00"
    },
    {
      "match_id": "cwc_qf_rma_dor_20250705",
      "sport_key": "soccer_cwc",
      "game": "Real Madrid vs Borussia Dortmund",
      "date_match": "2025-07-05",
      "time_match": "16:00:00",
      "home_team": "Real Madrid",
      "away_team": "Borussia Dortmund",
      "model": "RSF_PR_LR",
      "datetime_inference": "2025-07-05 12:00:00",
      "prob_home_win": 0.52,
      "prob_draw": 0.24,
      "prob_away_win": 0.24,
      "odds_home": 2.20,
      "odds_draw": 3.50,
      "odds_away": 3.30,
      "bookmaker_home": "Winamax",
      "bookmaker_draw": "Winamax",
      "bookmaker_away": "1xbet",
      "f_home": 0.10,
      "f_draw": 0.00,
      "f_away": 0.00,
      "datetime_optim": "2025-07-05 12:30:00",
      "utility_fn": "Kelly",
      "odds_home_datetime": "2025-07-05 12:00:00",
      "odds_draw_datetime": "2025-07-05 12:00:00",
      "odds_away_datetime": "2025-07-05 12:00:00",
      "optim_label": "cwckelly_0705_rma",
      "date": "2025-07-05",
      "time": "16:00:00",
      "home_xg": 2.2,
      "score": "3-2",
      "away_xg": 1.9,
      "attendance": 75000,
      "venue": "MetLife Stadium",
      "referee": "Daniele Orsato",
      "match_report": "Real Madrid win 3–2 with goals from García, Fran García and Mbappé. Dortmund scored via Beier and Guirassy (pen).",
      "notes": "",
      "index": 1,
      "away_g": 2,
      "home_g": 3,
      "away_sat": None,
      "home_sat": None,
      "datetime_insert": "2025-07-05 18:00:00"
    }
  ]
}

    try:
        results = fetch_past_performances_fn(optim_label=optim_label, datetime_first_match=datetime_first_match, datetime_last_match=datetime_last_match)
        logger.info(f"/fetch_past_performances route completed")
        return {"status": "success", "results": results.to_dict(orient='records')}
    except Exception as e:
        logger.error(f"/fetch_past_performances route failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/fetch/past_performances_gains")
def fetch_past_performances_gains(optim_label = 'manual', datetime_first_match = None, datetime_last_match = None):
    if optim_label == 'test':
        return {
  "status": "success",
  "results": [
    {"date": "2025-06-06", "gain": 1.00},
    {"date": "2025-06-07", "gain": 1.03},
    {"date": "2025-06-08", "gain": 1.06},
    {"date": "2025-06-09", "gain": 1.04},
    {"date": "2025-06-10", "gain": 1.08},
    {"date": "2025-06-11", "gain": 1.12},
    {"date": "2025-06-12", "gain": 1.16},
    {"date": "2025-06-13", "gain": 1.20},
    {"date": "2025-06-14", "gain": 1.19},
    {"date": "2025-06-15", "gain": 1.25},
    {"date": "2025-06-16", "gain": 1.28},
    {"date": "2025-06-17", "gain": 1.26},
    {"date": "2025-06-18", "gain": 1.31},
    {"date": "2025-06-19", "gain": 1.38},
    {"date": "2025-06-20", "gain": 1.35},
    {"date": "2025-06-21", "gain": 1.42},
    {"date": "2025-06-22", "gain": 1.45},
    {"date": "2025-06-23", "gain": 1.47},
    {"date": "2025-06-24", "gain": 1.51},
    {"date": "2025-06-25", "gain": 1.58},
    {"date": "2025-06-26", "gain": 1.61},
    {"date": "2025-06-27", "gain": 1.63},
    {"date": "2025-06-28", "gain": 1.65},
    {"date": "2025-06-29", "gain": 1.71},
    {"date": "2025-06-30", "gain": 1.75},
    {"date": "2025-07-01", "gain": 1.80},
    {"date": "2025-07-02", "gain": 1.84},
    {"date": "2025-07-03", "gain": 1.89},
    {"date": "2025-07-04", "gain": 1.93},
    {"date": "2025-07-05", "gain": 2.00}
  ]
}

    try:
        results = fetch_past_performances_gains_fn(optim_label=optim_label, datetime_first_match=datetime_first_match, datetime_last_match=datetime_last_match)
        logger.info(f"/fetch_past_performances_gains route completed")
        return {"status": "success", "results": results.to_dict(orient='records')}
    except Exception as e:
        logger.error(f"/fetch_past_performances route failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

