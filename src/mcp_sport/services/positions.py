"""Service layer for position data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.positions import Position, PositionsInput
from mcp_sport.validators.positions import validate_positions_input


def get_positions(filters: PositionsInput) -> list[Position]:
    """Fetch position history from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Position models converted from the raw API response.
    """
    validated = validate_positions_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("position", params)
    return [Position(**item) for item in raw]
