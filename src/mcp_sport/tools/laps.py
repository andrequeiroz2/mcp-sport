"""MCP tools for lap data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.laps import Lap, LapsInput
from mcp_sport.services import laps as laps_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register lap tools on the MCP server instance."""

    @mcp.tool()
    def get_laps(
        session_key: int | str | None = None,
        driver_number: int | None = None,
        lap_number: int | None = None,
    ) -> list[Lap]:
        """Fetch detailed lap-by-lap data for an F1 session from OpenF1.

        Args:
            session_key: int | str — required in practice, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — optional, 1-99. Driver number for the season.
            lap_number: int — optional, >= 1. Sequential lap number in the session.

        Validations:
            - session_key is required: lap data is scoped per session.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[Lap]: Laps with lap_duration, sector times (duration_sector_1/2/3,
            in seconds), speeds in km/h (i1_speed, i2_speed, st_speed),
            is_pit_out_lap flag and mini-sector values (segments_sector_*;
            0=n/a, 2048=yellow, 2049=green, 2051=purple, 2064=pitlane — not
            available during races). Nullable fields: all except session_key,
            meeting_key and driver_number. No value conversions are applied;
            raw API dicts are parsed into models with missing fields as None.
        """
        logger.info(
            "event=tool_call tool=get_laps session_key=%s driver_number=%s lap_number=%s",
            session_key,
            driver_number,
            lap_number,
        )
        filters = LapsInput(
            session_key=session_key,
            driver_number=driver_number,
            lap_number=lap_number,
        )
        return laps_service.get_laps(filters)
