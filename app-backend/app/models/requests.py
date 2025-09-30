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
    l: float = Field(
        10.0,
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
        ge=0,
        description="Divisor of fractions of bankroll to apply to stakes"
    )
    bet_precision: float = Field(
        0.01,
        gt=0,
        description="Precision level for bet amounts (e.g., 0.01 for centime, 0.1 for dizaine de centimes, 1.0 for euro)"
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
                "datetime_last_match": "2024-01-31 23:59:59",
                "bet_precision": 0.01
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

class BotStrategyEnum(Enum):
    """Enumeration for bot strategies with key and display name."""
    # Same Day strategies
    AUTO_SAME_DAY_KELLY = ("auto_same_day_kelly", "Same Day Kelly")
    AUTO_SAME_DAY_LINEAR_L10 = ("auto_same_day_linear_l10", "Same Day Linear L10")
    AUTO_SAME_DAY_LOG = ("auto_same_day_log", "Same Day Log")
    AUTO_SAME_DAY_EXP = ("auto_same_day_exp", "Same Day Exp")
    AUTO_SAME_DAY_CRRA_G05 = ("auto_same_day_crra_g05", "Same Day CRRA G0.5")
    
    # Same Day FR bookmakers
    AUTO_SAME_DAY_KELLY_FR = ("auto_same_day_kelly_fr", "Same Day Kelly FR")
    AUTO_SAME_DAY_LOG_FR = ("auto_same_day_log_fr", "Same Day Log FR")
    AUTO_SAME_DAY_EXP_FR = ("auto_same_day_exp_fr", "Same Day Exp FR")
    
    # Same Day 1xBet
    AUTO_SAME_DAY_KELLY_1XBET = ("auto_same_day_kelly_1xbet", "Same Day Kelly 1xBet")
    AUTO_SAME_DAY_LOG_1XBET = ("auto_same_day_log_1xbet", "Same Day Log 1xBet")
    AUTO_SAME_DAY_EXP_1XBET = ("auto_same_day_exp_1xbet", "Same Day Exp 1xBet")
    
    # Same Day CRRA risk aversions
    AUTO_SAME_DAY_CRRA_G02 = ("auto_same_day_crra_g02", "Same Day CRRA G0.2")
    AUTO_SAME_DAY_CRRA_G04 = ("auto_same_day_crra_g04", "Same Day CRRA G0.4")
    AUTO_SAME_DAY_CRRA_G06 = ("auto_same_day_crra_g06", "Same Day CRRA G0.6")
    AUTO_SAME_DAY_CRRA_G08 = ("auto_same_day_crra_g08", "Same Day CRRA G0.8")
    AUTO_SAME_DAY_CRRA_G1 = ("auto_same_day_crra_g1", "Same Day CRRA G1")
    AUTO_SAME_DAY_CRRA_G2 = ("auto_same_day_crra_g2", "Same Day CRRA G2")
    AUTO_SAME_DAY_CRRA_G5 = ("auto_same_day_crra_g5", "Same Day CRRA G5")
    AUTO_SAME_DAY_CRRA_G10 = ("auto_same_day_crra_g10", "Same Day CRRA G10")
    
    # Same Day CRRA FR
    AUTO_SAME_DAY_CRRA_G02_FR = ("auto_same_day_crra_g02_fr", "Same Day CRRA G0.2 FR")
    AUTO_SAME_DAY_CRRA_G05_FR = ("auto_same_day_crra_g05_fr", "Same Day CRRA G0.5 FR")
    AUTO_SAME_DAY_CRRA_G08_FR = ("auto_same_day_crra_g08_fr", "Same Day CRRA G0.8 FR")
    AUTO_SAME_DAY_CRRA_G1_FR = ("auto_same_day_crra_g1_fr", "Same Day CRRA G1 FR")
    AUTO_SAME_DAY_CRRA_G2_FR = ("auto_same_day_crra_g2_fr", "Same Day CRRA G2 FR")
    
    # Same Day CRRA 1xBet
    AUTO_SAME_DAY_CRRA_G02_1XBET = ("auto_same_day_crra_g02_1xbet", "Same Day CRRA G0.2 1xBet")
    AUTO_SAME_DAY_CRRA_G05_1XBET = ("auto_same_day_crra_g05_1xbet", "Same Day CRRA G0.5 1xBet")
    AUTO_SAME_DAY_CRRA_G08_1XBET = ("auto_same_day_crra_g08_1xbet", "Same Day CRRA G0.8 1xBet")
    AUTO_SAME_DAY_CRRA_G1_1XBET = ("auto_same_day_crra_g1_1xbet", "Same Day CRRA G1 1xBet")
    AUTO_SAME_DAY_CRRA_G2_1XBET = ("auto_same_day_crra_g2_1xbet", "Same Day CRRA G2 1xBet")
    
    # Same Day Linear risk aversions
    AUTO_SAME_DAY_LINEAR_L1 = ("auto_same_day_linear_l1", "Same Day Linear L1")
    AUTO_SAME_DAY_LINEAR_L2 = ("auto_same_day_linear_l2", "Same Day Linear L2")
    AUTO_SAME_DAY_LINEAR_L4 = ("auto_same_day_linear_l4", "Same Day Linear L4")
    AUTO_SAME_DAY_LINEAR_L6 = ("auto_same_day_linear_l6", "Same Day Linear L6")
    AUTO_SAME_DAY_LINEAR_L8 = ("auto_same_day_linear_l8", "Same Day Linear L8")
    AUTO_SAME_DAY_LINEAR_L15 = ("auto_same_day_linear_l15", "Same Day Linear L15")
    AUTO_SAME_DAY_LINEAR_L20 = ("auto_same_day_linear_l20", "Same Day Linear L20")
    AUTO_SAME_DAY_LINEAR_L50 = ("auto_same_day_linear_l50", "Same Day Linear L50")
    
    # Same Day Linear FR
    AUTO_SAME_DAY_LINEAR_L2_FR = ("auto_same_day_linear_l2_fr", "Same Day Linear L2 FR")
    AUTO_SAME_DAY_LINEAR_L5_FR = ("auto_same_day_linear_l5_fr", "Same Day Linear L5 FR")
    AUTO_SAME_DAY_LINEAR_L10_FR = ("auto_same_day_linear_l10_fr", "Same Day Linear L10 FR")
    AUTO_SAME_DAY_LINEAR_L20_FR = ("auto_same_day_linear_l20_fr", "Same Day Linear L20 FR")
    
    # Same Day Linear 1xBet
    AUTO_SAME_DAY_LINEAR_L2_1XBET = ("auto_same_day_linear_l2_1xbet", "Same Day Linear L2 1xBet")
    AUTO_SAME_DAY_LINEAR_L5_1XBET = ("auto_same_day_linear_l5_1xbet", "Same Day Linear L5 1xBet")
    AUTO_SAME_DAY_LINEAR_L10_1XBET = ("auto_same_day_linear_l10_1xbet", "Same Day Linear L10 1xBet")
    AUTO_SAME_DAY_LINEAR_L20_1XBET = ("auto_same_day_linear_l20_1xbet", "Same Day Linear L20 1xBet")
    
    # Same Day Exp risk aversions
    AUTO_SAME_DAY_EXP_A02 = ("auto_same_day_exp_a02", "Same Day Exp A0.2")
    AUTO_SAME_DAY_EXP_A04 = ("auto_same_day_exp_a04", "Same Day Exp A0.4")
    AUTO_SAME_DAY_EXP_A06 = ("auto_same_day_exp_a06", "Same Day Exp A0.6")
    AUTO_SAME_DAY_EXP_A08 = ("auto_same_day_exp_a08", "Same Day Exp A0.8")
    AUTO_SAME_DAY_EXP_A2 = ("auto_same_day_exp_a2", "Same Day Exp A2")
    AUTO_SAME_DAY_EXP_A5 = ("auto_same_day_exp_a5", "Same Day Exp A5")
    AUTO_SAME_DAY_EXP_A10 = ("auto_same_day_exp_a10", "Same Day Exp A10")
    
    # Same Day Exp FR
    AUTO_SAME_DAY_EXP_A05_FR = ("auto_same_day_exp_a05_fr", "Same Day Exp A0.5 FR")
    AUTO_SAME_DAY_EXP_A1_FR = ("auto_same_day_exp_a1_fr", "Same Day Exp A1 FR")
    AUTO_SAME_DAY_EXP_A2_FR = ("auto_same_day_exp_a2_fr", "Same Day Exp A2 FR")
    AUTO_SAME_DAY_EXP_A5_FR = ("auto_same_day_exp_a5_fr", "Same Day Exp A5 FR")
    
    # Same Day Exp 1xBet
    AUTO_SAME_DAY_EXP_A05_1XBET = ("auto_same_day_exp_a05_1xbet", "Same Day Exp A0.5 1xBet")
    AUTO_SAME_DAY_EXP_A1_1XBET = ("auto_same_day_exp_a1_1xbet", "Same Day Exp A1 1xBet")
    AUTO_SAME_DAY_EXP_A2_1XBET = ("auto_same_day_exp_a2_1xbet", "Same Day Exp A2 1xBet")
    AUTO_SAME_DAY_EXP_A5_1XBET = ("auto_same_day_exp_a5_1xbet", "Same Day Exp A5 1xBet")
    
    # Next 5 strategies
    AUTO_NEXT5_KELLY = ("auto_next5_kelly", "Next 5 Kelly")
    AUTO_NEXT5_LINEAR_L10 = ("auto_next5_linear_l10", "Next 5 Linear L10")
    AUTO_NEXT5_LOG = ("auto_next5_log", "Next 5 Log")
    AUTO_NEXT5_EXP = ("auto_next5_exp", "Next 5 Exp")
    AUTO_NEXT5_CRRA_G05 = ("auto_next5_crra_g05", "Next 5 CRRA G0.5")
    AUTO_NEXT5_KELLY_FR = ("auto_next5_kelly_fr", "Next 5 Kelly FR")
    AUTO_NEXT5_LINEAR_L10_FR = ("auto_next5_linear_l10_fr", "Next 5 Linear L10 FR")
    AUTO_NEXT5_LOG_FR = ("auto_next5_log_fr", "Next 5 Log FR")
    AUTO_NEXT5_EXP_FR = ("auto_next5_exp_fr", "Next 5 Exp FR")
    AUTO_NEXT5_KELLY_1XBET = ("auto_next5_kelly_1xbet", "Next 5 Kelly 1xBet")
    AUTO_NEXT5_LINEAR_L10_1XBET = ("auto_next5_linear_l10_1xbet", "Next 5 Linear L10 1xBet")
    AUTO_NEXT5_LOG_1XBET = ("auto_next5_log_1xbet", "Next 5 Log 1xBet")
    AUTO_NEXT5_CRRA_G05_FR = ("auto_next5_crra_g05_fr", "Next 5 CRRA G0.5 FR")
    AUTO_NEXT5_CRRA_G1_FR = ("auto_next5_crra_g1_fr", "Next 5 CRRA G1 FR")
    AUTO_NEXT5_CRRA_G2_FR = ("auto_next5_crra_g2_fr", "Next 5 CRRA G2 FR")
    AUTO_NEXT5_LINEAR_L5_FR = ("auto_next5_linear_l5_fr", "Next 5 Linear L5 FR")
    AUTO_NEXT5_LINEAR_L15_FR = ("auto_next5_linear_l15_fr", "Next 5 Linear L15 FR")
    AUTO_NEXT5_EXP_A1_FR = ("auto_next5_exp_a1_fr", "Next 5 Exp A1 FR")
    AUTO_NEXT5_EXP_A2_FR = ("auto_next5_exp_a2_fr", "Next 5 Exp A2 FR")
    
    # Next 10 strategies
    AUTO_NEXT10_KELLY = ("auto_next10_kelly", "Next 10 Kelly")
    AUTO_NEXT10_LINEAR_L10 = ("auto_next10_linear_l10", "Next 10 Linear L10")
    AUTO_NEXT10_LOG = ("auto_next10_log", "Next 10 Log")
    AUTO_NEXT10_EXP = ("auto_next10_exp", "Next 10 Exp")
    AUTO_NEXT10_CRRA_G05 = ("auto_next10_crra_g05", "Next 10 CRRA G0.5")
    AUTO_NEXT10_KELLY_FR = ("auto_next10_kelly_fr", "Next 10 Kelly FR")
    AUTO_NEXT10_LINEAR_L10_FR = ("auto_next10_linear_l10_fr", "Next 10 Linear L10 FR")
    AUTO_NEXT10_LOG_FR = ("auto_next10_log_fr", "Next 10 Log FR")
    AUTO_NEXT10_EXP_FR = ("auto_next10_exp_fr", "Next 10 Exp FR")
    AUTO_NEXT10_KELLY_1XBET = ("auto_next10_kelly_1xbet", "Next 10 Kelly 1xBet")
    AUTO_NEXT10_LINEAR_L10_1XBET = ("auto_next10_linear_l10_1xbet", "Next 10 Linear L10 1xBet")
    AUTO_NEXT10_LOG_1XBET = ("auto_next10_log_1xbet", "Next 10 Log 1xBet")
    AUTO_NEXT10_EXP_1XBET = ("auto_next10_exp_1xbet", "Next 10 Exp 1xBet")
    
    # Next 10 CRRA
    AUTO_NEXT10_CRRA_G02 = ("auto_next10_crra_g02", "Next 10 CRRA G0.2")
    AUTO_NEXT10_CRRA_G04 = ("auto_next10_crra_g04", "Next 10 CRRA G0.4")
    AUTO_NEXT10_CRRA_G06 = ("auto_next10_crra_g06", "Next 10 CRRA G0.6")
    AUTO_NEXT10_CRRA_G08 = ("auto_next10_crra_g08", "Next 10 CRRA G0.8")
    AUTO_NEXT10_CRRA_G1 = ("auto_next10_crra_g1", "Next 10 CRRA G1")
    AUTO_NEXT10_CRRA_G2 = ("auto_next10_crra_g2", "Next 10 CRRA G2")
    AUTO_NEXT10_CRRA_G5 = ("auto_next10_crra_g5", "Next 10 CRRA G5")
    AUTO_NEXT10_CRRA_G10 = ("auto_next10_crra_g10", "Next 10 CRRA G10")
    
    # Next 10 CRRA FR
    AUTO_NEXT10_CRRA_G02_FR = ("auto_next10_crra_g02_fr", "Next 10 CRRA G0.2 FR")
    AUTO_NEXT10_CRRA_G05_FR = ("auto_next10_crra_g05_fr", "Next 10 CRRA G0.5 FR")
    AUTO_NEXT10_CRRA_G08_FR = ("auto_next10_crra_g08_fr", "Next 10 CRRA G0.8 FR")
    AUTO_NEXT10_CRRA_G1_FR = ("auto_next10_crra_g1_fr", "Next 10 CRRA G1 FR")
    AUTO_NEXT10_CRRA_G2_FR = ("auto_next10_crra_g2_fr", "Next 10 CRRA G2 FR")
    
    # Next 10 CRRA 1xBet
    AUTO_NEXT10_CRRA_G02_1XBET = ("auto_next10_crra_g02_1xbet", "Next 10 CRRA G0.2 1xBet")
    AUTO_NEXT10_CRRA_G05_1XBET = ("auto_next10_crra_g05_1xbet", "Next 10 CRRA G0.5 1xBet")
    AUTO_NEXT10_CRRA_G08_1XBET = ("auto_next10_crra_g08_1xbet", "Next 10 CRRA G0.8 1xBet")
    AUTO_NEXT10_CRRA_G1_1XBET = ("auto_next10_crra_g1_1xbet", "Next 10 CRRA G1 1xBet")
    AUTO_NEXT10_CRRA_G2_1XBET = ("auto_next10_crra_g2_1xbet", "Next 10 CRRA G2 1xBet")
    
    # Next 10 Linear
    AUTO_NEXT10_LINEAR_L1 = ("auto_next10_linear_l1", "Next 10 Linear L1")
    AUTO_NEXT10_LINEAR_L2 = ("auto_next10_linear_l2", "Next 10 Linear L2")
    AUTO_NEXT10_LINEAR_L4 = ("auto_next10_linear_l4", "Next 10 Linear L4")
    AUTO_NEXT10_LINEAR_L6 = ("auto_next10_linear_l6", "Next 10 Linear L6")
    AUTO_NEXT10_LINEAR_L8 = ("auto_next10_linear_l8", "Next 10 Linear L8")
    AUTO_NEXT10_LINEAR_L15 = ("auto_next10_linear_l15", "Next 10 Linear L15")
    AUTO_NEXT10_LINEAR_L20 = ("auto_next10_linear_l20", "Next 10 Linear L20")
    AUTO_NEXT10_LINEAR_L50 = ("auto_next10_linear_l50", "Next 10 Linear L50")
    
    # Next 10 Linear FR
    AUTO_NEXT10_LINEAR_L2_FR = ("auto_next10_linear_l2_fr", "Next 10 Linear L2 FR")
    AUTO_NEXT10_LINEAR_L5_FR = ("auto_next10_linear_l5_fr", "Next 10 Linear L5 FR")
    AUTO_NEXT10_LINEAR_L20_FR = ("auto_next10_linear_l20_fr", "Next 10 Linear L20 FR")
    
    # Next 10 Linear 1xBet
    AUTO_NEXT10_LINEAR_L2_1XBET = ("auto_next10_linear_l2_1xbet", "Next 10 Linear L2 1xBet")
    AUTO_NEXT10_LINEAR_L5_1XBET = ("auto_next10_linear_l5_1xbet", "Next 10 Linear L5 1xBet")
    AUTO_NEXT10_LINEAR_L20_1XBET = ("auto_next10_linear_l20_1xbet", "Next 10 Linear L20 1xBet")
    
    # Next 10 Exp
    AUTO_NEXT10_EXP_A02 = ("auto_next10_exp_a02", "Next 10 Exp A0.2")
    AUTO_NEXT10_EXP_A04 = ("auto_next10_exp_a04", "Next 10 Exp A0.4")
    AUTO_NEXT10_EXP_A06 = ("auto_next10_exp_a06", "Next 10 Exp A0.6")
    AUTO_NEXT10_EXP_A08 = ("auto_next10_exp_a08", "Next 10 Exp A0.8")
    AUTO_NEXT10_EXP_A2 = ("auto_next10_exp_a2", "Next 10 Exp A2")
    AUTO_NEXT10_EXP_A5 = ("auto_next10_exp_a5", "Next 10 Exp A5")
    AUTO_NEXT10_EXP_A10 = ("auto_next10_exp_a10", "Next 10 Exp A10")
    
    # Next 10 Exp FR
    AUTO_NEXT10_EXP_A05_FR = ("auto_next10_exp_a05_fr", "Next 10 Exp A0.5 FR")
    AUTO_NEXT10_EXP_A1_FR = ("auto_next10_exp_a1_fr", "Next 10 Exp A1 FR")
    AUTO_NEXT10_EXP_A2_FR = ("auto_next10_exp_a2_fr", "Next 10 Exp A2 FR")
    AUTO_NEXT10_EXP_A5_FR = ("auto_next10_exp_a5_fr", "Next 10 Exp A5 FR")
    
    # Next 10 Exp 1xBet
    AUTO_NEXT10_EXP_A05_1XBET = ("auto_next10_exp_a05_1xbet", "Next 10 Exp A0.5 1xBet")
    AUTO_NEXT10_EXP_A1_1XBET = ("auto_next10_exp_a1_1xbet", "Next 10 Exp A1 1xBet")
    AUTO_NEXT10_EXP_A2_1XBET = ("auto_next10_exp_a2_1xbet", "Next 10 Exp A2 1xBet")
    AUTO_NEXT10_EXP_A5_1XBET = ("auto_next10_exp_a5_1xbet", "Next 10 Exp A5 1xBet")
    
    # Next 15 strategies
    AUTO_NEXT15_KELLY = ("auto_next15_kelly", "Next 15 Kelly")
    AUTO_NEXT15_LINEAR_L10 = ("auto_next15_linear_l10", "Next 15 Linear L10")
    AUTO_NEXT15_LOG = ("auto_next15_log", "Next 15 Log")
    AUTO_NEXT15_EXP = ("auto_next15_exp", "Next 15 Exp")
    AUTO_NEXT15_CRRA_G05 = ("auto_next15_crra_g05", "Next 15 CRRA G0.5")
    AUTO_NEXT15_KELLY_FR = ("auto_next15_kelly_fr", "Next 15 Kelly FR")
    AUTO_NEXT15_LINEAR_L10_FR = ("auto_next15_linear_l10_fr", "Next 15 Linear L10 FR")
    AUTO_NEXT15_LOG_FR = ("auto_next15_log_fr", "Next 15 Log FR")
    AUTO_NEXT15_EXP_FR = ("auto_next15_exp_fr", "Next 15 Exp FR")
    AUTO_NEXT15_KELLY_1XBET = ("auto_next15_kelly_1xbet", "Next 15 Kelly 1xBet")
    AUTO_NEXT15_LINEAR_L10_1XBET = ("auto_next15_linear_l10_1xbet", "Next 15 Linear L10 1xBet")
    AUTO_NEXT15_LOG_1XBET = ("auto_next15_log_1xbet", "Next 15 Log 1xBet")
    AUTO_NEXT15_CRRA_G05_FR = ("auto_next15_crra_g05_fr", "Next 15 CRRA G0.5 FR")
    AUTO_NEXT15_CRRA_G1_FR = ("auto_next15_crra_g1_fr", "Next 15 CRRA G1 FR")
    AUTO_NEXT15_CRRA_G2_FR = ("auto_next15_crra_g2_fr", "Next 15 CRRA G2 FR")
    AUTO_NEXT15_LINEAR_L5_FR = ("auto_next15_linear_l5_fr", "Next 15 Linear L5 FR")
    AUTO_NEXT15_LINEAR_L15_FR = ("auto_next15_linear_l15_fr", "Next 15 Linear L15 FR")
    AUTO_NEXT15_LINEAR_L25_FR = ("auto_next15_linear_l25_fr", "Next 15 Linear L25 FR")
    AUTO_NEXT15_EXP_A1_FR = ("auto_next15_exp_a1_fr", "Next 15 Exp A1 FR")
    AUTO_NEXT15_EXP_A3_FR = ("auto_next15_exp_a3_fr", "Next 15 Exp A3 FR")
    
    # Next 20 strategies
    AUTO_NEXT20_KELLY = ("auto_next20_kelly", "Next 20 Kelly")
    AUTO_NEXT20_LINEAR_L10 = ("auto_next20_linear_l10", "Next 20 Linear L10")
    AUTO_NEXT20_LOG = ("auto_next20_log", "Next 20 Log")
    AUTO_NEXT20_EXP = ("auto_next20_exp", "Next 20 Exp")
    AUTO_NEXT20_CRRA_G05 = ("auto_next20_crra_g05", "Next 20 CRRA G0.5")
    AUTO_NEXT20_KELLY_FR = ("auto_next20_kelly_fr", "Next 20 Kelly FR")
    AUTO_NEXT20_LINEAR_L10_FR = ("auto_next20_linear_l10_fr", "Next 20 Linear L10 FR")
    AUTO_NEXT20_LOG_FR = ("auto_next20_log_fr", "Next 20 Log FR")
    AUTO_NEXT20_EXP_FR = ("auto_next20_exp_fr", "Next 20 Exp FR")
    AUTO_NEXT20_KELLY_1XBET = ("auto_next20_kelly_1xbet", "Next 20 Kelly 1xBet")
    AUTO_NEXT20_LINEAR_L10_1XBET = ("auto_next20_linear_l10_1xbet", "Next 20 Linear L10 1xBet")
    AUTO_NEXT20_LOG_1XBET = ("auto_next20_log_1xbet", "Next 20 Log 1xBet")
    AUTO_NEXT20_CRRA_G05_FR = ("auto_next20_crra_g05_fr", "Next 20 CRRA G0.5 FR")
    AUTO_NEXT20_CRRA_G1_FR = ("auto_next20_crra_g1_fr", "Next 20 CRRA G1 FR")
    AUTO_NEXT20_CRRA_G2_FR = ("auto_next20_crra_g2_fr", "Next 20 CRRA G2 FR")
    AUTO_NEXT20_CRRA_G5_FR = ("auto_next20_crra_g5_fr", "Next 20 CRRA G5 FR")
    AUTO_NEXT20_LINEAR_L5_FR = ("auto_next20_linear_l5_fr", "Next 20 Linear L5 FR")
    AUTO_NEXT20_LINEAR_L15_FR = ("auto_next20_linear_l15_fr", "Next 20 Linear L15 FR")
    AUTO_NEXT20_LINEAR_L30_FR = ("auto_next20_linear_l30_fr", "Next 20 Linear L30 FR")
    AUTO_NEXT20_EXP_A1_FR = ("auto_next20_exp_a1_fr", "Next 20 Exp A1 FR")
    AUTO_NEXT20_EXP_A4_FR = ("auto_next20_exp_a4_fr", "Next 20 Exp A4 FR")
    
    @property
    def key(self) -> str:
        """Get the strategy key."""
        return self.value[0]
    
    @property
    def display_name(self) -> str:
        """Get the strategy display name."""
        return self.value[1]
