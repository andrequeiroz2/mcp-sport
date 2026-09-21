"""Shared validation helpers for tool input models."""

from datetime import datetime

from mcp_sport.exceptions import ToolValidationError
from mcp_sport.schemas.base import BaseInput

_LATEST = "latest"


def normalize_key(value: int | str | None, field_name: str) -> int | str | None:
    """Accept a positive int or the special value 'latest' (case-insensitive).

    Raises:
        ToolValidationError: If the value is neither a positive int nor 'latest'.
    """
    if value is None or isinstance(value, int):
        if isinstance(value, int) and value <= 0:
            raise ToolValidationError(f"{field_name} must be a positive integer")
        return value
    normalized = value.strip().lower()
    if normalized != _LATEST:
        raise ToolValidationError(
            f"{field_name} must be a positive integer or '{_LATEST}'"
        )
    return normalized


def require_at_least_one_filter(data: BaseInput) -> None:
    """Ensure at least one filter has a non-null value.

    Checks values, not model_fields_set: clients may send every field as null.

    Raises:
        ToolValidationError: If all filters are None.
    """
    if all(value is None for value in data.model_dump().values()):
        raise ToolValidationError(
            "At least one filter is required to avoid an unbounded API response"
        )


def validate_range(data: BaseInput, field: str) -> None:
    """Validate the <field>_min / <field>_max pair of an input model.

    Rules:
        - <field>_min must be <= <field>_max when both are set.
        - The equality filter <field> cannot be combined with its own range
          filters (contradictory).

    Raises:
        ToolValidationError: On contradictory or inverted ranges.
    """
    min_value = getattr(data, f"{field}_min", None)
    max_value = getattr(data, f"{field}_max", None)
    if min_value is None and max_value is None:
        return
    if getattr(data, field, None) is not None:
        raise ToolValidationError(
            f"{field} cannot be combined with {field}_min/{field}_max: "
            "use either equality or a range, not both"
        )
    if min_value is not None and max_value is not None and min_value > max_value:
        raise ToolValidationError(
            f"{field}_min must be less than or equal to {field}_max"
        )


def validate_date_range(
    data: BaseInput, from_field: str = "date_from", to_field: str = "date_to"
) -> None:
    """Validate an ISO 8601 date range (both bounds inclusive on the API side).

    Rules:
        - Both fields must be valid ISO 8601 when set.
        - <from_field> must be strictly earlier than <to_field>.

    Raises:
        ToolValidationError: On invalid format or inverted range.
    """
    start = getattr(data, from_field, None)
    end = getattr(data, to_field, None)
    if start is None and end is None:
        return
    try:
        start_dt = (
            datetime.fromisoformat(start.replace("Z", "+00:00"))
            if start is not None
            else None
        )
        end_dt = (
            datetime.fromisoformat(end.replace("Z", "+00:00"))
            if end is not None
            else None
        )
    except ValueError as exc:
        raise ToolValidationError(
            f"Dates must be ISO 8601 (e.g., '2026-09-13T13:00:00'): {exc}"
        ) from exc
    if start_dt is not None and end_dt is not None and start_dt >= end_dt:
        raise ToolValidationError(f"{from_field} must be earlier than {to_field}")
