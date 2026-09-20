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
    ) -> list[Position]:
        """Fetch driver position changes throughout an F1 session from OpenF1.

        Args:
            session_key: int | str — optional, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            meeting_key: int | str — optional, positive int or 'latest'.
                Meeting (Grand Prix weekend) identifier.
            driver_number: int — optional, 1-99. Driver number for the season.
            position: int — optional, >= 1. Position of the driver.

        Validations:
            - session_key or meeting_key is required to scope the position history.
            - session_key/meeting_key accept only a positive int or 'latest'.

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
        )
        return positions_service.get_positions(filters)
