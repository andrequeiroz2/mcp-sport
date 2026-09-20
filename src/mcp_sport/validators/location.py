"""Business/operation validations for the get_location tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.location import LocationInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_location_input(data: LocationInput) -> LocationInput:
    """Validate and normalize location filters before calling the API.

    Raises:
        ToolValidationError: If session_key or driver_number is missing —
            location is sampled at ~3.7 Hz, so both are required to keep
            responses bounded.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None or data.driver_number is None:
        raise ToolValidationError(
            "session_key and driver_number are both required: car location is "
            "sampled at ~3.7 Hz and unscoped queries return huge responses"
        )

    return data
