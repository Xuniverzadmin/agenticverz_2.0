# tests/observability/test_cost_tracker.py
"""
Tests for Cost Tracking and Quota Management
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone

# Path setup
_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.observability.cost_tracker import (
    CostTracker,
    CostQuota,
    CostRecord,
    CostAlert,
)


class TestCostTracking:
    """Test cost tracking functionality."""

    def test_record_cost(self):
        """Record a cost event."""
        tracker = CostTracker()

        alerts = tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="skill.llm_invoke",
            cost_cents=5.0,
            input_tokens=100,
            output_tokens=50,
            model="claude-sonnet-4-20250514"
        )

        # Small cost shouldn't trigger alerts
        assert len(alerts) == 0

    def test_get_spend_daily(self):
        """Get daily spend for tenant."""
        tracker = CostTracker()

        tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="skill.llm_invoke",
            cost_cents=10.0,
            input_tokens=100,
            output_tokens=50,
            model="claude-sonnet-4-20250514"
        )
        tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-2",
            skill_id="skill.llm_invoke",
            cost_cents=15.0,
            input_tokens=200,
            output_tokens=100,
            model="claude-sonnet-4-20250514"
        )

        spend = tracker.get_spend("tenant-1", "daily")
        assert spend == 25.0

    def test_get_spend_hourly(self):
        """Get hourly spend for tenant."""
        tracker = CostTracker()

        tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="skill.llm_invoke",
            cost_cents=7.5,
            input_tokens=100,
            output_tokens=50,
            model="claude-sonnet-4-20250514"
        )

        spend = tracker.get_spend("tenant-1", "hourly")
        assert spend == 7.5


class TestCostQuotas:
    """Test quota enforcement."""

    def test_per_request_limit_exceeded(self):
        """Single request exceeding limit triggers alert."""
        quota = CostQuota(per_request_limit_cents=50)
        tracker = CostTracker(quota)

        alerts = tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="skill.llm_invoke",
            cost_cents=75.0,  # Exceeds 50c limit
            input_tokens=1000,
            output_tokens=500,
            model="claude-opus"
        )

        assert len(alerts) >= 1
        critical = [a for a in alerts if a.level == "critical"]
        assert len(critical) == 1
        assert "exceeds limit" in critical[0].message

    def test_hourly_budget_warning(self):
        """Approaching hourly budget triggers warning."""
        quota = CostQuota(
            hourly_limit_cents=100,
            warn_threshold_percent=0.8
        )
        tracker = CostTracker(quota)

        # Spend 85% of hourly budget
        alerts = tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="skill.llm_invoke",
            cost_cents=85.0,
            input_tokens=1000,
            output_tokens=500,
            model="claude-sonnet-4-20250514"
        )

        warn_alerts = [a for a in alerts if a.level == "warn" and a.period == "hourly"]
        assert len(warn_alerts) == 1

    def test_daily_budget_exceeded(self):
        """Exceeding daily budget triggers exceeded alert."""
        quota = CostQuota(daily_limit_cents=100)
        tracker = CostTracker(quota)

        # First request under limit
        tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="skill.llm_invoke",
            cost_cents=60.0,
            input_tokens=1000,
            output_tokens=500,
            model="claude-sonnet-4-20250514"
        )

        # Second request pushes over limit
        alerts = tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-2",
            skill_id="skill.llm_invoke",
            cost_cents=50.0,
            input_tokens=1000,
            output_tokens=500,
            model="claude-sonnet-4-20250514"
        )

        exceeded = [a for a in alerts if a.level == "exceeded" and a.period == "daily"]
        assert len(exceeded) == 1

    def test_is_budget_exceeded(self):
        """Check budget exceeded status."""
        quota = CostQuota(daily_limit_cents=100)
        tracker = CostTracker(quota)

        assert tracker.is_budget_exceeded("tenant-1") is False

        tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="skill.llm_invoke",
            cost_cents=150.0,
            input_tokens=1000,
            output_tokens=500,
            model="claude-sonnet-4-20250514"
        )

        assert tracker.is_budget_exceeded("tenant-1") is True


class TestCostSummary:
    """Test cost summary generation."""

    def test_get_cost_summary(self):
        """Get comprehensive cost summary."""
        tracker = CostTracker()

        # Record multiple costs
        tracker.record_cost("tenant-1", "wf-1", "skill.llm_invoke", 10.0, 100, 50, "claude-sonnet")
        tracker.record_cost("tenant-1", "wf-2", "skill.llm_invoke", 20.0, 200, 100, "claude-opus")
        tracker.record_cost("tenant-1", "wf-3", "skill.http_call", 5.0, 0, 0, "none")

        summary = tracker.get_cost_summary("tenant-1", days=7)

        assert summary["tenant_id"] == "tenant-1"
        assert summary["total_cost_cents"] == 35.0
        assert summary["total_input_tokens"] == 300
        assert summary["request_count"] == 3
        assert summary["by_skill"]["skill.llm_invoke"] == 30.0
        assert summary["by_skill"]["skill.http_call"] == 5.0

    def test_get_remaining_budget(self):
        """Get remaining budget calculation."""
        quota = CostQuota(daily_limit_cents=1000)
        tracker = CostTracker(quota)

        tracker.record_cost("tenant-1", "wf-1", "skill.llm_invoke", 250.0, 100, 50, "claude")

        remaining = tracker.get_remaining_budget("tenant-1", "daily")
        assert remaining == 750.0


class TestAlertRetrieval:
    """Test alert retrieval functionality."""

    def test_get_all_alerts(self):
        """Get all alerts."""
        quota = CostQuota(per_request_limit_cents=10)
        tracker = CostTracker(quota)

        # Generate alerts
        tracker.record_cost("tenant-1", "wf-1", "skill.llm_invoke", 50.0, 100, 50, "claude")
        tracker.record_cost("tenant-2", "wf-2", "skill.llm_invoke", 30.0, 100, 50, "claude")

        alerts = tracker.get_alerts()
        assert len(alerts) == 2

    def test_get_alerts_by_tenant(self):
        """Filter alerts by tenant."""
        quota = CostQuota(per_request_limit_cents=10)
        tracker = CostTracker(quota)

        tracker.record_cost("tenant-1", "wf-1", "skill.llm_invoke", 50.0, 100, 50, "claude")
        tracker.record_cost("tenant-2", "wf-2", "skill.llm_invoke", 30.0, 100, 50, "claude")

        alerts = tracker.get_alerts(tenant_id="tenant-1")
        assert len(alerts) == 1
        assert alerts[0].tenant_id == "tenant-1"


class TestMultiTenancy:
    """Test multi-tenant isolation."""

    def test_tenant_isolation(self):
        """Tenants have isolated budgets."""
        quota = CostQuota(daily_limit_cents=100)
        tracker = CostTracker(quota)

        # Tenant 1 uses budget
        tracker.record_cost("tenant-1", "wf-1", "skill.llm_invoke", 80.0, 100, 50, "claude")

        # Tenant 2 should have full budget
        assert tracker.get_spend("tenant-1", "daily") == 80.0
        assert tracker.get_spend("tenant-2", "daily") == 0.0
        assert tracker.get_remaining_budget("tenant-2", "daily") == 100.0


class TestCostEnforcement:
    """Test hard cost ceiling enforcement (pre-request checks)."""

    def test_check_can_spend_allowed(self):
        """Request under all limits is allowed."""
        from app.observability.cost_tracker import CostEnforcementResult

        quota = CostQuota(
            daily_limit_cents=1000,
            hourly_limit_cents=100,
            per_request_limit_cents=50,
            per_workflow_limit_cents=200,
        )
        tracker = CostTracker(quota)

        result, reason = tracker.check_can_spend(
            tenant_id="tenant-1",
            estimated_cost_cents=10.0,
        )

        assert result == CostEnforcementResult.ALLOWED
        assert reason == "OK"

    def test_check_can_spend_request_too_expensive(self):
        """Single request exceeding per-request limit is blocked."""
        from app.observability.cost_tracker import CostEnforcementResult

        quota = CostQuota(per_request_limit_cents=50)
        tracker = CostTracker(quota)

        result, reason = tracker.check_can_spend(
            tenant_id="tenant-1",
            estimated_cost_cents=100.0,
        )

        assert result == CostEnforcementResult.REQUEST_TOO_EXPENSIVE
        assert "per-request limit" in reason

    def test_check_can_spend_workflow_budget_exceeded(self):
        """Workflow budget exceeded blocks request."""
        from app.observability.cost_tracker import CostEnforcementResult

        quota = CostQuota(
            per_workflow_limit_cents=100,
            enforce_hard_limit=True,
        )
        tracker = CostTracker(quota)

        # Spend 80c on workflow
        tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="llm_invoke",
            cost_cents=80.0,
            input_tokens=1000,
            output_tokens=500,
            model="claude",
        )

        # Request 30c more should exceed workflow budget
        result, reason = tracker.check_can_spend(
            tenant_id="tenant-1",
            estimated_cost_cents=30.0,
            workflow_id="wf-1",
        )

        assert result == CostEnforcementResult.BUDGET_EXCEEDED
        assert "Workflow budget" in reason

    def test_check_can_spend_hourly_exceeded(self):
        """Hourly budget exceeded blocks request."""
        from app.observability.cost_tracker import CostEnforcementResult

        quota = CostQuota(
            hourly_limit_cents=100,
            enforce_hard_limit=True,
        )
        tracker = CostTracker(quota)

        # Spend 80c this hour
        tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="llm_invoke",
            cost_cents=80.0,
            input_tokens=1000,
            output_tokens=500,
            model="claude",
        )

        # Request 30c more should exceed hourly budget
        result, reason = tracker.check_can_spend(
            tenant_id="tenant-1",
            estimated_cost_cents=30.0,
        )

        assert result == CostEnforcementResult.BUDGET_EXCEEDED
        assert "Hourly budget" in reason

    def test_check_can_spend_daily_exceeded(self):
        """Daily budget exceeded blocks request."""
        from app.observability.cost_tracker import CostEnforcementResult

        quota = CostQuota(
            daily_limit_cents=100,
            hourly_limit_cents=10000,  # High enough not to trigger
            enforce_hard_limit=True,
        )
        tracker = CostTracker(quota)

        # Spend 80c today
        tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="llm_invoke",
            cost_cents=80.0,
            input_tokens=1000,
            output_tokens=500,
            model="claude",
        )

        # Request 30c more should exceed daily budget
        result, reason = tracker.check_can_spend(
            tenant_id="tenant-1",
            estimated_cost_cents=30.0,
        )

        assert result == CostEnforcementResult.BUDGET_EXCEEDED
        assert "Daily budget" in reason

    def test_check_can_spend_warning_threshold(self):
        """Approaching budget triggers warning (not block)."""
        from app.observability.cost_tracker import CostEnforcementResult

        quota = CostQuota(
            daily_limit_cents=100,
            hourly_limit_cents=10000,
            warn_threshold_percent=0.8,
            enforce_hard_limit=True,
        )
        tracker = CostTracker(quota)

        # Spend 75c today (under 80% threshold)
        tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="llm_invoke",
            cost_cents=75.0,
            input_tokens=1000,
            output_tokens=500,
            model="claude",
        )

        # Request 10c more should trigger warning (85c > 80c threshold)
        result, reason = tracker.check_can_spend(
            tenant_id="tenant-1",
            estimated_cost_cents=10.0,
        )

        assert result == CostEnforcementResult.BUDGET_WARNING
        assert "Approaching daily budget" in reason

    def test_check_can_spend_soft_limit_mode(self):
        """With enforce_hard_limit=False, returns warning instead of exceeded."""
        from app.observability.cost_tracker import CostEnforcementResult

        quota = CostQuota(
            hourly_limit_cents=100,
            enforce_hard_limit=False,  # Soft limit mode
        )
        tracker = CostTracker(quota)

        # Spend 80c this hour
        tracker.record_cost(
            tenant_id="tenant-1",
            workflow_id="wf-1",
            skill_id="llm_invoke",
            cost_cents=80.0,
            input_tokens=1000,
            output_tokens=500,
            model="claude",
        )

        # Request 30c more should return warning (not exceeded)
        result, reason = tracker.check_can_spend(
            tenant_id="tenant-1",
            estimated_cost_cents=30.0,
        )

        assert result == CostEnforcementResult.BUDGET_WARNING
        assert "warning" in reason.lower()


class TestWorkflowBudgets:
    """Test workflow-specific budget management."""

    def test_get_workflow_spend(self):
        """Get total spend for a workflow."""
        tracker = CostTracker()

        tracker.record_cost("tenant-1", "wf-1", "llm_invoke", 10.0, 100, 50, "claude")
        tracker.record_cost("tenant-1", "wf-1", "llm_invoke", 15.0, 150, 75, "claude")
        tracker.record_cost("tenant-1", "wf-2", "llm_invoke", 20.0, 200, 100, "claude")

        assert tracker.get_workflow_spend("wf-1") == 25.0
        assert tracker.get_workflow_spend("wf-2") == 20.0
        assert tracker.get_workflow_spend("wf-3") == 0.0

    def test_set_and_get_workflow_budget(self):
        """Set custom budget for a workflow."""
        quota = CostQuota(per_workflow_limit_cents=100)
        tracker = CostTracker(quota)

        # Default budget
        assert tracker.get_workflow_budget("wf-1") == 100

        # Set custom budget
        tracker.set_workflow_budget("wf-1", 500)
        assert tracker.get_workflow_budget("wf-1") == 500

        # Other workflows still use default
        assert tracker.get_workflow_budget("wf-2") == 100


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
