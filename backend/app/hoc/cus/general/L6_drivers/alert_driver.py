# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: CostSimAlertQueueModel, CostSimCBIncidentModel
#   Writes: CostSimAlertQueueModel, CostSimCBIncidentModel
# Database:
#   Scope: domain (analytics)
#   Models: CostSimAlertQueueModel, CostSimCBIncidentModel
# Role: Data access for alert queue operations
# Callers: alert_worker.py (L5 engine)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5, httpx
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, Phase-2.5A Analytics Extraction
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for alert queue management.
# NO business logic - only DB operations.
# NO HTTP operations - delivery stays in adapter.
# Business logic (retry decisions, status transitions) stays in L4 engine.
#
# ============================================================================
# L6 DRIVER INVENTORY — ALERT DOMAIN (CANONICAL)
# ============================================================================
# Method                              | Purpose                    | Status
# ----------------------------------- | -------------------------- | ------
# fetch_pending_alerts                | Get alerts ready to send   | [DONE]
# update_alert_sent                   | Mark alert as sent         | [DONE]
# update_alert_retry                  | Schedule retry             | [TODO]
# update_alert_failed                 | Mark alert as failed       | [TODO]
# mark_incident_alert_sent            | Update incident flag       | [TODO]
# fetch_queue_stats                   | Get queue statistics       | [TODO]
# insert_alert                        | Enqueue new alert          | [TODO]
# retry_failed_alerts                 | Reset failed to pending    | [TODO]
# purge_old_alerts                    | Delete old alerts          | [TODO]
# ============================================================================

"""
Alert Driver (L6)

Pure database operations for alert queue management.
All business logic stays in L4 engine.
All HTTP delivery stays in adapter.

Operations:
- Read pending alerts from queue
- Update alert status (sent, retry, failed)
- Update incident alert_sent flag
- Queue statistics
- Enqueue new alerts
- Retry/purge operations

NO business logic:
- NO retry decision logic (L4)
- NO backoff calculation (L4)
- NO HTTP operations (adapter)

Reference: Phase-2.5A Analytics Extraction
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.costsim_cb import CostSimAlertQueueModel, CostSimCBIncidentModel


class AlertDriver:
    """
    L6 driver for alert queue data access.

    Pure database access - no business logic, no HTTP.
    Transaction management is delegated to caller (L4 engine).
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self._session = session

    # =========================================================================
    # FETCH OPERATIONS
    # =========================================================================

    async def fetch_pending_alerts(
        self,
        now: datetime,
        batch_size: int,
    ) -> List[CostSimAlertQueueModel]:
        """
        Fetch pending alerts ready to send.

        Args:
            now: Current timestamp for filtering
            batch_size: Maximum number of alerts to fetch

        Returns:
            List of alert queue models ready for processing
        """
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
            .with_for_update(skip_locked=True)
        )

        result = await self._session.execute(statement)
        return list(result.scalars())

    async def fetch_queue_stats(self) -> Dict[str, Any]:
        """
        Fetch alert queue statistics.

        Returns:
            Dictionary with counts by status and oldest pending timestamp
        """
        status_counts = {}
        for status in ["pending", "sent", "failed"]:
            result = await self._session.execute(
                select(func.count())
                .select_from(CostSimAlertQueueModel)
                .where(CostSimAlertQueueModel.status == status)
            )
            status_counts[status] = result.scalar() or 0

        result = await self._session.execute(
            select(func.min(CostSimAlertQueueModel.created_at)).where(
                CostSimAlertQueueModel.status == "pending"
            )
        )
        oldest_pending = result.scalar()

        return {
            "pending": status_counts.get("pending", 0),
            "sent": status_counts.get("sent", 0),
            "failed": status_counts.get("failed", 0),
            "oldest_pending": oldest_pending,
        }

    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================

    async def update_alert_sent(
        self,
        alert: CostSimAlertQueueModel,
        sent_at: datetime,
    ) -> None:
        """
        Mark alert as successfully sent.

        Args:
            alert: Alert model to update
            sent_at: Timestamp of successful send
        """
        alert.status = "sent"
        alert.sent_at = sent_at

    async def update_alert_retry(
        self,
        alert: CostSimAlertQueueModel,
        last_attempt_at: datetime,
        next_attempt_at: datetime,
        last_error: Optional[str] = None,
    ) -> None:
        """
        Schedule alert for retry.

        Args:
            alert: Alert model to update
            last_attempt_at: Timestamp of failed attempt
            next_attempt_at: Timestamp for next retry
            last_error: Error message from failed attempt
        """
        alert.attempts += 1
        alert.last_attempt_at = last_attempt_at
        alert.next_attempt_at = next_attempt_at
        if last_error:
            alert.last_error = last_error

    async def update_alert_failed(
        self,
        alert: CostSimAlertQueueModel,
        last_attempt_at: datetime,
        last_error: Optional[str] = None,
    ) -> None:
        """
        Mark alert as permanently failed.

        Args:
            alert: Alert model to update
            last_attempt_at: Timestamp of final attempt
            last_error: Error message from failed attempt
        """
        alert.status = "failed"
        alert.attempts += 1
        alert.last_attempt_at = last_attempt_at
        if last_error:
            alert.last_error = last_error

    async def mark_incident_alert_sent(
        self,
        incident_id: str,
        sent_at: datetime,
    ) -> None:
        """
        Mark incident as having alert sent.

        Args:
            incident_id: ID of incident to update
            sent_at: Timestamp of alert send
        """
        await self._session.execute(
            update(CostSimCBIncidentModel)
            .where(CostSimCBIncidentModel.id == incident_id)
            .values(
                alert_sent=True,
                alert_sent_at=sent_at,
            )
        )

    # =========================================================================
    # INSERT OPERATIONS
    # =========================================================================

    async def insert_alert(
        self,
        payload: List[Dict[str, Any]],
        alert_type: str,
        circuit_breaker_name: Optional[str] = None,
        incident_id: Optional[str] = None,
    ) -> CostSimAlertQueueModel:
        """
        Insert new alert into queue.

        Args:
            payload: Alertmanager payload
            alert_type: Type of alert
            circuit_breaker_name: Associated circuit breaker
            incident_id: Associated incident

        Returns:
            Created alert model
        """
        alert = CostSimAlertQueueModel(
            payload=payload,
            alert_type=alert_type,
            circuit_breaker_name=circuit_breaker_name,
            incident_id=incident_id,
            status="pending",
        )
        self._session.add(alert)
        await self._session.flush()
        await self._session.refresh(alert)
        return alert

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    async def retry_failed_alerts(
        self,
        max_retries: int,
        now: datetime,
    ) -> int:
        """
        Reset failed alerts to pending for retry.

        Args:
            max_retries: Additional retries to allow
            now: Timestamp for next_attempt_at

        Returns:
            Number of alerts reset
        """
        result = await self._session.execute(
            update(CostSimAlertQueueModel)
            .where(
                and_(
                    CostSimAlertQueueModel.status == "failed",
                    CostSimAlertQueueModel.attempts
                    < CostSimAlertQueueModel.max_attempts + max_retries,
                )
            )
            .values(
                status="pending",
                max_attempts=CostSimAlertQueueModel.max_attempts + max_retries,
                next_attempt_at=now,
            )
        )
        return result.rowcount or 0

    async def purge_old_alerts(
        self,
        cutoff: datetime,
        statuses: List[str],
    ) -> int:
        """
        Delete old alerts from queue.

        Args:
            cutoff: Delete alerts created before this timestamp
            statuses: Only delete alerts with these statuses

        Returns:
            Number of alerts deleted
        """
        result = await self._session.execute(
            delete(CostSimAlertQueueModel).where(
                and_(
                    CostSimAlertQueueModel.created_at < cutoff,
                    CostSimAlertQueueModel.status.in_(statuses),
                )
            )
        )
        return result.rowcount or 0

    # TRANSACTION HELPERS section removed — L6 DOES NOT COMMIT


def get_alert_driver(session: AsyncSession) -> AlertDriver:
    """Factory function to get AlertDriver instance."""
    return AlertDriver(session)


__all__ = [
    "AlertDriver",
    "get_alert_driver",
]
