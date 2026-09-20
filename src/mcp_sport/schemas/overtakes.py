"""Pydantic schemas for the get_overtakes tool (OpenF1 /overtakes endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class OvertakesInput(BaseInput):
    """Input filters for the get_overtakes tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    overtaking_driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Number of the overtaking driver"
    )
    overtaken_driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Number of the overtaken driver"
    )
    position: int | None = Field(
        default=None,
        ge=1,
        description="Position of the overtaking driver after the overtake",
    )


class Overtake(BaseModel):
    """Overtake record as returned by the OpenF1 /overtakes endpoint."""

    session_key: int
    meeting_key: int
    date: str | None = Field(default=None, description="UTC date and time, ISO 8601")
    overtaking_driver_number: int | None = None
    overtaken_driver_number: int | None = None
    position: int | None = Field(
        default=None,
        description="Position of the overtaking driver after the overtake (starts at 1)",
    )
