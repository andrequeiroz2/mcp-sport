"""Business/operation validations for the get_starting_grid tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.starting_grid import StartingGridInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_starting_grid_input(data: StartingGridInput) -> StartingGridInput:
    """Validate and normalize starting grid filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided, session_key is missing
            (grids are only published per session), or the key is invalid.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None:
        raise ToolValidationError(
            "session_key is required: starting grids are only published per session"
        )

    return data
