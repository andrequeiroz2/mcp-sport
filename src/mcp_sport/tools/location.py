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
        x_min: int | None = None,
        x_max: int | None = None,
        y_min: int | None = None,
        y_max: int | None = None,
        z_min: int | None = None,
        z_max: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[Location]:
        """Fetch approximate car positions on the circuit from OpenF1.

        Sampled at ~3.7 Hz — always narrow down with date_from/date_to (e.g.,
        a single lap) to keep responses usable. Useful for gauging progress
        along the track, but lacks lateral placement (left/right side). The
        origin point (0, 0, 0) is arbitrary.

        Args:
            session_key: int | str — required, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — required, 1-99. Driver number for the season.
            x_min / x_max: int — optional. X coordinate range (inclusive).
            y_min / y_max: int — optional. Y coordinate range (inclusive).
            z_min / z_max: int — optional. Z coordinate range (inclusive).
            date_from / date_to: str — optional, ISO 8601 UTC bounds
                (inclusive). To isolate one lap, call get_laps first and use
                the lap's date_start as date_from and the next lap's
                date_start as date_to.

        Validations:
            - session_key AND driver_number are both required: location is
              sampled at ~3.7 Hz and unscoped queries return huge responses.
            - session_key accepts only a positive int or 'latest'.
            - For every range pair, min must be <= max.
            - date_from must be earlier than date_to; both must be ISO 8601.
            - Responses are cached for up to 1 hour; for live sessions,
              resolve 'latest' to a concrete session_key via get_sessions
              first, or you may receive slightly stale data.

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
        filters = LocationInput(
            session_key=session_key,
            driver_number=driver_number,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
            z_min=z_min,
            z_max=z_max,
            date_from=date_from,
            date_to=date_to,
        )
        return location_service.get_location(filters)
