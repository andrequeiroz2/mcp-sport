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
