"""Pydantic schemas for the get_team_radio tool (OpenF1 /team_radio endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class TeamRadioInput(BaseInput):
    """Input filters for the get_team_radio tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )


class TeamRadio(BaseModel):
    """Team radio record as returned by the OpenF1 /team_radio endpoint."""

    session_key: int
    meeting_key: int
    driver_number: int
    date: str | None = Field(default=None, description="UTC date and time, ISO 8601")
    recording_url: str | None = Field(
        default=None, description="URL of the radio recording (MP3)"
    )
