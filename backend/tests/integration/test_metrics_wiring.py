# test_metrics_wiring.py
"""
M6 Integration Tests: Metrics Wiring Verification

These tests verify that metrics actually increment during runtime.execute().
This is part of the M6b deliverables for observability validation.

Per PIN-024:
- record_step_duration() should be called after skill execution
- record_cost_simulation_drift() should be called when cost tracking is enabled
"""

from __future__ import annotations
import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict

from app.worker.runtime.core import Runtime, SkillDescriptor

# Test fixtures and helpers


class MockPrometheusHistogram:
    """Mock Prometheus histogram for testing metric recording."""

    def __init__(self):
        self.observations = []
        self.labels_calls = []

    def labels(self, **kwargs) -> "MockPrometheusHistogram":
        self.labels_calls.append(kwargs)
        return self

    def observe(self, value: float) -> None:
        self.observations.append(value)


class MockPrometheusCounter:
    """Mock Prometheus counter for testing metric recording."""

    def __init__(self):
        self.increments = []
        self.labels_calls = []

    def labels(self, **kwargs) -> "MockPrometheusCounter":
        self.labels_calls.append(kwargs)
        return self

    def inc(self, amount: float = 1) -> None:
        self.increments.append(amount)


@pytest.fixture
def mock_step_duration_histogram():
    """Create a mock histogram for step duration."""
    return MockPrometheusHistogram()


@pytest.fixture
def mock_drift_histogram():
    """Create a mock histogram for cost drift."""
    return MockPrometheusHistogram()


@pytest.fixture
def mock_cost_simulated_counter():
    """Create a mock counter for simulated cost."""
    return MockPrometheusCounter()


@pytest.fixture
def mock_cost_actual_counter():
    """Create a mock counter for actual cost."""
    return MockPrometheusCounter()


def _make_descriptor(skill_id: str, name: str, desc: str, cost_cents: int = 0) -> SkillDescriptor:
    """Helper to create SkillDescriptor for tests."""
    return SkillDescriptor(
        skill_id=skill_id,
        name=name,
        description=desc,
        version="1.0.0",
        inputs_schema={"type": "object"},
        outputs_schema={"type": "object"},
        cost_model={"base_cents": cost_cents},
    )


class TestMetricsWiring:
    """Verify metrics actually increment during execution."""

    @pytest.mark.asyncio
    async def test_step_duration_recorded_on_success(
        self,
        mock_step_duration_histogram,
    ):
        """Step duration metric should increment after successful execution."""
        # Create runtime with a simple skill
        runtime = Runtime()

        async def mock_skill(inputs: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(0.01)  # Simulate work
            return {"status": "ok"}

        descriptor = _make_descriptor("test_skill", "Test Skill", "A test skill", 5)
        runtime.register_skill(descriptor, mock_skill)

        # Patch the metrics functions
        with patch(
            "app.worker.runtime.core.record_step_duration"
        ) as mock_record_duration:
            with patch("app.worker.runtime.core.METRICS_AVAILABLE", True):
                outcome = await runtime.execute("test_skill", {"param": "value"})

                # Verify skill executed successfully
                assert outcome.ok is True

                # Verify duration metric was called
                mock_record_duration.assert_called_once()
                call_args = mock_record_duration.call_args
                assert call_args[0][0] == "test_skill"  # skill_id
                assert call_args[0][1] > 0  # duration_seconds > 0
                assert call_args[0][2] is True  # success=True

    @pytest.mark.asyncio
    async def test_step_duration_recorded_on_failure(self):
        """Step duration metric should increment after failed execution."""
        runtime = Runtime()

        async def failing_skill(inputs: Dict[str, Any]) -> Dict[str, Any]:
            raise ValueError("Simulated failure")

        descriptor = _make_descriptor("failing_skill", "Failing Skill", "A skill that fails", 0)
        runtime.register_skill(descriptor, failing_skill)

        with patch(
            "app.worker.runtime.core.record_step_duration"
        ) as mock_record_duration:
            with patch("app.worker.runtime.core.METRICS_AVAILABLE", True):
                outcome = await runtime.execute("failing_skill", {})

                # Verify skill failed but didn't throw
                assert outcome.ok is False
                assert outcome.error is not None

                # Verify duration metric was still called
                mock_record_duration.assert_called_once()
                call_args = mock_record_duration.call_args
                assert call_args[0][0] == "failing_skill"
                assert call_args[0][2] is False  # success=False

    @pytest.mark.asyncio
    async def test_step_duration_recorded_on_timeout(self):
        """Step duration metric should increment after timeout."""
        runtime = Runtime()

        async def slow_skill(inputs: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(10)  # Very slow
            return {"status": "ok"}

        descriptor = _make_descriptor("slow_skill", "Slow Skill", "A slow skill", 0)
        runtime.register_skill(descriptor, slow_skill)

        with patch(
            "app.worker.runtime.core.record_step_duration"
        ) as mock_record_duration:
            with patch("app.worker.runtime.core.METRICS_AVAILABLE", True):
                outcome = await runtime.execute("slow_skill", {}, timeout_s=0.05)

                # Verify timeout occurred
                assert outcome.ok is False
                assert outcome.error["code"] == "ERR_TIMEOUT"

                # Verify duration metric was still called
                mock_record_duration.assert_called_once()
                call_args = mock_record_duration.call_args
                assert call_args[0][0] == "slow_skill"
                assert call_args[0][2] is False  # success=False

    @pytest.mark.asyncio
    async def test_cost_drift_recorded_when_cost_tracking_enabled(self):
        """Cost drift metric should record simulated vs actual cost."""
        runtime = Runtime()

        async def cost_skill(inputs: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "computed"}

        descriptor = _make_descriptor("cost_skill", "Cost Skill", "A skill with cost", 25)
        runtime.register_skill(descriptor, cost_skill)

        with patch(
            "app.worker.runtime.core.record_cost_simulation_drift"
        ) as mock_record_drift:
            with patch("app.worker.runtime.core.METRICS_AVAILABLE", True):
                outcome = await runtime.execute("cost_skill", {})

                assert outcome.ok is True
                assert outcome.meta.get("cost_cents") == 25

                # Verify drift metric was called
                mock_record_drift.assert_called_once()
                call_args = mock_record_drift.call_args
                assert call_args[0][0] == "cost_skill"  # skill_id
                assert call_args[0][1] == 25  # simulated_cents
                assert call_args[0][2] == 25  # actual_cents (same in stub)

    @pytest.mark.asyncio
    async def test_no_drift_metric_for_zero_cost_skills(self):
        """Cost drift metric should NOT be called for zero-cost skills."""
        runtime = Runtime()

        async def free_skill(inputs: Dict[str, Any]) -> Dict[str, Any]:
            return {"free": True}

        descriptor = _make_descriptor("free_skill", "Free Skill", "A free skill", 0)
        runtime.register_skill(descriptor, free_skill)

        with patch(
            "app.worker.runtime.core.record_cost_simulation_drift"
        ) as mock_record_drift:
            with patch("app.worker.runtime.core.METRICS_AVAILABLE", True):
                outcome = await runtime.execute("free_skill", {})

                assert outcome.ok is True

                # Drift metric should NOT be called for zero-cost skills
                mock_record_drift.assert_not_called()

    @pytest.mark.asyncio
    async def test_metrics_gracefully_handle_unavailable(self):
        """Runtime should not crash if metrics module unavailable."""
        runtime = Runtime()

        async def simple_skill(inputs: Dict[str, Any]) -> Dict[str, Any]:
            return {"ok": True}

        descriptor = _make_descriptor("simple_skill", "Simple Skill", "A simple skill", 10)
        runtime.register_skill(descriptor, simple_skill)

        # Test with METRICS_AVAILABLE = False
        with patch("app.worker.runtime.core.METRICS_AVAILABLE", False):
            with patch(
                "app.worker.runtime.core.record_step_duration", None
            ):
                with patch(
                    "app.worker.runtime.core.record_cost_simulation_drift", None
                ):
                    # Should not crash
                    outcome = await runtime.execute("simple_skill", {})
                    assert outcome.ok is True


class TestDriftMetricRecording:
    """Test the actual drift metric recording function."""

    def test_record_cost_simulation_drift_positive(self):
        """Test recording when actual cost exceeds simulated."""
        from app.workflow.metrics import (
            record_cost_simulation_drift,
            cost_simulation_drift_cents,
            cost_simulated_cents_total,
            cost_actual_cents_total,
            PROMETHEUS_AVAILABLE,
        )

        if PROMETHEUS_AVAILABLE:
            # This will record to actual Prometheus metrics
            record_cost_simulation_drift("test_skill", 100, 150)
            # Drift = 150 - 100 = 50 (positive, actual > simulated)

    def test_record_cost_simulation_drift_negative(self):
        """Test recording when simulated cost exceeds actual."""
        from app.workflow.metrics import (
            record_cost_simulation_drift,
            PROMETHEUS_AVAILABLE,
        )

        if PROMETHEUS_AVAILABLE:
            record_cost_simulation_drift("test_skill", 200, 150)
            # Drift = 150 - 200 = -50 (negative, simulated > actual)

    def test_record_cost_simulation_drift_zero(self):
        """Test recording when costs match exactly."""
        from app.workflow.metrics import (
            record_cost_simulation_drift,
            PROMETHEUS_AVAILABLE,
        )

        if PROMETHEUS_AVAILABLE:
            record_cost_simulation_drift("test_skill", 100, 100)
            # Drift = 0 (perfect prediction)


class TestStepDurationMetricRecording:
    """Test the actual step duration metric recording function."""

    def test_record_step_duration_success(self):
        """Test recording successful step duration."""
        from app.workflow.metrics import (
            record_step_duration,
            PROMETHEUS_AVAILABLE,
        )

        if PROMETHEUS_AVAILABLE:
            record_step_duration("http_call", 0.5, success=True)

    def test_record_step_duration_failure(self):
        """Test recording failed step duration."""
        from app.workflow.metrics import (
            record_step_duration,
            PROMETHEUS_AVAILABLE,
        )

        if PROMETHEUS_AVAILABLE:
            record_step_duration("llm_invoke", 1.5, success=False)


class TestMetricsModuleIntegration:
    """Test that the metrics module integrates correctly with Runtime."""

    @pytest.mark.asyncio
    async def test_full_execution_with_real_metrics_module(self):
        """End-to-end test with real metrics module (if available)."""
        from app.worker.runtime.core import METRICS_AVAILABLE

        runtime = Runtime()

        async def integration_skill(inputs: Dict[str, Any]) -> Dict[str, Any]:
            return {"processed": inputs.get("data", "none")}

        descriptor = _make_descriptor(
            "integration_skill", "Integration Skill", "For integration testing", 15
        )
        runtime.register_skill(descriptor, integration_skill)

        # Execute and verify
        outcome = await runtime.execute(
            "integration_skill",
            {"data": "test_value"},
        )

        assert outcome.ok is True
        assert outcome.result == {"processed": "test_value"}
        assert outcome.meta.get("cost_cents") == 15
        assert outcome.meta.get("duration_s", 0) > 0

        # If metrics available, they should have been recorded
        if METRICS_AVAILABLE:
            # The metrics have been recorded to Prometheus
            # We can't easily verify without scraping, but at least
            # we verify no exceptions were raised
            pass

    @pytest.mark.asyncio
    async def test_budget_exceeded_does_not_record_drift(self):
        """Budget exceeded should not record drift (execution didn't happen)."""
        # Use a fresh runtime - budget is set to 1000 by default
        runtime = Runtime()
        # Manually set budget low to trigger exceeded
        runtime._budget_total_cents = 10

        async def expensive_skill(inputs: Dict[str, Any]) -> Dict[str, Any]:
            return {"expensive": True}

        descriptor = _make_descriptor(
            "expensive_skill", "Expensive Skill", "Very expensive", 100
        )
        runtime.register_skill(descriptor, expensive_skill)

        with patch(
            "app.worker.runtime.core.record_cost_simulation_drift"
        ) as mock_record_drift:
            with patch("app.worker.runtime.core.METRICS_AVAILABLE", True):
                outcome = await runtime.execute("expensive_skill", {})

                # Should fail due to budget
                assert outcome.ok is False
                assert outcome.error["code"] == "ERR_BUDGET_EXCEEDED"

                # Drift metric should NOT be called (skill didn't execute)
                mock_record_drift.assert_not_called()


class TestPrometheusLabelsCardinality:
    """Test that metric labels follow cardinality rules."""

    def test_skill_id_labels_are_bounded(self):
        """Ensure skill_id labels come from registered skills only."""
        runtime = Runtime()

        # Only registered skills can be executed
        # So label cardinality is bounded by skill count

        async def dummy_handler(inputs: Dict[str, Any]) -> Dict[str, Any]:
            return {"ok": True}

        skills = ["http_call", "llm_invoke", "json_transform"]
        for skill in skills:
            descriptor = _make_descriptor(skill, skill, f"{skill} skill", 1)
            runtime.register_skill(descriptor, dummy_handler)

        # Verify cardinality is bounded
        assert len(runtime._registry) == 3
        assert len(runtime._skill_descriptors) == 3

    def test_status_labels_are_binary(self):
        """Status labels should only be 'success' or 'failure'."""
        from app.workflow.metrics import record_step_duration, PROMETHEUS_AVAILABLE

        # This is enforced by the function signature
        # success: bool -> "success" or "failure"
        if PROMETHEUS_AVAILABLE:
            record_step_duration("test", 0.1, success=True)
            record_step_duration("test", 0.1, success=False)
