"""MCP tools for starting grid data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.starting_grid import StartingGridEntry, StartingGridInput
from mcp_sport.services import starting_grid as starting_grid_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register starting grid tools on the MCP server instance."""

    @mcp.tool()
    def get_starting_grid(
        session_key: int | str | None = None,
        driver_number: int | None = None,
        position: int | None = None,
    ) -> list[StartingGridEntry]:
        """Fetch the starting grid for an F1 race from OpenF1.

        Grid data becomes available a few minutes after the official results
        are published on the Formula 1 website. If the API returns HTTP 404,
        the grid is not yet published for that session — retry with an earlier
        session_key (use get_sessions to find completed sessions).

        Args:
            session_key: int | str — required in practice, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — optional, 1-99. Driver number for the season.
            position: int — optional, >= 1. Position on the grid.

        Validations:
            - session_key is required: grids are only published per session.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[StartingGridEntry]: Grid entries with position, driver_number
            and lap_duration (qualifying lap, in seconds). Nullable fields:
            position, lap_duration. No value conversions are applied; raw API
            dicts are parsed into models with missing fields defaulting to None.
        """
        logger.info(
            "event=tool_call tool=get_starting_grid session_key=%s driver_number=%s",
            session_key,
            driver_number,
        )
        filters = StartingGridInput(
            session_key=session_key,
            driver_number=driver_number,
            position=position,
        )
        return starting_grid_service.get_starting_grid(filters)
