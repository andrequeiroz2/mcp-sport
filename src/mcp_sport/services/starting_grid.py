"""Service layer for starting grid data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.starting_grid import StartingGridEntry, StartingGridInput
from mcp_sport.validators.starting_grid import validate_starting_grid_input


def get_starting_grid(filters: StartingGridInput) -> list[StartingGridEntry]:
    """Fetch the starting grid from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of StartingGridEntry models converted from the raw API response.
    """
    validated = validate_starting_grid_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("starting_grid", params)
    return [StartingGridEntry(**item) for item in raw]
