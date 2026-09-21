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
        speed_min: int | None = None,
        speed_max: int | None = None,
        rpm_min: int | None = None,
        rpm_max: int | None = None,
        throttle_min: int | None = None,
        throttle_max: int | None = None,
        n_gear_min: int | None = None,
        n_gear_max: int | None = None,
        drs_min: int | None = None,
        drs_max: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[CarData]:
        """Fetch car telemetry (speed, rpm, gear, throttle, brake, DRS) from OpenF1.

        Sampled at ~3.7 Hz — always narrow down with the range filters below
        (e.g., a single lap via date_from/date_to, or high-speed samples via
        speed_min) to keep responses usable.

        Args:
            session_key: int | str — required, positive int or 'latest'.
                Session identifier; use get_sessions to discover it.
            driver_number: int — required, 1-99. Driver number for the season.
            speed_min / speed_max: int — optional, >= 0. Speed range in km/h
                (both inclusive). Example: speed_min=300 returns only samples
                at 300 km/h or more.
            rpm_min / rpm_max: int — optional, >= 0. Engine rpm range (inclusive).
            throttle_min / throttle_max: int — optional, 0-100. Throttle %
                range (inclusive).
            n_gear_min / n_gear_max: int — optional, 0-8. Gear range (inclusive).
            drs_min / drs_max: int — optional, 0-14. DRS status range
                (inclusive; 0/1 = off, 8 = eligible, 10/12/14 = on).
            date_from / date_to: str — optional, ISO 8601 UTC bounds
                (inclusive). To isolate one lap, call get_laps first and use
                the lap's date_start as date_from and the next lap's
                date_start as date_to.

        Validations:
            - session_key AND driver_number are both required: telemetry is
              sampled at ~3.7 Hz and unscoped queries return huge responses.
            - session_key accepts only a positive int or 'latest'.
            - For every range pair, min must be <= max.
            - date_from must be earlier than date_to; both must be ISO 8601.
            - Responses are cached for up to 1 hour; for live sessions,
              resolve 'latest' to a concrete session_key via get_sessions
              first, or you may receive slightly stale data.

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
        filters = CarDataInput(
            session_key=session_key,
            driver_number=driver_number,
            speed_min=speed_min,
            speed_max=speed_max,
            rpm_min=rpm_min,
            rpm_max=rpm_max,
            throttle_min=throttle_min,
            throttle_max=throttle_max,
            n_gear_min=n_gear_min,
            n_gear_max=n_gear_max,
            drs_min=drs_min,
            drs_max=drs_max,
            date_from=date_from,
            date_to=date_to,
        )
        return car_data_service.get_car_data(filters)
