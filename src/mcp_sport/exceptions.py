"""Project domain exceptions (see docs/Logging_Strategy.md and python-patterns skill)."""


class MCPSportError(Exception):
    """Base exception for the project."""


class OpenF1APIError(MCPSportError):
    """Failure calling the OpenF1 API."""

    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"OpenF1 request failed: {url} ({reason})")


class ToolValidationError(MCPSportError):
    """Business/operation validation failed before calling the API."""
