# Layer: L5 — HOC Spine (Services)
# Relocated: 2026-01-30 from hoc_spine/adapters/alert_delivery.py
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: engine call
#   Execution: async
# Role: HTTP delivery to Alertmanager
# Callers: alert_worker.py (L4 engine)
# Allowed Imports: httpx, logging
# Forbidden Imports: L1, L2, L4, L5, L6, sqlalchemy, sqlmodel
# Reference: Phase-2.5A Analytics Extraction
#
# GOVERNANCE NOTE:
# This adapter provides ONLY HTTP delivery functionality.
# NO business logic - only HTTP operations.
# NO database operations - persistence stays in driver.
# Business logic (retry decisions, status transitions) stays in L4 engine.

"""
Alert Delivery Adapter (L2)

Pure HTTP delivery to Alertmanager.
All business logic stays in L4 engine.
All database operations stay in L6 driver.

Operations:
- Send alert payload to Alertmanager
- Handle HTTP errors and timeouts
- Report delivery result

NO business logic:
- NO retry decisions (L4)
- NO status updates (L6)
- NO queue management (L6)

Reference: Phase-2.5A Analytics Extraction
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("nova.analytics.adapters.alert_delivery")


@dataclass
class DeliveryResult:
    """Result of alert delivery attempt."""

    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None


class AlertDeliveryAdapter:
    """
    Adapter for HTTP alert delivery.

    Pure HTTP operations - no business logic, no database.
    """

    def __init__(
        self,
        alertmanager_url: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ):
        """
        Initialize adapter with Alertmanager configuration.

        Args:
            alertmanager_url: Alertmanager API URL
            timeout_seconds: HTTP timeout
        """
        self.alertmanager_url = alertmanager_url
        self.timeout = timeout_seconds
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def send_alert(
        self,
        payload: List[Dict[str, Any]],
    ) -> DeliveryResult:
        """
        Send alert payload to Alertmanager.

        Args:
            payload: Alertmanager payload (list of alerts)

        Returns:
            DeliveryResult with success status and error details
        """
        if not self.alertmanager_url:
            logger.warning("Alertmanager URL not configured, treating as success")
            return DeliveryResult(success=True)

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.alertmanager_url}/api/v2/alerts",
                json=payload,
            )
            response.raise_for_status()

            return DeliveryResult(
                success=True,
                status_code=response.status_code,
            )

        except httpx.TimeoutException as e:
            error_msg = f"Timeout: {e}"
            logger.warning(f"Alert delivery timeout: {e}")
            return DeliveryResult(
                success=False,
                error_type="timeout",
                error_message=error_msg,
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            logger.warning(f"Alert delivery HTTP error: status={e.response.status_code}")
            return DeliveryResult(
                success=False,
                error_type=f"http_{e.response.status_code}",
                error_message=error_msg,
                status_code=e.response.status_code,
            )

        except Exception as e:
            error_msg = str(e)[:500]
            logger.error(f"Alert delivery error: {e}")
            return DeliveryResult(
                success=False,
                error_type="connection",
                error_message=error_msg,
            )


def get_alert_delivery_adapter(
    alertmanager_url: Optional[str] = None,
    timeout_seconds: float = 30.0,
) -> AlertDeliveryAdapter:
    """Factory function to get AlertDeliveryAdapter instance."""
    return AlertDeliveryAdapter(
        alertmanager_url=alertmanager_url,
        timeout_seconds=timeout_seconds,
    )


__all__ = [
    "AlertDeliveryAdapter",
    "DeliveryResult",
    "get_alert_delivery_adapter",
]
