"""Pydantic schemas for the get_laps tool (OpenF1 /laps endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class LapsInput(BaseInput):
    """Input filters for the get_laps tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )
    lap_number: int | None = Field(
        default=None, ge=1, description="Sequential lap number within the session"
    )


class Lap(BaseModel):
    """Lap record as returned by the OpenF1 /laps endpoint."""

    session_key: int
    meeting_key: int
    driver_number: int
    lap_number: int | None = Field(default=None, description="Starts at 1")
    lap_duration: float | None = Field(
        default=None, description="Total lap time, in seconds"
    )
    duration_sector_1: float | None = Field(default=None, description="Seconds")
    duration_sector_2: float | None = Field(default=None, description="Seconds")
    duration_sector_3: float | None = Field(default=None, description="Seconds")
    i1_speed: int | None = Field(
        default=None, description="Speed in km/h at the first intermediate point"
    )
    i2_speed: int | None = Field(
        default=None, description="Speed in km/h at the second intermediate point"
    )
    st_speed: int | None = Field(
        default=None, description="Speed in km/h at the speed trap"
    )
    is_pit_out_lap: bool | None = Field(
        default=None, description="True if the lap is an out lap from the pit"
    )
    segments_sector_1: list[int] | None = Field(
        default=None,
        description="Mini-sector values (0=n/a, 2048=yellow, 2049=green, 2051=purple, 2064=pitlane). Not available during races.",
    )
    segments_sector_2: list[int] | None = Field(
        default=None,
        description="Mini-sector values (0=n/a, 2048=yellow, 2049=green, 2051=purple, 2064=pitlane). Not available during races.",
    )
    segments_sector_3: list[int] | None = Field(
        default=None,
        description="Mini-sector values (0=n/a, 2048=yellow, 2049=green, 2051=purple, 2064=pitlane). Not available during races.",
    )
    date_start: str | None = Field(
        default=None, description="Approximate UTC lap start, ISO 8601"
    )
