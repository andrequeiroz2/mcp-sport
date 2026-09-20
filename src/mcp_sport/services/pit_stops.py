"""Service layer for pit stop data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.pit_stops import PitStop, PitStopsInput
from mcp_sport.validators.pit_stops import validate_pit_stops_input


def get_pit_stops(filters: PitStopsInput) -> list[PitStop]:
    """Fetch pit stops from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of PitStop models converted from the raw API response.
    """
    validated = validate_pit_stops_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("pit", params)
    return [PitStop(**item) for item in raw]
