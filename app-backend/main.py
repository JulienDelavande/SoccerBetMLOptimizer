"""
Soccer Bet ML Optimizer API

A comprehensive FastAPI application for soccer betting optimization using machine learning algorithms.
Provides endpoints for optimization computations, predictions fetching, and performance analysis.
"""

import time
import logging
import os
from typing import List, Annotated
import datetime

from fastapi import FastAPI, HTTPException, status, Body, Query, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

from app._config import PIPELINES_PROTOCOL, PIPELINES_HOST, PIPELINES_PORT, PIPELINES_ENDPOINT_OPTIMIZATION
from app import auth
from app.services import users as users_service

from app.models import (
    OptimizationRequest,
    PerformanceRequest,
    PerformanceResponse,
    PerformanceGainsRequest,
    PerformanceGainsResponse,
    HealthCheckResponse,
    BookmakerEnum,
    BotStrategyEnum,
    BotStrategy
)
from app.utils import (
    timing_decorator,
    format_performance_data,
    format_performance_gains_data,
)

from app.services.fetch_past_performances import fetch_past_performances_fn
from app.services.fetch_past_performances_gains import fetch_past_performances_gains_fn
from app.services.site import match_detail, site_payload

logger = logging.getLogger("app-backend")

app = FastAPI(
    title="Soccer Bet ML Optimizer API",
    version="1.0.0",
    description="A comprehensive API for soccer betting optimization using machine learning algorithms."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "https://optibet.delavande.fr"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app_start_time = time.time()


@app.on_event("startup")
def warm_elo_cache() -> None:
    """Compute the Elo history in the background so the first match page is fast."""
    import threading

    from app.services.site import elo_ratings

    def warm():
        try:
            elo_ratings()
        except Exception:
            logger.exception("Elo warm-up failed")

    threading.Thread(target=warm, daemon=True).start()

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
        matches, metrics, period_info = format_performance_data(results_df, request.bankroll, request.divisor, request.bet_precision)

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


@app.get(
    "/site",
    tags=["site"],
    summary="Public site data",
    description="Value bets of the day, settled history, bankroll curve and track-record statistics",
)
def fetch_site(optim_label: str = "value_pinnacle") -> dict:
    try:
        return site_payload(optim_label)
    except Exception as e:
        logger.exception("Failed to build site payload")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to build site data: {e}")


@app.get(
    "/site/match/{match_id}",
    tags=["site"],
    summary="Public site match detail",
    description="Pinnacle line movement, bookmaker prices at bet time, form and head-to-head of a recommended bet",
)
def fetch_site_match(match_id: str, optim_label: str = "value_pinnacle") -> dict:
    try:
        detail = match_detail(optim_label, match_id)
    except Exception as e:
        logger.exception("Failed to build match detail")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to build match detail: {e}")
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown bet")
    return detail


# ---------------------------------------------------------------------------
# Account area (Google sign-in, personal settings, personal bet ledger)
# ---------------------------------------------------------------------------
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")


class GoogleLogin(BaseModel):
    credential: str  # Google ID token from Google Identity Services


class SettingsUpdate(BaseModel):
    bankroll: float | None = None
    risk_preset: str | None = None  # prudent | balanced | aggressive
    books: list[str] | None = None
    min_edge: float | None = None
    alerts_enabled: bool | None = None


class BetConfirm(BaseModel):
    match_id: str
    side: str
    recommended_price: float | None = None
    placed_price: float | None = None
    stake: float | None = None


class BetDelete(BaseModel):
    match_id: str
    side: str


@app.get("/config", tags=["account"], summary="Public frontend config")
def public_config() -> dict:
    """Non-secret config the frontend needs (Google client id, whether sign-in is on)."""
    return {"auth_enabled": auth.auth_configured(), "google_client_id": auth.GOOGLE_CLIENT_ID or "",
            "telegram_bot": TELEGRAM_BOT_USERNAME}


@app.post("/auth/google", tags=["account"], summary="Sign in with a Google ID token")
def auth_google(body: GoogleLogin, response: Response) -> dict:
    claims = auth.verify_google_token(body.credential)
    uid = users_service.upsert_user(claims)
    auth.issue_session(response, uid)
    return {"user": users_service.get_profile(uid)}


@app.get("/auth/me", tags=["account"], summary="Current user (null if anonymous)")
def auth_me(uid: int | None = Depends(auth.optional_user)) -> dict:
    return {"user": users_service.get_profile(uid) if uid is not None else None}


@app.post("/auth/logout", tags=["account"], summary="Sign out")
def auth_logout(response: Response) -> dict:
    auth.clear_session(response)
    return {"status": "ok"}


@app.delete("/account", tags=["account"], summary="Delete account and all personal data")
def delete_account(response: Response, uid: int = Depends(auth.require_user)) -> dict:
    users_service.delete_account(uid)
    auth.clear_session(response)
    return {"status": "deleted"}


@app.get("/me/settings", tags=["account"], summary="Personal settings")
def get_settings(uid: int = Depends(auth.require_user)) -> dict:
    return {"user": users_service.get_profile(uid)}


@app.put("/me/settings", tags=["account"], summary="Update personal settings")
def put_settings(body: SettingsUpdate, uid: int = Depends(auth.require_user)) -> dict:
    try:
        return {"user": users_service.update_settings(uid, **body.model_dump(exclude_none=True))}
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@app.get("/me/bets", tags=["account"], summary="Personal ledger and stats")
def get_my_bets(uid: int = Depends(auth.require_user)) -> dict:
    df = users_service.ledger(uid)
    return {"bets": df.to_dict(orient="records"), "stats": users_service.personal_stats(uid)}


@app.post("/me/bets", tags=["account"], summary="Confirm a placed bet")
def post_my_bet(body: BetConfirm, uid: int = Depends(auth.require_user)) -> dict:
    users_service.confirm_bet(uid, body.match_id, body.side, body.recommended_price, body.placed_price, body.stake)
    return {"status": "ok"}


@app.delete("/me/bets", tags=["account"], summary="Remove a confirmed bet")
def delete_my_bet(body: BetDelete, uid: int = Depends(auth.require_user)) -> dict:
    users_service.remove_bet(uid, body.match_id, body.side)
    return {"status": "ok"}


@app.post("/me/telegram/link", tags=["account"], summary="Get a Telegram linking code")
def telegram_link(uid: int = Depends(auth.require_user)) -> dict:
    return {"code": users_service.telegram_link_code(uid), "bot": TELEGRAM_BOT_USERNAME}


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

@app.get(
    "/bot_strategies",
    response_model=List[BotStrategy],
    tags=["utils"],
    summary="List Bot Strategies",
    description="Get list of all available bot strategies with keys and display names"
)
async def list_bot_strategies() -> List[BotStrategy]:
    """Get list of all available bot strategies with keys and display names."""
    return [
        BotStrategy(
            key=strategy.key,
            name=strategy.display_name
        )
        for strategy in BotStrategyEnum
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

