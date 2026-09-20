"""Service layer for session results: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.session_results import SessionResult, SessionResultsInput
from mcp_sport.validators.session_results import validate_session_results_input


def get_session_results(filters: SessionResultsInput) -> list[SessionResult]:
    """Fetch session results from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of SessionResult models converted from the raw API response.
    """
    validated = validate_session_results_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("session_result", params)
    return [SessionResult(**item) for item in raw]
