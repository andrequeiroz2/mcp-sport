"""Shared base for tool input schemas.

All tool input models must inherit from BaseInput (see
docs/Architectural_Design.md, section 4.2).
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class BaseInput(BaseModel):
    """Base model for tool inputs with shared coercion rules."""

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("*", mode="before")
    @classmethod
    def empty_str_to_none(cls, value: Any) -> Any:
        """Treat empty strings as absent filters (clients may send "" for unset fields)."""
        if isinstance(value, str) and not value.strip():
            return None
        return value
