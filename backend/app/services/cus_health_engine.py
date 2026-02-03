# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api, scheduler
#   Execution: async
# Role: Health checking engine for customer LLM integrations
# Callers: cus_integration API, scheduled health checks
# Allowed Imports: L6 drivers (via injection)
# Forbidden Imports: sqlalchemy, sqlmodel, app.models
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Customer Health Engine

L4 engine for customer integration health decisions.

Decides: Health state interpretation, latency thresholds, rate limiting
Delegates: Data access to CusHealthDriver, HTTP calls to httpx

HEALTH STATES:
    - UNKNOWN: Never checked or no recent data
    - HEALTHY: Last check successful
    - DEGRADED: Slow or partial responses
    - FAILING: Check failed

CHECK STRATEGY:
    - OpenAI: GET /models endpoint (lightweight, no tokens)
    - Anthropic: POST /messages with max_tokens=1 (minimal cost)
    - Google: GET /models endpoint
    - Others: Provider-specific lightweight calls
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import httpx

from app.models.cus_models import CusHealthState
from app.services.cus_credential_engine import CusCredentialService
from app.services.cus_health_driver import (
    CusHealthDriver,
    IntegrationHealthRow,
    get_cus_health_driver,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class CusHealthEngine:
    """L4 engine for customer integration health decisions.

    Decides: Health state based on latency, HTTP status, rate limiting
    Delegates: Data access to CusHealthDriver
    """

    # Timeouts (decision: what counts as slow)
    CONNECT_TIMEOUT = 5.0  # seconds
    READ_TIMEOUT = 10.0  # seconds

    # Latency thresholds (decision: when to degrade)
    DEGRADED_LATENCY_MS = 2000  # ms - above this is degraded
    UNHEALTHY_LATENCY_MS = 5000  # ms - above this is unhealthy

    # Rate limiting (decision: how often to check)
    MIN_CHECK_INTERVAL_SECONDS = 60  # Don't check more than once per minute

    # Provider health endpoints (configuration, not logic)
    PROVIDER_HEALTH_ENDPOINTS = {
        "openai": {
            "url": "https://api.openai.com/v1/models",
            "method": "GET",
            "auth_header": "Authorization",
            "auth_prefix": "Bearer ",
        },
        "anthropic": {
            "url": "https://api.anthropic.com/v1/messages",
            "method": "POST",
            "auth_header": "x-api-key",
            "auth_prefix": "",
            "body": {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            },
            "extra_headers": {
                "anthropic-version": "2023-06-01",
            },
        },
        "google": {
            "url": "https://generativelanguage.googleapis.com/v1beta/models",
            "method": "GET",
            "auth_param": "key",
        },
        "azure": {
            "method": "GET",
            "auth_header": "api-key",
            "auth_prefix": "",
        },
    }

    def __init__(
        self,
        driver: CusHealthDriver,
        credential_service: Optional[CusCredentialService] = None,
    ):
        """Initialize engine with driver.

        Args:
            driver: CusHealthDriver instance for data access
            credential_service: Credential service for decrypting API keys
        """
        self._driver = driver
        self._credential_service = credential_service or CusCredentialService()

    # =========================================================================
    # SINGLE INTEGRATION CHECK
    # =========================================================================

    async def check_health(
        self,
        tenant_id: str,
        integration_id: str,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Check health of a single integration.

        DECISION LOGIC:
        1. Rate limiting - skip if checked recently
        2. Perform HTTP health check
        3. Interpret response (latency, status code)
        4. Update state in database

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration to check
            force: If True, bypass rate limiting

        Returns:
            Health check result dict
        """
        integration = self._driver.fetch_integration(tenant_id, integration_id)

        if not integration:
            return {
                "health_state": CusHealthState.UNKNOWN,
                "message": "Integration not found",
                "error": "not_found",
                "checked_at": datetime.now(timezone.utc),
            }

        # DECISION: Rate limiting check
        if not force and integration.health_checked_at:
            elapsed = datetime.now(timezone.utc) - integration.health_checked_at
            if elapsed.total_seconds() < self.MIN_CHECK_INTERVAL_SECONDS:
                return {
                    "health_state": integration.health_state,
                    "message": "Rate limited - using cached result",
                    "latency_ms": None,
                    "checked_at": integration.health_checked_at,
                    "cached": True,
                }

        # Perform the health check
        result = await self._perform_health_check(
            integration=integration,
            tenant_id=tenant_id,
        )

        # Update integration health state
        self._driver.update_health_state(
            integration_id=integration_id,
            health_state=result["health_state"],
            health_message=result["message"],
            health_checked_at=result["checked_at"],
        )

        logger.info(
            f"Health check for integration {integration_id}: "
            f"{result['health_state'].value}"
        )

        return result

    async def _perform_health_check(
        self,
        integration: IntegrationHealthRow,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Perform the actual health check call.

        DECISION LOGIC:
        - Map HTTP status codes to health states
        - Apply latency thresholds for DEGRADED state
        - Handle errors gracefully

        Args:
            integration: Integration data
            tenant_id: Tenant ID for credential resolution

        Returns:
            Health check result dict
        """
        provider = integration.provider_type.lower()
        endpoint_config = self.PROVIDER_HEALTH_ENDPOINTS.get(provider)

        if not endpoint_config:
            return {
                "health_state": CusHealthState.UNKNOWN,
                "message": f"No health check configured for provider: {provider}",
                "checked_at": datetime.now(timezone.utc),
            }

        # Resolve credential
        try:
            api_key = self._credential_service.resolve_credential(
                tenant_id=tenant_id,
                credential_ref=integration.credential_ref,
            )
        except Exception as e:
            logger.warning(f"Failed to resolve credential: {e}")
            return {
                "health_state": CusHealthState.FAILING,
                "message": "Credential resolution failed",
                "error": str(e),
                "checked_at": datetime.now(timezone.utc),
            }

        # Build request
        url = endpoint_config.get("url", "")
        method = endpoint_config.get("method", "GET")
        headers: Dict[str, str] = {}
        params: Dict[str, str] = {}
        body: Optional[Dict[str, Any]] = None

        # Handle Azure special case
        if provider == "azure":
            base_url = integration.config.get("azure_endpoint", "")
            deployment = integration.config.get("deployment_name", "")
            api_version = integration.config.get("api_version", "2024-02-15-preview")
            if not base_url or not deployment:
                return {
                    "health_state": CusHealthState.UNKNOWN,
                    "message": "Azure endpoint or deployment not configured",
                    "checked_at": datetime.now(timezone.utc),
                }
            url = f"{base_url}/openai/deployments/{deployment}/chat/completions"
            params["api-version"] = api_version

        # Auth header
        if "auth_header" in endpoint_config:
            prefix = endpoint_config.get("auth_prefix", "")
            headers[endpoint_config["auth_header"]] = f"{prefix}{api_key}"

        # Auth param (for Google)
        if "auth_param" in endpoint_config:
            params[endpoint_config["auth_param"]] = api_key

        # Extra headers
        if "extra_headers" in endpoint_config:
            headers.update(endpoint_config["extra_headers"])

        # Request body
        if "body" in endpoint_config:
            body = endpoint_config["body"]

        # Make the request and interpret response
        return await self._execute_health_request(url, method, headers, params, body)

    async def _execute_health_request(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        params: Dict[str, str],
        body: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute health check HTTP request.

        DECISION LOGIC:
        - 200 + fast → HEALTHY
        - 200 + slow → DEGRADED
        - 401 → UNHEALTHY (auth failed)
        - 403 → UNHEALTHY (access denied)
        - 429 → DEGRADED (rate limited)
        - Other → UNHEALTHY

        Args:
            url: Request URL
            method: HTTP method
            headers: Request headers
            params: Query params
            body: Request body (for POST)

        Returns:
            Health check result dict
        """
        start_time = datetime.now(timezone.utc)

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.CONNECT_TIMEOUT,
                    read=self.READ_TIMEOUT,
                    write=self.READ_TIMEOUT,
                    pool=self.READ_TIMEOUT,
                )
            ) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                else:
                    response = await client.post(
                        url,
                        headers=headers,
                        params=params,
                        json=body,
                    )

            latency_ms = int(
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )

            # DECISION: Interpret response
            return self._interpret_response(response.status_code, latency_ms)

        except httpx.ConnectError as e:
            return {
                "health_state": CusHealthState.FAILING,
                "message": "Connection failed - provider unreachable",
                "error": str(e),
                "checked_at": datetime.now(timezone.utc),
            }

        except httpx.TimeoutException:
            return {
                "health_state": CusHealthState.FAILING,
                "message": "Request timed out",
                "error": "timeout",
                "checked_at": datetime.now(timezone.utc),
            }

        except Exception as e:
            logger.exception(f"Health check failed: {e}")
            return {
                "health_state": CusHealthState.FAILING,
                "message": f"Health check failed: {e}",
                "error": str(e),
                "checked_at": datetime.now(timezone.utc),
            }

    def _interpret_response(
        self, status_code: int, latency_ms: int
    ) -> Dict[str, Any]:
        """Interpret HTTP response into health state.

        DECISION LOGIC (thresholds):
        - 200: Check latency thresholds
        - 401: Auth failed
        - 403: Access denied
        - 429: Rate limited (degraded, not failed)
        - Other: Error

        Args:
            status_code: HTTP status code
            latency_ms: Response latency in milliseconds

        Returns:
            Health check result dict
        """
        checked_at = datetime.now(timezone.utc)

        if status_code == 200:
            # DECISION: Apply latency thresholds
            if latency_ms <= self.DEGRADED_LATENCY_MS:
                return {
                    "health_state": CusHealthState.HEALTHY,
                    "message": f"OK ({latency_ms}ms)",
                    "latency_ms": latency_ms,
                    "checked_at": checked_at,
                }
            elif latency_ms <= self.UNHEALTHY_LATENCY_MS:
                return {
                    "health_state": CusHealthState.DEGRADED,
                    "message": f"Slow response ({latency_ms}ms)",
                    "latency_ms": latency_ms,
                    "checked_at": checked_at,
                }
            else:
                return {
                    "health_state": CusHealthState.DEGRADED,
                    "message": f"Very slow response ({latency_ms}ms)",
                    "latency_ms": latency_ms,
                    "checked_at": checked_at,
                }

        elif status_code == 401:
            return {
                "health_state": CusHealthState.FAILING,
                "message": "Authentication failed - invalid credentials",
                "latency_ms": latency_ms,
                "error": "auth_failed",
                "checked_at": checked_at,
            }

        elif status_code == 403:
            return {
                "health_state": CusHealthState.FAILING,
                "message": "Access denied - check API key permissions",
                "latency_ms": latency_ms,
                "error": "access_denied",
                "checked_at": checked_at,
            }

        elif status_code == 429:
            return {
                "health_state": CusHealthState.DEGRADED,
                "message": "Rate limited by provider",
                "latency_ms": latency_ms,
                "error": "rate_limited",
                "checked_at": checked_at,
            }

        else:
            return {
                "health_state": CusHealthState.FAILING,
                "message": f"Provider returned error: {status_code}",
                "latency_ms": latency_ms,
                "error": f"http_{status_code}",
                "checked_at": checked_at,
            }

    # =========================================================================
    # BATCH CHECKS
    # =========================================================================

    async def check_all_integrations(
        self,
        tenant_id: str,
        stale_threshold_minutes: int = 5,
    ) -> List[Dict[str, Any]]:
        """Check health of all integrations that need checking.

        Args:
            tenant_id: Tenant ID
            stale_threshold_minutes: Only check if last check older than this

        Returns:
            List of health check results
        """
        integrations = self._driver.fetch_stale_integrations(
            tenant_id, stale_threshold_minutes
        )
        results: List[Dict[str, Any]] = []

        # Check each integration with small delays
        for integration in integrations:
            result = await self.check_health(
                tenant_id=tenant_id,
                integration_id=integration.id,
                force=True,
            )
            result["integration_id"] = integration.id
            result["integration_name"] = integration.name
            results.append(result)

            # Small delay between checks
            await asyncio.sleep(0.5)

        logger.info(
            f"Batch health check for tenant {tenant_id}: "
            f"checked {len(results)} integrations"
        )

        return results

    # =========================================================================
    # HEALTH SUMMARY
    # =========================================================================

    async def get_health_summary(
        self,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Get health summary for all integrations.

        Args:
            tenant_id: Tenant ID

        Returns:
            Summary with counts by health state
        """
        integrations = self._driver.fetch_all_integrations(tenant_id)

        counts = {
            "healthy": 0,
            "degraded": 0,
            "failing": 0,
            "unknown": 0,
            "total": len(integrations),
        }

        stale_count = 0
        stale_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)

        for integration in integrations:
            state = integration.health_state.value.lower()
            if state in counts:
                counts[state] += 1

            if (
                integration.health_checked_at is None
                or integration.health_checked_at < stale_threshold
            ):
                stale_count += 1

        return {
            "counts": counts,
            "stale_count": stale_count,
            "overall_health": self._calculate_overall_health(counts),
            "checked_at": datetime.now(timezone.utc),
        }

    def _calculate_overall_health(self, counts: Dict[str, int]) -> str:
        """Calculate overall health status from counts.

        DECISION LOGIC:
        - Any failing → failing
        - Any degraded → degraded
        - All unknown → unknown
        - Otherwise → healthy

        Args:
            counts: Health state counts

        Returns:
            Overall health string
        """
        if counts["total"] == 0:
            return "unknown"

        if counts["failing"] > 0:
            return "failing"

        if counts["degraded"] > 0:
            return "degraded"

        if counts["unknown"] == counts["total"]:
            return "unknown"

        return "healthy"


# Factory function
def get_cus_health_engine() -> CusHealthEngine:
    """Get engine instance with default driver.

    Returns:
        CusHealthEngine instance
    """
    driver = get_cus_health_driver()
    return CusHealthEngine(driver=driver)


# Backward compatibility alias
CusHealthService = CusHealthEngine
get_cus_health_service = get_cus_health_engine
