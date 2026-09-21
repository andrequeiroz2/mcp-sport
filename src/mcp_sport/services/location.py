"""Service layer for car location: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.location import Location, LocationInput
from mcp_sport.services.common import build_params
from mcp_sport.validators.location import validate_location_input

_OPERATOR_FIELDS = {
    "x_min": "x>=",
    "x_max": "x<=",
    "y_min": "y>=",
    "y_max": "y<=",
    "z_min": "z>=",
    "z_max": "z<=",
    "date_from": "date>=",
    "date_to": "date<=",
}


def get_location(filters: LocationInput) -> list[Location]:
    """Fetch car location samples from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Location models converted from the raw API response.
    """
    validated = validate_location_input(filters)
    raw = openf1.get("location", build_params(validated, _OPERATOR_FIELDS))
    return [Location(**item) for item in raw]
