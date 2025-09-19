"""Request models for the Soccer Bet ML Optimizer API."""

from pydantic import BaseModel, Field, validator
from datetime import datetime
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
    MATCHBOOK = "matchbook"
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

class OptimizationRequest(BaseModel):
    """Request model for optimization computations."""

    datetime_first_match: str | None = Field(
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
    l: int = Field(
        10,
        ge=1,
        le=100,
        description="Parameter l for utility function Linear (only used if utility_fn is Linear, variance constraint)"
    )
    divisor: float = Field(
        2.0,
        ge=1.0,
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


class PerformanceRequest(BaseModel):
    """Request model for fetching past performances."""
    
    optim_label: str = Field(
        "manual",
        min_length=1,
        max_length=50,
        description="Label for the optimization run"
    )
    datetime_first_match: str | None = Field(
        None,
        description="Start datetime for performance analysis (format: YYYY-MM-DD HH:MM:SS)"
    )
    datetime_last_match: str | None = Field(
        None,
        description="End datetime for performance analysis (format: YYYY-MM-DD HH:MM:SS)"
    )
    bankroll: float | None = Field(
        1.0,
        ge=0.01,
        le=1000000.0,
        description="Bankroll amount to consider for performance calculations"
    )
    divisor: float = Field(
        2.0,
        ge=1.0,
        description="Divisor of fractions of bankroll to apply to stakes"
    )

    @validator('datetime_first_match', 'datetime_last_match')
    def validate_datetime_format(cls, v):
        """Validate datetime format if provided."""
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise ValueError('Datetime must be in format YYYY-MM-DD HH:MM:SS')
        return v

    @validator('datetime_last_match')
    def validate_date_order(cls, v, values):
        """Validate that last_match is after first_match."""
        if v is not None and 'datetime_first_match' in values and values['datetime_first_match'] is not None:
            first_date = datetime.strptime(values['datetime_first_match'], '%Y-%m-%d %H:%M:%S')
            last_date = datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            if last_date <= first_date:
                raise ValueError('datetime_last_match must be after datetime_first_match')
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "optim_label": "manual",
                "datetime_first_match": "2024-01-01 00:00:00",
                "datetime_last_match": "2024-01-31 23:59:59"
            }
        }


class PerformanceGainsRequest(PerformanceRequest):
    """Request model for fetching past performance gains."""
    
    divisor: float = Field(
        2,
        ge=1,
        description="Divisor for gain calculations"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "optim_label": "manual",
                "datetime_first_match": "2024-01-01 00:00:00",
                "datetime_last_match": "2024-01-31 23:59:59",
                "divisor": 2
            }
        }
