from datetime import datetime
from typing import Any, List

from pydantic import BaseModel, Field


class ValueBetsRequest(BaseModel):
    books: List[str] = Field(default=["onexbet"], description="Bookmakers where bets can be placed")
    min_edge: float = Field(default=0.02, ge=0, le=0.5, description="Minimum p*price-1 to bet")
    max_price: float = Field(default=3.5, gt=1, le=50, description="Ignore prices above this")
    kelly_fraction: float = Field(default=0.25, gt=0, le=1)
    max_stake: float = Field(default=0.05, gt=0, le=1, description="Cap per bet, share of bankroll")
    max_total: float = Field(default=0.30, gt=0, le=1, description="Cap per run, share of bankroll")
    blend_weight: float = Field(default=0.1, ge=0, le=1, description="Model weight blended with Pinnacle")
    fresh_hours: float = Field(default=6.0, gt=0, description="Max lag of a soft price behind Pinnacle's update")
    model: str = "RSF_PR_LR"
    optim_label: str = "value_pinnacle_1xbet"
    min_minutes_before_kickoff: int = Field(default=15, ge=0)
    dry_run: bool = False


class ValueBetsResponse(BaseModel):
    status: str
    datetime_optim: datetime
    optim_label: str
    n_bets: int
    bets: List[dict[str, Any]]
