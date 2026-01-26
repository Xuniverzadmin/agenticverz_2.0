# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api/worker
#   Execution: sync
# Lifecycle:
#   Emits: prevention_blocked, prevention_allowed
#   Subscribes: none
# Data Access:
#   Reads: Policy, PreventionRecord (via driver)
#   Writes: PreventionRecord (via driver)
# Role: Prevention-based policy validation
# Callers: policy/engine, workers
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, Policy System

# M24 Prevention Engine
# Multi-policy prevention with severity levels, async incident creation, and metrics
#
# Improvements over M23:
# - Multi-policy support (CONTENT_ACCURACY, SAFETY, PII, HALLUCINATION, BUDGET)
# - Severity classification (CRITICAL, HIGH, MEDIUM, LOW)
# - Async incident creation from violations
# - Prometheus metrics emission
# - Rule chaining with short-circuit
# - Counterfactual simulation result

import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4


class PolicyType(str, Enum):
    """Types of policies that can be evaluated."""

    CONTENT_ACCURACY = "CONTENT_ACCURACY"
    SAFETY = "SAFETY"
    PII = "PII"
    HALLUCINATION = "HALLUCINATION"
    BUDGET_LIMIT = "BUDGET_LIMIT"
    RATE_LIMIT = "RATE_LIMIT"
    CUSTOM = "CUSTOM"


class Severity(str, Enum):
    """Severity levels for policy violations."""

    CRITICAL = "critical"  # Immediate block, incident creation, alert
    HIGH = "high"  # Block, incident creation
    MEDIUM = "medium"  # Modify response, log warning
    LOW = "low"  # Log only, allow through


class PreventionAction(str, Enum):
    """Action to take when prevention triggers."""

    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"
    WARN = "warn"
    ESCALATE = "escalate"


@dataclass
class PolicyViolation:
    """A single policy violation detected."""

    policy: PolicyType
    severity: Severity
    rule_id: str
    reason: str
    evidence: Dict[str, Any]
    field_name: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    confidence: float = 0.9

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy": self.policy.value,
            "severity": self.severity.value,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "evidence": self.evidence,
            "field_name": self.field_name,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "confidence": self.confidence,
        }


@dataclass
class PreventionContext:
    """Context for prevention evaluation."""

    tenant_id: str
    call_id: str
    user_query: str
    llm_output: str
    context_data: Dict[str, Any]
    model: str = "unknown"
    user_id: Optional[str] = None
    system_prompt: Optional[str] = None
    output_tokens: int = 0
    input_tokens: int = 0
    cost_usd: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def hash_output(self) -> str:
        """Generate deterministic hash of output for replay verification."""
        return hashlib.sha256(self.llm_output.encode()).hexdigest()[:16]


@dataclass
class PreventionResult:
    """Result of prevention engine evaluation."""

    action: PreventionAction
    violations: List[PolicyViolation] = field(default_factory=list)
    passed_policies: List[PolicyType] = field(default_factory=list)
    modified_output: Optional[str] = None
    safe_output: Optional[str] = None
    would_prevent: bool = False

    # Metadata
    evaluation_id: str = field(default_factory=lambda: str(uuid4()))
    evaluation_ms: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def highest_severity(self) -> Optional[Severity]:
        if not self.violations:
            return None
        severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
        for sev in severity_order:
            if any(v.severity == sev for v in self.violations):
                return sev
        return None

    @property
    def primary_violation(self) -> Optional[PolicyViolation]:
        if not self.violations:
            return None
        return self.violations[0]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "violations": [v.to_dict() for v in self.violations],
            "passed_policies": [p.value for p in self.passed_policies],
            "modified_output": self.modified_output[:100] if self.modified_output else None,
            "would_prevent": self.would_prevent,
            "highest_severity": self.highest_severity.value if self.highest_severity else None,
            "evaluation_id": self.evaluation_id,
            "evaluation_ms": self.evaluation_ms,
        }


class BaseValidator:
    """Base class for policy validators."""

    policy_type: PolicyType = PolicyType.CUSTOM
    default_severity: Severity = Severity.MEDIUM

    def validate(self, ctx: PreventionContext) -> List[PolicyViolation]:
        """Validate and return list of violations. Empty list = pass."""
        raise NotImplementedError


class ContentAccuracyValidatorV2(BaseValidator):
    """Enhanced content accuracy validator."""

    policy_type = PolicyType.CONTENT_ACCURACY
    default_severity = Severity.HIGH

    # Definitive assertion patterns
    DEFINITIVE_PATTERNS = [
        r"\bis\b",
        r"\bwill\b",
        r"\bhas been\b",
        r"\byes\b",
        r"\bconfirm\b",
        r"\bdefinitely\b",
        r"\bcertainly\b",
        r"\babsolutely\b",
        r"\bguaranteed\b",
        r"\bscheduled\b",
        r"\bset to\b",
        r"\bwill be\b",
        r"\byou have\b",
    ]

    # Uncertainty patterns (good behavior)
    UNCERTAINTY_PATTERNS = [
        r"\bi don't have\b",
        r"\bi'm not sure\b",
        r"\bi cannot confirm\b",
        r"\bunable to verify\b",
        r"\bno information\b",
        r"\bmissing\b",
        r"\bnot available\b",
        r"\bwould need to check\b",
        r"\blet me look\b",
        r"\bi don't see\b",
        r"\bno record of\b",
        r"\bplease provide\b",
    ]

    # Domain terms to check
    DOMAIN_TERMS = {
        "auto_renew": ["auto-renew", "auto renew", "automatically renew", "renewal"],
        "expiration_date": ["expir", "end date", "terminate", "valid until"],
        "contract_value": ["value", "amount", "cost", "price", "fee", "total"],
        "payment_status": ["paid", "payment", "invoice", "billing", "charged"],
        "subscription_tier": ["tier", "plan", "subscription", "level", "package"],
        "account_status": ["account", "status", "active", "suspended", "cancelled"],
    }

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self._definitive_re = [re.compile(p, re.I) for p in self.DEFINITIVE_PATTERNS]
        self._uncertainty_re = [re.compile(p, re.I) for p in self.UNCERTAINTY_PATTERNS]

    def validate(self, ctx: PreventionContext) -> List[PolicyViolation]:
        violations = []
        output_lower = ctx.llm_output.lower()

        # Check if output expresses uncertainty (good)
        expresses_uncertainty = any(p.search(output_lower) for p in self._uncertainty_re)
        if expresses_uncertainty:
            return []  # Good behavior, no violation

        # Check if output makes definitive assertions
        is_definitive = any(p.search(output_lower) for p in self._definitive_re)
        if not is_definitive:
            return []  # Not making claims

        # Check each domain term
        for field_name, terms in self.DOMAIN_TERMS.items():
            field_mentioned = any(re.search(rf"\b{re.escape(term)}\b", ctx.llm_output, re.I) for term in terms)

            if not field_mentioned:
                continue

            # Check if field exists in context
            field_value = self._get_value(ctx.context_data, field_name)

            if field_value is None:
                # Made definitive claim about missing data
                claim = self._extract_claim(ctx.llm_output, terms)
                violations.append(
                    PolicyViolation(
                        policy=PolicyType.CONTENT_ACCURACY,
                        severity=Severity.HIGH,
                        rule_id="CA001",
                        reason=f"Definitive assertion about '{field_name}' but data is NULL/missing",
                        evidence={
                            "field": field_name,
                            "value_in_context": None,
                            "claim_made": claim[:100],
                        },
                        field_name=field_name,
                        expected_behavior="Express uncertainty when data is missing",
                        actual_behavior=f"Made definitive claim: '{claim[:50]}...'",
                        confidence=0.90,
                    )
                )

        return violations

    def _get_value(self, data: Dict[str, Any], key: str) -> Any:
        if "." in key:
            parts = key.split(".")
            for p in parts:
                if isinstance(data, dict):
                    data = data.get(p)
                else:
                    return None
            return data
        return data.get(key)

    def _extract_claim(self, text: str, terms: List[str]) -> str:
        sentences = re.split(r"[.!?]", text)
        for sent in sentences:
            if any(re.search(rf"\b{re.escape(t)}\b", sent, re.I) for t in terms):
                return sent.strip()
        return text[:100]


class PIIValidator(BaseValidator):
    """Detects PII in LLM output that shouldn't be exposed."""

    policy_type = PolicyType.PII
    default_severity = Severity.CRITICAL

    PII_PATTERNS = {
        "ssn": (r"\b\d{3}-\d{2}-\d{4}\b", "Social Security Number"),
        "credit_card": (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "Credit Card Number"),
        "email": (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "Email Address"),
        "phone": (r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "Phone Number"),
        "passport": (r"\b[A-Z]{1,2}\d{6,9}\b", "Passport Number"),
        "dob": (r"\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b", "Date of Birth"),
        "ip_address": (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "IP Address"),
        "api_key": (r"\b(?:sk|pk|api|key|token)[_-]?(?:[a-zA-Z0-9_-]+){20,}\b", "API Key"),
    }

    def __init__(self, allowed_pii: Optional[Set[str]] = None):
        self.allowed_pii = allowed_pii or set()
        self._patterns = {
            k: (re.compile(v[0], re.I), v[1]) for k, v in self.PII_PATTERNS.items() if k not in self.allowed_pii
        }

    def validate(self, ctx: PreventionContext) -> List[PolicyViolation]:
        violations = []

        for pii_type, (pattern, description) in self._patterns.items():
            matches = pattern.findall(ctx.llm_output)
            if matches:
                # Redact the actual values in evidence
                redacted = [self._redact(m) for m in matches[:3]]
                violations.append(
                    PolicyViolation(
                        policy=PolicyType.PII,
                        severity=Severity.CRITICAL,
                        rule_id=f"PII_{pii_type.upper()}",
                        reason=f"Detected {description} in output",
                        evidence={
                            "pii_type": pii_type,
                            "count": len(matches),
                            "samples_redacted": redacted,
                        },
                        expected_behavior="Never expose PII in responses",
                        actual_behavior=f"Exposed {len(matches)} {description}(s)",
                        confidence=0.95,
                    )
                )

        return violations

    def _redact(self, value: str) -> str:
        if len(value) <= 4:
            return "****"
        return value[:2] + "*" * (len(value) - 4) + value[-2:]


class SafetyValidator(BaseValidator):
    """Detects harmful, dangerous, or inappropriate content."""

    policy_type = PolicyType.SAFETY
    default_severity = Severity.CRITICAL

    HARM_PATTERNS = {
        "violence": [
            r"\b(?:kill|murder|attack|harm|hurt|injure)\s+(?:you|them|people|someone)\b",
            r"\bhow to (?:make|build|create)\s+(?:a\s+)?(?:bomb|weapon|poison)\b",
            r"\bmake\s+(?:a\s+)?(?:bomb|weapon|explosive)\b",
        ],
        "self_harm": [
            r"\b(?:kill yourself|end your life|commit suicide)\b",
            r"\b(?:methods of|ways to)\s+(?:suicide|self-harm)\b",
        ],
        "illegal_activity": [
            r"\bhow to (?:hack|steal|fraud|launder)\b",
            r"\b(?:drug|weapon)\s+(?:trafficking|dealing)\b",
        ],
        "hate_speech": [
            r"\b(?:all|every)\s+(?:jews|muslims|blacks|whites|asians)\s+(?:should|must|are)\b",
        ],
    }

    def __init__(self):
        self._patterns = {}
        for category, patterns in self.HARM_PATTERNS.items():
            self._patterns[category] = [re.compile(p, re.I) for p in patterns]

    def validate(self, ctx: PreventionContext) -> List[PolicyViolation]:
        violations = []

        for category, patterns in self._patterns.items():
            for pattern in patterns:
                match = pattern.search(ctx.llm_output)
                if match:
                    violations.append(
                        PolicyViolation(
                            policy=PolicyType.SAFETY,
                            severity=Severity.CRITICAL,
                            rule_id=f"SAFETY_{category.upper()}",
                            reason=f"Detected potentially harmful content: {category}",
                            evidence={
                                "category": category,
                                "matched_text": match.group()[:50],
                            },
                            expected_behavior="Refuse to provide harmful content",
                            actual_behavior=f"Generated content matching {category} pattern",
                            confidence=0.85,
                        )
                    )
                    break  # One violation per category is enough

        return violations


class HallucinationValidator(BaseValidator):
    """Detects potential hallucinations by checking for unsupported claims."""

    policy_type = PolicyType.HALLUCINATION
    default_severity = Severity.MEDIUM

    # Patterns suggesting fabricated specifics
    FABRICATION_PATTERNS = [
        r"\baccording to (?:the|a) (?:study|report|survey) (?:from|by|in) \d{4}\b",
        r"\b(?:research shows|studies indicate|data suggests) that \d+%\b",
        r"\b(?:Dr\.|Professor) [A-Z][a-z]+ [A-Z][a-z]+ (?:said|stated|found)\b",
        r"\b(?:in|on) (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b",
    ]

    def __init__(self, context_required_fields: Optional[List[str]] = None):
        self.context_required_fields = context_required_fields or []
        self._patterns = [re.compile(p, re.I) for p in self.FABRICATION_PATTERNS]

    def validate(self, ctx: PreventionContext) -> List[PolicyViolation]:
        violations = []

        # Check for fabrication patterns
        for pattern in self._patterns:
            match = pattern.search(ctx.llm_output)
            if match:
                # Check if this specific claim is in context
                claim = match.group()
                if not self._claim_in_context(claim, ctx.context_data):
                    violations.append(
                        PolicyViolation(
                            policy=PolicyType.HALLUCINATION,
                            severity=Severity.MEDIUM,
                            rule_id="HALL001",
                            reason="Potentially fabricated specific claim not in context",
                            evidence={
                                "claim": claim,
                                "pattern_matched": pattern.pattern[:50],
                            },
                            expected_behavior="Only cite information from provided context",
                            actual_behavior=f"Made specific claim: '{claim}'",
                            confidence=0.70,
                        )
                    )

        return violations

    def _claim_in_context(self, claim: str, context: Dict[str, Any]) -> bool:
        """Check if claim can be found anywhere in context."""
        context_str = str(context).lower()
        # Extract key terms from claim
        terms = re.findall(r"\b\w+\b", claim.lower())
        # If most terms are in context, it might be supported
        matches = sum(1 for t in terms if t in context_str)
        return matches > len(terms) * 0.7


class BudgetValidator(BaseValidator):
    """Validates that response doesn't exceed budget limits."""

    policy_type = PolicyType.BUDGET_LIMIT
    default_severity = Severity.HIGH

    def __init__(self, max_tokens: int = 4000, max_cost_usd: float = 0.10):
        self.max_tokens = max_tokens
        self.max_cost_usd = max_cost_usd

    def validate(self, ctx: PreventionContext) -> List[PolicyViolation]:
        violations = []

        total_tokens = ctx.input_tokens + ctx.output_tokens
        if total_tokens > self.max_tokens:
            violations.append(
                PolicyViolation(
                    policy=PolicyType.BUDGET_LIMIT,
                    severity=Severity.MEDIUM,
                    rule_id="BUDGET_TOKENS",
                    reason=f"Token usage ({total_tokens}) exceeds limit ({self.max_tokens})",
                    evidence={
                        "input_tokens": ctx.input_tokens,
                        "output_tokens": ctx.output_tokens,
                        "total_tokens": total_tokens,
                        "limit": self.max_tokens,
                    },
                    expected_behavior=f"Stay within {self.max_tokens} tokens",
                    actual_behavior=f"Used {total_tokens} tokens",
                    confidence=1.0,
                )
            )

        if ctx.cost_usd > self.max_cost_usd:
            violations.append(
                PolicyViolation(
                    policy=PolicyType.BUDGET_LIMIT,
                    severity=Severity.HIGH,
                    rule_id="BUDGET_COST",
                    reason=f"Cost (${ctx.cost_usd:.4f}) exceeds limit (${self.max_cost_usd:.4f})",
                    evidence={
                        "cost_usd": ctx.cost_usd,
                        "limit_usd": self.max_cost_usd,
                    },
                    expected_behavior=f"Stay within ${self.max_cost_usd:.4f}",
                    actual_behavior=f"Cost ${ctx.cost_usd:.4f}",
                    confidence=1.0,
                )
            )

        return violations


class PreventionEngine:
    """
    Multi-policy prevention engine with severity levels and async incident creation.

    Usage:
        engine = PreventionEngine()

        result = engine.evaluate(PreventionContext(
            tenant_id="tenant_123",
            call_id="call_abc",
            user_query="Is my contract auto-renewed?",
            llm_output="Yes, your contract will auto-renew...",
            context_data={"auto_renew": None},
        ))

        if result.action == PreventionAction.BLOCK:
            return error_response("Response blocked by policy")
        elif result.action == PreventionAction.MODIFY:
            return result.safe_output
    """

    DEFAULT_SAFE_RESPONSE = (
        "I apologize, but I don't have enough information to answer that question "
        "accurately. Please contact support or check your account settings for "
        "the most up-to-date information."
    )

    SEVERITY_TO_ACTION = {
        Severity.CRITICAL: PreventionAction.BLOCK,
        Severity.HIGH: PreventionAction.MODIFY,
        Severity.MEDIUM: PreventionAction.WARN,
        Severity.LOW: PreventionAction.ALLOW,
    }

    def __init__(
        self,
        validators: Optional[List[BaseValidator]] = None,
        strict_mode: bool = True,
        block_on_critical: bool = True,
        modify_on_high: bool = True,
        emit_metrics: bool = True,
    ):
        self.strict_mode = strict_mode
        self.block_on_critical = block_on_critical
        self.modify_on_high = modify_on_high
        self.emit_metrics = emit_metrics

        # Initialize default validators if not provided
        self.validators = validators or [
            ContentAccuracyValidatorV2(strict_mode=strict_mode),
            PIIValidator(),
            SafetyValidator(),
            HallucinationValidator(),
            BudgetValidator(),
        ]

    def evaluate(self, ctx: PreventionContext) -> PreventionResult:
        """Evaluate all policies and return result."""
        start = time.time()

        all_violations: List[PolicyViolation] = []
        passed_policies: List[PolicyType] = []

        # Run all validators
        for validator in self.validators:
            try:
                violations = validator.validate(ctx)
                if violations:
                    all_violations.extend(violations)
                else:
                    passed_policies.append(validator.policy_type)
            except Exception as e:
                # Log error but don't fail the entire evaluation
                all_violations.append(
                    PolicyViolation(
                        policy=validator.policy_type,
                        severity=Severity.LOW,
                        rule_id="VALIDATOR_ERROR",
                        reason=f"Validator error: {str(e)}",
                        evidence={"error": str(e)},
                        confidence=0.5,
                    )
                )

        # Sort violations by severity
        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
        all_violations.sort(key=lambda v: severity_order.get(v.severity, 99))

        # Determine action
        action = PreventionAction.ALLOW
        modified_output = None
        safe_output = None

        if all_violations:
            highest = all_violations[0].severity

            if highest == Severity.CRITICAL and self.block_on_critical:
                action = PreventionAction.BLOCK
                safe_output = self._generate_safe_response(ctx, all_violations)
            elif highest == Severity.HIGH and self.modify_on_high:
                action = PreventionAction.MODIFY
                safe_output = self._generate_safe_response(ctx, all_violations)
                modified_output = safe_output
            elif highest == Severity.MEDIUM:
                action = PreventionAction.WARN
            else:
                action = PreventionAction.ALLOW

        eval_ms = int((time.time() - start) * 1000)

        result = PreventionResult(
            action=action,
            violations=all_violations,
            passed_policies=passed_policies,
            modified_output=modified_output,
            safe_output=safe_output,
            would_prevent=len(all_violations) > 0,
            evaluation_ms=eval_ms,
        )

        # Emit metrics
        if self.emit_metrics:
            self._emit_metrics(ctx, result)

        return result

    def _generate_safe_response(
        self,
        ctx: PreventionContext,
        violations: List[PolicyViolation],
    ) -> str:
        """Generate a safe response based on the violation type."""
        if not violations:
            return self.DEFAULT_SAFE_RESPONSE

        primary = violations[0]

        # Custom responses by policy type
        if primary.policy == PolicyType.CONTENT_ACCURACY:
            return (
                "I don't have access to the specific information needed to answer that "
                "question accurately. To get the correct details, please check your account "
                "settings or contact our support team."
            )
        elif primary.policy == PolicyType.PII:
            return (
                "I'm unable to share that information. For security reasons, please contact "
                "our support team directly for assistance with sensitive account details."
            )
        elif primary.policy == PolicyType.SAFETY:
            return (
                "I'm not able to help with that request. If you have other questions I can "
                "assist with, please let me know."
            )
        elif primary.policy == PolicyType.HALLUCINATION:
            return (
                "I want to make sure I give you accurate information. Let me check on that "
                "and get back to you with verified details."
            )
        elif primary.policy == PolicyType.BUDGET_LIMIT:
            return (
                "I apologize, but I need to provide a shorter response. Here's a summary: "
                "Please contact support for more detailed information."
            )

        return self.DEFAULT_SAFE_RESPONSE

    def _emit_metrics(self, ctx: PreventionContext, result: PreventionResult) -> None:
        """Emit Prometheus metrics for prevention results."""
        try:
            from prometheus_client import Counter, Histogram

            # Define metrics (will use existing if already defined)
            prevention_total = Counter(
                "prevention_evaluations_total",
                "Total prevention evaluations",
                ["tenant_id", "action", "highest_severity"],
            )

            prevention_violations = Counter(
                "prevention_violations_total", "Total policy violations detected", ["tenant_id", "policy", "severity"]
            )

            prevention_latency = Histogram(
                "prevention_evaluation_seconds", "Prevention evaluation latency", ["tenant_id"]
            )

            # Emit
            severity = result.highest_severity.value if result.highest_severity else "none"
            prevention_total.labels(
                tenant_id=ctx.tenant_id,
                action=result.action.value,
                highest_severity=severity,
            ).inc()

            for v in result.violations:
                prevention_violations.labels(
                    tenant_id=ctx.tenant_id,
                    policy=v.policy.value,
                    severity=v.severity.value,
                ).inc()

            prevention_latency.labels(tenant_id=ctx.tenant_id).observe(result.evaluation_ms / 1000)

        except ImportError:
            pass  # Prometheus not available
        except Exception:
            pass  # Don't fail on metric errors


# Convenience functions

_engine: Optional[PreventionEngine] = None


def get_prevention_engine() -> PreventionEngine:
    """Get global prevention engine instance."""
    global _engine
    if _engine is None:
        _engine = PreventionEngine()
    return _engine


def evaluate_prevention(
    tenant_id: str,
    call_id: str,
    user_query: str,
    llm_output: str,
    context_data: Dict[str, Any],
    model: str = "unknown",
    user_id: Optional[str] = None,
) -> PreventionResult:
    """
    Convenience function to evaluate prevention.

    Usage:
        result = evaluate_prevention(
            tenant_id="tenant_123",
            call_id="call_abc",
            user_query="Is my contract auto-renewed?",
            llm_output="Yes, your contract will auto-renew...",
            context_data={"auto_renew": None},
        )

        if result.action != PreventionAction.ALLOW:
            # Handle blocked/modified response
            pass
    """
    engine = get_prevention_engine()
    ctx = PreventionContext(
        tenant_id=tenant_id,
        call_id=call_id,
        user_query=user_query,
        llm_output=llm_output,
        context_data=context_data,
        model=model,
        user_id=user_id,
    )
    return engine.evaluate(ctx)


async def create_incident_from_violation(
    ctx: PreventionContext,
    result: PreventionResult,
    session: Optional[Any] = None,
) -> Optional[str]:
    """
    Create an incident from prevention violation.

    S3 Truth Model (PIN-195):
    1. Persist violation fact
    2. Create incident (only after violation persisted)
    3. Link evidence

    Returns incident_id if created, None otherwise.
    """
    if not result.violations:
        return None

    primary = result.primary_violation

    # Build evidence from context and violation
    evidence = {
        "user_id": ctx.user_id,
        "model": ctx.model,
        "timestamp": ctx.timestamp.isoformat(),
        "user_query_excerpt": ctx.user_query[:500],
        "llm_output_excerpt": ctx.llm_output[:1000],
        "context_data_excerpt": {k: str(v)[:100] for k, v in list(ctx.context_data.items())[:10]},
        "prevention_action": result.action.value,
        "would_prevent": result.would_prevent,
        "evaluation_id": result.evaluation_id,
        "expected_behavior": primary.expected_behavior,
        "actual_behavior": primary.actual_behavior,
        "violation_evidence": primary.evidence,
    }

    # Use the PolicyViolationService for proper S3 truth handling
    try:
        from app.db_async import AsyncSessionLocal
        from app.hoc.cus.incidents.L5_engines.policy_violation_service import (
            PolicyViolationService,
            ViolationFact,
        )

        # Create session if not provided
        if session is None:
            async with AsyncSessionLocal() as async_session:
                return await _create_incident_with_service(async_session, ctx, primary, evidence)
        else:
            return await _create_incident_with_service(session, ctx, primary, evidence)

    except ImportError as e:
        # Fallback for backwards compatibility (no S3 guarantees)
        import logging

        logging.getLogger("nova.policy.prevention").warning(
            f"PolicyViolationService not available: {e}. Using fallback."
        )
        return f"inc_{result.evaluation_id[:12]}"


async def _create_incident_with_service(
    session: Any,
    ctx: PreventionContext,
    primary: PolicyViolation,
    evidence: dict,
) -> Optional[str]:
    """Helper to create incident using PolicyViolationService."""
    from app.hoc.cus.incidents.L5_engines.policy_violation_service import (
        PolicyViolationService,
        ViolationFact,
    )

    service = PolicyViolationService(session)

    violation = ViolationFact(
        run_id=ctx.call_id,
        tenant_id=ctx.tenant_id,
        policy_id=primary.policy.value,
        policy_type=primary.policy.value,
        violated_rule=primary.rule_id,
        evaluated_value=f"call:{ctx.call_id}",
        threshold_condition=primary.reason,
        severity=primary.severity.value,
        reason=primary.reason,
        evidence=evidence,
    )

    result = await service.persist_violation_and_create_incident(violation)
    return result.incident_id if result else None


# Export all
__all__ = [
    "PolicyType",
    "Severity",
    "PreventionAction",
    "PolicyViolation",
    "PreventionContext",
    "PreventionResult",
    "BaseValidator",
    "ContentAccuracyValidatorV2",
    "PIIValidator",
    "SafetyValidator",
    "HallucinationValidator",
    "BudgetValidator",
    "PreventionEngine",
    "get_prevention_engine",
    "evaluate_prevention",
    "create_incident_from_violation",
]
