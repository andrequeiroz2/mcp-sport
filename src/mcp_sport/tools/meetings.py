"""MCP tools for meeting data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.meetings import Meeting, MeetingsInput
from mcp_sport.services import meetings as meetings_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register meeting tools on the MCP server instance."""

    @mcp.tool()
    def get_meetings(
        meeting_key: int | str | None = None,
        year: int | None = None,
        country_name: str | None = None,
        meeting_name: str | None = None,
        circuit_key: int | None = None,
        location: str | None = None,
    ) -> list[Meeting]:
        """Fetch F1 meetings (Grand Prix or testing weekends) from OpenF1.

        Args:
            meeting_key: int | str — optional, positive int or 'latest'.
                Meeting identifier; 'latest' targets the current/most recent meeting.
            year: int — optional, >= 2023 (OpenF1 data starts in 2023).
            country_name: str — optional, 1-100 chars, e.g., 'Singapore'.
            meeting_name: str — optional, 1-100 chars, e.g., 'Singapore Grand Prix'.
            circuit_key: int — optional, positive int. Circuit identifier.
            location: str — optional, 1-100 chars, e.g., 'Marina Bay'.

        Validations:
            - At least one filter with a non-null value is required.
            - meeting_key accepts only a positive int or 'latest'.

        Returns:
            list[Meeting]: Meetings matching the filters, including meeting_key
            (use it to query other endpoints), meeting_name, date_start/date_end
            (ISO 8601 UTC), circuit info (with image URLs) and country info.
            Nullable fields: all except meeting_key. No value conversions are
            applied; raw API dicts are parsed into Meeting models with missing
            fields defaulting to None.
        """
        logger.info(
            "event=tool_call tool=get_meetings meeting_key=%s year=%s",
            meeting_key,
            year,
        )
        filters = MeetingsInput(
            meeting_key=meeting_key,
            year=year,
            country_name=country_name,
            meeting_name=meeting_name,
            circuit_key=circuit_key,
            location=location,
        )
        return meetings_service.get_meetings(filters)
