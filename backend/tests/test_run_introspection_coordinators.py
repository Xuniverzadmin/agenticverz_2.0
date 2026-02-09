# Layer: Test
# AUDIENCE: INTERNAL
# Role: Unit tests for PIN-519 run introspection coordinators
# Reference: PIN-519 System Run Introspection

"""
Run Introspection Coordinator Tests (PIN-519)

Tests for:
- RunEvidenceCoordinator: Cross-domain evidence aggregation
- RunProofCoordinator: Integrity verification via traces
- SignalFeedbackCoordinator: Signal feedback from audit ledger
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.hoc.cus.hoc_spine.schemas.run_introspection_protocols import (
    IncidentSummary,
    PolicyEvaluationSummary,
    LimitHitSummary,
    DecisionSummary,
    RunEvidenceResult,
    IntegrityVerificationResult,
    RunProofResult,
    SignalFeedbackResult,
    INTEGRITY_CONFIG,
)


class TestRunEvidenceCoordinator:
    """Tests for RunEvidenceCoordinator."""

    @pytest.mark.asyncio
    async def test_composes_cross_domain_evidence(self):
        """Coordinator aggregates evidence from all domains."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_evidence_coordinator import (
            RunEvidenceCoordinator,
        )

        coordinator = RunEvidenceCoordinator()
        session = AsyncMock()
        tenant_id = "tenant-123"
        run_id = "run-456"

        # Mock bridge capabilities (patch at source, not lazy import site)
        with patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.incidents_bridge.get_incidents_bridge"
        ) as mock_incidents, patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.policies_bridge.get_policies_bridge"
        ) as mock_policies, patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.controls_bridge.get_controls_bridge"
        ) as mock_controls:
            # Setup mock incident reader (async — returns list of dicts)
            incident_reader = AsyncMock()
            incident_reader.fetch_incidents_by_run_id.return_value = []
            mock_incidents.return_value.incidents_for_run_capability.return_value = incident_reader

            # Setup mock policy reader (returns prevention_records dicts)
            policy_reader = AsyncMock()
            policy_reader.fetch_policy_evaluations_for_run.return_value = [
                {
                    "policy_id": "rule-1",
                    "rule_name": "Test Rule",
                    "outcome": "WARNED",
                    "created_at": datetime.now(timezone.utc),
                }
            ]
            mock_policies.return_value.policy_evaluations_capability.return_value = policy_reader

            # Setup mock controls reader
            controls_reader = AsyncMock()
            controls_reader.fetch_limit_breaches_for_run.return_value = [
                {
                    "limit_id": "limit-1",
                    "limit_name": "Budget Limit",
                    "value_at_breach": 100.0,
                    "threshold_value": 90.0,
                    "breached_at": datetime.now(timezone.utc),
                }
            ]
            mock_controls.return_value.limit_breaches_capability.return_value = controls_reader

            result = await coordinator.get_run_evidence(session, tenant_id, run_id)

            assert result.run_id == run_id
            assert len(result.policies_evaluated) == 1
            assert result.policies_evaluated[0].policy_name == "Test Rule"
            assert len(result.limits_hit) == 1
            assert result.limits_hit[0].limit_name == "Budget Limit"
            assert len(result.decisions_made) == 1  # WARNED creates a decision

    @pytest.mark.asyncio
    async def test_returns_empty_lists_when_no_impact(self):
        """Coordinator returns empty lists when run has no cross-domain impact."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_evidence_coordinator import (
            RunEvidenceCoordinator,
        )

        coordinator = RunEvidenceCoordinator()
        session = AsyncMock()

        with patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.incidents_bridge.get_incidents_bridge"
        ) as mock_incidents, patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.policies_bridge.get_policies_bridge"
        ) as mock_policies, patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.controls_bridge.get_controls_bridge"
        ) as mock_controls:
            # All bridges return empty
            incident_reader = AsyncMock()
            incident_reader.fetch_incidents_by_run_id.return_value = []
            mock_incidents.return_value.incidents_for_run_capability.return_value = incident_reader

            policy_reader = AsyncMock()
            policy_reader.fetch_policy_evaluations_for_run.return_value = []
            mock_policies.return_value.policy_evaluations_capability.return_value = policy_reader

            controls_reader = AsyncMock()
            controls_reader.fetch_limit_breaches_for_run.return_value = []
            mock_controls.return_value.limit_breaches_capability.return_value = controls_reader

            result = await coordinator.get_run_evidence(session, "tenant-123", "run-456")

            assert result.run_id == "run-456"
            assert result.incidents_caused == []
            assert result.policies_evaluated == []
            assert result.limits_hit == []
            assert result.decisions_made == []


class TestRunProofCoordinator:
    """Tests for RunProofCoordinator."""

    @pytest.mark.asyncio
    async def test_returns_verified_with_valid_chain(self):
        """Coordinator returns VERIFIED when trace has valid hash chain."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_proof_coordinator import (
            RunProofCoordinator,
        )

        coordinator = RunProofCoordinator()
        session = AsyncMock()

        # Create mock trace with steps
        mock_trace = MagicMock()
        mock_trace.run_id = "run-123"
        mock_trace.status = MagicMock(value="completed")
        mock_trace.started_at = datetime.now(timezone.utc)
        mock_trace.completed_at = datetime.now(timezone.utc)

        mock_step = MagicMock()
        mock_step.step_index = 0
        mock_step.skill_name = "test_skill"
        mock_step.status = MagicMock(value="completed")
        mock_step.duration_ms = 100.0
        mock_step.cost_cents = 0.5
        mock_trace.steps = [mock_step]

        with patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge.get_logs_bridge"
        ) as mock_bridge:
            trace_store = AsyncMock()
            trace_store.get_trace.return_value = mock_trace
            mock_bridge.return_value.traces_store_capability.return_value = trace_store

            result = await coordinator.get_run_proof(session, "tenant-123", "run-123")

            assert result.run_id == "run-123"
            assert result.integrity.verification_status == "VERIFIED"
            assert result.integrity.model == "HASH_CHAIN"
            assert result.integrity.chain_length == 1
            assert result.integrity.root_hash is not None

    @pytest.mark.asyncio
    async def test_returns_unsupported_when_no_traces(self):
        """Coordinator returns UNSUPPORTED when no trace found."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_proof_coordinator import (
            RunProofCoordinator,
        )

        coordinator = RunProofCoordinator()
        session = AsyncMock()

        with patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge.get_logs_bridge"
        ) as mock_bridge:
            trace_store = AsyncMock()
            trace_store.get_trace.return_value = None
            mock_bridge.return_value.traces_store_capability.return_value = trace_store

            result = await coordinator.get_run_proof(session, "tenant-123", "run-missing")

            assert result.run_id == "run-missing"
            assert result.integrity.verification_status == "UNSUPPORTED"
            assert result.integrity.failure_reason == "No trace found for run"

    @pytest.mark.asyncio
    async def test_returns_unsupported_when_no_steps(self):
        """Coordinator returns UNSUPPORTED when trace has no steps."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_proof_coordinator import (
            RunProofCoordinator,
        )

        coordinator = RunProofCoordinator()
        session = AsyncMock()

        mock_trace = MagicMock()
        mock_trace.run_id = "run-empty"
        mock_trace.status = MagicMock(value="completed")
        mock_trace.started_at = datetime.now(timezone.utc)
        mock_trace.completed_at = datetime.now(timezone.utc)
        mock_trace.steps = []

        with patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge.get_logs_bridge"
        ) as mock_bridge:
            trace_store = AsyncMock()
            trace_store.get_trace.return_value = mock_trace
            mock_bridge.return_value.traces_store_capability.return_value = trace_store

            result = await coordinator.get_run_proof(session, "tenant-123", "run-empty")

            assert result.integrity.verification_status == "UNSUPPORTED"
            assert result.integrity.failure_reason == "No steps to verify"


class TestSignalFeedbackCoordinator:
    """Tests for SignalFeedbackCoordinator."""

    @pytest.mark.asyncio
    async def test_returns_feedback_from_audit_ledger(self):
        """Coordinator returns feedback when audit entries exist."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.signal_feedback_coordinator import (
            SignalFeedbackCoordinator,
        )

        coordinator = SignalFeedbackCoordinator()
        session = AsyncMock()

        with patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge.get_logs_bridge"
        ) as mock_bridge:
            reader = AsyncMock()
            reader.get_signal_feedback.return_value = {
                "acknowledged": True,
                "acknowledged_by": "user-123",
                "acknowledged_at": datetime.now(timezone.utc),
                "suppressed": False,
                "suppressed_until": None,
                "escalated": False,
                "escalated_at": None,
            }
            mock_bridge.return_value.audit_ledger_read_capability.return_value = reader

            result = await coordinator.get_signal_feedback(
                session, "tenant-123", "fingerprint-abc"
            )

            assert result is not None
            assert result.acknowledged is True
            assert result.acknowledged_by == "user-123"
            assert result.suppressed is False

    @pytest.mark.asyncio
    async def test_returns_none_when_no_feedback(self):
        """Coordinator returns None when no feedback exists."""
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.signal_feedback_coordinator import (
            SignalFeedbackCoordinator,
        )

        coordinator = SignalFeedbackCoordinator()
        session = AsyncMock()

        with patch(
            "app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge.get_logs_bridge"
        ) as mock_bridge:
            reader = AsyncMock()
            reader.get_signal_feedback.return_value = None
            mock_bridge.return_value.audit_ledger_read_capability.return_value = reader

            result = await coordinator.get_signal_feedback(
                session, "tenant-123", "fingerprint-new"
            )

            assert result is None


class TestIntegrityConfig:
    """Tests for integrity configuration."""

    def test_default_integrity_model_is_hash_chain(self):
        """Default integrity model should be HASH_CHAIN."""
        assert INTEGRITY_CONFIG["model"] == "HASH_CHAIN"

    def test_trust_boundary_is_system(self):
        """Trust boundary should be SYSTEM (Postgres)."""
        assert INTEGRITY_CONFIG["trust_boundary"] == "SYSTEM"

    def test_storage_is_postgres(self):
        """Storage should be POSTGRES."""
        assert INTEGRITY_CONFIG["storage"] == "POSTGRES"
