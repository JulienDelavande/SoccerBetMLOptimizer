
from pydantic import BaseModel, Field
from typing import Any, List, Literal
from datetime import datetime

class InferenceRequest(BaseModel):
    datetime_stop: datetime | None = Field(
        default=None,
        description="Datetime at ISO 8601 format (YYYY-MM-DDTHH:MM:SS) of the match to stop training and start the inference, by default None",
    )

class InferenceResponse(BaseModel):
    status: Literal["success"]
    datetime_inference: datetime
    train_test_metrics: List[dict[str, Any]]
    nb_matches_inferred: int
    first_match_name: str | None = None
    last_match_name: str | None = None