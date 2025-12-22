import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

import httpx

# Default configuration
DEFAULT_TIMEOUT = 5.0
DEFAULT_MAX_RETRIES = 3
BACKOFF_MULTIPLIER = 0.5  # 0.5s, 1s, 2s


async def run_http_skill(
    params: Dict[str, Any], max_retries: int = DEFAULT_MAX_RETRIES, timeout: float = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    Resilient HTTP skill with timeout, retries, and exponential backoff.
    Returns structured result with attempt tracking.
    """
    url = params.get("url", "https://api.github.com/zen")
    method = params.get("method", "GET").upper()
    timeout = params.get("timeout", timeout)
    max_retries = params.get("max_retries", max_retries)

    started_at = datetime.now(timezone.utc)
    attempts = 0
    last_error = None

    for attempt in range(max_retries):
        attempts = attempt + 1
        attempt_started = datetime.now(timezone.utc)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    response = await client.get(url)
                else:
                    response = await client.request(method, url)

                completed_at = datetime.now(timezone.utc)
                duration_ms = (completed_at - started_at).total_seconds() * 1000

                # Check for server errors (5xx) - retry these
                if response.status_code >= 500:
                    last_error = f"Server error: {response.status_code}"
                    if attempt < max_retries - 1:
                        backoff = BACKOFF_MULTIPLIER * (2**attempt)
                        await asyncio.sleep(backoff)
                        continue

                    return {
                        "status": "failed",
                        "skill": "http_call",
                        "url": url,
                        "method": method,
                        "http_status": response.status_code,
                        "error": "server_error",
                        "message": last_error,
                        "attempts": attempts,
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                        "duration_ms": round(duration_ms, 2),
                    }

                # Success
                return {
                    "status": "succeeded",
                    "skill": "http_call",
                    "url": url,
                    "method": method,
                    "http_status": response.status_code,
                    "response_body": response.text[:1000],  # Limit response size
                    "attempts": attempts,
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "duration_ms": round(duration_ms, 2),
                }

        except httpx.TimeoutException:
            last_error = f"Request timed out after {timeout}s"
        except httpx.ConnectError as e:
            last_error = f"Connection error: {str(e)[:200]}"
        except httpx.RequestError as e:
            last_error = f"Request error: {str(e)[:200]}"

        # Exponential backoff before retry
        if attempt < max_retries - 1:
            backoff = BACKOFF_MULTIPLIER * (2**attempt)
            await asyncio.sleep(backoff)

    # All retries exhausted
    completed_at = datetime.now(timezone.utc)
    duration_ms = (completed_at - started_at).total_seconds() * 1000

    return {
        "status": "failed",
        "skill": "http_call",
        "url": url,
        "method": method,
        "error": "max_retries_exceeded",
        "message": last_error or "Unknown error after all retries",
        "attempts": attempts,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "duration_ms": round(duration_ms, 2),
    }
