# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci|manual
#   Execution: sync
# Role: Job Executor invariant tests
# Callers: pytest, CI pipeline
# Allowed Imports: All (test code)
# Forbidden Imports: None
# Reference: PIN-294, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1

"""
Job Executor Invariant Tests (Part-2)

Tests for the Job Executor (L5) - the machine execution layer.

Invariants:
- EXEC-001: Execute steps in declared order
- EXEC-002: Emit evidence per step
- EXEC-003: Stop on first failure
- EXEC-004: Health is observed, never modified
- EXEC-005: No eligibility or contract mutation
- EXEC-006: No retry logic

The Job Executor is "just physics" - it runs the plan and records what happened.

Reference: PIN-294, PIN-292, PART2_CRM_WORKFLOW_CHARTER.md, part2-design-v1
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

from app.models.governance_job import (
    JobStatus,
    JobStep,
    StepStatus,
)
from app.services.governance.job_executor import (
    EXECUTOR_VERSION,
    ExecutionContext,
    ExecutionResult,
    FailingHandler,
    JobExecutor,
    NoOpHandler,
    StepOutput,
    create_default_executor,
    execution_result_to_evidence,
)

# ==============================================================================
# TEST FIXTURES
# ==============================================================================


@pytest.fixture
def executor() -> JobExecutor:
    """Default Job Executor with no-op handlers."""
    return create_default_executor()


@pytest.fixture
def job_id():
    """Test job ID."""
    return uuid4()


@pytest.fixture
def contract_id():
    """Test contract ID."""
    return uuid4()


@pytest.fixture
def single_step() -> list[JobStep]:
    """Single step for testing."""
    return [
        JobStep(
            step_index=0,
            step_type="capability_enable",
            target="TEST_CAPABILITY",
            parameters={"param1": "value1"},
            timeout_seconds=60,
        )
    ]


@pytest.fixture
def multiple_steps() -> list[JobStep]:
    """Multiple steps for testing."""
    return [
        JobStep(
            step_index=0,
            step_type="capability_enable",
            target="CAP_A",
            parameters={},
            timeout_seconds=60,
        ),
        JobStep(
            step_index=1,
            step_type="capability_enable",
            target="CAP_B",
            parameters={},
            timeout_seconds=60,
        ),
        JobStep(
            step_index=2,
            step_type="capability_enable",
            target="CAP_C",
            parameters={},
            timeout_seconds=60,
        ),
    ]


class MockHealthObserver:
    """Mock health observer for testing."""

    def __init__(self, health_state: dict[str, Any] | None = None):
        self._health = health_state or {
            "capabilities": {"TEST_CAP": {"state": "HEALTHY"}},
            "system": {"status": "OK"},
        }
        self.observe_calls = 0

    def observe_health(self) -> dict[str, Any]:
        """Capture health state (read-only)."""
        self.observe_calls += 1
        return self._health.copy()


# ==============================================================================
# EXEC-001: Execute Steps in Declared Order
# ==============================================================================


class TestEXEC001StepOrder:
    """EXEC-001: Execute steps in declared order."""

    def test_single_step_executes(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """Single step executes and completes."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
        )

        assert result.final_status == JobStatus.COMPLETED
        assert result.steps_executed == 1
        assert result.steps_succeeded == 1

    def test_multiple_steps_execute_in_order(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        multiple_steps,
    ):
        """Multiple steps execute in declared order."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=multiple_steps,
        )

        assert result.final_status == JobStatus.COMPLETED
        assert result.steps_executed == 3
        assert result.steps_succeeded == 3

        # Verify order
        for idx, step_result in enumerate(result.step_results):
            assert step_result.step_index == idx

    def test_step_indices_are_sequential(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        multiple_steps,
    ):
        """Step results have sequential indices."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=multiple_steps,
        )

        indices = [sr.step_index for sr in result.step_results]
        assert indices == [0, 1, 2]


# ==============================================================================
# EXEC-002: Emit Evidence Per Step
# ==============================================================================


class TestEXEC002EvidenceEmission:
    """EXEC-002: Emit evidence per step."""

    def test_step_result_has_status(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """Each step result has a status."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
        )

        assert len(result.step_results) == 1
        assert result.step_results[0].status == StepStatus.COMPLETED

    def test_step_result_has_timestamps(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """Each step result has timestamps."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
        )

        step_result = result.step_results[0]
        assert step_result.started_at is not None
        assert step_result.completed_at is not None
        assert step_result.completed_at >= step_result.started_at

    def test_step_result_has_output(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """Successful step result has output."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
        )

        step_result = result.step_results[0]
        assert step_result.output is not None
        assert isinstance(step_result.output, dict)

    def test_multiple_steps_all_have_evidence(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        multiple_steps,
    ):
        """All steps emit evidence."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=multiple_steps,
        )

        assert len(result.step_results) == 3
        for sr in result.step_results:
            assert sr.status is not None
            assert sr.started_at is not None
            assert sr.completed_at is not None

    def test_evidence_to_audit_format(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        multiple_steps,
    ):
        """Evidence can be converted to audit format."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=multiple_steps,
        )

        evidence = execution_result_to_evidence(result)

        assert evidence["job_id"] == str(job_id)
        assert evidence["final_status"] == "COMPLETED"
        assert evidence["execution_summary"]["steps_executed"] == 3
        assert len(evidence["step_results"]) == 3
        assert "timing" in evidence
        assert "executor_version" in evidence


# ==============================================================================
# EXEC-003: Stop on First Failure
# ==============================================================================


class TestEXEC003StopOnFailure:
    """EXEC-003: Stop on first failure."""

    def test_stops_on_failed_step(
        self,
        job_id,
        contract_id,
        multiple_steps,
    ):
        """Execution stops when a step fails."""
        executor = JobExecutor()
        executor.register_handler("capability_enable", NoOpHandler())

        # Make the second step fail
        failing_handler = FailingHandler("Step 1 failed intentionally")
        # We need to make step 1 use a different type to fail
        multiple_steps[1].step_type = "failing_step"
        executor.register_handler("failing_step", failing_handler)

        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=multiple_steps,
        )

        # Should stop after step 1 fails
        assert result.final_status == JobStatus.FAILED
        assert result.steps_executed == 2  # 0 succeeded, 1 failed
        assert result.steps_succeeded == 1
        assert result.steps_failed == 1

    def test_remaining_steps_not_executed(
        self,
        job_id,
        contract_id,
    ):
        """Steps after failure are not executed."""
        executor = JobExecutor()
        executor.register_handler("good", NoOpHandler())
        executor.register_handler("bad", FailingHandler())

        steps = [
            JobStep(step_index=0, step_type="good", target="A", parameters={}, timeout_seconds=60),
            JobStep(step_index=1, step_type="bad", target="B", parameters={}, timeout_seconds=60),
            JobStep(step_index=2, step_type="good", target="C", parameters={}, timeout_seconds=60),
        ]

        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=steps,
        )

        # Step 2 should not be in results
        assert len(result.step_results) == 2
        assert result.step_results[-1].step_index == 1
        assert result.step_results[-1].status == StepStatus.FAILED

    def test_failure_reason_recorded(
        self,
        job_id,
        contract_id,
        single_step,
    ):
        """Failure reason is recorded."""
        executor = JobExecutor()
        executor.register_handler(
            "capability_enable",
            FailingHandler("Custom failure message"),
        )

        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
        )

        assert result.final_status == JobStatus.FAILED
        assert "Custom failure message" in result.final_reason

    def test_missing_handler_is_failure(
        self,
        job_id,
        contract_id,
    ):
        """Missing handler causes step failure."""
        executor = JobExecutor()  # No handlers registered

        steps = [
            JobStep(
                step_index=0,
                step_type="unregistered_type",
                target="X",
                parameters={},
                timeout_seconds=60,
            )
        ]

        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=steps,
        )

        assert result.final_status == JobStatus.FAILED
        assert "No handler" in result.step_results[0].error


# ==============================================================================
# EXEC-004: Health is Observed, Never Modified
# ==============================================================================


class TestEXEC004HealthObservation:
    """EXEC-004: Health is observed, never modified."""

    def test_health_before_captured(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """Health is captured before execution."""
        observer = MockHealthObserver()

        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
            health_observer=observer,
        )

        assert result.health_before is not None
        assert "capabilities" in result.health_before

    def test_health_after_captured_per_step(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """Health is captured after each step."""
        observer = MockHealthObserver()

        executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
            health_observer=observer,
        )

        # Health should be captured once before + once per step
        assert observer.observe_calls >= 2

    def test_health_observation_is_read_only(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """Health observer returns copies, not mutable originals."""
        observer = MockHealthObserver({"capabilities": {"CAP": {"state": "HEALTHY"}}, "system": {}})

        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
            health_observer=observer,
        )

        # Modify the returned value
        if result.health_before:
            result.health_before["modified"] = True

        # Re-observe should not have the modification
        fresh_health = observer.observe_health()
        assert "modified" not in fresh_health

    def test_health_in_evidence(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """Health observations included in evidence."""
        observer = MockHealthObserver()

        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
            health_observer=observer,
        )

        evidence = execution_result_to_evidence(result)
        assert "health_observations" in evidence
        assert evidence["health_observations"]["before"] is not None


# ==============================================================================
# EXEC-005: No Eligibility or Contract Mutation
# ==============================================================================


class TestEXEC005NoMutation:
    """EXEC-005: No eligibility or contract mutation."""

    def test_executor_has_no_contract_service(self):
        """Executor has no reference to ContractService."""
        executor = JobExecutor()

        # Check that executor has no contract-related attributes
        assert not hasattr(executor, "_contract_service")
        assert not hasattr(executor, "contract_service")
        assert not hasattr(executor, "update_contract")
        assert not hasattr(executor, "modify_contract")

    def test_executor_has_no_eligibility_service(self):
        """Executor has no reference to EligibilityEngine."""
        executor = JobExecutor()

        assert not hasattr(executor, "_eligibility_engine")
        assert not hasattr(executor, "eligibility_engine")
        assert not hasattr(executor, "check_eligibility")

    def test_execution_context_is_read_only(self):
        """ExecutionContext is frozen (immutable)."""
        context = ExecutionContext(
            job_id=uuid4(),
            contract_id=uuid4(),
            step_index=0,
            step_type="test",
            target="TARGET",
            executed_by="tester",
            started_at=datetime.now(timezone.utc),
        )

        with pytest.raises((AttributeError, TypeError)):
            context.step_index = 999  # type: ignore

    def test_step_output_is_frozen(self):
        """StepOutput is frozen (immutable)."""
        output = StepOutput(success=True, output={"key": "value"})

        with pytest.raises((AttributeError, TypeError)):
            output.success = False  # type: ignore

    def test_execution_result_is_frozen(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """ExecutionResult is frozen (immutable)."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
        )

        with pytest.raises((AttributeError, TypeError)):
            result.final_status = JobStatus.FAILED  # type: ignore


# ==============================================================================
# EXEC-006: No Retry Logic
# ==============================================================================


class TestEXEC006NoRetry:
    """EXEC-006: No retry logic."""

    def test_executor_has_no_retry_method(self):
        """Executor has no retry methods."""
        executor = JobExecutor()

        assert not hasattr(executor, "retry")
        assert not hasattr(executor, "retry_step")
        assert not hasattr(executor, "retry_job")
        assert not hasattr(executor, "rerun")

    def test_failed_step_not_retried(
        self,
        job_id,
        contract_id,
    ):
        """Failed step is not automatically retried."""
        call_count = 0

        class CountingFailHandler:
            def execute(self, step: JobStep, context: ExecutionContext) -> StepOutput:
                nonlocal call_count
                call_count += 1
                return StepOutput(success=False, output={}, error="Fail")

        executor = JobExecutor()
        executor.register_handler("counting_fail", CountingFailHandler())

        steps = [
            JobStep(
                step_index=0,
                step_type="counting_fail",
                target="X",
                parameters={},
                timeout_seconds=60,
            )
        ]

        executor.execute_job(job_id=job_id, contract_id=contract_id, steps=steps)

        # Handler should only be called once (no retry)
        assert call_count == 1

    def test_execution_result_is_final(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """Execution result is final - no way to retry."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
        )

        # Result is frozen and cannot be modified
        assert isinstance(result, ExecutionResult)
        assert hasattr(result, "__dataclass_fields__")


# ==============================================================================
# HANDLER TESTS
# ==============================================================================


class TestStepHandlers:
    """Tests for step handlers."""

    def test_noop_handler_always_succeeds(self):
        """NoOpHandler always returns success."""
        handler = NoOpHandler()
        step = JobStep(
            step_index=0,
            step_type="test",
            target="TARGET",
            parameters={},
            timeout_seconds=60,
        )
        context = ExecutionContext(
            job_id=uuid4(),
            contract_id=uuid4(),
            step_index=0,
            step_type="test",
            target="TARGET",
            executed_by="tester",
            started_at=datetime.now(timezone.utc),
        )

        output = handler.execute(step, context)

        assert output.success is True
        assert output.error is None

    def test_failing_handler_always_fails(self):
        """FailingHandler always returns failure."""
        handler = FailingHandler("Test error")
        step = JobStep(
            step_index=0,
            step_type="test",
            target="TARGET",
            parameters={},
            timeout_seconds=60,
        )
        context = ExecutionContext(
            job_id=uuid4(),
            contract_id=uuid4(),
            step_index=0,
            step_type="test",
            target="TARGET",
            executed_by="tester",
            started_at=datetime.now(timezone.utc),
        )

        output = handler.execute(step, context)

        assert output.success is False
        assert output.error == "Test error"

    def test_handler_receives_step_parameters(self):
        """Handler receives step parameters."""
        received_params = {}

        class ParamCaptureHandler:
            def execute(self, step: JobStep, context: ExecutionContext) -> StepOutput:
                received_params.update(step.parameters)
                return StepOutput(success=True, output={})

        executor = JobExecutor()
        executor.register_handler("param_test", ParamCaptureHandler())

        steps = [
            JobStep(
                step_index=0,
                step_type="param_test",
                target="X",
                parameters={"key1": "value1", "key2": 42},
                timeout_seconds=60,
            )
        ]

        executor.execute_job(job_id=uuid4(), contract_id=uuid4(), steps=steps)

        assert received_params == {"key1": "value1", "key2": 42}


# ==============================================================================
# EXECUTOR METADATA
# ==============================================================================


class TestExecutorMetadata:
    """Tests for executor metadata."""

    def test_executor_has_version(self):
        """Executor has version."""
        executor = JobExecutor()
        assert executor.version == EXECUTOR_VERSION

    def test_version_is_semantic(self):
        """Version follows semantic versioning."""
        import re

        pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(pattern, EXECUTOR_VERSION)

    def test_evidence_includes_version(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        single_step,
    ):
        """Evidence includes executor version."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=single_step,
        )

        evidence = execution_result_to_evidence(result)
        assert evidence["executor_version"] == EXECUTOR_VERSION


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================


class TestExecutorIntegration:
    """Integration tests for Job Executor."""

    def test_full_successful_execution(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
        multiple_steps,
    ):
        """Full successful job execution."""
        observer = MockHealthObserver()

        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=multiple_steps,
            health_observer=observer,
            executed_by="integration_test",
        )

        assert result.job_id == job_id
        assert result.final_status == JobStatus.COMPLETED
        assert result.steps_executed == 3
        assert result.steps_succeeded == 3
        assert result.steps_failed == 0
        assert result.health_before is not None
        assert result.health_after is not None
        assert result.completed_at > result.started_at

    def test_partial_execution_on_failure(
        self,
        job_id,
        contract_id,
    ):
        """Partial execution when step fails."""
        executor = JobExecutor()
        executor.register_handler("good", NoOpHandler())
        executor.register_handler("bad", FailingHandler("Boom"))

        steps = [
            JobStep(step_index=0, step_type="good", target="A", parameters={}, timeout_seconds=60),
            JobStep(step_index=1, step_type="good", target="B", parameters={}, timeout_seconds=60),
            JobStep(step_index=2, step_type="bad", target="C", parameters={}, timeout_seconds=60),
            JobStep(step_index=3, step_type="good", target="D", parameters={}, timeout_seconds=60),
        ]

        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=steps,
        )

        assert result.final_status == JobStatus.FAILED
        assert result.steps_executed == 3  # Executed 0, 1, 2 (stopped at 2)
        assert result.steps_succeeded == 2
        assert result.steps_failed == 1
        assert "Step 2 failed" in result.final_reason

    def test_empty_steps_completes(
        self,
        executor: JobExecutor,
        job_id,
        contract_id,
    ):
        """Empty step list completes successfully."""
        result = executor.execute_job(
            job_id=job_id,
            contract_id=contract_id,
            steps=[],
        )

        assert result.final_status == JobStatus.COMPLETED
        assert result.steps_executed == 0
        assert result.steps_succeeded == 0
        assert result.steps_failed == 0
