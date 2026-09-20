"""Service layer for car telemetry: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.car_data import CarData, CarDataInput
from mcp_sport.validators.car_data import validate_car_data_input


def get_car_data(filters: CarDataInput) -> list[CarData]:
    """Fetch car telemetry from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of CarData models converted from the raw API response.
    """
    validated = validate_car_data_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("car_data", params)
    return [CarData(**item) for item in raw]
