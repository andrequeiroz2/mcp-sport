"""Service layer for interval data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.intervals import Interval, IntervalsInput
from mcp_sport.validators.intervals import validate_intervals_input


def get_intervals(filters: IntervalsInput) -> list[Interval]:
    """Fetch intervals from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Interval models converted from the raw API response.
    """
    validated = validate_intervals_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("intervals", params)
    return [Interval(**item) for item in raw]
