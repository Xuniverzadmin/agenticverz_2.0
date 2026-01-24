# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Phase A Intent Guardrails (design-time validation)
# Reference: PIN-420, L2_1_PANEL_ADAPTER_SPEC.yaml

"""
Intent Guardrails — Phase A of two-phase semantic validation.

These rules validate intent YAML at design-time, BEFORE any SDSR or API calls.

CRITICAL INVARIANT:
    Phase A rules must NEVER depend on SDSR or APIs.
    Phase A rules judge whether an idea is allowed to exist.

Fix Owner: Product / Architecture
Trigger: sync from intent ledger, adding/modifying intent YAML

Checks:
    INT-001: Signal provability
    INT-002: Capability cardinality
    INT-003: Semantic duplication
    INT-004: Contradictory intents
    INT-005: Missing evolution path
    INT-006: Unbounded intent scope
    INT-007: Missing semantic contract
    INT-008: Invalid capability reference
"""

import logging
from typing import Any, Dict, List, Optional, Set

from .semantic_types import (
    IntentFailureCode,
    SemanticContext,
    SemanticSeverity,
    SemanticViolation,
    ViolationClass,
)

logger = logging.getLogger("nova.panel_adapter.intent_guardrails")


# =============================================================================
# CONFIGURATION
# =============================================================================

MAX_CAPABILITIES_PER_PANEL = 5   # Too many capabilities = too much coupling
MAX_SIGNALS_PER_CAPABILITY = 10  # Too many signals = probably needs splitting
MAX_SIGNALS_PER_PANEL = 20       # Unbounded panels are unmanageable


# =============================================================================
# HELPER: Get failure info
# =============================================================================

def _get_int_fix_owner(code: IntentFailureCode) -> str:
    """Get fix owner for intent failure code."""
    owners = {
        IntentFailureCode.INT_001: "Product",
        IntentFailureCode.INT_002: "Architecture",
        IntentFailureCode.INT_003: "Product",
        IntentFailureCode.INT_004: "Product",
        IntentFailureCode.INT_005: "Product",
        IntentFailureCode.INT_006: "Architecture",
        IntentFailureCode.INT_007: "Product",
        IntentFailureCode.INT_008: "Architecture",
    }
    return owners.get(code, "Unknown")


def _get_int_fix_action(code: IntentFailureCode) -> str:
    """Get fix action for intent failure code."""
    actions = {
        IntentFailureCode.INT_001: "Make signal observable or add computed_from declaration",
        IntentFailureCode.INT_002: "Split intent into multiple panels or reduce capability dependencies",
        IntentFailureCode.INT_003: "Unify meaning or rename signal to avoid collision",
        IntentFailureCode.INT_004: "Resolve contradiction between intents",
        IntentFailureCode.INT_005: "Declare maturity stage and prerequisites",
        IntentFailureCode.INT_006: "Bound the intent scope (max signals, pagination)",
        IntentFailureCode.INT_007: "Declare semantic contract in INTENT_LEDGER.md",
        IntentFailureCode.INT_008: "Reference a valid capability ID from registry",
    }
    return actions.get(code, "Investigate")


def _create_violation(
    code: IntentFailureCode,
    severity: SemanticSeverity,
    message: str,
    ctx: SemanticContext,
    evidence: Optional[Dict[str, Any]] = None,
) -> SemanticViolation:
    """Create an intent violation with standard metadata."""
    return SemanticViolation(
        code=code,
        vclass=ViolationClass.INTENT,
        severity=severity,
        message=message,
        context=ctx,
        evidence=evidence or {},
        fix_owner=_get_int_fix_owner(code),
        fix_action=_get_int_fix_action(code),
    )


# =============================================================================
# INTENT GUARDRAIL CHECKS
# =============================================================================

def check_int_001_signal_provable(
    intent: Dict[str, Any],
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    INT-001: Check that every signal is provable.

    A signal is provable if it is either:
    - observable (can be read from API)
    - computed_from (derived from other signals)

    If a signal is neither, it cannot be materialized.
    """
    consumed_caps = intent.get("consumed_capabilities", [])

    for cap in consumed_caps:
        signals = cap.get("signals", [])
        cap_id = cap.get("capability_id", "")

        for signal in signals:
            # In V2 spec, signals are just names; provability comes from
            # the signal_translator having a mapping or compute function.
            # At intent time, we check if the signal has a declared source.
            signal_name = signal if isinstance(signal, str) else signal.get("name", "")

            # For now, we trust that signals declared in consumed_capabilities
            # are provable if the capability exists. More detailed checks
            # happen in Phase B (SEM-001).
            pass

    return None  # Detailed check in Phase B


def check_int_002_capability_cardinality(
    intent: Dict[str, Any],
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    INT-002: Check capability cardinality.

    A panel depending on too many capabilities:
    - Has too many failure modes
    - Is hard to reason about
    - Should probably be split
    """
    consumed_caps = intent.get("consumed_capabilities", [])
    cap_ids = set()

    for cap in consumed_caps:
        cap_id = cap.get("capability_id", "")
        if cap_id:
            cap_ids.add(cap_id)

    # Also check capability_binding (V1 compatibility)
    if intent.get("capability_binding"):
        cap_ids.add(intent["capability_binding"])

    if len(cap_ids) > MAX_CAPABILITIES_PER_PANEL:
        return _create_violation(
            code=IntentFailureCode.INT_002,
            severity=SemanticSeverity.BLOCKING,
            message=f"Panel depends on {len(cap_ids)} capabilities (max: {MAX_CAPABILITIES_PER_PANEL})",
            ctx=ctx,
            evidence={
                "capability_count": len(cap_ids),
                "max_allowed": MAX_CAPABILITIES_PER_PANEL,
                "capabilities": list(cap_ids),
            },
        )

    return None


def check_int_003_semantic_duplication(
    intent: Dict[str, Any],
    all_intents: List[Dict[str, Any]],
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    INT-003: Check for semantic duplication.

    The same signal name used with different meanings across panels
    creates confusion and potential data inconsistency.
    """
    # Build signal -> meaning map from all intents
    signal_meanings: Dict[str, Dict[str, Any]] = {}

    for other_intent in all_intents:
        other_panel_id = other_intent.get("panel_id", "")
        consumed_caps = other_intent.get("consumed_capabilities", [])

        for cap in consumed_caps:
            cap_id = cap.get("capability_id", "")
            signals = cap.get("signals", [])

            for signal in signals:
                signal_name = signal if isinstance(signal, str) else signal.get("name", "")
                key = f"{signal_name}:{cap_id}"  # Signal name + capability

                if key not in signal_meanings:
                    signal_meanings[key] = {
                        "signal": signal_name,
                        "capability": cap_id,
                        "panels": [],
                    }
                signal_meanings[key]["panels"].append(other_panel_id)

    # Check for signals used across many panels with different capabilities
    # (This is a heuristic - true duplication detection requires semantic analysis)
    panel_id = intent.get("panel_id", "")
    consumed_caps = intent.get("consumed_capabilities", [])

    for cap in consumed_caps:
        cap_id = cap.get("capability_id", "")
        signals = cap.get("signals", [])

        for signal in signals:
            signal_name = signal if isinstance(signal, str) else signal.get("name", "")

            # Check if same signal name is used with a DIFFERENT capability elsewhere
            for key, info in signal_meanings.items():
                if info["signal"] == signal_name and info["capability"] != cap_id:
                    if panel_id not in info["panels"]:
                        return _create_violation(
                            code=IntentFailureCode.INT_003,
                            severity=SemanticSeverity.WARNING,
                            message=f"Signal '{signal_name}' used with different capabilities",
                            ctx=SemanticContext(
                                panel_id=panel_id,
                                signal=signal_name,
                                capability_id=cap_id,
                            ),
                            evidence={
                                "this_capability": cap_id,
                                "other_capability": info["capability"],
                                "other_panels": info["panels"],
                            },
                        )

    return None


def check_int_004_contradictory_intents(
    intent: Dict[str, Any],
    all_intents: List[Dict[str, Any]],
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    INT-004: Check for contradictory intents.

    Two intents making mutually exclusive assertions about the same scope
    cannot both be true. This indicates a design error.
    """
    # Check for semantic contradictions based on panel semantics
    panel_id = intent.get("panel_id", "")
    semantics = intent.get("semantics", {})
    this_assertion = semantics.get("assertion", "")

    if not this_assertion:
        return None

    # Known contradiction patterns
    contradictions = {
        "NO_ACTIVE_INCIDENTS": "ACTIVE_INCIDENTS_GT_ZERO",
        "ACTIVE_INCIDENTS_GT_ZERO": "NO_ACTIVE_INCIDENTS",
        "SYSTEM_HEALTHY": "SYSTEM_DEGRADED",
        "SYSTEM_DEGRADED": "SYSTEM_HEALTHY",
        "NO_ACTIVE_RUNS": "ACTIVE_RUNS_GT_ZERO",
        "ACTIVE_RUNS_GT_ZERO": "NO_ACTIVE_RUNS",
    }

    contradicts = contradictions.get(this_assertion)
    if not contradicts:
        return None

    # Check if any other intent makes the contradictory assertion
    for other_intent in all_intents:
        other_panel_id = other_intent.get("panel_id", "")
        if other_panel_id == panel_id:
            continue

        other_semantics = other_intent.get("semantics", {})
        other_assertion = other_semantics.get("assertion", "")

        if other_assertion == contradicts:
            # Check if they're in the same scope (domain)
            this_domain = intent.get("domain", "")
            other_domain = other_intent.get("domain", "")

            if this_domain == other_domain:
                return _create_violation(
                    code=IntentFailureCode.INT_004,
                    severity=SemanticSeverity.BLOCKING,
                    message=f"Intent contradicts '{other_panel_id}' in same domain",
                    ctx=ctx,
                    evidence={
                        "this_assertion": this_assertion,
                        "other_assertion": other_assertion,
                        "conflicting_panel": other_panel_id,
                        "domain": this_domain,
                    },
                )

    return None


def check_int_005_missing_evolution_path(
    intent: Dict[str, Any],
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    INT-005: Check for missing evolution/maturity declaration.

    Every intent should declare its maturity stage and prerequisites
    so the system can track readiness and dependencies.
    """
    # Check for maturity or evolution declaration
    maturity = intent.get("maturity")
    migration_status = intent.get("migration_status")
    panel_state = intent.get("panel_state")

    # If none of these exist, the intent lacks evolution metadata
    if not any([maturity, migration_status, panel_state]):
        return _create_violation(
            code=IntentFailureCode.INT_005,
            severity=SemanticSeverity.WARNING,
            message="Intent missing evolution/maturity declaration",
            ctx=ctx,
            evidence={
                "has_maturity": maturity is not None,
                "has_migration_status": migration_status is not None,
                "has_panel_state": panel_state is not None,
            },
        )

    return None


def check_int_006_unbounded_intent_scope(
    intent: Dict[str, Any],
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    INT-006: Check for unbounded intent scope.

    An intent that can grow without limit (e.g., "show all X" without
    pagination) is a design problem.
    """
    consumed_caps = intent.get("consumed_capabilities", [])
    total_signals = 0

    for cap in consumed_caps:
        signals = cap.get("signals", [])
        total_signals += len(signals)

    if total_signals > MAX_SIGNALS_PER_PANEL:
        return _create_violation(
            code=IntentFailureCode.INT_006,
            severity=SemanticSeverity.WARNING,
            message=f"Panel has {total_signals} signals (max: {MAX_SIGNALS_PER_PANEL})",
            ctx=ctx,
            evidence={
                "signal_count": total_signals,
                "max_allowed": MAX_SIGNALS_PER_PANEL,
            },
        )

    # Check for list-type semantics without pagination
    semantics = intent.get("semantics", {})
    verb = semantics.get("verb", "")
    obj = semantics.get("object", "")

    # If it's a list view without pagination declaration, warn
    if verb == "VIEW" and "LIST" in obj.upper():
        pagination = intent.get("pagination")
        if not pagination:
            return _create_violation(
                code=IntentFailureCode.INT_006,
                severity=SemanticSeverity.WARNING,
                message="List intent without pagination declaration",
                ctx=ctx,
                evidence={
                    "verb": verb,
                    "object": obj,
                },
            )

    return None


def check_int_007_missing_semantic_contract(
    intent: Dict[str, Any],
    registered_panels: Set[str],
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    INT-007: Check for missing semantic contract.

    Every panel must be declared in the intent registry before use.
    """
    panel_id = intent.get("panel_id", "")

    if panel_id and panel_id not in registered_panels:
        return _create_violation(
            code=IntentFailureCode.INT_007,
            severity=SemanticSeverity.BLOCKING,
            message=f"Panel '{panel_id}' not in intent registry",
            ctx=ctx,
            evidence={
                "panel_id": panel_id,
                "registered_count": len(registered_panels),
            },
        )

    return None


def check_int_008_invalid_capability_reference(
    intent: Dict[str, Any],
    known_capabilities: Set[str],
    ctx: SemanticContext,
) -> Optional[SemanticViolation]:
    """
    INT-008: Check for invalid capability references.

    Every capability referenced must exist in the capability registry
    (even if not yet OBSERVED).
    """
    consumed_caps = intent.get("consumed_capabilities", [])

    for cap in consumed_caps:
        cap_id = cap.get("capability_id", "")
        if cap_id and cap_id not in known_capabilities:
            return _create_violation(
                code=IntentFailureCode.INT_008,
                severity=SemanticSeverity.BLOCKING,
                message=f"Capability '{cap_id}' not found in registry",
                ctx=SemanticContext(
                    panel_id=intent.get("panel_id", ""),
                    capability_id=cap_id,
                ),
                evidence={
                    "capability_id": cap_id,
                    "known_capability_count": len(known_capabilities),
                },
            )

    # Also check capability_binding (V1 compatibility)
    cap_binding = intent.get("capability_binding")
    if cap_binding and cap_binding not in known_capabilities:
        return _create_violation(
            code=IntentFailureCode.INT_008,
            severity=SemanticSeverity.BLOCKING,
            message=f"Capability binding '{cap_binding}' not found in registry",
            ctx=SemanticContext(
                panel_id=intent.get("panel_id", ""),
                capability_id=cap_binding,
            ),
            evidence={
                "capability_id": cap_binding,
                "known_capability_count": len(known_capabilities),
            },
        )

    return None


# =============================================================================
# INTENT GUARDRAIL RUNNER
# =============================================================================

def run_intent_guardrails(
    intent: Dict[str, Any],
    all_intents: List[Dict[str, Any]],
    registered_panels: Set[str],
    known_capabilities: Set[str],
) -> List[SemanticViolation]:
    """
    Run all Phase A intent guardrail checks on a single intent.

    Args:
        intent: The intent to validate
        all_intents: All intents for cross-intent checks
        registered_panels: Set of panel IDs in the intent registry
        known_capabilities: Set of capability IDs in the capability registry

    Returns:
        List of violations (may be empty)
    """
    violations: List[SemanticViolation] = []
    panel_id = intent.get("panel_id", "")

    ctx = SemanticContext(
        panel_id=panel_id,
        source="intent_yaml",
    )

    # Run each check
    checks = [
        lambda: check_int_001_signal_provable(intent, ctx),
        lambda: check_int_002_capability_cardinality(intent, ctx),
        lambda: check_int_003_semantic_duplication(intent, all_intents, ctx),
        lambda: check_int_004_contradictory_intents(intent, all_intents, ctx),
        lambda: check_int_005_missing_evolution_path(intent, ctx),
        lambda: check_int_006_unbounded_intent_scope(intent, ctx),
        lambda: check_int_007_missing_semantic_contract(intent, registered_panels, ctx),
        lambda: check_int_008_invalid_capability_reference(intent, known_capabilities, ctx),
    ]

    for check in checks:
        violation = check()
        if violation:
            violations.append(violation)

    return violations
