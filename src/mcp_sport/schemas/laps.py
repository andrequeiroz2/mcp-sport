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
    lap_number_min: int | None = Field(
        default=None, ge=1, description="First lap of the range (inclusive)"
    )
    lap_number_max: int | None = Field(
        default=None, ge=1, description="Last lap of the range (inclusive)"
    )
    lap_duration_min: float | None = Field(
        default=None, gt=0, description="Minimum lap time in seconds (inclusive)"
    )
    lap_duration_max: float | None = Field(
        default=None, gt=0, description="Maximum lap time in seconds (inclusive)"
    )
    duration_sector_1_min: float | None = Field(
        default=None, gt=0, description="Minimum sector 1 time in seconds (inclusive)"
    )
    duration_sector_1_max: float | None = Field(
        default=None, gt=0, description="Maximum sector 1 time in seconds (inclusive)"
    )
    duration_sector_2_min: float | None = Field(
        default=None, gt=0, description="Minimum sector 2 time in seconds (inclusive)"
    )
    duration_sector_2_max: float | None = Field(
        default=None, gt=0, description="Maximum sector 2 time in seconds (inclusive)"
    )
    duration_sector_3_min: float | None = Field(
        default=None, gt=0, description="Minimum sector 3 time in seconds (inclusive)"
    )
    duration_sector_3_max: float | None = Field(
        default=None, gt=0, description="Maximum sector 3 time in seconds (inclusive)"
    )
    i1_speed_min: int | None = Field(
        default=None, ge=0, description="Minimum speed at intermediate 1, km/h (inclusive)"
    )
    i1_speed_max: int | None = Field(
        default=None, ge=0, description="Maximum speed at intermediate 1, km/h (inclusive)"
    )
    i2_speed_min: int | None = Field(
        default=None, ge=0, description="Minimum speed at intermediate 2, km/h (inclusive)"
    )
    i2_speed_max: int | None = Field(
        default=None, ge=0, description="Maximum speed at intermediate 2, km/h (inclusive)"
    )
    st_speed_min: int | None = Field(
        default=None, ge=0, description="Minimum speed trap speed, km/h (inclusive)"
    )
    st_speed_max: int | None = Field(
        default=None, ge=0, description="Maximum speed trap speed, km/h (inclusive)"
    )
    date_from: str | None = Field(
        default=None,
        description="Lap start (date_start) lower bound, ISO 8601 UTC (inclusive)",
    )
    date_to: str | None = Field(
        default=None,
        description="Lap start (date_start) upper bound, ISO 8601 UTC (inclusive)",
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
    segments_sector_1: list[int | None] | None = Field(
        default=None,
        description="Mini-sector values (0=n/a, 2048=yellow, 2049=green, 2051=purple, 2064=pitlane; null = no data). Not available during races.",
    )
    segments_sector_2: list[int | None] | None = Field(
        default=None,
        description="Mini-sector values (0=n/a, 2048=yellow, 2049=green, 2051=purple, 2064=pitlane; null = no data). Not available during races.",
    )
    segments_sector_3: list[int | None] | None = Field(
        default=None,
        description="Mini-sector values (0=n/a, 2048=yellow, 2049=green, 2051=purple, 2064=pitlane; null = no data). Not available during races.",
    )
    date_start: str | None = Field(
        default=None, description="Approximate UTC lap start, ISO 8601"
    )
