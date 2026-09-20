"""Pydantic schemas for the get_location tool (OpenF1 /location endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class LocationInput(BaseInput):
    """Input filters for the get_location tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )


class Location(BaseModel):
    """Car location sample (~3.7 Hz) as returned by the OpenF1 /location endpoint."""

    session_key: int
    meeting_key: int
    driver_number: int
    date: str | None = Field(default=None, description="UTC date and time, ISO 8601")
    x: int | None = Field(
        default=None, description="X in a 3D Cartesian system (arbitrary origin)"
    )
    y: int | None = Field(
        default=None, description="Y in a 3D Cartesian system (arbitrary origin)"
    )
    z: int | None = Field(
        default=None, description="Z in a 3D Cartesian system (arbitrary origin)"
    )
