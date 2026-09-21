"""Pydantic schemas for the get_car_data tool (OpenF1 /car_data endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class CarDataInput(BaseInput):
    """Input filters for the get_car_data tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    driver_number: int | None = Field(
        default=None, ge=1, le=99, description="Driver number for the season (1-99)"
    )
    speed_min: int | None = Field(
        default=None, ge=0, description="Minimum speed in km/h (inclusive)"
    )
    speed_max: int | None = Field(
        default=None, ge=0, description="Maximum speed in km/h (inclusive)"
    )
    rpm_min: int | None = Field(
        default=None, ge=0, description="Minimum engine rpm (inclusive)"
    )
    rpm_max: int | None = Field(
        default=None, ge=0, description="Maximum engine rpm (inclusive)"
    )
    throttle_min: int | None = Field(
        default=None, ge=0, le=100, description="Minimum throttle % (inclusive)"
    )
    throttle_max: int | None = Field(
        default=None, ge=0, le=100, description="Maximum throttle % (inclusive)"
    )
    n_gear_min: int | None = Field(
        default=None, ge=0, le=8, description="Minimum gear (inclusive)"
    )
    n_gear_max: int | None = Field(
        default=None, ge=0, le=8, description="Maximum gear (inclusive)"
    )
    drs_min: int | None = Field(
        default=None, ge=0, le=14, description="Minimum DRS status (inclusive)"
    )
    drs_max: int | None = Field(
        default=None, ge=0, le=14, description="Maximum DRS status (inclusive)"
    )
    date_from: str | None = Field(
        default=None,
        description="Interval start, ISO 8601 UTC (inclusive), e.g. lap date_start",
    )
    date_to: str | None = Field(
        default=None, description="Interval end, ISO 8601 UTC (inclusive)"
    )


class CarData(BaseModel):
    """Car telemetry sample (~3.7 Hz) as returned by the OpenF1 /car_data endpoint."""

    session_key: int
    meeting_key: int
    driver_number: int
    date: str | None = Field(default=None, description="UTC date and time, ISO 8601")
    speed: int | None = Field(default=None, description="Velocity of the car in km/h")
    rpm: int | None = Field(default=None, description="Engine revolutions per minute")
    n_gear: int | None = Field(
        default=None, description="Current gear (1-8; 0 = neutral/no gear)"
    )
    throttle: int | None = Field(
        default=None, description="Percentage of maximum engine power (0-100)"
    )
    brake: int | None = Field(
        default=None, description="100 = brake pedal pressed, 0 = not pressed"
    )
    drs: int | None = Field(
        default=None,
        description="DRS status: 0/1 = off, 8 = eligible, 10/12/14 = on",
    )
