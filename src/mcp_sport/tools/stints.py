"""MCP tools for stint data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.stints import Stint, StintsInput
from mcp_sport.services import stints as stints_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register stint tools on the MCP server instance."""

    @mcp.tool()
    def get_stints(
        session_key: int | str | None = None,
        driver_number: int | None = None,
        stint_number: int | None = None,
        compound: str | None = None,
        lap_start_min: int | None = None,
        lap_start_max: int | None = None,
        lap_end_min: int | None = None,
        lap_end_max: int | None = None,
        tyre_age_at_start_min: int | None = None,
        tyre_age_at_start_max: int | None = None,
    ) -> list[Stint]:
        """Fetch tyre stints (periods of continuous driving) from OpenF1.

        Args:
            session_key: int | str — required in practice, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — optional, 1-99. Driver number for the season.
            stint_number: int — optional, >= 1. Sequential stint number.
            compound: str — optional, 1-20 chars, e.g., 'SOFT', 'MEDIUM', 'HARD'.
                Normalized to uppercase.
            lap_start_min / lap_start_max: int — optional, >= 1. Range of
                stint start laps (inclusive).
            lap_end_min / lap_end_max: int — optional, >= 1. Range of stint
                end laps (inclusive).
            tyre_age_at_start_min / tyre_age_at_start_max: int — optional,
                >= 0. Tyre age range in laps (inclusive). Example:
                tyre_age_at_start_min=20 returns only stints started on
                heavily used tyres.

        Validations:
            - session_key is required: stint data is scoped per session.
            - session_key accepts only a positive int or 'latest'.
            - For every range pair, min must be <= max.

        Returns:
            list[Stint]: Stints with compound, lap_start, lap_end and
            tyre_age_at_start (in laps). Nullable fields: stint_number,
            compound, lap_start, lap_end, tyre_age_at_start. No value
            conversions are applied; raw API dicts are parsed into models with
            missing fields defaulting to None.
        """
        logger.info(
            "event=tool_call tool=get_stints session_key=%s driver_number=%s compound=%s",
            session_key,
            driver_number,
            compound,
        )
        filters = StintsInput(
            session_key=session_key,
            driver_number=driver_number,
            stint_number=stint_number,
            compound=compound,
            lap_start_min=lap_start_min,
            lap_start_max=lap_start_max,
            lap_end_min=lap_end_min,
            lap_end_max=lap_end_max,
            tyre_age_at_start_min=tyre_age_at_start_min,
            tyre_age_at_start_max=tyre_age_at_start_max,
        )
        return stints_service.get_stints(filters)
