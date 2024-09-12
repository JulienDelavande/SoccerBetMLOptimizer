from fastapi import FastAPI, HTTPException
from app.services.get_optim_results import get_optim_results
# from app._config import engine
# import logging

app = FastAPI()

#logger = logging.getLogger('app-backend')

@app.get("/")
def read_root():
    return {"Info": "App backend for monitoring and display of data"}

@app.get("/optim_results")
def get_optim_results_route(datetime_first_match: str = None, n_matches: int = None, bookmakers: str = None, bankroll: float = 1, method: str = 'SLSQP'):
    try:
        df_optim_results, metrics, durations = get_optim_results(datetime_first_match, n_matches, bookmakers, bankroll, method)
        return {"status": "success", "df_optim_results": df_optim_results.to_dict(orient='records'), "metrics": metrics, "durations": durations}
    except Exception as e:
        #logger.info(f"Optimisation failed: {str(e)}")
        #logger.error(f"Optimisation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/compute/regular_strategy")
def compute_regular_strategy_route(datetime_computation: str = None, n_matches: int = None, bookmakers: str = None):
    pass