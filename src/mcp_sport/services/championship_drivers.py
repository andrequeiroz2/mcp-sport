"""Service layer for drivers championship: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.championship_drivers import (
    DriversChampionshipEntry,
    DriversChampionshipInput,
)
from mcp_sport.validators.championship_drivers import (
    validate_drivers_championship_input,
)


def get_drivers_championship(
    filters: DriversChampionshipInput,
) -> list[DriversChampionshipEntry]:
    """Fetch drivers championship standings from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of DriversChampionshipEntry models converted from the raw API response.
    """
    validated = validate_drivers_championship_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("championship_drivers", params)
    return [DriversChampionshipEntry(**item) for item in raw]
