"""MCP tools for car location (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.location import Location, LocationInput
from mcp_sport.services import location as location_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register car location tools on the MCP server instance."""

    @mcp.tool()
    def get_location(
        session_key: int | str | None = None,
        driver_number: int | None = None,
    ) -> list[Location]:
        """Fetch approximate car positions on the circuit from OpenF1.

        Sampled at ~3.7 Hz — responses are large even for a single driver.
        Useful for gauging progress along the track, but lacks lateral placement
        (left/right side). The origin point (0, 0, 0) is arbitrary.

        Args:
            session_key: int | str — required, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — required, 1-99. Driver number for the season.

        Validations:
            - session_key AND driver_number are both required: location is
              sampled at ~3.7 Hz and unscoped queries return huge responses.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[Location]: Position samples with date (ISO 8601 UTC) and
            x, y, z coordinates in a 3D Cartesian system with arbitrary origin.
            Nullable fields: date, x, y, z. No value conversions are applied.
        """
        logger.info(
            "event=tool_call tool=get_location session_key=%s driver_number=%s",
            session_key,
            driver_number,
        )
        filters = LocationInput(session_key=session_key, driver_number=driver_number)
        return location_service.get_location(filters)
