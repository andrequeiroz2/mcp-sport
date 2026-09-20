"""MCP tools for teams championship (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.championship_teams import (
    TeamsChampionshipEntry,
    TeamsChampionshipInput,
)
from mcp_sport.services import championship_teams as championship_teams_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register teams championship tools on the MCP server instance."""

    @mcp.tool()
    def get_teams_championship(
        session_key: int | str | None = None,
        team_name: str | None = None,
    ) -> list[TeamsChampionshipEntry]:
        """Fetch teams championship standings from OpenF1 (beta endpoint).

        Only available for race sessions. This endpoint is in beta: its
        behavior or fields may change without notice.

        Args:
            session_key: int | str — required in practice, positive int or
                'latest'. Race session identifier; use get_sessions with
                session_type='Race' to discover it.
            team_name: str — optional, 1-100 chars, e.g., 'McLaren'.

        Validations:
            - session_key is required: standings are computed per race session.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[TeamsChampionshipEntry]: Standings with team_name,
            position_start and position_current (before/after the race) and
            points_start and points_current. Nullable fields: position_current,
            position_start, points_current, points_start. No value conversions
            are applied.
        """
        logger.info(
            "event=tool_call tool=get_teams_championship session_key=%s team_name=%s",
            session_key,
            team_name,
        )
        filters = TeamsChampionshipInput(session_key=session_key, team_name=team_name)
        return championship_teams_service.get_teams_championship(filters)
