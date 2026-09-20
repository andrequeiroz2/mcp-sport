"""MCP tools for session data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.sessions import Session, SessionsInput
from mcp_sport.services import sessions as sessions_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register session tools on the MCP server instance."""

    @mcp.tool()
    def get_sessions(
        session_key: int | str | None = None,
        meeting_key: int | str | None = None,
        year: int | None = None,
        country_name: str | None = None,
        session_name: str | None = None,
        session_type: str | None = None,
        circuit_key: int | None = None,
        location: str | None = None,
    ) -> list[Session]:
        """Fetch F1 sessions (practice, qualifying, sprint, race) from OpenF1.

        Args:
            session_key: int | str — optional, positive int or 'latest'.
                Session identifier; 'latest' targets the current/most recent session.
            meeting_key: int | str — optional, positive int or 'latest'.
                Meeting (Grand Prix weekend) identifier.
            year: int — optional, >= 2023 (OpenF1 data starts in 2023).
            country_name: str — optional, 1-100 chars, e.g., 'Belgium'.
            session_name: str — optional, e.g., 'Practice 1', 'Qualifying', 'Race'.
            session_type: str — optional, e.g., 'Practice', 'Qualifying', 'Race'.
            circuit_key: int — optional, positive int. Circuit identifier.
            location: str — optional, 1-100 chars, e.g., 'Spa-Francorchamps'.

        Validations:
            - At least one filter with a non-null value is required.
            - session_key/meeting_key accept only a positive int or 'latest'.

        Returns:
            list[Session]: Sessions matching the filters, including session_key
            (use it to query other endpoints), session_name, session_type,
            date_start/date_end (ISO 8601 UTC), circuit and country info.
            Nullable fields: all except session_key and meeting_key.
            No value conversions are applied; raw API dicts are parsed into
            Session models with missing fields defaulting to None.
        """
        logger.info(
            "event=tool_call tool=get_sessions session_key=%s meeting_key=%s year=%s",
            session_key,
            meeting_key,
            year,
        )
        filters = SessionsInput(
            session_key=session_key,
            meeting_key=meeting_key,
            year=year,
            country_name=country_name,
            session_name=session_name,
            session_type=session_type,
            circuit_key=circuit_key,
            location=location,
        )
        return sessions_service.get_sessions(filters)
