# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: background worker
#   Execution: async
# Role: Alert queue processing decisions and orchestration
# Callers: background task, cron
# Allowed Imports: L5, L6 (drivers), L3 (adapters)
# Forbidden Imports: L1, L2, sqlalchemy direct queries, httpx
# Reference: Phase-2.5A Analytics Extraction
#
# GOVERNANCE NOTE:
# This L4 engine handles DECISIONS only:
# - Retry eligibility
# - Backoff calculation
# - Status transitions
#
# PERSISTENCE (L6 Driver): alert_driver.py
# DELIVERY (L3 Adapter): alert_delivery.py
#
# ============================================================================
# AUTHORITY PARTITION — ALERT WORKER
# ============================================================================
# Method                  | Bucket      | Notes
# ----------------------- | ----------- | --------------------------------
# process_batch           | DECISION    | Orchestrates retry logic
# _send_alert             | DELIVERY    | → Delegated to adapter
# _mark_incident_alert_sent | PERSISTENCE | → Delegated to driver
# run_continuous          | DECISION    | Orchestrates continuous loop
# get_queue_stats         | PERSISTENCE | → Delegated to driver
# enqueue_alert           | PERSISTENCE | → Delegated to driver
# retry_failed_alerts     | PERSISTENCE | → Delegated to driver
# purge_old_alerts        | PERSISTENCE | → Delegated to driver
# ============================================================================

"""
CostSim Alert Worker - Reliable Alert Delivery (L4 Engine)

Background worker for reliable alert delivery.

Phase-2.5A Extraction:
- PERSISTENCE: Delegated to AlertDriver (L6)
- DELIVERY: Delegated to AlertDeliveryAdapter (L3)
- DECISIONS: Retained in this engine (L4)

This worker processes the alert queue, sending alerts to Alertmanager
with exponential backoff retry logic. It ensures alerts are delivered
even if Alertmanager is temporarily unavailable.

Features:
- Exponential backoff (1s, 2s, 4s, 8s, ... up to max_backoff)
- Maximum retry attempts (configurable, default 10)
- Dead letter handling (marks alerts as failed after max attempts)
- Leader election (only one worker processes at a time)
- Batch processing for efficiency

Usage:
    from app.costsim.alert_worker import AlertWorker, run_alert_worker

    # Run continuously
    await run_alert_worker()

    # Or run once (e.g., from cron)
    worker = AlertWorker()
    processed = await worker.process_batch(batch_size=10)
"""

from __future__ import annotations

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# Sends alerts to Alertmanager - external HTTP calls are non-deterministic
# Cannot safely retry without idempotency key (which Alertmanager may not support)
FEATURE_INTENT = FeatureIntent.EXTERNAL_SIDE_EFFECT
RETRY_POLICY = RetryPolicy.NEVER

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.costsim.config import get_config
from app.costsim.leader import (
    LOCK_ALERT_WORKER,
    leader_election,
)
from app.costsim.metrics import get_metrics
from app.db_async import AsyncSessionLocal, async_session_context

logger = logging.getLogger("nova.costsim.alert_worker")


class AlertWorker:
    """
    Background worker for processing alert queue.

    Phase-2.5A Extraction:
    - PERSISTENCE: Delegated to AlertDriver (L6)
    - DELIVERY: Delegated to AlertDeliveryAdapter (L3)
    - DECISIONS: Retained here (L4) - retry eligibility, backoff, status transitions
    """

    def __init__(
        self,
        alertmanager_url: Optional[str] = None,
        max_backoff_seconds: int = 300,  # 5 minutes
        batch_size: int = 10,
        process_interval_seconds: float = 5.0,
    ):
        """
        Initialize alert worker.

        Args:
            alertmanager_url: Alertmanager API URL (from config if not provided)
            max_backoff_seconds: Maximum backoff between retries
            batch_size: Number of alerts to process per batch
            process_interval_seconds: Interval between batch processing
        """
        config = get_config()
        self.alertmanager_url = alertmanager_url or config.alertmanager_url
        self.max_backoff = max_backoff_seconds
        self.batch_size = batch_size
        self.process_interval = process_interval_seconds
        self.timeout = config.alertmanager_timeout_seconds

        # Phase-2.5A: Adapter for HTTP delivery
        from app.hoc.cus.analytics.adapters.alert_delivery import (
            get_alert_delivery_adapter,
        )

        self._adapter = get_alert_delivery_adapter(
            alertmanager_url=self.alertmanager_url,
            timeout_seconds=self.timeout,
        )

    async def close(self) -> None:
        """Close adapter resources."""
        await self._adapter.close()

    async def process_batch(self, batch_size: Optional[int] = None) -> int:
        """
        Process a batch of pending alerts.

        Phase-2.5A Extraction:
        - Fetch alerts: Delegated to driver
        - Send alerts: Delegated to adapter
        - Update status: Delegated to driver
        - Decisions: Retained here (retry eligibility, backoff calculation)

        Args:
            batch_size: Override default batch size

        Returns:
            Number of alerts processed
        """
        # Phase-2.5A: Import driver at method scope to avoid circular imports
        from app.hoc.cus.analytics.drivers.alert_driver import (
            get_alert_driver,
        )

        batch_size = batch_size or self.batch_size
        processed = 0

        async with async_session_context() as session:
            driver = get_alert_driver(session)
            now = datetime.now(timezone.utc)

            # Phase-2.5A: Delegate fetch to driver
            alerts = await driver.fetch_pending_alerts(now=now, batch_size=batch_size)

            # Update queue depth metric
            metrics = get_metrics()
            metrics.set_alert_queue_depth(len(alerts))

            for alert in alerts:
                # Phase-2.5A: Delegate delivery to adapter
                result = await self._adapter.send_alert(alert.payload)
                processed += 1

                if result.success:
                    # Phase-2.5A: Delegate status update to driver
                    sent_at = datetime.now(timezone.utc)
                    await driver.update_alert_sent(alert, sent_at)
                    logger.info(f"Alert sent: id={alert.id}, type={alert.alert_type}")

                    # Update incident if linked
                    if alert.incident_id:
                        await driver.mark_incident_alert_sent(alert.incident_id, sent_at)
                else:
                    # L4 DECISION: Check if max attempts reached
                    current_attempts = alert.attempts + 1
                    last_attempt_at = datetime.now(timezone.utc)

                    if current_attempts >= alert.max_attempts:
                        # Phase-2.5A: Delegate failed status to driver
                        await driver.update_alert_failed(
                            alert, last_attempt_at, result.error_message
                        )
                        logger.error(
                            f"Alert failed (max attempts): id={alert.id}, attempts={current_attempts}"
                        )
                    else:
                        # L4 DECISION: Calculate exponential backoff
                        backoff = min(2**current_attempts, self.max_backoff)
                        next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=backoff)

                        # Phase-2.5A: Delegate retry scheduling to driver
                        await driver.update_alert_retry(
                            alert, last_attempt_at, next_attempt_at, result.error_message
                        )
                        logger.warning(
                            f"Alert retry scheduled: id={alert.id}, attempt={current_attempts}, backoff={backoff}s"
                        )

                    # Record metric for failure
                    if result.error_type:
                        get_metrics().record_alert_send_failure(
                            alert_type=alert.alert_type or "unknown",
                            error_type=result.error_type,
                        )

            await driver.commit()

        return processed

    async def run_continuous(
        self,
        use_leader_election: bool = True,
    ) -> None:
        """
        Run worker continuously.

        Args:
            use_leader_election: Only run if we hold the leader lock
        """
        logger.info("Starting alert worker continuous mode")

        try:
            while True:
                try:
                    if use_leader_election:
                        async with leader_election(LOCK_ALERT_WORKER) as is_leader:
                            if is_leader:
                                await self.process_batch()
                            else:
                                logger.debug("Not the leader, skipping batch")
                    else:
                        await self.process_batch()

                except Exception as e:
                    logger.error(f"Alert worker batch error: {e}")

                await asyncio.sleep(self.process_interval)

        finally:
            await self.close()

    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get alert queue statistics.

        Phase-2.5A: Delegated to driver (L6).

        Returns:
            Dictionary with queue stats
        """
        from app.hoc.cus.analytics.drivers.alert_driver import (
            get_alert_driver,
        )

        async with async_session_context() as session:
            driver = get_alert_driver(session)
            stats = await driver.fetch_queue_stats()

            return {
                "pending": stats["pending"],
                "sent": stats["sent"],
                "failed": stats["failed"],
                "oldest_pending": stats["oldest_pending"].isoformat() if stats["oldest_pending"] else None,
            }


async def enqueue_alert(
    payload: List[Dict[str, Any]],
    alert_type: str,
    circuit_breaker_name: Optional[str] = None,
    incident_id: Optional[str] = None,
    session: Optional[AsyncSession] = None,
) -> int:
    """
    Enqueue an alert for delivery.

    Phase-2.5A: Delegated to driver (L6).

    Args:
        payload: Alertmanager payload
        alert_type: Type of alert (disable, enable, canary_fail)
        circuit_breaker_name: Associated circuit breaker
        incident_id: Associated incident
        session: Optional async session

    Returns:
        ID of created queue entry
    """
    from app.hoc.cus.analytics.drivers.alert_driver import (
        get_alert_driver,
    )

    own_session = session is None

    if own_session:
        session = AsyncSessionLocal()

    try:
        assert session is not None
        driver = get_alert_driver(session)
        alert = await driver.insert_alert(
            payload=payload,
            alert_type=alert_type,
            circuit_breaker_name=circuit_breaker_name,
            incident_id=incident_id,
        )
        await driver.commit()

        logger.debug(f"Alert enqueued: id={alert.id}, type={alert_type}")
        return alert.id

    except Exception as e:
        logger.error(f"Failed to enqueue alert: {e}")
        if own_session:
            assert session is not None
            await session.rollback()
        raise

    finally:
        if own_session:
            assert session is not None
            await session.close()


async def retry_failed_alerts(
    max_retries: int = 3,
) -> int:
    """
    Retry failed alerts (reset to pending).

    Phase-2.5A: Delegated to driver (L6).

    Args:
        max_retries: Maximum additional retries to allow

    Returns:
        Number of alerts reset
    """
    from app.hoc.cus.analytics.drivers.alert_driver import (
        get_alert_driver,
    )

    async with async_session_context() as session:
        now = datetime.now(timezone.utc)
        driver = get_alert_driver(session)

        count = await driver.retry_failed_alerts(max_retries=max_retries, now=now)
        await driver.commit()

        if count > 0:
            logger.info(f"Reset {count} failed alerts for retry")

        return count


async def purge_old_alerts(
    days: int = 30,
    statuses: Optional[List[str]] = None,
) -> int:
    """
    Purge old alerts from queue.

    Phase-2.5A: Delegated to driver (L6).

    Args:
        days: Delete alerts older than this many days
        statuses: Only delete these statuses (default: sent, failed)

    Returns:
        Number of alerts deleted
    """
    from app.hoc.cus.analytics.drivers.alert_driver import (
        get_alert_driver,
    )

    statuses = statuses or ["sent", "failed"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    async with async_session_context() as session:
        driver = get_alert_driver(session)

        count = await driver.purge_old_alerts(cutoff=cutoff, statuses=statuses)
        await driver.commit()

        if count > 0:
            logger.info(f"Purged {count} old alerts")

        return count


async def run_alert_worker(
    use_leader_election: bool = True,
    process_interval: float = 5.0,
) -> None:
    """
    Run alert worker continuously.

    Convenience function for running the worker as a background task.

    Args:
        use_leader_election: Only process if we hold the leader lock
        process_interval: Seconds between processing batches
    """
    worker = AlertWorker(process_interval_seconds=process_interval)
    await worker.run_continuous(use_leader_election=use_leader_election)
