"""Pydantic models for the Soccer Bet ML Optimizer API."""

from .requests import (
    BookmakerEnum,
    OptimMethodEnum,
    UtilityFunctionEnum,
    OptimizationRequest,
    PerformanceRequest,
    PerformanceGainsRequest,
    BotStrategyEnum,
)

from .responses import (
    APIResponse,
    OptimizationMetrics,
    OptimizationDurations,
    OptimizationResult,
    OptimizationResponse,
    MatchPerformance,
    PerformanceMetrics,
    PerformanceResponse,
    GainResult,
    PerformanceGainsResponse,
    HealthCheckResponse,
    ErrorResponse,
    BotStrategy,
)

__all__ = [
    # Enums
    "BookmakerEnum",
    "OptimMethodEnum", 
    "UtilityFunctionEnum",
    "BotStrategyEnum",
    
    # Request models
    "OptimizationRequest",
    "PerformanceRequest",
    "PerformanceGainsRequest",
    
    # Response models
    "APIResponse",
    "OptimizationMetrics",
    "OptimizationDurations",
    "OptimizationResult",
    "OptimizationResponse",
    "MatchPerformance",
    "PerformanceMetrics",
    "PerformanceResponse",
    "GainResult",
    "PerformanceGainsResponse",
    "HealthCheckResponse",
    "ErrorResponse",
    "BotStrategy",
]