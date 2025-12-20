# Budget Tracker
# Tracks LLM costs and enforces budget limits per agent/tenant
# Phase 5: Budget Protection Layer (BPL)

import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlmodel import Session, text

from ..db import Agent, engine

logger = logging.getLogger("nova.utils.budget_tracker")

# Alert threshold percentage (default 80%)
BUDGET_ALERT_THRESHOLD = float(os.getenv("BUDGET_ALERT_THRESHOLD", "0.8"))

# ==================== BUDGET PROTECTION LAYER CONFIG ====================
# Per-run limits (prevent single run from consuming too much)
PER_RUN_MAX_CENTS = int(os.getenv("PER_RUN_MAX_CENTS", "500"))  # $5 per run

# Per-day rolling limits (prevent daily runaway costs)
PER_DAY_MAX_CENTS = int(os.getenv("PER_DAY_MAX_CENTS", "10000"))  # $100 per day

# Per-model limits (prevent expensive model abuse)
PER_MODEL_LIMITS: Dict[str, int] = {
    "claude-3-opus-20240229": int(os.getenv("OPUS_MAX_CENTS_PER_RUN", "1000")),
    "gpt-4-turbo": int(os.getenv("GPT4_MAX_CENTS_PER_RUN", "500")),
    # Sonnet/Haiku use default PER_RUN_MAX_CENTS
}

# Auto-pause behavior
AUTO_PAUSE_ON_BREACH = os.getenv("AUTO_PAUSE_ON_BREACH", "true").lower() == "true"


@dataclass
class BudgetStatus:
    """Current budget status for an agent."""

    budget_cents: int
    spent_cents: int
    remaining_cents: int
    usage_percent: float
    is_exhausted: bool
    is_alert_threshold: bool
    today_spent_cents: int = 0
    is_paused: bool = False


@dataclass
class BudgetCheckResult:
    """Result of a budget enforcement check."""

    allowed: bool
    reason: Optional[str] = None
    breach_type: Optional[str] = None  # "per_run", "per_day", "per_model", "total_budget"
    limit_cents: int = 0
    current_cents: int = 0


class BudgetTracker:
    """Tracks and enforces LLM cost budgets.

    Provides atomic budget deduction and cost recording.
    Supports alert thresholds for proactive notification.
    """

    def __init__(self, alert_threshold: float = BUDGET_ALERT_THRESHOLD):
        """Initialize budget tracker.

        Args:
            alert_threshold: Percentage (0-1) at which to trigger alerts
        """
        self.alert_threshold = alert_threshold

    def get_status(self, agent_id: str) -> Optional[BudgetStatus]:
        """Get current budget status for an agent.

        Args:
            agent_id: Agent ID to check

        Returns:
            BudgetStatus or None if agent not found
        """
        with Session(engine) as session:
            agent = session.get(Agent, agent_id)
            if not agent:
                return None

            budget = agent.budget_cents or 0
            spent = agent.spent_cents or 0
            remaining = budget - spent

            usage_percent = (spent / budget * 100) if budget > 0 else 0

            # Get today's spending from llm_costs table
            today_spent = self._get_today_spent(session, agent_id)

            # Check if agent is paused
            is_paused = getattr(agent, "is_paused", False)

            return BudgetStatus(
                budget_cents=budget,
                spent_cents=spent,
                remaining_cents=max(0, remaining),
                usage_percent=usage_percent,
                is_exhausted=remaining <= 0 and budget > 0,
                is_alert_threshold=usage_percent >= (self.alert_threshold * 100),
                today_spent_cents=today_spent,
                is_paused=is_paused,
            )

    def _get_today_spent(self, session: Session, agent_id: str) -> int:
        """Get total spent today from llm_costs table."""
        try:
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            query = text(
                """
                SELECT COALESCE(SUM(cost_cents), 0) as total
                FROM llm_costs
                WHERE agent_id = :agent_id AND created_at >= :today_start
            """
            )
            result = session.exec(query, {"agent_id": agent_id, "today_start": today_start})
            row = result.first()
            return int(row[0]) if row else 0
        except Exception:
            # Table might not exist
            return 0

    def check_budget(
        self,
        agent_id: str,
        estimated_cost_cents: int,
    ) -> tuple[bool, Optional[str]]:
        """Check if agent has sufficient budget for estimated cost.

        Args:
            agent_id: Agent to check
            estimated_cost_cents: Estimated cost of the operation

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        result = self.enforce_budget(agent_id, estimated_cost_cents)
        return result.allowed, result.reason

    def enforce_budget(
        self,
        agent_id: str,
        estimated_cost_cents: int,
        model: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> BudgetCheckResult:
        """Full budget enforcement with all protection layers.

        Args:
            agent_id: Agent to check
            estimated_cost_cents: Estimated cost of the operation
            model: Optional model name for per-model limits
            run_id: Optional run ID for per-run tracking

        Returns:
            BudgetCheckResult with detailed breach information
        """
        # 1. Check per-run limit FIRST (global limit, applies to all agents)
        if estimated_cost_cents > PER_RUN_MAX_CENTS:
            logger.warning(
                "budget_per_run_exceeded",
                extra={
                    "agent_id": agent_id,
                    "estimated_cost": estimated_cost_cents,
                    "limit": PER_RUN_MAX_CENTS,
                },
            )
            return BudgetCheckResult(
                allowed=False,
                reason=f"Estimated cost ({estimated_cost_cents}c) exceeds per-run limit ({PER_RUN_MAX_CENTS}c)",
                breach_type="per_run",
                limit_cents=PER_RUN_MAX_CENTS,
                current_cents=estimated_cost_cents,
            )

        # 2. Check per-model limit (global limit)
        if model and model in PER_MODEL_LIMITS:
            model_limit = PER_MODEL_LIMITS[model]
            if estimated_cost_cents > model_limit:
                logger.warning(
                    "budget_per_model_exceeded",
                    extra={
                        "agent_id": agent_id,
                        "model": model,
                        "estimated_cost": estimated_cost_cents,
                        "limit": model_limit,
                    },
                )
                return BudgetCheckResult(
                    allowed=False,
                    reason=f"Model {model} cost ({estimated_cost_cents}c) exceeds limit ({model_limit}c)",
                    breach_type="per_model",
                    limit_cents=model_limit,
                    current_cents=estimated_cost_cents,
                )

        # Now check agent-specific limits
        status = self.get_status(agent_id)

        if status is None:
            return BudgetCheckResult(allowed=True)

        # Check if agent is paused
        if status.is_paused:
            return BudgetCheckResult(
                allowed=False,
                reason="Agent is paused due to budget breach",
                breach_type="paused",
            )

        # 3. Check per-day limit (agent-specific)
        projected_today = status.today_spent_cents + estimated_cost_cents
        if projected_today > PER_DAY_MAX_CENTS:
            logger.warning(
                "budget_per_day_exceeded",
                extra={
                    "agent_id": agent_id,
                    "today_spent": status.today_spent_cents,
                    "estimated_cost": estimated_cost_cents,
                    "projected": projected_today,
                    "limit": PER_DAY_MAX_CENTS,
                },
            )
            # Auto-pause agent if configured
            if AUTO_PAUSE_ON_BREACH:
                self._pause_agent(agent_id, "per_day_limit_exceeded")

            return BudgetCheckResult(
                allowed=False,
                reason=f"Daily spending ({projected_today}c) would exceed limit ({PER_DAY_MAX_CENTS}c)",
                breach_type="per_day",
                limit_cents=PER_DAY_MAX_CENTS,
                current_cents=status.today_spent_cents,
            )

        # 4. Check total budget
        if status.budget_cents == 0:
            return BudgetCheckResult(allowed=True)  # No budget configured

        if status.is_exhausted:
            return BudgetCheckResult(
                allowed=False,
                reason="Budget exhausted",
                breach_type="total_budget",
                limit_cents=status.budget_cents,
                current_cents=status.spent_cents,
            )

        if status.remaining_cents < estimated_cost_cents:
            return BudgetCheckResult(
                allowed=False,
                reason=f"Insufficient budget: {status.remaining_cents}c remaining, need {estimated_cost_cents}c",
                breach_type="total_budget",
                limit_cents=status.budget_cents,
                current_cents=status.spent_cents,
            )

        # Log alert threshold warning
        if status.is_alert_threshold:
            logger.warning(
                "budget_alert_threshold",
                extra={
                    "agent_id": agent_id,
                    "usage_percent": status.usage_percent,
                    "remaining_cents": status.remaining_cents,
                },
            )

        return BudgetCheckResult(allowed=True)

    def _pause_agent(self, agent_id: str, reason: str):
        """Pause an agent due to budget breach."""
        try:
            with Session(engine) as session:
                # Try to set is_paused flag (column may not exist)
                query = text(
                    """
                    UPDATE agents SET is_paused = true WHERE id = :agent_id
                """
                )
                session.exec(query, {"agent_id": agent_id})
                session.commit()

                logger.warning("agent_paused_budget_breach", extra={"agent_id": agent_id, "reason": reason})
        except Exception as e:
            # Column might not exist, log but continue
            logger.warning("agent_pause_failed", extra={"agent_id": agent_id, "error": str(e)[:100]})

    def deduct(
        self,
        agent_id: str,
        cost_cents: int,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Atomically deduct cost from agent budget.

        Args:
            agent_id: Agent to deduct from
            cost_cents: Cost to deduct
            tenant_id: Optional tenant filter for safety

        Returns:
            True if deduction successful, False if budget would go negative
        """
        with Session(engine) as session:
            # Use raw SQL for atomic update with check
            query = text(
                """
                UPDATE agents
                SET spent_cents = spent_cents + :cost
                WHERE id = :agent_id
                AND (budget_cents = 0 OR budget_cents - spent_cents >= :cost)
                RETURNING id, budget_cents, spent_cents
            """
            )

            if tenant_id:
                query = text(
                    """
                    UPDATE agents
                    SET spent_cents = spent_cents + :cost
                    WHERE id = :agent_id
                    AND tenant_id = :tenant_id
                    AND (budget_cents = 0 OR budget_cents - spent_cents >= :cost)
                    RETURNING id, budget_cents, spent_cents
                """
                )
                result = session.execute(query, {"agent_id": agent_id, "cost": cost_cents, "tenant_id": tenant_id})
            else:
                result = session.execute(query, {"agent_id": agent_id, "cost": cost_cents})

            row = result.first()
            session.commit()

            if row:
                logger.info(
                    "budget_deducted",
                    extra={
                        "agent_id": agent_id,
                        "cost_cents": cost_cents,
                        "new_spent": row[2],
                        "budget": row[1],
                    },
                )
                return True
            else:
                logger.warning("budget_deduction_failed", extra={"agent_id": agent_id, "cost_cents": cost_cents})
                return False

    def record_cost(
        self,
        run_id: str,
        agent_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_cents: int,
    ):
        """Record LLM cost for auditing.

        Stores cost record in llm_costs table (if exists).
        Falls back to logging if table doesn't exist.
        """
        try:
            with Session(engine) as session:
                # Try to insert into llm_costs table
                query = text(
                    """
                    INSERT INTO llm_costs (id, run_id, agent_id, provider, model, input_tokens, output_tokens, cost_cents, created_at)
                    VALUES (:id, :run_id, :agent_id, :provider, :model, :input_tokens, :output_tokens, :cost_cents, :created_at)
                """
                )
                session.exec(
                    query,
                    {
                        "id": str(uuid.uuid4()),
                        "run_id": run_id,
                        "agent_id": agent_id,
                        "provider": provider,
                        "model": model,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cost_cents": cost_cents,
                        "created_at": datetime.now(timezone.utc),
                    },
                )
                session.commit()

        except Exception as e:
            # Table might not exist yet, just log
            logger.info(
                "llm_cost_recorded",
                extra={
                    "run_id": run_id,
                    "agent_id": agent_id,
                    "provider": provider,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_cents": cost_cents,
                    "error": str(e)[:100] if "llm_costs" not in str(e) else "table_missing",
                },
            )


# Singleton instance
_tracker: Optional[BudgetTracker] = None


def get_budget_tracker() -> BudgetTracker:
    """Get the singleton budget tracker."""
    global _tracker
    if _tracker is None:
        _tracker = BudgetTracker()
    return _tracker


def check_budget(agent_id: str, estimated_cost_cents: int) -> tuple[bool, Optional[str]]:
    """Convenience function to check budget."""
    return get_budget_tracker().check_budget(agent_id, estimated_cost_cents)


def deduct_budget(agent_id: str, cost_cents: int, tenant_id: Optional[str] = None) -> bool:
    """Convenience function to deduct budget."""
    return get_budget_tracker().deduct(agent_id, cost_cents, tenant_id)


def record_cost(
    run_id: str,
    agent_id: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_cents: int,
):
    """Convenience function to record cost."""
    get_budget_tracker().record_cost(run_id, agent_id, provider, model, input_tokens, output_tokens, cost_cents)


def enforce_budget(
    agent_id: str,
    estimated_cost_cents: int,
    model: Optional[str] = None,
    run_id: Optional[str] = None,
) -> BudgetCheckResult:
    """Full budget enforcement with all protection layers.

    This is the main entry point for Phase 5 budget protection.
    Checks: per-run, per-model, per-day, and total budget limits.
    """
    return get_budget_tracker().enforce_budget(agent_id, estimated_cost_cents, model, run_id)
