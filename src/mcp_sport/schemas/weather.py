"""Pydantic schemas for the get_weather tool (OpenF1 /weather endpoint)."""

from pydantic import BaseModel, Field

from mcp_sport.schemas.base import BaseInput


class WeatherInput(BaseInput):
    """Input filters for the get_weather tool."""

    session_key: int | str | None = Field(
        default=None,
        description="Session identifier, or 'latest' for the current/most recent session",
    )
    meeting_key: int | str | None = Field(
        default=None,
        description="Meeting identifier, or 'latest' for the current/most recent meeting",
    )
    air_temperature_min: float | None = Field(
        default=None, description="Minimum air temperature in °C (inclusive)"
    )
    air_temperature_max: float | None = Field(
        default=None, description="Maximum air temperature in °C (inclusive)"
    )
    track_temperature_min: float | None = Field(
        default=None, description="Minimum track temperature in °C (inclusive)"
    )
    track_temperature_max: float | None = Field(
        default=None, description="Maximum track temperature in °C (inclusive)"
    )
    humidity_min: int | None = Field(
        default=None, ge=0, le=100, description="Minimum humidity % (inclusive)"
    )
    humidity_max: int | None = Field(
        default=None, ge=0, le=100, description="Maximum humidity % (inclusive)"
    )
    rainfall_min: int | None = Field(
        default=None, ge=0, le=1,
        description="Minimum rainfall flag (inclusive); use 1 to get only rainy samples",
    )
    rainfall_max: int | None = Field(
        default=None, ge=0, le=1, description="Maximum rainfall flag (inclusive)"
    )
    wind_speed_min: float | None = Field(
        default=None, ge=0, description="Minimum wind speed in m/s (inclusive)"
    )
    wind_speed_max: float | None = Field(
        default=None, ge=0, description="Maximum wind speed in m/s (inclusive)"
    )
    date_from: str | None = Field(
        default=None, description="Interval start, ISO 8601 UTC (inclusive)"
    )
    date_to: str | None = Field(
        default=None, description="Interval end, ISO 8601 UTC (inclusive)"
    )


class Weather(BaseModel):
    """Weather record as returned by the OpenF1 /weather endpoint."""

    session_key: int
    meeting_key: int
    date: str | None = Field(default=None, description="UTC date and time, ISO 8601")
    air_temperature: float | None = Field(default=None, description="Celsius")
    track_temperature: float | None = Field(default=None, description="Celsius")
    humidity: float | None = Field(default=None, description="Relative humidity (%)")
    pressure: float | None = Field(default=None, description="Air pressure (mbar)")
    rainfall: int | None = Field(default=None, description="0 = no rain, 1 = rain")
    wind_direction: int | None = Field(
        default=None, description="Wind direction in degrees (0-359)"
    )
    wind_speed: float | None = Field(default=None, description="Wind speed (m/s)")
