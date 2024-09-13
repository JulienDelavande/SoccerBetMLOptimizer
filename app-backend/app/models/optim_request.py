from pydantic import BaseModel
from fastapi import Query
from typing import Optional, Literal
import datetime

bookmaker_keys = [
    "onexbet",
    "sport888",
    "betclic",
    "betanysports",
    "betfair_ex_eu",
    "betonlineag",
    "betsson",
    "betvictor",
    "coolbet",
    "everygame",
    "gtbets",
    "livescorebet_eu",
    "marathonbet",
    "matchbook",
    "mybookieag",
    "nordicbet",
    "pinnacle",
    "suprabets",
    "tipico_de",
    "unibet_eu",
    "williamhill"
]
optim_methods = ["SLSQP", "COBYLA", "trust-constr"]

class OptimRequest(BaseModel):
    datetime_first_match: Optional[str] = Query(
        None, 
        pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
        description="Datetime of the first match to consider for the optimisation"
    )
    n_matches: Optional[int] = Query(
        None, 
        ge=1,
        description="Number of upcoming matches to consider for the optimisation"
    )
    bookmakers: Optional[Literal[
        "onexbet", "sport888", "betclic", "betanysports", "betfair_ex_eu", "betonlineag", "betsson", "betvictor", 
        "coolbet", "everygame", "gtbets", "livescorebet_eu", "marathonbet", "matchbook", "mybookieag", "nordicbet", 
        "pinnacle", "suprabets", "tipico_de", "unibet_eu", "williamhill"
        ]] = Query(
        None, 
        description=f"Bookmakers to consider for the optimisation (choose from {bookmaker_keys})"
    )
    bankroll: Optional[float] = Query(
        1, 
        ge=0,
        description="Bankroll to consider for the optimisation"
    )
    method: Optional[Literal["SLSQP", "COBYLA", "trust-constr"]] = Query(
        "SLSQP", 
        description=f"Optimisation method to use (choose from {optim_methods})"
    )