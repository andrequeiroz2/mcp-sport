"""Service layer for race control data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.race_control import RaceControlInput, RaceControlMessage
from mcp_sport.services.common import build_params
from mcp_sport.validators.race_control import validate_race_control_input

_OPERATOR_FIELDS = {
    "lap_number_min": "lap_number>=",
    "lap_number_max": "lap_number<=",
    "date_from": "date>=",
    "date_to": "date<=",
}


def get_race_control(filters: RaceControlInput) -> list[RaceControlMessage]:
    """Fetch race control messages from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of RaceControlMessage models converted from the raw API response.
    """
    validated = validate_race_control_input(filters)
    raw = openf1.get("race_control", build_params(validated, _OPERATOR_FIELDS))
    return [RaceControlMessage(**item) for item in raw]
