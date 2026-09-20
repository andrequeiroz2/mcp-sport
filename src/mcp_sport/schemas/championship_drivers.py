"""Pydantic schemas for the get_drivers_championship tool (OpenF1 /championship_drivers, beta)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class DriversChampionshipInput(BaseInput):
    """Input filters for the get_drivers_championship tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Race session identifier, or 'latest' for the most recent one",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )


class DriversChampionshipEntry(BaseModel):
    """Championship standing as returned by /championship_drivers (beta)."""

    session_key: int
    meeting_key: int
    driver_number: int
    position_current: int | None = Field(
        default=None, description="Championship position during/after the race"
    )
    position_start: int | None = Field(
        default=None, description="Championship position before the race started"
    )
    points_current: float | None = Field(
        default=None, description="Championship points during/after the race"
    )
    points_start: float | None = Field(
        default=None, description="Championship points before the race started"
    )
