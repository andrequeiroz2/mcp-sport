"""Pydantic schemas for the get_drivers tool (OpenF1 /drivers endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class DriversInput(BaseInput):
    """Input filters for the get_drivers tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    meeting_key: int | str | None = Field(
        default=None,
        description="Meeting identifier, or 'latest' for the current/most recent meeting",
    )
    driver_number: int | None = Field(
        default=None,
        ge=1,
        le=99,
        description="Driver number for the season (1-99)",
    )
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    name_acronym: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Three-letter driver acronym (e.g., VER)",
    )
    team_name: str | None = Field(default=None, min_length=1, max_length=100)
    country_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Three-letter country code (deprecated by OpenF1, removed after 2026)",
    )


class Driver(BaseModel):
    """Driver record as returned by the OpenF1 /drivers endpoint."""

    meeting_key: int
    session_key: int
    driver_number: int
    broadcast_name: str | None = None
    full_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    name_acronym: str | None = None
    team_name: str | None = None
    team_colour: str | None = Field(
        default=None, description="Team color as hex RRGGBB, without '#'"
    )
    headshot_url: str | None = None
    country_code: str | None = Field(
        default=None,
        description="Deprecated by OpenF1: removed at the end of the 2026 season",
    )
