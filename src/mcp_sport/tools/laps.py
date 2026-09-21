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
        lap_number_min: int | None = None,
        lap_number_max: int | None = None,
        lap_duration_min: float | None = None,
        lap_duration_max: float | None = None,
        duration_sector_1_min: float | None = None,
        duration_sector_1_max: float | None = None,
        duration_sector_2_min: float | None = None,
        duration_sector_2_max: float | None = None,
        duration_sector_3_min: float | None = None,
        duration_sector_3_max: float | None = None,
        i1_speed_min: int | None = None,
        i1_speed_max: int | None = None,
        i2_speed_min: int | None = None,
        i2_speed_max: int | None = None,
        st_speed_min: int | None = None,
        st_speed_max: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[Lap]:
        """Fetch detailed lap-by-lap data for an F1 session from OpenF1.

        Args:
            session_key: int | str — required in practice, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — optional, 1-99. Driver number for the season.
            lap_number: int — optional, >= 1. Exact lap number (do not combine
                with lap_number_min/max).
            lap_number_min / lap_number_max: int — optional, >= 1. Lap number
                range (inclusive).
            lap_duration_min / lap_duration_max: float — optional, seconds.
                Lap time range (inclusive). Example: lap_duration_max=80
                returns only laps of 1m20s or less.
            duration_sector_1_min/max, duration_sector_2_min/max,
            duration_sector_3_min/max: float — optional, seconds. Sector time
                ranges (inclusive).
            i1_speed_min/max, i2_speed_min/max, st_speed_min/max: int —
                optional, km/h. Speed ranges at the intermediates and speed
                trap (inclusive).
            date_from / date_to: str — optional, ISO 8601 UTC bounds on the
                lap start (date_start), inclusive.

        Validations:
            - session_key is required: lap data is scoped per session.
            - session_key accepts only a positive int or 'latest'.
            - For every range pair, min must be <= max; an equality filter
              cannot be combined with its own range (e.g., lap_number with
              lap_number_min).
            - date_from must be earlier than date_to; both must be ISO 8601.

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
            lap_number_min=lap_number_min,
            lap_number_max=lap_number_max,
            lap_duration_min=lap_duration_min,
            lap_duration_max=lap_duration_max,
            duration_sector_1_min=duration_sector_1_min,
            duration_sector_1_max=duration_sector_1_max,
            duration_sector_2_min=duration_sector_2_min,
            duration_sector_2_max=duration_sector_2_max,
            duration_sector_3_min=duration_sector_3_min,
            duration_sector_3_max=duration_sector_3_max,
            i1_speed_min=i1_speed_min,
            i1_speed_max=i1_speed_max,
            i2_speed_min=i2_speed_min,
            i2_speed_max=i2_speed_max,
            st_speed_min=st_speed_min,
            st_speed_max=st_speed_max,
            date_from=date_from,
            date_to=date_to,
        )
        return laps_service.get_laps(filters)
