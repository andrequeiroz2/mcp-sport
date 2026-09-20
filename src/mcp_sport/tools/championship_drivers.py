"""MCP tools for drivers championship (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.championship_drivers import (
    DriversChampionshipEntry,
    DriversChampionshipInput,
)
from mcp_sport.services import championship_drivers as championship_drivers_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register drivers championship tools on the MCP server instance."""

    @mcp.tool()
    def get_drivers_championship(
        session_key: int | str | None = None,
        driver_number: int | None = None,
    ) -> list[DriversChampionshipEntry]:
        """Fetch drivers championship standings from OpenF1 (beta endpoint).

        Only available for race sessions. This endpoint is in beta: its
        behavior or fields may change without notice.

        Args:
            session_key: int | str — required in practice, positive int or
                'latest'. Race session identifier; use get_sessions with
                session_type='Race' to discover it.
            driver_number: int — optional, 1-99. Driver number for the season.

        Validations:
            - session_key is required: standings are computed per race session.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[DriversChampionshipEntry]: Standings with position_start and
            position_current (before/after the race) and points_start and
            points_current. Nullable fields: position_current, position_start,
            points_current, points_start. No value conversions are applied.
        """
        logger.info(
            "event=tool_call tool=get_drivers_championship session_key=%s driver_number=%s",
            session_key,
            driver_number,
        )
        filters = DriversChampionshipInput(
            session_key=session_key,
            driver_number=driver_number,
        )
        return championship_drivers_service.get_drivers_championship(filters)
