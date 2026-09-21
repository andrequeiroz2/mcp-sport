"""Shared helpers for service layers (see docs/Architectural_Design.md)."""

from typing import Any

from mcp_sport.schemas.base import BaseInput


def build_params(
    data: BaseInput, operator_fields: dict[str, str] | None = None
) -> dict[str, Any]:
    """Build OpenF1 query params from a validated input model.

    Args:
        data: Validated input model (only explicitly set fields are included).
        operator_fields: Maps friendly range fields to API operator keys,
            e.g. {"speed_min": "speed>=", "speed_max": "speed<="}.
            Fields not listed are sent as equality filters.

    Returns:
        Query params ready for clients/openf1.py (which serializes operator
        keys literally — see its _build_query).
    """
    mapping = operator_fields or {}
    return {
        mapping.get(key, key): value
        for key, value in data.model_dump().items()
        if key in data.model_fields_set
    }
