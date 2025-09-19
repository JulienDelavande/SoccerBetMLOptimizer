"""Response models for the Soccer Bet ML Optimizer API."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class APIResponse(BaseModel):
    """Base response model for all API endpoints."""
    
    status: str = Field(description="Status of the request")
    message: Optional[str] = Field(None, description="Optional message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class OptimizationMetrics(BaseModel):
    """Model for optimization metrics."""
    
    total_return: float = Field(description="Total expected return")
    total_stake: float = Field(description="Total stake amount")
    roi: float = Field(description="Return on investment percentage")
    num_bets: int = Field(description="Number of recommended bets")
    max_bet_amount: float = Field(description="Maximum individual bet amount")
    min_bet_amount: float = Field(description="Minimum individual bet amount")
    avg_bet_amount: float = Field(description="Average bet amount")


class OptimizationDurations(BaseModel):
    """Model for optimization duration metrics."""
    
    data_fetch_duration: float = Field(description="Time spent fetching data (seconds)")
    optimization_duration: float = Field(description="Time spent on optimization (seconds)")
    total_duration: float = Field(description="Total processing time (seconds)")


class OptimizationResult(BaseModel):
    """Model for individual optimization result."""
    
    match_id: str = Field(description="Unique match identifier")
    home_team: str = Field(description="Home team name")
    away_team: str = Field(description="Away team name")
    match_datetime: str = Field(description="Match date and time")
    bookmaker: str = Field(description="Recommended bookmaker")
    bet_type: str = Field(description="Type of bet (e.g., 1X2, Over/Under)")
    bet_selection: str = Field(description="Specific bet selection")
    odds: float = Field(description="Odds for the bet")
    stake: float = Field(description="Recommended stake amount")
    expected_return: float = Field(description="Expected return from the bet")
    probability: float = Field(description="Estimated probability of success")
    kelly_fraction: Optional[float] = Field(None, description="Kelly criterion fraction")


class OptimizationResponse(APIResponse):
    """Response model for optimization computations."""
    
    results: List[OptimizationResult] = Field(description="List of optimization results")
    metrics: OptimizationMetrics = Field(description="Overall optimization metrics")
    durations: OptimizationDurations = Field(description="Performance timing information")
    parameters: Dict[str, Any] = Field(description="Parameters used for optimization")


class PredictionResult(BaseModel):
    """Model for individual prediction result."""
    
    prediction_id: str = Field(description="Unique prediction identifier")
    match_id: str = Field(description="Unique match identifier")
    home_team: str = Field(description="Home team name")
    away_team: str = Field(description="Away team name")
    match_datetime: str = Field(description="Match date and time")
    prediction_type: str = Field(description="Type of prediction")
    predicted_outcome: str = Field(description="Predicted outcome")
    confidence: float = Field(description="Confidence score (0-1)")
    odds: Optional[float] = Field(None, description="Associated odds")
    created_at: str = Field(description="Prediction creation timestamp")


class MatchPerformance(BaseModel):
    """Model for a complete match performance analysis."""
    
    # Match identification
    match_id: str | None = Field(None, description="Unique match identifier")
    game: str | None = Field(None, description="Game identifier")
    home_team: str | None = Field(None, description="Home team name")
    away_team: str | None = Field(None, description="Away team name")
    date_match: str | None = Field(None, description="Match date")
    time_match: str | None = Field(None, description="Match time")
    
    # Prediction data
    model: str | None = Field(None, description="ML model used")
    datetime_inference: str | None = Field(None, description="When inference was made")
    prob_home_win: float | None = Field(None, description="Predicted home win probability")
    prob_draw: float | None = Field(None, description="Predicted draw probability") 
    prob_away_win: float | None = Field(None, description="Predicted away win probability")
    
    # Betting data
    odds_home: float | None = Field(None, description="Home team odds")
    odds_draw: float | None = Field(None, description="Draw odds")
    odds_away: float | None = Field(None, description="Away team odds")
    bookmaker_home: str | None = Field(None, description="Bookmaker for home bet")
    bookmaker_draw: str | None = Field(None, description="Bookmaker for draw bet")
    bookmaker_away: str | None = Field(None, description="Bookmaker for away bet")
    bookmaker_home_key: str | None = Field(None, description="Bookmaker key for home bet")
    bookmaker_draw_key: str | None = Field(None, description="Bookmaker key for draw bet")
    bookmaker_away_key: str | None = Field(None, description="Bookmaker key for away bet")
    
    # Optimization results
    f_home: float | None = Field(None, description="Optimal fraction for home bet")
    f_draw: float | None = Field(None, description="Optimal fraction for draw bet")
    f_away: float | None = Field(None, description="Optimal fraction for away bet")
    utility_fn: str | None = Field(None, description="Utility function used")
    datetime_optim: str | None = Field(None, description="When optimization was performed")
    optim_label: str | None = Field(None, description="Optimization label")
    
    # Actual results
    home_goals: int | None = Field(None, description="Actual home team goals")
    away_goals: int | None = Field(None, description="Actual away team goals")
    match_result: str | None = Field(None, description="Actual match result (H/D/A)")
    
    # Performance metrics (calculated)
    stake_home: float | None = Field(None, description="Actual stake on home")
    stake_draw: float | None = Field(None, description="Actual stake on draw")
    stake_away: float | None = Field(None, description="Actual stake on away")
    total_stake: float | None = Field(None, description="Total stake for this match")
    payout: float | None = Field(None, description="Total payout received")
    profit_loss: float | None = Field(None, description="Net profit/loss for this match")

class PerformanceMetrics(BaseModel):
    """Model for overall performance metrics."""
    
    total_matches: int = Field(description="Total number of matches analyzed")
    total_bets_placed: int = Field(description="Total number of individual bets placed")
    total_stake: float = Field(description="Total amount staked")
    total_payout: float = Field(description="Total payout received")
    total_profit_loss: float = Field(description="Net profit/loss")
    roi_percentage: float = Field(description="Return on investment percentage")
    
    # Win/loss statistics
    winning_matches: int = Field(description="Number of profitable matches")
    losing_matches: int = Field(description="Number of losing matches")
    break_even_matches: int = Field(description="Number of break-even matches")
    win_rate: float = Field(description="Percentage of profitable matches")
    
    # Betting statistics
    home_bets: int = Field(description="Number of home team bets")
    draw_bets: int = Field(description="Number of draw bets")
    away_bets: int = Field(description="Number of away team bets")
    
    # Average values
    avg_stake_per_match: float = Field(description="Average stake per match")
    avg_profit_per_match: float = Field(description="Average profit per match")
    avg_odds: float = Field(description="Average odds across all bets")

class PerformanceResponse(APIResponse):
    """Response model for performance analysis."""
    
    matches: List[MatchPerformance] = Field(description="List of match performances")
    metrics: PerformanceMetrics = Field(description="Overall performance metrics")
    period: Dict[str, Any] = Field(description="Analysis period information")
    optim_label: str = Field(description="Optimization label analyzed")


class PerformanceMetrics(BaseModel):
    """Model for performance metrics."""
    
    total_bets: int = Field(description="Total number of bets")
    winning_bets: int = Field(description="Number of winning bets")
    losing_bets: int = Field(description="Number of losing bets")
    void_bets: int = Field(description="Number of void bets")
    win_rate: float = Field(description="Win rate percentage")
    total_stake: float = Field(description="Total amount staked")
    total_payout: float = Field(description="Total payout received")
    total_profit_loss: float = Field(description="Total profit or loss")
    roi: float = Field(description="Return on investment percentage")
    average_odds: float = Field(description="Average odds of bets placed")


class GainResult(BaseModel):
    """Model for gain calculation result."""
    
    period: str = Field(description="Time period for the gain calculation")
    initial_bankroll: float = Field(description="Starting bankroll amount")
    final_bankroll: float = Field(description="Ending bankroll amount")
    absolute_gain: float = Field(description="Absolute gain amount")
    percentage_gain: float = Field(description="Percentage gain")
    number_of_bets: int = Field(description="Number of bets in the period")
    average_bet_size: float = Field(description="Average bet size in the period")


class PerformanceGainsResponse(APIResponse):
    """Response model for performance gains."""
    
    gains: List[GainResult] = Field(description="List of gain calculations")
    total_gain: GainResult = Field(description="Overall gain summary")
    optim_label: str = Field(description="Optimization label used")
    divisor: int = Field(description="Divisor used for calculations")


class HealthCheckResponse(APIResponse):
    """Response model for health check endpoint."""
    
    uptime: float = Field(description="Service uptime in seconds")
    database_status: str = Field(description="Database connection status")
    services_status: Dict[str, str] = Field(description="Status of various services")

class ErrorResponse(APIResponse):
    """Response model for error cases."""
    
    error_code: str = Field(description="Specific error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "status": "error",
                "message": "Invalid request parameters",
                "timestamp": "2024-01-15T14:30:00",
                "error_code": "VALIDATION_ERROR",
                "error_details": {
                    "field": "datetime_first_match",
                    "issue": "Invalid datetime format"
                }
            }
        }
