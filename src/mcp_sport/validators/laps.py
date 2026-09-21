"""Business/operation validations for the get_laps tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.laps import LapsInput
from mcp_sport.validators.common import (
    normalize_key,
    require_at_least_one_filter,
    validate_date_range,
    validate_range,
)

_RANGE_FIELDS = (
    "lap_number",
    "lap_duration",
    "duration_sector_1",
    "duration_sector_2",
    "duration_sector_3",
    "i1_speed",
    "i2_speed",
    "st_speed",
)


def validate_laps_input(data: LapsInput) -> LapsInput:
    """Validate and normalize lap filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided or session_key is missing
            (lap data is only meaningful per session and high-volume otherwise),
            or a range filter is contradictory.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None:
        raise ToolValidationError(
            "session_key is required: lap data is scoped per session"
        )

    for field in _RANGE_FIELDS:
        validate_range(data, field)
    validate_date_range(data)

    return data
