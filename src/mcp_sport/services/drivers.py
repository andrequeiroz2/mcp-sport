"""Service layer for driver data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.drivers import Driver, DriversInput
from mcp_sport.validators.drivers import validate_drivers_input


def get_drivers(filters: DriversInput) -> list[Driver]:
    """Fetch drivers from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Driver models converted from the raw API response.
    """
    validated = validate_drivers_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("drivers", params)
    return [Driver(**item) for item in raw]
