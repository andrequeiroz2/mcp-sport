"""Business/operation validations for the get_sessions tool."""

from mcp_sport.schemas.sessions import SessionsInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_sessions_input(data: SessionsInput) -> SessionsInput:
    """Validate and normalize session filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided or a key is invalid.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    data.meeting_key = normalize_key(data.meeting_key, "meeting_key")

    return data
