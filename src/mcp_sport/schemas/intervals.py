"""Pydantic schemas for the get_intervals tool (OpenF1 /intervals endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class IntervalsInput(BaseInput):
    """Input filters for the get_intervals tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )
    date_from: str | None = Field(
        default=None, description="Interval start, ISO 8601 UTC (inclusive)"
    )
    date_to: str | None = Field(
        default=None, description="Interval end, ISO 8601 UTC (inclusive)"
    )


class Interval(BaseModel):
    """Interval record as returned by the OpenF1 /intervals endpoint."""

    session_key: int
    meeting_key: int
    driver_number: int
    date: str | None = Field(default=None, description="UTC date and time, ISO 8601")
    gap_to_leader: float | str | None = Field(
        default=None,
        description="Gap to the race leader in seconds, '+1 LAP' if lapped, or null for the leader",
    )
    interval: float | str | None = Field(
        default=None,
        description="Gap to the car ahead in seconds, '+1 LAP' if lapped, or null for the leader",
    )
