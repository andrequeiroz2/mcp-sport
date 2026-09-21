"""Pydantic schemas for the get_stints tool (OpenF1 /stints endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class StintsInput(BaseInput):
    """Input filters for the get_stints tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )
    stint_number: int | None = Field(
        default=None, ge=1, description="Sequential stint number within the session"
    )
    compound: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        description="Tyre compound, e.g., 'SOFT', 'MEDIUM', 'HARD'",
    )
    lap_start_min: int | None = Field(
        default=None, ge=1, description="Minimum stint start lap (inclusive)"
    )
    lap_start_max: int | None = Field(
        default=None, ge=1, description="Maximum stint start lap (inclusive)"
    )
    lap_end_min: int | None = Field(
        default=None, ge=1, description="Minimum stint end lap (inclusive)"
    )
    lap_end_max: int | None = Field(
        default=None, ge=1, description="Maximum stint end lap (inclusive)"
    )
    tyre_age_at_start_min: int | None = Field(
        default=None, ge=0, description="Minimum tyre age in laps (inclusive)"
    )
    tyre_age_at_start_max: int | None = Field(
        default=None, ge=0, description="Maximum tyre age in laps (inclusive)"
    )


class Stint(BaseModel):
    """Stint record as returned by the OpenF1 /stints endpoint."""

    session_key: int
    meeting_key: int
    driver_number: int
    stint_number: int | None = Field(default=None, description="Starts at 1")
    compound: str | None = Field(
        default=None, description="Tyre compound (SOFT, MEDIUM, HARD, ...)"
    )
    lap_start: int | None = Field(default=None, description="First lap of the stint")
    lap_end: int | None = Field(default=None, description="Last completed lap")
    tyre_age_at_start: int | None = Field(
        default=None, description="Tyre age at stint start, in laps completed"
    )
