"""Service layer for session data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.sessions import Session, SessionsInput
from mcp_sport.validators.sessions import validate_sessions_input


def get_sessions(filters: SessionsInput) -> list[Session]:
    """Fetch sessions from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Session models converted from the raw API response.
    """
    validated = validate_sessions_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("sessions", params)
    return [Session(**item) for item in raw]
