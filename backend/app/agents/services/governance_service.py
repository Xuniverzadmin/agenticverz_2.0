# M15 LLM Governance Service
# Orchestrates BudgetLLM governance across the M12 multi-agent system
#
# Features:
# - Per-job budget envelope management
# - Per-worker budget allocation and tracking
# - Risk aggregation and metrics
# - Budget check before LLM calls
# - Automatic budget distribution

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("nova.agents.governance_service")


# =============================================================================
# Data Types
# =============================================================================

@dataclass
class BudgetStatus:
    """Budget status for a job or worker."""
    budget_cents: Optional[int]  # None = unlimited
    used_cents: int
    remaining_cents: Optional[int]
    is_exceeded: bool
    utilization_pct: Optional[float]


@dataclass
class RiskMetrics:
    """Risk metrics for a job or worker."""
    total_items: int
    blocked_items: int
    avg_risk_score: float
    max_risk_score: float
    risk_violations: int
    risk_distribution: Dict[str, int]  # low/medium/high counts


@dataclass
class GovernanceStatus:
    """Combined governance status."""
    job_id: UUID
    budget: BudgetStatus
    risk: RiskMetrics
    config: Dict[str, Any]


@dataclass
class WorkerBudgetCheck:
    """Result of worker budget check."""
    can_proceed: bool
    budget_remaining: Optional[int]
    reason: str


# =============================================================================
# Governance Service
# =============================================================================

class GovernanceService:
    """
    LLM Governance orchestration service.

    Manages budget allocation, tracking, and risk aggregation
    across the M12 multi-agent system.
    """

    # Safety margin: stop workers 20 cents before true exhaustion
    DEFAULT_SAFETY_MARGIN_CENTS = 20

    def __init__(
        self,
        database_url: Optional[str] = None,
        safety_margin_cents: int = DEFAULT_SAFETY_MARGIN_CENTS,
    ):
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL required for GovernanceService")

        self.safety_margin_cents = safety_margin_cents

        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.Session = sessionmaker(bind=self.engine)

    # =========================================================================
    # Job-level operations
    # =========================================================================

    def get_job_budget_status(self, job_id: UUID) -> Optional[BudgetStatus]:
        """Get budget status for a job."""
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT
                        llm_budget_cents,
                        llm_budget_used,
                        llm_risk_violations
                    FROM agents.jobs
                    WHERE id = :job_id
                """),
                {"job_id": str(job_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            budget_cents, used_cents, _ = row
            remaining = (budget_cents - used_cents) if budget_cents else None

            return BudgetStatus(
                budget_cents=budget_cents,
                used_cents=used_cents or 0,
                remaining_cents=remaining,
                is_exceeded=budget_cents is not None and (used_cents or 0) >= budget_cents,
                utilization_pct=(
                    round((used_cents / budget_cents) * 100, 2)
                    if budget_cents and used_cents else None
                ),
            )

    def get_job_risk_metrics(self, job_id: UUID) -> Optional[RiskMetrics]:
        """Get risk metrics for a job."""
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT
                        COUNT(*) as total_items,
                        COUNT(*) FILTER (WHERE blocked = true) as blocked_items,
                        COALESCE(AVG(risk_score), 0) as avg_risk,
                        COALESCE(MAX(risk_score), 0) as max_risk,
                        COUNT(*) FILTER (WHERE risk_score < 0.3) as low_risk,
                        COUNT(*) FILTER (WHERE risk_score >= 0.3 AND risk_score < 0.6) as medium_risk,
                        COUNT(*) FILTER (WHERE risk_score >= 0.6) as high_risk
                    FROM agents.job_items
                    WHERE job_id = :job_id AND risk_score IS NOT NULL
                """),
                {"job_id": str(job_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            # Get violations count from job
            job_result = session.execute(
                text("SELECT llm_risk_violations FROM agents.jobs WHERE id = :job_id"),
                {"job_id": str(job_id)}
            )
            job_row = job_result.fetchone()
            violations = job_row[0] if job_row else 0

            return RiskMetrics(
                total_items=row[0] or 0,
                blocked_items=row[1] or 0,
                avg_risk_score=float(row[2] or 0),
                max_risk_score=float(row[3] or 0),
                risk_violations=violations or 0,
                risk_distribution={
                    "low": row[4] or 0,
                    "medium": row[5] or 0,
                    "high": row[6] or 0,
                },
            )

    def get_job_governance_status(self, job_id: UUID) -> Optional[GovernanceStatus]:
        """Get full governance status for a job."""
        budget = self.get_job_budget_status(job_id)
        risk = self.get_job_risk_metrics(job_id)

        if not budget:
            return None

        # Get config
        with self.Session() as session:
            result = session.execute(
                text("SELECT llm_config FROM agents.jobs WHERE id = :job_id"),
                {"job_id": str(job_id)}
            )
            row = result.fetchone()
            config = row[0] if row and row[0] else {}
            if isinstance(config, str):
                config = json.loads(config)

        return GovernanceStatus(
            job_id=job_id,
            budget=budget,
            risk=risk or RiskMetrics(
                total_items=0, blocked_items=0, avg_risk_score=0,
                max_risk_score=0, risk_violations=0, risk_distribution={}
            ),
            config=config,
        )

    def update_job_budget(
        self,
        job_id: UUID,
        cost_cents: float,
        blocked: bool = False,
    ) -> BudgetStatus:
        """
        Update job budget after LLM call.

        Args:
            job_id: Job ID
            cost_cents: Cost of the LLM call
            blocked: Whether the call was blocked

        Returns:
            Updated budget status
        """
        with self.Session() as session:
            session.execute(
                text("""
                    UPDATE agents.jobs
                    SET
                        llm_budget_used = llm_budget_used + :cost,
                        llm_risk_violations = llm_risk_violations + CASE WHEN :blocked THEN 1 ELSE 0 END
                    WHERE id = :job_id
                """),
                {
                    "job_id": str(job_id),
                    "cost": int(cost_cents),
                    "blocked": blocked,
                }
            )
            session.commit()

        return self.get_job_budget_status(job_id)

    # =========================================================================
    # Worker-level operations
    # =========================================================================

    def check_worker_budget(
        self,
        instance_id: str,
        estimated_cost_cents: int,
    ) -> WorkerBudgetCheck:
        """
        Check if worker has budget for an LLM call.

        Uses the SQL function: agents.check_worker_budget()
        Then applies safety margin on top.

        Args:
            instance_id: Worker instance ID
            estimated_cost_cents: Estimated cost of the call

        Returns:
            WorkerBudgetCheck with result
        """
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT can_proceed, budget_remaining, reason
                    FROM agents.check_worker_budget(:instance_id, :estimated_cost)
                """),
                {
                    "instance_id": instance_id,
                    "estimated_cost": estimated_cost_cents,
                }
            )
            row = result.fetchone()

            if not row:
                return WorkerBudgetCheck(
                    can_proceed=True,
                    budget_remaining=None,
                    reason="no_worker_found"
                )

            can_proceed = row[0]
            budget_remaining = row[1]
            reason = row[2]

            # Apply safety margin: stop if remaining < safety_margin + estimated_cost
            if budget_remaining is not None and can_proceed:
                effective_remaining = budget_remaining - self.safety_margin_cents
                if effective_remaining < estimated_cost_cents:
                    can_proceed = False
                    reason = f"safety_margin_exceeded (remaining={budget_remaining}, margin={self.safety_margin_cents})"

            return WorkerBudgetCheck(
                can_proceed=can_proceed,
                budget_remaining=budget_remaining,
                reason=reason,
            )

    def allocate_worker_budget(
        self,
        instance_id: str,
        job_id: UUID,
        budget_cents: Optional[int] = None,
    ) -> bool:
        """
        Allocate budget to a worker from job envelope.

        Args:
            instance_id: Worker instance ID
            job_id: Job to allocate from
            budget_cents: Specific budget (None = equal share of remaining)

        Returns:
            True if allocation successful
        """
        with self.Session() as session:
            # Get job budget info
            job_result = session.execute(
                text("""
                    SELECT llm_budget_cents, llm_budget_used, config
                    FROM agents.jobs WHERE id = :job_id
                """),
                {"job_id": str(job_id)}
            )
            job_row = job_result.fetchone()

            if not job_row:
                return False

            job_budget, job_used, config = job_row
            if isinstance(config, str):
                config = json.loads(config)

            # Calculate worker budget
            worker_budget = budget_cents
            if worker_budget is None and job_budget:
                # Get per-item budget from config or calculate
                worker_budget = config.get("llm_budget_per_item")
                if not worker_budget:
                    # Equal share of remaining
                    remaining = (job_budget - (job_used or 0))
                    parallelism = config.get("parallelism", 1)
                    worker_budget = max(1, remaining // parallelism)

            # Update worker
            llm_config = {
                "job_id": str(job_id),
                "risk_threshold": config.get("risk_threshold", 0.6),
                "max_temperature": config.get("max_temperature", 1.0),
                "enforce_safety": config.get("enforce_safety", True),
            }

            session.execute(
                text("""
                    UPDATE agents.instances
                    SET
                        llm_budget_cents = :budget,
                        llm_config = CAST(:config AS JSONB)
                    WHERE instance_id = :instance_id
                """),
                {
                    "instance_id": instance_id,
                    "budget": worker_budget,
                    "config": json.dumps(llm_config),
                }
            )
            session.commit()

            logger.info(
                "worker_budget_allocated",
                extra={
                    "instance_id": instance_id,
                    "job_id": str(job_id),
                    "budget_cents": worker_budget,
                }
            )

            return True

    def get_worker_budget_status(self, instance_id: str) -> Optional[BudgetStatus]:
        """Get budget status for a worker."""
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT
                        llm_budget_cents,
                        llm_budget_used,
                        llm_risk_violations
                    FROM agents.instances
                    WHERE instance_id = :instance_id
                """),
                {"instance_id": instance_id}
            )
            row = result.fetchone()

            if not row:
                return None

            budget_cents, used_cents, _ = row
            remaining = (budget_cents - used_cents) if budget_cents else None

            return BudgetStatus(
                budget_cents=budget_cents,
                used_cents=used_cents or 0,
                remaining_cents=remaining,
                is_exceeded=budget_cents is not None and (used_cents or 0) >= budget_cents,
                utilization_pct=(
                    round((used_cents / budget_cents) * 100, 2)
                    if budget_cents and used_cents else None
                ),
            )

    # =========================================================================
    # Item-level operations
    # =========================================================================

    def record_item_llm_usage(
        self,
        item_id: UUID,
        cost_cents: float,
        tokens_used: int,
        risk_score: float,
        risk_factors: Dict[str, Any],
        blocked: bool,
        blocked_reason: Optional[str],
        params_clamped: Dict[str, Any],
    ) -> bool:
        """
        Record LLM usage for a job item.

        Uses the SQL function: agents.record_llm_usage()

        Args:
            item_id: Job item ID
            cost_cents: Cost in cents
            tokens_used: Total tokens used
            risk_score: Calculated risk score
            risk_factors: Risk factor breakdown
            blocked: Whether output was blocked
            blocked_reason: Reason for blocking
            params_clamped: Parameters that were clamped

        Returns:
            True if recording successful
        """
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT agents.record_llm_usage(
                        :item_id,
                        :cost_cents,
                        :tokens,
                        :risk_score,
                        CAST(:risk_factors AS JSONB),
                        :blocked,
                        :blocked_reason,
                        CAST(:params_clamped AS JSONB)
                    )
                """),
                {
                    "item_id": str(item_id),
                    "cost_cents": cost_cents,
                    "tokens": tokens_used,
                    "risk_score": risk_score,
                    "risk_factors": json.dumps(risk_factors),
                    "blocked": blocked,
                    "blocked_reason": blocked_reason,
                    "params_clamped": json.dumps(params_clamped),
                }
            )
            session.commit()

            return True

    # =========================================================================
    # Aggregation and reporting
    # =========================================================================

    def get_governance_summary(
        self,
        tenant_id: str = "default",
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get governance summary for dashboard.

        Args:
            tenant_id: Tenant to summarize
            time_range_hours: Time range for metrics

        Returns:
            Summary dict with budget and risk metrics
        """
        with self.Session() as session:
            # Job-level aggregations
            result = session.execute(
                text("""
                    SELECT
                        COUNT(*) as total_jobs,
                        SUM(llm_budget_cents) as total_budget,
                        SUM(llm_budget_used) as total_used,
                        SUM(llm_risk_violations) as total_violations
                    FROM agents.jobs
                    WHERE tenant_id = :tenant_id
                      AND created_at >= now() - interval ':hours hours'
                """.replace(":hours", str(time_range_hours))),
                {"tenant_id": tenant_id}
            )
            job_row = result.fetchone()

            # Item-level aggregations
            item_result = session.execute(
                text("""
                    SELECT
                        COUNT(*) as total_items,
                        COUNT(*) FILTER (WHERE blocked = true) as blocked_items,
                        COALESCE(AVG(risk_score), 0) as avg_risk,
                        SUM(llm_cost_cents) as total_cost,
                        SUM(llm_tokens_used) as total_tokens
                    FROM agents.job_items ji
                    JOIN agents.jobs j ON ji.job_id = j.id
                    WHERE j.tenant_id = :tenant_id
                      AND j.created_at >= now() - interval ':hours hours'
                """.replace(":hours", str(time_range_hours))),
                {"tenant_id": tenant_id}
            )
            item_row = item_result.fetchone()

            return {
                "time_range_hours": time_range_hours,
                "jobs": {
                    "total": job_row[0] or 0 if job_row else 0,
                    "total_budget_cents": job_row[1] or 0 if job_row else 0,
                    "total_used_cents": job_row[2] or 0 if job_row else 0,
                    "total_violations": job_row[3] or 0 if job_row else 0,
                },
                "items": {
                    "total": item_row[0] or 0 if item_row else 0,
                    "blocked": item_row[1] or 0 if item_row else 0,
                    "avg_risk_score": float(item_row[2] or 0) if item_row else 0,
                    "total_cost_cents": float(item_row[3] or 0) if item_row else 0,
                    "total_tokens": item_row[4] or 0 if item_row else 0,
                },
                "utilization_pct": (
                    round((job_row[2] / job_row[1]) * 100, 2)
                    if job_row and job_row[1] else None
                ),
            }

    def get_high_risk_items(
        self,
        job_id: Optional[UUID] = None,
        risk_threshold: float = 0.6,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get high-risk items for review."""
        with self.Session() as session:
            query = """
                SELECT
                    ji.id,
                    ji.job_id,
                    ji.item_index,
                    ji.risk_score,
                    ji.risk_factors,
                    ji.blocked,
                    ji.blocked_reason,
                    ji.llm_cost_cents
                FROM agents.job_items ji
                WHERE ji.risk_score >= :threshold
            """
            params = {"threshold": risk_threshold, "limit": limit}

            if job_id:
                query += " AND ji.job_id = :job_id"
                params["job_id"] = str(job_id)

            query += " ORDER BY ji.risk_score DESC LIMIT :limit"

            result = session.execute(text(query), params)

            items = []
            for row in result:
                items.append({
                    "id": str(row[0]),
                    "job_id": str(row[1]),
                    "item_index": row[2],
                    "risk_score": float(row[3]) if row[3] else 0,
                    "risk_factors": row[4] if isinstance(row[4], dict) else {},
                    "blocked": row[5],
                    "blocked_reason": row[6],
                    "cost_cents": float(row[7]) if row[7] else 0,
                })

            return items

    # =========================================================================
    # Aggregator Governance Hooks
    # =========================================================================

    def get_job_outputs_filtered(
        self,
        job_id: UUID,
        exclude_blocked: bool = True,
        min_risk_threshold: Optional[float] = None,
        max_risk_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get job item outputs filtered by governance criteria.

        Used by aggregators to exclude blocked items from final results.

        Args:
            job_id: Job ID
            exclude_blocked: Exclude blocked items (default True)
            min_risk_threshold: Only include items above this risk (optional)
            max_risk_threshold: Only include items below this risk (optional)

        Returns:
            List of item outputs that passed governance filters
        """
        with self.Session() as session:
            # Build query with governance filters
            query = """
                SELECT
                    ji.id,
                    ji.item_index,
                    ji.output,
                    ji.risk_score,
                    ji.blocked,
                    ji.blocked_reason,
                    ji.llm_cost_cents,
                    ji.status
                FROM agents.job_items ji
                WHERE ji.job_id = :job_id
                  AND ji.status = 'completed'
            """
            params: Dict[str, Any] = {"job_id": str(job_id)}

            if exclude_blocked:
                query += " AND (ji.blocked = false OR ji.blocked IS NULL)"

            if min_risk_threshold is not None:
                query += " AND (ji.risk_score >= :min_risk OR ji.risk_score IS NULL)"
                params["min_risk"] = min_risk_threshold

            if max_risk_threshold is not None:
                query += " AND (ji.risk_score <= :max_risk OR ji.risk_score IS NULL)"
                params["max_risk"] = max_risk_threshold

            query += " ORDER BY ji.item_index ASC"

            result = session.execute(text(query), params)

            items = []
            for row in result:
                output = row[2]
                if isinstance(output, str):
                    try:
                        output = json.loads(output)
                    except json.JSONDecodeError:
                        pass

                items.append({
                    "id": str(row[0]),
                    "item_index": row[1],
                    "output": output,
                    "risk_score": float(row[3]) if row[3] is not None else None,
                    "blocked": row[4] or False,
                    "blocked_reason": row[5],
                    "cost_cents": float(row[6]) if row[6] else 0,
                    "status": row[7],
                })

            return items

    def get_worker_cost_breakdown(
        self,
        job_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Get per-worker cost breakdown for visualization.

        Returns cost, tokens, and risk stats per worker instance.

        Args:
            job_id: Job ID

        Returns:
            List of worker stats with cost breakdown
        """
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT
                        i.instance_id,
                        i.agent_name,
                        i.llm_budget_cents,
                        i.llm_budget_used,
                        i.llm_risk_violations,
                        COUNT(ji.id) as items_processed,
                        SUM(ji.llm_cost_cents) as total_item_cost,
                        SUM(ji.llm_tokens_used) as total_tokens,
                        AVG(ji.risk_score) as avg_risk,
                        COUNT(*) FILTER (WHERE ji.blocked = true) as blocked_count
                    FROM agents.instances i
                    LEFT JOIN agents.job_items ji ON ji.worker_instance_id = i.instance_id
                    WHERE EXISTS (
                        SELECT 1 FROM agents.job_items ji2
                        WHERE ji2.job_id = :job_id AND ji2.worker_instance_id = i.instance_id
                    )
                    GROUP BY i.instance_id, i.agent_name, i.llm_budget_cents,
                             i.llm_budget_used, i.llm_risk_violations
                    ORDER BY i.instance_id
                """),
                {"job_id": str(job_id)}
            )

            workers = []
            for row in result:
                budget = row[2]
                used = row[3] or 0
                workers.append({
                    "instance_id": row[0],
                    "agent_name": row[1],
                    "budget_cents": budget,
                    "budget_used_cents": used,
                    "budget_remaining_cents": (budget - used) if budget else None,
                    "utilization_pct": round((used / budget) * 100, 2) if budget else None,
                    "risk_violations": row[4] or 0,
                    "items_processed": row[5] or 0,
                    "total_cost_cents": float(row[6]) if row[6] else 0,
                    "total_tokens": row[7] or 0,
                    "avg_risk_score": float(row[8]) if row[8] else 0,
                    "blocked_items": row[9] or 0,
                })

            return workers

    def get_risk_distribution(
        self,
        job_id: UUID,
        buckets: int = 10,
    ) -> Dict[str, Any]:
        """
        Get risk score distribution for a job.

        Returns histogram data for dashboard visualization.

        Args:
            job_id: Job ID
            buckets: Number of histogram buckets (default 10)

        Returns:
            Dict with distribution data
        """
        with self.Session() as session:
            # Get raw risk scores
            result = session.execute(
                text("""
                    SELECT
                        risk_score,
                        blocked,
                        llm_cost_cents
                    FROM agents.job_items
                    WHERE job_id = :job_id AND risk_score IS NOT NULL
                    ORDER BY risk_score
                """),
                {"job_id": str(job_id)}
            )

            scores = []
            blocked_scores = []
            total_cost = 0.0
            for row in result:
                risk = float(row[0]) if row[0] is not None else 0
                scores.append(risk)
                if row[1]:  # blocked
                    blocked_scores.append(risk)
                total_cost += float(row[2]) if row[2] else 0

            if not scores:
                return {
                    "job_id": str(job_id),
                    "total_items": 0,
                    "histogram": [],
                    "blocked_histogram": [],
                    "percentiles": {},
                    "stats": {},
                }

            # Build histogram buckets
            bucket_size = 1.0 / buckets
            histogram = []
            blocked_histogram = []

            for i in range(buckets):
                lower = i * bucket_size
                upper = (i + 1) * bucket_size
                bucket_label = f"{lower:.1f}-{upper:.1f}"

                count = sum(1 for s in scores if lower <= s < upper)
                blocked_count = sum(1 for s in blocked_scores if lower <= s < upper)

                histogram.append({"bucket": bucket_label, "count": count})
                blocked_histogram.append({"bucket": bucket_label, "count": blocked_count})

            # Calculate percentiles
            sorted_scores = sorted(scores)
            n = len(sorted_scores)
            percentiles = {
                "p50": sorted_scores[int(n * 0.5)] if n > 0 else 0,
                "p75": sorted_scores[int(n * 0.75)] if n > 0 else 0,
                "p90": sorted_scores[int(n * 0.90)] if n > 0 else 0,
                "p95": sorted_scores[int(n * 0.95)] if n > 0 else 0,
                "p99": sorted_scores[int(n * 0.99)] if n > 0 else 0,
            }

            # Calculate stats
            avg = sum(scores) / n if n > 0 else 0
            stats = {
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "avg": avg,
                "total_cost_cents": total_cost,
                "blocked_count": len(blocked_scores),
                "blocked_pct": round((len(blocked_scores) / n) * 100, 2) if n > 0 else 0,
            }

            return {
                "job_id": str(job_id),
                "total_items": n,
                "histogram": histogram,
                "blocked_histogram": blocked_histogram,
                "percentiles": percentiles,
                "stats": stats,
            }

    def get_aggregation_summary(
        self,
        job_id: UUID,
    ) -> Dict[str, Any]:
        """
        Get complete aggregation summary with governance data.

        This is the primary hook for aggregators to understand
        job health before combining outputs.

        Args:
            job_id: Job ID

        Returns:
            Complete aggregation summary
        """
        budget = self.get_job_budget_status(job_id)
        risk = self.get_job_risk_metrics(job_id)
        workers = self.get_worker_cost_breakdown(job_id)
        distribution = self.get_risk_distribution(job_id)

        # Get filtered outputs (non-blocked only)
        filtered_outputs = self.get_job_outputs_filtered(job_id, exclude_blocked=True)

        with self.Session() as session:
            # Get total items count
            result = session.execute(
                text("""
                    SELECT
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'completed') as completed,
                        COUNT(*) FILTER (WHERE blocked = true) as blocked
                    FROM agents.job_items
                    WHERE job_id = :job_id
                """),
                {"job_id": str(job_id)}
            )
            row = result.fetchone()

        total_items = row[0] if row else 0
        completed_items = row[1] if row else 0
        blocked_items = row[2] if row else 0

        return {
            "job_id": str(job_id),
            "aggregation": {
                "total_items": total_items,
                "completed_items": completed_items,
                "blocked_items": blocked_items,
                "usable_items": len(filtered_outputs),
                "usable_pct": round((len(filtered_outputs) / completed_items) * 100, 2) if completed_items > 0 else 0,
            },
            "budget": {
                "total_cents": budget.budget_cents if budget else None,
                "used_cents": budget.used_cents if budget else 0,
                "remaining_cents": budget.remaining_cents if budget else None,
                "utilization_pct": budget.utilization_pct if budget else None,
                "is_exceeded": budget.is_exceeded if budget else False,
            },
            "risk": {
                "avg_score": risk.avg_risk_score if risk else 0,
                "max_score": risk.max_risk_score if risk else 0,
                "violations": risk.risk_violations if risk else 0,
                "distribution": risk.risk_distribution if risk else {},
            },
            "workers": {
                "count": len(workers),
                "breakdown": workers,
            },
            "risk_histogram": distribution,
        }


# =============================================================================
# Singleton
# =============================================================================

_service: Optional[GovernanceService] = None


def get_governance_service() -> GovernanceService:
    """Get singleton governance service instance."""
    global _service
    if _service is None:
        _service = GovernanceService()
    return _service
