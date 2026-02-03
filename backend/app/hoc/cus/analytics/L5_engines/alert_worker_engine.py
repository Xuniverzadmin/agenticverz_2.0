# Layer: L5 — Analytics (Engine)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: worker|scheduler
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: alert_queue (via L6 driver)
#   Writes: alert_queue (via L6 driver)
# Database:
#   Scope: analytics
#   Models: CostSimAlertQueueModel, CostSimCBIncidentModel (via driver)
# Role: Alert worker engine - orchestrates alert delivery using L6 driver + L5 service
# Callers: scheduler, workers
# Allowed Imports: L6 drivers, hoc_spine services
# Forbidden Imports: L1, L2, sqlalchemy (session managed by driver)
# Reference: PIN-520 Wiring Audit
# artifact_class: CODE

"""
Alert Worker Engine (L5)

Orchestrates alert delivery by wiring:
- AlertDriver (L6) — DB operations (fetch, update status)
- AlertDeliveryAdapter (L5 service) — HTTP delivery to Alertmanager

This engine owns the business logic:
- Batch processing with exponential backoff
- Retry decisions (max attempts, backoff calculation)
- Dead letter handling (mark as failed after max attempts)

The L6 driver handles pure DB access (with its own session context).
The L5 service handles pure HTTP delivery.
This engine coordinates the flow.

L5 Compliance (PIN-512):
- No session parameters — driver manages its own session via context manager
- No sqlalchemy imports — DB access via driver only

Usage:
    from app.hoc.cus.analytics.L5_engines.alert_worker_engine import (
        get_alert_worker,
        AlertWorkerEngine,
    )

    worker = get_alert_worker(alertmanager_url="http://alertmanager:9093")
    stats = await worker.process_batch(batch_size=10)

Reference: PIN-520 Wiring Audit
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.analytics.alert_worker")


class AlertWorkerEngine:
    """
    Alert Worker Engine (L5)

    Orchestrates alert queue processing using:
    - AlertDriver (L6) for DB operations (manages its own session)
    - AlertDeliveryAdapter (L5 service) for HTTP delivery

    Business logic owned here:
    - Exponential backoff calculation
    - Retry decision logic
    - Dead letter handling
    """

    def __init__(
        self,
        alertmanager_url: Optional[str] = None,
        max_backoff_seconds: int = 300,
        timeout_seconds: float = 30.0,
    ):
        """
        Initialize alert worker engine.

        Args:
            alertmanager_url: Alertmanager API URL
            max_backoff_seconds: Maximum backoff between retries (default 5 min)
            timeout_seconds: HTTP timeout for delivery
        """
        self.alertmanager_url = alertmanager_url
        self.max_backoff = max_backoff_seconds
        self.timeout = timeout_seconds
        self._adapter = None

    def _get_adapter(self):
        """Get AlertDeliveryAdapter instance (lazy, cached)."""
        if self._adapter is None:
            from app.hoc.cus.hoc_spine.services import get_alert_delivery_adapter

            self._adapter = get_alert_delivery_adapter(
                alertmanager_url=self.alertmanager_url,
                timeout_seconds=self.timeout,
            )
        return self._adapter

    async def close(self) -> None:
        """Close HTTP adapter."""
        if self._adapter is not None:
            await self._adapter.close()
            self._adapter = None

    def _calculate_backoff(self, attempts: int) -> int:
        """Calculate exponential backoff: 2^attempts seconds, capped."""
        return min(2**attempts, self.max_backoff)

    async def process_batch(
        self,
        batch_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Process a batch of pending alerts.

        The L6 driver manages its own session context internally.

        Args:
            batch_size: Number of alerts to process

        Returns:
            Dict with processed, sent, failed, retried counts
        """
        from app.hoc.cus.hoc_spine.drivers.alert_driver import AlertDriver

        adapter = self._get_adapter()
        now = datetime.now(timezone.utc)

        stats = {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "retried": 0,
        }

        # Driver manages its own session via context manager
        async with AlertDriver() as driver:
            # Fetch pending alerts via L6 driver
            alerts = await driver.fetch_pending_alerts(now=now, batch_size=batch_size)

            for alert in alerts:
                stats["processed"] += 1

                # Send via L5 adapter
                result = await adapter.send_alert(alert.payload)

                if result.success:
                    # Mark as sent via L6 driver
                    await driver.update_alert_sent(alert, sent_at=now)
                    stats["sent"] += 1

                    logger.info(
                        f"Alert sent: id={alert.id}, type={alert.alert_type}"
                    )

                    # Update incident if linked
                    if alert.incident_id:
                        await driver.mark_incident_alert_sent(
                            incident_id=alert.incident_id,
                            sent_at=now,
                        )
                else:
                    # Delivery failed
                    if alert.attempts + 1 >= alert.max_attempts:
                        # Max attempts reached - mark as failed
                        await driver.update_alert_failed(
                            alert,
                            last_attempt_at=now,
                            last_error=result.error_message,
                        )
                        stats["failed"] += 1

                        logger.error(
                            f"Alert failed (max attempts): id={alert.id}, "
                            f"attempts={alert.attempts + 1}, error={result.error_type}"
                        )
                    else:
                        # Schedule retry with exponential backoff
                        backoff = self._calculate_backoff(alert.attempts + 1)
                        next_attempt = now + timedelta(seconds=backoff)

                        await driver.update_alert_retry(
                            alert,
                            last_attempt_at=now,
                            next_attempt_at=next_attempt,
                            last_error=result.error_message,
                        )
                        stats["retried"] += 1

                        logger.warning(
                            f"Alert retry scheduled: id={alert.id}, "
                            f"attempt={alert.attempts + 1}, backoff={backoff}s"
                        )

        return stats

    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get alert queue statistics.

        Returns:
            Dict with pending, sent, failed counts and oldest_pending
        """
        from app.hoc.cus.hoc_spine.drivers.alert_driver import AlertDriver

        async with AlertDriver() as driver:
            return await driver.fetch_queue_stats()

    async def retry_failed_alerts(
        self,
        max_retries: int = 3,
    ) -> int:
        """
        Reset failed alerts to pending for retry.

        Args:
            max_retries: Additional retries to allow

        Returns:
            Number of alerts reset
        """
        from app.hoc.cus.hoc_spine.drivers.alert_driver import AlertDriver

        now = datetime.now(timezone.utc)

        async with AlertDriver() as driver:
            count = await driver.retry_failed_alerts(max_retries=max_retries, now=now)

        if count > 0:
            logger.info(f"Reset {count} failed alerts for retry")

        return count

    async def purge_old_alerts(
        self,
        days: int = 30,
        statuses: Optional[List[str]] = None,
    ) -> int:
        """
        Purge old alerts from queue.

        Args:
            days: Delete alerts older than this many days
            statuses: Only delete these statuses (default: sent, failed)

        Returns:
            Number of alerts deleted
        """
        from app.hoc.cus.hoc_spine.drivers.alert_driver import AlertDriver

        statuses = statuses or ["sent", "failed"]
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        async with AlertDriver() as driver:
            count = await driver.purge_old_alerts(cutoff=cutoff, statuses=statuses)

        if count > 0:
            logger.info(f"Purged {count} old alerts")

        return count


# =============================================================================
# Factory function
# =============================================================================

_worker_instance: Optional[AlertWorkerEngine] = None


def get_alert_worker(
    alertmanager_url: Optional[str] = None,
    max_backoff_seconds: int = 300,
    timeout_seconds: float = 30.0,
) -> AlertWorkerEngine:
    """
    Get alert worker engine instance.

    Args:
        alertmanager_url: Alertmanager API URL
        max_backoff_seconds: Maximum backoff between retries
        timeout_seconds: HTTP timeout for delivery

    Returns:
        AlertWorkerEngine instance
    """
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = AlertWorkerEngine(
            alertmanager_url=alertmanager_url,
            max_backoff_seconds=max_backoff_seconds,
            timeout_seconds=timeout_seconds,
        )
    return _worker_instance


__all__ = [
    "AlertWorkerEngine",
    "get_alert_worker",
]
