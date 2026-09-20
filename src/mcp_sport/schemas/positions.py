"""Pydantic schemas for the get_positions tool (OpenF1 /position endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class PositionsInput(BaseInput):
    """Input filters for the get_positions tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    meeting_key: int | str | None = Field(
        default=None,
        description="Meeting identifier, or 'latest' for the current/most recent meeting",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )
    position: int | None = Field(
        default=None, ge=1, description="Position of the driver (starts at 1)"
    )


class Position(BaseModel):
    """Position record as returned by the OpenF1 /position endpoint."""

    session_key: int
    meeting_key: int
    driver_number: int
    position: int | None = Field(default=None, description="Position (starts at 1)")
    date: str | None = Field(default=None, description="UTC date and time, ISO 8601")
