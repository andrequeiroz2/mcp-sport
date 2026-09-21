"""Service layer for weather data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.weather import Weather, WeatherInput
from mcp_sport.services.common import build_params
from mcp_sport.validators.weather import validate_weather_input

_OPERATOR_FIELDS = {
    "air_temperature_min": "air_temperature>=",
    "air_temperature_max": "air_temperature<=",
    "track_temperature_min": "track_temperature>=",
    "track_temperature_max": "track_temperature<=",
    "humidity_min": "humidity>=",
    "humidity_max": "humidity<=",
    "rainfall_min": "rainfall>=",
    "rainfall_max": "rainfall<=",
    "wind_speed_min": "wind_speed>=",
    "wind_speed_max": "wind_speed<=",
    "date_from": "date>=",
    "date_to": "date<=",
}


def get_weather(filters: WeatherInput) -> list[Weather]:
    """Fetch weather samples from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Weather models converted from the raw API response.
    """
    validated = validate_weather_input(filters)
    raw = openf1.get("weather", build_params(validated, _OPERATOR_FIELDS))
    return [Weather(**item) for item in raw]
