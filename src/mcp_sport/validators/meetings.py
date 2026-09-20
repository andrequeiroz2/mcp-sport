"""Business/operation validations for the get_meetings tool."""

from mcp_sport.schemas.meetings import MeetingsInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_meetings_input(data: MeetingsInput) -> MeetingsInput:
    """Validate and normalize meeting filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided or meeting_key is invalid.
    """
    require_at_least_one_filter(data)

    data.meeting_key = normalize_key(data.meeting_key, "meeting_key")

    return data
