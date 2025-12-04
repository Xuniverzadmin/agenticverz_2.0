# app/observability/cost_tracker.py
"""
Cost Tracking and Quota Management

Tracks LLM spend per tenant, workflow, and skill.
Provides alerting when budgets are approached/exceeded.
Enforces hard cost ceilings at workflow and tenant levels.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional
from collections import defaultdict
from enum import Enum
import threading


class CostEnforcementResult(Enum):
    """Result of cost enforcement check."""
    ALLOWED = "allowed"
    BUDGET_WARNING = "budget_warning"  # Approaching limit
    BUDGET_EXCEEDED = "budget_exceeded"  # Hard limit hit
    REQUEST_TOO_EXPENSIVE = "request_too_expensive"  # Single request exceeds limit


@dataclass
class CostQuota:
    """Cost quota configuration."""
    daily_limit_cents: int = 10000  # $100/day default
    hourly_limit_cents: int = 1000  # $10/hour default
    per_request_limit_cents: int = 100  # $1/request default
    per_workflow_limit_cents: int = 500  # $5/workflow default
    warn_threshold_percent: float = 0.8  # Warn at 80%
    enforce_hard_limit: bool = True  # If True, reject requests that exceed budget


@dataclass
class CostRecord:
    """Individual cost record."""
    timestamp: datetime
    tenant_id: str
    workflow_id: str
    skill_id: str
    cost_cents: float
    input_tokens: int
    output_tokens: int
    model: str


@dataclass
class CostAlert:
    """Cost alert notification."""
    level: str  # "warn", "critical", "exceeded"
    message: str
    tenant_id: str
    current_spend_cents: float
    limit_cents: int
    period: str  # "hourly", "daily"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CostTracker:
    """
    Tracks LLM costs and enforces quotas.

    Thread-safe for concurrent access.
    """

    def __init__(self, quota: Optional[CostQuota] = None):
        self.quota = quota or CostQuota()
        self._records: list[CostRecord] = []
        self._lock = threading.Lock()
        self._alerts: list[CostAlert] = []

        # In-memory aggregates for quick lookups
        self._hourly_spend: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._daily_spend: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def record_cost(
        self,
        tenant_id: str,
        workflow_id: str,
        skill_id: str,
        cost_cents: float,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> list[CostAlert]:
        """
        Record a cost event and return any triggered alerts.
        """
        now = datetime.now(timezone.utc)
        record = CostRecord(
            timestamp=now,
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            skill_id=skill_id,
            cost_cents=cost_cents,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model
        )

        alerts = []

        with self._lock:
            self._records.append(record)

            # Update aggregates
            hour_key = now.strftime("%Y-%m-%d-%H")
            day_key = now.strftime("%Y-%m-%d")

            self._hourly_spend[hour_key][tenant_id] += cost_cents
            self._daily_spend[day_key][tenant_id] += cost_cents

            # Check quotas
            hourly = self._hourly_spend[hour_key][tenant_id]
            daily = self._daily_spend[day_key][tenant_id]

            # Per-request check
            if cost_cents > self.quota.per_request_limit_cents:
                alerts.append(CostAlert(
                    level="critical",
                    message=f"Single request cost ({cost_cents:.2f}c) exceeds limit ({self.quota.per_request_limit_cents}c)",
                    tenant_id=tenant_id,
                    current_spend_cents=cost_cents,
                    limit_cents=self.quota.per_request_limit_cents,
                    period="request"
                ))

            # Hourly check
            if hourly >= self.quota.hourly_limit_cents:
                alerts.append(CostAlert(
                    level="exceeded",
                    message=f"Hourly budget exceeded: {hourly:.2f}c / {self.quota.hourly_limit_cents}c",
                    tenant_id=tenant_id,
                    current_spend_cents=hourly,
                    limit_cents=self.quota.hourly_limit_cents,
                    period="hourly"
                ))
            elif hourly >= self.quota.hourly_limit_cents * self.quota.warn_threshold_percent:
                alerts.append(CostAlert(
                    level="warn",
                    message=f"Hourly budget warning: {hourly:.2f}c / {self.quota.hourly_limit_cents}c",
                    tenant_id=tenant_id,
                    current_spend_cents=hourly,
                    limit_cents=self.quota.hourly_limit_cents,
                    period="hourly"
                ))

            # Daily check
            if daily >= self.quota.daily_limit_cents:
                alerts.append(CostAlert(
                    level="exceeded",
                    message=f"Daily budget exceeded: {daily:.2f}c / {self.quota.daily_limit_cents}c",
                    tenant_id=tenant_id,
                    current_spend_cents=daily,
                    limit_cents=self.quota.daily_limit_cents,
                    period="daily"
                ))
            elif daily >= self.quota.daily_limit_cents * self.quota.warn_threshold_percent:
                alerts.append(CostAlert(
                    level="warn",
                    message=f"Daily budget warning: {daily:.2f}c / {self.quota.daily_limit_cents}c",
                    tenant_id=tenant_id,
                    current_spend_cents=daily,
                    limit_cents=self.quota.daily_limit_cents,
                    period="daily"
                ))

            self._alerts.extend(alerts)

        return alerts

    def get_spend(
        self,
        tenant_id: str,
        period: str = "daily"
    ) -> float:
        """Get current spend for tenant."""
        now = datetime.now(timezone.utc)

        with self._lock:
            if period == "hourly":
                key = now.strftime("%Y-%m-%d-%H")
                return self._hourly_spend.get(key, {}).get(tenant_id, 0.0)
            else:  # daily
                key = now.strftime("%Y-%m-%d")
                return self._daily_spend.get(key, {}).get(tenant_id, 0.0)

    def get_remaining_budget(
        self,
        tenant_id: str,
        period: str = "daily"
    ) -> float:
        """Get remaining budget for tenant."""
        current = self.get_spend(tenant_id, period)
        if period == "hourly":
            return max(0, self.quota.hourly_limit_cents - current)
        return max(0, self.quota.daily_limit_cents - current)

    def is_budget_exceeded(
        self,
        tenant_id: str,
        period: str = "daily"
    ) -> bool:
        """Check if budget is exceeded."""
        return self.get_remaining_budget(tenant_id, period) <= 0

    def get_alerts(
        self,
        tenant_id: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> list[CostAlert]:
        """Get alerts, optionally filtered."""
        with self._lock:
            alerts = self._alerts.copy()

        if tenant_id:
            alerts = [a for a in alerts if a.tenant_id == tenant_id]
        if since:
            alerts = [a for a in alerts if a.timestamp >= since]

        return alerts

    def get_cost_summary(
        self,
        tenant_id: str,
        days: int = 7
    ) -> dict:
        """Get cost summary for tenant."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=days)

        with self._lock:
            records = [r for r in self._records
                      if r.tenant_id == tenant_id and r.timestamp >= cutoff]

        total_cost = sum(r.cost_cents for r in records)
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)

        # By skill
        by_skill: dict[str, float] = defaultdict(float)
        for r in records:
            by_skill[r.skill_id] += r.cost_cents

        # By model
        by_model: dict[str, float] = defaultdict(float)
        for r in records:
            by_model[r.model] += r.cost_cents

        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_cost_cents": total_cost,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "request_count": len(records),
            "by_skill": dict(by_skill),
            "by_model": dict(by_model),
            "current_daily_spend": self.get_spend(tenant_id, "daily"),
            "daily_budget_remaining": self.get_remaining_budget(tenant_id, "daily"),
            "current_hourly_spend": self.get_spend(tenant_id, "hourly"),
            "hourly_budget_remaining": self.get_remaining_budget(tenant_id, "hourly")
        }

    def cleanup_old_records(self, days: int = 30) -> int:
        """Remove records older than specified days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        with self._lock:
            before = len(self._records)
            self._records = [r for r in self._records if r.timestamp >= cutoff]
            removed = before - len(self._records)

        return removed

    # =========================================================================
    # HARD COST ENFORCEMENT
    # =========================================================================

    def check_can_spend(
        self,
        tenant_id: str,
        estimated_cost_cents: float,
        workflow_id: Optional[str] = None
    ) -> tuple[CostEnforcementResult, str]:
        """
        Check if a request with estimated cost can proceed.

        This is the PRE-REQUEST enforcement gate. Call before executing
        any cost-incurring operation.

        Args:
            tenant_id: Tenant making the request
            estimated_cost_cents: Estimated cost of the operation
            workflow_id: Optional workflow ID for workflow-level limits

        Returns:
            Tuple of (result, reason_message)
        """
        # Check per-request limit
        if estimated_cost_cents > self.quota.per_request_limit_cents:
            return (
                CostEnforcementResult.REQUEST_TOO_EXPENSIVE,
                f"Estimated cost ({estimated_cost_cents:.2f}c) exceeds per-request limit ({self.quota.per_request_limit_cents}c)"
            )

        # Check workflow limit if workflow_id provided
        if workflow_id:
            workflow_spend = self.get_workflow_spend(workflow_id)
            if workflow_spend + estimated_cost_cents > self.quota.per_workflow_limit_cents:
                if self.quota.enforce_hard_limit:
                    return (
                        CostEnforcementResult.BUDGET_EXCEEDED,
                        f"Workflow budget exceeded: {workflow_spend:.2f}c + {estimated_cost_cents:.2f}c > {self.quota.per_workflow_limit_cents}c limit"
                    )
                else:
                    return (
                        CostEnforcementResult.BUDGET_WARNING,
                        f"Workflow budget warning: approaching limit"
                    )

        # Check hourly limit
        hourly_spend = self.get_spend(tenant_id, "hourly")
        if hourly_spend + estimated_cost_cents > self.quota.hourly_limit_cents:
            if self.quota.enforce_hard_limit:
                return (
                    CostEnforcementResult.BUDGET_EXCEEDED,
                    f"Hourly budget exceeded: {hourly_spend:.2f}c + {estimated_cost_cents:.2f}c > {self.quota.hourly_limit_cents}c limit"
                )
            else:
                return (
                    CostEnforcementResult.BUDGET_WARNING,
                    f"Hourly budget warning: approaching limit"
                )

        # Check daily limit
        daily_spend = self.get_spend(tenant_id, "daily")
        if daily_spend + estimated_cost_cents > self.quota.daily_limit_cents:
            if self.quota.enforce_hard_limit:
                return (
                    CostEnforcementResult.BUDGET_EXCEEDED,
                    f"Daily budget exceeded: {daily_spend:.2f}c + {estimated_cost_cents:.2f}c > {self.quota.daily_limit_cents}c limit"
                )
            else:
                return (
                    CostEnforcementResult.BUDGET_WARNING,
                    f"Daily budget warning: approaching limit"
                )

        # Check warning threshold
        daily_threshold = self.quota.daily_limit_cents * self.quota.warn_threshold_percent
        if daily_spend + estimated_cost_cents > daily_threshold:
            return (
                CostEnforcementResult.BUDGET_WARNING,
                f"Approaching daily budget: {daily_spend + estimated_cost_cents:.2f}c / {self.quota.daily_limit_cents}c"
            )

        return (CostEnforcementResult.ALLOWED, "OK")

    def get_workflow_spend(self, workflow_id: str) -> float:
        """Get total spend for a workflow."""
        with self._lock:
            return sum(
                r.cost_cents for r in self._records
                if r.workflow_id == workflow_id
            )

    def set_workflow_budget(
        self,
        workflow_id: str,
        budget_cents: int
    ) -> None:
        """Set custom budget for a specific workflow."""
        # Store in a separate dict for workflow-specific budgets
        if not hasattr(self, '_workflow_budgets'):
            self._workflow_budgets: dict[str, int] = {}
        self._workflow_budgets[workflow_id] = budget_cents

    def get_workflow_budget(self, workflow_id: str) -> int:
        """Get budget for a workflow (default or custom)."""
        if hasattr(self, '_workflow_budgets') and workflow_id in self._workflow_budgets:
            return self._workflow_budgets[workflow_id]
        return self.quota.per_workflow_limit_cents


# Global instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def configure_cost_quota(quota: CostQuota) -> None:
    """Configure global cost quota."""
    global _cost_tracker
    _cost_tracker = CostTracker(quota)
