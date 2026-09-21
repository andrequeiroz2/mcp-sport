"""HTTP client for the OpenF1 API.

Centralizes URL building, query param serialization and response parsing.
Logs follow docs/Logging_Strategy.md (logger: mcp_sport.openf1).
"""

import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from mcp_sport.exceptions import OpenF1APIError
from mcp_sport.logging_config import get_logger

BASE_URL = "https://api.openf1.org/v1"
DEFAULT_TIMEOUT_SECONDS = 10
_RETRY_STATUSES = {429, 503}
_MAX_ATTEMPTS = 4

_OPERATOR_SUFFIXES = (">=", "<=", ">", "<")

logger = get_logger("openf1")


def _build_query(params: dict[str, Any]) -> str:
    """Serialize query params keeping OpenF1 operator suffixes literal.

    The OpenF1 API parses the raw query string and does NOT percent-decode
    parameter names: 'speed>=' must be sent literally. A key ending in an
    operator suffix is joined to its value without an extra '=' separator
    ('speed>=' + 315 -> 'speed>=315'); plain keys use the standard 'key=value'.
    """
    parts = []
    for key, value in params.items():
        if value is None:
            continue
        encoded_key = quote(str(key), safe="><=")
        separator = "" if encoded_key.endswith(_OPERATOR_SUFFIXES) else "="
        parts.append(f"{encoded_key}{separator}{quote(str(value))}")
    return "&".join(parts)


def _retry_delay(exc: HTTPError, attempt: int) -> float:
    """Seconds to wait before retrying a rate-limited OpenF1 response."""
    header = exc.headers.get("Retry-After") if exc.headers else None
    if header and header.isdigit():
        return min(float(header), 15)
    return float(2 ** (attempt - 1))


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
    query = _build_query(params)
    url = f"{BASE_URL}/{path}?{query}" if query else f"{BASE_URL}/{path}"

    logger.info("event=openf1_request path=%s params=%s", path, query)
    start = time.perf_counter()
    data = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            with urlopen(url, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except HTTPError as exc:
            if exc.code in _RETRY_STATUSES and attempt < _MAX_ATTEMPTS:
                delay = _retry_delay(exc, attempt)
                logger.warning(
                    "event=openf1_retry path=%s status=%s attempt=%d delay_s=%.1f",
                    path,
                    exc.code,
                    attempt,
                    delay,
                )
                exc.close()
                time.sleep(delay)
                continue
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
