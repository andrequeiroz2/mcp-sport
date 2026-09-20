"""MCP tools for pit stop data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.pit_stops import PitStop, PitStopsInput
from mcp_sport.services import pit_stops as pit_stops_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register pit stop tools on the MCP server instance."""

    @mcp.tool()
    def get_pit_stops(
        session_key: int | str | None = None,
        driver_number: int | None = None,
        lap_number: int | None = None,
    ) -> list[PitStop]:
        """Fetch pit lane passes for an F1 session from OpenF1.

        Args:
            session_key: int | str — required in practice, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — optional, 1-99. Driver number for the season.
            lap_number: int — optional, >= 1. Lap on which the stop occurred.

        Validations:
            - session_key is required: pit stop data is scoped per session.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[PitStop]: Pit stops with date (ISO 8601 UTC), lap_number,
            lane_duration (total pit lane time, seconds) and stop_duration
            (stationary time, seconds — only available from the 2024 US GP
            onwards). pit_duration is deprecated by OpenF1 (same as
            lane_duration, removed after 2026). Nullable fields: lap_number,
            date, lane_duration, stop_duration, pit_duration. No value
            conversions are applied.
        """
        logger.info(
            "event=tool_call tool=get_pit_stops session_key=%s driver_number=%s",
            session_key,
            driver_number,
        )
        filters = PitStopsInput(
            session_key=session_key,
            driver_number=driver_number,
            lap_number=lap_number,
        )
        return pit_stops_service.get_pit_stops(filters)
