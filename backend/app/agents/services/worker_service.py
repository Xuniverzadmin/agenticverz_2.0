# M12 Worker Service
# Concurrent-safe job item claiming using FOR UPDATE SKIP LOCKED
#
# Pattern reused from M10 recovery_claim_worker.py (95% reuse)

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .credit_service import get_credit_service, CreditService
from .governance_service import get_governance_service, GovernanceService

logger = logging.getLogger("nova.agents.worker_service")


@dataclass
class ClaimedItem:
    """A claimed job item ready for processing."""
    id: UUID
    job_id: UUID
    item_index: int
    input: Any
    max_retries: int
    retry_count: int

    # M15: LLM Governance
    llm_budget_cents: Optional[int] = None
    llm_config: Optional[Dict[str, Any]] = None


@dataclass
class WorkerStats:
    """Statistics for a worker."""
    instance_id: str
    items_claimed: int
    items_completed: int
    items_failed: int


class WorkerService:
    """
    Worker service for M12 multi-agent system.

    Provides concurrent-safe job item claiming using FOR UPDATE SKIP LOCKED.
    Handles item completion, failure, and retry logic.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        credit_service: Optional[CreditService] = None,
        governance_service: Optional[GovernanceService] = None,
    ):
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL required for WorkerService")

        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.Session = sessionmaker(bind=self.engine)
        self.credit_service = credit_service or get_credit_service()
        self.governance_service = governance_service or get_governance_service()

    def claim_item(
        self,
        job_id: UUID,
        worker_instance_id: str,
    ) -> Optional[ClaimedItem]:
        """
        Claim next available item from job using FOR UPDATE SKIP LOCKED.

        This is concurrent-safe: multiple workers can call simultaneously
        and each gets a unique item (or None if all claimed).

        Args:
            job_id: Job to claim from
            worker_instance_id: Worker claiming the item

        Returns:
            ClaimedItem if available, None if no items left
        """
        with self.Session() as session:
            # Use the pre-built claim function or raw SQL
            try:
                result = session.execute(
                    text("""
                        SELECT * FROM agents.claim_job_item(
                            CAST(:job_id AS UUID),
                            :worker_instance_id
                        )
                    """),
                    {
                        "job_id": str(job_id),
                        "worker_instance_id": worker_instance_id,
                    }
                )
                row = result.fetchone()
                session.commit()

                if not row or row[0] is None:
                    return None

                # Fetch full item details
                item_result = session.execute(
                    text("""
                        SELECT id, job_id, item_index, input, max_retries, retry_count
                        FROM agents.job_items
                        WHERE id = :item_id
                    """),
                    {"item_id": str(row[0])}
                )
                item_row = item_result.fetchone()

                if not item_row:
                    return None

                logger.debug(
                    "item_claimed",
                    extra={
                        "job_id": str(job_id),
                        "item_id": str(row[0]),
                        "worker_instance_id": worker_instance_id,
                    }
                )

                # M15: Get LLM governance config from job
                llm_config = self._get_job_llm_config(session, job_id)

                item = ClaimedItem(
                    id=UUID(str(item_row[0])),
                    job_id=UUID(str(item_row[1])),
                    item_index=item_row[2],
                    input=item_row[3],
                    max_retries=item_row[4] or 3,
                    retry_count=item_row[5] or 0,
                    llm_budget_cents=llm_config.get("llm_budget_per_item") if llm_config else None,
                    llm_config=llm_config,
                )

                # M15: Allocate budget to worker
                if llm_config and llm_config.get("llm_budget_cents"):
                    self.governance_service.allocate_worker_budget(
                        instance_id=worker_instance_id,
                        job_id=job_id,
                        budget_cents=llm_config.get("llm_budget_per_item"),
                    )

                return item

            except Exception as e:
                session.rollback()
                # Fall back to raw SQL if function doesn't exist
                logger.debug(f"claim_job_item function failed, using raw SQL: {e}")
                return self._claim_item_raw(session, job_id, worker_instance_id)

    def _claim_item_raw(
        self,
        session,
        job_id: UUID,
        worker_instance_id: str,
    ) -> Optional[ClaimedItem]:
        """Fallback raw SQL claim (from M10 pattern)."""
        try:
            result = session.execute(
                text("""
                    WITH claimed AS (
                        SELECT id
                        FROM agents.job_items
                        WHERE job_id = :job_id AND status = 'pending'
                        ORDER BY item_index ASC
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    )
                    UPDATE agents.job_items
                    SET status = 'claimed',
                        worker_instance_id = :worker_instance_id,
                        claimed_at = now()
                    FROM claimed
                    WHERE agents.job_items.id = claimed.id
                    RETURNING agents.job_items.id, agents.job_items.job_id,
                              agents.job_items.item_index, agents.job_items.input,
                              agents.job_items.max_retries, agents.job_items.retry_count
                """),
                {
                    "job_id": str(job_id),
                    "worker_instance_id": worker_instance_id,
                }
            )
            row = result.fetchone()
            session.commit()

            if not row:
                return None

            return ClaimedItem(
                id=UUID(str(row[0])),
                job_id=UUID(str(row[1])),
                item_index=row[2],
                input=row[3],
                max_retries=row[4] or 3,
                retry_count=row[5] or 0,
            )

        except Exception as e:
            session.rollback()
            logger.error(f"Raw claim failed: {e}")
            return None

    def _get_job_llm_config(self, session, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get LLM governance config from job (M15)."""
        try:
            result = session.execute(
                text("""
                    SELECT llm_budget_cents, llm_config, config
                    FROM agents.jobs
                    WHERE id = :job_id
                """),
                {"job_id": str(job_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            llm_budget, llm_config, job_config = row

            # Parse JSON if needed
            if isinstance(llm_config, str):
                llm_config = json.loads(llm_config)
            if isinstance(job_config, str):
                job_config = json.loads(job_config)

            # Merge configs
            merged = {
                "llm_budget_cents": llm_budget,
                **(llm_config or {}),
            }

            # Get per-item budget from job config if available
            if job_config and "llm_budget_per_item" in (job_config or {}):
                merged["llm_budget_per_item"] = job_config["llm_budget_per_item"]
            elif llm_budget:
                # Calculate per-item budget
                total_items_result = session.execute(
                    text("SELECT total_items FROM agents.jobs WHERE id = :job_id"),
                    {"job_id": str(job_id)}
                )
                total_row = total_items_result.fetchone()
                if total_row and total_row[0]:
                    merged["llm_budget_per_item"] = llm_budget // total_row[0]

            return merged

        except Exception as e:
            logger.warning(f"Failed to get job LLM config: {e}")
            return None

    def start_item(self, item_id: UUID) -> bool:
        """
        Mark item as running (transition from claimed to running).

        Args:
            item_id: Item to start

        Returns:
            True if started successfully
        """
        with self.Session() as session:
            try:
                result = session.execute(
                    text("""
                        UPDATE agents.job_items
                        SET status = 'running'
                        WHERE id = :item_id AND status = 'claimed'
                        RETURNING id
                    """),
                    {"item_id": str(item_id)}
                )
                row = result.fetchone()
                session.commit()
                return row is not None
            except Exception as e:
                session.rollback()
                logger.error(f"Start item failed: {e}")
                return False

    def complete_item(
        self,
        item_id: UUID,
        output: Any,
        # M15: Governance data
        llm_cost_cents: Optional[float] = None,
        llm_tokens_used: Optional[int] = None,
        risk_score: Optional[float] = None,
        risk_factors: Optional[Dict[str, Any]] = None,
        blocked: bool = False,
        blocked_reason: Optional[str] = None,
        params_clamped: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Mark item as completed with output.

        Also updates job counters and charges credits.
        M15: Records LLM governance data if provided.

        Args:
            item_id: Item to complete
            output: Result data
            llm_cost_cents: LLM cost in cents
            llm_tokens_used: Total tokens used
            risk_score: Risk score (0.0-1.0)
            risk_factors: Risk factor breakdown
            blocked: Whether output was blocked
            blocked_reason: Reason for blocking
            params_clamped: Parameters that were clamped

        Returns:
            True if completed successfully
        """
        with self.Session() as session:
            try:
                # Get job_id for credit tracking
                result = session.execute(
                    text("""
                        SELECT job_id, status
                        FROM agents.job_items
                        WHERE id = :item_id
                    """),
                    {"item_id": str(item_id)}
                )
                row = result.fetchone()

                if not row:
                    return False

                job_id, current_status = row

                if current_status not in ("claimed", "running"):
                    logger.warning(f"Cannot complete item in status: {current_status}")
                    return False

                # Update item (M15: include governance data)
                session.execute(
                    text("""
                        UPDATE agents.job_items
                        SET status = 'completed',
                            output = CAST(:output AS JSONB),
                            completed_at = now(),
                            risk_score = COALESCE(:risk_score, risk_score),
                            risk_factors = COALESCE(CAST(:risk_factors AS JSONB), risk_factors),
                            blocked = :blocked,
                            blocked_reason = :blocked_reason,
                            params_clamped = COALESCE(CAST(:params_clamped AS JSONB), params_clamped),
                            llm_cost_cents = COALESCE(:llm_cost, llm_cost_cents),
                            llm_tokens_used = COALESCE(:llm_tokens, llm_tokens_used)
                        WHERE id = :item_id
                    """),
                    {
                        "item_id": str(item_id),
                        "output": json.dumps(output) if not isinstance(output, str) else output,
                        "risk_score": risk_score,
                        "risk_factors": json.dumps(risk_factors) if risk_factors else None,
                        "blocked": blocked,
                        "blocked_reason": blocked_reason,
                        "params_clamped": json.dumps(params_clamped) if params_clamped else None,
                        "llm_cost": llm_cost_cents,
                        "llm_tokens": llm_tokens_used,
                    }
                )

                # Update job counters (M15: include LLM budget usage)
                llm_cost_int = int(llm_cost_cents) if llm_cost_cents else 0
                session.execute(
                    text("""
                        UPDATE agents.jobs
                        SET completed_items = completed_items + 1,
                            credits_spent = credits_spent + 2,
                            llm_budget_used = llm_budget_used + :llm_cost,
                            llm_risk_violations = llm_risk_violations + CASE WHEN :blocked THEN 1 ELSE 0 END
                        WHERE id = :job_id
                    """),
                    {
                        "job_id": str(job_id),
                        "llm_cost": llm_cost_int,
                        "blocked": blocked,
                    }
                )

                session.commit()

                logger.info(
                    "item_completed",
                    extra={
                        "item_id": str(item_id),
                        "job_id": str(job_id),
                        "risk_score": risk_score,
                        "llm_cost_cents": llm_cost_cents,
                        "blocked": blocked,
                    }
                )

                return True

            except Exception as e:
                session.rollback()
                logger.error(f"Complete item failed: {e}")
                return False

    def fail_item(
        self,
        item_id: UUID,
        error_message: str,
        retry: bool = True,
    ) -> bool:
        """
        Mark item as failed.

        If retry=True and retries available, resets to pending.
        Otherwise marks as failed and refunds credits.

        Args:
            item_id: Item that failed
            error_message: Error description
            retry: Whether to retry if possible

        Returns:
            True if processed successfully
        """
        with self.Session() as session:
            try:
                # Get current state
                result = session.execute(
                    text("""
                        SELECT job_id, retry_count, max_retries, status
                        FROM agents.job_items
                        WHERE id = :item_id
                    """),
                    {"item_id": str(item_id)}
                )
                row = result.fetchone()

                if not row:
                    return False

                job_id, retry_count, max_retries, current_status = row

                if current_status not in ("claimed", "running"):
                    logger.warning(f"Cannot fail item in status: {current_status}")
                    return False

                # Can we retry?
                can_retry = retry and (retry_count or 0) < (max_retries or 3)

                if can_retry:
                    # Reset to pending for retry
                    session.execute(
                        text("""
                            UPDATE agents.job_items
                            SET status = 'pending',
                                worker_instance_id = NULL,
                                claimed_at = NULL,
                                retry_count = retry_count + 1,
                                error_message = :error
                            WHERE id = :item_id
                        """),
                        {
                            "item_id": str(item_id),
                            "error": error_message[:1000],
                        }
                    )
                    logger.info(
                        "item_retrying",
                        extra={
                            "item_id": str(item_id),
                            "retry_count": (retry_count or 0) + 1,
                        }
                    )
                else:
                    # Mark as permanently failed
                    session.execute(
                        text("""
                            UPDATE agents.job_items
                            SET status = 'failed',
                                error_message = :error,
                                completed_at = now()
                            WHERE id = :item_id
                        """),
                        {
                            "item_id": str(item_id),
                            "error": error_message[:1000],
                        }
                    )

                    # Update job counters and refund credits
                    session.execute(
                        text("""
                            UPDATE agents.jobs
                            SET failed_items = failed_items + 1,
                                credits_refunded = credits_refunded + 2
                            WHERE id = :job_id
                        """),
                        {"job_id": str(job_id)}
                    )

                    logger.info(
                        "item_failed",
                        extra={
                            "item_id": str(item_id),
                            "job_id": str(job_id),
                            "error": error_message[:100],
                        }
                    )

                session.commit()
                return True

            except Exception as e:
                session.rollback()
                logger.error(f"Fail item failed: {e}")
                return False

    def release_claimed(self, worker_instance_id: str) -> int:
        """
        Release all items claimed by a worker.

        Called during graceful shutdown.

        Args:
            worker_instance_id: Worker being shut down

        Returns:
            Number of items released
        """
        with self.Session() as session:
            try:
                result = session.execute(
                    text("""
                        UPDATE agents.job_items
                        SET status = 'pending',
                            worker_instance_id = NULL,
                            claimed_at = NULL
                        WHERE worker_instance_id = :worker_instance_id
                          AND status IN ('claimed', 'running')
                        RETURNING id
                    """),
                    {"worker_instance_id": worker_instance_id}
                )
                released = len(result.fetchall())
                session.commit()

                if released > 0:
                    logger.info(
                        "items_released",
                        extra={
                            "worker_instance_id": worker_instance_id,
                            "count": released,
                        }
                    )

                return released

            except Exception as e:
                session.rollback()
                logger.error(f"Release claimed failed: {e}")
                return 0

    def get_worker_stats(self, worker_instance_id: str) -> WorkerStats:
        """Get statistics for a worker."""
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT
                        COUNT(*) FILTER (WHERE status IN ('claimed', 'running')) as claimed,
                        COUNT(*) FILTER (WHERE status = 'completed') as completed,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed
                    FROM agents.job_items
                    WHERE worker_instance_id = :worker_instance_id
                """),
                {"worker_instance_id": worker_instance_id}
            )
            row = result.fetchone()

            return WorkerStats(
                instance_id=worker_instance_id,
                items_claimed=row[0] or 0,
                items_completed=row[1] or 0,
                items_failed=row[2] or 0,
            )


# Singleton instance
_service: Optional[WorkerService] = None


def get_worker_service() -> WorkerService:
    """Get singleton worker service instance."""
    global _service
    if _service is None:
        _service = WorkerService()
    return _service
