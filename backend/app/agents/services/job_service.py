# M12 Job Service
# Job creation, status tracking, and item distribution
#
# Handles:
# - Job spawn with item creation
# - Job status queries
# - Progress tracking
# - Job completion/failure handling

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .credit_service import CreditService, get_credit_service, CREDIT_COSTS

logger = logging.getLogger("nova.agents.job_service")


@dataclass
class JobConfig:
    """Configuration for a parallel job."""
    orchestrator_agent: str
    worker_agent: str
    task: str
    items: List[Any]  # Input items to process
    parallelism: int = 10
    timeout_per_item: int = 60  # seconds
    max_retries: int = 3

    # M15: LLM Governance
    llm_budget_cents: Optional[int] = None  # Total LLM budget for this job
    llm_budget_per_item: Optional[int] = None  # Budget per item (calculated if not set)
    llm_risk_threshold: float = 0.6  # Risk score threshold for blocking
    llm_max_temperature: float = 1.0  # Max temperature allowed
    llm_enforce_safety: bool = True  # Whether to block high-risk outputs
    llm_config: Optional[Dict[str, Any]] = None  # Additional LLM config


@dataclass
class JobProgress:
    """Job progress status."""
    total: int
    completed: int
    failed: int
    pending: int
    progress_pct: float


@dataclass
class JobCredits:
    """Job credit tracking."""
    reserved: Decimal
    spent: Decimal
    refunded: Decimal


@dataclass
class Job:
    """Job entity."""
    id: UUID
    orchestrator_instance_id: str
    task: str
    config: Dict[str, Any]
    status: str
    progress: JobProgress
    credits: JobCredits
    tenant_id: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


@dataclass
class JobItem:
    """Individual work item in a job."""
    id: UUID
    job_id: UUID
    item_index: int
    input: Any
    output: Optional[Any]
    worker_instance_id: Optional[str]
    status: str
    claimed_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


class JobService:
    """
    Job management service for M12 multi-agent system.

    Creates jobs with items, tracks progress, handles completion.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        credit_service: Optional[CreditService] = None,
    ):
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL required for JobService")

        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.Session = sessionmaker(bind=self.engine)
        self.credit_service = credit_service or get_credit_service()

    def create_job(
        self,
        config: JobConfig,
        orchestrator_instance_id: str,
        tenant_id: str = "default",
    ) -> Job:
        """
        Create a new parallel job with items.

        Args:
            config: Job configuration
            orchestrator_instance_id: ID of orchestrator agent
            tenant_id: Tenant for billing

        Returns:
            Created job with ID

        Raises:
            ValueError: If validation fails
            RuntimeError: If credit check fails
        """
        # Validate
        if not config.items:
            raise ValueError("Job must have at least one item")
        if config.parallelism < 1:
            raise ValueError("Parallelism must be >= 1")

        job_id = uuid.uuid4()
        item_count = len(config.items)

        # Step 1: Pre-flight credit check (BEFORE job creation)
        credit_check = self.credit_service.check_reservation(
            tenant_id=tenant_id,
            item_count=item_count,
        )

        if not credit_check.success:
            raise RuntimeError(f"Credit check failed: {credit_check.reason}")

        credit_amount = credit_check.amount

        with self.Session() as session:
            try:
                # Create job
                job_config = {
                    "orchestrator_agent": config.orchestrator_agent,
                    "worker_agent": config.worker_agent,
                    "parallelism": config.parallelism,
                    "timeout_per_item": config.timeout_per_item,
                    "max_retries": config.max_retries,
                }

                # M15: LLM Governance config
                llm_governance_config = {
                    "risk_threshold": config.llm_risk_threshold,
                    "max_temperature": config.llm_max_temperature,
                    "enforce_safety": config.llm_enforce_safety,
                    **(config.llm_config or {}),
                }

                # Step 2: Create job FIRST (so credit_ledger FK is valid)
                session.execute(
                    text("""
                        INSERT INTO agents.jobs (
                            id, orchestrator_instance_id, task, config,
                            status, total_items, tenant_id,
                            credits_reserved, created_at, started_at,
                            llm_budget_cents, llm_config
                        ) VALUES (
                            :id, :orchestrator_instance_id, :task,
                            CAST(:config AS JSONB),
                            'running', :total_items, :tenant_id,
                            :credits_reserved, now(), now(),
                            :llm_budget_cents, CAST(:llm_config AS JSONB)
                        )
                    """),
                    {
                        "id": str(job_id),
                        "orchestrator_instance_id": orchestrator_instance_id,
                        "task": config.task,
                        "config": json.dumps(job_config),
                        "total_items": item_count,
                        "tenant_id": tenant_id,
                        "credits_reserved": float(credit_amount),
                        "llm_budget_cents": config.llm_budget_cents,
                        "llm_config": json.dumps(llm_governance_config),
                    }
                )

                # Create job items
                for idx, item_input in enumerate(config.items):
                    item_id = uuid.uuid4()
                    session.execute(
                        text("""
                            INSERT INTO agents.job_items (
                                id, job_id, item_index, input, status, max_retries
                            ) VALUES (
                                :id, :job_id, :item_index,
                                CAST(:input AS JSONB), 'pending', :max_retries
                            )
                        """),
                        {
                            "id": str(item_id),
                            "job_id": str(job_id),
                            "item_index": idx,
                            "input": json.dumps(item_input) if not isinstance(item_input, str) else json.dumps({"value": item_input}),
                            "max_retries": config.max_retries,
                        }
                    )

                session.commit()

                # Step 3: Log credit reservation AFTER job creation (FK safe)
                self.credit_service.log_reservation(
                    job_id=job_id,
                    tenant_id=tenant_id,
                    amount=credit_amount,
                )

                logger.info(
                    "job_created",
                    extra={
                        "job_id": str(job_id),
                        "task": config.task,
                        "item_count": item_count,
                        "parallelism": config.parallelism,
                        "tenant_id": tenant_id,
                        "credits_reserved": float(credit_amount),
                    }
                )

                return Job(
                    id=job_id,
                    orchestrator_instance_id=orchestrator_instance_id,
                    task=config.task,
                    config=job_config,
                    status="running",
                    progress=JobProgress(
                        total=item_count,
                        completed=0,
                        failed=0,
                        pending=item_count,
                        progress_pct=0.0,
                    ),
                    credits=JobCredits(
                        reserved=credit_amount,
                        spent=Decimal("0"),
                        refunded=Decimal("0"),
                    ),
                    tenant_id=tenant_id,
                    created_at=datetime.now(timezone.utc),
                    started_at=datetime.now(timezone.utc),
                    completed_at=None,
                )

            except Exception as e:
                session.rollback()
                logger.error(f"Job creation failed: {e}")
                raise

    def get_job(self, job_id: UUID) -> Optional[Job]:
        """Get job by ID with current progress."""
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT
                        id, orchestrator_instance_id, task, config, status,
                        total_items, completed_items, failed_items,
                        credits_reserved, credits_spent, credits_refunded,
                        tenant_id, created_at, started_at, completed_at
                    FROM agents.jobs
                    WHERE id = :job_id
                """),
                {"job_id": str(job_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            total = row[5] or 0
            completed = row[6] or 0
            failed = row[7] or 0
            pending = total - completed - failed

            return Job(
                id=UUID(str(row[0])),
                orchestrator_instance_id=row[1],
                task=row[2],
                config=row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {},
                status=row[4],
                progress=JobProgress(
                    total=total,
                    completed=completed,
                    failed=failed,
                    pending=pending,
                    progress_pct=round((completed / total) * 100, 2) if total > 0 else 0.0,
                ),
                credits=JobCredits(
                    reserved=Decimal(str(row[8] or 0)),
                    spent=Decimal(str(row[9] or 0)),
                    refunded=Decimal(str(row[10] or 0)),
                ),
                tenant_id=row[11],
                created_at=row[12],
                started_at=row[13],
                completed_at=row[14],
            )

    def list_jobs(
        self,
        tenant_id: str = "default",
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Job]:
        """List jobs for tenant."""
        with self.Session() as session:
            query = """
                SELECT
                    id, orchestrator_instance_id, task, config, status,
                    total_items, completed_items, failed_items,
                    credits_reserved, credits_spent, credits_refunded,
                    tenant_id, created_at, started_at, completed_at
                FROM agents.jobs
                WHERE tenant_id = :tenant_id
            """
            params = {"tenant_id": tenant_id, "limit": limit}

            if status:
                query += " AND status = :status"
                params["status"] = status

            query += " ORDER BY created_at DESC LIMIT :limit"

            result = session.execute(text(query), params)
            jobs = []

            for row in result:
                total = row[5] or 0
                completed = row[6] or 0
                failed = row[7] or 0
                pending = total - completed - failed

                jobs.append(Job(
                    id=UUID(str(row[0])),
                    orchestrator_instance_id=row[1],
                    task=row[2],
                    config=row[3] if isinstance(row[3], dict) else json.loads(row[3]) if row[3] else {},
                    status=row[4],
                    progress=JobProgress(
                        total=total,
                        completed=completed,
                        failed=failed,
                        pending=pending,
                        progress_pct=round((completed / total) * 100, 2) if total > 0 else 0.0,
                    ),
                    credits=JobCredits(
                        reserved=Decimal(str(row[8] or 0)),
                        spent=Decimal(str(row[9] or 0)),
                        refunded=Decimal(str(row[10] or 0)),
                    ),
                    tenant_id=row[11],
                    created_at=row[12],
                    started_at=row[13],
                    completed_at=row[14],
                ))

            return jobs

    def check_job_completion(self, job_id: UUID) -> bool:
        """
        Check if job is complete and update status if so.

        Returns True if job is now complete.
        """
        with self.Session() as session:
            # Check if all items are done
            result = session.execute(
                text("""
                    SELECT
                        total_items,
                        completed_items,
                        failed_items,
                        status
                    FROM agents.jobs
                    WHERE id = :job_id
                """),
                {"job_id": str(job_id)}
            )
            row = result.fetchone()

            if not row:
                return False

            total, completed, failed, status = row

            if status in ("completed", "failed", "cancelled"):
                return True

            # All items processed?
            if completed + failed >= total:
                new_status = "completed" if failed == 0 else "failed"

                session.execute(
                    text("""
                        UPDATE agents.jobs
                        SET status = :status, completed_at = now()
                        WHERE id = :job_id
                    """),
                    {"job_id": str(job_id), "status": new_status}
                )
                session.commit()

                logger.info(
                    "job_completed",
                    extra={
                        "job_id": str(job_id),
                        "status": new_status,
                        "completed": completed,
                        "failed": failed,
                    }
                )

                return True

            return False

    def cancel_job(
        self,
        job_id: UUID,
        cancelled_by: str = "system",
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Cancel a running job with credit refunds.

        Args:
            job_id: Job to cancel
            cancelled_by: Who is cancelling (user ID or "system")
            reason: Optional cancellation reason

        Returns:
            Cancellation details including refunded credits, or None if not found/cancellable
        """
        with self.Session() as session:
            try:
                # Get job state
                result = session.execute(
                    text("""
                        SELECT
                            id, status, total_items, completed_items, failed_items,
                            credits_reserved, credits_spent, tenant_id
                        FROM agents.jobs
                        WHERE id = :job_id
                        FOR UPDATE
                    """),
                    {"job_id": str(job_id)}
                )
                row = result.fetchone()

                if not row:
                    return None

                job_id_db, status, total, completed, failed, reserved, spent, tenant_id = row

                # Can only cancel pending or running jobs
                if status not in ("pending", "running"):
                    logger.warning(f"Cannot cancel job {job_id} in status {status}")
                    return None

                # Calculate items to cancel and credits to refund
                items_cancelled = total - completed - failed
                # Refund = reserved credits for uncompleted items
                # Each item costs CREDIT_COSTS["job_item"] = 2
                from .credit_service import CREDIT_COSTS
                credits_to_refund = Decimal(str(items_cancelled)) * CREDIT_COSTS["job_item"]

                # Update job status
                session.execute(
                    text("""
                        UPDATE agents.jobs
                        SET status = 'cancelled',
                            completed_at = now(),
                            credits_refunded = credits_refunded + :refund
                        WHERE id = :job_id
                    """),
                    {
                        "job_id": str(job_id),
                        "refund": float(credits_to_refund),
                    }
                )

                # Mark unclaimed items as cancelled
                session.execute(
                    text("""
                        UPDATE agents.job_items
                        SET status = 'cancelled'
                        WHERE job_id = :job_id AND status = 'pending'
                    """),
                    {"job_id": str(job_id)}
                )

                # Record cancellation
                session.execute(
                    text("""
                        INSERT INTO agents.job_cancellations (
                            job_id, cancelled_by, reason,
                            items_completed, items_cancelled, credits_refunded
                        ) VALUES (
                            CAST(:job_id AS UUID), :cancelled_by, :reason,
                            :completed, :cancelled, :refunded
                        )
                    """),
                    {
                        "job_id": str(job_id),
                        "cancelled_by": cancelled_by,
                        "reason": reason,
                        "completed": completed,
                        "cancelled": items_cancelled,
                        "refunded": float(credits_to_refund),
                    }
                )

                # Log refund to credit ledger
                session.execute(
                    text("""
                        INSERT INTO agents.credit_ledger (
                            job_id, tenant_id, operation, skill, amount
                        ) VALUES (
                            CAST(:job_id AS UUID), :tenant_id, 'refund', 'job_cancel', :amount
                        )
                    """),
                    {
                        "job_id": str(job_id),
                        "tenant_id": tenant_id,
                        "amount": float(credits_to_refund),
                    }
                )

                session.commit()

                result_data = {
                    "job_id": str(job_id),
                    "status": "cancelled",
                    "completed_items": completed,
                    "cancelled_items": items_cancelled,
                    "credits_refunded": float(credits_to_refund),
                    "cancelled_by": cancelled_by,
                    "reason": reason,
                }

                logger.info(
                    "job_cancelled_with_refund",
                    extra=result_data
                )

                return result_data

            except Exception as e:
                session.rollback()
                logger.error(f"Job cancellation failed: {e}")
                raise

    def get_job_items(
        self,
        job_id: UUID,
        status: Optional[str] = None,
    ) -> List[JobItem]:
        """Get items for a job."""
        with self.Session() as session:
            query = """
                SELECT
                    id, job_id, item_index, input, output,
                    worker_instance_id, status, claimed_at,
                    completed_at, error_message
                FROM agents.job_items
                WHERE job_id = :job_id
            """
            params = {"job_id": str(job_id)}

            if status:
                query += " AND status = :status"
                params["status"] = status

            query += " ORDER BY item_index"

            result = session.execute(text(query), params)
            items = []

            for row in result:
                items.append(JobItem(
                    id=UUID(str(row[0])),
                    job_id=UUID(str(row[1])),
                    item_index=row[2],
                    input=row[3],
                    output=row[4],
                    worker_instance_id=row[5],
                    status=row[6],
                    claimed_at=row[7],
                    completed_at=row[8],
                    error_message=row[9],
                ))

            return items


# Singleton instance
_service: Optional[JobService] = None


def get_job_service() -> JobService:
    """Get singleton job service instance."""
    global _service
    if _service is None:
        _service = JobService()
    return _service
