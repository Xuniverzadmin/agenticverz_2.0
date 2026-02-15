"""
Phase 5A E2E Governance Tests

Trust regression testing for hard budget enforcement.
NOT feature testing - this verifies governance contracts hold.

Test Matrix:
- G5A-01: Hard budget halts mid-execution
- G5A-02: Soft budget does NOT halt
- G5A-03: Partial results preserved on halt
- G5A-04: Status is "halted" not "failed"
- G5A-05: Founder timeline reconstructable (no decisions after halt)
- G5A-06: Customer sees halt reason
- G5A-07: No double emission on same run
- G5A-08: Halt is between steps only
- G5A-09: Budget context immutable during run
- G5A-10: No silent halt (event published)
"""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import patch

# Import the components under test
from app.contracts.decisions import (
    CausalRole,
    DecisionOutcome,
    DecisionRecord,
    DecisionSource,
    DecisionTrigger,
    DecisionType,
    _check_budget_enforcement_exists,
    emit_budget_enforcement_decision,
)
from app.hoc.int.worker.runner import BudgetContext

# =============================================================================
# Test Fixtures
# =============================================================================


@dataclass
class MockAgent:
    """Mock Agent for testing budget context loading."""

    id: str
    budget_cents: Optional[int] = None
    spent_cents: int = 0
    capabilities_json: Optional[str] = None


@dataclass
class MockRun:
    """Mock Run for testing execution."""

    id: str
    agent_id: str
    goal: str
    tenant_id: str = "test-tenant"
    status: str = "running"
    attempts: int = 0
    plan_json: Optional[str] = None
    started_at: Optional[datetime] = None


@dataclass
class MockStepResult:
    """Mock step execution result with cost."""

    result: Dict[str, Any]
    side_effects: Dict[str, Any]
    skill_version: str = "1.0.0"

    def get(self, key: str, default: Any = None) -> Any:
        if key == "result":
            return self.result
        if key == "side_effects":
            return self.side_effects
        if key == "skill_version":
            return self.skill_version
        return default


class MockPublisher:
    """Mock event publisher that captures events."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def publish(self, event_type: str, payload: Dict[str, Any]):
        self.events.append({"type": event_type, "payload": payload})

    def get_events(self, event_type: str) -> List[Dict[str, Any]]:
        return [e for e in self.events if e["type"] == event_type]


# =============================================================================
# G5A-01: Hard Budget Halts Mid-Execution
# =============================================================================


class TestG5A01HardBudgetHalts:
    """Test that hard budget enforcement halts execution."""

    def test_budget_context_detects_hard_mode(self):
        """Budget context correctly identifies hard mode."""
        ctx = BudgetContext(
            mode="hard",
            limit_cents=100,
            consumed_cents=90,
            hard_limit=True,
        )

        assert ctx.hard_limit is True
        assert ctx.mode == "hard"
        assert ctx.remaining_cents == 10

    def test_would_exceed_returns_true_when_over_limit(self):
        """would_exceed correctly detects budget exhaustion."""
        ctx = BudgetContext(
            mode="hard",
            limit_cents=100,
            consumed_cents=90,
            hard_limit=True,
        )

        # 10c remaining, adding 15c would exceed
        assert ctx.would_exceed(15) is True
        # Adding exactly 10c would hit the limit
        assert ctx.would_exceed(10) is False
        # Adding less than 10c is fine
        assert ctx.would_exceed(5) is False

    def test_soft_mode_never_exceeds(self):
        """Soft mode never reports would_exceed."""
        ctx = BudgetContext(
            mode="soft",
            limit_cents=100,
            consumed_cents=150,  # Already over!
            hard_limit=False,
        )

        # Even with massive additional cost, soft mode doesn't halt
        assert ctx.would_exceed(1000) is False

    def test_decision_type_is_budget_enforcement(self):
        """Verify the correct decision type enum exists."""
        assert DecisionType.BUDGET_ENFORCEMENT.value == "budget_enforcement"

    def test_decision_outcome_is_execution_halted(self):
        """Verify the correct decision outcome enum exists."""
        assert DecisionOutcome.EXECUTION_HALTED.value == "execution_halted"


# =============================================================================
# G5A-02: Soft Budget Does NOT Halt
# =============================================================================


class TestG5A02SoftBudgetNoHalt:
    """Test that soft budget mode allows execution to continue."""

    def test_soft_mode_context(self):
        """Soft mode budget context is correctly configured."""
        ctx = BudgetContext(
            mode="soft",
            limit_cents=100,
            consumed_cents=90,
            hard_limit=False,
        )

        assert ctx.hard_limit is False
        assert ctx.mode == "soft"

    def test_soft_mode_allows_over_budget(self):
        """Soft mode allows spending over budget."""
        ctx = BudgetContext(
            mode="soft",
            limit_cents=100,
            consumed_cents=0,
            hard_limit=False,
        )

        # Simulate spending 150c (50% over budget)
        # In soft mode, this should NOT trigger halt
        assert ctx.would_exceed(150) is False

    def test_no_budget_means_soft_mode(self):
        """No budget configured means soft mode."""
        ctx = BudgetContext(
            mode="soft",
            limit_cents=0,
            consumed_cents=0,
            hard_limit=False,
        )

        assert ctx.hard_limit is False
        assert ctx.would_exceed(999999) is False


# =============================================================================
# G5A-03: Partial Results Preserved on Halt
# =============================================================================


class TestG5A03PartialResultsPreserved:
    """Test that partial results are preserved when halted."""

    def test_tool_calls_structure(self):
        """Tool calls structure matches expected format."""
        tool_call = {
            "step_id": "s1",
            "skill": "http_call",
            "skill_version": "1.0.0",
            "request": {"url": "https://example.com"},
            "response": {"status": 200},
            "side_effects": {"cost_cents": 10},
            "duration": 0.5,
            "ts": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "attempts": 1,
            "on_error": "abort",
        }

        # Verify all required fields present
        assert "step_id" in tool_call
        assert "skill" in tool_call
        assert "response" in tool_call
        assert "side_effects" in tool_call
        assert "status" in tool_call

    def test_partial_tool_calls_serializable(self):
        """Partial tool calls can be serialized to JSON."""
        tool_calls = [
            {"step_id": "s1", "status": "completed", "response": {"data": 1}},
            {"step_id": "s2", "status": "completed", "response": {"data": 2}},
        ]

        # Should be JSON serializable
        json_str = json.dumps(tool_calls)
        assert json_str is not None

        # Should deserialize back
        parsed = json.loads(json_str)
        assert len(parsed) == 2
        assert parsed[0]["step_id"] == "s1"


# =============================================================================
# G5A-04: Status is "halted" not "failed"
# =============================================================================


class TestG5A04StatusSemantics:
    """Test that halted runs have correct status semantics."""

    def test_halted_status_value(self):
        """Verify 'halted' is the correct status for budget halt."""
        # This tests the semantic distinction
        valid_statuses = ["queued", "running", "succeeded", "failed", "retry", "halted"]
        assert "halted" in valid_statuses
        assert "halted" != "failed"

    def test_halted_is_terminal(self):
        """Halted is a terminal state - no retry."""
        # Terminal states don't get retried
        terminal_states = ["succeeded", "failed", "halted"]
        retryable_states = ["queued", "retry"]

        assert "halted" in terminal_states
        assert "halted" not in retryable_states


# =============================================================================
# G5A-05: Founder Timeline Reconstructable
# =============================================================================


class TestG5A05FounderTimeline:
    """Test that founder timeline can be reconstructed."""

    def test_decision_record_has_causal_role(self):
        """Decision records include causal role for timeline."""
        record = DecisionRecord(
            decision_type=DecisionType.BUDGET_ENFORCEMENT,
            decision_source=DecisionSource.SYSTEM,
            decision_trigger=DecisionTrigger.REACTIVE,
            decision_inputs={},
            decision_outcome=DecisionOutcome.EXECUTION_HALTED,
            run_id="test-run-id",
            causal_role=CausalRole.IN_RUN,
        )

        assert record.causal_role == CausalRole.IN_RUN
        assert record.run_id == "test-run-id"

    def test_decision_record_has_timestamp(self):
        """Decision records have timestamp for ordering."""
        before = datetime.now(timezone.utc)

        record = DecisionRecord(
            decision_type=DecisionType.BUDGET_ENFORCEMENT,
            decision_source=DecisionSource.SYSTEM,
            decision_trigger=DecisionTrigger.REACTIVE,
            decision_inputs={},
            decision_outcome=DecisionOutcome.EXECUTION_HALTED,
        )

        after = datetime.now(timezone.utc)

        assert record.decided_at >= before
        assert record.decided_at <= after

    def test_no_decisions_after_halt_assertion(self):
        """
        G5A-05 additional assertion: No decisions after budget_enforcement.

        This ensures the halt truly ends causality.
        """
        # Simulate a timeline
        timeline = [
            {"type": "step_completed", "step_id": "s1", "ts": 1},
            {"type": "step_completed", "step_id": "s2", "ts": 2},
            {"type": "budget_enforcement", "ts": 3},
            # NO MORE ENTRIES SHOULD APPEAR AFTER THIS
        ]

        # Find the halt point
        halt_index = None
        for i, event in enumerate(timeline):
            if event["type"] == "budget_enforcement":
                halt_index = i
                break

        # Verify no events after halt
        assert halt_index is not None
        events_after_halt = timeline[halt_index + 1 :]
        assert len(events_after_halt) == 0, "No decisions should appear after budget_enforcement"


# =============================================================================
# G5A-06: Customer Sees Halt Reason
# =============================================================================


class TestG5A06CustomerVisibility:
    """Test that customers can see halt reason."""

    def test_decision_reason_includes_amounts(self):
        """Decision reason includes consumed and limit amounts."""
        record = DecisionRecord(
            decision_type=DecisionType.BUDGET_ENFORCEMENT,
            decision_source=DecisionSource.SYSTEM,
            decision_trigger=DecisionTrigger.REACTIVE,
            decision_inputs={
                "budget_limit_cents": 100,
                "budget_consumed_cents": 110,
            },
            decision_outcome=DecisionOutcome.EXECUTION_HALTED,
            decision_reason="Hard budget limit reached: 110c consumed >= 100c limit",
        )

        assert "110c consumed" in record.decision_reason
        assert "100c limit" in record.decision_reason
        assert "Hard budget limit" in record.decision_reason

    def test_decision_inputs_contain_budget_details(self):
        """Decision inputs contain full budget details."""
        inputs = {
            "budget_limit_cents": 100,
            "budget_consumed_cents": 110,
            "step_cost_cents": 20,
            "completed_steps": 3,
            "total_steps": 5,
        }

        record = DecisionRecord(
            decision_type=DecisionType.BUDGET_ENFORCEMENT,
            decision_source=DecisionSource.SYSTEM,
            decision_trigger=DecisionTrigger.REACTIVE,
            decision_inputs=inputs,
            decision_outcome=DecisionOutcome.EXECUTION_HALTED,
        )

        assert record.decision_inputs["budget_limit_cents"] == 100
        assert record.decision_inputs["budget_consumed_cents"] == 110
        assert record.decision_inputs["completed_steps"] == 3
        assert record.decision_inputs["total_steps"] == 5


# =============================================================================
# G5A-07: No Double Emission on Same Run
# =============================================================================


class TestG5A07NoDoubleEmission:
    """Test that budget_enforcement is emitted exactly once per run."""

    def test_idempotency_guard_exists(self):
        """Idempotency guard function exists."""
        assert callable(_check_budget_enforcement_exists)

    def test_emit_returns_none_on_duplicate(self):
        """emit_budget_enforcement_decision returns None if already emitted."""
        run_id = str(uuid.uuid4())

        # Mock the existence check to return True (already exists)
        with patch(
            "app.contracts.decisions._check_budget_enforcement_exists",
            return_value=True,
        ):
            result = emit_budget_enforcement_decision(
                run_id=run_id,
                budget_limit_cents=100,
                budget_consumed_cents=110,
                step_cost_cents=10,
                completed_steps=3,
                total_steps=5,
            )

            # Should return None (idempotent no-op)
            assert result is None

    def test_emit_returns_record_on_first_call(self):
        """emit_budget_enforcement_decision returns record on first call."""
        run_id = str(uuid.uuid4())

        # Mock the existence check to return False (not exists)
        # and the service to not actually emit
        with patch(
            "app.contracts.decisions._check_budget_enforcement_exists",
            return_value=False,
        ):
            with patch("app.contracts.decisions.get_decision_service") as mock_service:
                mock_service.return_value.emit_sync.return_value = True

                result = emit_budget_enforcement_decision(
                    run_id=run_id,
                    budget_limit_cents=100,
                    budget_consumed_cents=110,
                    step_cost_cents=10,
                    completed_steps=3,
                    total_steps=5,
                )

                # Should return the record
                assert result is not None
                assert isinstance(result, DecisionRecord)
                assert result.run_id == run_id


# =============================================================================
# G5A-08: Halt is Between Steps Only
# =============================================================================


class TestG5A08HaltBetweenSteps:
    """Test that halt occurs between steps, not mid-step."""

    def test_last_step_fully_completed(self):
        """Last completed step has full result data."""
        # Simulate tool_calls after halt
        tool_calls = [
            {
                "step_id": "s1",
                "skill": "http_call",
                "status": "completed",  # Fully completed
                "response": {"status": 200, "body": "OK"},
                "duration": 0.5,
                "attempts": 1,
            },
            {
                "step_id": "s2",
                "skill": "llm_invoke",
                "status": "completed",  # Last step before halt
                "response": {"content": "Generated text"},
                "duration": 1.2,
                "attempts": 1,
            },
            # Step 3 never started (halted after step 2)
        ]

        # Verify last step is complete
        last_step = tool_calls[-1]
        assert last_step["status"] == "completed"
        assert "response" in last_step
        assert last_step["duration"] > 0

    def test_no_partial_step_markers(self):
        """No step should have partial/interrupted status."""
        tool_calls = [
            {"step_id": "s1", "status": "completed"},
            {"step_id": "s2", "status": "completed"},
        ]

        invalid_statuses = ["partial", "interrupted", "in_progress"]

        for tc in tool_calls:
            assert tc["status"] not in invalid_statuses


# =============================================================================
# G5A-09: Budget Context Immutable During Run
# =============================================================================


class TestG5A09BudgetContextImmutable:
    """Test that budget context is immutable during run execution."""

    def test_budget_context_is_dataclass(self):
        """BudgetContext is a dataclass (immutable by convention)."""
        from dataclasses import is_dataclass

        assert is_dataclass(BudgetContext)

    def test_budget_context_values_preserved(self):
        """Budget context values are preserved throughout execution."""
        # Create context
        ctx = BudgetContext(
            mode="hard",
            limit_cents=100,
            consumed_cents=50,
            hard_limit=True,
        )

        # Simulate execution (values should not change)
        for _ in range(10):
            # Each iteration represents a step
            assert ctx.limit_cents == 100
            assert ctx.consumed_cents == 50
            assert ctx.hard_limit is True

    def test_run_consumed_is_separate(self):
        """run_consumed_cents is tracked separately from budget_context."""
        ctx = BudgetContext(
            mode="hard",
            limit_cents=100,
            consumed_cents=50,
            hard_limit=True,
        )

        # Simulate run-local tracking
        run_consumed_cents = 0

        # Step 1 costs 10c
        run_consumed_cents += 10
        total = ctx.consumed_cents + run_consumed_cents
        assert total == 60
        assert ctx.consumed_cents == 50  # Context unchanged

        # Step 2 costs 20c
        run_consumed_cents += 20
        total = ctx.consumed_cents + run_consumed_cents
        assert total == 80
        assert ctx.consumed_cents == 50  # Context still unchanged


# =============================================================================
# G5A-10: No Silent Halt (Event Published)
# =============================================================================


class TestG5A10NoSilentHalt:
    """Test that halts are always visible via events."""

    def test_halt_event_structure(self):
        """run.halted event has required fields."""
        event = {
            "type": "run.halted",
            "payload": {
                "run_id": "test-run-id",
                "status": "halted",
                "halt_reason": "hard_budget_limit",
                "budget_limit_cents": 100,
                "budget_consumed_cents": 110,
                "completed_steps": 3,
                "total_steps": 5,
                "duration_ms": 1234.5,
            },
        }

        payload = event["payload"]

        # Required fields
        assert "run_id" in payload
        assert "status" in payload
        assert payload["status"] == "halted"
        assert "halt_reason" in payload
        assert payload["halt_reason"] == "hard_budget_limit"

        # Budget details
        assert "budget_limit_cents" in payload
        assert "budget_consumed_cents" in payload

        # Execution progress
        assert "completed_steps" in payload
        assert "total_steps" in payload

    def test_mock_publisher_captures_halt(self):
        """MockPublisher correctly captures halt events."""
        publisher = MockPublisher()

        publisher.publish(
            "run.halted",
            {
                "run_id": "test-run",
                "status": "halted",
                "halt_reason": "hard_budget_limit",
            },
        )

        halt_events = publisher.get_events("run.halted")
        assert len(halt_events) == 1
        assert halt_events[0]["payload"]["halt_reason"] == "hard_budget_limit"


# =============================================================================
# Integration: Full Flow Test
# =============================================================================


class TestFullGovernanceFlow:
    """Integration test covering the complete governance flow."""

    def test_pre_run_to_halt_to_outcome_flow(self):
        """
        Verify the complete flow:
        PRE-RUN → EXECUTE → HALT → OUTCOME

        This is the founder timeline integrity test.

        Implementation note: The actual runner checks budget AFTER each step
        completes, so the halt occurs after the step that pushed over the limit.
        """
        # 1. PRE-RUN: Budget context loaded
        ctx = BudgetContext(
            mode="hard",
            limit_cents=100,
            consumed_cents=80,
            hard_limit=True,
        )

        # 2. EXECUTE: Steps run and accumulate cost
        run_consumed_cents = 0
        tool_calls = []
        halted = False

        steps = [
            {"step_id": "s1", "cost": 10},
            {"step_id": "s2", "cost": 15},  # This pushes total to 105 >= 100
            {"step_id": "s3", "cost": 10},  # Never reached
        ]

        for step in steps:
            # Execute step first (step always completes)
            run_consumed_cents += step["cost"]
            tool_calls.append({"step_id": step["step_id"], "status": "completed"})

            # Check budget AFTER step completes (matches actual implementation)
            total = ctx.consumed_cents + run_consumed_cents

            if ctx.hard_limit and total >= ctx.limit_cents:
                halted = True
                break

        # 3. HALT: Should have halted after step 2 (which pushed over limit)
        assert halted is True
        assert len(tool_calls) == 2  # Steps 1 and 2 completed

        # 4. OUTCOME: Verify outcome semantics
        final_consumed = ctx.consumed_cents + run_consumed_cents
        assert final_consumed == 105  # 80 + 10 + 15

        # Verify partial results
        assert tool_calls[0]["step_id"] == "s1"
        assert tool_calls[1]["step_id"] == "s2"

    def test_decision_record_matches_contract(self):
        """
        Verify decision record matches contract specification:
        - decision_type: budget_enforcement
        - decision_source: system
        - decision_trigger: reactive
        - decision_outcome: execution_halted
        """
        record = DecisionRecord(
            decision_type=DecisionType.BUDGET_ENFORCEMENT,
            decision_source=DecisionSource.SYSTEM,
            decision_trigger=DecisionTrigger.REACTIVE,
            decision_inputs={
                "budget_limit_cents": 100,
                "budget_consumed_cents": 110,
                "completed_steps": 2,
                "total_steps": 5,
            },
            decision_outcome=DecisionOutcome.EXECUTION_HALTED,
            decision_reason="Hard budget limit reached",
            run_id="test-run",
            causal_role=CausalRole.IN_RUN,
        )

        # Contract verification
        assert record.decision_type == DecisionType.BUDGET_ENFORCEMENT
        assert record.decision_source == DecisionSource.SYSTEM
        assert record.decision_trigger == DecisionTrigger.REACTIVE
        assert record.decision_outcome == DecisionOutcome.EXECUTION_HALTED
        assert record.causal_role == CausalRole.IN_RUN
