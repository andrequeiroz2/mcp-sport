"""Business/operation validations for the get_teams_championship tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.championship_teams import TeamsChampionshipInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_teams_championship_input(
    data: TeamsChampionshipInput,
) -> TeamsChampionshipInput:
    """Validate and normalize championship filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided or session_key is missing
            (standings are only computed for race sessions).
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    if data.session_key is None:
        raise ToolValidationError(
            "session_key is required: championship standings are computed per race session"
        )

    return data
