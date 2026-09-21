"""Pydantic schemas for the get_pit_stops tool (OpenF1 /pit endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class PitStopsInput(BaseInput):
    """Input filters for the get_pit_stops tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )
    lap_number: int | None = Field(
        default=None, ge=1, description="Lap on which the pit stop occurred"
    )
    lap_number_min: int | None = Field(
        default=None, ge=1, description="First lap of the range (inclusive)"
    )
    lap_number_max: int | None = Field(
        default=None, ge=1, description="Last lap of the range (inclusive)"
    )
    lane_duration_min: float | None = Field(
        default=None, gt=0, description="Minimum pit lane time in seconds (inclusive)"
    )
    lane_duration_max: float | None = Field(
        default=None, gt=0, description="Maximum pit lane time in seconds (inclusive)"
    )
    date_from: str | None = Field(
        default=None, description="Interval start, ISO 8601 UTC (inclusive)"
    )
    date_to: str | None = Field(
        default=None, description="Interval end, ISO 8601 UTC (inclusive)"
    )


class PitStop(BaseModel):
    """Pit stop record as returned by the OpenF1 /pit endpoint."""

    session_key: int
    meeting_key: int
    driver_number: int
    lap_number: int | None = Field(default=None, description="Starts at 1")
    date: str | None = Field(default=None, description="UTC date and time, ISO 8601")
    lane_duration: float | None = Field(
        default=None, description="Time spent in the pit lane, in seconds"
    )
    stop_duration: float | None = Field(
        default=None,
        description="Stationary pit stop time, in seconds. Only available from the 2024 US GP onwards.",
    )
    pit_duration: float | None = Field(
        default=None,
        description="Deprecated by OpenF1: same as lane_duration, removed after the 2026 season.",
    )
