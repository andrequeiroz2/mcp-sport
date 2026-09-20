"""MCP tools for race control data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.race_control import RaceControlInput, RaceControlMessage
from mcp_sport.services import race_control as race_control_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register race control tools on the MCP server instance."""

    @mcp.tool()
    def get_race_control(
        session_key: int | str | None = None,
        driver_number: int | None = None,
        flag: str | None = None,
        category: str | None = None,
        scope: str | None = None,
    ) -> list[RaceControlMessage]:
        """Fetch race control events (flags, safety car, incidents) from OpenF1.

        Args:
            session_key: int | str — optional, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — optional, 1-99. Driver number for the season.
            flag: str — optional, 1-50 chars, e.g., 'YELLOW', 'BLACK AND WHITE'.
                Normalized to uppercase.
            category: str — optional, e.g., 'SessionStatus', 'CarEvent', 'Drs',
                'Flag', 'SafetyCar'.
            scope: str — optional, e.g., 'Track', 'Driver', 'Sector'.

        Validations:
            - session_key or driver_number is required to scope the messages.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[RaceControlMessage]: Events with date (ISO 8601 UTC), category,
            flag, message, scope, sector, lap_number and qualifying_phase.
            Nullable fields: all except session_key and meeting_key —
            driver_number is null for non-driver-specific events. No value
            conversions are applied.
        """
        logger.info(
            "event=tool_call tool=get_race_control session_key=%s driver_number=%s flag=%s",
            session_key,
            driver_number,
            flag,
        )
        filters = RaceControlInput(
            session_key=session_key,
            driver_number=driver_number,
            flag=flag,
            category=category,
            scope=scope,
        )
        return race_control_service.get_race_control(filters)
