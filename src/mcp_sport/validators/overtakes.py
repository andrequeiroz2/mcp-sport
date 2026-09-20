"""Business/operation validations for the get_overtakes tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.overtakes import OvertakesInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_overtakes_input(data: OvertakesInput) -> OvertakesInput:
    """Validate and normalize overtake filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided or session_key is missing
            (overtakes are only recorded during races, per session).
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None:
        raise ToolValidationError(
            "session_key is required: overtakes are scoped per race session"
        )

    return data
