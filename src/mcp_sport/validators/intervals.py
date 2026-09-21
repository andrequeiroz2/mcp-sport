"""Business/operation validations for the get_intervals tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.intervals import IntervalsInput
from mcp_sport.validators.common import (
    normalize_key,
    require_at_least_one_filter,
    validate_date_range,
)


def validate_intervals_input(data: IntervalsInput) -> IntervalsInput:
    """Validate and normalize interval filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided or session_key is missing
            (interval data is real-time and high-volume), or the date range
            is invalid.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None:
        raise ToolValidationError(
            "session_key is required: interval data is scoped per session"
        )

    validate_date_range(data)

    return data
