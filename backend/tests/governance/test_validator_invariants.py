# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Validator invariant tests (VAL-001 through VAL-005)
# Callers: pytest
# Allowed Imports: Any (test layer)
# Forbidden Imports: None
# Reference: PIN-287, VALIDATOR_LOGIC.md, part2-design-v1

"""
Validator Invariant Tests

Tests enforcement of validator invariants from VALIDATOR_LOGIC.md:

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| VAL-001 | Validator is stateless | No writes |
| VAL-002 | Verdicts include version | Required field |
| VAL-003 | Confidence in [0,1] | Clamping |
| VAL-004 | Unknown type defers | Action logic |
| VAL-005 | Escalation always escalates | Action logic |

Reference: PIN-287, VALIDATOR_LOGIC.md
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.governance.validator_service import (
    VALIDATOR_VERSION,
    IssueType,
    RecommendedAction,
    Severity,
    ValidatorInput,
    ValidatorService,
)

# ==============================================================================
# TEST FIXTURES
# ==============================================================================


@pytest.fixture
def validator() -> ValidatorService:
    """Create validator with test capability registry."""
    return ValidatorService(capability_registry=["email_send", "sms_send", "webhook_call", "data_export"])


@pytest.fixture
def basic_input() -> ValidatorInput:
    """Create basic validator input."""
    return ValidatorInput(
        issue_id=uuid4(),
        source="support_ticket",
        raw_payload={
            "subject": "Test Issue",
            "body": "This is a test issue body.",
        },
        received_at=datetime.now(timezone.utc),
    )


def make_input(subject: str, body: str, source: str = "support_ticket") -> ValidatorInput:
    """Helper to create validator input with specific content."""
    return ValidatorInput(
        issue_id=uuid4(),
        source=source,
        raw_payload={"subject": subject, "body": body},
        received_at=datetime.now(timezone.utc),
    )


# ==============================================================================
# VAL-001: Validator is Stateless
# ==============================================================================


class TestVAL001Stateless:
    """VAL-001: Validator is stateless (no writes)."""

    def test_multiple_calls_same_input_same_output(self, validator: ValidatorService):
        """Same input should produce same output (determinism)."""
        input = make_input(
            subject="Enable email_send capability",
            body="Please enable the email_send capability for our account.",
        )

        verdict1 = validator.validate(input)
        verdict2 = validator.validate(input)

        assert verdict1.issue_type == verdict2.issue_type
        assert verdict1.severity == verdict2.severity
        assert verdict1.recommended_action == verdict2.recommended_action
        assert verdict1.confidence_score == verdict2.confidence_score
        assert verdict1.affected_capabilities == verdict2.affected_capabilities

    def test_validator_has_no_mutable_state(self, validator: ValidatorService):
        """Validator should not accumulate state between calls."""
        input1 = make_input("Enable email_send", "Enable capability")
        input2 = make_input("Bug in webhook", "The webhook is broken")

        # Process different inputs
        verdict1 = validator.validate(input1)
        _ = validator.validate(input2)  # Different input should not affect state

        # Process first input again - should be identical to original
        verdict1_again = validator.validate(input1)

        assert verdict1.issue_type == verdict1_again.issue_type
        assert verdict1.severity == verdict1_again.severity
        assert verdict1.confidence_score == verdict1_again.confidence_score


# ==============================================================================
# VAL-002: Verdicts Include Version
# ==============================================================================


class TestVAL002VersionRequired:
    """VAL-002: Verdicts include version (required field)."""

    def test_verdict_has_version(self, validator: ValidatorService, basic_input: ValidatorInput):
        """Every verdict must include validator version."""
        verdict = validator.validate(basic_input)
        assert verdict.validator_version is not None
        assert len(verdict.validator_version) > 0

    def test_version_matches_constant(self, validator: ValidatorService, basic_input: ValidatorInput):
        """Version should match the VALIDATOR_VERSION constant."""
        verdict = validator.validate(basic_input)
        assert verdict.validator_version == VALIDATOR_VERSION

    def test_version_is_semantic(self, validator: ValidatorService, basic_input: ValidatorInput):
        """Version should be semantic (X.Y.Z format)."""
        verdict = validator.validate(basic_input)
        parts = verdict.validator_version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_fallback_verdict_has_version(self, validator: ValidatorService):
        """Even fallback verdicts must have version."""
        # Create input that might cause issues
        input = ValidatorInput(
            issue_id=uuid4(),
            source="manual",
            raw_payload={},  # Empty payload
            received_at=datetime.now(timezone.utc),
        )
        verdict = validator.validate(input)
        assert verdict.validator_version == VALIDATOR_VERSION


# ==============================================================================
# VAL-003: Confidence in [0, 1]
# ==============================================================================


class TestVAL003ConfidenceClamping:
    """VAL-003: Confidence in [0,1] (clamping)."""

    def test_confidence_minimum_zero(self, validator: ValidatorService):
        """Confidence should never be negative."""
        # Create input with minimal confidence signals
        input = make_input(
            subject="asdf",
            body="qwerty",
            source="manual",  # Lowest source weight
        )
        verdict = validator.validate(input)
        assert verdict.confidence_score >= Decimal("0.0")

    def test_confidence_maximum_one(self, validator: ValidatorService):
        """Confidence should never exceed 1.0."""
        # Create input with maximum confidence signals
        input = make_input(
            subject="URGENT SECURITY BREACH - Critical bug in email_send capability",
            body=(
                "Production outage affecting multiple tenants. "
                "The email_send capability is completely broken. "
                "Business-critical workflow blocked. "
                "Security implications detected."
            ),
            source="ops_alert",  # Highest source weight
        )
        verdict = validator.validate(input)
        assert verdict.confidence_score <= Decimal("1.0")

    def test_confidence_is_decimal(self, validator: ValidatorService, basic_input: ValidatorInput):
        """Confidence should be Decimal type."""
        verdict = validator.validate(basic_input)
        assert isinstance(verdict.confidence_score, Decimal)

    def test_various_inputs_bounded(self, validator: ValidatorService):
        """All inputs should produce bounded confidence."""
        test_cases = [
            make_input("Enable feature", "Please enable", "crm_feedback"),
            make_input("Bug bug bug bug", "Error error error", "support_ticket"),
            make_input("Configure threshold", "Change the limit", "ops_alert"),
            make_input("URGENT EMERGENCY", "Critical security", "manual"),
        ]

        for input in test_cases:
            verdict = validator.validate(input)
            assert Decimal("0.0") <= verdict.confidence_score <= Decimal("1.0"), (
                f"Confidence {verdict.confidence_score} out of bounds for input: {input.raw_payload}"
            )


# ==============================================================================
# VAL-004: Unknown Type Defers
# ==============================================================================


class TestVAL004UnknownDefers:
    """VAL-004: Unknown type defers (action logic)."""

    def test_unknown_classification_defers(self, validator: ValidatorService):
        """Issues classified as unknown should defer."""
        # Create input with no classification signals
        input = make_input(
            subject="xyz abc",
            body="123 456 789",
        )
        verdict = validator.validate(input)

        if verdict.issue_type == IssueType.UNKNOWN:
            assert verdict.recommended_action == RecommendedAction.DEFER

    def test_low_confidence_may_produce_unknown(self, validator: ValidatorService):
        """Very low confidence should result in unknown classification."""
        # Create input with contradictory/weak signals
        input = make_input(
            subject="",
            body="",
        )
        verdict = validator.validate(input)

        # Unknown type must defer
        if verdict.issue_type == IssueType.UNKNOWN:
            assert verdict.recommended_action == RecommendedAction.DEFER


# ==============================================================================
# VAL-005: Escalation Always Escalates
# ==============================================================================


class TestVAL005EscalationAlwaysEscalates:
    """VAL-005: Escalation always escalates (action logic)."""

    def test_urgent_keyword_escalates(self, validator: ValidatorService):
        """Issues with 'urgent' keyword should escalate."""
        input = make_input(
            subject="URGENT: Server down",
            body="This is urgent, please respond immediately.",
        )
        verdict = validator.validate(input)
        assert verdict.recommended_action == RecommendedAction.ESCALATE

    def test_emergency_keyword_escalates(self, validator: ValidatorService):
        """Issues with 'emergency' keyword should escalate."""
        input = make_input(
            subject="Emergency situation",
            body="We have an emergency that needs immediate attention.",
        )
        verdict = validator.validate(input)
        assert verdict.recommended_action == RecommendedAction.ESCALATE

    def test_security_keyword_escalates(self, validator: ValidatorService):
        """Issues with 'security' keyword should escalate."""
        input = make_input(
            subject="Security incident",
            body="We detected a potential security breach.",
        )
        verdict = validator.validate(input)
        assert verdict.recommended_action == RecommendedAction.ESCALATE

    def test_critical_keyword_escalates(self, validator: ValidatorService):
        """Issues with 'critical' keyword should escalate."""
        input = make_input(
            subject="Critical issue",
            body="This is a critical problem affecting production.",
        )
        verdict = validator.validate(input)
        assert verdict.recommended_action == RecommendedAction.ESCALATE

    def test_escalation_type_always_escalates(self, validator: ValidatorService):
        """IssueType.ESCALATION must always produce ESCALATE action."""
        # Test multiple escalation keywords
        escalation_phrases = [
            ("urgent", "urgent request"),
            ("emergency", "emergency situation"),
            ("critical", "critical issue"),
            ("security", "security concern"),
            ("asap", "need this asap"),
        ]

        for phrase, context in escalation_phrases:
            input = make_input(
                subject=f"Test {phrase}",
                body=f"This is a {context}.",
            )
            verdict = validator.validate(input)

            # If classified as escalation, must escalate
            if verdict.issue_type == IssueType.ESCALATION:
                assert verdict.recommended_action == RecommendedAction.ESCALATE, (
                    f"Escalation type did not escalate for phrase: {phrase}"
                )


# ==============================================================================
# ISSUE TYPE CLASSIFICATION TESTS
# ==============================================================================


class TestIssueTypeClassification:
    """Test issue type classification logic."""

    def test_capability_request_classification(self, validator: ValidatorService):
        """Test capability request classification."""
        input = make_input(
            subject="Enable email_send capability",
            body="Please enable the email_send capability for our tenant.",
        )
        verdict = validator.validate(input)
        assert verdict.issue_type == IssueType.CAPABILITY_REQUEST

    def test_bug_report_classification(self, validator: ValidatorService):
        """Test bug report classification."""
        input = make_input(
            subject="Bug in webhook processing",
            body="The webhook fails with an error when sending to external endpoint.",
        )
        verdict = validator.validate(input)
        assert verdict.issue_type == IssueType.BUG_REPORT

    def test_configuration_change_classification(self, validator: ValidatorService):
        """Test configuration change classification."""
        input = make_input(
            subject="Configure rate limit threshold",
            body="Please update the rate limit setting to 1000 requests per minute.",
        )
        verdict = validator.validate(input)
        assert verdict.issue_type == IssueType.CONFIGURATION_CHANGE


# ==============================================================================
# SEVERITY CLASSIFICATION TESTS
# ==============================================================================


class TestSeverityClassification:
    """Test severity classification logic."""

    def test_critical_severity(self, validator: ValidatorService):
        """Test critical severity classification."""
        input = make_input(
            subject="Production outage",
            body="Multiple tenants affected by system-wide failure. Data integrity at risk.",
        )
        verdict = validator.validate(input)
        assert verdict.severity in [Severity.CRITICAL, Severity.HIGH]

    def test_low_severity(self, validator: ValidatorService):
        """Test low severity classification."""
        input = make_input(
            subject="Minor cosmetic issue",
            body="There's a typo in the documentation. Nice to have fix.",
        )
        verdict = validator.validate(input)
        assert verdict.severity == Severity.LOW


# ==============================================================================
# CAPABILITY EXTRACTION TESTS
# ==============================================================================


class TestCapabilityExtraction:
    """Test capability extraction logic."""

    def test_exact_match_extraction(self, validator: ValidatorService):
        """Test exact capability name match."""
        input = make_input(
            subject="Issue with email_send",
            body="The email_send capability is not working.",
        )
        verdict = validator.validate(input)
        assert "email_send" in verdict.affected_capabilities

    def test_hint_inclusion(self):
        """Test that hints are included in capabilities."""
        validator = ValidatorService(capability_registry=["email_send"])
        input = ValidatorInput(
            issue_id=uuid4(),
            source="support_ticket",
            raw_payload={"subject": "Test", "body": "Test body"},
            received_at=datetime.now(timezone.utc),
            affected_capabilities_hint=["custom_capability"],
        )
        verdict = validator.validate(input)
        assert "custom_capability" in verdict.affected_capabilities

    def test_empty_capabilities(self):
        """Test with no capability registry."""
        validator = ValidatorService(capability_registry=None)
        input = make_input(
            subject="General issue",
            body="Something is wrong.",
        )
        verdict = validator.validate(input)
        # Should still work, just with empty capabilities
        assert verdict.affected_capabilities is not None


# ==============================================================================
# RECOMMENDED ACTION TESTS
# ==============================================================================


class TestRecommendedAction:
    """Test recommended action logic."""

    def test_high_confidence_creates_contract(self, validator: ValidatorService):
        """High confidence non-escalation should create contract."""
        input = make_input(
            subject="Enable email_send capability for our account",
            body="We need to enable the email_send feature. Please activate this capability.",
            source="ops_alert",
        )
        verdict = validator.validate(input)

        # If not escalation and high confidence, should create contract
        if (
            verdict.issue_type != IssueType.ESCALATION
            and verdict.issue_type != IssueType.UNKNOWN
            and verdict.confidence_score >= Decimal("0.5")
        ):
            assert verdict.recommended_action == RecommendedAction.CREATE_CONTRACT

    def test_critical_bug_escalates(self, validator: ValidatorService):
        """Critical bugs should escalate."""
        input = make_input(
            subject="Critical bug - production outage",
            body=(
                "The system is completely broken. Multiple tenants affected. "
                "Production outage ongoing. Data integrity at risk."
            ),
            source="ops_alert",
        )
        verdict = validator.validate(input)

        # Critical bugs or security issues should escalate
        if verdict.severity == Severity.CRITICAL:
            assert verdict.recommended_action == RecommendedAction.ESCALATE


# ==============================================================================
# EVIDENCE AND REASON TESTS
# ==============================================================================


class TestVerdictEvidence:
    """Test verdict evidence and reason fields."""

    def test_verdict_has_evidence(self, validator: ValidatorService, basic_input: ValidatorInput):
        """Verdicts should include evidence."""
        verdict = validator.validate(basic_input)
        assert verdict.evidence is not None
        assert isinstance(verdict.evidence, dict)

    def test_evidence_has_confidence_components(self, validator: ValidatorService, basic_input: ValidatorInput):
        """Evidence should include confidence components."""
        verdict = validator.validate(basic_input)
        assert "confidence_components" in verdict.evidence

    def test_verdict_has_reason(self, validator: ValidatorService, basic_input: ValidatorInput):
        """Verdicts should include human-readable reason."""
        verdict = validator.validate(basic_input)
        assert verdict.reason is not None
        assert len(verdict.reason) > 0

    def test_verdict_has_analyzed_at(self, validator: ValidatorService, basic_input: ValidatorInput):
        """Verdicts should include analysis timestamp."""
        verdict = validator.validate(basic_input)
        assert verdict.analyzed_at is not None
        assert verdict.analyzed_at.tzinfo is not None  # Should be timezone-aware
