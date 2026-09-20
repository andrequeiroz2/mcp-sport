"""Service layer for lap data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.laps import Lap, LapsInput
from mcp_sport.validators.laps import validate_laps_input


def get_laps(filters: LapsInput) -> list[Lap]:
    """Fetch laps from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Lap models converted from the raw API response.
    """
    validated = validate_laps_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("laps", params)
    return [Lap(**item) for item in raw]
