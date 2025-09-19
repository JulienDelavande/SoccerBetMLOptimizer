"""Pydantic models for the Soccer Bet ML Optimizer API."""

from .requests import (
    BookmakerEnum,
    OptimMethodEnum,
    UtilityFunctionEnum,
    OptimizationRequest,
    PerformanceRequest,
    PerformanceGainsRequest,
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
)

__all__ = [
    # Enums
    "BookmakerEnum",
    "OptimMethodEnum", 
    "UtilityFunctionEnum",
    
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
]