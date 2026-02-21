# capability_id: CAP-001
# Layer: L6 — Domain Driver
# NOTE: Renamed panel_consistency_checker.py → panel_consistency_driver.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Database:
#   Scope: domain (logs)
#   Models: none (pure logic)
# Role: Cross-slot consistency enforcement
# Callers: Panel adapters
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470, L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Panel Consistency Checker — Cross-slot consistency rules

Checks that output signals across slots in a panel are consistent.
Inconsistencies are violations, not warnings.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .panel_types import PanelSlotResult

logger = logging.getLogger("nova.panel_adapter.consistency")


@dataclass
class ConsistencyViolation:
    """A consistency violation between slots."""
    rule_id: str
    rule_name: str
    slots_involved: List[str]
    expected: str
    actual: str
    severity: str = "ERROR"


@dataclass
class ConsistencyCheckResult:
    """Result of consistency checking."""
    panel_id: str
    is_consistent: bool
    violations: List[ConsistencyViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PanelConsistencyChecker:
    """
    Checks cross-slot consistency within a panel.

    Usage:
        checker = PanelConsistencyChecker(rules)
        result = checker.check(panel_id, slot_results)
    """

    def __init__(self, rules: Optional[List[Dict[str, Any]]] = None):
        self.rules = rules or self._default_rules()

    def _default_rules(self) -> List[Dict[str, Any]]:
        """Default consistency rules from spec."""
        return [
            {
                "id": "CONS-001",
                "name": "active_incidents_attention_consistency",
                "description": "If active_incidents > 0 then attention_required must be true",
                "signal_a": "active_incidents",
                "signal_b": "attention_required",
                "condition": "signal_a > 0 implies signal_b == True",
            },
            {
                "id": "CONS-002",
                "name": "at_risk_system_state_consistency",
                "description": "If at_risk_runs > 0 then system_state must be STRESSED",
                "signal_a": "at_risk_runs",
                "signal_b": "system_state",
                "condition": "signal_a > 0 implies signal_b == 'STRESSED'",
            },
            {
                "id": "CONS-003",
                "name": "running_count_consistency",
                "description": "active_runs must match sum of running counts",
                "signal_a": "active_runs",
                "signal_b": "runs.by_status.running",
                "condition": "signal_a == signal_b",
            },
            {
                "id": "CONS-004",
                "name": "incident_severity_consistency",
                "description": "If active_incidents > 0 then highest_severity must not be NONE",
                "signal_a": "active_incidents",
                "signal_b": "highest_severity",
                "condition": "signal_a > 0 implies signal_b != 'NONE'",
            },
        ]

    def check(
        self,
        panel_id: str,
        slot_results: List[PanelSlotResult],
    ) -> ConsistencyCheckResult:
        """
        Check consistency across all slots in a panel.

        Returns ConsistencyCheckResult with violations if any.
        """
        violations: List[ConsistencyViolation] = []
        warnings: List[str] = []

        # Collect all output signals across slots
        all_signals: Dict[str, Any] = {}
        signal_sources: Dict[str, str] = {}  # signal_id -> slot_id

        for slot_result in slot_results:
            for sig_id, sig_val in slot_result.output_signals.items():
                if sig_id in all_signals:
                    # Signal exists in multiple slots - check consistency
                    if all_signals[sig_id] != sig_val:
                        violations.append(ConsistencyViolation(
                            rule_id="CONS-DUP",
                            rule_name="duplicate_signal_mismatch",
                            slots_involved=[signal_sources[sig_id], slot_result.slot_id],
                            expected=f"{sig_id}={all_signals[sig_id]} (from {signal_sources[sig_id]})",
                            actual=f"{sig_id}={sig_val} (from {slot_result.slot_id})",
                        ))
                else:
                    all_signals[sig_id] = sig_val
                    signal_sources[sig_id] = slot_result.slot_id

        # Check each rule
        for rule in self.rules:
            violation = self._check_rule(rule, all_signals, signal_sources)
            if violation:
                violations.append(violation)

        return ConsistencyCheckResult(
            panel_id=panel_id,
            is_consistent=len(violations) == 0,
            violations=violations,
            warnings=warnings,
        )

    def _check_rule(
        self,
        rule: Dict[str, Any],
        signals: Dict[str, Any],
        sources: Dict[str, str],
    ) -> Optional[ConsistencyViolation]:
        """Check a single consistency rule."""
        signal_a_id = rule.get("signal_a", "")
        signal_b_id = rule.get("signal_b", "")
        condition = rule.get("condition", "")

        # Get signal values
        signal_a = signals.get(signal_a_id)
        signal_b = signals.get(signal_b_id)

        # Skip if signals not present
        if signal_a is None or signal_b is None:
            return None

        # Evaluate condition
        try:
            is_valid = self._evaluate_condition(condition, signal_a, signal_b)
            if not is_valid:
                slots = []
                if signal_a_id in sources:
                    slots.append(sources[signal_a_id])
                if signal_b_id in sources and sources[signal_b_id] not in slots:
                    slots.append(sources[signal_b_id])

                return ConsistencyViolation(
                    rule_id=rule.get("id", "UNKNOWN"),
                    rule_name=rule.get("name", ""),
                    slots_involved=slots,
                    expected=rule.get("description", condition),
                    actual=f"{signal_a_id}={signal_a}, {signal_b_id}={signal_b}",
                )
        except Exception as e:
            logger.warning(f"Failed to evaluate rule {rule.get('id')}: {e}")

        return None

    def _evaluate_condition(
        self,
        condition: str,
        signal_a: Any,
        signal_b: Any,
    ) -> bool:
        """Evaluate a condition expression."""
        # Simple pattern matching for common conditions
        if "implies" in condition:
            # "signal_a > 0 implies signal_b == True"
            parts = condition.split(" implies ")
            if len(parts) == 2:
                antecedent = self._eval_expr(parts[0].strip(), signal_a, signal_b)
                consequent = self._eval_expr(parts[1].strip(), signal_a, signal_b)
                # P implies Q = not P or Q
                return (not antecedent) or consequent

        if "==" in condition:
            # "signal_a == signal_b"
            return signal_a == signal_b

        if "!=" in condition:
            # "signal_a != signal_b"
            return signal_a != signal_b

        # Default: cannot evaluate
        logger.warning(f"Cannot evaluate condition: {condition}")
        return True

    def _eval_expr(self, expr: str, signal_a: Any, signal_b: Any) -> bool:
        """Evaluate a simple expression."""
        expr = expr.strip()

        # Replace signal references
        if "signal_a" in expr:
            if "> 0" in expr:
                return signal_a > 0 if isinstance(signal_a, (int, float)) else bool(signal_a)
            if "== 0" in expr:
                return signal_a == 0 if isinstance(signal_a, (int, float)) else not bool(signal_a)

        if "signal_b" in expr:
            if "== True" in expr or "== true" in expr:
                return signal_b is True
            if "== False" in expr or "== false" in expr:
                return signal_b is False
            if "== 'STRESSED'" in expr:
                return signal_b == "STRESSED"
            if "!= 'NONE'" in expr:
                return signal_b != "NONE"

        return True


# Factory
def create_consistency_checker(
    rules: Optional[List[Dict[str, Any]]] = None,
) -> PanelConsistencyChecker:
    """Create consistency checker with optional custom rules."""
    return PanelConsistencyChecker(rules)
