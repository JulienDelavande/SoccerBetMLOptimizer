from fastapi import FastAPI, HTTPException
from app.services.get_optim_results import get_optim_results

app = FastAPI()

@app.get("/")
def read_root():
    return {"Info": "App backend for monitoring and display of data"}

@app.get("/optim_results")
def get_optim_results_route(datetime_computation: str = None, n_matchs: int = None, bookmakers: str = None):
    return get_optim_results(datetime_computation, n_matchs, bookmakers)