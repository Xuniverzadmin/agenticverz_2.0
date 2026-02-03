# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api|scheduler
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Integration (via session)
#   Writes: Integration (session.add, session.commit)
# Role: Health checking engine for customer LLM integrations
# Product: system-wide
# Callers: cus_integration_service.py, scheduled health checks
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Forbidden: session.commit(), session.rollback() — L5 DOES NOT COMMIT (L4 coordinator owns)
# Reference: PIN-470, docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
# NOTE: Renamed cus_health_service.py → cus_health_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
#       Reclassified L4→L5 - Per HOC topology, engines are L5 (business logic)

"""Customer Health Engine

PURPOSE:
    Provider reachability and credential validation for customer LLM integrations.
    Performs lightweight health checks without consuming significant quota.

RESPONSIBILITIES:
    - Test provider connectivity
    - Validate credentials are still valid
    - Measure response latency
    - Update health state in integrations

HEALTH STATES:
    - UNKNOWN: Never checked or no recent data
    - HEALTHY: Last check successful
    - DEGRADED: Slow or partial responses
    - UNHEALTHY: Check failed

CHECK STRATEGY:
    - OpenAI: GET /models endpoint (lightweight, no tokens)
    - Anthropic: POST /messages with max_tokens=1 (minimal cost)
    - Google: GET /models endpoint
    - Others: Provider-specific lightweight calls

RATE LIMITING:
    - Maximum one check per integration per minute
    - Batch checks spread over time
    - Failed integrations checked less frequently
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from sqlmodel import Session, select

from app.db import get_engine
from app.models.cus_models import CusHealthState, CusIntegration
from app.hoc.cus.hoc_spine.services.cus_credential_engine import CusCredentialService

logger = logging.getLogger(__name__)


class CusHealthService:
    """Service for health checking customer LLM integrations.

    Phase 4: Provider reachability and credential validation.
    """

    # Timeouts
    CONNECT_TIMEOUT = 5.0  # seconds
    READ_TIMEOUT = 10.0  # seconds

    # Thresholds
    DEGRADED_LATENCY_MS = 2000  # ms - above this is degraded
    UNHEALTHY_LATENCY_MS = 5000  # ms - above this is unhealthy

    # Rate limiting
    MIN_CHECK_INTERVAL_SECONDS = 60  # Don't check more than once per minute

    # Provider endpoints (for health checks)
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
            # Azure requires deployment-specific URL
            "method": "GET",
            "auth_header": "api-key",
            "auth_prefix": "",
        },
    }

    def __init__(self, credential_service: Optional[CusCredentialService] = None):
        """Initialize health service.

        Args:
            credential_service: Credential service for decrypting API keys.
                               If None, creates a new instance.
        """
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

        Args:
            tenant_id: Tenant for ownership verification
            integration_id: Integration to check
            force: If True, bypass rate limiting

        Returns:
            Health check result with:
                - health_state: Current state
                - message: Human-readable status
                - latency_ms: Response time (if successful)
                - checked_at: Timestamp
                - error: Error details (if failed)
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == UUID(integration_id),
                    CusIntegration.tenant_id == UUID(tenant_id),
                )
            ).first()

            if not integration:
                return {
                    "health_state": CusHealthState.UNKNOWN,
                    "message": "Integration not found",
                    "error": "not_found",
                    "checked_at": datetime.now(timezone.utc),
                }

            # Rate limiting check
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
            integration.health_state = result["health_state"]
            integration.health_checked_at = result["checked_at"]
            integration.health_message = result["message"]
            integration.updated_at = datetime.now(timezone.utc)

            session.add(integration)
            # NO COMMIT — L4 coordinator owns transaction boundary

            logger.info(
                f"Health check for integration {integration_id}: "
                f"{result['health_state'].value}"
            )

            return result

    async def _perform_health_check(
        self,
        integration: CusIntegration,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Perform the actual health check call.

        Args:
            integration: The integration to check
            tenant_id: Tenant ID for credential decryption

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
                "health_state": CusHealthState.UNHEALTHY,
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

        # Handle Azure special case (needs deployment URL from config)
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

        # Make the request
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

            # Evaluate response
            if response.status_code == 200:
                # Success - determine health based on latency
                if latency_ms <= self.DEGRADED_LATENCY_MS:
                    health_state = CusHealthState.HEALTHY
                    message = f"OK ({latency_ms}ms)"
                elif latency_ms <= self.UNHEALTHY_LATENCY_MS:
                    health_state = CusHealthState.DEGRADED
                    message = f"Slow response ({latency_ms}ms)"
                else:
                    health_state = CusHealthState.DEGRADED
                    message = f"Very slow response ({latency_ms}ms)"

                return {
                    "health_state": health_state,
                    "message": message,
                    "latency_ms": latency_ms,
                    "checked_at": datetime.now(timezone.utc),
                }

            elif response.status_code == 401:
                return {
                    "health_state": CusHealthState.UNHEALTHY,
                    "message": "Authentication failed - invalid credentials",
                    "latency_ms": latency_ms,
                    "error": "auth_failed",
                    "checked_at": datetime.now(timezone.utc),
                }

            elif response.status_code == 403:
                return {
                    "health_state": CusHealthState.UNHEALTHY,
                    "message": "Access denied - check API key permissions",
                    "latency_ms": latency_ms,
                    "error": "access_denied",
                    "checked_at": datetime.now(timezone.utc),
                }

            elif response.status_code == 429:
                return {
                    "health_state": CusHealthState.DEGRADED,
                    "message": "Rate limited by provider",
                    "latency_ms": latency_ms,
                    "error": "rate_limited",
                    "checked_at": datetime.now(timezone.utc),
                }

            else:
                return {
                    "health_state": CusHealthState.UNHEALTHY,
                    "message": f"Provider returned error: {response.status_code}",
                    "latency_ms": latency_ms,
                    "error": f"http_{response.status_code}",
                    "checked_at": datetime.now(timezone.utc),
                }

        except httpx.ConnectError as e:
            return {
                "health_state": CusHealthState.UNHEALTHY,
                "message": "Connection failed - provider unreachable",
                "error": str(e),
                "checked_at": datetime.now(timezone.utc),
            }

        except httpx.TimeoutException:
            return {
                "health_state": CusHealthState.UNHEALTHY,
                "message": "Request timed out",
                "error": "timeout",
                "checked_at": datetime.now(timezone.utc),
            }

        except Exception as e:
            logger.exception(f"Health check failed: {e}")
            return {
                "health_state": CusHealthState.UNHEALTHY,
                "message": f"Health check failed: {e}",
                "error": str(e),
                "checked_at": datetime.now(timezone.utc),
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

        Only checks integrations that:
        - Are enabled
        - Haven't been checked recently (beyond stale threshold)

        Args:
            tenant_id: Tenant ID
            stale_threshold_minutes: Only check if last check older than this

        Returns:
            List of health check results
        """
        engine = get_engine()
        results: List[Dict[str, Any]] = []

        with Session(engine) as session:
            # Find integrations needing checks
            stale_threshold = datetime.now(timezone.utc) - timedelta(
                minutes=stale_threshold_minutes
            )

            query = (
                select(CusIntegration)
                .where(
                    CusIntegration.tenant_id == UUID(tenant_id),
                    CusIntegration.status == "enabled",
                )
                .where(
                    (CusIntegration.health_checked_at.is_(None))
                    | (CusIntegration.health_checked_at < stale_threshold)
                )
            )

            integrations = list(session.exec(query).all())

        # Check each integration with small delays to avoid rate limits
        for integration in integrations:
            result = await self.check_health(
                tenant_id=tenant_id,
                integration_id=str(integration.id),
                force=True,
            )
            result["integration_id"] = str(integration.id)
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
        engine = get_engine()

        with Session(engine) as session:
            integrations = list(
                session.exec(
                    select(CusIntegration).where(
                        CusIntegration.tenant_id == UUID(tenant_id),
                    )
                ).all()
            )

            counts = {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
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

        Args:
            counts: Health state counts

        Returns:
            Overall health: healthy, degraded, unhealthy, or unknown
        """
        if counts["total"] == 0:
            return "unknown"

        if counts["unhealthy"] > 0:
            return "unhealthy"

        if counts["degraded"] > 0:
            return "degraded"

        if counts["unknown"] == counts["total"]:
            return "unknown"

        return "healthy"
