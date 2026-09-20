"""Business/operation validations for the get_drivers tool.

Pydantic validates shape; these validators enforce semantics
(see tasks/01_mcpapi.md, section 5.1).
"""

import re

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.drivers import DriversInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter

_ACRONYM_PATTERN = re.compile(r"^[A-Z]{3}$")


def validate_drivers_input(data: DriversInput) -> DriversInput:
    """Validate and normalize driver filters before calling the API.

    Raises:
        ToolValidationError: If no filter is provided, a key is invalid,
            or name_acronym is not three uppercase letters.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")
    data.meeting_key = normalize_key(data.meeting_key, "meeting_key")

    if data.name_acronym is not None:
        data.name_acronym = data.name_acronym.upper()
        if not _ACRONYM_PATTERN.match(data.name_acronym):
            raise ToolValidationError(
                "name_acronym must be exactly three letters (e.g., VER)"
            )

    if data.country_code is not None:
        data.country_code = data.country_code.upper()

    return data
