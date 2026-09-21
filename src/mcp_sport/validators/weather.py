"""Business/operation validations for the get_weather tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.weather import WeatherInput
from mcp_sport.validators.common import (
    normalize_key,
    require_at_least_one_filter,
    validate_date_range,
    validate_range,
)

_RANGE_FIELDS = (
    "air_temperature",
    "track_temperature",
    "humidity",
    "rainfall",
    "wind_speed",
)


def validate_weather_input(data: WeatherInput) -> WeatherInput:
    """Validate and normalize weather filters before calling the API.

    Raises:
        ToolValidationError: If neither session_key nor meeting_key is given
            (weather is sampled every minute — unscoped queries are too broad),
            a key is invalid, or a range filter is contradictory.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    data.meeting_key = normalize_key(data.meeting_key, "meeting_key")

    for field in _RANGE_FIELDS:
        validate_range(data, field)
    validate_date_range(data)

    return data
