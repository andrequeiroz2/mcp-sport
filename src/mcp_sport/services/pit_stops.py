"""Service layer for pit stop data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.pit_stops import PitStop, PitStopsInput
from mcp_sport.services.common import build_params
from mcp_sport.validators.pit_stops import validate_pit_stops_input

_OPERATOR_FIELDS = {
    "lap_number_min": "lap_number>=",
    "lap_number_max": "lap_number<=",
    "lane_duration_min": "lane_duration>=",
    "lane_duration_max": "lane_duration<=",
    "date_from": "date>=",
    "date_to": "date<=",
}


def get_pit_stops(filters: PitStopsInput) -> list[PitStop]:
    """Fetch pit stops from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of PitStop models converted from the raw API response.
    """
    validated = validate_pit_stops_input(filters)
    raw = openf1.get("pit", build_params(validated, _OPERATOR_FIELDS))
    return [PitStop(**item) for item in raw]
