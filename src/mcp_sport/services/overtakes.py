"""Service layer for overtake data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.overtakes import Overtake, OvertakesInput
from mcp_sport.validators.overtakes import validate_overtakes_input


def get_overtakes(filters: OvertakesInput) -> list[Overtake]:
    """Fetch overtakes from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Overtake models converted from the raw API response.
    """
    validated = validate_overtakes_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("overtakes", params)
    return [Overtake(**item) for item in raw]
