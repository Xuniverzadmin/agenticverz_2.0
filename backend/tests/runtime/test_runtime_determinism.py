"""
Runtime Determinism Tests for AOS
M6 Deliverable: Prove runtime behavior is deterministic

These tests verify that the AOS runtime produces deterministic behavior
for the same inputs, regardless of external service responses.
"""

import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, "/root/agenticverz2.0/backend")

from app.runtime.replay import ReplayEngine, validate_determinism
from app.hoc.cus.logs.L5_schemas import (
    TraceRecord,
    TraceStatus,
    TraceStep,
    compare_traces,
)
from app.hoc.cus.logs.L6_drivers.trace_store import InMemoryTraceStore, generate_correlation_id, generate_run_id


class TestTraceDeterminism:
    """Test determinism of trace signatures."""

    def test_same_steps_produce_same_signature(self):
        """Identical steps should produce identical signatures."""
        step1 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com", "method": "GET"},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data={"response": "data1"},
            cost_cents=0.5,
            duration_ms=100.0,
            retry_count=0,
        )

        step2 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com", "method": "GET"},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data={"response": "different_data"},  # Different response
            cost_cents=1.0,  # Different cost
            duration_ms=200.0,  # Different duration
            retry_count=0,
        )

        # Should produce same hash (determinism fields match)
        assert step1.determinism_hash() == step2.determinism_hash()

    def test_different_params_produce_different_signature(self):
        """Different parameters should produce different signatures."""
        step1 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com/v1"},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=0.0,
            retry_count=0,
        )

        step2 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com/v2"},  # Different URL
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=0.0,
            retry_count=0,
        )

        assert step1.determinism_hash() != step2.determinism_hash()

    def test_different_skill_produces_different_signature(self):
        """Different skill names should produce different signatures."""
        step1 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com"},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=0.0,
            retry_count=0,
        )

        step2 = TraceStep(
            step_index=0,
            skill_name="llm_invoke",  # Different skill
            params={"url": "https://api.example.com"},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=0.0,
            retry_count=0,
        )

        assert step1.determinism_hash() != step2.determinism_hash()

    def test_different_retry_count_produces_different_signature(self):
        """Different retry counts should produce different signatures."""
        step1 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com"},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=0.0,
            retry_count=0,
        )

        step2 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com"},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=0.0,
            retry_count=1,  # One retry occurred
        )

        assert step1.determinism_hash() != step2.determinism_hash()

    def test_param_order_invariance(self):
        """Parameter key order should not affect signature."""
        step1 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com", "method": "GET", "timeout": 30},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=0.0,
            retry_count=0,
        )

        step2 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"timeout": 30, "method": "GET", "url": "https://api.example.com"},  # Different order
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=0.0,
            retry_count=0,
        )

        assert step1.determinism_hash() == step2.determinism_hash()


class TestTraceComparison:
    """Test trace-level parity comparison."""

    def create_trace(
        self,
        run_id: str,
        steps: list[TraceStep],
        status: str = "completed",
    ) -> TraceRecord:
        """Helper to create a trace record."""
        return TraceRecord(
            run_id=run_id,
            correlation_id=generate_correlation_id(),
            tenant_id="test_tenant",
            agent_id="test_agent",
            plan=[{"skill": s.skill_name, "params": s.params} for s in steps],
            steps=steps,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            status=status,
        )

    def test_identical_traces_have_parity(self):
        """Identical traces should have parity."""
        steps = [
            TraceStep(
                step_index=0,
                skill_name="http_call",
                params={"url": "https://api.example.com"},
                status=TraceStatus.SUCCESS,
                outcome_category="SUCCESS",
                outcome_code=None,
                outcome_data={"data": "response1"},
                cost_cents=0.5,
                duration_ms=100.0,
                retry_count=0,
            ),
            TraceStep(
                step_index=1,
                skill_name="json_transform",
                params={"query": ".data"},
                status=TraceStatus.SUCCESS,
                outcome_category="SUCCESS",
                outcome_code=None,
                outcome_data={"result": "transformed"},
                cost_cents=0.0,
                duration_ms=5.0,
                retry_count=0,
            ),
        ]

        trace1 = self.create_trace("run_1", steps)
        trace2 = self.create_trace("run_2", steps)

        result = compare_traces(trace1, trace2)
        assert result.is_parity
        assert result.divergence_step is None
        assert result.divergence_reason is None

    def test_different_response_data_still_has_parity(self):
        """Different response data should still have parity (not deterministic)."""
        steps1 = [
            TraceStep(
                step_index=0,
                skill_name="http_call",
                params={"url": "https://api.example.com"},
                status=TraceStatus.SUCCESS,
                outcome_category="SUCCESS",
                outcome_code=None,
                outcome_data={"price": 100},
                cost_cents=0.5,
                duration_ms=100.0,
                retry_count=0,
            ),
        ]

        steps2 = [
            TraceStep(
                step_index=0,
                skill_name="http_call",
                params={"url": "https://api.example.com"},
                status=TraceStatus.SUCCESS,
                outcome_category="SUCCESS",
                outcome_code=None,
                outcome_data={"price": 200},  # Different response
                cost_cents=0.8,  # Different cost
                duration_ms=150.0,  # Different duration
                retry_count=0,
            ),
        ]

        trace1 = self.create_trace("run_1", steps1)
        trace2 = self.create_trace("run_2", steps2)

        result = compare_traces(trace1, trace2)
        assert result.is_parity  # Still parity - deterministic fields match

    def test_different_skill_breaks_parity(self):
        """Different skill in same position breaks parity."""
        steps1 = [
            TraceStep(
                step_index=0,
                skill_name="http_call",
                params={"url": "https://api.example.com"},
                status=TraceStatus.SUCCESS,
                outcome_category="SUCCESS",
                outcome_code=None,
                outcome_data=None,
                cost_cents=0.0,
                duration_ms=0.0,
                retry_count=0,
            ),
        ]

        steps2 = [
            TraceStep(
                step_index=0,
                skill_name="llm_invoke",  # Different skill
                params={"url": "https://api.example.com"},
                status=TraceStatus.SUCCESS,
                outcome_category="SUCCESS",
                outcome_code=None,
                outcome_data=None,
                cost_cents=0.0,
                duration_ms=0.0,
                retry_count=0,
            ),
        ]

        trace1 = self.create_trace("run_1", steps1)
        trace2 = self.create_trace("run_2", steps2)

        result = compare_traces(trace1, trace2)
        assert not result.is_parity
        assert result.divergence_step == 0
        assert "skill" in result.divergence_reason

    def test_different_step_count_breaks_parity(self):
        """Different number of steps breaks parity."""
        steps1 = [
            TraceStep(
                step_index=0,
                skill_name="http_call",
                params={"url": "https://api.example.com"},
                status=TraceStatus.SUCCESS,
                outcome_category="SUCCESS",
                outcome_code=None,
                outcome_data=None,
                cost_cents=0.0,
                duration_ms=0.0,
                retry_count=0,
            ),
            TraceStep(
                step_index=1,
                skill_name="json_transform",
                params={"query": ".data"},
                status=TraceStatus.SUCCESS,
                outcome_category="SUCCESS",
                outcome_code=None,
                outcome_data=None,
                cost_cents=0.0,
                duration_ms=0.0,
                retry_count=0,
            ),
        ]

        steps2 = [
            TraceStep(
                step_index=0,
                skill_name="http_call",
                params={"url": "https://api.example.com"},
                status=TraceStatus.SUCCESS,
                outcome_category="SUCCESS",
                outcome_code=None,
                outcome_data=None,
                cost_cents=0.0,
                duration_ms=0.0,
                retry_count=0,
            ),
        ]

        trace1 = self.create_trace("run_1", steps1)
        trace2 = self.create_trace("run_2", steps2)

        result = compare_traces(trace1, trace2)
        assert not result.is_parity
        assert "step count" in result.divergence_reason


class TestReplayEngine:
    """Test the replay engine."""

    @pytest.fixture
    def trace_store(self):
        """Create an in-memory trace store for testing."""
        return InMemoryTraceStore()

    @pytest.fixture
    def replay_engine(self, trace_store):
        """Create a replay engine with in-memory store."""
        return ReplayEngine(trace_store=trace_store)

    @pytest.mark.asyncio
    async def test_replay_missing_run_returns_error(self, replay_engine):
        """Replaying a non-existent run should return an error."""
        result = await replay_engine.replay_run("nonexistent_run")

        assert not result.success
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_replay_dry_run_preserves_parity(self, replay_engine, trace_store):
        """Dry-run replay should preserve parity with original."""
        # Create original trace
        run_id = generate_run_id()
        await trace_store.start_trace(
            run_id=run_id,
            correlation_id=generate_correlation_id(),
            tenant_id="test",
            agent_id="test_agent",
            plan=[{"skill": "http_call", "params": {"url": "https://api.example.com"}}],
        )

        await trace_store.record_step(
            run_id=run_id,
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com"},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data={"data": "test"},
            cost_cents=0.5,
            duration_ms=100.0,
            retry_count=0,
        )

        await trace_store.complete_trace(run_id, "completed")

        # Replay with dry_run=True
        result = await replay_engine.replay_run(
            run_id=run_id,
            verify_parity=True,
            dry_run=True,
        )

        assert result.success
        assert result.parity_check is not None
        assert result.parity_check.is_parity
        assert result.divergence_point is None

    @pytest.mark.asyncio
    async def test_replay_creates_new_trace(self, replay_engine, trace_store):
        """Replay should create a new trace with different run_id.

        S6 COMPLIANCE: Replay is observational by default (emit_traces=False).
        The trace is built in memory and returned in result.trace, NOT persisted
        to the trace store. This is correct behavior per PIN-198.

        To test persistence, pass emit_traces=True (see test_replay_persists_when_requested).
        """
        # Create original trace
        original_run_id = generate_run_id()
        await trace_store.start_trace(
            run_id=original_run_id,
            correlation_id=generate_correlation_id(),
            tenant_id="test",
            agent_id="test_agent",
            plan=[],
        )
        await trace_store.complete_trace(original_run_id, "completed")

        # Replay (default: emit_traces=False, S6 compliance)
        result = await replay_engine.replay_run(
            run_id=original_run_id,
            dry_run=True,
        )

        assert result.run_id != original_run_id
        assert result.original_run_id == original_run_id

        # In-memory trace should exist in result (S6: not persisted by default)
        assert result.trace is not None
        assert result.trace.metadata.get("replay_of") == original_run_id

        # Verify NOT persisted (S6 compliance - replay is observational)
        persisted_trace = await trace_store.get_trace(result.run_id)
        assert persisted_trace is None, "S6: Replay should not persist by default"


class TestDeterminismValidation:
    """Test batch determinism validation."""

    @pytest.fixture
    def trace_store(self):
        return InMemoryTraceStore()

    @pytest.mark.asyncio
    async def test_validate_multiple_runs(self, trace_store):
        """Validate determinism across multiple runs."""
        # Create two identical runs
        for run_id in ["run_1", "run_2"]:
            await trace_store.start_trace(
                run_id=run_id,
                correlation_id=generate_correlation_id(),
                tenant_id="test",
                agent_id="test_agent",
                plan=[{"skill": "http_call", "params": {"url": "https://api.example.com"}}],
            )

            await trace_store.record_step(
                run_id=run_id,
                step_index=0,
                skill_name="http_call",
                params={"url": "https://api.example.com"},
                status=TraceStatus.SUCCESS,
                outcome_category="SUCCESS",
                outcome_code=None,
                outcome_data=None,
                cost_cents=0.5,
                duration_ms=100.0,
                retry_count=0,
            )

            await trace_store.complete_trace(run_id, "completed")

        # Validate both runs
        results = await validate_determinism(
            ["run_1", "run_2"],
            trace_store=trace_store,
        )

        assert len(results) == 2
        assert all(r.is_parity for r in results.values())


class TestRetryDeterminism:
    """Test that retry behavior is deterministic."""

    def test_retry_count_affects_signature(self):
        """Different retry counts should produce different signatures."""
        step_no_retry = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com"},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=0.0,
            retry_count=0,
        )

        step_with_retry = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com"},
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=0.0,
            retry_count=2,
        )

        # Different retry counts = different determinism hash
        assert step_no_retry.determinism_hash() != step_with_retry.determinism_hash()

    def test_failure_then_success_is_tracked(self):
        """Failures leading to success should be tracked in trace."""
        trace = TraceRecord(
            run_id="test",
            correlation_id="corr_123",
            tenant_id="test",
            agent_id=None,
            plan=[],
            steps=[
                TraceStep(
                    step_index=0,
                    skill_name="http_call",
                    params={"url": "https://api.example.com"},
                    status=TraceStatus.RETRY,  # First attempt failed
                    outcome_category="TRANSIENT",
                    outcome_code="TIMEOUT",
                    outcome_data=None,
                    cost_cents=0.0,
                    duration_ms=30000.0,
                    retry_count=0,
                ),
                TraceStep(
                    step_index=0,  # Same step, retry
                    skill_name="http_call",
                    params={"url": "https://api.example.com"},
                    status=TraceStatus.SUCCESS,  # Retry succeeded
                    outcome_category="SUCCESS",
                    outcome_code=None,
                    outcome_data={"data": "finally"},
                    cost_cents=0.5,
                    duration_ms=200.0,
                    retry_count=1,
                ),
            ],
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            status="completed",
        )

        assert trace.success_count == 1
        assert trace.failure_count == 0  # RETRY is not FAILURE


class TestErrorClassificationDeterminism:
    """Test that error classification is deterministic."""

    def test_same_error_same_category(self):
        """Same error should always classify to same category."""
        step1 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com"},
            status=TraceStatus.FAILURE,
            outcome_category="TRANSIENT",
            outcome_code="HTTP_503",
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=100.0,
            retry_count=0,
        )

        step2 = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com"},
            status=TraceStatus.FAILURE,
            outcome_category="TRANSIENT",
            outcome_code="HTTP_503",
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=150.0,  # Different timing
            retry_count=0,
        )

        # Same error classification = same determinism hash
        assert step1.determinism_hash() == step2.determinism_hash()

    def test_different_error_different_category(self):
        """Different errors should have different signatures."""
        step_transient = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com"},
            status=TraceStatus.FAILURE,
            outcome_category="TRANSIENT",
            outcome_code="HTTP_503",
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=100.0,
            retry_count=0,
        )

        step_permanent = TraceStep(
            step_index=0,
            skill_name="http_call",
            params={"url": "https://api.example.com"},
            status=TraceStatus.FAILURE,
            outcome_category="PERMANENT",  # Different category
            outcome_code="HTTP_404",
            outcome_data=None,
            cost_cents=0.0,
            duration_ms=100.0,
            retry_count=0,
        )

        # Different error = different determinism hash
        assert step_transient.determinism_hash() != step_permanent.determinism_hash()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
