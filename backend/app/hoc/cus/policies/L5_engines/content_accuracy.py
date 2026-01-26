# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Policy content accuracy validation (pure logic)
# Callers: policy/engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, Policy System
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure logic

# M23 Content Accuracy Validator
# Prevents AI from making assertions about data that is missing or NULL
#
# The CONTENT_ACCURACY policy gap:
# - AI output: "Yes, your contract is set to auto-renew on January 1, 2026."
# - Context data: auto_renew = NULL
# - Problem: AI made definitive assertion when data was missing
#
# This validator detects and prevents such assertions.

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AssertionType(str, Enum):
    """Types of assertions detected in output."""

    DEFINITIVE = "definitive"  # "Your contract IS auto-renewed"
    CONDITIONAL = "conditional"  # "IF auto-renew is enabled, THEN..."
    UNCERTAIN = "uncertain"  # "I'm not sure if..." or "I don't have that info"
    HEDGED = "hedged"  # "Based on available data..." or "It appears..."


class ValidationResult(str, Enum):
    """Result of content accuracy validation."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass
class AssertionCheck:
    """A single assertion check result."""

    field_name: str  # Field being asserted about
    assertion_type: AssertionType
    field_value: Any  # Actual value from context (None if missing)
    field_present: bool  # Whether field exists in context
    output_claim: str  # What the output claimed
    is_violation: bool  # True if assertion violates policy
    reason: Optional[str] = None


@dataclass
class ContentAccuracyResult:
    """Complete result of content accuracy validation."""

    result: ValidationResult
    checks: List[AssertionCheck] = field(default_factory=list)
    violations: List[AssertionCheck] = field(default_factory=list)
    overall_reason: Optional[str] = None
    confidence: float = 0.0

    # For incident creation
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result": self.result.value,
            "checks": [
                {
                    "field": c.field_name,
                    "assertion_type": c.assertion_type.value,
                    "field_value": str(c.field_value) if c.field_value else None,
                    "field_present": c.field_present,
                    "output_claim": c.output_claim[:100],
                    "is_violation": c.is_violation,
                    "reason": c.reason,
                }
                for c in self.checks
            ],
            "violation_count": len(self.violations),
            "overall_reason": self.overall_reason,
            "confidence": self.confidence,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
        }


# Patterns that indicate definitive assertions
DEFINITIVE_PATTERNS = [
    r"\bis\b",  # "is set to", "is enabled"
    r"\bwill\b",  # "will auto-renew"
    r"\bhas been\b",  # "has been configured"
    r"\byes\b",  # "Yes, your contract..."
    r"\bconfirm\b",  # "I can confirm that..."
    r"\bdefinitely\b",
    r"\bcertainly\b",
    r"\babsolutely\b",
    r"\bguaranteed\b",
    r"\bscheduled\b",  # "scheduled for"
    r"\bset to\b",  # "set to auto-renew"
]

# Patterns that indicate appropriate uncertainty
UNCERTAINTY_PATTERNS = [
    r"\bi don't have\b",
    r"\bi'm not sure\b",
    r"\bi cannot confirm\b",
    r"\bunable to verify\b",
    r"\bno information\b",
    r"\bmissing\b",
    r"\bnot available\b",
    r"\bwould need to check\b",
    r"\bplease provide\b",
    r"\blet me look into\b",
    r"\bi don't see\b",
    r"\bno record of\b",
]

# Patterns that indicate hedged/qualified statements
HEDGED_PATTERNS = [
    r"\bbased on\b",
    r"\baccording to\b",
    r"\bit appears\b",
    r"\bit seems\b",
    r"\bmight\b",
    r"\bmay\b",
    r"\bcould\b",
    r"\bpossibly\b",
    r"\blikely\b",
    r"\bif .+ then\b",
]

# Domain-specific terms to look for in assertions
CONTRACT_TERMS = {
    "auto_renew": ["auto-renew", "auto renew", "automatically renew", "renewal"],
    "expiration_date": ["expir", "end date", "terminate", "valid until"],
    "contract_value": ["value", "amount", "cost", "price", "fee"],
    "payment_status": ["paid", "payment", "invoice", "billing"],
    "tier": ["tier", "plan", "subscription", "level"],
}


class ContentAccuracyValidator:
    """
    Validates that LLM output does not make assertions about missing data.

    Prevention mechanism for the CONTENT_ACCURACY policy gap:
    - Detects when output makes definitive claims
    - Checks if the claimed data exists in context
    - Blocks/warns when assertions are made about NULL/missing fields
    """

    def __init__(
        self,
        strict_mode: bool = True,
        required_fields: Optional[List[str]] = None,
        domain_terms: Optional[Dict[str, List[str]]] = None,
    ):
        self.strict_mode = strict_mode
        self.required_fields = required_fields or []
        self.domain_terms = domain_terms or CONTRACT_TERMS

        # Compile patterns
        self._definitive_re = [re.compile(p, re.IGNORECASE) for p in DEFINITIVE_PATTERNS]
        self._uncertainty_re = [re.compile(p, re.IGNORECASE) for p in UNCERTAINTY_PATTERNS]
        self._hedged_re = [re.compile(p, re.IGNORECASE) for p in HEDGED_PATTERNS]

    def validate(
        self,
        output: str,
        context: Dict[str, Any],
        user_query: Optional[str] = None,
    ) -> ContentAccuracyResult:
        """
        Validate that output content is accurate given the context.

        Args:
            output: The LLM output text
            context: The context data that was available to the LLM
            user_query: Optional user query for additional context

        Returns:
            ContentAccuracyResult with pass/fail and details
        """
        checks: List[AssertionCheck] = []
        violations: List[AssertionCheck] = []

        # Detect assertion type in output
        assertion_type = self._detect_assertion_type(output)

        # Check each domain term
        for field_name, terms in self.domain_terms.items():
            # Check if output mentions this field
            field_mentioned = any(re.search(rf"\b{re.escape(term)}\b", output, re.IGNORECASE) for term in terms)

            if not field_mentioned:
                continue

            # Get field value from context
            field_value = self._get_nested_value(context, field_name)
            field_present = field_value is not None

            # Extract the claim about this field
            output_claim = self._extract_claim(output, terms)

            # Check if this is a violation
            is_violation = False
            reason = None

            if assertion_type == AssertionType.DEFINITIVE and not field_present:
                is_violation = True
                reason = f"Made definitive assertion about '{field_name}' but field is NULL/missing in context"
            elif assertion_type == AssertionType.DEFINITIVE and field_value is False:
                # Check if output claims True when value is False
                if self._claims_affirmative(output_claim):
                    is_violation = True
                    reason = f"Claimed '{field_name}' is true/enabled but context shows it's False"

            check = AssertionCheck(
                field_name=field_name,
                assertion_type=assertion_type,
                field_value=field_value,
                field_present=field_present,
                output_claim=output_claim,
                is_violation=is_violation,
                reason=reason,
            )
            checks.append(check)

            if is_violation:
                violations.append(check)

        # Determine overall result
        if violations:
            result = ValidationResult.FAIL
            overall_reason = f"Found {len(violations)} content accuracy violation(s): " + "; ".join(
                v.reason for v in violations if v.reason
            )
            expected = "Express uncertainty when data is missing (e.g., 'I don't have information about...')"
            actual = f"Made definitive assertion: '{violations[0].output_claim[:50]}...'"
        elif assertion_type == AssertionType.DEFINITIVE and self.strict_mode:
            result = ValidationResult.WARN
            overall_reason = "Definitive assertion detected - verify data availability"
            expected = None
            actual = None
        else:
            result = ValidationResult.PASS
            overall_reason = None
            expected = None
            actual = None

        return ContentAccuracyResult(
            result=result,
            checks=checks,
            violations=violations,
            overall_reason=overall_reason,
            confidence=0.85 if violations else 0.95,
            expected_behavior=expected,
            actual_behavior=actual,
        )

    def _detect_assertion_type(self, text: str) -> AssertionType:
        """Detect the type of assertion in the text."""
        text_lower = text.lower()

        # Check for uncertainty first (takes precedence)
        for pattern in self._uncertainty_re:
            if pattern.search(text_lower):
                return AssertionType.UNCERTAIN

        # Check for hedged statements
        for pattern in self._hedged_re:
            if pattern.search(text_lower):
                return AssertionType.HEDGED

        # Check for definitive assertions
        for pattern in self._definitive_re:
            if pattern.search(text_lower):
                return AssertionType.DEFINITIVE

        return AssertionType.CONDITIONAL

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get a value from nested dict using dot notation."""
        keys = key.split(".")
        value = data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None

            if value is None:
                return None

        return value

    def _extract_claim(self, text: str, terms: List[str]) -> str:
        """Extract the sentence containing the claim about these terms."""
        sentences = re.split(r"[.!?]", text)

        for sentence in sentences:
            for term in terms:
                if re.search(rf"\b{re.escape(term)}\b", sentence, re.IGNORECASE):
                    return sentence.strip()

        return text[:100]

    def _claims_affirmative(self, claim: str) -> bool:
        """Check if the claim makes an affirmative statement."""
        affirmative_patterns = [
            r"\byes\b",
            r"\bis\b",
            r"\bwill\b",
            r"\bhas\b",
            r"\benabled\b",
            r"\bactive\b",
            r"\bset to\b",
        ]

        for pattern in affirmative_patterns:
            if re.search(pattern, claim, re.IGNORECASE):
                return True

        return False


def validate_content_accuracy(
    output: str,
    context: Dict[str, Any],
    user_query: Optional[str] = None,
    strict_mode: bool = True,
) -> ContentAccuracyResult:
    """
    Convenience function to validate content accuracy.

    Usage:
        result = validate_content_accuracy(
            output="Yes, your contract is set to auto-renew on January 1, 2026.",
            context={"auto_renew": None, "customer_id": "cust_8372"},
            user_query="Is my contract auto-renewed?"
        )

        if result.result == ValidationResult.FAIL:
            # Block the response or create incident
            pass
    """
    validator = ContentAccuracyValidator(strict_mode=strict_mode)
    return validator.validate(output, context, user_query)


# Quick test
if __name__ == "__main__":
    # Test the validator with the demo scenario
    result = validate_content_accuracy(
        output="Yes, your contract is set to auto-renew on January 1, 2026.",
        context={
            "customer_id": "cust_8372",
            "auto_renew": None,  # NULL - data is missing!
            "contract_status": "active",
        },
        user_query="Is my contract auto-renewed?",
    )

    print(f"Result: {result.result.value}")
    print(f"Violations: {len(result.violations)}")
    if result.violations:
        print(f"Reason: {result.overall_reason}")
        print(f"Expected: {result.expected_behavior}")
        print(f"Actual: {result.actual_behavior}")
