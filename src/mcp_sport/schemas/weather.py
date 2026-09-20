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


class Weather(BaseModel):
    """Weather record as returned by the OpenF1 /weather endpoint."""

    session_key: int
    meeting_key: int
    date: str | None = Field(default=None, description="UTC date and time, ISO 8601")
    air_temperature: float | None = Field(default=None, description="Celsius")
    track_temperature: float | None = Field(default=None, description="Celsius")
    humidity: int | None = Field(default=None, description="Relative humidity (%)")
    pressure: float | None = Field(default=None, description="Air pressure (mbar)")
    rainfall: int | None = Field(default=None, description="0 = no rain, 1 = rain")
    wind_direction: int | None = Field(
        default=None, description="Wind direction in degrees (0-359)"
    )
    wind_speed: float | None = Field(default=None, description="Wind speed (m/s)")
