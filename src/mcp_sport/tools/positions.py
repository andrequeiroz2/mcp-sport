"""MCP tools for position data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.positions import Position, PositionsInput
from mcp_sport.services import positions as positions_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register position tools on the MCP server instance."""

    @mcp.tool()
    def get_positions(
        session_key: int | str | None = None,
        meeting_key: int | str | None = None,
        driver_number: int | None = None,
        position: int | None = None,
        position_min: int | None = None,
        position_max: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[Position]:
        """Fetch driver position changes throughout an F1 session from OpenF1.

        Args:
            session_key: int | str — optional, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            meeting_key: int | str — optional, positive int or 'latest'.
                Meeting (Grand Prix weekend) identifier.
            driver_number: int — optional, 1-99. Driver number for the season.
            position: int — optional, >= 1. Exact position (do not combine
                with position_min/max).
            position_min / position_max: int — optional, >= 1. Position range
                (inclusive). Example: position_max=3 returns only records
                where the driver was on the podium.
            date_from / date_to: str — optional, ISO 8601 UTC bounds
                (inclusive).

        Validations:
            - session_key or meeting_key is required to scope the position history.
            - session_key/meeting_key accept only a positive int or 'latest'.
            - position cannot be combined with position_min/position_max;
              for range pairs, min must be <= max.
            - date_from must be earlier than date_to; both must be ISO 8601.
            - Responses are cached for up to 1 hour; for live sessions,
              resolve 'latest' to a concrete session_key via get_sessions
              first, or you may receive slightly stale data.

        Returns:
            list[Position]: Position records over time, each with date
            (ISO 8601 UTC), driver_number and position. Nullable fields:
            position, date. No value conversions are applied; raw API dicts are
            parsed into models with missing fields defaulting to None.
        """
        logger.info(
            "event=tool_call tool=get_positions session_key=%s meeting_key=%s driver_number=%s",
            session_key,
            meeting_key,
            driver_number,
        )
        filters = PositionsInput(
            session_key=session_key,
            meeting_key=meeting_key,
            driver_number=driver_number,
            position=position,
            position_min=position_min,
            position_max=position_max,
            date_from=date_from,
            date_to=date_to,
        )
        return positions_service.get_positions(filters)
