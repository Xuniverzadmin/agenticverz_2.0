# HTTP Call Skill
# Pluggable HTTP skill with retry logic and external call control

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Type

import httpx
from pydantic import BaseModel

from ..schemas.skill import HttpCallInput, HttpCallOutput
from .registry import skill

logger = logging.getLogger("nova.skills.http_call")


class HttpCallConfig(BaseModel):
    """Configuration schema for http_call skill."""

    allow_external: bool = True
    timeout: float = 30.0
    max_retries: int = 3


@skill(
    "http_call",
    input_schema=HttpCallInput,
    output_schema=HttpCallOutput,
    tags=["network", "http", "api"],
    default_config={"allow_external": True, "timeout": 30.0, "max_retries": 3},
)
class HttpCallSkill:
    """HTTP call skill with configurable behavior.

    Features:
    - Configurable timeout and retries
    - Exponential backoff
    - External call control (can stub non-local URLs)
    - Structured result format with side effects tracking
    """

    VERSION = "0.2.0"
    DESCRIPTION = "Make HTTP requests to external APIs with retry support"

    # Default configuration
    DEFAULT_TIMEOUT = 5.0
    DEFAULT_MAX_RETRIES = 3
    BACKOFF_MULTIPLIER = 0.5

    def __init__(
        self, *, allow_external: bool = True, timeout: float = DEFAULT_TIMEOUT, max_retries: int = DEFAULT_MAX_RETRIES
    ):
        """Initialize HTTP skill.

        Args:
            allow_external: If False, stub non-local URLs
            timeout: Default request timeout
            max_retries: Default max retry attempts
        """
        self.allow_external = allow_external
        self.timeout = timeout
        self.max_retries = max_retries

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request.

        Args:
            params: Dict with url, method, body, headers, timeout, max_retries

        Returns:
            Structured result with status, response, duration, side_effects
        """
        url = params.get("url", "https://api.github.com/zen")
        method = params.get("method", "GET").upper()
        body = params.get("body")
        headers = params.get("headers", {})
        timeout = params.get("timeout", self.timeout)
        max_retries = params.get("max_retries", self.max_retries)

        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        logger.info("skill_execution_start", extra={"skill": "http_call", "url": url, "method": method})

        # Check if external calls are allowed (contract: url_behavior)
        if not self.allow_external:
            duration = time.time() - start_time

            if self._is_local_url(url):
                # Contract: local_urls.when_allow_external_false = FORBIDDEN
                # Local URLs forbidden when in stub mode to ensure determinism
                logger.info(
                    "skill_execution_forbidden",
                    extra={"skill": "http_call", "url": url, "reason": "local_url_forbidden_in_stub_mode"},
                )
                return {
                    "skill": "http_call",
                    "skill_version": self.VERSION,
                    "result": {
                        "status": "forbidden",
                        "code": 403,
                        "body": {
                            "error": "LOCAL_URL_FORBIDDEN",
                            "message": "Local URLs are forbidden when external calls disabled",
                        },
                    },
                    "duration": duration,
                    "side_effects": {},
                }
            else:
                # Contract: external_urls.when_allow_external_false = STUBBED
                logger.info(
                    "skill_execution_stubbed",
                    extra={"skill": "http_call", "url": url, "reason": "external_calls_disabled"},
                )
                return {
                    "skill": "http_call",
                    "skill_version": self.VERSION,
                    "result": {
                        "status": "stubbed",
                        "code": 501,
                        "body": {"note": "External calls disabled in skill configuration"},
                    },
                    "duration": duration,
                    "side_effects": {},
                }

        # Execute with retries
        attempts = 0
        last_error = None

        for attempt in range(max_retries):
            attempts = attempt + 1

            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    if method == "GET":
                        response = await client.get(url, headers=headers)
                    elif method == "POST":
                        response = await client.post(url, json=body, headers=headers)
                    elif method == "PUT":
                        response = await client.put(url, json=body, headers=headers)
                    elif method == "DELETE":
                        response = await client.delete(url, headers=headers)
                    else:
                        response = await client.request(method, url, json=body, headers=headers)

                    duration = time.time() - start_time
                    completed_at = datetime.now(timezone.utc)

                    # Check for server errors (5xx) - retry these
                    if response.status_code >= 500:
                        last_error = f"Server error: {response.status_code}"
                        if attempt < max_retries - 1:
                            backoff = self.BACKOFF_MULTIPLIER * (2**attempt)
                            await asyncio.sleep(backoff)
                            continue

                    # Success or client error (don't retry 4xx)
                    status = "ok" if response.status_code < 400 else "error"

                    logger.info(
                        "skill_execution_end",
                        extra={
                            "skill": "http_call",
                            "url": url,
                            "status": status,
                            "http_status": response.status_code,
                            "duration": round(duration, 3),
                            "attempts": attempts,
                        },
                    )

                    return {
                        "skill": "http_call",
                        "skill_version": self.VERSION,
                        "result": {
                            "status": status,
                            "code": response.status_code,
                            "body": response.text[:1000],  # Limit size
                            "attempts": attempts,
                        },
                        "duration": round(duration, 3),
                        "side_effects": {},
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                    }

            except httpx.TimeoutException:
                last_error = f"Request timed out after {timeout}s"
            except httpx.ConnectError as e:
                last_error = f"Connection error: {str(e)[:200]}"
            except httpx.RequestError as e:
                last_error = f"Request error: {str(e)[:200]}"

            # Exponential backoff before retry
            if attempt < max_retries - 1:
                backoff = self.BACKOFF_MULTIPLIER * (2**attempt)
                await asyncio.sleep(backoff)

        # All retries exhausted
        duration = time.time() - start_time
        logger.warning(
            "skill_execution_failed",
            extra={"skill": "http_call", "url": url, "error": last_error, "attempts": attempts},
        )

        return {
            "skill": "http_call",
            "skill_version": self.VERSION,
            "result": {
                "status": "error",
                "error": "max_retries_exceeded",
                "message": last_error or "Unknown error",
                "attempts": attempts,
            },
            "duration": round(duration, 3),
            "side_effects": {},
        }

    def _is_local_url(self, url: str) -> bool:
        """Check if URL is local/safe for testing."""
        local_prefixes = [
            "http://127.0.0.1",
            "http://localhost",
            "https://127.0.0.1",
            "https://localhost",
            "https://example.local",
            "http://example.local",
        ]
        return any(url.startswith(prefix) for prefix in local_prefixes)

    @classmethod
    def get_input_schema(cls) -> Type[BaseModel]:
        """Return input schema for validation."""
        return HttpCallInput

    @classmethod
    def get_output_schema(cls) -> Type[BaseModel]:
        """Return output schema for validation."""
        return HttpCallOutput


# Registration happens via @skill decorator above
