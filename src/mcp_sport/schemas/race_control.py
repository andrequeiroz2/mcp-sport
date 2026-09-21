"""Pydantic schemas for the get_race_control tool (OpenF1 /race_control endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class RaceControlInput(BaseInput):
    """Input filters for the get_race_control tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )
    flag: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="e.g., 'GREEN', 'YELLOW', 'DOUBLE YELLOW', 'CHEQUERED', 'BLACK AND WHITE'",
    )
    category: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="e.g., 'SessionStatus', 'CarEvent', 'Drs', 'Flag', 'SafetyCar'",
    )
    scope: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
        description="e.g., 'Track', 'Driver', 'Sector'",
    )
    lap_number_min: int | None = Field(
        default=None, ge=1, description="First lap of the range (inclusive)"
    )
    lap_number_max: int | None = Field(
        default=None, ge=1, description="Last lap of the range (inclusive)"
    )
    date_from: str | None = Field(
        default=None, description="Interval start, ISO 8601 UTC (inclusive)"
    )
    date_to: str | None = Field(
        default=None, description="Interval end, ISO 8601 UTC (inclusive)"
    )


class RaceControlMessage(BaseModel):
    """Race control record as returned by the OpenF1 /race_control endpoint."""

    session_key: int
    meeting_key: int
    date: str | None = Field(default=None, description="UTC date and time, ISO 8601")
    category: str | None = Field(
        default=None, description="SessionStatus, CarEvent, Drs, Flag, SafetyCar, ..."
    )
    flag: str | None = Field(
        default=None, description="GREEN, YELLOW, DOUBLE YELLOW, CHEQUERED, ..."
    )
    message: str | None = Field(default=None, description="Description of the event")
    driver_number: int | None = Field(
        default=None, description="Null when the event is not driver-specific"
    )
    lap_number: int | None = Field(default=None, description="Lap in a race session")
    scope: str | None = Field(default=None, description="Track, Driver, Sector, ...")
    sector: int | None = Field(default=None, description="Mini-sector (starts at 1)")
    qualifying_phase: int | None = Field(
        default=None, description="1, 2 or 3 in qualifying sessions"
    )
