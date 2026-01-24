"""
Memory Update Rules Engine - M7 Implementation

Provides rule-based transformations for memory updates:
- Schema validation
- Data sanitization
- Transformation rules
- Merge strategies

Usage:
    from app.memory.update_rules import UpdateRulesEngine

    engine = UpdateRulesEngine()
    engine.add_rule("config:*", schema=ConfigSchema, merge="deep")
    transformed = await engine.apply("tenant", "config:rate_limits", data)
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Pattern

from prometheus_client import Counter

logger = logging.getLogger("nova.memory.update_rules")

# =============================================================================
# Prometheus Metrics
# =============================================================================

RULES_APPLIED = Counter("memory_update_rules_applied_total", "Memory update rules applied", ["rule_name", "status"])

RULES_ERRORS = Counter("memory_update_rules_errors_total", "Memory update rules errors", ["rule_name", "error_type"])


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class UpdateRule:
    """
    Single update rule definition.

    Attributes:
        name: Rule identifier
        pattern: Key pattern (glob or regex)
        schema: Optional Pydantic model for validation
        transform: Optional transformation function
        merge_strategy: How to merge with existing data
        sanitizers: List of sanitization functions
        enabled: Whether rule is active
    """

    name: str
    pattern: str
    schema: Optional[Any] = None  # Pydantic model
    transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    merge_strategy: str = "replace"  # replace, deep_merge, append, increment
    sanitizers: List[Callable[[Any], Any]] = field(default_factory=list)
    enabled: bool = True
    _compiled: Optional[Pattern] = field(default=None, repr=False)

    def __post_init__(self):
        """Compile pattern to regex."""
        # Convert glob pattern to regex
        regex_pattern = self.pattern.replace("*", ".*").replace("?", ".")
        self._compiled = re.compile(f"^{regex_pattern}$")

    def matches(self, key: str) -> bool:
        """Check if key matches this rule."""
        return self._compiled.match(key) is not None


@dataclass
class RuleResult:
    """Result of rule application."""

    rule_name: str
    applied: bool
    value: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# Built-in Sanitizers
# =============================================================================


def sanitize_strings(value: Any) -> Any:
    """Strip whitespace from string values."""
    if isinstance(value, str):
        return value.strip()
    elif isinstance(value, dict):
        return {k: sanitize_strings(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_strings(v) for v in value]
    return value


def sanitize_nulls(value: Any) -> Any:
    """Remove null/None values from dicts."""
    if isinstance(value, dict):
        return {k: sanitize_nulls(v) for k, v in value.items() if v is not None}
    elif isinstance(value, list):
        return [sanitize_nulls(v) for v in value if v is not None]
    return value


def sanitize_timestamps(value: Any) -> Any:
    """Convert timestamp strings to ISO format."""
    if isinstance(value, str):
        # Try to parse and reformat datetime strings
        try:
            # Common formats
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
            ]:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.replace(tzinfo=timezone.utc).isoformat()
                except ValueError:
                    continue
        except Exception:
            pass
        return value
    elif isinstance(value, dict):
        return {k: sanitize_timestamps(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_timestamps(v) for v in value]
    return value


# =============================================================================
# Merge Strategies
# =============================================================================


def deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Values in update override base, but nested dicts are merged recursively.
    """
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def append_lists(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append list values from update to base.

    Non-list values are replaced.
    """
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = result[key] + value
        else:
            result[key] = value
    return result


def increment_numbers(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Increment numeric values.

    Useful for counters and aggregations.
    """
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], (int, float)) and isinstance(value, (int, float)):
            result[key] = result[key] + value
        else:
            result[key] = value
    return result


MERGE_STRATEGIES: Dict[str, Callable] = {
    "replace": lambda base, update: update,
    "deep_merge": deep_merge,
    "append": append_lists,
    "increment": increment_numbers,
}


# =============================================================================
# Update Rules Engine
# =============================================================================


class UpdateRulesEngine:
    """
    Engine for applying update rules to memory values.

    Features:
    - Pattern-based rule matching
    - Schema validation
    - Data transformation
    - Multiple merge strategies
    - Sanitization pipeline
    """

    def __init__(self):
        """Initialize rules engine."""
        self._rules: List[UpdateRule] = []
        self._default_sanitizers: List[Callable] = [
            sanitize_strings,
            sanitize_nulls,
        ]

    def add_rule(
        self,
        name: str,
        pattern: str,
        schema: Optional[Any] = None,
        transform: Optional[Callable] = None,
        merge_strategy: str = "replace",
        sanitizers: Optional[List[Callable]] = None,
    ) -> None:
        """
        Add an update rule.

        Args:
            name: Rule identifier
            pattern: Key pattern (supports * and ? wildcards)
            schema: Optional Pydantic model for validation
            transform: Optional transformation function
            merge_strategy: Merge strategy (replace, deep_merge, append, increment)
            sanitizers: Additional sanitization functions
        """
        rule = UpdateRule(
            name=name,
            pattern=pattern,
            schema=schema,
            transform=transform,
            merge_strategy=merge_strategy,
            sanitizers=sanitizers or [],
        )
        self._rules.append(rule)
        logger.info(f"Added update rule: {name} for pattern {pattern}")

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name."""
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                self._rules.pop(i)
                logger.info(f"Removed update rule: {name}")
                return True
        return False

    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all rules as dicts."""
        return [
            {
                "name": r.name,
                "pattern": r.pattern,
                "merge_strategy": r.merge_strategy,
                "enabled": r.enabled,
                "has_schema": r.schema is not None,
                "has_transform": r.transform is not None,
            }
            for r in self._rules
        ]

    async def apply(
        self, tenant_id: str, key: str, value: Dict[str, Any], existing: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply all matching rules to a value.

        Args:
            tenant_id: Tenant context
            key: Memory key
            value: Value to transform
            existing: Optional existing value for merge

        Returns:
            Transformed value
        """
        result = value.copy()

        # Apply default sanitizers
        for sanitizer in self._default_sanitizers:
            try:
                result = sanitizer(result)
            except Exception as e:
                logger.warning(f"Default sanitizer error: {e}")

        # Find and apply matching rules
        for rule in self._rules:
            if not rule.enabled or not rule.matches(key):
                continue

            try:
                result = self._apply_rule(rule, result, existing)
                RULES_APPLIED.labels(rule_name=rule.name, status="success").inc()
                logger.debug(f"Applied rule {rule.name} to {key}")

            except Exception as e:
                RULES_APPLIED.labels(rule_name=rule.name, status="error").inc()
                RULES_ERRORS.labels(rule_name=rule.name, error_type=type(e).__name__).inc()
                logger.warning(f"Rule {rule.name} error: {e}")
                # Continue with other rules

        return result

    def _apply_rule(
        self, rule: UpdateRule, value: Dict[str, Any], existing: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Apply a single rule."""
        result = value

        # Apply custom sanitizers
        for sanitizer in rule.sanitizers:
            result = sanitizer(result)

        # Validate against schema
        if rule.schema:
            try:
                validated = rule.schema.model_validate(result)
                result = validated.model_dump()
            except Exception as e:
                raise ValueError(f"Schema validation failed: {e}")

        # Apply transformation
        if rule.transform:
            result = rule.transform(result)

        # Apply merge strategy
        if existing and rule.merge_strategy in MERGE_STRATEGIES:
            merge_fn = MERGE_STRATEGIES[rule.merge_strategy]
            result = merge_fn(existing, result)

        return result

    def validate(self, key: str, value: Dict[str, Any]) -> List[str]:
        """
        Validate a value against matching rules without applying.

        Returns list of validation errors.
        """
        errors = []

        for rule in self._rules:
            if not rule.enabled or not rule.matches(key):
                continue

            if rule.schema:
                try:
                    rule.schema.model_validate(value)
                except Exception as e:
                    errors.append(f"{rule.name}: {e}")

        return errors


# =============================================================================
# Pre-configured Rules
# =============================================================================


def create_default_engine() -> UpdateRulesEngine:
    """Create engine with default rules."""
    engine = UpdateRulesEngine()

    # Config entries use deep merge
    engine.add_rule(name="config_merge", pattern="config:*", merge_strategy="deep_merge")

    # Counter entries use increment
    engine.add_rule(name="counter_increment", pattern="counter:*", merge_strategy="increment")

    # Log entries use append
    engine.add_rule(name="log_append", pattern="log:*", merge_strategy="append")

    # Agent preferences use deep merge
    engine.add_rule(name="agent_preferences", pattern="agent:*:preferences", merge_strategy="deep_merge")

    return engine


# =============================================================================
# Global Instance
# =============================================================================

_engine: Optional[UpdateRulesEngine] = None


def get_update_rules_engine() -> UpdateRulesEngine:
    """Get or create global rules engine."""
    global _engine
    if _engine is None:
        _engine = create_default_engine()
    return _engine


def init_update_rules_engine() -> UpdateRulesEngine:
    """Initialize global rules engine."""
    global _engine
    _engine = create_default_engine()
    return _engine
