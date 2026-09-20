"""Business/operation validations for the get_race_control tool."""

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.race_control import RaceControlInput
from mcp_sport.validators.common import normalize_key, require_at_least_one_filter


def validate_race_control_input(data: RaceControlInput) -> RaceControlInput:
    """Validate and normalize race control filters before calling the API.

    Raises:
        ToolValidationError: If neither session_key nor driver_number is given
            (unscoped race control history is too broad), or a key is invalid.
    """
    require_at_least_one_filter(data)

    data.session_key = normalize_key(data.session_key, "session_key")

    if data.session_key is None and data.driver_number is None:
        raise ToolValidationError(
            "session_key or driver_number is required to scope race control messages"
        )

    if data.flag is not None:
        data.flag = data.flag.upper()

    return data
