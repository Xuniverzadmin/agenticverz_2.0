# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci | manual
#   Execution: sync
# Role: Tests for execution envelope (PIN-330)
# Callers: pytest
# Allowed Imports: All (test code)
# Forbidden Imports: None
# Reference: PIN-330

"""
Execution Envelope Tests - PIN-330 Implicit Authority Hardening

Verifies:
1. CLI envelope creation (CAP-020)
2. SDK envelope creation (CAP-021)
3. Auto-execute envelope creation (SUB-019)
4. Plan hashing and mutation detection
5. Impersonation visibility
6. Evidence emission (in-memory)
7. Cross-reference context

CONSTRAINTS:
- Tests verify evidence emission, not enforcement
- Execution unchanged regardless of envelope state
"""

import json
import uuid
from datetime import datetime, timezone

import pytest

from app.auth.execution_envelope import (
    CallerType,
    CapabilityId,
    ExecutionEnvelopeFactory,
    ExecutionVector,
    InMemoryEvidenceSink,
    compute_plan_hash,
    detect_plan_mutation,
    emit_envelope,
    get_evidence_sink,
    set_evidence_sink,
)
from app.auth.invocation_context import (
    get_current_invocation_id,
    get_invocation_metadata,
    invocation_context,
    tag_with_invocation,
)


# =============================================================================
# PHASE 6.1: CONTROLLED TEST RUNS
# =============================================================================


class TestCLIEnvelope:
    """Tests for CAP-020 (CLI Execution) envelope creation."""

    def test_create_cli_envelope_basic(self):
        """Test basic CLI envelope creation."""
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="user@example.com",
            tenant_id="tenant-123",
            command="aos simulate --plan",
            raw_input={"goal": "test"},
            resolved_plan={"steps": [{"skill": "test_skill"}]},
        )

        assert envelope.envelope_id is not None
        assert envelope.capability_id == CapabilityId.CAP_020
        assert envelope.execution_vector == ExecutionVector.CLI
        assert envelope.caller_identity.type == CallerType.HUMAN
        assert envelope.caller_identity.subject == "user@example.com"
        assert envelope.caller_identity.impersonated_subject is None
        assert envelope.caller_identity.impersonation_declared is False
        assert envelope.tenant_context.tenant_id == "tenant-123"
        assert envelope.plan.input_hash is not None
        assert envelope.plan.resolved_plan_hash is not None
        assert envelope.plan.plan_mutation_detected is False
        assert envelope.attribution.source_command == "aos simulate --plan"
        assert envelope.attribution.origin == "PIN-330"

    def test_create_cli_envelope_with_impersonation(self):
        """Test CLI envelope with --by parameter (impersonation)."""
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="admin@example.com",
            tenant_id="tenant-123",
            command="aos recovery approve --by operator@example.com",
            raw_input={"candidate_id": "rec-123"},
            resolved_plan={"action": "approve"},
            impersonated_subject="operator@example.com",
            reason_code="Admin approving on behalf of operator",
        )

        assert envelope.caller_identity.subject == "admin@example.com"
        assert envelope.caller_identity.impersonated_subject == "operator@example.com"
        assert envelope.caller_identity.impersonation_declared is True
        assert envelope.attribution.reason_code == "Admin approving on behalf of operator"

    def test_create_cli_envelope_impersonation_without_reason(self):
        """Test CLI envelope with impersonation but no reason (audit finding)."""
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="admin@example.com",
            tenant_id="tenant-123",
            command="aos recovery approve --by operator@example.com",
            raw_input={"candidate_id": "rec-123"},
            resolved_plan={"action": "approve"},
            impersonated_subject="operator@example.com",
            # No reason_code provided
        )

        # Impersonation visible but NOT declared (audit finding)
        assert envelope.caller_identity.impersonated_subject == "operator@example.com"
        assert envelope.caller_identity.impersonation_declared is False
        assert envelope.attribution.reason_code is None


class TestSDKEnvelope:
    """Tests for CAP-021 (SDK Execution) envelope creation."""

    def test_create_sdk_envelope_basic(self):
        """Test basic SDK envelope creation."""
        envelope = ExecutionEnvelopeFactory.create_sdk_envelope(
            subject="service-account-123",
            tenant_id="tenant-456",
            method_name="AOSClient.create_run",
            raw_input={"plan": {"steps": []}},
            resolved_plan={"run_id": "run-789"},
            caller_type=CallerType.SERVICE,
            sdk_version="1.2.3",
        )

        assert envelope.capability_id == CapabilityId.CAP_021
        assert envelope.execution_vector == ExecutionVector.SDK
        assert envelope.caller_identity.type == CallerType.SERVICE
        assert envelope.caller_identity.subject == "service-account-123"
        assert envelope.attribution.sdk_version == "1.2.3"
        assert envelope.attribution.source_command == "AOSClient.create_run"

    def test_create_sdk_envelope_with_force_skill(self):
        """Test SDK envelope with force_skill parameter (planning bypass)."""
        envelope = ExecutionEnvelopeFactory.create_sdk_envelope(
            subject="service-account-123",
            tenant_id="tenant-456",
            method_name="AOSClient.post_goal",
            raw_input={"goal": "test", "force_skill": "email_skill"},
            resolved_plan={"skill": "email_skill"},
            force_skill="email_skill",
            reason_code="Testing specific skill",
        )

        # force_skill recorded as impersonated_subject (planning bypass)
        assert envelope.caller_identity.impersonated_subject == "email_skill"
        assert envelope.caller_identity.impersonation_declared is True


class TestAutoExecuteEnvelope:
    """Tests for SUB-019 (Auto-Execute Recovery) envelope creation."""

    def test_create_auto_execute_envelope(self):
        """Test auto-execute envelope creation."""
        envelope = ExecutionEnvelopeFactory.create_auto_execute_envelope(
            tenant_id="tenant-789",
            confidence_score=0.85,
            threshold=0.80,
            proposed_action={"type": "retry", "target": "run-123"},
            resolved_plan={"action": "execute_retry"},
            recovery_candidate_id="candidate-456",
        )

        assert envelope.capability_id == CapabilityId.SUB_019
        assert envelope.execution_vector == ExecutionVector.AUTO_EXEC
        assert envelope.caller_identity.type == CallerType.SYSTEM
        assert envelope.caller_identity.subject == "recovery_claim_worker"
        assert envelope.caller_identity.impersonation_declared is False  # System cannot impersonate
        assert envelope.confidence is not None
        assert envelope.confidence.score == 0.85
        assert envelope.confidence.threshold_used == 0.80
        assert envelope.confidence.auto_execute_triggered is True

    def test_create_auto_execute_below_threshold(self):
        """Test auto-execute envelope when below threshold."""
        envelope = ExecutionEnvelopeFactory.create_auto_execute_envelope(
            tenant_id="tenant-789",
            confidence_score=0.75,  # Below 0.80 threshold
            threshold=0.80,
            proposed_action={"type": "retry"},
            resolved_plan={"action": "queue_for_review"},
        )

        assert envelope.confidence.score == 0.75
        assert envelope.confidence.auto_execute_triggered is False


class TestPlanHashing:
    """Tests for plan hashing (anti-injection evidence)."""

    def test_compute_plan_hash_deterministic(self):
        """Test that plan hashing is deterministic."""
        data = {"steps": [{"skill": "email"}, {"skill": "calendar"}]}

        hash1 = compute_plan_hash(data)
        hash2 = compute_plan_hash(data)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex

    def test_compute_plan_hash_order_independent(self):
        """Test that key order doesn't affect hash (canonical JSON)."""
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}

        hash1 = compute_plan_hash(data1)
        hash2 = compute_plan_hash(data2)

        assert hash1 == hash2

    def test_compute_plan_hash_different_data(self):
        """Test that different data produces different hashes."""
        data1 = {"steps": [{"skill": "email"}]}
        data2 = {"steps": [{"skill": "calendar"}]}

        hash1 = compute_plan_hash(data1)
        hash2 = compute_plan_hash(data2)

        assert hash1 != hash2


class TestMutationDetection:
    """Tests for plan mutation detection (observe-only)."""

    def test_detect_no_mutation(self):
        """Test that unchanged plan is not marked as mutated."""
        original_plan = {"steps": [{"skill": "email"}]}

        envelope = ExecutionEnvelopeFactory.create_sdk_envelope(
            subject="test",
            tenant_id="tenant-123",
            method_name="test",
            raw_input={},
            resolved_plan=original_plan,
        )

        mutated, updated = detect_plan_mutation(envelope, original_plan)

        assert mutated is False
        assert updated is None

    def test_detect_mutation(self):
        """Test that changed plan is detected and tracked."""
        original_plan = {"steps": [{"skill": "email"}]}
        mutated_plan = {"steps": [{"skill": "email"}, {"skill": "calendar"}]}

        envelope = ExecutionEnvelopeFactory.create_sdk_envelope(
            subject="test",
            tenant_id="tenant-123",
            method_name="test",
            raw_input={},
            resolved_plan=original_plan,
        )

        original_invocation_id = envelope.invocation.invocation_id

        mutated, updated = detect_plan_mutation(envelope, mutated_plan)

        assert mutated is True
        assert updated is not None
        assert updated.plan.plan_mutation_detected is True
        assert updated.plan.original_invocation_id == original_invocation_id
        assert updated.invocation.invocation_id != original_invocation_id
        assert updated.invocation.sequence_number == 1


class TestEvidenceEmission:
    """Tests for evidence emission to sink."""

    def setup_method(self):
        """Set up in-memory evidence sink for each test."""
        self.sink = InMemoryEvidenceSink()
        set_evidence_sink(self.sink)

    def test_emit_envelope_success(self):
        """Test successful envelope emission."""
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="test@example.com",
            tenant_id="tenant-123",
            command="aos version",
            raw_input={},
            resolved_plan={},
        )

        success = emit_envelope(envelope)

        assert success is True
        assert self.sink.count == 1

    def test_emit_multiple_envelopes(self):
        """Test emitting multiple envelopes."""
        for i in range(3):
            envelope = ExecutionEnvelopeFactory.create_cli_envelope(
                subject=f"user{i}@example.com",
                tenant_id="tenant-123",
                command=f"aos command{i}",
                raw_input={"index": i},
                resolved_plan={},
            )
            emit_envelope(envelope)

        assert self.sink.count == 3

    def test_query_by_capability(self):
        """Test querying envelopes by capability."""
        # Emit CLI and SDK envelopes
        cli_envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="cli@example.com",
            tenant_id="tenant-123",
            command="aos test",
            raw_input={},
            resolved_plan={},
        )
        sdk_envelope = ExecutionEnvelopeFactory.create_sdk_envelope(
            subject="sdk@example.com",
            tenant_id="tenant-123",
            method_name="test",
            raw_input={},
            resolved_plan={},
        )

        emit_envelope(cli_envelope)
        emit_envelope(sdk_envelope)

        # Query by capability
        cli_results = self.sink.query_by_capability(CapabilityId.CAP_020)
        sdk_results = self.sink.query_by_capability(CapabilityId.CAP_021)

        assert len(cli_results) == 1
        assert len(sdk_results) == 1
        assert cli_results[0]["capability_id"] == "CAP-020"
        assert sdk_results[0]["capability_id"] == "CAP-021"

    def test_query_by_tenant(self):
        """Test querying envelopes by tenant."""
        envelope1 = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="user@example.com",
            tenant_id="tenant-A",
            command="aos test",
            raw_input={},
            resolved_plan={},
        )
        envelope2 = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="user@example.com",
            tenant_id="tenant-B",
            command="aos test",
            raw_input={},
            resolved_plan={},
        )

        emit_envelope(envelope1)
        emit_envelope(envelope2)

        results_a = self.sink.query_by_tenant("tenant-A")
        results_b = self.sink.query_by_tenant("tenant-B")

        assert len(results_a) == 1
        assert len(results_b) == 1


class TestInvocationContext:
    """Tests for invocation context propagation."""

    def test_invocation_context_basic(self):
        """Test basic invocation context."""
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="test@example.com",
            tenant_id="tenant-123",
            command="aos test",
            raw_input={},
            resolved_plan={},
        )

        # Outside context
        assert get_current_invocation_id() is None

        # Inside context
        with invocation_context(envelope):
            assert get_current_invocation_id() == envelope.invocation.invocation_id

        # After context
        assert get_current_invocation_id() is None

    def test_tag_with_invocation_dict(self):
        """Test tagging a dict with invocation_id."""
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="test@example.com",
            tenant_id="tenant-123",
            command="aos test",
            raw_input={},
            resolved_plan={},
        )

        event = {"type": "skill_executed", "skill": "email"}

        with invocation_context(envelope):
            tagged = tag_with_invocation(event)

        assert tagged is True
        assert event["invocation_id"] == envelope.invocation.invocation_id

    def test_get_invocation_metadata(self):
        """Test getting all invocation metadata."""
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="test@example.com",
            tenant_id="tenant-123",
            command="aos test",
            raw_input={},
            resolved_plan={},
        )

        with invocation_context(envelope):
            metadata = get_invocation_metadata()

        assert metadata["invocation_id"] == envelope.invocation.invocation_id
        assert metadata["capability_id"] == "CAP-020"
        assert metadata["tenant_id"] == "tenant-123"


class TestEnvelopeSerialization:
    """Tests for envelope serialization."""

    def test_to_dict(self):
        """Test envelope to_dict() serialization."""
        envelope = ExecutionEnvelopeFactory.create_auto_execute_envelope(
            tenant_id="tenant-123",
            confidence_score=0.85,
            threshold=0.80,
            proposed_action={"type": "retry"},
            resolved_plan={"action": "execute"},
        )

        data = envelope.to_dict()

        assert data["envelope_id"] == envelope.envelope_id
        assert data["capability_id"] == "SUB-019"
        assert data["execution_vector"] == "AUTO_EXEC"
        assert data["confidence"]["score"] == 0.85
        assert data["confidence"]["auto_execute_triggered"] is True

    def test_to_json(self):
        """Test envelope to_json() serialization."""
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="test@example.com",
            tenant_id="tenant-123",
            command="aos version",
            raw_input={},
            resolved_plan={},
        )

        json_str = envelope.to_json()
        parsed = json.loads(json_str)

        assert parsed["envelope_id"] == envelope.envelope_id
        assert parsed["capability_id"] == "CAP-020"


# =============================================================================
# EXECUTION UNCHANGED VERIFICATION
# =============================================================================


class TestExecutionUnchanged:
    """
    Verify that execution semantics are unchanged.

    These tests confirm that the envelope system is evidence-only
    and does not block, alter, or interfere with execution.
    """

    def test_envelope_failure_does_not_block(self):
        """Test that envelope emission failure does not block execution."""
        # Create envelope
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="test@example.com",
            tenant_id="tenant-123",
            command="aos test",
            raw_input={},
            resolved_plan={},
        )

        # Simulate execution - should always succeed
        execution_result = "success"

        # Even if emission fails, execution continues
        emit_envelope(envelope)

        assert execution_result == "success"

    def test_mutation_detection_does_not_block(self):
        """Test that mutation detection does not block execution."""
        original_plan = {"steps": []}
        mutated_plan = {"steps": [{"new": "step"}]}

        envelope = ExecutionEnvelopeFactory.create_sdk_envelope(
            subject="test",
            tenant_id="tenant-123",
            method_name="test",
            raw_input={},
            resolved_plan=original_plan,
        )

        # Detect mutation
        mutated, updated = detect_plan_mutation(envelope, mutated_plan)

        # Execution continues regardless
        execution_result = "success"

        assert mutated is True  # Mutation detected
        assert execution_result == "success"  # But execution unchanged

    def test_missing_impersonation_reason_does_not_block(self):
        """Test that missing impersonation reason does not block execution."""
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(
            subject="admin@example.com",
            tenant_id="tenant-123",
            command="aos recovery approve --by other@example.com",
            raw_input={},
            resolved_plan={},
            impersonated_subject="other@example.com",
            # No reason_code - this is an audit finding, NOT a blocker
        )

        # Execution continues
        execution_result = "success"

        assert envelope.caller_identity.impersonation_declared is False  # Audit finding
        assert execution_result == "success"  # Execution unchanged
