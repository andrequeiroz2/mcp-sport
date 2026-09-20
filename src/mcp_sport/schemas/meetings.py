"""Pydantic schemas for the get_meetings tool (OpenF1 /meetings endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class MeetingsInput(BaseInput):
    """Input filters for the get_meetings tool."""

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
        default=None, min_length=1, max_length=100, description="e.g., 'Singapore'"
    )
    meeting_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="e.g., 'Singapore Grand Prix'",
    )
    circuit_key: int | None = Field(
        default=None, ge=1, description="Unique identifier for the circuit"
    )
    location: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="City or geographical location, e.g., 'Marina Bay'",
    )


class Meeting(BaseModel):
    """Meeting record as returned by the OpenF1 /meetings endpoint."""

    meeting_key: int
    meeting_name: str | None = None
    meeting_official_name: str | None = None
    date_start: str | None = Field(default=None, description="UTC start, ISO 8601")
    date_end: str | None = Field(default=None, description="UTC end, ISO 8601")
    gmt_offset: str | None = None
    location: str | None = None
    country_key: int | None = None
    country_code: str | None = None
    country_name: str | None = None
    country_flag: str | None = Field(default=None, description="Flag image URL")
    circuit_key: int | None = None
    circuit_short_name: str | None = None
    circuit_type: str | None = Field(
        default=None,
        description="'Permanent', 'Temporary - Street' or 'Temporary - Road'",
    )
    circuit_image: str | None = Field(default=None, description="Circuit image URL")
    circuit_info_url: str | None = Field(
        default=None, description="URL to detailed circuit info JSON (MultiViewer)"
    )
    year: int | None = None
    is_cancelled: bool | None = None
