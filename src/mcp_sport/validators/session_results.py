"""Business/operation validations for the get_session_results tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.session_results import SessionResultsInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_session_results_input(data: SessionResultsInput) -> SessionResultsInput:
    """Validate and normalize session result filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided, session_key is missing
            (results are only meaningful per session), or a key is invalid.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None:
        raise ToolValidationError(
            "session_key is required: session results are only published per session"
        )

    return data
