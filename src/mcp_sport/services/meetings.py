"""Service layer for meeting data: orchestrates validators, client and conversion."""

from mcp_sport.clients import openf1
from mcp_sport.schemas.meetings import Meeting, MeetingsInput
from mcp_sport.validators.meetings import validate_meetings_input


def get_meetings(filters: MeetingsInput) -> list[Meeting]:
    """Fetch meetings from OpenF1 applying validated filters.

    Args:
        filters: Validated input filters (shape validated by Pydantic).

    Returns:
        List of Meeting models converted from the raw API response.
    """
    validated = validate_meetings_input(filters)
    params = {
        key: value
        for key, value in validated.model_dump().items()
        if key in validated.model_fields_set
    }
    raw = openf1.get("meetings", params)
    return [Meeting(**item) for item in raw]
