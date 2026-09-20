"""Business/operation validations for the get_stints tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.stints import StintsInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_stints_input(data: StintsInput) -> StintsInput:
    """Validate and normalize stint filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided or session_key is missing.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None:
        raise ToolValidationError(
            "session_key is required: stint data is scoped per session"
        )

    if data.compound is not None:
        data.compound = data.compound.upper()

    return data
