"""Service layer for position data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.positions import Position, PositionsInput
from mcp_sport.services.common import build_params
from mcp_sport.validators.positions import validate_positions_input

_OPERATOR_FIELDS = {
    "position_min": "position>=",
    "position_max": "position<=",
    "date_from": "date>=",
    "date_to": "date<=",
}


def get_positions(filters: PositionsInput) -> list[Position]:
    """Fetch position history from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Position models converted from the raw API response.
    """
    validated = validate_positions_input(filters)
    raw = openf1.get("position", build_params(validated, _OPERATOR_FIELDS))
    return [Position(**item) for item in raw]
