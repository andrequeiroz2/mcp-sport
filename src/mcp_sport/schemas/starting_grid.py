"""Pydantic schemas for the get_starting_grid tool (OpenF1 /starting_grid endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class StartingGridInput(BaseInput):
    """Input filters for the get_starting_grid tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )
    position: int | None = Field(
        default=None, ge=1, description="Position on the grid (starts at 1)"
    )


class StartingGridEntry(BaseModel):
    """Starting grid record as returned by the OpenF1 /starting_grid endpoint."""

    session_key: int
    meeting_key: int
    driver_number: int
    position: int | None = Field(default=None, description="Position on the grid")
    lap_duration: float | None = Field(
        default=None, description="Duration of the qualifying lap, in seconds"
    )
