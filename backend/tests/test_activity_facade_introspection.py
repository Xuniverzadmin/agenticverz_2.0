# Layer: Test
# AUDIENCE: INTERNAL
# Role: Integration tests for PIN-519 activity facade introspection
# Reference: PIN-519 System Run Introspection

"""
Activity Facade Introspection Tests (PIN-519)

Integration tests for activity facade methods that delegate to L4 coordinators:
- get_run_evidence() -> RunEvidenceCoordinator
- get_run_proof() -> RunProofCoordinator
- get_signals() -> SignalFeedbackCoordinator (for feedback)
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.hoc.cus.activity.L5_engines.activity_facade import (
    ActivityFacade,
    RunEvidenceResult,
    RunProofResult,
    SignalsResult,
)


class TestActivityFacadeIntrospection:
    """Integration tests for activity facade introspection methods."""

    @pytest.fixture
    def facade(self):
        """Create ActivityFacade instance."""
        return ActivityFacade()

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_run_evidence_delegates_to_coordinator(self, facade, mock_session):
        """get_run_evidence() should delegate to L4 RunEvidenceCoordinator."""
        from app.hoc.cus.hoc_spine.schemas.run_introspection_protocols import (
            RunEvidenceResult as L4RunEvidenceResult,
            PolicyEvaluationSummary,
            LimitHitSummary,
            DecisionSummary,
        )

        # Mock the coordinator
        mock_result = L4RunEvidenceResult(
            run_id="run-123",
            incidents_caused=[],
            policies_evaluated=[
                PolicyEvaluationSummary(
                    policy_id="policy-1",
                    policy_name="Cost Limit",
                    outcome="WARNED",
                    evaluated_at=datetime.now(timezone.utc),
                )
            ],
            limits_hit=[
                LimitHitSummary(
                    limit_id="limit-1",
                    limit_name="Budget",
                    breached_value=100.0,
                    threshold_value=90.0,
                    breached_at=datetime.now(timezone.utc),
                )
            ],
            decisions_made=[
                DecisionSummary(
                    decision_id="dec-1",
                    decision_type="POLICY_EVALUATION",
                    outcome="WARNED",
                    decided_at=datetime.now(timezone.utc),
                )
            ],
        )

        with patch(
            "app.hoc.cus.activity.L5_engines.activity_facade.get_run_evidence_coordinator"
        ) as mock_get_coordinator:
            coordinator = AsyncMock()
            coordinator.get_run_evidence.return_value = mock_result
            mock_get_coordinator.return_value = coordinator

            result = await facade.get_run_evidence(mock_session, "tenant-123", "run-123")

            # Verify coordinator was called
            coordinator.get_run_evidence.assert_called_once_with(
                mock_session, "tenant-123", "run-123"
            )

            # Verify result structure
            assert result.run_id == "run-123"
            assert len(result.policies_triggered) == 1
            assert result.policies_triggered[0]["policy_name"] == "Cost Limit"
            assert len(result.traces_linked) == 1  # limits_hit maps to traces_linked

    @pytest.mark.asyncio
    async def test_get_run_proof_delegates_to_coordinator(self, facade, mock_session):
        """get_run_proof() should delegate to L4 RunProofCoordinator."""
        from app.hoc.cus.hoc_spine.schemas.run_introspection_protocols import (
            RunProofResult as L4RunProofResult,
            IntegrityVerificationResult,
            TraceSummary,
            TraceStepSummary,
        )

        mock_result = L4RunProofResult(
            run_id="run-123",
            integrity=IntegrityVerificationResult(
                model="HASH_CHAIN",
                root_hash="abc123def456",
                chain_length=5,
                verification_status="VERIFIED",
                failure_reason=None,
            ),
            aos_traces=[
                TraceSummary(
                    trace_id="trace-1",
                    run_id="run-123",
                    status="completed",
                    step_count=5,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )
            ],
            aos_trace_steps=[
                TraceStepSummary(
                    step_index=0,
                    skill_name="analyze",
                    status="completed",
                    duration_ms=100.0,
                    cost_cents=0.5,
                )
            ],
            raw_logs=None,
        )

        with patch(
            "app.hoc.cus.activity.L5_engines.activity_facade.get_run_proof_coordinator"
        ) as mock_get_coordinator:
            coordinator = AsyncMock()
            coordinator.get_run_proof.return_value = mock_result
            mock_get_coordinator.return_value = coordinator

            result = await facade.get_run_proof(
                mock_session, "tenant-123", "run-123", include_payloads=False
            )

            # Verify coordinator was called
            coordinator.get_run_proof.assert_called_once_with(
                mock_session, "tenant-123", "run-123", False
            )

            # Verify result structure
            assert result.run_id == "run-123"
            assert result.integrity["verification_status"] == "VERIFIED"
            assert result.integrity["model"] == "HASH_CHAIN"
            assert result.integrity["root_hash"] == "abc123def456"
            assert len(result.aos_traces) == 1
            assert len(result.aos_trace_steps) == 1

    @pytest.mark.asyncio
    async def test_signals_include_feedback(self, facade, mock_session):
        """get_signals() should include feedback from audit ledger."""
        from app.hoc.cus.hoc_spine.schemas.run_introspection_protocols import (
            SignalFeedbackResult,
        )
        from app.hoc.cus.activity.L5_engines.signal_feedback_engine import (
            SignalFeedbackStatus,
        )

        # Mock the driver for fetching runs
        mock_driver = AsyncMock()
        mock_driver.fetch_at_risk_runs.return_value = [
            {
                "run_id": "run-123",
                "tenant_id": "tenant-123",
                "project_id": None,
                "is_synthetic": False,
                "source": "SDK",
                "provider_type": "ANTHROPIC",
                "state": "COMPLETED",
                "status": "SUCCESS",
                "started_at": datetime.now(timezone.utc),
                "last_seen_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc),
                "duration_ms": 1000,
                "risk_level": "AT_RISK",
                "latency_bucket": "FAST",
                "evidence_health": "COMPLETE",
                "integrity_status": "VERIFIED",
                "incident_count": 0,
                "policy_draft_count": 0,
                "policy_violation": False,
                "input_tokens": 100,
                "output_tokens": 50,
                "estimated_cost_usd": 0.01,
                "policy_id": "policy-1",
                "policy_name": "Test Policy",
                "policy_scope": "GLOBAL",
                "limit_type": "BUDGET",
                "threshold_value": 100.0,
                "threshold_unit": "USD",
                "threshold_source": "SYSTEM",
                "evaluation_outcome": "PASS",
                "actual_value": 50.0,
                "risk_type": "COST",
                "proximity_pct": 50.0,
            }
        ]
        mock_driver.count_runs.return_value = 1

        # Mock signal feedback coordinator
        mock_feedback = SignalFeedbackResult(
            acknowledged=True,
            acknowledged_by="user-123",
            acknowledged_at=datetime.now(timezone.utc),
            suppressed=False,
            suppressed_until=None,
            escalated=False,
            escalated_at=None,
        )

        with patch.object(
            facade, "_get_driver", return_value=mock_driver
        ), patch(
            "app.hoc.cus.activity.L5_engines.activity_facade.get_signal_feedback_coordinator"
        ) as mock_get_coordinator:
            coordinator = AsyncMock()
            coordinator.get_signal_feedback.return_value = mock_feedback
            mock_get_coordinator.return_value = coordinator

            result = await facade.get_signals(mock_session, "tenant-123")

            # Verify signals were fetched
            assert isinstance(result, SignalsResult)
            assert len(result.signals) == 1

            # Verify feedback was included
            signal = result.signals[0]
            assert signal.feedback is not None
            assert signal.feedback.acknowledged is True
            assert signal.feedback.acknowledged_by == "user-123"


class TestActivityFacadeNoCoordinatorFallback:
    """Tests for graceful fallback when coordinators fail."""

    @pytest.fixture
    def facade(self):
        """Create ActivityFacade instance."""
        return ActivityFacade()

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_signals_fallback_when_feedback_fails(self, facade, mock_session):
        """get_signals() should return None feedback when coordinator fails."""
        mock_driver = AsyncMock()
        mock_driver.fetch_at_risk_runs.return_value = [
            {
                "run_id": "run-123",
                "tenant_id": "tenant-123",
                "project_id": None,
                "is_synthetic": False,
                "source": "SDK",
                "provider_type": "ANTHROPIC",
                "state": "COMPLETED",
                "status": "SUCCESS",
                "started_at": datetime.now(timezone.utc),
                "last_seen_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc),
                "duration_ms": 1000,
                "risk_level": "AT_RISK",
                "latency_bucket": "FAST",
                "evidence_health": "COMPLETE",
                "integrity_status": "VERIFIED",
                "incident_count": 0,
                "policy_draft_count": 0,
                "policy_violation": False,
                "input_tokens": 100,
                "output_tokens": 50,
                "estimated_cost_usd": 0.01,
                "policy_id": "policy-1",
                "policy_name": "Test Policy",
                "policy_scope": "GLOBAL",
                "limit_type": "BUDGET",
                "threshold_value": 100.0,
                "threshold_unit": "USD",
                "threshold_source": "SYSTEM",
                "evaluation_outcome": "PASS",
                "actual_value": 50.0,
                "risk_type": "COST",
                "proximity_pct": 50.0,
            }
        ]
        mock_driver.count_runs.return_value = 1

        with patch.object(
            facade, "_get_driver", return_value=mock_driver
        ), patch(
            "app.hoc.cus.activity.L5_engines.activity_facade.get_signal_feedback_coordinator"
        ) as mock_get_coordinator:
            # Coordinator raises exception
            coordinator = AsyncMock()
            coordinator.get_signal_feedback.side_effect = Exception("DB connection failed")
            mock_get_coordinator.return_value = coordinator

            result = await facade.get_signals(mock_session, "tenant-123")

            # Should still return signals, but with None feedback
            assert len(result.signals) == 1
            assert result.signals[0].feedback is None


class TestSingleActivityFacadeEnforcement:
    """Test that only one Activity Facade exists in HOC tree (PIN-519)."""

    def test_single_activity_facade_exists_in_hoc(self):
        """
        Only one activity_facade.py should exist in the HOC tree.

        Canonical path: app/hoc/cus/activity/L5_engines/activity_facade.py

        This test enforces PIN-519 architectural lock - any duplicate
        activity_facade.py in the HOC tree is a violation.
        """
        import glob
        import os

        # Find all activity_facade.py files in the HOC tree
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        hoc_root = os.path.join(backend_root, "app", "hoc")

        hits = glob.glob(os.path.join(hoc_root, "**", "activity_facade.py"), recursive=True)

        # Normalize to relative paths for comparison
        rel_hits = [os.path.relpath(h, backend_root) for h in hits]

        canonical_path = "app/hoc/cus/activity/L5_engines/activity_facade.py"

        assert rel_hits == [canonical_path], (
            f"Multiple activity_facade.py files found in HOC tree.\n"
            f"Expected only: {canonical_path}\n"
            f"Found: {rel_hits}\n"
            f"Per PIN-519, only one Activity Facade is allowed. "
            f"Delete duplicates or merge into canonical location."
        )

    def test_canonical_facade_has_architectural_lock_comment(self):
        """The canonical activity_facade.py must have the ARCHITECTURAL LOCK comment."""
        import os

        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        canonical_path = os.path.join(
            backend_root, "app", "hoc", "cus", "activity", "L5_engines", "activity_facade.py"
        )

        with open(canonical_path, "r") as f:
            content = f.read()

        assert "ARCHITECTURAL LOCK" in content, (
            "Canonical activity_facade.py is missing ARCHITECTURAL LOCK comment. "
            "See PIN-519 for required intent lock."
        )
        assert "PIN-519" in content, (
            "Canonical activity_facade.py must reference PIN-519 in the lock comment."
        )
