from pydantic import BaseModel, Field
from typing import Optional, Literal

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

class OptimParams(BaseModel):
    datetime_first_match: Optional[str] = Field(
        None, 
        pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
        description="Datetime of the first match to consider for the optimisation"
    )
    n_matches: Optional[int] = Field(
        None, 
        ge=1,
        description="Number of upcoming matches to consider for the optimisation"
    )
    bookmakers: Optional[Literal[
        "onexbet", "sport888", "betclic", "betanysports", "betfair_ex_eu", "betonlineag", "betsson", "betvictor", 
        "coolbet", "everygame", "gtbets", "livescorebet_eu", "marathonbet", "matchbook", "mybookieag", "nordicbet", 
        "pinnacle", "suprabets", "tipico_de", "unibet_eu", "williamhill"
        ]] = Field(
        None, 
        description=f"Bookmakers to consider for the optimisation (choose from {bookmaker_keys})"
    )
    bankroll: Optional[float] = Field(
        1, 
        ge=0,
        description="Bankroll to consider for the optimisation"
    )