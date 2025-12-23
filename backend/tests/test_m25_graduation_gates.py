"""
M25 Graduation Gate Tests

These tests prove that M25 LEARNS, not just executes.

Three gates must pass for M25 to graduate from ALPHA to COMPLETE:
- Gate 1: Prevention Proof (policy prevented at least one incident)
- Gate 2: Regret Rollback (policy auto-demoted due to harm)
- Gate 3: Console Timeline (user can see the learning in action)

"A system that can safely attempt to improve itself" vs
"A system that demonstrably improves itself"
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.integrations.learning_proof import (
    # Gate 1
    PreventionOutcome,
    PreventionRecord,
    PreventionTracker,
    # Gate 2
    RegretType,
    RegretEvent,
    PolicyRegretTracker,
    GlobalRegretTracker,
    # Adaptive
    PatternCalibration,
    AdaptiveConfidenceSystem,
    # Checkpoints
    CheckpointPriority,
    CheckpointConfig,
    PrioritizedCheckpoint,
    # Graduation
    M25GraduationStatus,
    PreventionTimeline,
)


# =============================================================================
# GATE 1: PREVENTION PROOF TESTS
# =============================================================================


class TestGate1PreventionProof:
    """
    Gate 1: Policy must prevent at least one incident recurrence.

    Without this, we have plumbing, not learning.
    """

    def test_create_prevention_record(self):
        """Prevention record captures the evidence."""
        record = PreventionRecord.create_prevention(
            policy_id="pol_001",
            pattern_id="pat_001",
            original_incident_id="inc_001",
            blocked_incident_id="inc_002",
            tenant_id="tenant_001",
            signature_match=0.92,
            policy_age=timedelta(days=3),
            calls_evaluated=150,
        )

        assert record.outcome == PreventionOutcome.PREVENTED
        assert record.signature_match_confidence == 0.92
        assert record.calls_evaluated == 150

    def test_prevention_tracker_records_prevention(self):
        """Tracker accumulates prevention evidence."""
        tracker = PreventionTracker()

        record = PreventionRecord.create_prevention(
            policy_id="pol_001",
            pattern_id="pat_001",
            original_incident_id="inc_001",
            blocked_incident_id="inc_002",
            tenant_id="tenant_001",
            signature_match=0.88,
            policy_age=timedelta(hours=12),
        )

        tracker.record_prevention(record)

        assert tracker.total_preventions == 1
        assert "pol_001" in tracker.policies_with_prevention
        assert len(tracker.prevention_by_pattern["pat_001"]) == 1

    def test_gate1_passes_after_one_prevention(self):
        """Gate 1 passes after a single prevention."""
        tracker = PreventionTracker()

        # Before prevention
        assert not tracker.has_proven_prevention

        # Record prevention
        record = PreventionRecord.create_prevention(
            policy_id="pol_001",
            pattern_id="pat_001",
            original_incident_id="inc_001",
            blocked_incident_id="inc_002",
            tenant_id="tenant_001",
            signature_match=0.85,
            policy_age=timedelta(minutes=30),
        )
        tracker.record_prevention(record)

        # After prevention
        assert tracker.has_proven_prevention
        assert tracker.prevention_rate == 1.0

    def test_prevention_rate_calculation(self):
        """Prevention rate accounts for failures."""
        tracker = PreventionTracker()

        # 3 preventions
        for i in range(3):
            record = PreventionRecord.create_prevention(
                policy_id=f"pol_{i}",
                pattern_id="pat_001",
                original_incident_id=f"inc_orig_{i}",
                blocked_incident_id=f"inc_block_{i}",
                tenant_id="tenant_001",
                signature_match=0.9,
                policy_age=timedelta(hours=1),
            )
            tracker.record_prevention(record)

        # 1 failure
        tracker.record_failure("pol_fail", "pat_001")

        # 3/4 = 75%
        assert tracker.prevention_rate == 0.75

    def test_prevention_timeline_console_format(self):
        """Prevention record formats for console display."""
        record = PreventionRecord.create_prevention(
            policy_id="pol_001",
            pattern_id="pat_001",
            original_incident_id="inc_001",
            blocked_incident_id="inc_002",
            tenant_id="tenant_001",
            signature_match=0.95,
            policy_age=timedelta(days=1, hours=6),
        )

        timeline = record.to_console_timeline()

        assert timeline["type"] == "prevention"
        assert timeline["is_milestone"] is True
        assert "policy" in timeline["details"]
        assert "confidence" in timeline["details"]


# =============================================================================
# GATE 2: REGRET ROLLBACK TESTS
# =============================================================================


class TestGate2RegretRollback:
    """
    Gate 2: At least one policy must be auto-demoted due to causing harm.

    This proves the system can self-correct, not just self-improve.
    """

    def test_regret_event_creation(self):
        """Regret event captures harm details."""
        event = RegretEvent(
            regret_id="reg_001",
            policy_id="pol_001",
            tenant_id="tenant_001",
            regret_type=RegretType.FALSE_POSITIVE,
            description="Blocked legitimate API request",
            severity=7,
            created_at=datetime.now(timezone.utc),
            affected_calls=50,
            affected_users=12,
            impact_duration=timedelta(minutes=15),
        )

        assert event.regret_type == RegretType.FALSE_POSITIVE
        assert event.severity == 7
        assert event.affected_users == 12

    def test_policy_regret_tracker_accumulates(self):
        """Regret tracker accumulates weighted score."""
        tracker = PolicyRegretTracker(policy_id="pol_001")

        event = RegretEvent(
            regret_id="reg_001",
            policy_id="pol_001",
            tenant_id="tenant_001",
            regret_type=RegretType.FALSE_POSITIVE,
            description="Test",
            severity=6,
            created_at=datetime.now(timezone.utc),
            affected_calls=10,
            affected_users=2,
            impact_duration=timedelta(minutes=5),
        )

        demoted = tracker.add_regret(event)

        # Single event with severity 6 → score 3.0
        assert tracker.regret_score == 3.0
        assert not demoted  # Not above threshold yet

    def test_auto_demotion_on_score_threshold(self):
        """Policy demoted when regret score exceeds threshold."""
        tracker = PolicyRegretTracker(
            policy_id="pol_001",
            auto_demote_score=5.0,
        )

        # Add two high-severity events
        for severity in [8, 8]:  # 8*0.5 + 8*0.5 = 8.0 > 5.0
            event = RegretEvent(
                regret_id=f"reg_{severity}",
                policy_id="pol_001",
                tenant_id="tenant_001",
                regret_type=RegretType.CASCADING_FAILURE,
                description="Major issue",
                severity=severity,
                created_at=datetime.now(timezone.utc),
                affected_calls=100,
                affected_users=50,
                impact_duration=timedelta(hours=1),
            )
            demoted = tracker.add_regret(event)

        assert demoted
        assert tracker.is_demoted
        assert "Regret score" in tracker.demoted_reason

    def test_auto_demotion_on_count_threshold(self):
        """Policy demoted when regret event count exceeds threshold."""
        tracker = PolicyRegretTracker(
            policy_id="pol_001",
            auto_demote_count=3,
            auto_demote_score=100,  # High score threshold
        )

        # Add 3 low-severity events
        for i in range(3):
            event = RegretEvent(
                regret_id=f"reg_{i}",
                policy_id="pol_001",
                tenant_id="tenant_001",
                regret_type=RegretType.ESCALATION_NOISE,
                description="Minor noise",
                severity=2,
                created_at=datetime.now(timezone.utc),
                affected_calls=5,
                affected_users=1,
                impact_duration=timedelta(minutes=1),
            )
            demoted = tracker.add_regret(event)

        assert demoted
        assert "count" in tracker.demoted_reason.lower()

    def test_global_regret_tracker_gate2(self):
        """Global tracker tracks Gate 2 passage."""
        global_tracker = GlobalRegretTracker()

        # Before demotion
        assert not global_tracker.has_proven_rollback

        # Create and record regret until demotion
        for i in range(3):
            event = RegretEvent(
                regret_id=f"reg_{i}",
                policy_id="pol_001",
                tenant_id="tenant_001",
                regret_type=RegretType.FALSE_POSITIVE,
                description="Harm caused",
                severity=10,
                created_at=datetime.now(timezone.utc),
                affected_calls=100,
                affected_users=50,
                impact_duration=timedelta(hours=1),
            )
            global_tracker.record_regret("pol_001", event)

        # After demotion
        assert global_tracker.has_proven_rollback
        assert global_tracker.total_auto_demotions >= 1

    def test_regret_decay(self):
        """Regret score decays over time."""
        tracker = PolicyRegretTracker(policy_id="pol_001", decay_rate=0.2)

        # Add event
        event = RegretEvent(
            regret_id="reg_001",
            policy_id="pol_001",
            tenant_id="tenant_001",
            regret_type=RegretType.FALSE_POSITIVE,
            description="Test",
            severity=10,
            created_at=datetime.now(timezone.utc),
            affected_calls=10,
            affected_users=2,
            impact_duration=timedelta(minutes=5),
        )
        tracker.add_regret(event)

        initial_score = tracker.regret_score

        # Simulate daily decay
        tracker.decay_regret()

        assert tracker.regret_score < initial_score
        assert tracker.regret_score == initial_score * 0.8  # 20% decay


# =============================================================================
# ADAPTIVE CONFIDENCE TESTS
# =============================================================================


class TestAdaptiveConfidence:
    """
    Tests for adaptive confidence calibration.

    Moves from "cargo cult 0.85" to empirical thresholds.
    """

    def test_pattern_calibration_records_outcomes(self):
        """Calibration records prediction outcomes."""
        cal = PatternCalibration(pattern_id="pat_001")

        # Record 5 correct predictions at high confidence
        for _ in range(5):
            cal.record_outcome(0.92, was_correct=True)

        # Record 2 incorrect at low confidence
        for _ in range(2):
            cal.record_outcome(0.55, was_correct=False)

        assert cal.total_matches == 7
        assert cal.correct_matches == 5

    def test_calibration_adjusts_thresholds(self):
        """Thresholds adjust based on outcomes."""
        cal = PatternCalibration(pattern_id="pat_001")

        # Simulate: high confidence predictions are accurate
        for _ in range(20):
            cal.record_outcome(0.90, was_correct=True)

        # Simulate: lower confidence predictions are mixed
        for _ in range(5):
            cal.record_outcome(0.70, was_correct=True)
        for _ in range(5):
            cal.record_outcome(0.70, was_correct=False)

        # After calibration, should adjust thresholds
        assert cal.is_calibrated
        # High confidence should remain strong threshold
        assert cal.empirical_strong_threshold <= 0.90

    def test_calibrated_band_classification(self):
        """Use calibrated thresholds for classification."""
        cal = PatternCalibration(pattern_id="pat_001")
        cal.empirical_strong_threshold = 0.80  # Lower than default
        cal.empirical_weak_threshold = 0.55

        # 0.82 would be weak with default, strong with calibrated
        band = cal.get_calibrated_band(0.82)
        assert band == "strong_match"

    def test_adaptive_system_global_accuracy(self):
        """System tracks global prediction accuracy."""
        system = AdaptiveConfidenceSystem()

        # Record outcomes across patterns
        for i in range(10):
            system.record_outcome(f"pat_{i % 3}", 0.85, was_correct=(i % 3 != 0))

        # 6 correct out of 10
        assert system.global_accuracy == pytest.approx(0.6, rel=0.1)

    def test_confidence_report(self):
        """System generates confidence health report."""
        system = AdaptiveConfidenceSystem()

        # Calibrate one pattern
        for _ in range(25):
            system.record_outcome("pat_001", 0.88, was_correct=True)

        report = system.get_confidence_report()

        assert "total_patterns" in report
        assert "global_accuracy" in report


# =============================================================================
# CHECKPOINT PRIORITIZATION TESTS
# =============================================================================


class TestCheckpointPrioritization:
    """
    Tests for checkpoint priority and configuration.

    Prevents checkpoint fatigue.
    """

    def test_checkpoint_config_defaults(self):
        """Config has sensible defaults."""
        config = CheckpointConfig(tenant_id="tenant_001")

        assert "approve_policy" in config.enabled_types
        assert config.auto_approve_confidence == 0.95
        assert config.max_pending_checkpoints == 10

    def test_priority_based_on_confidence(self):
        """High confidence checkpoints get lower priority."""
        config = CheckpointConfig(tenant_id="tenant_001")

        # Very high confidence
        priority = config.get_priority("approve_policy", confidence=0.98)
        assert priority == CheckpointPriority.ADVISORY

        # Normal confidence
        priority = config.get_priority("approve_policy", confidence=0.70)
        assert priority == CheckpointPriority.HIGH

    def test_blocking_checkpoints(self):
        """Some checkpoints block loop progress."""
        config = CheckpointConfig(tenant_id="tenant_001")

        assert config.is_blocking("approve_policy")
        assert config.is_blocking("override_guardrail")
        assert not config.is_blocking("simulate_routing")

    def test_auto_dismiss_low_priority(self):
        """Low priority checkpoints auto-dismiss after timeout."""
        config = CheckpointConfig(tenant_id="tenant_001", auto_dismiss_after_hours=24)

        # Low priority, old
        assert config.should_auto_dismiss("simulate_routing", age_hours=30)

        # Low priority, recent
        assert not config.should_auto_dismiss("simulate_routing", age_hours=12)

        # Critical, old (never auto-dismiss)
        assert not config.should_auto_dismiss("override_guardrail", age_hours=100)

    def test_prioritized_checkpoint_creation(self):
        """Checkpoints created with priority from config."""
        config = CheckpointConfig(tenant_id="tenant_001")

        checkpoint = PrioritizedCheckpoint.create(
            checkpoint_type="approve_policy",
            incident_id="inc_001",
            tenant_id="tenant_001",
            description="Approve new policy",
            confidence=0.72,
            config=config,
        )

        assert checkpoint.priority == CheckpointPriority.HIGH
        assert checkpoint.is_blocking

    def test_checkpoint_auto_dismiss_mechanism(self):
        """Checkpoint auto-dismisses when expired."""
        config = CheckpointConfig(tenant_id="tenant_001")

        checkpoint = PrioritizedCheckpoint.create(
            checkpoint_type="simulate_routing",
            incident_id="inc_001",
            tenant_id="tenant_001",
            description="Test",
            confidence=0.50,  # Low confidence
            config=config,
        )

        # Force expiry
        checkpoint.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        dismissed = checkpoint.check_auto_dismiss()

        assert dismissed
        assert checkpoint.auto_dismissed
        assert checkpoint.resolved_at is not None


# =============================================================================
# GRADUATION STATUS TESTS
# =============================================================================


class TestM25Graduation:
    """
    Tests for M25 graduation status tracking.

    M25 graduates from ALPHA to COMPLETE when all 3 gates pass.
    """

    def test_initial_status_alpha(self):
        """Initial status is ALPHA with 0 gates."""
        status = M25GraduationStatus()

        assert not status.is_graduated
        assert status.status_label == "M25-ALPHA (0/3 gates)"

    def test_gate1_contribution(self):
        """Gate 1 contributes to status."""
        status = M25GraduationStatus()

        # Pass gate 1
        record = PreventionRecord.create_prevention(
            policy_id="pol_001",
            pattern_id="pat_001",
            original_incident_id="inc_001",
            blocked_incident_id="inc_002",
            tenant_id="tenant_001",
            signature_match=0.90,
            policy_age=timedelta(hours=6),
        )
        status.prevention_tracker.record_prevention(record)

        assert status.gate1_passed
        assert not status.gate2_passed
        assert not status.gate3_passed
        assert status.status_label == "M25-ALPHA (1/3 gates)"

    def test_gate2_contribution(self):
        """Gate 2 contributes to status."""
        status = M25GraduationStatus()

        # Pass gate 2 via regret demotion
        for i in range(3):
            event = RegretEvent(
                regret_id=f"reg_{i}",
                policy_id="pol_001",
                tenant_id="tenant_001",
                regret_type=RegretType.FALSE_POSITIVE,
                description="Harm",
                severity=10,
                created_at=datetime.now(timezone.utc),
                affected_calls=100,
                affected_users=50,
                impact_duration=timedelta(hours=1),
            )
            status.regret_tracker.record_regret("pol_001", event)

        assert not status.gate1_passed
        assert status.gate2_passed
        assert status.status_label == "M25-ALPHA (1/3 gates)"

    def test_gate3_contribution(self):
        """Gate 3 contributes to status."""
        status = M25GraduationStatus()

        # Pass gate 3
        status.console_proof_incidents.append("inc_001")

        assert not status.gate1_passed
        assert not status.gate2_passed
        assert status.gate3_passed
        assert status.status_label == "M25-ALPHA (1/3 gates)"

    def test_full_graduation(self):
        """All gates passed = graduated."""
        status = M25GraduationStatus()

        # Pass gate 1
        record = PreventionRecord.create_prevention(
            policy_id="pol_001",
            pattern_id="pat_001",
            original_incident_id="inc_001",
            blocked_incident_id="inc_002",
            tenant_id="tenant_001",
            signature_match=0.88,
            policy_age=timedelta(hours=2),
        )
        status.prevention_tracker.record_prevention(record)

        # Pass gate 2
        for i in range(3):
            event = RegretEvent(
                regret_id=f"reg_{i}",
                policy_id="pol_002",
                tenant_id="tenant_001",
                regret_type=RegretType.FALSE_POSITIVE,
                description="Harm",
                severity=10,
                created_at=datetime.now(timezone.utc),
                affected_calls=100,
                affected_users=50,
                impact_duration=timedelta(hours=1),
            )
            status.regret_tracker.record_regret("pol_002", event)

        # Pass gate 3
        status.console_proof_incidents.append("inc_001")

        assert status.is_graduated
        assert status.status_label == "M25-COMPLETE"

    def test_dashboard_output(self):
        """Dashboard provides clear status information."""
        status = M25GraduationStatus()

        dashboard = status.to_dashboard()

        assert "status" in dashboard
        assert "gates" in dashboard
        assert "next_action" in dashboard
        assert "gate1_prevention" in dashboard["gates"]
        assert "gate2_rollback" in dashboard["gates"]
        assert "gate3_console" in dashboard["gates"]


# =============================================================================
# CONSOLE TIMELINE TESTS
# =============================================================================


class TestPreventionTimeline:
    """
    Tests for console timeline visualization.

    Gate 3 requires users to SEE the learning.
    """

    def test_timeline_creation(self):
        """Timeline tracks events."""
        timeline = PreventionTimeline(
            incident_id="inc_001",
            tenant_id="tenant_001",
        )

        timeline.add_incident_created(
            datetime.now(timezone.utc) - timedelta(days=3),
            {"title": "Timeout error"},
        )

        timeline.add_policy_born(
            datetime.now(timezone.utc) - timedelta(days=2),
            "pol_001",
            "Block timeout errors",
        )

        assert len(timeline.events) == 2

    def test_timeline_with_prevention(self):
        """Timeline shows prevention milestone."""
        timeline = PreventionTimeline(
            incident_id="inc_001",
            tenant_id="tenant_001",
        )

        timeline.add_incident_created(
            datetime.now(timezone.utc) - timedelta(days=3),
            {"title": "Timeout error"},
        )

        timeline.add_policy_born(
            datetime.now(timezone.utc) - timedelta(days=2),
            "pol_001",
            "Block timeout errors",
        )

        record = PreventionRecord.create_prevention(
            policy_id="pol_001",
            pattern_id="pat_001",
            original_incident_id="inc_001",
            blocked_incident_id="inc_002",
            tenant_id="tenant_001",
            signature_match=0.91,
            policy_age=timedelta(days=2),
        )
        timeline.add_prevention(datetime.now(timezone.utc), record)

        console = timeline.to_console()

        assert console["summary"]["has_prevention"]
        assert console["summary"]["is_learning_proof"]

    def test_timeline_with_regret_and_rollback(self):
        """Timeline shows regret and rollback."""
        timeline = PreventionTimeline(
            incident_id="inc_001",
            tenant_id="tenant_001",
        )

        # Add regret
        event = RegretEvent(
            regret_id="reg_001",
            policy_id="pol_001",
            tenant_id="tenant_001",
            regret_type=RegretType.FALSE_POSITIVE,
            description="Blocked valid request",
            severity=8,
            created_at=datetime.now(timezone.utc),
            affected_calls=50,
            affected_users=10,
            impact_duration=timedelta(minutes=30),
        )
        timeline.add_regret(datetime.now(timezone.utc), event)

        # Add rollback
        tracker = PolicyRegretTracker(policy_id="pol_001")
        tracker.demoted_at = datetime.now(timezone.utc)
        tracker.demoted_reason = "Too many false positives"
        tracker.regret_score = 8.0
        timeline.add_rollback(datetime.now(timezone.utc), tracker)

        console = timeline.to_console()

        assert console["summary"]["has_rollback"]

    def test_narrative_generation(self):
        """Timeline generates human-readable narrative."""
        timeline = PreventionTimeline(
            incident_id="inc_001",
            tenant_id="tenant_001",
        )

        record = PreventionRecord.create_prevention(
            policy_id="pol_001",
            pattern_id="pat_001",
            original_incident_id="inc_001",
            blocked_incident_id="inc_002",
            tenant_id="tenant_001",
            signature_match=0.88,
            policy_age=timedelta(days=1),
        )
        timeline.add_prevention(datetime.now(timezone.utc), record)

        console = timeline.to_console()

        assert "learning" in console["narrative"].lower()
        assert "prevent" in console["narrative"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
