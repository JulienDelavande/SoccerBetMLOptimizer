from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service health status")
    timestamp: float = Field(..., description="Response timestamp")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")


class StandardResponse(BaseModel):
    """Standard API response model"""
    status: str = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[Any] = Field(None, description="Response data")


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = Field("error", description="Response status")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Error details")


class PredictionRequest(BaseModel):
    """Prediction computation request model"""
    datetime_first_match: Optional[str] = Field(
        None, description="Datetime of the first match (YYYY-MM-DD HH:MM:SS)"
    )
    n_matches: Optional[int] = Field(
        None, ge=1, le=100, description="Number of matches to analyze"
    )
    bookmakers: Optional[str] = Field(
        None, description="Comma-separated list of bookmakers"
    )
    bankroll: Optional[float] = Field(
        1.0, ge=0.01, le=1000000, description="Initial bankroll amount"
    )
    method: Optional[str] = Field(
        "SLSQP", description="Optimization method"
    )
    utility_fn: Optional[str] = Field(
        "Kelly", description="Utility function"
    )
    same_day: Optional[bool] = Field(
        False, description="Only consider matches on the same day"
    )


class MatchPrediction(BaseModel):
    """Single match prediction model"""
    match_id: str = Field(..., description="Unique match identifier")
    sport_key: str = Field(..., description="Sport key")
    game: str = Field(..., description="Match description")
    date_match: str = Field(..., description="Match date")
    time_match: str = Field(..., description="Match time")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    model: str = Field(..., description="ML model used")
    datetime_inference: str = Field(..., description="Inference timestamp")
    prob_home_win: float = Field(..., ge=0, le=1, description="Home win probability")
    prob_draw: float = Field(..., ge=0, le=1, description="Draw probability")
    prob_away_win: float = Field(..., ge=0, le=1, description="Away win probability")
    odds_home: float = Field(..., gt=0, description="Home win odds")
    odds_draw: float = Field(..., gt=0, description="Draw odds")
    odds_away: float = Field(..., gt=0, description="Away win odds")
    bookmaker_home: str = Field(..., description="Best bookmaker for home win")
    bookmaker_draw: str = Field(..., description="Best bookmaker for draw")
    bookmaker_away: str = Field(..., description="Best bookmaker for away win")
    f_home: float = Field(..., ge=0, description="Fraction to bet on home")
    f_draw: float = Field(..., ge=0, description="Fraction to bet on draw")
    f_away: float = Field(..., ge=0, description="Fraction to bet on away")
    datetime_optim: str = Field(..., description="Optimization timestamp")
    utility_fn: str = Field(..., description="Utility function used")


class PredictionResponse(BaseModel):
    """Prediction response model"""
    status: str = Field("success", description="Response status")
    df_optim_results: List[MatchPrediction] = Field(
        ..., description="Optimization results"
    )
    metrics: dict = Field(..., description="Performance metrics")
    durations: dict = Field(..., description="Execution time metrics")


class DataIngestionResponse(BaseModel):
    """Data ingestion response model"""
    status: str = Field("success", description="Response status")
    inserted_rows: int = Field(..., ge=0, description="Number of rows inserted")
    first_row: Optional[str] = Field(None, description="First row summary")
    last_row: Optional[str] = Field(None, description="Last row summary")


class MLInferenceRequest(BaseModel):
    """ML inference request model"""
    date_stop: Optional[str] = Field(
        None, description="Stop date for inference (YYYY-MM-DD HH:MM:SS)"
    )


class MLInferenceResponse(BaseModel):
    """ML inference response model"""
    status: str = Field("success", description="Response status")
    datetime_inference: str = Field(..., description="Inference timestamp")
    train_test_metrics: dict = Field(..., description="Model performance metrics")
    nb_matches_infered: int = Field(..., ge=0, description="Number of matches processed")
    first_match_name: str = Field(..., description="First match name")
    last_match_name: str = Field(..., description="Last match name")


class OptimizationRequest(BaseModel):
    """Optimization request model"""
    datetime_first_match: Optional[str] = Field(
        None, description="First match datetime"
    )
    model: str = Field("RSF_PR_LR", description="ML model to use")
    n_matches: Optional[int] = Field(None, ge=1, description="Number of matches")
    same_day: bool = Field(False, description="Same day optimization")
    bookmakers: Optional[str] = Field(None, description="Bookmakers list")
    bankroll: float = Field(1.0, gt=0, description="Bankroll amount")
    method: str = Field("SLSQP", description="Optimization method")
    utility_fn: str = Field("Kelly", description="Utility function")
    optim_label: str = Field("manual", description="Optimization label")


class OptimizationResponse(BaseModel):
    """Optimization response model"""
    status: str = Field("success", description="Response status")
    datetime_optim: str = Field(..., description="Optimization timestamp")
    optim_label: str = Field(..., description="Optimization label")
    df_results: List[dict] = Field(..., description="Optimization results")