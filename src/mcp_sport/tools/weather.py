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
        air_temperature_min: float | None = None,
        air_temperature_max: float | None = None,
        track_temperature_min: float | None = None,
        track_temperature_max: float | None = None,
        humidity_min: int | None = None,
        humidity_max: int | None = None,
        rainfall_min: int | None = None,
        rainfall_max: int | None = None,
        wind_speed_min: float | None = None,
        wind_speed_max: float | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[Weather]:
        """Fetch weather conditions over the track from OpenF1 (sampled every minute).

        Args:
            session_key: int | str — optional, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            meeting_key: int | str — optional, positive int or 'latest'.
                Meeting (Grand Prix weekend) identifier.
            air_temperature_min / air_temperature_max: float — optional, °C.
                Air temperature range (inclusive).
            track_temperature_min / track_temperature_max: float — optional,
                °C. Track temperature range (inclusive).
            humidity_min / humidity_max: int — optional, 0-100. Humidity
                range (inclusive).
            rainfall_min / rainfall_max: int — optional, 0-1. Rainfall flag
                range (inclusive). Example: rainfall_min=1 returns only
                samples where it was raining.
            wind_speed_min / wind_speed_max: float — optional, m/s. Wind
                speed range (inclusive).
            date_from / date_to: str — optional, ISO 8601 UTC bounds
                (inclusive).

        Validations:
            - At least one of session_key or meeting_key is required (weather is
              sampled every minute — unscoped queries are too broad).
            - session_key/meeting_key accept only a positive int or 'latest'.
            - For every range pair, min must be <= max.
            - date_from must be earlier than date_to; both must be ISO 8601.
            - Responses are cached for up to 30 minutes; for live sessions,
              resolve 'latest' to a concrete session_key via get_sessions
              first, or you may receive slightly stale data.

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
        filters = WeatherInput(
            session_key=session_key,
            meeting_key=meeting_key,
            air_temperature_min=air_temperature_min,
            air_temperature_max=air_temperature_max,
            track_temperature_min=track_temperature_min,
            track_temperature_max=track_temperature_max,
            humidity_min=humidity_min,
            humidity_max=humidity_max,
            rainfall_min=rainfall_min,
            rainfall_max=rainfall_max,
            wind_speed_min=wind_speed_min,
            wind_speed_max=wind_speed_max,
            date_from=date_from,
            date_to=date_to,
        )
        return weather_service.get_weather(filters)
