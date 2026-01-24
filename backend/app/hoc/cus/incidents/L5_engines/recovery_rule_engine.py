# Layer: L5 — Domain Engine (System Truth)
# Product: system-wide (NOT console-owned)
# Callers: recovery_evaluator.py (worker)
# Reference: PIN-240
# WARNING: If this logic is wrong, ALL products break.

# M10 Recovery Rule Engine
"""
Rule-based evaluation engine for recovery suggestions.

Evaluates a set of rules against failure context and returns
scored action recommendations.

Rules can be:
1. Error code matching (exact or prefix)
2. Historical pattern matching
3. Skill-specific rules
4. Tenant-specific overrides
5. Time-based rules (e.g., different behavior during incidents)

Environment Variables:
- RECOVERY_RULE_DEBUG: Enable debug logging for rule evaluation
"""

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.recovery_rule_engine")

DEBUG_MODE = os.getenv("RECOVERY_RULE_DEBUG", "").lower() == "true"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class RuleContext:
    """Context provided to rules for evaluation."""

    error_code: str
    error_message: str
    skill_id: Optional[str] = None
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None
    occurrence_count: int = 1
    historical_matches: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "skill_id": self.skill_id,
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "occurrence_count": self.occurrence_count,
            "historical_matches": len(self.historical_matches),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class RuleResult:
    """Result from evaluating a single rule."""

    rule_id: str
    rule_name: str
    matched: bool
    score: float  # 0.0 to 1.0
    action_code: Optional[str] = None
    explanation: str = ""
    confidence_adjustment: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "matched": self.matched,
            "score": self.score,
            "action_code": self.action_code,
            "explanation": self.explanation,
            "confidence_adjustment": self.confidence_adjustment,
            "metadata": self.metadata,
        }


@dataclass
class EvaluationResult:
    """Complete result from rule evaluation."""

    rules_evaluated: List[RuleResult]
    recommended_action: Optional[str] = None
    total_score: float = 0.0
    confidence: float = 0.0
    explanation: str = ""
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rules_evaluated": [r.to_dict() for r in self.rules_evaluated],
            "recommended_action": self.recommended_action,
            "total_score": self.total_score,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "duration_ms": self.duration_ms,
        }


# =============================================================================
# Rule Definitions
# =============================================================================


class Rule:
    """Base class for recovery rules."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        priority: int = 50,
        weight: float = 1.0,
    ):
        self.rule_id = rule_id
        self.name = name
        self.priority = priority
        self.weight = weight

    def evaluate(self, context: RuleContext) -> RuleResult:
        """Evaluate rule against context. Override in subclasses."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<Rule {self.rule_id}: {self.name}>"


class ErrorCodeRule(Rule):
    """Match based on error code patterns."""

    def __init__(
        self, rule_id: str, name: str, error_patterns: List[str], action_code: str, score: float = 0.8, **kwargs
    ):
        super().__init__(rule_id, name, **kwargs)
        self.error_patterns = [p.upper() for p in error_patterns]
        self.action_code = action_code
        self.score = score

    def evaluate(self, context: RuleContext) -> RuleResult:
        error_upper = context.error_code.upper()

        for pattern in self.error_patterns:
            if error_upper.startswith(pattern) or pattern in error_upper:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    matched=True,
                    score=self.score * self.weight,
                    action_code=self.action_code,
                    explanation=f"Error code '{context.error_code}' matches pattern '{pattern}'",
                    metadata={"matched_pattern": pattern},
                )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            matched=False,
            score=0.0,
            explanation=f"Error code '{context.error_code}' did not match any patterns",
        )


class HistoricalPatternRule(Rule):
    """Match based on historical success patterns."""

    def __init__(self, rule_id: str, name: str, min_occurrences: int = 3, min_success_rate: float = 0.7, **kwargs):
        super().__init__(rule_id, name, **kwargs)
        self.min_occurrences = min_occurrences
        self.min_success_rate = min_success_rate

    def evaluate(self, context: RuleContext) -> RuleResult:
        if not context.historical_matches:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                matched=False,
                score=0.0,
                explanation="No historical matches available",
            )

        # Count successes
        total = len(context.historical_matches)
        successes = sum(1 for m in context.historical_matches if m.get("recovery_succeeded"))

        if total < self.min_occurrences:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                matched=False,
                score=0.0,
                explanation=f"Insufficient history ({total} < {self.min_occurrences})",
            )

        success_rate = successes / total if total > 0 else 0.0

        if success_rate >= self.min_success_rate:
            # Find most common successful recovery
            successful_recoveries = [
                m.get("recovery_suggestion")
                for m in context.historical_matches
                if m.get("recovery_succeeded") and m.get("recovery_suggestion")
            ]

            action_code = None
            if successful_recoveries:
                # Use most common recovery
                from collections import Counter

                most_common = Counter(successful_recoveries).most_common(1)
                if most_common:
                    action_code = most_common[0][0]

            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                matched=True,
                score=success_rate * self.weight,
                action_code=action_code,
                explanation=f"Historical success rate {success_rate:.1%} ({successes}/{total})",
                confidence_adjustment=success_rate * 0.2,  # Boost confidence
                metadata={
                    "success_rate": success_rate,
                    "total_matches": total,
                    "successes": successes,
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            matched=False,
            score=0.0,
            explanation=f"Success rate {success_rate:.1%} below threshold {self.min_success_rate:.1%}",
        )


class SkillSpecificRule(Rule):
    """Rules specific to certain skills."""

    def __init__(self, rule_id: str, name: str, skill_ids: List[str], action_code: str, score: float = 0.7, **kwargs):
        super().__init__(rule_id, name, **kwargs)
        self.skill_ids = skill_ids
        self.action_code = action_code
        self.score = score

    def evaluate(self, context: RuleContext) -> RuleResult:
        if context.skill_id and context.skill_id in self.skill_ids:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                matched=True,
                score=self.score * self.weight,
                action_code=self.action_code,
                explanation=f"Skill '{context.skill_id}' matches rule",
                metadata={"matched_skill": context.skill_id},
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            matched=False,
            score=0.0,
            explanation=f"Skill '{context.skill_id}' not in target list",
        )


class OccurrenceThresholdRule(Rule):
    """Escalate based on occurrence count."""

    def __init__(self, rule_id: str, name: str, threshold: int, action_code: str, score: float = 0.9, **kwargs):
        super().__init__(rule_id, name, **kwargs)
        self.threshold = threshold
        self.action_code = action_code
        self.score = score

    def evaluate(self, context: RuleContext) -> RuleResult:
        if context.occurrence_count >= self.threshold:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                matched=True,
                score=self.score * self.weight,
                action_code=self.action_code,
                explanation=f"Occurrence count {context.occurrence_count} >= threshold {self.threshold}",
                confidence_adjustment=0.1,  # Boost for repeated failures
                metadata={
                    "occurrence_count": context.occurrence_count,
                    "threshold": self.threshold,
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            matched=False,
            score=0.0,
            explanation=f"Occurrence count {context.occurrence_count} < threshold {self.threshold}",
        )


class CompositeRule(Rule):
    """Combine multiple rules with AND/OR logic."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        rules: List[Rule],
        logic: str = "and",  # "and" or "or"
        **kwargs,
    ):
        super().__init__(rule_id, name, **kwargs)
        self.rules = rules
        self.logic = logic.lower()

    def evaluate(self, context: RuleContext) -> RuleResult:
        results = [rule.evaluate(context) for rule in self.rules]

        if self.logic == "and":
            matched = all(r.matched for r in results)
            score = min(r.score for r in results) if matched else 0.0
        else:  # "or"
            matched = any(r.matched for r in results)
            score = max(r.score for r in results) if matched else 0.0

        # Find best action code from matched rules
        action_code = None
        for r in sorted(results, key=lambda x: x.score, reverse=True):
            if r.matched and r.action_code:
                action_code = r.action_code
                break

        explanations = [r.explanation for r in results if r.matched]

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            matched=matched,
            score=score * self.weight,
            action_code=action_code,
            explanation=f"Composite ({self.logic}): " + "; ".join(explanations[:3]),
            metadata={"sub_results": [r.to_dict() for r in results]},
        )


# =============================================================================
# Default Rules
# =============================================================================

DEFAULT_RULES: List[Rule] = [
    # High priority - specific error handling
    ErrorCodeRule(
        rule_id="timeout_retry",
        name="Retry on Timeout",
        error_patterns=["TIMEOUT", "DEADLINE", "TIMED_OUT"],
        action_code="retry_exponential",
        score=0.85,
        priority=90,
    ),
    ErrorCodeRule(
        rule_id="rate_limit_backoff",
        name="Backoff on Rate Limit",
        error_patterns=["RATE_LIMIT", "429", "TOO_MANY_REQUESTS", "QUOTA"],
        action_code="retry_exponential",
        score=0.90,
        priority=85,
    ),
    ErrorCodeRule(
        rule_id="server_error_fallback",
        name="Fallback on Server Error",
        error_patterns=["HTTP_5XX", "500", "502", "503", "504", "INTERNAL_ERROR"],
        action_code="circuit_breaker",
        score=0.80,
        priority=80,
    ),
    ErrorCodeRule(
        rule_id="budget_fallback",
        name="Fallback on Budget Exceeded",
        error_patterns=["BUDGET", "COST_EXCEEDED", "QUOTA_EXCEEDED"],
        action_code="fallback_model",
        score=0.85,
        priority=75,
    ),
    ErrorCodeRule(
        rule_id="auth_notify",
        name="Notify on Auth Failure",
        error_patterns=["AUTH", "PERMISSION", "FORBIDDEN", "401", "403"],
        action_code="notify_ops",
        score=0.75,
        priority=70,
    ),
    ErrorCodeRule(
        rule_id="connection_retry",
        name="Retry on Connection Error",
        error_patterns=["CONNECTION", "NETWORK", "DNS", "RESOLVE"],
        action_code="retry_exponential",
        score=0.80,
        priority=65,
    ),
    # Medium priority - pattern-based
    HistoricalPatternRule(
        rule_id="historical_success",
        name="Follow Historical Success",
        min_occurrences=3,
        min_success_rate=0.7,
        priority=60,
        weight=1.2,  # Boost weight for historical evidence
    ),
    # Lower priority - escalation rules
    OccurrenceThresholdRule(
        rule_id="escalate_repeated",
        name="Escalate Repeated Failures",
        threshold=5,
        action_code="notify_ops",
        score=0.70,
        priority=40,
    ),
    OccurrenceThresholdRule(
        rule_id="manual_review_high",
        name="Manual Review for High Occurrence",
        threshold=10,
        action_code="manual_intervention",
        score=0.85,
        priority=35,
    ),
    # Catch-all
    ErrorCodeRule(
        rule_id="unknown_manual",
        name="Manual Review for Unknown",
        error_patterns=["UNKNOWN", "UNHANDLED", "UNEXPECTED"],
        action_code="manual_intervention",
        score=0.50,
        priority=10,
    ),
]


# =============================================================================
# Rule Engine
# =============================================================================


class RecoveryRuleEngine:
    """
    Evaluates rules against failure context to recommend recovery actions.

    Usage:
        engine = RecoveryRuleEngine()
        result = engine.evaluate(context)
        print(result.recommended_action)
    """

    def __init__(self, rules: Optional[List[Rule]] = None):
        """
        Initialize rule engine.

        Args:
            rules: Custom rules to use. If None, uses DEFAULT_RULES.
        """
        self.rules = rules or DEFAULT_RULES.copy()
        # Sort by priority (higher first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the engine."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        original_len = len(self.rules)
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        return len(self.rules) < original_len

    def evaluate(self, context: RuleContext) -> EvaluationResult:
        """
        Evaluate all rules against the context.

        Args:
            context: Rule evaluation context

        Returns:
            EvaluationResult with recommendations
        """
        start_time = time.perf_counter()

        results: List[RuleResult] = []
        matched_results: List[RuleResult] = []

        for rule in self.rules:
            try:
                result = rule.evaluate(context)
                results.append(result)

                if result.matched:
                    matched_results.append(result)

                if DEBUG_MODE:
                    logger.debug(
                        f"Rule {rule.rule_id}: matched={result.matched}, "
                        f"score={result.score:.2f}, action={result.action_code}"
                    )

            except Exception as e:
                logger.warning(f"Rule {rule.rule_id} evaluation failed: {e}")
                results.append(
                    RuleResult(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        matched=False,
                        score=0.0,
                        explanation=f"Evaluation error: {str(e)}",
                    )
                )

        # Calculate aggregated score and recommendation
        recommended_action = None
        total_score = 0.0
        confidence = 0.0
        explanations = []

        if matched_results:
            # Sort by score descending
            matched_results.sort(key=lambda r: r.score, reverse=True)

            # Use highest scoring action
            for r in matched_results:
                if r.action_code:
                    recommended_action = r.action_code
                    break

            # Calculate total score (weighted average of top 3)
            top_scores = [r.score for r in matched_results[:3]]
            total_score = sum(top_scores) / len(top_scores) if top_scores else 0.0

            # Calculate confidence with adjustments
            base_confidence = total_score
            adjustments = sum(r.confidence_adjustment for r in matched_results)
            confidence = min(1.0, max(0.0, base_confidence + adjustments))

            # Collect explanations
            explanations = [r.explanation for r in matched_results[:3]]

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        return EvaluationResult(
            rules_evaluated=results,
            recommended_action=recommended_action,
            total_score=round(total_score, 4),
            confidence=round(confidence, 4),
            explanation="; ".join(explanations) if explanations else "No rules matched",
            duration_ms=duration_ms,
        )


# =============================================================================
# Domain Classification Functions (L4 Authority)
# =============================================================================
# These functions define domain rules for error classification and recovery.
# They are the AUTHORITATIVE source for these decisions.
# L5 workers must call these functions, not implement their own heuristics.
# Reference: PIN-254 Phase A Fix (SHADOW-002, SHADOW-003)


# =============================================================================
# L4 Domain Decision Thresholds
# =============================================================================
# These thresholds are the AUTHORITATIVE source for recovery decisions.
# L5 workers must call these functions, not implement their own thresholds.
# Reference: PIN-257 Phase E-4 Extraction #3

# Auto-execute confidence threshold (L4 domain rule)
# This is the authoritative threshold for automatic recovery execution.
# Reference: PIN-254 Phase A Fix (SHADOW-001)
AUTO_EXECUTE_CONFIDENCE_THRESHOLD: float = 0.8

# Action selection threshold (L4 domain rule)
# This is the authoritative threshold for action selection.
# Reference: PIN-257 Phase E-4 Extraction #3
ACTION_SELECTION_THRESHOLD: float = 0.3


def combine_confidences(rule_confidence: float, match_confidence: float) -> float:
    """
    Combine rule and matcher confidence scores.

    This is an L4 domain decision. L5 workers must NOT implement their own formulas.

    Args:
        rule_confidence: Confidence from rule evaluation (0.0 to 1.0)
        match_confidence: Confidence from pattern matching (0.0 to 1.0)

    Returns:
        Combined confidence score (0.0 to 1.0)

    Reference: PIN-257 Phase E-4 Extraction #3
    """
    return (rule_confidence + match_confidence) / 2


def should_select_action(combined_confidence: float) -> bool:
    """
    Determine if an action should be selected based on combined confidence.

    This is an L4 domain decision. L5 workers must NOT hardcode thresholds.

    Args:
        combined_confidence: Combined confidence score (0.0 to 1.0)

    Returns:
        True if confidence meets threshold for action selection

    Reference: PIN-257 Phase E-4 Extraction #3
    """
    return combined_confidence >= ACTION_SELECTION_THRESHOLD


def should_auto_execute(confidence: float) -> bool:
    """
    Determine if a recovery action should be auto-executed based on confidence.

    This is an L4 domain decision. L5 workers must NOT hardcode thresholds.

    Args:
        confidence: Combined confidence score (0.0 to 1.0)

    Returns:
        True if confidence meets threshold for auto-execution
    """
    return confidence >= AUTO_EXECUTE_CONFIDENCE_THRESHOLD


# Error Category Classification (L4 domain rule)
# These keywords define the authoritative category classification rules.
ERROR_CATEGORY_RULES: Dict[str, List[str]] = {
    "TRANSIENT": ["timeout", "network", "connection", "dns", "unavailable", "503"],
    "PERMISSION": ["permission", "auth", "forbidden", "401", "403"],
    "RESOURCE": ["budget", "quota", "rate", "limit", "429"],
    "VALIDATION": ["validation", "schema", "invalid", "parse"],
    "INFRASTRUCTURE": ["db", "database", "sql", "postgres", "redis"],
    "PLANNER": ["llm", "claude", "openai", "anthropic", "model"],
}


def classify_error_category(error_codes: List[str]) -> str:
    """
    Classify error codes into a category.

    This is an L4 domain decision. L5 workers must NOT implement their own heuristics.

    Args:
        error_codes: List of error codes to classify

    Returns:
        Category string (TRANSIENT, PERMISSION, RESOURCE, VALIDATION, INFRASTRUCTURE, PLANNER, PERMANENT)
    """
    codes_str = " ".join(error_codes).lower()

    for category, keywords in ERROR_CATEGORY_RULES.items():
        if any(k in codes_str for k in keywords):
            return category

    return "PERMANENT"


# Recovery Mode Suggestion (L4 domain rule)
# These keywords define the authoritative recovery mode selection rules.
RECOVERY_MODE_RULES: Dict[str, List[str]] = {
    "RETRY_EXPONENTIAL": ["timeout", "network", "unavailable", "503"],
    "RETRY_WITH_JITTER": ["rate", "429", "quota"],
    "ESCALATE": ["permission", "auth", "forbidden", "401", "403"],
    "ABORT": ["validation", "invalid", "schema", "parse"],
}


def suggest_recovery_mode(error_codes: List[str]) -> str:
    """
    Suggest a recovery mode based on error codes.

    This is an L4 domain decision. L5 workers must NOT implement their own heuristics.

    Args:
        error_codes: List of error codes to analyze

    Returns:
        Recovery mode string (RETRY_EXPONENTIAL, RETRY_WITH_JITTER, ESCALATE, ABORT)
    """
    codes_str = " ".join(error_codes).lower()

    for mode, keywords in RECOVERY_MODE_RULES.items():
        if any(k in codes_str for k in keywords):
            return mode

    return "ABORT"


# =============================================================================
# Convenience Function
# =============================================================================


def evaluate_rules(
    error_code: str,
    error_message: str,
    skill_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    occurrence_count: int = 1,
    historical_matches: Optional[List[Dict[str, Any]]] = None,
    custom_rules: Optional[List[Rule]] = None,
) -> EvaluationResult:
    """
    Convenience function to evaluate rules against a failure.

    Args:
        error_code: The error code (e.g., "TIMEOUT", "HTTP_503")
        error_message: The raw error message
        skill_id: Optional skill ID
        tenant_id: Optional tenant ID
        occurrence_count: How many times this failure has occurred
        historical_matches: Historical similar failures
        custom_rules: Custom rules to add to evaluation

    Returns:
        EvaluationResult with recommendation
    """
    context = RuleContext(
        error_code=error_code,
        error_message=error_message,
        skill_id=skill_id,
        tenant_id=tenant_id,
        occurrence_count=occurrence_count,
        historical_matches=historical_matches or [],
    )

    engine = RecoveryRuleEngine()

    if custom_rules:
        for rule in custom_rules:
            engine.add_rule(rule)

    return engine.evaluate(context)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "Rule",
    "RuleContext",
    "RuleResult",
    "EvaluationResult",
    "ErrorCodeRule",
    "HistoricalPatternRule",
    "SkillSpecificRule",
    "OccurrenceThresholdRule",
    "CompositeRule",
    "RecoveryRuleEngine",
    "evaluate_rules",
    "DEFAULT_RULES",
    # L4 Domain Classification Functions (PIN-254 Phase A)
    "AUTO_EXECUTE_CONFIDENCE_THRESHOLD",
    "should_auto_execute",
    "ERROR_CATEGORY_RULES",
    "classify_error_category",
    "RECOVERY_MODE_RULES",
    "suggest_recovery_mode",
    # L4 Domain Decision Functions (PIN-257 Phase E-4 Extraction #3)
    "ACTION_SELECTION_THRESHOLD",
    "combine_confidences",
    "should_select_action",
]
