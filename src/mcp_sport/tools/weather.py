"""MCP tools for weather data (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.weather import Weather, WeatherInput
from mcp_sport.services import weather as weather_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register weather tools on the MCP server instance."""

    @mcp.tool()
    def get_weather(
        session_key: int | str | None = None,
        meeting_key: int | str | None = None,
    ) -> list[Weather]:
        """Fetch weather conditions over the track from OpenF1 (sampled every minute).

        Args:
            session_key: int | str — optional, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            meeting_key: int | str — optional, positive int or 'latest'.
                Meeting (Grand Prix weekend) identifier.

        Validations:
            - At least one of session_key or meeting_key is required (weather is
              sampled every minute — unscoped queries are too broad).
            - session_key/meeting_key accept only a positive int or 'latest'.

        Returns:
            list[Weather]: Weather samples with date (ISO 8601 UTC),
            air_temperature and track_temperature (°C), humidity (%),
            pressure (mbar), rainfall (0 = no, 1 = yes), wind_direction
            (0-359°) and wind_speed (m/s). Nullable fields: all except
            session_key and meeting_key. No value conversions are applied.
        """
        logger.info(
            "event=tool_call tool=get_weather session_key=%s meeting_key=%s",
            session_key,
            meeting_key,
        )
        filters = WeatherInput(session_key=session_key, meeting_key=meeting_key)
        return weather_service.get_weather(filters)
