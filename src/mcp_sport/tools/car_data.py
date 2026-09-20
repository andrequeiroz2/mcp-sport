"""MCP tools for car telemetry (thin layer — see docs/Architectural_Design.md)."""

from fastmcp import FastMCP

from mcp_sport.logging_config import get_logger
from mcp_sport.schemas.car_data import CarData, CarDataInput
from mcp_sport.services import car_data as car_data_service

logger = get_logger("tools")


def register(mcp: FastMCP) -> None:
    """Register car telemetry tools on the MCP server instance."""

    @mcp.tool()
    def get_car_data(
        session_key: int | str | None = None,
        driver_number: int | None = None,
    ) -> list[CarData]:
        """Fetch car telemetry (speed, rpm, gear, throttle, brake, DRS) from OpenF1.

        Sampled at ~3.7 Hz — responses are large even for a single driver.

        Args:
            session_key: int | str — required, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — required, 1-99. Driver number for the season.

        Validations:
            - session_key AND driver_number are both required: telemetry is
              sampled at ~3.7 Hz and unscoped queries return huge responses.
            - session_key accepts only a positive int or 'latest'.

        Returns:
            list[CarData]: Telemetry samples with date (ISO 8601 UTC), speed
            (km/h), rpm, n_gear (1-8, 0 = neutral), throttle (0-100%), brake
            (0 or 100) and drs status (0/1 = off, 8 = eligible, 10/12/14 = on).
            Nullable fields: date, speed, rpm, n_gear, throttle, brake, drs.
            No value conversions are applied.
        """
        logger.info(
            "event=tool_call tool=get_car_data session_key=%s driver_number=%s",
            session_key,
            driver_number,
        )
        filters = CarDataInput(session_key=session_key, driver_number=driver_number)
        return car_data_service.get_car_data(filters)
