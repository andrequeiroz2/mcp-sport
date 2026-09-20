"""Pydantic schemas for the get_sessions tool (OpenF1 /sessions endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class SessionsInput(BaseInput):
    """Input filters for the get_sessions tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    meeting_key: int | str | None = Field(
        default=None,
        description="Meeting identifier, or 'latest' for the current/most recent meeting",
    )
    year: int | None = Field(
        default=None,
        ge=2023,
        description="Year of the event (OpenF1 data starts in 2023)",
    )
    country_name: str | None = Field(
        default=None, min_length=1, max_length=100, description="e.g., 'Belgium'"
    )
    session_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="e.g., 'Practice 1', 'Qualifying', 'Race', 'Sprint Qualifying'",
    )
    session_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="e.g., 'Practice', 'Qualifying', 'Race'",
    )
    circuit_key: int | None = Field(
        default=None, ge=1, description="Unique identifier for the circuit"
    )
    location: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="City or geographical location, e.g., 'Spa-Francorchamps'",
    )


class Session(BaseModel):
    """Session record as returned by the OpenF1 /sessions endpoint."""

    session_key: int
    meeting_key: int
    session_name: str | None = Field(
        default=None, description="e.g., 'Practice 1', 'Qualifying', 'Race'"
    )
    session_type: str | None = Field(
        default=None, description="e.g., 'Practice', 'Qualifying', 'Race'"
    )
    date_start: str | None = Field(default=None, description="UTC start, ISO 8601")
    date_end: str | None = Field(default=None, description="UTC end, ISO 8601")
    gmt_offset: str | None = None
    location: str | None = None
    country_key: int | None = None
    country_code: str | None = None
    country_name: str | None = None
    circuit_key: int | None = None
    circuit_short_name: str | None = None
    year: int | None = None
    is_cancelled: bool | None = None
