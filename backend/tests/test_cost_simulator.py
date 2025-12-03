# Tests for Cost Simulator (M5)
"""
Unit tests for pre-execution cost simulation.
"""

import pytest
from pathlib import Path

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.worker.simulate import (
    CostSimulator,
    SimulationResult,
    FeasibilityStatus,
    StepRisk,
    simulate_plan,
)


class TestCostSimulatorBasic:
    """Basic tests for cost simulator."""

    def test_empty_plan_not_feasible(self):
        """Test empty plan is not feasible."""
        simulator = CostSimulator(budget_cents=1000)
        result = simulator.simulate([])

        assert result.feasible is False
        assert result.status == FeasibilityStatus.INVALID_PLAN
        assert "Empty plan" in result.warnings[0]

    def test_single_http_call(self):
        """Test single HTTP call simulation."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "http_call", "params": {"url": "https://example.com"}}]

        result = simulator.simulate(plan)

        assert result.feasible is True
        assert result.estimated_cost_cents == 0  # HTTP calls are free
        assert result.estimated_duration_ms > 0
        assert result.budget_sufficient is True

    def test_single_llm_call(self):
        """Test single LLM call simulation."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "llm_invoke", "params": {"prompt": "Hello world"}}]

        result = simulator.simulate(plan)

        assert result.feasible is True
        assert result.estimated_cost_cents >= 5  # LLM calls have cost
        assert result.budget_sufficient is True


class TestBudgetFeasibility:
    """Tests for budget feasibility checks."""

    def test_budget_exceeded(self):
        """Test plan exceeding budget is not feasible."""
        simulator = CostSimulator(budget_cents=1)  # Very low budget
        plan = [
            {"skill": "llm_invoke", "params": {"prompt": "x" * 10000}},  # Large prompt
            {"skill": "llm_invoke", "params": {"prompt": "x" * 10000}},
        ]

        result = simulator.simulate(plan)

        assert result.feasible is False
        assert result.status == FeasibilityStatus.BUDGET_INSUFFICIENT
        assert result.budget_sufficient is False

    def test_budget_remaining_calculated(self):
        """Test budget remaining is calculated correctly."""
        simulator = CostSimulator(budget_cents=100)
        plan = [
            {"skill": "llm_invoke", "params": {"prompt": "short"}},
        ]

        result = simulator.simulate(plan)

        expected_remaining = 100 - result.estimated_cost_cents
        assert result.budget_remaining_cents == expected_remaining

    def test_multiple_llm_calls_cost(self):
        """Test multiple LLM calls accumulate cost."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [
            {"skill": "llm_invoke", "params": {"prompt": "call 1"}},
            {"skill": "llm_invoke", "params": {"prompt": "call 2"}},
            {"skill": "llm_invoke", "params": {"prompt": "call 3"}},
        ]

        result = simulator.simulate(plan)

        # Each LLM call is at least 5 cents
        assert result.estimated_cost_cents >= 15


class TestPermissionChecks:
    """Tests for permission/skill allowlist checks."""

    def test_allowed_skills(self):
        """Test plan with allowed skills passes."""
        simulator = CostSimulator(
            budget_cents=100,
            allowed_skills=["http_call", "json_transform"],
        )
        plan = [
            {"skill": "http_call", "params": {}},
            {"skill": "json_transform", "params": {}},
        ]

        result = simulator.simulate(plan)

        assert result.feasible is True
        assert len(result.permission_gaps) == 0

    def test_disallowed_skill_fails(self):
        """Test plan with disallowed skill fails."""
        simulator = CostSimulator(
            budget_cents=100,
            allowed_skills=["http_call"],  # Only http_call allowed
        )
        plan = [
            {"skill": "http_call", "params": {}},
            {"skill": "llm_invoke", "params": {}},  # Not allowed
        ]

        result = simulator.simulate(plan)

        assert result.feasible is False
        assert result.status == FeasibilityStatus.PERMISSION_DENIED
        assert "llm_invoke" in result.permission_gaps

    def test_no_allowlist_means_all_allowed(self):
        """Test no allowlist means all skills allowed."""
        simulator = CostSimulator(
            budget_cents=100,
            allowed_skills=None,
        )
        plan = [
            {"skill": "http_call", "params": {}},
            {"skill": "llm_invoke", "params": {}},
            {"skill": "some_future_skill", "params": {}},
        ]

        result = simulator.simulate(plan)

        assert len(result.permission_gaps) == 0


class TestRiskAssessment:
    """Tests for risk assessment."""

    def test_http_call_has_timeout_risk(self):
        """Test HTTP calls have timeout risk."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "http_call", "params": {}}]

        result = simulator.simulate(plan)

        http_risks = [r for r in result.risks if r.skill_id == "http_call"]
        assert len(http_risks) >= 1
        assert http_risks[0].risk_type == "timeout"

    def test_risk_has_mitigation(self):
        """Test risks have mitigation suggestions."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "http_call", "params": {}}]

        result = simulator.simulate(plan)

        for risk in result.risks:
            assert risk.mitigation is not None
            assert len(risk.mitigation) > 0

    def test_high_risk_plan_not_feasible(self):
        """Test plan with high cumulative risk may fail."""
        simulator = CostSimulator(
            budget_cents=10000,
            risk_threshold=0.3,  # Low risk threshold
        )
        # Many HTTP calls = high cumulative risk
        plan = [{"skill": "http_call", "params": {}} for _ in range(10)]

        result = simulator.simulate(plan)

        # With 10 HTTP calls each with 10% timeout risk,
        # cumulative risk is ~65%, which exceeds 30% threshold
        if result.metadata["cumulative_risk"] > 0.3:
            assert result.feasible is False
            assert result.status == FeasibilityStatus.RISK_TOO_HIGH


class TestDurationEstimation:
    """Tests for duration estimation."""

    def test_json_transform_fast(self):
        """Test JSON transform is fast."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "json_transform", "params": {}}]

        result = simulator.simulate(plan)

        assert result.estimated_duration_ms <= 50  # Should be very fast

    def test_llm_call_slow(self):
        """Test LLM call is slower."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "llm_invoke", "params": {}}]

        result = simulator.simulate(plan)

        assert result.estimated_duration_ms >= 1000  # At least 1 second

    def test_durations_sum(self):
        """Test durations sum across steps."""
        simulator = CostSimulator(budget_cents=100)
        plan = [
            {"skill": "http_call", "params": {}},
            {"skill": "llm_invoke", "params": {}},
            {"skill": "json_transform", "params": {}},
        ]

        result = simulator.simulate(plan)

        # Sum should be at least LLM duration
        assert result.estimated_duration_ms >= 2000


class TestStepEstimates:
    """Tests for per-step estimates."""

    def test_step_estimates_returned(self):
        """Test step estimates are returned."""
        simulator = CostSimulator(budget_cents=100)
        plan = [
            {"skill": "http_call", "params": {}},
            {"skill": "llm_invoke", "params": {}},
        ]

        result = simulator.simulate(plan)

        assert len(result.step_estimates) == 2
        assert result.step_estimates[0]["skill_id"] == "http_call"
        assert result.step_estimates[1]["skill_id"] == "llm_invoke"

    def test_step_estimates_have_costs(self):
        """Test step estimates include costs."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "llm_invoke", "params": {}}]

        result = simulator.simulate(plan)

        assert "cost_cents" in result.step_estimates[0]
        assert "latency_ms" in result.step_estimates[0]
        assert "risk_probability" in result.step_estimates[0]


class TestAlternatives:
    """Tests for alternative suggestions."""

    def test_budget_failure_suggests_alternatives(self):
        """Test budget failure suggests alternatives."""
        simulator = CostSimulator(budget_cents=1)
        plan = [
            {"skill": "llm_invoke", "params": {"prompt": "x" * 5000}},
        ]

        result = simulator.simulate(plan)

        if result.status == FeasibilityStatus.BUDGET_INSUFFICIENT:
            assert len(result.alternatives) > 0


class TestConvenienceFunction:
    """Tests for convenience function."""

    def test_simulate_plan_function(self):
        """Test simulate_plan convenience function."""
        plan = [
            {"skill": "http_call", "params": {}},
        ]

        result = simulate_plan(plan, budget_cents=100)

        assert isinstance(result, SimulationResult)
        assert result.feasible is True


class TestResultSerialization:
    """Tests for result serialization."""

    def test_result_to_dict(self):
        """Test result serialization to dict."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "http_call", "params": {}}]

        result = simulator.simulate(plan)
        data = result.to_dict()

        assert "feasible" in data
        assert "status" in data
        assert "estimated_cost_cents" in data
        assert "estimated_duration_ms" in data
        assert "risks" in data
        assert "step_estimates" in data

    def test_status_serializes_to_string(self):
        """Test status enum serializes to string."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "http_call", "params": {}}]

        result = simulator.simulate(plan)
        data = result.to_dict()

        assert isinstance(data["status"], str)
        assert data["status"] == "feasible"


class TestUnknownSkills:
    """Tests for unknown skill handling."""

    def test_unknown_skill_has_conservative_estimates(self):
        """Test unknown skills use conservative estimates."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "some_future_skill_not_in_catalog", "params": {}}]

        result = simulator.simulate(plan)

        # Unknown skills should have higher cost/risk estimates
        assert result.estimated_cost_cents >= 10  # Conservative default
        assert len(result.risks) >= 1  # Should flag as risky
