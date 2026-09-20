"""Business/operation validations for the get_team_radio tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.team_radio import TeamRadioInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_team_radio_input(data: TeamRadioInput) -> TeamRadioInput:
    """Validate and normalize team radio filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided or session_key is missing.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None:
        raise ToolValidationError(
            "session_key is required: team radio is scoped per session"
        )

    return data
