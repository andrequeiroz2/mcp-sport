"""Service layer for team radio data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.team_radio import TeamRadio, TeamRadioInput
from mcp_sport.validators.team_radio import validate_team_radio_input


def get_team_radio(filters: TeamRadioInput) -> list[TeamRadio]:
    """Fetch team radio recordings from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of TeamRadio models converted from the raw API response.
    """
    validated = validate_team_radio_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("team_radio", params)
    return [TeamRadio(**item) for item in raw]
