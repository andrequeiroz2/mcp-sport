"""MCP tools for session results (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.session_results import SessionResult, SessionResultsInput
from mcp_sport.services import session_results as session_results_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register session result tools on the MCP server instance."""

    @mcp.tool()
    def get_session_results(
        session_key: int | str | None = None,
        driver_number: int | None = None,
        position: int | None = None,
    ) -> list[SessionResult]:
        """Fetch the final classification of an F1 session from OpenF1.

        Results become available a few minutes after the official results are
        published on the Formula 1 website. If the API returns HTTP 404, the
        results are not yet published for that session — retry with an earlier
        session_key (use get_sessions to find completed sessions).

        Args:
            session_key: int | str — required in practice, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — optional, 1-99. Driver number for the season.
            position: int — optional, >= 1. Final position in the session.

        Validations:
            - session_key is required: results are only published per session.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[SessionResult]: Final standings with position, number_of_laps,
            dnf/dns/dsq flags, duration and gap_to_leader. Nullable fields:
            position, number_of_laps, dnf, dns, dsq, duration, gap_to_leader.
            Conversions: duration and gap_to_leader are floats in seconds, but
            in qualifying sessions they are arrays of three values (Q1, Q2, Q3);
            gap_to_leader can also be the string '+N LAP(S)' for lapped drivers.
        """
        logger.info(
            "event=tool_call tool=get_session_results session_key=%s driver_number=%s",
            session_key,
            driver_number,
        )
        filters = SessionResultsInput(
            session_key=session_key,
            driver_number=driver_number,
            position=position,
        )
        return session_results_service.get_session_results(filters)
