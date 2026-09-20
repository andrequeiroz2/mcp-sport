"""Service layer for weather data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.weather import Weather, WeatherInput
from mcp_sport.validators.weather import validate_weather_input


def get_weather(filters: WeatherInput) -> list[Weather]:
    """Fetch weather samples from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Weather models converted from the raw API response.
    """
    validated = validate_weather_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("weather", params)
    return [Weather(**item) for item in raw]
