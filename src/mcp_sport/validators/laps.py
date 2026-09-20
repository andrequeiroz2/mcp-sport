"""Business/operation validations for the get_laps tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.laps import LapsInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_laps_input(data: LapsInput) -> LapsInput:
    """Validate and normalize lap filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided or session_key is missing
            (lap data is only meaningful per session and high-volume otherwise).
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None:
        raise ToolValidationError(
            "session_key is required: lap data is scoped per session"
        )

    return data
