"""
Soccer Bet ML Optimizer API

A comprehensive FastAPI application for soccer betting optimization using machine learning algorithms.
Provides endpoints for optimization computations, predictions fetching, and performance analysis.
"""

import time
import logging
from typing import List, Annotated
import datetime

from fastapi import FastAPI, HTTPException, status, Body, Query
import httpx

from app._config import PIPELINES_PROTOCOL, PIPELINES_HOST, PIPELINES_PORT, PIPELINES_ENDPOINT_OPTIMIZATION

from app.models import (
    OptimizationRequest,
    PerformanceRequest,
    PerformanceResponse,
    PerformanceGainsRequest,
    PerformanceGainsResponse,
    HealthCheckResponse,
    BookmakerEnum
)
from app.utils import (
    timing_decorator,
    format_performance_data,
    format_performance_gains_data,
)

from app.services.fetch_past_performances import fetch_past_performances_fn
from app.services.fetch_past_performances_gains import fetch_past_performances_gains_fn

logger = logging.getLogger("app-backend")

app = FastAPI(
    title="Soccer Bet ML Optimizer API",
    version="1.0.0",
    description="A comprehensive API for soccer betting optimization using machine learning algorithms."
)

app_start_time = time.time()

@app.get(
    "/",
    response_model=HealthCheckResponse,
    tags=["health"],
    summary="API Information",
    description="Get basic information about the Soccer Bet ML Optimizer API"
)
async def read_root() -> HealthCheckResponse:
    """Get API information and health status."""
    uptime = time.time() - app_start_time
    
    return HealthCheckResponse(
        status="success",
        message="Soccer Bet ML Optimizer API is operational",
        uptime=uptime,
        database_status="connected",  # TODO: Add actual DB health check
        services_status={
            "optimization_service": "operational",
            "prediction_service": "operational",
            "performance_service": "operational"
        }
    )


# Optimization endpoints
@app.post(
    "/optimize",
    tags=["optimization"],
    summary="Compute Betting Optimization",
    description="Compute optimal betting strategies using machine learning algorithms",
    responses={
        200: {"description": "Optimization completed successfully"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "Internal server error"}
    }
)
@timing_decorator
async def compute_optimization(
    request: Annotated[OptimizationRequest, Body()],
):
    """
    Compute optimal betting strategies for upcoming matches.
    
    This endpoint proxies requests to the pipelines microservice.
    """ 
    try:
        pipelines_url = f"{PIPELINES_PROTOCOL}://{PIPELINES_HOST}:{PIPELINES_PORT}/{PIPELINES_ENDPOINT_OPTIMIZATION}"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                pipelines_url,
                json=request.dict(),
                timeout=300.0  # 5 minutes timeout
            )
            response.raise_for_status()
        return response.json()
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error when calling pipelines service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Pipelines service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )

# Performance endpoints
@app.get(
    "/performance",
    response_model=PerformanceResponse,
    tags=["performance"],
    summary="Fetch Performance Data",
    description="Retrieve historical betting performance data for analysis"
)
@timing_decorator
async def fetch_performance(
    request: Annotated[PerformanceRequest, Query()]
) -> PerformanceResponse:
    """Fetch historical performance data."""
    
    try:
        results_df = fetch_past_performances_fn(
            optim_label=request.optim_label,
            datetime_first_match=request.datetime_first_match,
            datetime_last_match=request.datetime_last_match
        )
        
        # Use utility function to format performance data
        matches, metrics, period_info = format_performance_data(results_df, request.bankroll, request.divisor)

        # Add user-provided period info
        period_info.update({
            "start_date": request.datetime_first_match or (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S"),
            "end_date": request.datetime_last_match or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        logger.info(f"Fetched {len(matches)} performance records for {request.optim_label}")

        return PerformanceResponse(
            status="success",
            message="Performance analysis completed",
            matches=matches,
            metrics=metrics,
            period=period_info,
            optim_label=request.optim_label
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch performance data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch performance data: {str(e)}"
        )


@app.get(
    "/performance/gains",
    response_model=PerformanceGainsResponse,
    tags=["performance"],
    summary="Fetch Performance Gains",
    description="Calculate and retrieve performance gains over time periods"
)
@timing_decorator
async def fetch_performance_gains(
    request: Annotated[PerformanceGainsRequest, Query()]
    ) -> PerformanceGainsResponse:
    """Fetch performance gains data."""
    try:
        results_df = fetch_past_performances_gains_fn(
            optim_label=request.optim_label,
            datetime_first_match=request.datetime_first_match,
            datetime_last_match=request.datetime_last_match,
            divisor=request.divisor
        )
        
        # Use utility function to format gains data
        gains_data, total_gain = format_performance_gains_data(results_df, bankroll=request.bankroll)
        
        logger.info(f"Calculated gains for {len(gains_data)} days with divisor {request.divisor}")
        
        return PerformanceGainsResponse(
            status="success",
            message="Performance gains calculated successfully",
            gains=gains_data,
            total_gain=total_gain,
            optim_label=request.optim_label,
            divisor=request.divisor
        )
        
    except Exception as e:
        logger.error(f"Failed to calculate performance gains: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate performance gains: {str(e)}"
        )


# Additional utility endpoints
@app.get(
    "/bookmakers",
    response_model=List[str],
    tags=["utils"],
    summary="List Available Bookmakers",
    description="Get list of all supported bookmakers"
)
async def list_bookmakers() -> List[str]:
    """Get list of all supported bookmakers."""
    return [bookmaker.value for bookmaker in BookmakerEnum]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

