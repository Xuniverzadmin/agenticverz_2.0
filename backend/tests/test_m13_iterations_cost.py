# M13 Regression Tests: Iterations Cost Calculator
"""
Test suite to prevent regression of the iterations cost bug.

Bug: Cost calculator ignored iterations field, always calculating cost for 1 iteration.
Fix: Cost and latency now multiply by iterations field.

These tests MUST pass before any merge to main.
"""

import math
import pytest
from app.worker.simulate import CostSimulator, FeasibilityStatus


class TestIterationsCostCalculation:
    """Test that cost correctly multiplies by iterations."""

    def test_single_iteration_default(self):
        """Default iterations=1 should calculate single cost."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "llm_invoke", "params": {}}]
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 5  # llm_invoke base cost
        assert result.feasible is True

    def test_iterations_multiply_cost(self):
        """Cost should be base_cost * iterations."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 10}]
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 50  # 5 * 10
        assert result.step_estimates[0]["iterations"] == 10
        assert result.step_estimates[0]["base_cost_cents"] == 5
        assert result.step_estimates[0]["cost_cents"] == 50

    def test_multiple_steps_with_iterations(self):
        """Multiple steps with iterations should sum correctly."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [
            {"skill": "llm_invoke", "params": {}, "iterations": 10},  # 5 * 10 = 50
            {"skill": "email_send", "params": {}, "iterations": 10},  # 1 * 10 = 10
        ]
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 60  # 50 + 10

    def test_mixed_iterations_and_default(self):
        """Mix of explicit iterations and defaults should work."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [
            {"skill": "llm_invoke", "params": {}, "iterations": 5},  # 5 * 5 = 25
            {"skill": "http_call", "params": {}},  # 0 * 1 = 0 (default iterations=1)
            {"skill": "email_send", "params": {}, "iterations": 3},  # 1 * 3 = 3
        ]
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 28  # 25 + 0 + 3


class TestIterationsBudgetValidation:
    """Test that budget validation uses correct iterated costs."""

    def test_budget_sufficient_with_iterations(self):
        """Budget should be sufficient when cost <= budget."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 10}]  # 50 cents
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 50
        assert result.budget_sufficient is True
        assert result.budget_remaining_cents == 50

    def test_budget_insufficient_with_iterations(self):
        """Budget should be insufficient when iterations push cost over."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 50}]  # 250 cents
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 250
        assert result.budget_sufficient is False
        assert result.budget_remaining_cents == -150
        assert result.status == FeasibilityStatus.BUDGET_INSUFFICIENT
        assert result.feasible is False

    def test_budget_exact_match(self):
        """Budget exactly equal to cost should be sufficient."""
        simulator = CostSimulator(budget_cents=50)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 10}]  # 50 cents
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 50
        assert result.budget_sufficient is True
        assert result.budget_remaining_cents == 0

    def test_budget_one_cent_over(self):
        """Budget one cent under cost should fail."""
        simulator = CostSimulator(budget_cents=49)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 10}]  # 50 cents
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 50
        assert result.budget_sufficient is False
        assert result.feasible is False


class TestIterationsLatencyCalculation:
    """Test that latency correctly multiplies by iterations."""

    def test_latency_single_iteration(self):
        """Default iterations should use base latency."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "llm_invoke", "params": {}}]
        result = simulator.simulate(plan)

        assert result.estimated_duration_ms == 2000  # llm_invoke base latency

    def test_latency_multiplied_by_iterations(self):
        """Latency should multiply by iterations."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 10}]
        result = simulator.simulate(plan)

        assert result.estimated_duration_ms == 20000  # 2000 * 10
        assert result.step_estimates[0]["base_latency_ms"] == 2000
        assert result.step_estimates[0]["latency_ms"] == 20000

    def test_latency_multiple_steps(self):
        """Multiple steps should sum latencies correctly."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [
            {"skill": "llm_invoke", "params": {}, "iterations": 5},  # 2000 * 5 = 10000
            {"skill": "http_call", "params": {}, "iterations": 10},  # 500 * 10 = 5000
        ]
        result = simulator.simulate(plan)

        assert result.estimated_duration_ms == 15000  # 10000 + 5000


class TestIterationsRiskCompounding:
    """Test that risk compounds correctly with iterations."""

    def test_risk_single_iteration(self):
        """Single iteration should use base risk probability."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "http_call", "params": {}}]  # 10% risk
        result = simulator.simulate(plan)

        assert len(result.risks) == 1
        assert math.isclose(result.risks[0].probability, 0.1, rel_tol=1e-6)

    def test_risk_compounded_with_iterations(self):
        """Risk should compound: P(fail) = 1 - (1-p)^n."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "http_call", "params": {}, "iterations": 10}]  # 10% base risk
        result = simulator.simulate(plan)

        # P(at least one failure in 10 tries) = 1 - (0.9)^10 = ~0.6513
        expected_risk = 1.0 - (0.9 ** 10)
        assert len(result.risks) == 1
        assert math.isclose(result.risks[0].probability, expected_risk, rel_tol=1e-4)

    def test_risk_description_includes_iterations(self):
        """Risk description should mention iteration count."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "http_call", "params": {}, "iterations": 5}]
        result = simulator.simulate(plan)

        assert "x5" in result.risks[0].description


class TestIterationsEdgeCases:
    """Test edge cases for iterations handling."""

    def test_iterations_zero_cost_skill(self):
        """Zero-cost skill with iterations should remain zero."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "json_transform", "params": {}, "iterations": 100}]
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 0  # 0 * 100 = 0

    def test_iterations_missing_defaults_to_one(self):
        """Missing iterations field should default to 1."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "llm_invoke", "params": {}}]  # No iterations field
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 5
        assert result.step_estimates[0].get("iterations", 1) == 1

    def test_high_iteration_count(self):
        """High iteration counts should calculate correctly."""
        simulator = CostSimulator(budget_cents=100000)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 100}]
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 500  # 5 * 100
        assert result.estimated_duration_ms == 200000  # 2000 * 100


class TestIterationsAPIModel:
    """Test PlanStep model validation."""

    def test_planstep_accepts_iterations(self):
        """PlanStep should accept valid iterations."""
        from app.api.runtime import PlanStep

        step = PlanStep(skill="llm_invoke", params={}, iterations=50)
        assert step.iterations == 50

    def test_planstep_default_iterations(self):
        """PlanStep should default iterations to 1."""
        from app.api.runtime import PlanStep

        step = PlanStep(skill="llm_invoke", params={})
        assert step.iterations == 1

    def test_planstep_rejects_zero_iterations(self):
        """PlanStep should reject iterations < 1."""
        from app.api.runtime import PlanStep
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PlanStep(skill="llm_invoke", params={}, iterations=0)

    def test_planstep_rejects_negative_iterations(self):
        """PlanStep should reject negative iterations."""
        from app.api.runtime import PlanStep
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PlanStep(skill="llm_invoke", params={}, iterations=-5)

    def test_planstep_rejects_excessive_iterations(self):
        """PlanStep should reject iterations > 100."""
        from app.api.runtime import PlanStep
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PlanStep(skill="llm_invoke", params={}, iterations=101)

    def test_planstep_accepts_max_iterations(self):
        """PlanStep should accept iterations = 100."""
        from app.api.runtime import PlanStep

        step = PlanStep(skill="llm_invoke", params={}, iterations=100)
        assert step.iterations == 100


# Acceptance criteria verification
class TestM13AcceptanceCriteria:
    """Verify all M13 acceptance criteria are met."""

    def test_ac1_iterations_multiply_cost(self):
        """AC1: Iterations multiply both cost and latency."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 10}]
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 50  # Cost multiplied
        assert result.estimated_duration_ms == 20000  # Latency multiplied

    def test_ac2_budget_fails_when_exceeded(self):
        """AC2: Budget fails when total cost > budget."""
        simulator = CostSimulator(budget_cents=100)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 50}]
        result = simulator.simulate(plan)

        assert result.feasible is False
        assert result.status == FeasibilityStatus.BUDGET_INSUFFICIENT

    def test_ac3_per_step_cost_correct(self):
        """AC3: Per-step cost shows cost × iterations."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 10}]
        result = simulator.simulate(plan)

        step = result.step_estimates[0]
        assert step["cost_cents"] == 50  # Not 5

    def test_ac4_duration_scales(self):
        """AC4: Predicted duration scales with iterations."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 50}]
        result = simulator.simulate(plan)

        assert result.estimated_duration_ms == 100000  # 2000 * 50

    def test_ac5_50_llm_calls_equals_250(self):
        """AC5: Cost for 50 LLM calls = 250, not 5."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [{"skill": "llm_invoke", "params": {}, "iterations": 50}]
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 250

    def test_ac6_10_llm_10_email_equals_60(self):
        """AC6: Cost for 10 LLM + 10 emails = 60, not 6."""
        simulator = CostSimulator(budget_cents=1000)
        plan = [
            {"skill": "llm_invoke", "params": {}, "iterations": 10},
            {"skill": "email_send", "params": {}, "iterations": 10},
        ]
        result = simulator.simulate(plan)

        assert result.estimated_cost_cents == 60

    def test_ac7_rejects_invalid_iterations(self):
        """AC7: Backend rejects negative or zero iterations."""
        from app.api.runtime import PlanStep
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PlanStep(skill="test", params={}, iterations=0)

        with pytest.raises(ValidationError):
            PlanStep(skill="test", params={}, iterations=-1)
