# CostSim Alert Worker - Reliable Alert Delivery
"""
Background worker for reliable alert delivery.

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

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.costsim.config import get_config
from app.costsim.leader import (
    LOCK_ALERT_WORKER,
    leader_election,
)
from app.costsim.metrics import get_metrics
from app.db_async import AsyncSessionLocal, async_session_context
from app.models.costsim_cb import CostSimAlertQueueModel, CostSimCBIncidentModel

logger = logging.getLogger("nova.costsim.alert_worker")


class AlertWorker:
    """
    Background worker for processing alert queue.

    Sends pending alerts to Alertmanager with retry logic.
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

        # HTTP client
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

    async def process_batch(self, batch_size: Optional[int] = None) -> int:
        """
        Process a batch of pending alerts.

        Args:
            batch_size: Override default batch size

        Returns:
            Number of alerts processed
        """
        batch_size = batch_size or self.batch_size
        processed = 0

        async with async_session_context() as session:
            # Get pending alerts ready to send
            now = datetime.now(timezone.utc)

            statement = (
                select(CostSimAlertQueueModel)
                .where(
                    and_(
                        CostSimAlertQueueModel.status == "pending",
                        CostSimAlertQueueModel.next_attempt_at <= now,
                    )
                )
                .order_by(CostSimAlertQueueModel.next_attempt_at)
                .limit(batch_size)
                .with_for_update(skip_locked=True)  # Skip locked rows
            )

            result = await session.execute(statement)
            alerts = list(result.scalars())

            # Update queue depth metric
            metrics = get_metrics()
            metrics.set_alert_queue_depth(len(alerts))

            for alert in alerts:
                success = await self._send_alert(alert, session)
                processed += 1

                if success:
                    alert.status = "sent"
                    alert.sent_at = datetime.now(timezone.utc)
                    logger.info(f"Alert sent: id={alert.id}, type={alert.alert_type}")

                    # Update incident if linked
                    if alert.incident_id:
                        await self._mark_incident_alert_sent(session, alert.incident_id)
                else:
                    # Increment attempts and calculate next retry
                    alert.attempts += 1
                    alert.last_attempt_at = datetime.now(timezone.utc)

                    if alert.attempts >= alert.max_attempts:
                        alert.status = "failed"
                        logger.error(f"Alert failed (max attempts): id={alert.id}, attempts={alert.attempts}")
                    else:
                        # Exponential backoff: 2^attempts seconds, capped
                        backoff = min(2**alert.attempts, self.max_backoff)
                        alert.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=backoff)
                        logger.warning(
                            f"Alert retry scheduled: id={alert.id}, attempt={alert.attempts}, backoff={backoff}s"
                        )

            await session.commit()

        return processed

    async def _send_alert(
        self,
        alert: CostSimAlertQueueModel,
        session: AsyncSession,
    ) -> bool:
        """
        Send alert to Alertmanager.

        Args:
            alert: Alert queue model
            session: Database session for updating error

        Returns:
            True if sent successfully
        """
        if not self.alertmanager_url:
            logger.warning("Alertmanager URL not configured, skipping alert")
            return True  # Treat as success to avoid infinite retries

        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.alertmanager_url}/api/v2/alerts",
                json=alert.payload,
            )
            response.raise_for_status()
            return True

        except httpx.TimeoutException as e:
            alert.last_error = f"Timeout: {e}"
            logger.warning(f"Alert timeout: id={alert.id}, error={e}")
            get_metrics().record_alert_send_failure(
                alert_type=alert.alert_type or "unknown",
                error_type="timeout",
            )
            return False

        except httpx.HTTPStatusError as e:
            alert.last_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            logger.warning(f"Alert HTTP error: id={alert.id}, status={e.response.status_code}")
            get_metrics().record_alert_send_failure(
                alert_type=alert.alert_type or "unknown",
                error_type=f"http_{e.response.status_code}",
            )
            return False

        except Exception as e:
            alert.last_error = str(e)[:500]
            logger.error(f"Alert error: id={alert.id}, error={e}")
            get_metrics().record_alert_send_failure(
                alert_type=alert.alert_type or "unknown",
                error_type="connection",
            )
            return False

    async def _mark_incident_alert_sent(
        self,
        session: AsyncSession,
        incident_id: str,
    ) -> None:
        """Mark incident as having alert sent."""
        try:
            await session.execute(
                update(CostSimCBIncidentModel)
                .where(CostSimCBIncidentModel.id == incident_id)
                .values(
                    alert_sent=True,
                    alert_sent_at=datetime.now(timezone.utc),
                )
            )
        except Exception as e:
            logger.error(f"Failed to mark incident alert sent: {e}")

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

        Returns:
            Dictionary with queue stats
        """
        async with async_session_context() as session:
            from sqlalchemy import func

            # Count by status
            status_counts = {}
            for status in ["pending", "sent", "failed"]:
                result = await session.execute(
                    select(func.count())
                    .select_from(CostSimAlertQueueModel)
                    .where(CostSimAlertQueueModel.status == status)
                )
                status_counts[status] = result.scalar() or 0

            # Get oldest pending
            result = await session.execute(
                select(func.min(CostSimAlertQueueModel.created_at)).where(CostSimAlertQueueModel.status == "pending")
            )
            oldest_pending = result.scalar()

            return {
                "pending": status_counts.get("pending", 0),
                "sent": status_counts.get("sent", 0),
                "failed": status_counts.get("failed", 0),
                "oldest_pending": oldest_pending.isoformat() if oldest_pending else None,
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

    Args:
        payload: Alertmanager payload
        alert_type: Type of alert (disable, enable, canary_fail)
        circuit_breaker_name: Associated circuit breaker
        incident_id: Associated incident
        session: Optional async session

    Returns:
        ID of created queue entry
    """
    own_session = session is None

    if own_session:
        session = AsyncSessionLocal()

    try:
        alert = CostSimAlertQueueModel(
            payload=payload,
            alert_type=alert_type,
            circuit_breaker_name=circuit_breaker_name,
            incident_id=incident_id,
            status="pending",
        )
        assert session is not None
        session.add(alert)
        assert session is not None
        await session.commit()
        await session.refresh(alert)

        logger.debug(f"Alert enqueued: id={alert.id}, type={alert_type}")
        return alert.id

    except Exception as e:
        assert logger is not None
        logger.error(f"Failed to enqueue alert: {e}")
        if own_session:
            await session.rollback()
        raise

    finally:
        if own_session:
            await session.close()


async def retry_failed_alerts(
    max_retries: int = 3,
) -> int:
    """
    Retry failed alerts (reset to pending).

    Args:
        max_retries: Maximum additional retries to allow

    Returns:
        Number of alerts reset
    """
    async with async_session_context() as session:
        now = datetime.now(timezone.utc)

        result = await session.execute(
            update(CostSimAlertQueueModel)
            .where(
                and_(
                    CostSimAlertQueueModel.status == "failed",
                    CostSimAlertQueueModel.attempts < CostSimAlertQueueModel.max_attempts + max_retries,
                )
            )
            .values(
                status="pending",
                max_attempts=CostSimAlertQueueModel.max_attempts + max_retries,
                next_attempt_at=now,
            )
        )
        await session.commit()

        count = result.rowcount or 0
        if count > 0:
            logger.info(f"Reset {count} failed alerts for retry")

        return count


async def purge_old_alerts(
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
    statuses = statuses or ["sent", "failed"]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    async with async_session_context() as session:
        from sqlalchemy import delete

        result = await session.execute(
            delete(CostSimAlertQueueModel).where(
                and_(
                    CostSimAlertQueueModel.created_at < cutoff,
                    CostSimAlertQueueModel.status.in_(statuses),
                )
            )
        )
        await session.commit()

        count = result.rowcount or 0
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
