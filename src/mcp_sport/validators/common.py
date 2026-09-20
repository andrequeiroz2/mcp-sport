"""Shared validation helpers for tool input models."""

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
