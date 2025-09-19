from pydantic import BaseModel, Field

class FbrefRequest(BaseModel):
    get_current_season_only: bool = Field(default=True, description="Only fetch current season")
    use_cache: bool = Field(default=False, description="Use cached data if available")
    cutoff_days: int = Field(default=7, description="Only fetch matches from the last N days")
    run_in_background: bool = Field(default=False, description="Run the task in background")

class FbrefResponse(BaseModel):
    status: str
    inserted_rows: int | None = None
    first_row: str | None = None
    last_row: str | None = None
    message: str | None = None

class SofifaRequest(BaseModel):
    use_cache: bool = False
    scrap_all: bool = False
    run_in_background: bool = Field(default=False, description="Run the task in background")

class SofifaResponse(BaseModel):
    status: str
    message: str | None = None

class OddsRequest(BaseModel):
    run_in_background: bool = Field(default=False, description="Run the task in background")

class OddsResponse(BaseModel):
    status: str
    message: str | None = None