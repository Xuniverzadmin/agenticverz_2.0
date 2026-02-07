# Layer: L5 — Domain Engine
# NOTE: Relocated from L5_support/CRM/engines/ → L5_engines/ (2026-01-31) per standard directory topology. Duplicate validator_engine.py deleted (header-only diff).
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: issues (via driver)
#   Writes: verdicts (via driver)
# Role: Issue Validator - pure analysis, advisory verdicts (pure business logic)
# Callers: L3 (adapters), L4 (orchestrators)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-287, VALIDATOR_LOGIC.md, part2-design-v1
# NOTE: Renamed validator_service.py → validator_engine.py (2026-01-24) - BANNED_NAMING fix
#       Reclassified L4→L5 per HOC Topology V1
#
# ==============================================================================
# GOVERNANCE RULE: VALIDATOR-IS-ADVISORY (Non-Negotiable)
# ==============================================================================
#
# This service produces ADVISORY verdicts, not DECISIONS.
#
# Validator properties:
#   - ADVISORY: Produces recommendations, not decisions
#   - STATELESS: No side effects, no writes
#   - DETERMINISTIC: Same input produces same output
#   - VERSIONED: Every verdict includes validator version
#
# The Validator:
#   - MAY: Read issue payload, query capability registry (read-only)
#   - MUST NOT: Create contracts, modify state, make eligibility decisions
#
# Enforcement:
#   - No writes to database
#   - No external calls that mutate state
#   - Verdicts feed Eligibility Engine, not contract creation
#
# Reference: VALIDATOR_LOGIC.md (frozen), part2-design-v1
#
# ==============================================================================

"""
Part-2 Validator Service (L4)

Analyzes incoming CRM issues and produces structured verdicts for the
eligibility engine. The Validator is advisory only - it recommends but
does not decide.

Responsibilities:
1. Classify issue type (capability_request, bug_report, etc.)
2. Determine severity (critical, high, medium, low)
3. Extract affected capabilities
4. Recommend action (create_contract, defer, reject, escalate)
5. Calculate confidence score

Invariants (from VALIDATOR_LOGIC.md):
- VAL-001: Validator is stateless (no writes)
- VAL-002: Verdicts include version (required field)
- VAL-003: Confidence in [0,1] (clamping)
- VAL-004: Unknown type defers (action logic)
- VAL-005: Escalation always escalates (action logic)

Reference: PIN-287, VALIDATOR_LOGIC.md, part2-design-v1
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from uuid import UUID

# Validator version (semantic versioning)
# Major: Breaking changes to verdict schema
# Minor: New classification rules
# Patch: Bug fixes, confidence tuning
VALIDATOR_VERSION = "1.0.0"


from app.hoc.cus.account.L5_schemas.crm_validator_types import (
    IssueSource,
    IssueType,
    RecommendedAction,
    Severity,
    ValidatorError,
    ValidatorErrorType,
    ValidatorInput,
    ValidatorVerdict,
)


# ==============================================================================
# CLASSIFICATION KEYWORDS
# ==============================================================================

# Keywords for issue type classification
CAPABILITY_REQUEST_KEYWORDS = frozenset(
    [
        "enable",
        "disable",
        "turn on",
        "turn off",
        "activate",
        "deactivate",
        "feature",
        "capability",
        "access",
        "permission",
    ]
)

BUG_REPORT_KEYWORDS = frozenset(
    [
        "bug",
        "broken",
        "not working",
        "error",
        "fails",
        "failure",
        "crash",
        "issue",
        "problem",
        "defect",
    ]
)

CONFIGURATION_KEYWORDS = frozenset(
    [
        "configure",
        "setting",
        "parameter",
        "threshold",
        "limit",
        "config",
        "change",
        "update",
        "modify",
    ]
)

ESCALATION_KEYWORDS = frozenset(
    [
        "urgent",
        "emergency",
        "critical",
        "security",
        "breach",
        "immediate",
        "asap",
        "priority",
        "escalate",
    ]
)

# Severity indicator keywords
CRITICAL_INDICATORS = frozenset(
    [
        "multiple tenants",
        "security",
        "data integrity",
        "production outage",
        "all users",
        "system-wide",
        "breach",
    ]
)

HIGH_INDICATORS = frozenset(
    [
        "severely impacted",
        "completely broken",
        "business-critical",
        "blocked",
        "cannot use",
    ]
)

LOW_INDICATORS = frozenset(
    [
        "cosmetic",
        "enhancement",
        "nice to have",
        "minor",
        "documentation",
        "typo",
    ]
)


# ==============================================================================
# VALIDATOR SERVICE
# ==============================================================================


class ValidatorService:
    """
    Part-2 Validator Service (L4)

    Analyzes CRM issues and produces advisory verdicts.

    Properties:
    - ADVISORY: Produces recommendations, not decisions
    - STATELESS: No side effects (VAL-001)
    - DETERMINISTIC: Same input produces same output
    - VERSIONED: Every verdict includes version (VAL-002)

    Reference: VALIDATOR_LOGIC.md, part2-design-v1
    """

    def __init__(self, capability_registry: Optional[list[str]] = None):
        """
        Initialize validator with optional capability registry.

        Args:
            capability_registry: List of known capability names for matching.
                                If None, capability extraction returns empty.
        """
        self._capability_registry = frozenset(capability_registry or [])

    def validate(self, input: ValidatorInput) -> ValidatorVerdict:
        """
        Validate an issue and produce a verdict.

        This is the main entry point. It:
        1. Classifies issue type
        2. Determines severity
        3. Extracts affected capabilities
        4. Determines recommended action
        5. Calculates confidence

        Returns:
            ValidatorVerdict with classification and recommendation

        Raises:
            Nothing - errors return fallback verdict
        """
        try:
            return self._do_validate(input)
        except Exception as e:
            return self._create_fallback_verdict(
                ValidatorErrorType.UNKNOWN,
                str(e),
            )

    def _do_validate(self, input: ValidatorInput) -> ValidatorVerdict:
        """Internal validation logic."""
        # Extract text for analysis
        text = self._extract_text(input.raw_payload)
        text_lower = text.lower()

        # Classify issue type with confidence
        issue_type, type_confidence, type_evidence = self._classify_issue_type(text_lower)

        # Determine severity with confidence
        severity, severity_confidence = self._classify_severity(text_lower, issue_type)

        # Extract affected capabilities
        capabilities = self._extract_capabilities(text_lower, input.affected_capabilities_hint)

        # Calculate overall confidence
        confidence = self._calculate_confidence(
            input.source,
            type_confidence,
            capabilities,
        )

        # Determine recommended action
        action = self._determine_action(issue_type, severity, confidence)

        # Build reason
        reason = self._build_reason(issue_type, severity, action, confidence)

        # Build evidence
        evidence = {
            "type_classification": type_evidence,
            "severity_indicators": self._find_severity_indicators(text_lower),
            "capability_matches": list(capabilities),
            "source": input.source,
            "confidence_components": {
                "type_confidence": float(type_confidence),
                "source_weight": self._get_source_weight(input.source),
                "capability_confidence": self._get_capability_confidence(capabilities),
            },
        }

        return ValidatorVerdict(
            issue_type=issue_type,
            severity=severity,
            affected_capabilities=tuple(capabilities),
            recommended_action=action,
            confidence_score=confidence,
            reason=reason,
            evidence=evidence,
            analyzed_at=datetime.now(timezone.utc),
            validator_version=VALIDATOR_VERSION,  # VAL-002
        )

    def _extract_text(self, payload: dict[str, Any]) -> str:
        """Extract searchable text from payload."""
        parts = []

        # Standard fields
        if "subject" in payload:
            parts.append(str(payload["subject"]))
        if "body" in payload:
            parts.append(str(payload["body"]))
        if "description" in payload:
            parts.append(str(payload["description"]))
        if "title" in payload:
            parts.append(str(payload["title"]))

        # Nested payload
        if "payload" in payload and isinstance(payload["payload"], dict):
            nested = payload["payload"]
            if "subject" in nested:
                parts.append(str(nested["subject"]))
            if "body" in nested:
                parts.append(str(nested["body"]))

        return " ".join(parts)

    def _classify_issue_type(self, text: str) -> tuple[IssueType, Decimal, dict[str, Any]]:
        """
        Classify issue type from text.

        Returns:
            Tuple of (issue_type, confidence, evidence)

        Reference: VALIDATOR_LOGIC.md Issue Type Classification
        """
        scores: dict[IssueType, Decimal] = {
            IssueType.CAPABILITY_REQUEST: Decimal("0"),
            IssueType.BUG_REPORT: Decimal("0"),
            IssueType.CONFIGURATION_CHANGE: Decimal("0"),
            IssueType.ESCALATION: Decimal("0"),
        }
        evidence: dict[str, list[str]] = {
            "capability_request_matches": [],
            "bug_report_matches": [],
            "configuration_matches": [],
            "escalation_matches": [],
        }

        # Score each type based on keyword matches
        for keyword in CAPABILITY_REQUEST_KEYWORDS:
            if keyword in text:
                scores[IssueType.CAPABILITY_REQUEST] += Decimal("0.15")
                evidence["capability_request_matches"].append(keyword)

        for keyword in BUG_REPORT_KEYWORDS:
            if keyword in text:
                scores[IssueType.BUG_REPORT] += Decimal("0.15")
                evidence["bug_report_matches"].append(keyword)

        for keyword in CONFIGURATION_KEYWORDS:
            if keyword in text:
                scores[IssueType.CONFIGURATION_CHANGE] += Decimal("0.15")
                evidence["configuration_matches"].append(keyword)

        for keyword in ESCALATION_KEYWORDS:
            if keyword in text:
                scores[IssueType.ESCALATION] += Decimal("0.20")  # Higher weight
                evidence["escalation_matches"].append(keyword)

        # Find highest score
        max_type = max(scores, key=lambda k: scores[k])
        max_score = scores[max_type]

        # VAL-005: Escalation always wins if present (even with lower score)
        # This check comes AFTER finding max but BEFORE the confidence threshold
        # because escalation keywords indicate urgent human attention needed
        if scores[IssueType.ESCALATION] > Decimal("0"):
            max_type = IssueType.ESCALATION
            max_score = scores[IssueType.ESCALATION]
            # Escalation bypasses confidence threshold (VAL-005)
            confidence = min(Decimal("1.0"), max_score)
            return max_type, confidence, evidence

        # If confidence too low, classify as unknown (non-escalation only)
        if max_score < Decimal("0.3"):
            return IssueType.UNKNOWN, max_score, evidence

        # Clamp confidence to [0, 1]
        confidence = min(Decimal("1.0"), max_score)

        return max_type, confidence, evidence

    def _classify_severity(self, text: str, issue_type: IssueType) -> tuple[Severity, Decimal]:
        """
        Classify severity from text and issue type.

        Returns:
            Tuple of (severity, confidence)

        Reference: VALIDATOR_LOGIC.md Severity Classification
        """
        # Check critical indicators (threshold > 0.8)
        critical_matches = sum(1 for ind in CRITICAL_INDICATORS if ind in text)
        if critical_matches > 0:
            confidence = min(Decimal("1.0"), Decimal("0.5") + Decimal("0.2") * critical_matches)
            if confidence > Decimal("0.8"):
                return Severity.CRITICAL, confidence

        # Check high indicators (threshold > 0.6)
        high_matches = sum(1 for ind in HIGH_INDICATORS if ind in text)
        if high_matches > 0:
            confidence = min(Decimal("1.0"), Decimal("0.4") + Decimal("0.15") * high_matches)
            if confidence > Decimal("0.6"):
                return Severity.HIGH, confidence

        # Check low indicators
        low_matches = sum(1 for ind in LOW_INDICATORS if ind in text)
        if low_matches > 0:
            return Severity.LOW, Decimal("0.7")

        # Escalation type implies higher severity
        if issue_type == IssueType.ESCALATION:
            return Severity.HIGH, Decimal("0.8")

        # Default: medium
        return Severity.MEDIUM, Decimal("0.5")

    def _find_severity_indicators(self, text: str) -> dict[str, list[str]]:
        """Find severity indicators in text for evidence."""
        return {
            "critical": [ind for ind in CRITICAL_INDICATORS if ind in text],
            "high": [ind for ind in HIGH_INDICATORS if ind in text],
            "low": [ind for ind in LOW_INDICATORS if ind in text],
        }

    def _extract_capabilities(self, text: str, hints: Optional[list[str]]) -> list[str]:
        """
        Extract affected capabilities from text.

        Reference: VALIDATOR_LOGIC.md Capability Extraction

        Returns:
            List of capability names (deduplicated)
        """
        capabilities = set()

        # Include hints if provided (from CRM event)
        if hints:
            capabilities.update(hints)

        # Exact match against registry
        for cap in self._capability_registry:
            if cap.lower() in text:
                capabilities.add(cap)

        # Fuzzy match (simple word boundary match)
        # Note: Real fuzzy matching would use Levenshtein distance
        for cap in self._capability_registry:
            # Match with word boundaries
            pattern = rf"\b{re.escape(cap.lower())}\b"
            if re.search(pattern, text):
                capabilities.add(cap)

        return sorted(capabilities)

    def _get_source_weight(self, source: str) -> Decimal:
        """
        Get confidence weight for source.

        Reference: VALIDATOR_LOGIC.md Confidence Score Calculation
        """
        weights = {
            IssueSource.OPS_ALERT.value: Decimal("0.2"),
            IssueSource.SUPPORT_TICKET.value: Decimal("0.1"),
            IssueSource.CRM_FEEDBACK.value: Decimal("0.05"),
            IssueSource.MANUAL.value: Decimal("0.0"),
            IssueSource.INTEGRATION.value: Decimal("0.05"),
        }
        return weights.get(source, Decimal("0.0"))

    def _get_capability_confidence(self, capabilities: list[str]) -> Decimal:
        """Get confidence modifier based on capability matches."""
        if not capabilities:
            return Decimal("-0.1")

        # All capabilities in registry
        if self._capability_registry and all(cap in self._capability_registry for cap in capabilities):
            return Decimal("0.1")

        # Some capabilities in registry
        if self._capability_registry and any(cap in self._capability_registry for cap in capabilities):
            return Decimal("0.05")

        return Decimal("0.0")

    def _calculate_confidence(
        self,
        source: str,
        type_confidence: Decimal,
        capabilities: list[str],
    ) -> Decimal:
        """
        Calculate overall confidence score.

        Reference: VALIDATOR_LOGIC.md Confidence Score Calculation

        Invariant VAL-003: Confidence in [0,1] (clamping)
        """
        base = Decimal("0.5")  # Start at neutral

        # Source quality
        base += self._get_source_weight(source)

        # Classification confidence
        base += type_confidence * Decimal("0.3")

        # Capability confidence
        base += self._get_capability_confidence(capabilities)

        # VAL-003: Clamp to [0, 1]
        return max(Decimal("0.0"), min(Decimal("1.0"), base))

    def _determine_action(
        self,
        issue_type: IssueType,
        severity: Severity,
        confidence: Decimal,
    ) -> RecommendedAction:
        """
        Determine recommended action.

        Reference: VALIDATOR_LOGIC.md Recommended Action Logic

        Invariants:
        - VAL-004: Unknown type defers
        - VAL-005: Escalation always escalates
        """
        # VAL-005: Escalation always escalates
        if issue_type == IssueType.ESCALATION:
            return RecommendedAction.ESCALATE

        # VAL-004: Unknown always defers
        if issue_type == IssueType.UNKNOWN:
            return RecommendedAction.DEFER

        # Critical bugs escalate
        if issue_type == IssueType.BUG_REPORT and severity == Severity.CRITICAL:
            return RecommendedAction.ESCALATE

        # Low confidence defers
        if confidence < Decimal("0.5"):
            return RecommendedAction.DEFER

        # Low severity with low confidence can be rejected
        if severity == Severity.LOW and confidence < Decimal("0.7"):
            return RecommendedAction.REJECT

        # Default: create contract
        return RecommendedAction.CREATE_CONTRACT

    def _build_reason(
        self,
        issue_type: IssueType,
        severity: Severity,
        action: RecommendedAction,
        confidence: Decimal,
    ) -> str:
        """Build human-readable reason for verdict."""
        parts = []

        parts.append(f"Classified as {issue_type.value} with {severity.value} severity.")

        if action == RecommendedAction.ESCALATE:
            parts.append("Escalation required due to issue nature.")
        elif action == RecommendedAction.DEFER:
            parts.append(
                f"Deferred due to {'low confidence' if confidence < Decimal('0.5') else 'unknown classification'}."
            )
        elif action == RecommendedAction.REJECT:
            parts.append("Rejected due to low severity and confidence.")
        else:
            parts.append("Recommended for contract creation.")

        parts.append(f"Confidence: {float(confidence):.2f}")

        return " ".join(parts)

    def _create_fallback_verdict(self, error_type: ValidatorErrorType, message: str) -> ValidatorVerdict:
        """
        Create fallback verdict on error.

        Reference: VALIDATOR_LOGIC.md Error Handling

        On error, returns safe fallback that defers to human review.
        """
        return ValidatorVerdict(
            issue_type=IssueType.UNKNOWN,
            severity=Severity.MEDIUM,
            affected_capabilities=(),
            recommended_action=RecommendedAction.DEFER,
            confidence_score=Decimal("0.0"),
            reason=f"Validator error: {error_type.value} - {message}",
            evidence={"error_type": error_type.value, "error_message": message},
            analyzed_at=datetime.now(timezone.utc),
            validator_version=VALIDATOR_VERSION,
        )
