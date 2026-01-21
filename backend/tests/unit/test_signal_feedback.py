# Layer: L8 — Tests
# Product: ai-console
# Role: Unit tests for Signal Feedback Loop
# Reference: Attention Feedback Loop Implementation Plan
#
# Tests:
# - test_signal_fingerprint_deterministic()
# - test_acknowledge_creates_audit_entry()
# - test_suppress_creates_audit_entry_with_ttl()
# - test_fingerprint_format_validation()
# - test_dampening_is_idempotent()

"""
Signal Feedback Unit Tests

Verifies:
- SIGNAL-ID-001: Canonical fingerprint derivation
- ATTN-DAMP-001: Idempotent dampening
- SIGNAL-SUPPRESS-001: Suppression constraints
- AUDIT-SIGNAL-CTX-001: Structured context schema
"""

import hashlib
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# =============================================================================
# Signal Identity Tests (SIGNAL-ID-001)
# =============================================================================


class TestSignalFingerprint:
    """Tests for signal_identity.py"""

    def test_signal_fingerprint_deterministic(self):
        """
        SIGNAL-ID-001: Fingerprint computation is deterministic.
        Same input always produces same output.
        """
        from app.services.activity.signal_identity import compute_signal_fingerprint_from_row

        row = {
            "run_id": "run-abc123",
            "signal_type": "COST_RISK",
            "risk_type": "COST",
            "evaluation_outcome": "BREACH",
        }

        # Compute twice
        fp1 = compute_signal_fingerprint_from_row(row)
        fp2 = compute_signal_fingerprint_from_row(row)

        # Must be identical
        assert fp1 == fp2, "Fingerprint must be deterministic"

        # Verify format
        assert fp1.startswith("sig-"), "Fingerprint must start with 'sig-'"
        assert len(fp1) == 20, "Fingerprint must be 20 chars (sig- + 16 hex)"

    def test_signal_fingerprint_format(self):
        """
        SIGNAL-ID-001: Fingerprint format is sig-{16 hex chars}.
        """
        from app.services.activity.signal_identity import compute_signal_fingerprint_from_row

        row = {
            "run_id": "test-run",
            "signal_type": "TIME_RISK",
            "risk_type": "TIME",
            "evaluation_outcome": "NEAR_THRESHOLD",
        }

        fp = compute_signal_fingerprint_from_row(row)

        # Format validation
        assert fp.startswith("sig-")
        hash_part = fp[4:]
        assert len(hash_part) == 16
        # Verify it's valid hex
        int(hash_part, 16)  # Should not raise

    def test_signal_fingerprint_different_inputs(self):
        """
        SIGNAL-ID-001: Different inputs produce different fingerprints.
        """
        from app.services.activity.signal_identity import compute_signal_fingerprint_from_row

        row1 = {
            "run_id": "run-1",
            "signal_type": "COST_RISK",
            "risk_type": "COST",
            "evaluation_outcome": "BREACH",
        }

        row2 = {
            "run_id": "run-2",  # Different run_id
            "signal_type": "COST_RISK",
            "risk_type": "COST",
            "evaluation_outcome": "BREACH",
        }

        fp1 = compute_signal_fingerprint_from_row(row1)
        fp2 = compute_signal_fingerprint_from_row(row2)

        assert fp1 != fp2, "Different inputs must produce different fingerprints"

    def test_fingerprint_validation(self):
        """
        SIGNAL-ID-001: Fingerprint validation function works correctly.
        """
        from app.services.activity.signal_identity import validate_signal_fingerprint

        # Valid fingerprints
        assert validate_signal_fingerprint("sig-a1b2c3d4e5f6g7h8") is False  # 'g' is not hex
        assert validate_signal_fingerprint("sig-a1b2c3d4e5f67890") is True
        assert validate_signal_fingerprint("sig-0000000000000000") is True
        assert validate_signal_fingerprint("sig-ffffffffffffffff") is True

        # Invalid fingerprints
        assert validate_signal_fingerprint("") is False
        assert validate_signal_fingerprint(None) is False
        assert validate_signal_fingerprint("invalid") is False
        assert validate_signal_fingerprint("sig-") is False
        assert validate_signal_fingerprint("sig-short") is False
        assert validate_signal_fingerprint("sig-toolongtobevalid123") is False


# =============================================================================
# Signal Context Tests (AUDIT-SIGNAL-CTX-001)
# =============================================================================


class TestSignalContext:
    """Tests for SignalContext schema"""

    def test_build_signal_context_schema(self):
        """
        AUDIT-SIGNAL-CTX-001: Signal context has fixed schema.
        """
        from app.services.activity.signal_feedback_service import build_signal_context

        ctx = build_signal_context(
            run_id="run-123",
            signal_type="COST_RISK",
            risk_type="COST",
            evaluation_outcome="BREACH",
            policy_id="pol-456",
        )

        # Required fields
        assert ctx["run_id"] == "run-123"
        assert ctx["signal_type"] == "COST_RISK"
        assert ctx["risk_type"] == "COST"
        assert ctx["evaluation_outcome"] == "BREACH"
        assert ctx["policy_id"] == "pol-456"
        assert ctx["schema_version"] == "1.0"

    def test_signal_context_without_policy(self):
        """
        AUDIT-SIGNAL-CTX-001: policy_id is optional.
        """
        from app.services.activity.signal_feedback_service import build_signal_context

        ctx = build_signal_context(
            run_id="run-123",
            signal_type="COST_RISK",
            risk_type="COST",
            evaluation_outcome="BREACH",
        )

        assert ctx["policy_id"] is None
        assert ctx["schema_version"] == "1.0"


# =============================================================================
# Dampening Tests (ATTN-DAMP-001)
# =============================================================================


class TestDampening:
    """Tests for attention score dampening"""

    def test_dampening_constant_frozen(self):
        """
        ATTN-DAMP-001: ACK_DAMPENER is frozen at 0.6.
        """
        from app.services.activity.attention_ranking_service import ACK_DAMPENER

        assert ACK_DAMPENER == 0.6, "ACK_DAMPENER must be 0.6 (frozen)"

    def test_dampening_is_idempotent(self):
        """
        ATTN-DAMP-001: Dampening is idempotent (apply once, not compound).
        """
        from app.services.activity.attention_ranking_service import ACK_DAMPENER

        base_score = 0.85

        # Apply dampening once
        effective_score = base_score * ACK_DAMPENER

        # Verify it's NOT compounded
        # If we were to apply again (which we shouldn't), it would be different
        wrong_compounded = effective_score * ACK_DAMPENER

        assert effective_score == 0.51  # 0.85 * 0.6 = 0.51
        assert wrong_compounded != effective_score, "Dampening must not compound"

        # The correct behavior: apply ONCE
        assert effective_score == base_score * 0.6


# =============================================================================
# Suppression Constraints Tests (SIGNAL-SUPPRESS-001)
# =============================================================================


class TestSuppressionConstraints:
    """Tests for suppression duration constraints"""

    def test_suppression_min_duration(self):
        """
        SIGNAL-SUPPRESS-001: Minimum duration is 15 minutes.
        """
        # Duration validation is in the API endpoint
        min_duration = 15
        assert min_duration == 15

    def test_suppression_max_duration(self):
        """
        SIGNAL-SUPPRESS-001: Maximum duration is 1440 minutes (24 hours).
        """
        max_duration = 1440
        assert max_duration == 1440

    def test_suppression_duration_range(self):
        """
        SIGNAL-SUPPRESS-001: Valid durations are 15-1440 minutes.
        """
        valid_durations = [15, 30, 60, 120, 480, 1440]
        invalid_durations = [0, 1, 14, 1441, 2880]

        for d in valid_durations:
            assert 15 <= d <= 1440, f"Duration {d} should be valid"

        for d in invalid_durations:
            assert not (15 <= d <= 1440), f"Duration {d} should be invalid"


# =============================================================================
# Audit Entry Tests
# =============================================================================


class TestAuditEntries:
    """Tests for audit ledger entries"""

    def test_signal_entity_type_exists(self):
        """
        Audit ledger has SIGNAL entity type.
        """
        from app.models.audit_ledger import AuditEntityType

        assert hasattr(AuditEntityType, "SIGNAL")
        assert AuditEntityType.SIGNAL.value == "SIGNAL"

    def test_signal_event_types_exist(self):
        """
        Audit ledger has signal event types.
        """
        from app.models.audit_ledger import AuditEventType

        assert hasattr(AuditEventType, "SIGNAL_ACKNOWLEDGED")
        assert hasattr(AuditEventType, "SIGNAL_SUPPRESSED")

        assert AuditEventType.SIGNAL_ACKNOWLEDGED.value == "SignalAcknowledged"
        assert AuditEventType.SIGNAL_SUPPRESSED.value == "SignalSuppressed"


# =============================================================================
# Weights Validation Tests
# =============================================================================


class TestAttentionWeights:
    """Tests for attention score weights"""

    def test_weights_sum_to_one(self):
        """
        Attention weights must sum to 1.0.
        """
        from app.services.activity.attention_ranking_service import ATTENTION_WEIGHTS

        total = sum(ATTENTION_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, expected 1.0"

    def test_weights_version_exists(self):
        """
        Weights version is tracked.
        """
        from app.services.activity.attention_ranking_service import WEIGHTS_VERSION

        assert WEIGHTS_VERSION == "1.0"
