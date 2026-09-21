"""Service layer for lap data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.laps import Lap, LapsInput
from mcp_sport.services.common import build_params
from mcp_sport.validators.laps import validate_laps_input

_OPERATOR_FIELDS = {
    "lap_number_min": "lap_number>=",
    "lap_number_max": "lap_number<=",
    "lap_duration_min": "lap_duration>=",
    "lap_duration_max": "lap_duration<=",
    "duration_sector_1_min": "duration_sector_1>=",
    "duration_sector_1_max": "duration_sector_1<=",
    "duration_sector_2_min": "duration_sector_2>=",
    "duration_sector_2_max": "duration_sector_2<=",
    "duration_sector_3_min": "duration_sector_3>=",
    "duration_sector_3_max": "duration_sector_3<=",
    "i1_speed_min": "i1_speed>=",
    "i1_speed_max": "i1_speed<=",
    "i2_speed_min": "i2_speed>=",
    "i2_speed_max": "i2_speed<=",
    "st_speed_min": "st_speed>=",
    "st_speed_max": "st_speed<=",
    "date_from": "date_start>=",
    "date_to": "date_start<=",
}


def get_laps(filters: LapsInput) -> list[Lap]:
    """Fetch laps from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Lap models converted from the raw API response.
    """
    validated = validate_laps_input(filters)
    raw = openf1.get("laps", build_params(validated, _OPERATOR_FIELDS))
    return [Lap(**item) for item in raw]
