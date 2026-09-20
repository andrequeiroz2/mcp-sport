"""MCP tools for team radio data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.team_radio import TeamRadio, TeamRadioInput
from mcp_sport.services import team_radio as team_radio_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register team radio tools on the MCP server instance."""

    @mcp.tool()
    def get_team_radio(
        session_key: int | str | None = None,
        driver_number: int | None = None,
    ) -> list[TeamRadio]:
        """Fetch team radio exchanges between drivers and teams from OpenF1.

        Only a limited selection of communications is included, not the complete
        record. Coverage has decreased significantly starting in 2026, with most
        events providing no radio data at all (a limitation on F1's side).

        Args:
            session_key: int | str — required in practice, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — optional, 1-99. Driver number for the season.

        Validations:
            - session_key is required: team radio is scoped per session.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[TeamRadio]: Radio exchanges with date (ISO 8601 UTC),
            driver_number and recording_url (MP3). Nullable fields: date,
            recording_url. No value conversions are applied; raw API dicts are
            parsed into models with missing fields defaulting to None.
        """
        logger.info(
            "event=tool_call tool=get_team_radio session_key=%s driver_number=%s",
            session_key,
            driver_number,
        )
        filters = TeamRadioInput(session_key=session_key, driver_number=driver_number)
        return team_radio_service.get_team_radio(filters)
