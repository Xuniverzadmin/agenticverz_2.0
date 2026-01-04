# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Eligibility Engine invariant tests (ELIG-001 through ELIG-005)
# Callers: pytest
# Allowed Imports: Any (test layer)
# Forbidden Imports: None
# Reference: PIN-289, ELIGIBILITY_RULES.md, part2-design-v1

"""
Eligibility Engine Invariant Tests

Tests enforcement of eligibility invariants from ELIGIBILITY_RULES.md:

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| ELIG-001 | Eligibility is deterministic | Pure function, no side effects |
| ELIG-002 | Every verdict has a reason | Required field |
| ELIG-003 | MAY_NOT rules take precedence | Evaluation order |
| ELIG-004 | Health degradation blocks all | E-104 priority |
| ELIG-005 | Frozen capabilities are inviolable | E-102 check |

Reference: PIN-289, ELIGIBILITY_RULES.md
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.governance.eligibility_engine import (
    ELIGIBILITY_ENGINE_VERSION,
    DefaultCapabilityLookup,
    DefaultContractLookup,
    DefaultGovernanceSignalLookup,
    DefaultPreApprovalLookup,
    DefaultSystemHealthLookup,
    EligibilityConfig,
    EligibilityDecision,
    EligibilityEngine,
    EligibilityInput,
    SystemHealthStatus,
)
from app.services.governance.validator_service import (
    IssueType,
    RecommendedAction,
    Severity,
    ValidatorVerdict,
)

# ==============================================================================
# TEST FIXTURES
# ==============================================================================


@pytest.fixture
def capability_registry() -> frozenset[str]:
    """Standard capability registry for testing."""
    return frozenset(["email_send", "sms_send", "webhook_call", "data_export"])


@pytest.fixture
def engine(capability_registry: frozenset[str]) -> EligibilityEngine:
    """Create eligibility engine with test lookups."""
    return EligibilityEngine(
        capability_lookup=DefaultCapabilityLookup(registry=capability_registry),
    )


@pytest.fixture
def high_confidence_verdict() -> ValidatorVerdict:
    """Create a high confidence validator verdict."""
    return ValidatorVerdict(
        issue_type=IssueType.CAPABILITY_REQUEST,
        severity=Severity.MEDIUM,
        affected_capabilities=("email_send",),
        recommended_action=RecommendedAction.CREATE_CONTRACT,
        confidence_score=Decimal("0.85"),
        reason="High confidence capability request",
        evidence={"test": True},
        analyzed_at=datetime.now(timezone.utc),
        validator_version="1.0.0",
    )


@pytest.fixture
def low_confidence_verdict() -> ValidatorVerdict:
    """Create a low confidence validator verdict."""
    return ValidatorVerdict(
        issue_type=IssueType.UNKNOWN,
        severity=Severity.MEDIUM,
        affected_capabilities=(),
        recommended_action=RecommendedAction.DEFER,
        confidence_score=Decimal("0.20"),
        reason="Low confidence",
        evidence={"test": True},
        analyzed_at=datetime.now(timezone.utc),
        validator_version="1.0.0",
    )


def make_input(
    verdict: ValidatorVerdict,
    source: str = "support_ticket",
    capabilities: tuple[str, ...] | None = None,
) -> EligibilityInput:
    """Helper to create eligibility input."""
    return EligibilityInput(
        proposal_id=uuid4(),
        validator_verdict=verdict,
        source=source,
        affected_capabilities=capabilities or verdict.affected_capabilities,
        received_at=datetime.now(timezone.utc),
    )


def make_verdict(
    issue_type: IssueType = IssueType.CAPABILITY_REQUEST,
    severity: Severity = Severity.MEDIUM,
    action: RecommendedAction = RecommendedAction.CREATE_CONTRACT,
    confidence: Decimal = Decimal("0.85"),
    capabilities: tuple[str, ...] = ("email_send",),
) -> ValidatorVerdict:
    """Helper to create a validator verdict."""
    return ValidatorVerdict(
        issue_type=issue_type,
        severity=severity,
        affected_capabilities=capabilities,
        recommended_action=action,
        confidence_score=confidence,
        reason="Test verdict",
        evidence={"test": True},
        analyzed_at=datetime.now(timezone.utc),
        validator_version="1.0.0",
    )


# ==============================================================================
# ELIG-001: Eligibility is Deterministic
# ==============================================================================


class TestELIG001Deterministic:
    """ELIG-001: Eligibility is deterministic (pure function, no side effects)."""

    def test_same_input_same_output(self, engine: EligibilityEngine, high_confidence_verdict: ValidatorVerdict):
        """Same input should produce same output."""
        input = make_input(high_confidence_verdict)

        verdict1 = engine.evaluate(input)
        verdict2 = engine.evaluate(input)

        assert verdict1.decision == verdict2.decision
        assert verdict1.reason == verdict2.reason
        assert verdict1.rules_evaluated == verdict2.rules_evaluated
        assert verdict1.first_failing_rule == verdict2.first_failing_rule

    def test_no_state_accumulation(self, engine: EligibilityEngine):
        """Engine should not accumulate state between calls."""
        verdict1 = make_verdict(confidence=Decimal("0.85"))
        verdict2 = make_verdict(confidence=Decimal("0.20"))

        input1 = make_input(verdict1)
        input2 = make_input(verdict2)

        result1a = engine.evaluate(input1)
        _ = engine.evaluate(input2)  # Different input
        result1b = engine.evaluate(input1)

        assert result1a.decision == result1b.decision
        assert result1a.rules_evaluated == result1b.rules_evaluated

    def test_different_inputs_independent(self, engine: EligibilityEngine):
        """Different inputs should produce independent results."""
        verdict_high = make_verdict(confidence=Decimal("0.85"))
        verdict_low = make_verdict(confidence=Decimal("0.20"))

        result_high = engine.evaluate(make_input(verdict_high))
        result_low = engine.evaluate(make_input(verdict_low))

        # Different confidence should produce different decisions
        assert result_high.decision == EligibilityDecision.MAY
        assert result_low.decision == EligibilityDecision.MAY_NOT


# ==============================================================================
# ELIG-002: Every Verdict Has a Reason
# ==============================================================================


class TestELIG002ReasonRequired:
    """ELIG-002: Every verdict has a reason (required field)."""

    def test_may_verdict_has_reason(self, engine: EligibilityEngine, high_confidence_verdict: ValidatorVerdict):
        """MAY verdicts must have a reason."""
        verdict = engine.evaluate(make_input(high_confidence_verdict))
        assert verdict.reason is not None
        assert len(verdict.reason) > 0

    def test_may_not_verdict_has_reason(self, engine: EligibilityEngine, low_confidence_verdict: ValidatorVerdict):
        """MAY_NOT verdicts must have a reason."""
        verdict = engine.evaluate(make_input(low_confidence_verdict))
        assert verdict.reason is not None
        assert len(verdict.reason) > 0

    def test_reason_references_failing_rule(self, engine: EligibilityEngine):
        """Reason should reference the specific failing rule."""
        verdict = make_verdict(confidence=Decimal("0.10"))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule is not None
        # Reason should contain meaningful text
        assert "confidence" in result.reason.lower() or "threshold" in result.reason.lower()

    def test_all_rule_results_have_reasons(self, engine: EligibilityEngine, high_confidence_verdict: ValidatorVerdict):
        """All rule results in audit trail should have reasons."""
        verdict = engine.evaluate(make_input(high_confidence_verdict))

        for rule_result in verdict.rule_results:
            assert rule_result.rule_id is not None
            assert rule_result.rule_name is not None
            # Only failing rules must have reasons
            if not rule_result.passed:
                assert len(rule_result.reason) > 0


# ==============================================================================
# ELIG-003: MAY_NOT Rules Take Precedence
# ==============================================================================


class TestELIG003MayNotPrecedence:
    """ELIG-003: MAY_NOT rules take precedence (evaluation order)."""

    def test_may_not_rules_evaluated_first(self):
        """MAY_NOT rules (E-100 series) should be evaluated before MAY rules."""
        # Create engine with degraded health (E-104 is MAY_NOT)
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
            health_lookup=DefaultSystemHealthLookup(status=SystemHealthStatus.DEGRADED),
        )

        # Even with perfect input, should fail on E-104 first
        verdict = make_verdict(confidence=Decimal("0.95"))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-104"

    def test_may_not_stops_evaluation(self):
        """When MAY_NOT rule fails, evaluation should stop immediately."""
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
            health_lookup=DefaultSystemHealthLookup(status=SystemHealthStatus.DEGRADED),
        )

        verdict = make_verdict(confidence=Decimal("0.95"))
        result = engine.evaluate(make_input(verdict))

        # Should only have evaluated up to E-104
        assert result.first_failing_rule == "E-104"
        # E-001 (MAY rule) should NOT have been evaluated
        evaluated_ids = [r.rule_id for r in result.rule_results]
        assert "E-001" not in evaluated_ids

    def test_multiple_may_not_failures_first_wins(self):
        """If multiple MAY_NOT rules would fail, first one wins."""
        # Health degraded AND low confidence (both MAY_NOT)
        engine = EligibilityEngine(
            health_lookup=DefaultSystemHealthLookup(status=SystemHealthStatus.DEGRADED),
        )

        verdict = make_verdict(confidence=Decimal("0.10"))  # Also triggers E-100
        result = engine.evaluate(make_input(verdict))

        # E-104 is checked first, so it should be the first failing rule
        assert result.first_failing_rule == "E-104"


# ==============================================================================
# ELIG-004: Health Degradation Blocks All
# ==============================================================================


class TestELIG004HealthBlocks:
    """ELIG-004: Health degradation blocks all (E-104 priority)."""

    def test_degraded_health_blocks(self):
        """Degraded system health should block all contracts."""
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
            health_lookup=DefaultSystemHealthLookup(status=SystemHealthStatus.DEGRADED),
        )

        verdict = make_verdict(confidence=Decimal("0.99"))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-104"
        assert "health" in result.reason.lower()

    def test_critical_health_blocks(self):
        """Critical system health should block all contracts."""
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
            health_lookup=DefaultSystemHealthLookup(status=SystemHealthStatus.CRITICAL),
        )

        verdict = make_verdict(confidence=Decimal("0.99"))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-104"

    def test_healthy_allows_contracts(self):
        """Healthy system should allow contracts."""
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
            health_lookup=DefaultSystemHealthLookup(status=SystemHealthStatus.HEALTHY),
        )

        verdict = make_verdict(confidence=Decimal("0.85"))
        result = engine.evaluate(make_input(verdict))

        # Should pass E-104 (may fail other rules)
        passed_e104 = next((r for r in result.rule_results if r.rule_id == "E-104"), None)
        assert passed_e104 is not None
        assert passed_e104.passed

    def test_health_check_is_first(self):
        """Health check (E-104) should be the first rule evaluated."""
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
            health_lookup=DefaultSystemHealthLookup(status=SystemHealthStatus.HEALTHY),
        )

        verdict = make_verdict(confidence=Decimal("0.85"))
        result = engine.evaluate(make_input(verdict))

        # First rule result should be E-104
        assert result.rule_results[0].rule_id == "E-104"


# ==============================================================================
# ELIG-005: Frozen Capabilities Are Inviolable
# ==============================================================================


class TestELIG005FrozenInviolable:
    """ELIG-005: Frozen capabilities are inviolable (E-102 check)."""

    def test_frozen_capability_blocks(self):
        """Proposals targeting frozen capabilities should be blocked."""
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(
                registry=frozenset(["email_send", "frozen_cap"]),
                frozen=frozenset(["frozen_cap"]),
            ),
        )

        verdict = make_verdict(confidence=Decimal("0.85"), capabilities=("frozen_cap",))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-102"
        assert "frozen" in result.reason.lower()

    def test_multiple_caps_one_frozen_blocks(self):
        """Even one frozen capability among many should block."""
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(
                registry=frozenset(["email_send", "frozen_cap", "data_export"]),
                frozen=frozenset(["frozen_cap"]),
            ),
        )

        verdict = make_verdict(
            confidence=Decimal("0.85"),
            capabilities=("email_send", "frozen_cap", "data_export"),
        )
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-102"

    def test_non_frozen_allowed(self):
        """Non-frozen capabilities should be allowed."""
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(
                registry=frozenset(["email_send", "frozen_cap"]),
                frozen=frozenset(["frozen_cap"]),
            ),
        )

        verdict = make_verdict(confidence=Decimal("0.85"), capabilities=("email_send",))
        result = engine.evaluate(make_input(verdict))

        # Should pass E-102
        e102_result = next((r for r in result.rule_results if r.rule_id == "E-102"), None)
        assert e102_result is not None
        assert e102_result.passed


# ==============================================================================
# E-100: Below Minimum Confidence
# ==============================================================================


class TestE100BelowMinimumConfidence:
    """E-100: Below Minimum Confidence."""

    def test_below_minimum_rejects(self, engine: EligibilityEngine):
        """Confidence below minimum threshold should reject."""
        verdict = make_verdict(confidence=Decimal("0.15"))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-100"

    def test_at_minimum_allows(self, engine: EligibilityEngine):
        """Confidence at minimum threshold should allow past E-100."""
        verdict = make_verdict(confidence=Decimal("0.30"))
        result = engine.evaluate(make_input(verdict))

        # Should pass E-100
        e100_result = next((r for r in result.rule_results if r.rule_id == "E-100"), None)
        assert e100_result is not None
        assert e100_result.passed

    def test_custom_minimum_threshold(self):
        """Custom minimum threshold should be respected."""
        config = EligibilityConfig(minimum_confidence=Decimal("0.50"))
        engine = EligibilityEngine(
            config=config,
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
        )

        # 0.40 < 0.50 should fail
        verdict = make_verdict(confidence=Decimal("0.40"))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-100"


# ==============================================================================
# E-101: Critical Without Escalation
# ==============================================================================


class TestE101CriticalWithoutEscalation:
    """E-101: Critical Without Escalation."""

    def test_critical_without_escalate_rejects(self, engine: EligibilityEngine):
        """Critical severity without escalate action should reject."""
        verdict = make_verdict(
            severity=Severity.CRITICAL,
            action=RecommendedAction.CREATE_CONTRACT,
            confidence=Decimal("0.85"),
        )
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-101"
        assert "escalat" in result.reason.lower()

    def test_critical_with_escalate_allows(self, engine: EligibilityEngine):
        """Critical severity with escalate action should allow past E-101."""
        verdict = make_verdict(
            issue_type=IssueType.ESCALATION,
            severity=Severity.CRITICAL,
            action=RecommendedAction.ESCALATE,
            confidence=Decimal("0.85"),
        )
        result = engine.evaluate(make_input(verdict))

        # Should pass E-101
        e101_result = next((r for r in result.rule_results if r.rule_id == "E-101"), None)
        assert e101_result is not None
        assert e101_result.passed

    def test_non_critical_allows(self, engine: EligibilityEngine):
        """Non-critical severity should allow past E-101."""
        verdict = make_verdict(
            severity=Severity.MEDIUM,
            action=RecommendedAction.CREATE_CONTRACT,
            confidence=Decimal("0.85"),
        )
        result = engine.evaluate(make_input(verdict))

        # Should pass E-101
        e101_result = next((r for r in result.rule_results if r.rule_id == "E-101"), None)
        assert e101_result is not None
        assert e101_result.passed


# ==============================================================================
# E-001: Validator Confidence Threshold
# ==============================================================================


class TestE001ConfidenceThreshold:
    """E-001: Validator Confidence Threshold."""

    def test_below_threshold_rejects(self, engine: EligibilityEngine):
        """Confidence below threshold should reject."""
        verdict = make_verdict(confidence=Decimal("0.50"))  # Below 0.70
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert "E-001" in result.first_failing_rule or "E-100" in result.first_failing_rule

    def test_above_threshold_allows(self, engine: EligibilityEngine):
        """Confidence above threshold should allow past E-001."""
        verdict = make_verdict(confidence=Decimal("0.80"))
        result = engine.evaluate(make_input(verdict))

        # Should pass E-001
        e001_result = next((r for r in result.rule_results if r.rule_id == "E-001"), None)
        assert e001_result is not None
        assert e001_result.passed

    def test_at_threshold_allows(self, engine: EligibilityEngine):
        """Confidence at threshold should allow past E-001."""
        verdict = make_verdict(confidence=Decimal("0.70"))
        result = engine.evaluate(make_input(verdict))

        # Should pass E-001
        e001_result = next((r for r in result.rule_results if r.rule_id == "E-001"), None)
        assert e001_result is not None
        assert e001_result.passed


# ==============================================================================
# E-002: Known Capability Reference
# ==============================================================================


class TestE002KnownCapability:
    """E-002: Known Capability Reference."""

    def test_unknown_capability_rejects(self, engine: EligibilityEngine):
        """Unknown capabilities should reject."""
        verdict = make_verdict(confidence=Decimal("0.85"), capabilities=("nonexistent_cap",))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-002"
        assert "unknown" in result.reason.lower()

    def test_known_capability_allows(self, engine: EligibilityEngine):
        """Known capabilities should allow past E-002."""
        verdict = make_verdict(confidence=Decimal("0.85"), capabilities=("email_send",))
        result = engine.evaluate(make_input(verdict))

        # Should pass E-002
        e002_result = next((r for r in result.rule_results if r.rule_id == "E-002"), None)
        assert e002_result is not None
        assert e002_result.passed

    def test_system_scope_bypasses_check(self, engine: EligibilityEngine):
        """SYSTEM scope should not be checked against capability registry."""
        verdict = make_verdict(confidence=Decimal("0.85"), capabilities=("SYSTEM", "email_send"))
        result = engine.evaluate(make_input(verdict))

        # SYSTEM should not cause E-002 failure
        e002_result = next((r for r in result.rule_results if r.rule_id == "E-002"), None)
        if e002_result:
            # If we get to E-002, SYSTEM should have been skipped
            assert "SYSTEM" not in e002_result.evidence.get("unknown_capabilities", [])


# ==============================================================================
# E-003: No Blocking Governance Signal
# ==============================================================================


class TestE003NoBlockingSignal:
    """E-003: No Blocking Governance Signal."""

    def test_blocking_signal_rejects(self):
        """Blocking governance signal should reject."""
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
            governance_lookup=DefaultGovernanceSignalLookup(blocking_scopes={"email_send": "MAINTENANCE_WINDOW"}),
        )

        verdict = make_verdict(confidence=Decimal("0.85"), capabilities=("email_send",))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-003"
        assert len(result.blocking_signals) > 0

    def test_system_blocking_rejects(self):
        """System-wide blocking signal should reject."""
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
            governance_lookup=DefaultGovernanceSignalLookup(blocking_scopes={"SYSTEM": "GLOBAL_FREEZE"}),
        )

        verdict = make_verdict(confidence=Decimal("0.85"), capabilities=("email_send",))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-003"

    def test_no_blocking_allows(self, engine: EligibilityEngine):
        """No blocking signals should allow past E-003."""
        verdict = make_verdict(confidence=Decimal("0.85"), capabilities=("email_send",))
        result = engine.evaluate(make_input(verdict))

        # Should pass E-003
        e003_result = next((r for r in result.rule_results if r.rule_id == "E-003"), None)
        assert e003_result is not None
        assert e003_result.passed


# ==============================================================================
# E-004: Actionable Issue Type
# ==============================================================================


class TestE004ActionableType:
    """E-004: Actionable Issue Type."""

    def test_unknown_type_rejects(self, engine: EligibilityEngine):
        """Unknown issue type should reject."""
        verdict = make_verdict(
            issue_type=IssueType.UNKNOWN,
            confidence=Decimal("0.85"),
        )
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-004"
        assert "manual" in result.reason.lower()

    def test_escalation_type_rejects(self, engine: EligibilityEngine):
        """Escalation issue type should reject (requires human)."""
        verdict = make_verdict(
            issue_type=IssueType.ESCALATION,
            action=RecommendedAction.ESCALATE,
            confidence=Decimal("0.85"),
        )
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-004"

    def test_capability_request_allows(self, engine: EligibilityEngine):
        """Capability request should allow past E-004."""
        verdict = make_verdict(
            issue_type=IssueType.CAPABILITY_REQUEST,
            confidence=Decimal("0.85"),
        )
        result = engine.evaluate(make_input(verdict))

        # Should pass E-004
        e004_result = next((r for r in result.rule_results if r.rule_id == "E-004"), None)
        assert e004_result is not None
        assert e004_result.passed

    def test_bug_with_escalate_rejects(self, engine: EligibilityEngine):
        """Bug report with escalate action should reject."""
        verdict = make_verdict(
            issue_type=IssueType.BUG_REPORT,
            action=RecommendedAction.ESCALATE,
            confidence=Decimal("0.85"),
        )
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-004"


# ==============================================================================
# E-005: Source Allowlist
# ==============================================================================


class TestE005SourceAllowlist:
    """E-005: Source Allowlist."""

    def test_disallowed_source_rejects(self, engine: EligibilityEngine):
        """Disallowed source should reject."""
        verdict = make_verdict(confidence=Decimal("0.85"))
        input = make_input(verdict, source="unknown_source")
        result = engine.evaluate(input)

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-005"
        assert "allowlist" in result.reason.lower()

    def test_support_ticket_allows(self, engine: EligibilityEngine):
        """Support ticket source should allow past E-005."""
        verdict = make_verdict(confidence=Decimal("0.85"))
        input = make_input(verdict, source="support_ticket")
        result = engine.evaluate(input)

        # Should pass E-005
        e005_result = next((r for r in result.rule_results if r.rule_id == "E-005"), None)
        assert e005_result is not None
        assert e005_result.passed

    def test_ops_alert_allows(self, engine: EligibilityEngine):
        """Ops alert source should allow past E-005."""
        verdict = make_verdict(confidence=Decimal("0.85"))
        input = make_input(verdict, source="ops_alert")
        result = engine.evaluate(input)

        # Should pass E-005
        e005_result = next((r for r in result.rule_results if r.rule_id == "E-005"), None)
        assert e005_result is not None
        assert e005_result.passed


# ==============================================================================
# E-006: Not Duplicate
# ==============================================================================


class TestE006NotDuplicate:
    """E-006: Not Duplicate."""

    def test_duplicate_rejects(self):
        """Duplicate contract should reject."""
        pending_id = uuid4()
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
            contract_lookup=DefaultContractLookup(pending_contracts={frozenset(["email_send"]): pending_id}),
        )

        verdict = make_verdict(confidence=Decimal("0.85"), capabilities=("email_send",))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-006"
        assert "pending" in result.reason.lower()

    def test_no_duplicate_allows(self, engine: EligibilityEngine):
        """No duplicate should allow past E-006."""
        verdict = make_verdict(confidence=Decimal("0.85"), capabilities=("email_send",))
        result = engine.evaluate(make_input(verdict))

        # Should pass E-006
        e006_result = next((r for r in result.rule_results if r.rule_id == "E-006"), None)
        assert e006_result is not None
        assert e006_result.passed


# ==============================================================================
# E-103: System Scope Without Pre-Approval
# ==============================================================================


class TestE103SystemScopePreApproval:
    """E-103: System Scope Without Founder Pre-Approval."""

    def test_system_scope_without_preapproval_rejects(self, engine: EligibilityEngine):
        """System scope without pre-approval should reject."""
        verdict = make_verdict(
            confidence=Decimal("0.85"),
            capabilities=("SYSTEM", "email_send"),
        )
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-103"
        assert "pre-approval" in result.reason.lower()

    def test_system_scope_with_preapproval_allows(self):
        """System scope with pre-approval should allow past E-103."""
        proposal_id = uuid4()
        engine = EligibilityEngine(
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send", "SYSTEM"])),
            pre_approval_lookup=DefaultPreApprovalLookup(approved_ids={proposal_id}),
        )

        verdict = make_verdict(
            confidence=Decimal("0.85"),
            capabilities=("SYSTEM", "email_send"),
        )
        input = EligibilityInput(
            proposal_id=proposal_id,
            validator_verdict=verdict,
            source="support_ticket",
            affected_capabilities=("SYSTEM", "email_send"),
            received_at=datetime.now(timezone.utc),
        )
        result = engine.evaluate(input)

        # Should pass E-103
        e103_result = next((r for r in result.rule_results if r.rule_id == "E-103"), None)
        assert e103_result is not None
        assert e103_result.passed

    def test_non_system_scope_allows(self, engine: EligibilityEngine):
        """Non-system scope should allow past E-103."""
        verdict = make_verdict(
            confidence=Decimal("0.85"),
            capabilities=("email_send",),
        )
        result = engine.evaluate(make_input(verdict))

        # Should pass E-103
        e103_result = next((r for r in result.rule_results if r.rule_id == "E-103"), None)
        assert e103_result is not None
        assert e103_result.passed


# ==============================================================================
# VERSION AND CONFIGURATION
# ==============================================================================


class TestVersionAndConfig:
    """Test version and configuration handling."""

    def test_verdict_has_version(self, engine: EligibilityEngine, high_confidence_verdict: ValidatorVerdict):
        """Verdicts should include rules version."""
        verdict = engine.evaluate(make_input(high_confidence_verdict))
        assert verdict.rules_version is not None
        assert verdict.rules_version == ELIGIBILITY_ENGINE_VERSION

    def test_custom_config_applied(self):
        """Custom configuration should be applied."""
        config = EligibilityConfig(
            confidence_threshold=Decimal("0.90"),
            minimum_confidence=Decimal("0.40"),
        )
        engine = EligibilityEngine(
            config=config,
            capability_lookup=DefaultCapabilityLookup(registry=frozenset(["email_send"])),
        )

        # 0.85 is above default (0.70) but below custom (0.90)
        verdict = make_verdict(confidence=Decimal("0.85"))
        result = engine.evaluate(make_input(verdict))

        assert result.decision == EligibilityDecision.MAY_NOT
        assert result.first_failing_rule == "E-001"


# ==============================================================================
# FULL PASS INTEGRATION
# ==============================================================================


class TestFullPassIntegration:
    """Integration tests for full pass scenarios."""

    def test_all_rules_pass(self, engine: EligibilityEngine):
        """Perfect input should pass all rules and return MAY."""
        verdict = make_verdict(
            issue_type=IssueType.CAPABILITY_REQUEST,
            severity=Severity.MEDIUM,
            action=RecommendedAction.CREATE_CONTRACT,
            confidence=Decimal("0.85"),
            capabilities=("email_send",),
        )
        input = make_input(verdict, source="support_ticket")
        result = engine.evaluate(input)

        assert result.decision == EligibilityDecision.MAY
        assert result.first_failing_rule is None
        assert result.rules_evaluated == 11  # 5 MAY_NOT + 6 MAY rules
        assert all(r.passed for r in result.rule_results)

    def test_audit_trail_complete(self, engine: EligibilityEngine):
        """Audit trail should be complete for all evaluated rules."""
        verdict = make_verdict(confidence=Decimal("0.85"))
        result = engine.evaluate(make_input(verdict))

        # Should have results for all evaluated rules
        assert len(result.rule_results) > 0
        for rule in result.rule_results:
            assert rule.rule_id is not None
            assert rule.rule_name is not None
            assert rule.evidence is not None
