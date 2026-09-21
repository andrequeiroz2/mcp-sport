"""Response cache configuration for mcp-sport (see tasks/04_cache.md).

Uses FastMCP's official ResponseCachingMiddleware. One middleware instance per
TTL group, with disjoint included_tools lists: a tool is cached by exactly one
instance, and instances pass through tools they don't include.

Env vars:
- MCP_SPORT_CACHE_ENABLED: "true" (default) / "false" — master switch.
- MCP_SPORT_CACHE_BACKEND: "memory" (default) / "file".
- MCP_SPORT_CACHE_DIR: directory for the file backend
  (default: .cache/mcp_sport).
"""

import os
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.middleware.caching import (
    CallToolSettings,
    ListToolsSettings,
    ResponseCachingMiddleware,
)
from key_value.aio.protocols.key_value import AsyncKeyValue

from mcp_sport.logging_config import get_logger

logger = get_logger("cache")

TTL_30_SECONDS = 30
TTL_30_MINUTES = 30 * 60
TTL_1_HOUR = 60 * 60
TTL_6_HOURS = 6 * 60 * 60
TTL_24_HOURS = 24 * 60 * 60

# (ttl_seconds, tools) — disjoint groups; see tasks/04_cache.md, section 4.
_TOOL_TTL_GROUPS: tuple[tuple[int, list[str]], ...] = (
    (TTL_24_HOURS, ["get_meetings", "get_sessions"]),
    (TTL_6_HOURS, ["get_session_results", "get_starting_grid"]),
    (
        TTL_1_HOUR,
        [
            "get_drivers",
            "get_laps",
            "get_pit_stops",
            "get_stints",
            "get_positions",
            "get_race_control",
            "get_overtakes",
            "get_team_radio",
            "get_car_data",
            "get_location",
            "get_drivers_championship",
            "get_teams_championship",
        ],
    ),
    (TTL_30_MINUTES, ["get_weather"]),
    (TTL_30_SECONDS, ["get_intervals"]),
)

_DEFAULT_CACHE_DIR = ".cache/mcp_sport"


def _build_storage() -> AsyncKeyValue | None:
    """Build the cache backend from env vars (None = default in-memory)."""
    backend = os.environ.get("MCP_SPORT_CACHE_BACKEND", "memory").lower()
    if backend == "memory":
        return None
    if backend == "file":
        from key_value.aio.stores.filetree import (
            FileTreeStore,
            FileTreeV1CollectionSanitizationStrategy,
            FileTreeV1KeySanitizationStrategy,
        )

        cache_dir = Path(os.environ.get("MCP_SPORT_CACHE_DIR", _DEFAULT_CACHE_DIR))
        return FileTreeStore(
            data_directory=cache_dir,
            key_sanitization_strategy=FileTreeV1KeySanitizationStrategy(cache_dir),
            collection_sanitization_strategy=FileTreeV1CollectionSanitizationStrategy(
                cache_dir
            ),
        )
    raise ValueError(
        f"Invalid MCP_SPORT_CACHE_BACKEND: {backend!r} (expected 'memory' or 'file')"
    )


def setup_cache(mcp: FastMCP) -> None:
    """Attach response caching middleware to the server, one per TTL group."""
    if os.environ.get("MCP_SPORT_CACHE_ENABLED", "true").lower() not in (
        "1",
        "true",
        "yes",
    ):
        logger.info("event=cache_disabled")
        return

    storage = _build_storage()
    for ttl, tools in _TOOL_TTL_GROUPS:
        mcp.add_middleware(
            ResponseCachingMiddleware(
                cache_storage=storage,
                call_tool_settings=CallToolSettings(ttl=ttl, included_tools=tools),
                list_tools_settings=ListToolsSettings(enabled=False),
            )
        )
        logger.info(
            "event=cache_group ttl_seconds=%d tools=%s", ttl, ",".join(tools)
        )

    # tools/list caching only (tools/call disabled: every tool is already
    # covered by exactly one TTL group above).
    mcp.add_middleware(
        ResponseCachingMiddleware(
            cache_storage=storage,
            call_tool_settings=CallToolSettings(enabled=False),
            list_tools_settings=ListToolsSettings(ttl=TTL_30_SECONDS),
        )
    )
    logger.info("event=cache_enabled backend=%s", storage is None and "memory" or "file")
