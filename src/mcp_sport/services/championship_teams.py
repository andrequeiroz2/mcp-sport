"""Service layer for teams championship: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.championship_teams import (
    TeamsChampionshipEntry,
    TeamsChampionshipInput,
)
from mcp_sport.validators.championship_teams import (
    validate_teams_championship_input,
)


def get_teams_championship(
    filters: TeamsChampionshipInput,
) -> list[TeamsChampionshipEntry]:
    """Fetch teams championship standings from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of TeamsChampionshipEntry models converted from the raw API response.
    """
    validated = validate_teams_championship_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("championship_teams", params)
    return [TeamsChampionshipEntry(**item) for item in raw]
