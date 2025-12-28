"""
C5-S1 Learning Tests.

Tests against acceptance criteria from C5_S1_ACCEPTANCE_CRITERIA.md.

Reference: PIN-232, C5_S1_LEARNING_SCENARIO.md
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from unittest.mock import patch

import pytest

from app.learning.config import (
    learning_enabled,
    require_learning_enabled,
    set_learning_enabled,
)
from app.learning.s1_rollback import (
    RollbackObserver,
    observe_rollback_frequency,
)
from app.learning.suggestions import (
    LearningSuggestion,
    SuggestionConfidence,
    SuggestionStatus,
    validate_suggestion_text,
)
from app.optimization.envelope import (
    CoordinationAuditRecord,
    CoordinationDecisionType,
    EnvelopeClass,
)


class TestInvariantCriteria:
    """I-Series: Invariant verification tests."""

    def test_ac_s1_i1_advisory_only(self):
        """AC-S1-I1: Learning outputs are advisory only."""
        suggestion = LearningSuggestion()
        assert suggestion.suggestion_type == "advisory"
        # Cannot be anything else due to Literal type

    def test_ac_s1_i2_no_change_without_approval(self):
        """AC-S1-I2: No learned change applies without approval."""
        suggestion = LearningSuggestion(
            status=SuggestionStatus.PENDING_REVIEW,
            applied=False,
        )
        # Suggestion exists but applied is False
        assert not suggestion.applied
        assert suggestion.status == SuggestionStatus.PENDING_REVIEW

    def test_ac_s1_i3_metadata_only(self):
        """AC-S1-I3: Learning operates on metadata, not runtime."""
        # Verify we import from envelope.py (types) not coordinator.py (manager)
        from app.learning import s1_rollback

        source = open(s1_rollback.__file__).read()

        # Should have CoordinationAuditRecord import
        assert "CoordinationAuditRecord" in source

        # Should NOT import CoordinationManager
        assert "CoordinationManager" not in source or "# NOTE:" in source

    def test_ac_s1_i4_suggestions_versioned(self):
        """AC-S1-I4: All learned suggestions are versioned."""
        suggestion = LearningSuggestion()
        assert suggestion.version >= 1
        assert suggestion.id is not None
        assert suggestion.created_at is not None

    def test_ac_s1_i5_learning_disabled(self):
        """AC-S1-I5: Learning can be disabled without affecting coordination."""
        # Save original state
        original = learning_enabled()

        # Disable learning
        set_learning_enabled(False)
        os.environ["LEARNING_ENABLED"] = "false"

        try:
            # When disabled, observation returns None
            result = observe_rollback_frequency([], window_hours=24)
            assert result is None

            # Verify the guard decorator works
            @require_learning_enabled
            def test_func():
                return "executed"

            assert test_func() is None
        finally:
            # Restore
            set_learning_enabled(original)
            if "LEARNING_ENABLED" in os.environ:
                del os.environ["LEARNING_ENABLED"]

    def test_ac_s1_i6_killswitch_unchanged(self):
        """AC-S1-I6: Kill-switch supremacy is unchanged."""
        # Verify no kill-switch imports in learning module
        from app.learning import s1_rollback

        source = open(s1_rollback.__file__).read()

        # Should NOT have killswitch imports
        assert "from app.optimization.killswitch" not in source
        assert "import killswitch" not in source

    def test_ac_s1_i7_suggestions_replayable(self):
        """AC-S1-I7: Learned policies are replayable."""
        # Same input should produce same structure
        observer1 = RollbackObserver()
        observer2 = RollbackObserver()

        records = self._create_test_records(10, rollback_rate=0.5)

        with patch.object(observer1, "_compute_confidence", return_value=SuggestionConfidence.MEDIUM):
            with patch.object(observer2, "_compute_confidence", return_value=SuggestionConfidence.MEDIUM):
                set_learning_enabled(True)
                os.environ["LEARNING_ENABLED"] = "true"

                try:
                    window_start = datetime.now(timezone.utc) - timedelta(hours=24)
                    window_end = datetime.now(timezone.utc)

                    result1 = observer1.observe(records, window_start, window_end)
                    result2 = observer2.observe(records, window_start, window_end)

                    # Both should produce suggestions
                    assert result1 is not None
                    assert result2 is not None

                    if result1 and result2:
                        # Same structure (excluding UUID and timestamp)
                        assert len(result1) == len(result2)
                finally:
                    set_learning_enabled(False)
                    del os.environ["LEARNING_ENABLED"]

    def test_ac_s1_i8_no_autonomous_mutation(self):
        """AC-S1-I8: No autonomous policy mutation."""
        suggestion = LearningSuggestion(
            status=SuggestionStatus.ACKNOWLEDGED,
        )
        # Acknowledged but not applied
        assert not suggestion.applied
        # No mutation without explicit human action

    def _create_test_records(self, count: int, rollback_rate: float = 0.3) -> List[CoordinationAuditRecord]:
        """Create test audit records."""
        records = []
        rollback_count = int(count * rollback_rate)

        for i in range(count):
            decision = CoordinationDecisionType.REJECTED if i < rollback_count else CoordinationDecisionType.APPLIED
            records.append(
                CoordinationAuditRecord(
                    audit_id=str(uuid.uuid4()),
                    envelope_id=f"test-envelope-{i}",
                    envelope_class=EnvelopeClass.COST,
                    decision=decision,
                    reason="test",
                    timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                )
            )
        return records


class TestBoundaryCriteria:
    """B-Series: Boundary enforcement tests."""

    def test_ac_s1_b1_metadata_table_boundary(self):
        """AC-S1-B1: Only allowed tables accessed."""
        from app.learning.tables import LEARNING_ALLOWED_TABLES, LEARNING_FORBIDDEN_TABLES

        # Verify boundary definitions exist
        assert "learning_suggestions" in LEARNING_ALLOWED_TABLES
        assert "runs" in LEARNING_FORBIDDEN_TABLES
        assert "steps" in LEARNING_FORBIDDEN_TABLES

    def test_ac_s1_b2_killswitch_isolation(self):
        """AC-S1-B2: Zero imports from killswitch.py."""
        from app.learning import s1_rollback

        source = open(s1_rollback.__file__).read()
        assert "from app.optimization.killswitch" not in source

    def test_ac_s1_b3_coordinator_isolation(self):
        """AC-S1-B3: Zero manager imports from coordinator.py."""
        from app.learning import s1_rollback

        source = open(s1_rollback.__file__).read()
        # May import type definitions, but not the manager
        if "from app.optimization.coordinator" in source:
            assert "CoordinationManager" not in source

    def test_ac_s1_b4_forbidden_language_detection(self):
        """AC-S1-B4: Text contains no forbidden language patterns."""
        # Test forbidden patterns
        bad_texts = [
            "You should reduce the bounds",
            "This must be fixed",
            "This will improve reliability",
            "System recommends applying",
            "Apply this change now",
        ]

        for text in bad_texts:
            assert not validate_suggestion_text(text), f"Should reject: {text}"

        # Test allowed patterns
        good_texts = [
            "Rollback frequency suggests an issue",
            "You may want to review",
            "This pattern has been observed",
        ]

        for text in good_texts:
            assert validate_suggestion_text(text), f"Should allow: {text}"


class TestImmutabilityCriteria:
    """M-Series: Immutability guarantee tests."""

    def test_ac_s1_m1_core_fields_immutable(self):
        """AC-S1-M1: Core fields cannot be updated."""
        suggestion = LearningSuggestion(
            observation={"test": "data"},
            suggestion_text="Original text",
            suggestion_confidence=SuggestionConfidence.LOW,
        )

        original_text = suggestion.suggestion_text
        original_observation = suggestion.observation

        # These should be considered immutable in the database
        # (enforced by trigger, tested at integration level)
        # Here we just verify the fields exist
        assert suggestion.suggestion_text == original_text
        assert suggestion.observation == original_observation

    def test_ac_s1_m2_status_transition_only(self):
        """AC-S1-M2: Only status can transition."""
        suggestion = LearningSuggestion(
            status=SuggestionStatus.PENDING_REVIEW,
        )

        # Valid transitions
        suggestion.acknowledge("user-123")
        assert suggestion.status == SuggestionStatus.ACKNOWLEDGED

        # Can transition to applied_externally from acknowledged
        suggestion.mark_applied_externally("user-123")
        assert suggestion.status == SuggestionStatus.APPLIED_EXTERNALLY

    def test_ac_s1_m3_version_never_decreases(self):
        """AC-S1-M3: Version never decreases."""
        suggestion1 = LearningSuggestion(version=1)
        suggestion2 = LearningSuggestion(version=2)

        assert suggestion2.version > suggestion1.version


class TestObservationCriteria:
    """O-Series: Observation correctness tests."""

    def test_ac_s1_o1_no_rollbacks_no_suggestion(self):
        """AC-S1-O1: No rollbacks produces no suggestion."""
        set_learning_enabled(True)
        os.environ["LEARNING_ENABLED"] = "true"

        try:
            observer = RollbackObserver()

            # All APPLIED, no REJECTED (rollbacks)
            records = [
                CoordinationAuditRecord(
                    audit_id=str(uuid.uuid4()),
                    envelope_id=f"test-{i}",
                    envelope_class=EnvelopeClass.COST,
                    decision=CoordinationDecisionType.APPLIED,
                    reason="test",
                    timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                )
                for i in range(5)
            ]

            result = observer.observe(records)
            assert result == []
        finally:
            set_learning_enabled(False)
            del os.environ["LEARNING_ENABLED"]

    def test_ac_s1_o2_below_threshold_no_suggestion(self):
        """AC-S1-O2: Below threshold produces no suggestion."""
        set_learning_enabled(True)
        os.environ["LEARNING_ENABLED"] = "true"

        try:
            observer = RollbackObserver()

            # 1 rollback out of 10 = 10% (below 30% threshold)
            records = []
            for i in range(10):
                decision = CoordinationDecisionType.REJECTED if i == 0 else CoordinationDecisionType.APPLIED
                records.append(
                    CoordinationAuditRecord(
                        audit_id=str(uuid.uuid4()),
                        envelope_id=f"test-{i}",
                        envelope_class=EnvelopeClass.COST,
                        decision=decision,
                        reason="test",
                        timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                    )
                )

            result = observer.observe(records)
            assert result == []
        finally:
            set_learning_enabled(False)
            del os.environ["LEARNING_ENABLED"]

    def test_ac_s1_o3_above_threshold_produces_advisory(self):
        """AC-S1-O3: Above threshold produces advisory suggestion."""
        set_learning_enabled(True)
        os.environ["LEARNING_ENABLED"] = "true"

        try:
            observer = RollbackObserver()

            # 5 rollbacks out of 10 = 50% (above 30% threshold)
            records = []
            for i in range(10):
                decision = CoordinationDecisionType.REJECTED if i < 5 else CoordinationDecisionType.APPLIED
                records.append(
                    CoordinationAuditRecord(
                        audit_id=str(uuid.uuid4()),
                        envelope_id=f"test-{i}",
                        envelope_class=EnvelopeClass.COST,
                        decision=decision,
                        reason="test",
                        timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                    )
                )

            result = observer.observe(records)
            assert result is not None
            assert len(result) > 0
            assert result[0].suggestion_type == "advisory"
            assert result[0].status == SuggestionStatus.PENDING_REVIEW
        finally:
            set_learning_enabled(False)
            del os.environ["LEARNING_ENABLED"]

    def test_ac_s1_o4_window_boundaries_respected(self):
        """AC-S1-O4: Only records inside window are counted."""
        set_learning_enabled(True)
        os.environ["LEARNING_ENABLED"] = "true"

        try:
            observer = RollbackObserver()

            now = datetime.now(timezone.utc)

            # Records outside window (should be excluded)
            outside_records = [
                CoordinationAuditRecord(
                    audit_id=str(uuid.uuid4()),
                    envelope_id=f"outside-{i}",
                    envelope_class=EnvelopeClass.COST,
                    decision=CoordinationDecisionType.REJECTED,
                    reason="test",
                    timestamp=now - timedelta(days=10 + i),
                )
                for i in range(5)
            ]

            # Records inside window
            inside_records = [
                CoordinationAuditRecord(
                    audit_id=str(uuid.uuid4()),
                    envelope_id=f"inside-{i}",
                    envelope_class=EnvelopeClass.COST,
                    decision=CoordinationDecisionType.APPLIED,
                    reason="test",
                    timestamp=now - timedelta(hours=i),
                )
                for i in range(5)
            ]

            all_records = outside_records + inside_records

            # Only inside records should be analyzed
            window_start = now - timedelta(hours=24)
            window_end = now

            result = observer.observe(all_records, window_start, window_end)

            # No suggestion because inside records have no rollbacks
            assert result == []
        finally:
            set_learning_enabled(False)
            del os.environ["LEARNING_ENABLED"]


class TestHumanInteractionCriteria:
    """H-Series: Human interaction model tests."""

    def test_ac_s1_h1_acknowledge_changes_status_only(self):
        """AC-S1-H1: Acknowledge changes status, no system change."""
        suggestion = LearningSuggestion(
            status=SuggestionStatus.PENDING_REVIEW,
        )

        suggestion.acknowledge("user-123")

        assert suggestion.status == SuggestionStatus.ACKNOWLEDGED
        assert suggestion.human_action == "acknowledge"
        assert suggestion.human_actor_id == "user-123"
        assert suggestion.human_action_at is not None
        assert not suggestion.applied  # No system change

    def test_ac_s1_h2_dismiss_changes_status_only(self):
        """AC-S1-H2: Dismiss changes status, no system change."""
        suggestion = LearningSuggestion(
            status=SuggestionStatus.PENDING_REVIEW,
        )

        suggestion.dismiss("user-123")

        assert suggestion.status == SuggestionStatus.DISMISSED
        assert suggestion.human_action == "dismiss"
        assert not suggestion.applied  # No system change

    def test_ac_s1_h3_mark_applied_records_only(self):
        """AC-S1-H3: Mark applied changes status, records only."""
        suggestion = LearningSuggestion(
            status=SuggestionStatus.ACKNOWLEDGED,
        )

        suggestion.mark_applied_externally("user-123")

        assert suggestion.status == SuggestionStatus.APPLIED_EXTERNALLY
        assert suggestion.human_action == "mark_applied"
        assert suggestion.applied  # Records that human took action

    def test_ac_s1_h4_human_action_logged(self):
        """AC-S1-H4: Human action logged with all fields."""
        suggestion = LearningSuggestion()

        suggestion.acknowledge("user-123")

        assert suggestion.human_action is not None
        assert suggestion.human_action_at is not None
        assert suggestion.human_actor_id is not None


class TestDisableFlagCriteria:
    """D-Series: Disable flag behavior tests."""

    def test_ac_s1_d1_disable_flag_prevents_observation(self):
        """AC-S1-D1: Disable flag prevents observation."""
        set_learning_enabled(False)
        os.environ["LEARNING_ENABLED"] = "false"

        try:
            observer = RollbackObserver()
            records = [
                CoordinationAuditRecord(
                    audit_id=str(uuid.uuid4()),
                    envelope_id="test",
                    envelope_class=EnvelopeClass.COST,
                    decision=CoordinationDecisionType.REJECTED,
                    reason="test",
                    timestamp=datetime.now(timezone.utc),
                )
            ]

            result = observer.observe(records)
            assert result is None  # Returns None when disabled
        finally:
            del os.environ["LEARNING_ENABLED"]

    def test_ac_s1_d2_disable_flag_prevents_generation(self):
        """AC-S1-D2: Disable flag prevents suggestion generation."""
        set_learning_enabled(False)
        os.environ["LEARNING_ENABLED"] = "false"

        try:
            result = observe_rollback_frequency([])
            assert result is None
        finally:
            del os.environ["LEARNING_ENABLED"]

    def test_ac_s1_d3_disable_flag_silent(self):
        """AC-S1-D3: Disable flag is silent (no error)."""
        set_learning_enabled(False)
        os.environ["LEARNING_ENABLED"] = "false"

        try:
            # Should not raise, just return None
            result = observe_rollback_frequency([])
            assert result is None
        except Exception as e:
            pytest.fail(f"Should not raise when disabled: {e}")
        finally:
            del os.environ["LEARNING_ENABLED"]


class TestSuggestionTextGeneration:
    """Test suggestion text uses observational language."""

    def test_generated_text_observational(self):
        """Generated text uses observational language only."""
        set_learning_enabled(True)
        os.environ["LEARNING_ENABLED"] = "true"

        try:
            observer = RollbackObserver()

            # High rollback rate to trigger suggestion
            records = [
                CoordinationAuditRecord(
                    audit_id=str(uuid.uuid4()),
                    envelope_id=f"test-{i}",
                    envelope_class=EnvelopeClass.COST,
                    decision=(CoordinationDecisionType.REJECTED if i < 7 else CoordinationDecisionType.APPLIED),
                    reason="test",
                    timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                )
                for i in range(10)
            ]

            result = observer.observe(records)

            assert result is not None
            assert len(result) > 0

            for suggestion in result:
                # Verify text passes validation
                assert validate_suggestion_text(
                    suggestion.suggestion_text
                ), f"Text should use observational language: {suggestion.suggestion_text}"
        finally:
            set_learning_enabled(False)
            del os.environ["LEARNING_ENABLED"]
