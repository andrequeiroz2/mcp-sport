"""MCP tools for driver data (thin layer — see tasks/01_mcpapi.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.drivers import Driver, DriversInput
from mcp_sport.services import drivers as drivers_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register driver tools on the MCP server instance."""

    @mcp.tool()
    def get_drivers(
        session_key: int | str | None = None,
        meeting_key: int | str | None = None,
        driver_number: int | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        full_name: str | None = None,
        name_acronym: str | None = None,
        team_name: str | None = None,
        country_code: str | None = None,
    ) -> list[Driver]:
        """Fetch F1 drivers from OpenF1, filtered by session, meeting or identity fields.

        Args:
            session_key: int | str — optional, positive int or 'latest'.
                Session identifier; 'latest' targets the current/most recent session.
            meeting_key: int | str — optional, positive int or 'latest'.
                Meeting (Grand Prix weekend) identifier.
            driver_number: int — optional, 1-99. Driver number for the season.
            first_name: str — optional, 1-100 chars. Driver first name.
            last_name: str — optional, 1-100 chars. Driver last name.
            full_name: str — optional, 1-200 chars. Driver full name.
            name_acronym: str — optional, exactly 3 letters (e.g., VER).
                Normalized to uppercase.
            team_name: str — optional, 1-100 chars. Team name.
            country_code: str — optional, 3 letters, normalized to uppercase.
                Deprecated by OpenF1 (removed after the 2026 season).

        Validations:
            - At least one filter is required (unfiltered responses are ~500 KB).
            - session_key/meeting_key accept only a positive int or 'latest'.
            - name_acronym must match three letters after uppercase normalization.

        Returns:
            list[Driver]: Driver records for the given filters. Nullable fields:
            broadcast_name, full_name, first_name, last_name, name_acronym,
            team_name, team_colour (hex RRGGBB without '#'), headshot_url,
            country_code. No value conversions are applied; raw API dicts are
            parsed into Driver models with missing fields defaulting to None.
        """
        logger.info(
            "event=tool_call tool=get_drivers session_key=%s meeting_key=%s driver_number=%s",
            session_key,
            meeting_key,
            driver_number,
        )
        filters = DriversInput(
            session_key=session_key,
            meeting_key=meeting_key,
            driver_number=driver_number,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            name_acronym=name_acronym,
            team_name=team_name,
            country_code=country_code,
        )
        return drivers_service.get_drivers(filters)
