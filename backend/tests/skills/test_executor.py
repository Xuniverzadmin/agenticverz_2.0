# tests/skills/test_executor.py
"""
Tests for SkillExecutor with budget enforcement.
"""

import pytest
import sys
from pathlib import Path

# Path setup
_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.skills.executor import (
    SkillExecutor,
    SkillExecutionError,
    BudgetExceededError,
    execute_skill,
)
from app.observability.cost_tracker import (
    CostTracker,
    CostQuota,
    CostEnforcementResult,
    configure_cost_quota,
)
from app.skills import load_all_skills


@pytest.fixture(autouse=True)
def load_skills():
    """Load all skills before running tests."""
    load_all_skills()


@pytest.fixture
def reset_cost_tracker():
    """Reset global cost tracker before each test."""
    # Configure a fresh tracker with test quota
    configure_cost_quota(CostQuota(
        daily_limit_cents=10000,
        hourly_limit_cents=1000,
        per_request_limit_cents=100,
        per_workflow_limit_cents=500,
        enforce_hard_limit=True,
    ))
    yield


class TestExecutorBudgetEnforcement:
    """Test budget enforcement in SkillExecutor."""

    @pytest.mark.asyncio
    async def test_execute_allowed_under_budget(self, reset_cost_tracker):
        """Execution proceeds when under budget."""
        executor = SkillExecutor(enforce_budget=True)

        # json_transform has 0 cost, should always pass
        result, status = await executor.execute(
            skill_name="json_transform",
            params={"data": {"key": "value"}, "operation": "identity"},
            tenant_id="tenant-test",
        )

        assert status.value in ("succeeded", "ok")

    @pytest.mark.asyncio
    async def test_execute_blocked_when_budget_exceeded(self, reset_cost_tracker):
        """Execution blocked when budget would be exceeded."""
        # Configure very low budget
        configure_cost_quota(CostQuota(
            daily_limit_cents=1,  # Only 1 cent total
            hourly_limit_cents=1,
            per_request_limit_cents=100,
            enforce_hard_limit=True,
        ))

        executor = SkillExecutor(enforce_budget=True)

        # Record spend that exceeds budget
        from app.observability.cost_tracker import get_cost_tracker as get_tracker
        tracker = get_tracker()
        tracker.record_cost(
            tenant_id="tenant-test",
            workflow_id="wf-1",
            skill_id="llm_invoke",
            cost_cents=10.0,  # Way over 1c limit
            input_tokens=100,
            output_tokens=50,
            model="claude",
        )

        # Now execute should fail - llm_invoke has default 5c estimate
        with pytest.raises(BudgetExceededError) as exc_info:
            await executor.execute(
                skill_name="llm_invoke",
                params={"prompt": "test"},
                tenant_id="tenant-test",
            )

        assert exc_info.value.enforcement_result == CostEnforcementResult.BUDGET_EXCEEDED
        assert exc_info.value.tenant_id == "tenant-test"
        assert exc_info.value.is_retryable is False

    @pytest.mark.asyncio
    async def test_execute_no_budget_check_without_tenant_id(self, reset_cost_tracker):
        """Budget not checked if tenant_id not provided."""
        # Configure very low budget
        configure_cost_quota(CostQuota(
            daily_limit_cents=0,  # Zero budget
            hourly_limit_cents=0,
            enforce_hard_limit=True,
        ))

        executor = SkillExecutor(enforce_budget=True)

        # Without tenant_id, no budget check happens
        result, status = await executor.execute(
            skill_name="json_transform",
            params={"data": {"key": "value"}, "operation": "identity"},
            # No tenant_id
        )

        assert status.value in ("succeeded", "ok")

    @pytest.mark.asyncio
    async def test_execute_no_budget_check_when_disabled(self, reset_cost_tracker):
        """Budget not checked when enforce_budget=False."""
        # Configure very low budget
        configure_cost_quota(CostQuota(
            daily_limit_cents=0,  # Zero budget
            hourly_limit_cents=0,
            enforce_hard_limit=True,
        ))

        executor = SkillExecutor(enforce_budget=False)  # Disabled

        # Even with tenant_id, no budget check
        result, status = await executor.execute(
            skill_name="json_transform",
            params={"data": {"key": "value"}, "operation": "identity"},
            tenant_id="tenant-test",
        )

        assert status.value in ("succeeded", "ok")

    @pytest.mark.asyncio
    async def test_workflow_budget_enforcement(self, reset_cost_tracker):
        """Workflow-level budget is enforced."""
        configure_cost_quota(CostQuota(
            daily_limit_cents=10000,
            hourly_limit_cents=1000,
            per_workflow_limit_cents=10,  # Very low workflow limit
            enforce_hard_limit=True,
        ))

        executor = SkillExecutor(enforce_budget=True)

        # Exhaust workflow budget
        tracker = get_cost_tracker()
        tracker.record_cost(
            tenant_id="tenant-test",
            workflow_id="wf-test",
            skill_id="llm_invoke",
            cost_cents=15.0,  # Over 10c workflow limit
            input_tokens=100,
            output_tokens=50,
            model="claude",
        )

        # Should fail for this workflow
        with pytest.raises(BudgetExceededError) as exc_info:
            await executor.execute(
                skill_name="llm_invoke",
                params={"prompt": "test"},
                tenant_id="tenant-test",
                workflow_id="wf-test",  # This workflow is over budget
            )

        assert "Workflow budget" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_budget_exceeded_error_attributes(self, reset_cost_tracker):
        """BudgetExceededError has correct attributes."""
        configure_cost_quota(CostQuota(
            daily_limit_cents=1,
            hourly_limit_cents=1,
            enforce_hard_limit=True,
        ))

        # Exhaust budget
        tracker = get_cost_tracker()
        tracker.record_cost(
            tenant_id="tenant-attrs",
            workflow_id="wf-1",
            skill_id="llm_invoke",
            cost_cents=100.0,
            input_tokens=100,
            output_tokens=50,
            model="claude",
        )

        executor = SkillExecutor(enforce_budget=True)

        with pytest.raises(BudgetExceededError) as exc_info:
            await executor.execute(
                skill_name="llm_invoke",
                params={"prompt": "test"},
                step_id="step-123",
                tenant_id="tenant-attrs",
                workflow_id="wf-attrs",
            )

        err = exc_info.value
        assert err.skill_name == "llm_invoke"
        assert err.step_id == "step-123"
        assert err.tenant_id == "tenant-attrs"
        assert err.estimated_cost_cents == 5.0  # llm_invoke default estimate
        assert err.is_retryable is False


class TestExecutorCostEstimates:
    """Test skill cost estimation."""

    def test_skill_cost_estimates(self):
        """Skill cost estimates are defined."""
        executor = SkillExecutor()

        assert executor.SKILL_COST_ESTIMATES["llm_invoke"] > 0
        assert executor.SKILL_COST_ESTIMATES["http_call"] == 0
        assert executor.SKILL_COST_ESTIMATES["json_transform"] == 0
        assert executor.DEFAULT_COST_ESTIMATE > 0


# Import helper for tests
def get_cost_tracker():
    from app.observability.cost_tracker import get_cost_tracker as _get
    return _get()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
