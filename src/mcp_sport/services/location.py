"""Service layer for car location: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.location import Location, LocationInput
from mcp_sport.validators.location import validate_location_input


def get_location(filters: LocationInput) -> list[Location]:
    """Fetch car location samples from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Location models converted from the raw API response.
    """
    validated = validate_location_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("location", params)
    return [Location(**item) for item in raw]
