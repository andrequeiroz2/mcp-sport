"""MCP server entrypoint: FastMCP instance and tool registration."""

from fastmcp import FastMCP

from mcp_sport.apps import championship_view, race_replay_view
from mcp_sport.cache_config import setup_cache
from mcp_sport.logging_config import setup_logging
from mcp_sport.tools import (
    car_data,
    championship_drivers,
    championship_teams,
    drivers,
    intervals,
    laps,
    location,
    meetings,
    overtakes,
    pit_stops,
    positions,
    race_control,
    session_results,
    sessions,
    starting_grid,
    stints,
    team_radio,
    weather,
)

setup_logging()

mcp = FastMCP("F1 Telemetry MCP 🏎️")

setup_cache(mcp)

drivers.register(mcp)
sessions.register(mcp)
meetings.register(mcp)
session_results.register(mcp)
starting_grid.register(mcp)
positions.register(mcp)
laps.register(mcp)
pit_stops.register(mcp)
stints.register(mcp)
intervals.register(mcp)
race_control.register(mcp)
weather.register(mcp)
overtakes.register(mcp)
team_radio.register(mcp)
car_data.register(mcp)
location.register(mcp)
championship_drivers.register(mcp)
championship_teams.register(mcp)
championship_view.register(mcp)
race_replay_view.register(mcp)


if __name__ == "__main__":
    mcp.run()
