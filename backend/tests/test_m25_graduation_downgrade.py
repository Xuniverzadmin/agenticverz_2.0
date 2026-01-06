"""
M25 Graduation Downgrade Regression Tests

These tests verify that graduation can FALL BACK when evidence regresses.
This is critical for trust - graduation must not be a one-way ratchet.

Test Categories:
1. Prevention rate collapse → downgrade
2. Regret rate spike → downgrade
3. Evidence staleness → downgrade
4. Capability lockouts re-engage

IMPORTANT: These tests are part of the M25 code freeze enforcement (PIN-130).
Any changes to graduation logic must pass these tests.
"""

import os

# Import graduation engine components
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.integrations.graduation_engine import (
    CapabilityGates,
    ComputedGraduationStatus,
    GraduationEngine,
    GraduationEvidence,
    GraduationLevel,
)


class TestGraduationDowngrade:
    """Test that graduation correctly degrades when evidence regresses."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = GraduationEngine()
        self.now = datetime.now(timezone.utc)

    def _make_evidence(
        self,
        total_preventions: int = 0,
        total_prevention_attempts: int = 0,
        prevention_rate: float = 0.0,
        total_regret_events: int = 0,
        total_auto_demotions: int = 0,
        regret_rate: float = 0.0,
        timeline_views_with_prevention: int = 0,
        last_prevention_at: datetime = None,
        last_demotion_at: datetime = None,
        last_timeline_view_at: datetime = None,
    ) -> GraduationEvidence:
        """Create evidence with specified values."""
        return GraduationEvidence(
            total_preventions=total_preventions,
            total_prevention_attempts=total_prevention_attempts or total_preventions,
            last_prevention_at=last_prevention_at or (self.now if total_preventions > 0 else None),
            prevention_rate=prevention_rate,
            total_regret_events=total_regret_events,
            total_auto_demotions=total_auto_demotions,
            last_demotion_at=last_demotion_at or (self.now if total_auto_demotions > 0 else None),
            regret_rate=regret_rate,
            timeline_views_with_prevention=timeline_views_with_prevention,
            last_timeline_view_at=last_timeline_view_at or (self.now if timeline_views_with_prevention > 0 else None),
            evaluated_at=self.now,
            evidence_window_start=self.now - timedelta(days=30),
            evidence_window_end=self.now,
        )

    # =========================================================================
    # TEST: Prevention Rate Collapse → Downgrade
    # =========================================================================

    def test_prevention_rate_collapse_triggers_downgrade(self):
        """
        When prevention rate drops below threshold, graduation should degrade.

        Scenario:
        - Was at BETA level (Gate 1 passed)
        - Prevention rate drops to 0.05 (below 0.3 threshold for downgrade)
        - Should degrade to DEGRADED level
        """
        # Create evidence with low prevention rate
        evidence = self._make_evidence(
            total_preventions=1,  # Had prevention before
            prevention_rate=0.05,  # Now below threshold (0.3)
            total_regret_events=0,
            regret_rate=0.0,
        )

        # Create a mock previous status at BETA level
        previous_status = ComputedGraduationStatus(
            level=GraduationLevel.BETA,
            gates={},
            thresholds=self.engine.thresholds,
            computed_at=self.now - timedelta(hours=1),
        )

        # Compute with previous status
        status = self.engine.compute(evidence, previous_status)

        # Should be degraded due to prevention rate collapse
        assert status.is_degraded, "Should be degraded when prevention rate collapses"
        assert status.level == GraduationLevel.DEGRADED
        assert "Prevention rate dropped" in (status.degradation_reason or "")

    def test_healthy_prevention_rate_no_downgrade(self):
        """Prevention rate above threshold should not cause downgrade."""
        evidence = self._make_evidence(
            total_preventions=5,
            prevention_rate=0.55,  # Healthy rate (>= 0.5 for passing)
            total_regret_events=0,
            regret_rate=0.0,
        )

        status = self.engine.compute(evidence)

        assert not status.is_degraded
        # With >= 1 prevention and >= 50% rate, Gate 1 passes → BETA
        assert status.level == GraduationLevel.BETA

    # =========================================================================
    # TEST: Regret Rate Spike → Downgrade
    # =========================================================================

    def test_regret_rate_spike_triggers_downgrade(self):
        """
        When regret rate spikes above threshold, graduation should degrade.

        Scenario:
        - Was at CANDIDATE level (Gates 1+2 passed)
        - Regret rate spikes to 0.55 (above 0.5 threshold)
        - Should degrade to DEGRADED level
        """
        evidence = self._make_evidence(
            total_preventions=5,
            prevention_rate=0.55,
            total_regret_events=10,  # High regret count
            total_auto_demotions=2,
            regret_rate=0.55,  # Above threshold (0.5)
        )

        previous_status = ComputedGraduationStatus(
            level=GraduationLevel.CANDIDATE,
            gates={},
            thresholds=self.engine.thresholds,
            computed_at=self.now - timedelta(hours=1),
        )

        status = self.engine.compute(evidence, previous_status)

        assert status.is_degraded, "Should be degraded when regret rate spikes"
        assert status.level == GraduationLevel.DEGRADED
        assert "Regret rate spiked" in (status.degradation_reason or "")

    def test_healthy_regret_rate_no_downgrade(self):
        """Regret rate below threshold should not cause downgrade."""
        evidence = self._make_evidence(
            total_preventions=5,
            prevention_rate=0.55,
            total_regret_events=2,
            total_auto_demotions=1,
            regret_rate=0.10,  # Healthy rate
        )

        status = self.engine.compute(evidence)

        assert not status.is_degraded
        # Gates 1 and 2 pass → CANDIDATE
        assert status.level == GraduationLevel.CANDIDATE

    # =========================================================================
    # TEST: Evidence Staleness → Downgrade
    # =========================================================================

    def test_stale_evidence_triggers_downgrade(self):
        """
        When no prevention evidence for extended period, graduation should degrade.

        Scenario:
        - Was at COMPLETE level
        - No new prevention for 20 days (> 14 day threshold)
        - Should degrade due to staleness
        """
        stale_date = self.now - timedelta(days=20)

        evidence = self._make_evidence(
            total_preventions=10,
            prevention_rate=0.40,  # Above downgrade threshold
            total_regret_events=2,
            total_auto_demotions=1,
            regret_rate=0.05,
            timeline_views_with_prevention=5,
            last_prevention_at=stale_date,  # Stale!
        )

        previous_status = ComputedGraduationStatus(
            level=GraduationLevel.COMPLETE,
            gates={},
            thresholds=self.engine.thresholds,
            computed_at=self.now - timedelta(hours=1),
        )

        status = self.engine.compute(evidence, previous_status)

        # Should degrade due to stale evidence
        assert status.is_degraded
        assert "No prevention in" in (status.degradation_reason or "")

    # =========================================================================
    # TEST: Capability Lockouts Re-engage
    # =========================================================================

    def test_capability_lockouts_reengage_on_downgrade(self):
        """
        When graduation degrades, capability lockouts should re-engage.

        Scenario:
        - Was at CANDIDATE (auto_apply_recovery + auto_activate_policy unlocked)
        - Degrades to DEGRADED
        - Capabilities should be blocked again
        """
        # First, verify capabilities at CANDIDATE
        healthy_evidence = self._make_evidence(
            total_preventions=5,
            prevention_rate=0.55,
            total_regret_events=2,
            total_auto_demotions=1,
            regret_rate=0.10,
        )

        candidate_status = self.engine.compute(healthy_evidence)

        # At CANDIDATE, should have some capabilities
        assert CapabilityGates.can_auto_apply_recovery(candidate_status), "CANDIDATE should have auto_apply_recovery"
        assert CapabilityGates.can_auto_activate_policy(candidate_status), "CANDIDATE should have auto_activate_policy"

        # Now create degraded evidence
        degraded_evidence = self._make_evidence(
            total_preventions=1,
            prevention_rate=0.05,  # Collapsed below threshold
            total_regret_events=0,
            regret_rate=0.0,
        )

        # Create new engine to clear state
        new_engine = GraduationEngine()
        previous = ComputedGraduationStatus(
            level=GraduationLevel.CANDIDATE,
            gates={},
            thresholds=new_engine.thresholds,
            computed_at=self.now - timedelta(hours=1),
        )

        degraded_status = new_engine.compute(degraded_evidence, previous)

        # Capabilities should be blocked at DEGRADED level
        assert not CapabilityGates.can_auto_apply_recovery(degraded_status), (
            "DEGRADED should not have auto_apply_recovery"
        )
        assert not CapabilityGates.can_auto_activate_policy(degraded_status), (
            "DEGRADED should not have auto_activate_policy"
        )
        assert not CapabilityGates.can_full_auto_routing(degraded_status), "DEGRADED should not have full_auto_routing"

    # =========================================================================
    # TEST: Downgrade is Recorded
    # =========================================================================

    def test_downgrade_includes_from_level(self):
        """Downgrade should record what level it degraded from."""
        evidence = self._make_evidence(
            total_preventions=1,
            prevention_rate=0.05,  # Collapsed
        )

        previous = ComputedGraduationStatus(
            level=GraduationLevel.BETA,
            gates={},
            thresholds=self.engine.thresholds,
            computed_at=self.now - timedelta(hours=1),
        )

        status = self.engine.compute(evidence, previous)

        assert status.is_degraded
        assert status.degraded_from == GraduationLevel.BETA

    def test_downgrade_includes_reason(self):
        """Downgrade should include a specific reason."""
        evidence = self._make_evidence(
            total_preventions=5,
            prevention_rate=0.55,
            total_regret_events=10,
            total_auto_demotions=2,
            regret_rate=0.55,  # Spiked
        )

        previous = ComputedGraduationStatus(
            level=GraduationLevel.CANDIDATE,
            gates={},
            thresholds=self.engine.thresholds,
            computed_at=self.now - timedelta(hours=1),
        )

        status = self.engine.compute(evidence, previous)

        assert status.is_degraded
        assert status.degradation_reason is not None
        assert len(status.degradation_reason) > 10  # Not empty

    # =========================================================================
    # TEST: No Downgrade from ALPHA
    # =========================================================================

    def test_alpha_cannot_downgrade_further(self):
        """ALPHA is the lowest level - cannot degrade further."""
        evidence = self._make_evidence(
            total_preventions=0,
            prevention_rate=0.0,
        )

        previous = ComputedGraduationStatus(
            level=GraduationLevel.ALPHA,
            gates={},
            thresholds=self.engine.thresholds,
            computed_at=self.now - timedelta(hours=1),
        )

        status = self.engine.compute(evidence, previous)

        # Should stay at ALPHA, not become DEGRADED
        assert status.level == GraduationLevel.ALPHA
        assert not status.is_degraded

    # =========================================================================
    # TEST: Recovery from Degraded State
    # =========================================================================

    def test_can_recover_from_degraded(self):
        """
        After evidence improves, should be able to recover from DEGRADED.

        Scenario:
        - Was DEGRADED due to prevention rate collapse
        - Prevention rate recovers to healthy level
        - Should progress back to BETA (if Gate 1 passes)
        """
        # Good evidence after recovery
        recovered_evidence = self._make_evidence(
            total_preventions=5,
            prevention_rate=0.55,  # Healthy again
        )

        # No previous status = fresh computation
        status = self.engine.compute(recovered_evidence)

        # Should not be degraded
        assert not status.is_degraded
        # Should be at BETA (Gate 1 passed)
        assert status.level == GraduationLevel.BETA


class TestGraduationEdgeCases:
    """Test edge cases in graduation computation."""

    def setup_method(self):
        self.engine = GraduationEngine()
        self.now = datetime.now(timezone.utc)

    def test_zero_evidence(self):
        """Zero evidence should result in ALPHA."""
        evidence = GraduationEvidence(
            total_preventions=0,
            total_prevention_attempts=0,
            last_prevention_at=None,
            prevention_rate=0.0,
            total_regret_events=0,
            total_auto_demotions=0,
            last_demotion_at=None,
            regret_rate=0.0,
            timeline_views_with_prevention=0,
            last_timeline_view_at=None,
            evaluated_at=self.now,
            evidence_window_start=self.now - timedelta(days=30),
            evidence_window_end=self.now,
        )

        status = self.engine.compute(evidence)

        assert status.level == GraduationLevel.ALPHA
        assert not status.is_graduated
        assert not status.is_degraded

    def test_all_gates_passed(self):
        """All gates passed should result in COMPLETE."""
        evidence = GraduationEvidence(
            total_preventions=10,
            total_prevention_attempts=15,
            last_prevention_at=self.now,
            prevention_rate=0.60,  # >= 0.5 threshold
            total_regret_events=3,
            total_auto_demotions=2,  # >= 1 demotion
            last_demotion_at=self.now - timedelta(days=1),
            regret_rate=0.08,  # <= 0.3 threshold
            timeline_views_with_prevention=5,  # >= 1 view
            last_timeline_view_at=self.now,
            evaluated_at=self.now,
            evidence_window_start=self.now - timedelta(days=30),
            evidence_window_end=self.now,
        )

        status = self.engine.compute(evidence)

        assert status.level == GraduationLevel.COMPLETE
        assert status.is_graduated
        assert not status.is_degraded

    def test_gates_passed_count(self):
        """Verify correct counting of passed gates."""
        # Gate 1 only
        evidence_g1 = GraduationEvidence(
            total_preventions=5,
            total_prevention_attempts=8,
            last_prevention_at=self.now,
            prevention_rate=0.55,  # >= 0.5 threshold
            total_regret_events=0,
            total_auto_demotions=0,  # No demotions = Gate 2 fails
            last_demotion_at=None,
            regret_rate=0.0,
            timeline_views_with_prevention=0,  # No views = Gate 3 fails
            last_timeline_view_at=None,
            evaluated_at=self.now,
            evidence_window_start=self.now - timedelta(days=30),
            evidence_window_end=self.now,
        )

        status_g1 = self.engine.compute(evidence_g1)
        passed_count = sum(1 for g in status_g1.gates.values() if g.passed)

        assert passed_count == 1
        assert status_g1.level == GraduationLevel.BETA


class TestCapabilityGatesIntegration:
    """Test capability gates integrate correctly with graduation levels."""

    def setup_method(self):
        self.engine = GraduationEngine()
        self.now = datetime.now(timezone.utc)

    def test_alpha_has_no_capabilities(self):
        """ALPHA level should have no capabilities unlocked."""
        evidence = GraduationEvidence(
            total_preventions=0,
            total_prevention_attempts=0,
            last_prevention_at=None,
            prevention_rate=0.0,
            total_regret_events=0,
            total_auto_demotions=0,
            last_demotion_at=None,
            regret_rate=0.0,
            timeline_views_with_prevention=0,
            last_timeline_view_at=None,
            evaluated_at=self.now,
            evidence_window_start=self.now - timedelta(days=30),
            evidence_window_end=self.now,
        )

        status = self.engine.compute(evidence)

        assert not CapabilityGates.can_auto_apply_recovery(status)
        assert not CapabilityGates.can_auto_activate_policy(status)
        assert not CapabilityGates.can_full_auto_routing(status)

        unlocked = CapabilityGates.get_unlocked_capabilities(status)
        assert len(unlocked) == 0

    def test_complete_has_all_capabilities(self):
        """COMPLETE level should have all capabilities unlocked."""
        evidence = GraduationEvidence(
            total_preventions=10,
            total_prevention_attempts=15,
            last_prevention_at=self.now,
            prevention_rate=0.60,
            total_regret_events=3,
            total_auto_demotions=2,
            last_demotion_at=self.now - timedelta(days=1),
            regret_rate=0.08,
            timeline_views_with_prevention=5,
            last_timeline_view_at=self.now,
            evaluated_at=self.now,
            evidence_window_start=self.now - timedelta(days=30),
            evidence_window_end=self.now,
        )

        status = self.engine.compute(evidence)

        assert CapabilityGates.can_auto_apply_recovery(status)
        assert CapabilityGates.can_auto_activate_policy(status)
        assert CapabilityGates.can_full_auto_routing(status)

        unlocked = CapabilityGates.get_unlocked_capabilities(status)
        assert len(unlocked) == 3


# Run with: PYTHONPATH=backend python -m pytest backend/tests/test_m25_graduation_downgrade.py -v
