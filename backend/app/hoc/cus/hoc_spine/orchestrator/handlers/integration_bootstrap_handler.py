# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — integration subsystem bootstrap + notification dispatch
# Callers: App startup (lifespan), coordinators (alert/incident/policy)
# Allowed Imports: hoc_spine, hoc.cus.integrations (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 1D Wiring
# artifact_class: CODE

"""
Integration Bootstrap Handler (PIN-513 Batch 1D Wiring)

L4 handler that owns integration subsystem initialization and
notification dispatch authority.

Wires previously orphaned symbols:

From integrations/L5_notifications/engines/channel_engine.py:
- get_notify_service()        → singleton accessor
- get_channel_config()        → channel config read
- check_channel_health()      → health check
- send_notification()         → notification dispatch

From integrations/L6_drivers/worker_registry_driver.py:
- get_worker_registry_service() → already wired via IntegrationsWorkersHandler

Note on bridges_engine (create_bridges/register_all_bridges):
  These live in legacy app/integrations/bridges.py, NOT in HOC.
  The HOC file cost_bridges_engine.py is a different component (cost loop).
  Bridge bootstrap requires legacy-to-HOC migration first (separate PIN).

Note on external_response_driver:
  Lives in hoc/int/ (INTERNAL audience), not hoc/cus/.
  Out of scope for this handler (hoc/cus/* scope).

Flow:
  App startup
    → IntegrationBootstrapHandler.initialize()
        → get_notify_service() [warm singleton]

  Alert/Incident/Policy coordinator
    → IntegrationBootstrapHandler.send_notification(...)
        → send_notification(tenant_id, event_type, payload)

  Ops dashboard
    → IntegrationBootstrapHandler.check_health(tenant_id)
        → check_channel_health(tenant_id)
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.hoc_spine.handlers.integration_bootstrap")


class IntegrationBootstrapHandler:
    """L4 handler: integration subsystem bootstrap and notification dispatch.

    Owns initialization authority and notification routing.
    L5 channel engine provides business logic.
    """

    async def initialize(self) -> Dict[str, Any]:
        """Initialize integration subsystem — called on app startup.

        Warms the notification service singleton so first notification
        doesn't incur cold-start latency.

        Returns:
            Dict with initialization status
        """
        from app.hoc.cus.integrations.L5_notifications.engines.channel_engine import (
            get_notify_service,
        )

        service = get_notify_service()

        logger.info(
            "integration_bootstrap_initialized",
            extra={"service_type": type(service).__name__},
        )

        return {"initialized": True, "service": type(service).__name__}

    async def send_notification(
        self,
        tenant_id: str,
        event_type: Any,
        payload: Dict[str, Any],
        channels: Optional[List[Any]] = None,
    ) -> List[Any]:
        """Send notification via enabled channels.

        Args:
            tenant_id: Tenant identifier
            event_type: NotifyEventType enum value
            payload: Notification payload
            channels: Optional specific channels to use

        Returns:
            List of NotifyDeliveryResult
        """
        from app.hoc.cus.integrations.L5_notifications.engines.channel_engine import (
            send_notification,
        )

        results = await send_notification(
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload,
            channels=channels,
        )

        logger.info(
            "integration_notification_sent",
            extra={
                "tenant_id": tenant_id,
                "event_type": str(event_type),
                "channels_attempted": len(results),
                "channels_succeeded": sum(
                    1 for r in results if r.success
                ),
            },
        )

        return results

    async def check_health(
        self,
        tenant_id: str,
    ) -> Dict[Any, Dict[str, Any]]:
        """Check health of all notification channels for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict mapping NotifyChannel → health status dict
        """
        from app.hoc.cus.integrations.L5_notifications.engines.channel_engine import (
            check_channel_health,
        )

        return await check_channel_health(tenant_id=tenant_id)

    def get_channel_config(
        self,
        tenant_id: str,
        channel: Any,
    ) -> Any:
        """Get configuration for a specific notification channel.

        Args:
            tenant_id: Tenant identifier
            channel: NotifyChannel enum value

        Returns:
            NotifyChannelConfig or None
        """
        from app.hoc.cus.integrations.L5_notifications.engines.channel_engine import (
            get_channel_config,
        )

        return get_channel_config(tenant_id=tenant_id, channel=channel)
