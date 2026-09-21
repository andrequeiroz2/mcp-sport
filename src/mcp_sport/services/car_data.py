"""Service layer for car telemetry: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.car_data import CarData, CarDataInput
from mcp_sport.services.common import build_params
from mcp_sport.validators.car_data import validate_car_data_input

_OPERATOR_FIELDS = {
    "speed_min": "speed>=",
    "speed_max": "speed<=",
    "rpm_min": "rpm>=",
    "rpm_max": "rpm<=",
    "throttle_min": "throttle>=",
    "throttle_max": "throttle<=",
    "n_gear_min": "n_gear>=",
    "n_gear_max": "n_gear<=",
    "drs_min": "drs>=",
    "drs_max": "drs<=",
    "date_from": "date>=",
    "date_to": "date<=",
}


def get_car_data(filters: CarDataInput) -> list[CarData]:
    """Fetch car telemetry from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of CarData models converted from the raw API response.
    """
    validated = validate_car_data_input(filters)
    raw = openf1.get("car_data", build_params(validated, _OPERATOR_FIELDS))
    return [CarData(**item) for item in raw]
