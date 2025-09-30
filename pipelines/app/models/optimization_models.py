from datetime import datetime
from typing import Any, List, Literal
from pydantic import BaseModel, Field
from enum import Enum


class BookmakerEnum(str, Enum):
    """Enum for supported bookmakers."""
    BETANYSPORTS = "betanysports"
    BETCLIC = "betclic"
    BETCLIC_FR = "betclic_fr"
    BETFAIR_EX_EU = "betfair_ex_eu"
    BETFAIR_EX_UK = "betfair_ex_uk"
    BETFAIR_SB_UK = "betfair_sb_uk"
    BETONLINEAG = "betonlineag"
    BETSSON = "betsson"
    BETVICTOR = "betvictor"
    BETWAY = "betway"
    BOYLESPORTS = "boylesports"
    CASUMO = "casumo"
    COOLBET = "coolbet"
    CORAL = "coral"
    EVERYGAME = "everygame"
    GROSVENOR = "grosvenor"
    GTBETS = "gtbets"
    LADBROKES_UK = "ladbrokes_uk"
    LEOVEGAS = "leovegas"
    LIVESCOREBET = "livescorebet"
    LIVESCOREBET_EU = "livescorebet_eu"
    MARATHONBET = "marathonbet"
    # MATCHBOOK = "matchbook"
    MYBOOKIEAG = "mybookieag"
    NORDICBET = "nordicbet"
    ONEXBET = "onexbet"
    PADDYPOWER = "paddypower"
    PARIONSSPORT_FR = "parionssport_fr"
    PINNACLE = "pinnacle"
    SKYBET = "skybet"
    SMARKETS = "smarkets"
    SPORT888 = "sport888"
    SUPRABETS = "suprabets"
    TIPICO_DE = "tipico_de"
    UNIBET_EU = "unibet_eu"
    UNIBET_FR = "unibet_fr"
    UNIBET_IT = "unibet_it"
    UNIBET_NL = "unibet_nl"
    UNIBET_UK = "unibet_uk"
    VIRGINBET = "virginbet"
    WILLIAMHILL = "williamhill"
    WINAMAX_DE = "winamax_de"
    WINAMAX_FR = "winamax_fr"


class OptimMethodEnum(str, Enum):
    """Enum for optimization methods."""
    SLSQP = "SLSQP"
    COBYLA = "COBYLA"
    TRUST_CONSTR = "trust-constr"


class UtilityFunctionEnum(str, Enum):
    """Enum for utility functions."""
    KELLY = "Kelly"
    LINEAR = "Linear"
    EXP = "Exp"
    LOG = "Log"
    CRRA = "CRRA"


class OptimizationRequest(BaseModel):
    """Request model for optimization computations."""

    datetime_first_match: datetime | None = Field(
        None,
        description="Datetime of the first match to consider (format: YYYY-MM-DD HH:MM:SS)",
        example="2024-01-15 14:30:00"
    )
    n_matches: int | None = Field(
        None,
        ge=1,
        le=100,
        description="Number of upcoming matches to consider for optimization"
    )
    bookmakers: list[BookmakerEnum] | None = Field(
        None,
        description="List of bookmakers to consider for optimization"
    )
    bankroll: float | None = Field(
        1.0,
        ge=0.01,
        le=1000000.0,
        description="Bankroll amount to consider for optimization"
    )
    method: OptimMethodEnum = Field(
        OptimMethodEnum.SLSQP,
        description="Optimization method to use"
    )
    utility_fn: UtilityFunctionEnum = Field(
        UtilityFunctionEnum.LINEAR,
        description="Utility function to use for optimization"
    )
    same_day: bool = Field(
        False,
        description="Whether to consider only matches on the same day"
    )
    optim_label: str = Field(
        "user_request",
        max_length=50,
        description="Label for the optimization run"
    )
    l: float = Field(
        10,
        description="Parameter l for utility function Linear (only used if utility_fn is Linear, variance constraint)"
    )
    divisor: float = Field(
        2.0,
        ge=0,
        description="Divisor for utility function adjustments"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "datetime_first_match": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "n_matches": 10,
                "bookmakers": ["pinnacle", "betclic"],
                "bankroll": 1,
                "method": "SLSQP",
                "utility_fn": "Linear",
                "same_day": True,
                "optim_label": "user_request",
                "l": 10,
                "divisor": 2.0
            }
        }


class MatchOptimization(BaseModel):
    """Model for a single match optimization result."""
    match_id: str | None = None
    sport_key: str | None = None
    game: str | None = None
    date_match: str | None = None  # Date as string from DataFrame
    time_match: str | None = None
    home_team: str | None = None
    away_team: str | None = None
    model: str | None = None
    datetime_inference: datetime | None = None
    
    # Probabilities from the model
    prob_home_win: float | None = None
    prob_draw: float | None = None
    prob_away_win: float | None = None
    
    # Best odds found
    odds_home: float | None = None
    odds_draw: float | None = None
    odds_away: float | None = None
    
    # Bookmakers offering the best odds
    bookmaker_home: str | None = None
    bookmaker_draw: str | None = None
    bookmaker_away: str | None = None
    bookmaker_home_key: str | None = None
    bookmaker_draw_key: str | None = None
    bookmaker_away_key: str | None = None
    
    # Optimal fractions to bet (Kelly criterion results)
    f_home: float | None = None
    f_draw: float | None = None
    f_away: float | None = None
    
    # Optimization metadata
    datetime_optim: datetime | None = None
    utility_fn: str | None = None
    optim_label: str | None = None
    
    # Odds timestamps
    odds_home_datetime: datetime | None = None
    odds_draw_datetime: datetime | None = None
    odds_away_datetime: datetime | None = None

class OptimizationResponse(BaseModel):
    """Response model for optimization results."""
    status: Literal["success"]
    datetime_optim: datetime
    optim_label: str
    matches: List[MatchOptimization] | List[dict[str, Any]]