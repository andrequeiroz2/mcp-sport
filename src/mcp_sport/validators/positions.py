"""Business/operation validations for the get_positions tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.positions import PositionsInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_positions_input(data: PositionsInput) -> PositionsInput:
    """Validate and normalize position filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided, neither session_key nor
            meeting_key is given (position history is too broad without one),
            or a key is invalid.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    data.meeting_key = normalize_key(data.meeting_key, "meeting_key")

    if data.session_key is None and data.meeting_key is None:
        raise ToolValidationError(
            "session_key or meeting_key is required to scope position history"
        )

    return data
