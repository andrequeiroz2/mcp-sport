"""MCP tools for interval data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.intervals import Interval, IntervalsInput
from mcp_sport.services import intervals as intervals_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register interval tools on the MCP server instance."""

    @mcp.tool()
    def get_intervals(
        session_key: int | str | None = None,
        driver_number: int | None = None,
    ) -> list[Interval]:
        """Fetch real-time gaps between drivers and to the race leader from OpenF1.

        Available during races only, with updates approximately every 4 seconds.

        Args:
            session_key: int | str — required in practice, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — optional, 1-99. Driver number for the season.

        Validations:
            - session_key is required: interval data is scoped per session.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[Interval]: Interval samples with date (ISO 8601 UTC),
            gap_to_leader and interval (gap to the car ahead), both in seconds.
            Conversions: gap_to_leader and interval can be the string '+1 LAP'
            for lapped drivers or null for the race leader. Nullable fields:
            date, gap_to_leader, interval.
        """
        logger.info(
            "event=tool_call tool=get_intervals session_key=%s driver_number=%s",
            session_key,
            driver_number,
        )
        filters = IntervalsInput(session_key=session_key, driver_number=driver_number)
        return intervals_service.get_intervals(filters)
