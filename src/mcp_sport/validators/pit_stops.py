"""Business/operation validations for the get_pit_stops tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.pit_stops import PitStopsInput
from mcp_sport.validators.common import (
    normalize_key,
    require_at_least_one_filter,
    validate_date_range,
    validate_range,
)

_RANGE_FIELDS = ("lap_number", "lane_duration")


def validate_pit_stops_input(data: PitStopsInput) -> PitStopsInput:
    """Validate and normalize pit stop filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided or session_key is missing,
            or a range filter is contradictory.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None:
        raise ToolValidationError(
            "session_key is required: pit stop data is scoped per session"
        )

    for field in _RANGE_FIELDS:
        validate_range(data, field)
    validate_date_range(data)

    return data
