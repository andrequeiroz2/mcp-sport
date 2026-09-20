"""HTTP client for the OpenF1 API.

Centralizes URL building, query param serialization and response parsing.
Logs follow docs/Logging_Strategy.md (logger: mcp_sport.openf1).
"""

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from mcp_sport.exceptions import OpenF1APIError
from mcp_sport.logging_config import get_logger

BASE_URL = "https://api.openf1.org/v1"
DEFAULT_TIMEOUT_SECONDS = 10

logger = get_logger("openf1")


def get(path: str, params: dict[str, Any]) -> list[dict]:
    """Perform a GET request to the OpenF1 API.

    Args:
        path: Endpoint path (e.g., "drivers").
        params: Query parameters. Entries with None values are skipped.

    Returns:
        Parsed JSON response as a list of dicts.

    Raises:
        OpenF1APIError: On network, HTTP or parsing failures.
    """
    query = urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{BASE_URL}/{path}?{query}" if query else f"{BASE_URL}/{path}"

    logger.info("event=openf1_request path=%s params=%s", path, query)
    start = time.perf_counter()
    try:
        with urlopen(url, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        logger.exception("event=openf1_error path=%s status=%s", path, exc.code)
        raise OpenF1APIError(url, f"HTTP {exc.code}") from exc
    except URLError as exc:
        logger.exception("event=openf1_error path=%s", path)
        raise OpenF1APIError(url, str(exc.reason)) from exc
    except json.JSONDecodeError as exc:
        logger.exception("event=openf1_error path=%s", path)
        raise OpenF1APIError(url, "invalid JSON response") from exc

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "event=openf1_response path=%s results=%d duration_ms=%.0f",
        path,
        len(data),
        duration_ms,
    )
    return data
