"""Service layer for stint data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.stints import Stint, StintsInput
from mcp_sport.validators.stints import validate_stints_input


def get_stints(filters: StintsInput) -> list[Stint]:
    """Fetch stints from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Stint models converted from the raw API response.
    """
    validated = validate_stints_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("stints", params)
    return [Stint(**item) for item in raw]
