"""Service layer for stint data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.stints import Stint, StintsInput
from mcp_sport.services.common import build_params
from mcp_sport.validators.stints import validate_stints_input

_OPERATOR_FIELDS = {
    "lap_start_min": "lap_start>=",
    "lap_start_max": "lap_start<=",
    "lap_end_min": "lap_end>=",
    "lap_end_max": "lap_end<=",
    "tyre_age_at_start_min": "tyre_age_at_start>=",
    "tyre_age_at_start_max": "tyre_age_at_start<=",
}


def get_stints(filters: StintsInput) -> list[Stint]:
    """Fetch stints from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Stint models converted from the raw API response.
    """
    validated = validate_stints_input(filters)
    raw = openf1.get("stints", build_params(validated, _OPERATOR_FIELDS))
    return [Stint(**item) for item in raw]
