"""MCP tools for overtake data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.overtakes import Overtake, OvertakesInput
from mcp_sport.services import overtakes as overtakes_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register overtake tools on the MCP server instance."""

    @mcp.tool()
    def get_overtakes(
        session_key: int | str | None = None,
        overtaking_driver_number: int | None = None,
        overtaken_driver_number: int | None = None,
        position: int | None = None,
    ) -> list[Overtake]:
        """Fetch overtakes during F1 races from OpenF1.

        Covers on-track passes and position changes from pit stops or
        post-race penalties. Only available during races and may be incomplete.

        Args:
            session_key: int | str — required in practice, positive int or 'latest'.
                Race session identifier; use get_sessions to discover it.
            overtaking_driver_number: int — optional, 1-99. The attacking driver.
            overtaken_driver_number: int — optional, 1-99. The passed driver.
            position: int — optional, >= 1. Position of the overtaking driver
                after the overtake.

        Validations:
            - session_key is required: overtakes are scoped per race session.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[Overtake]: Overtakes with date (ISO 8601 UTC),
            overtaking_driver_number, overtaken_driver_number and position
            after the pass. Nullable fields: date, overtaking_driver_number,
            overtaken_driver_number, position. No value conversions applied.
        """
        logger.info(
            "event=tool_call tool=get_overtakes session_key=%s overtaking=%s overtaken=%s",
            session_key,
            overtaking_driver_number,
            overtaken_driver_number,
        )
        filters = OvertakesInput(
            session_key=session_key,
            overtaking_driver_number=overtaking_driver_number,
            overtaken_driver_number=overtaken_driver_number,
            position=position,
        )
        return overtakes_service.get_overtakes(filters)
