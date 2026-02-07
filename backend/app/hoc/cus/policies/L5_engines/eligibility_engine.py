# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: eligibility rules (via driver)
#   Writes: none
# Role: Eligibility Engine - pure rules, deterministic gating
# Callers: L3 (adapters), L2 (governance APIs)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-287, ELIGIBILITY_RULES.md, part2-design-v1
#
# ==============================================================================
# GOVERNANCE RULE: ELIGIBILITY-IS-DETERMINISTIC (Non-Negotiable)
# ==============================================================================
#
# This engine produces DETERMINISTIC verdicts based on rules.
#
# Eligibility properties:
#   - DETERMINISTIC: Same input produces same output (ELIG-001)
#   - BINARY: MAY or MAY_NOT, no "maybe"
#   - AUDITABLE: Every decision has a reason (ELIG-002)
#   - PURE: No side effects, no writes
#
# The Eligibility Engine:
#   - MAY: Read validator verdict, query lookups (read-only)
#   - MUST NOT: Create contracts, modify state, skip rules
#
# Enforcement:
#   - No writes to database
#   - Rules evaluated in specified order
#   - First failing rule terminates evaluation
#
# Reference: ELIGIBILITY_RULES.md (frozen), part2-design-v1
#
# ==============================================================================

"""
Part-2 Eligibility Engine (L4)

Applies eligibility rules to determine if a validated proposal MAY or
MAY_NOT become a System Contract. The engine is pure - it receives data
via lookups, does not fetch externally.

Responsibilities:
1. Evaluate MAY_NOT rules (rejection rules)
2. Evaluate MAY rules (acceptance rules)
3. Produce deterministic verdicts
4. Track rule evaluation for auditing

Invariants (from ELIGIBILITY_RULES.md):
- ELIG-001: Eligibility is deterministic (pure function, no side effects)
- ELIG-002: Every verdict has a reason (required field)
- ELIG-003: MAY_NOT rules take precedence (evaluation order)
- ELIG-004: Health degradation blocks all (E-104 priority)
- ELIG-005: Frozen capabilities are inviolable (E-102 check)

Reference: PIN-289, ELIGIBILITY_RULES.md, part2-design-v1
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Optional, Protocol
from uuid import UUID

# PIN-520: Import validator types as schema-only types (avoid cross-domain L5 engine imports)
from app.hoc.cus.account.L5_schemas.crm_validator_types import (
    IssueType,
    RecommendedAction,
    Severity,
    ValidatorVerdict,
)

# Engine version (semantic versioning)
# Major: Breaking changes to verdict schema or rule semantics
# Minor: New rules added
# Patch: Bug fixes, threshold tuning
ELIGIBILITY_ENGINE_VERSION = "1.0.0"


# ==============================================================================
# ELIGIBILITY DECISION ENUM
# ==============================================================================


class EligibilityDecision(str, Enum):
    """
    Binary eligibility decision.

    Reference: ELIGIBILITY_RULES.md
    """

    MAY = "MAY"  # Proposal may become a contract
    MAY_NOT = "MAY_NOT"  # Proposal may not become a contract


# ==============================================================================
# SYSTEM HEALTH STATUS
# ==============================================================================


class SystemHealthStatus(str, Enum):
    """System health status for E-104 rule."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


# ==============================================================================
# ELIGIBILITY CONFIGURATION
# ==============================================================================


@dataclass(frozen=True)
class EligibilityConfig:
    """
    Eligibility engine configuration.

    Reference: ELIGIBILITY_RULES.md Configuration
    """

    confidence_threshold: Decimal = Decimal("0.70")  # E-001
    minimum_confidence: Decimal = Decimal("0.30")  # E-100
    allowed_sources: tuple[str, ...] = (  # E-005
        "crm_feedback",
        "support_ticket",
        "ops_alert",
    )
    actionable_types: tuple[IssueType, ...] = (  # E-004
        IssueType.CAPABILITY_REQUEST,
        IssueType.CONFIGURATION_CHANGE,
        IssueType.BUG_REPORT,
    )
    duplicate_window_hours: int = 24  # E-006
    rules_version: str = ELIGIBILITY_ENGINE_VERSION


# Default configuration
DEFAULT_ELIGIBILITY_CONFIG = EligibilityConfig()


# ==============================================================================
# LOOKUP PROTOCOLS
# ==============================================================================


class CapabilityLookup(Protocol):
    """Protocol for capability registry lookups."""

    def exists(self, capability_name: str) -> bool:
        """Check if capability exists in registry."""
        ...

    def is_frozen(self, capability_name: str) -> bool:
        """Check if capability is frozen."""
        ...


class GovernanceSignalLookup(Protocol):
    """Protocol for governance signal lookups."""

    def has_blocking_signal(self, scope: str) -> tuple[bool, Optional[str]]:
        """
        Check if scope has a blocking governance signal.

        Returns:
            Tuple of (has_blocking, signal_type) where signal_type is
            the type of blocking signal if any.
        """
        ...


class SystemHealthLookup(Protocol):
    """Protocol for system health lookups."""

    def get_status(self) -> SystemHealthStatus:
        """Get current system health status."""
        ...


class ContractLookup(Protocol):
    """Protocol for contract lookups."""

    def has_similar_pending(
        self,
        capabilities: tuple[str, ...],
        window_hours: int,
    ) -> tuple[bool, Optional[UUID]]:
        """
        Check for similar pending contracts.

        Returns:
            Tuple of (has_similar, contract_id) where contract_id is
            the ID of the similar contract if any.
        """
        ...


class PreApprovalLookup(Protocol):
    """Protocol for pre-approval lookups."""

    def has_system_pre_approval(self, proposal_id: UUID) -> bool:
        """Check if proposal has system-wide pre-approval."""
        ...


# ==============================================================================
# DEFAULT LOOKUPS (For Testing / Standalone Mode)
# ==============================================================================


class DefaultCapabilityLookup:
    """
    Default capability lookup using provided registry.

    For production, inject a database-backed lookup.
    """

    def __init__(
        self,
        registry: Optional[frozenset[str]] = None,
        frozen: Optional[frozenset[str]] = None,
    ):
        self._registry = registry or frozenset()
        self._frozen = frozen or frozenset()

    def exists(self, capability_name: str) -> bool:
        return capability_name in self._registry

    def is_frozen(self, capability_name: str) -> bool:
        return capability_name in self._frozen


class DefaultGovernanceSignalLookup:
    """
    Default governance signal lookup with no blocking signals.

    For production, inject a database-backed lookup.
    """

    def __init__(self, blocking_scopes: Optional[dict[str, str]] = None):
        self._blocking = blocking_scopes or {}

    def has_blocking_signal(self, scope: str) -> tuple[bool, Optional[str]]:
        if scope in self._blocking:
            return True, self._blocking[scope]
        return False, None


class DefaultSystemHealthLookup:
    """
    Default system health lookup returning HEALTHY.

    For production, inject a real health service lookup.
    """

    def __init__(self, status: SystemHealthStatus = SystemHealthStatus.HEALTHY):
        self._status = status

    def get_status(self) -> SystemHealthStatus:
        return self._status


class DefaultContractLookup:
    """
    Default contract lookup with no pending contracts.

    For production, inject a database-backed lookup.
    """

    def __init__(
        self,
        pending_contracts: Optional[dict[frozenset[str], UUID]] = None,
    ):
        self._pending = pending_contracts or {}

    def has_similar_pending(
        self,
        capabilities: tuple[str, ...],
        window_hours: int,
    ) -> tuple[bool, Optional[UUID]]:
        cap_set = frozenset(capabilities)
        for pending_caps, contract_id in self._pending.items():
            if cap_set & pending_caps:  # Any overlap
                return True, contract_id
        return False, None


class DefaultPreApprovalLookup:
    """
    Default pre-approval lookup with no pre-approvals.

    For production, inject a database-backed lookup.
    """

    def __init__(self, approved_ids: Optional[set[UUID]] = None):
        self._approved = approved_ids or set()

    def has_system_pre_approval(self, proposal_id: UUID) -> bool:
        return proposal_id in self._approved


# ==============================================================================
# ELIGIBILITY INPUT
# ==============================================================================


@dataclass(frozen=True)
class EligibilityInput:
    """
    Input to the eligibility engine.

    Reference: ELIGIBILITY_RULES.md
    """

    proposal_id: UUID
    validator_verdict: ValidatorVerdict
    source: str  # Original issue source
    affected_capabilities: tuple[str, ...]
    received_at: datetime
    tenant_id: Optional[UUID] = None


# ==============================================================================
# RULE RESULT
# ==============================================================================


@dataclass(frozen=True)
class RuleResult:
    """Result of evaluating a single rule."""

    rule_id: str
    rule_name: str
    passed: bool
    reason: str
    evidence: dict[str, Any]


# ==============================================================================
# ELIGIBILITY VERDICT
# ==============================================================================


@dataclass(frozen=True)
class EligibilityVerdict:
    """
    Output from the eligibility engine.

    Reference: ELIGIBILITY_RULES.md Eligibility Verdict Schema

    Invariant ELIG-002: Every verdict has a reason (required field)
    """

    decision: EligibilityDecision
    reason: str  # ELIG-002: Required
    rules_evaluated: int
    first_failing_rule: Optional[str]
    blocking_signals: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    evaluated_at: datetime
    rules_version: str
    rule_results: tuple[RuleResult, ...]  # Full audit trail


# ==============================================================================
# ELIGIBILITY ENGINE
# ==============================================================================


class EligibilityEngine:
    """
    Part-2 Eligibility Engine (L4)

    Evaluates eligibility rules to determine if a proposal MAY or MAY_NOT
    become a System Contract.

    Properties:
    - DETERMINISTIC: Same input produces same output (ELIG-001)
    - BINARY: MAY or MAY_NOT, no "maybe"
    - AUDITABLE: Every decision has a reason (ELIG-002)
    - PURE: No side effects, no writes

    Rule Evaluation Order:
    1. MAY_NOT rules (E-100 series) evaluated first
    2. If any MAY_NOT triggers → immediate MAY_NOT verdict
    3. MAY rules (E-001 series) evaluated in order
    4. If all MAY rules pass → MAY verdict
    5. If any MAY rule fails → MAY_NOT verdict

    Reference: ELIGIBILITY_RULES.md, part2-design-v1
    """

    def __init__(
        self,
        config: Optional[EligibilityConfig] = None,
        capability_lookup: Optional[CapabilityLookup] = None,
        governance_lookup: Optional[GovernanceSignalLookup] = None,
        health_lookup: Optional[SystemHealthLookup] = None,
        contract_lookup: Optional[ContractLookup] = None,
        pre_approval_lookup: Optional[PreApprovalLookup] = None,
    ):
        """
        Initialize eligibility engine with lookups.

        Args:
            config: Engine configuration (uses defaults if None)
            capability_lookup: Capability registry lookup
            governance_lookup: Governance signal lookup
            health_lookup: System health lookup
            contract_lookup: Contract lookup for duplicates
            pre_approval_lookup: Pre-approval lookup for system changes
        """
        self._config = config or DEFAULT_ELIGIBILITY_CONFIG
        self._capability = capability_lookup or DefaultCapabilityLookup()
        self._governance = governance_lookup or DefaultGovernanceSignalLookup()
        self._health = health_lookup or DefaultSystemHealthLookup()
        self._contracts = contract_lookup or DefaultContractLookup()
        self._pre_approval = pre_approval_lookup or DefaultPreApprovalLookup()

    def evaluate(self, input: EligibilityInput) -> EligibilityVerdict:
        """
        Evaluate eligibility for a proposal.

        This is the main entry point. It:
        1. Evaluates MAY_NOT rules (rejection rules)
        2. If any MAY_NOT triggers, returns MAY_NOT immediately
        3. Evaluates MAY rules (acceptance rules)
        4. If all MAY rules pass, returns MAY
        5. If any MAY rule fails, returns MAY_NOT

        Returns:
            EligibilityVerdict with decision and audit trail

        Invariant ELIG-003: MAY_NOT rules take precedence
        """
        results: list[RuleResult] = []
        blocking_signals: list[str] = []
        missing_prerequisites: list[str] = []

        # Phase 1: Evaluate MAY_NOT rules (E-100 series)
        # ELIG-003: These take precedence
        may_not_rules = [
            self._evaluate_e104_health_degraded,  # ELIG-004: Evaluated first
            self._evaluate_e100_below_minimum_confidence,
            self._evaluate_e101_critical_without_escalation,
            self._evaluate_e102_frozen_capability,
            self._evaluate_e103_system_scope_without_preapproval,
        ]

        for rule_fn in may_not_rules:
            result = rule_fn(input)
            results.append(result)

            if not result.passed:
                # MAY_NOT rule triggered - immediate rejection
                if "blocking_signal" in result.evidence:
                    blocking_signals.append(result.evidence["blocking_signal"])
                if "missing_prerequisite" in result.evidence:
                    missing_prerequisites.append(result.evidence["missing_prerequisite"])

                return self._create_verdict(
                    decision=EligibilityDecision.MAY_NOT,
                    reason=result.reason,
                    results=results,
                    first_failing=result.rule_id,
                    blocking_signals=blocking_signals,
                    missing_prerequisites=missing_prerequisites,
                )

        # Phase 2: Evaluate MAY rules (E-001 series)
        may_rules = [
            self._evaluate_e001_confidence_threshold,
            self._evaluate_e002_known_capability,
            self._evaluate_e003_no_blocking_signal,
            self._evaluate_e004_actionable_type,
            self._evaluate_e005_source_allowlist,
            self._evaluate_e006_not_duplicate,
        ]

        for rule_fn in may_rules:
            result = rule_fn(input)
            results.append(result)

            if not result.passed:
                # MAY rule failed - rejection
                if "blocking_signal" in result.evidence:
                    blocking_signals.append(result.evidence["blocking_signal"])
                if "missing_prerequisite" in result.evidence:
                    missing_prerequisites.append(result.evidence["missing_prerequisite"])

                return self._create_verdict(
                    decision=EligibilityDecision.MAY_NOT,
                    reason=result.reason,
                    results=results,
                    first_failing=result.rule_id,
                    blocking_signals=blocking_signals,
                    missing_prerequisites=missing_prerequisites,
                )

        # All rules passed
        return self._create_verdict(
            decision=EligibilityDecision.MAY,
            reason="All eligibility rules passed",
            results=results,
            first_failing=None,
            blocking_signals=blocking_signals,
            missing_prerequisites=missing_prerequisites,
        )

    # ==========================================================================
    # MAY_NOT RULES (E-100 SERIES)
    # ==========================================================================

    def _evaluate_e104_health_degraded(self, input: EligibilityInput) -> RuleResult:
        """
        E-104: Health Degraded

        ELIG-004: Health degradation blocks all new contracts.

        Reference: ELIGIBILITY_RULES.md Rule E-104
        """
        status = self._health.get_status()
        passed = status == SystemHealthStatus.HEALTHY

        return RuleResult(
            rule_id="E-104",
            rule_name="Health Degraded",
            passed=passed,
            reason="" if passed else "System health degraded - no new contracts",
            evidence={
                "health_status": status.value,
                "blocking_signal": "SYSTEM_HEALTH_DEGRADED" if not passed else "",
            },
        )

    def _evaluate_e100_below_minimum_confidence(self, input: EligibilityInput) -> RuleResult:
        """
        E-100: Below Minimum Confidence

        Reference: ELIGIBILITY_RULES.md Rule E-100
        """
        confidence = input.validator_verdict.confidence_score
        minimum = self._config.minimum_confidence
        passed = confidence >= minimum

        return RuleResult(
            rule_id="E-100",
            rule_name="Below Minimum Confidence",
            passed=passed,
            reason=""
            if passed
            else f"Confidence below minimum threshold ({float(confidence):.2f} < {float(minimum):.2f})",
            evidence={
                "confidence_score": float(confidence),
                "minimum_threshold": float(minimum),
            },
        )

    def _evaluate_e101_critical_without_escalation(self, input: EligibilityInput) -> RuleResult:
        """
        E-101: Critical Without Escalation

        Reference: ELIGIBILITY_RULES.md Rule E-101
        """
        verdict = input.validator_verdict
        is_critical = verdict.severity == Severity.CRITICAL
        is_escalated = verdict.recommended_action == RecommendedAction.ESCALATE

        # Passes if: not critical, OR critical with escalation
        passed = not is_critical or is_escalated

        return RuleResult(
            rule_id="E-101",
            rule_name="Critical Without Escalation",
            passed=passed,
            reason="" if passed else "Critical issues must be escalated",
            evidence={
                "severity": verdict.severity.value,
                "recommended_action": verdict.recommended_action.value,
                "is_critical": is_critical,
                "is_escalated": is_escalated,
            },
        )

    def _evaluate_e102_frozen_capability(self, input: EligibilityInput) -> RuleResult:
        """
        E-102: Frozen Capability Target

        ELIG-005: Frozen capabilities are inviolable.

        Reference: ELIGIBILITY_RULES.md Rule E-102
        """
        frozen_caps = []
        for cap in input.affected_capabilities:
            if self._capability.is_frozen(cap):
                frozen_caps.append(cap)

        passed = len(frozen_caps) == 0

        return RuleResult(
            rule_id="E-102",
            rule_name="Frozen Capability Target",
            passed=passed,
            reason="" if passed else f"Cannot modify frozen capability: {', '.join(frozen_caps)}",
            evidence={
                "affected_capabilities": list(input.affected_capabilities),
                "frozen_capabilities": frozen_caps,
            },
        )

    def _evaluate_e103_system_scope_without_preapproval(self, input: EligibilityInput) -> RuleResult:
        """
        E-103: System Scope Without Founder Pre-Approval

        Reference: ELIGIBILITY_RULES.md Rule E-103
        """
        is_system_scope = "SYSTEM" in input.affected_capabilities
        has_preapproval = self._pre_approval.has_system_pre_approval(input.proposal_id)

        # Passes if: not system scope, OR has pre-approval
        passed = not is_system_scope or has_preapproval

        return RuleResult(
            rule_id="E-103",
            rule_name="System Scope Without Founder Pre-Approval",
            passed=passed,
            reason="" if passed else "System-wide changes require pre-approval",
            evidence={
                "is_system_scope": is_system_scope,
                "has_preapproval": has_preapproval,
                "missing_prerequisite": "FOUNDER_PRE_APPROVAL" if not passed else "",
            },
        )

    # ==========================================================================
    # MAY RULES (E-001 SERIES)
    # ==========================================================================

    def _evaluate_e001_confidence_threshold(self, input: EligibilityInput) -> RuleResult:
        """
        E-001: Validator Confidence Threshold

        Reference: ELIGIBILITY_RULES.md Rule E-001
        """
        confidence = input.validator_verdict.confidence_score
        threshold = self._config.confidence_threshold
        passed = confidence >= threshold

        return RuleResult(
            rule_id="E-001",
            rule_name="Validator Confidence Threshold",
            passed=passed,
            reason="" if passed else f"Validator confidence too low ({float(confidence):.2f} < {float(threshold):.2f})",
            evidence={
                "confidence_score": float(confidence),
                "threshold": float(threshold),
            },
        )

    def _evaluate_e002_known_capability(self, input: EligibilityInput) -> RuleResult:
        """
        E-002: Known Capability Reference

        Reference: ELIGIBILITY_RULES.md Rule E-002
        """
        unknown_caps = []
        for cap in input.affected_capabilities:
            # Skip SYSTEM as it's a special scope, not a capability
            if cap == "SYSTEM":
                continue
            if not self._capability.exists(cap):
                unknown_caps.append(cap)

        passed = len(unknown_caps) == 0

        return RuleResult(
            rule_id="E-002",
            rule_name="Known Capability Reference",
            passed=passed,
            reason="" if passed else f"Unknown capability referenced: {', '.join(unknown_caps)}",
            evidence={
                "affected_capabilities": list(input.affected_capabilities),
                "unknown_capabilities": unknown_caps,
            },
        )

    def _evaluate_e003_no_blocking_signal(self, input: EligibilityInput) -> RuleResult:
        """
        E-003: No Blocking Governance Signal

        Reference: ELIGIBILITY_RULES.md Rule E-003
        """
        blocking_signals = []

        # Check SYSTEM scope
        has_block, signal_type = self._governance.has_blocking_signal("SYSTEM")
        if has_block and signal_type:
            blocking_signals.append(f"SYSTEM:{signal_type}")

        # Check each affected capability
        for cap in input.affected_capabilities:
            has_block, signal_type = self._governance.has_blocking_signal(cap)
            if has_block and signal_type:
                blocking_signals.append(f"{cap}:{signal_type}")

        passed = len(blocking_signals) == 0

        return RuleResult(
            rule_id="E-003",
            rule_name="No Blocking Governance Signal",
            passed=passed,
            reason="" if passed else f"Blocked by governance signal: {', '.join(blocking_signals)}",
            evidence={
                "blocking_signals": blocking_signals,
                "blocking_signal": blocking_signals[0] if blocking_signals else "",
            },
        )

    def _evaluate_e004_actionable_type(self, input: EligibilityInput) -> RuleResult:
        """
        E-004: Actionable Issue Type

        Reference: ELIGIBILITY_RULES.md Rule E-004
        """
        issue_type = input.validator_verdict.issue_type
        action = input.validator_verdict.recommended_action

        # Bug reports with escalate action are not actionable
        if issue_type == IssueType.BUG_REPORT and action == RecommendedAction.ESCALATE:
            return RuleResult(
                rule_id="E-004",
                rule_name="Actionable Issue Type",
                passed=False,
                reason=f"Issue type {issue_type.value} with escalate action requires manual handling",
                evidence={
                    "issue_type": issue_type.value,
                    "recommended_action": action.value,
                    "actionable_types": [t.value for t in self._config.actionable_types],
                },
            )

        # Check if type is actionable
        passed = issue_type in self._config.actionable_types

        return RuleResult(
            rule_id="E-004",
            rule_name="Actionable Issue Type",
            passed=passed,
            reason="" if passed else f"Issue type {issue_type.value} requires manual handling",
            evidence={
                "issue_type": issue_type.value,
                "actionable_types": [t.value for t in self._config.actionable_types],
            },
        )

    def _evaluate_e005_source_allowlist(self, input: EligibilityInput) -> RuleResult:
        """
        E-005: Source Allowlist

        Reference: ELIGIBILITY_RULES.md Rule E-005
        """
        source = input.source
        passed = source in self._config.allowed_sources

        return RuleResult(
            rule_id="E-005",
            rule_name="Source Allowlist",
            passed=passed,
            reason="" if passed else f"Source {source} not in allowlist",
            evidence={
                "source": source,
                "allowed_sources": list(self._config.allowed_sources),
            },
        )

    def _evaluate_e006_not_duplicate(self, input: EligibilityInput) -> RuleResult:
        """
        E-006: Not Duplicate

        Reference: ELIGIBILITY_RULES.md Rule E-006
        """
        has_similar, contract_id = self._contracts.has_similar_pending(
            input.affected_capabilities,
            self._config.duplicate_window_hours,
        )

        passed = not has_similar

        return RuleResult(
            rule_id="E-006",
            rule_name="Not Duplicate",
            passed=passed,
            reason="" if passed else f"Similar contract already pending: {contract_id}",
            evidence={
                "has_similar_pending": has_similar,
                "similar_contract_id": str(contract_id) if contract_id else None,
                "duplicate_window_hours": self._config.duplicate_window_hours,
            },
        )

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def _create_verdict(
        self,
        decision: EligibilityDecision,
        reason: str,
        results: list[RuleResult],
        first_failing: Optional[str],
        blocking_signals: list[str],
        missing_prerequisites: list[str],
    ) -> EligibilityVerdict:
        """Create eligibility verdict from evaluation results."""
        return EligibilityVerdict(
            decision=decision,
            reason=reason,  # ELIG-002: Required
            rules_evaluated=len(results),
            first_failing_rule=first_failing,
            blocking_signals=tuple(blocking_signals),
            missing_prerequisites=tuple(missing_prerequisites),
            evaluated_at=datetime.now(timezone.utc),
            rules_version=self._config.rules_version,
            rule_results=tuple(results),
        )
