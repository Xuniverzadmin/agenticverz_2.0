# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Semantic failure taxonomy and fix guidance for incidents domain
# Callers: Panel adapters (L3), incident engines (L4)
# Allowed Imports: sibling types only
# Forbidden Imports: L1, L2, L3, L5, L6, sqlalchemy
# Reference: PIN-420, INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Phase II.1
#
# RECLASSIFICATION NOTE (2026-01-24):
# This file was previously declared as L2.1 (Panel Adapter Layer).
# Reclassified to L4 because it contains domain-specific failure taxonomy
# for the incidents domain. Pure data structures, no DB access.

"""
Semantic Failures — Canonical failure taxonomy for two-phase validation.

Two Phases:
- Phase A: Intent Guardrails (INT-*) — design-time, human-facing
- Phase B: Semantic Reality (SEM-*) — proof-time, system-facing

Each failure code has:
- Name: Human-readable name
- Class: INTENT_VIOLATION or SEMANTIC_VIOLATION
- Severity: BLOCKING or WARNING
- Fix Owner: Who is responsible for fixing
- Fix Action: What action to take

This taxonomy ensures violations are actionable, not just noise.
"""

from typing import Any, Dict, Union

from .semantic_types import (
    FailureCode,
    IntentFailureCode,
    SemanticFailureCode,
    SemanticSeverity,
    ViolationClass,
)


# =============================================================================
# COMBINED FAILURE TAXONOMY (INT-* and SEM-*)
# =============================================================================
# Format: code -> {name, class, severity, fix_owner, fix_action, description}
#
# Phase A Fix Owners (Intent Guardrails):
#   - "Product" - Product/design decision needed
#   - "Architecture" - Architectural change needed
#
# Phase B Fix Owners (Semantic Reality):
#   - "Panel Adapter" - panel_signal_translator.py or panel spec
#   - "Backend" - API endpoint or response schema
#   - "SDSR" - Need to run SDSR scenario
#   - "Intent" - INTENT_LEDGER.md needs update
#   - "System" - Cross-component issue
# =============================================================================

FAILURE_TAXONOMY: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # PHASE A: Intent Guardrails (INT-*) — Design-time, Human-facing
    # =========================================================================
    "INT-001": {
        "name": "SIGNAL_NOT_PROVABLE",
        "class": ViolationClass.INTENT,
        "severity": SemanticSeverity.BLOCKING,
        "fix_owner": "Product",
        "fix_action": "Make signal observable or add computed_from declaration",
        "description": (
            "A signal is declared but is neither observable nor computable. "
            "Every signal must have a source of truth."
        ),
    },
    "INT-002": {
        "name": "CAPABILITY_CARDINALITY_EXCEEDED",
        "class": ViolationClass.INTENT,
        "severity": SemanticSeverity.BLOCKING,
        "fix_owner": "Architecture",
        "fix_action": "Split intent into multiple panels or reduce capability dependencies",
        "description": (
            "A panel depends on too many capabilities. "
            "This creates excessive coupling and failure modes."
        ),
    },
    "INT-003": {
        "name": "SEMANTIC_DUPLICATION",
        "class": ViolationClass.INTENT,
        "severity": SemanticSeverity.WARNING,
        "fix_owner": "Product",
        "fix_action": "Unify meaning or rename signal to avoid collision",
        "description": (
            "The same signal name is used with different meanings across panels. "
            "This creates confusion and potential data inconsistency."
        ),
    },
    "INT-004": {
        "name": "CONTRADICTORY_INTENTS",
        "class": ViolationClass.INTENT,
        "severity": SemanticSeverity.BLOCKING,
        "fix_owner": "Product",
        "fix_action": "Resolve contradiction between intents",
        "description": (
            "Two intents make mutually exclusive assertions in the same scope. "
            "They cannot both be true."
        ),
    },
    "INT-005": {
        "name": "MISSING_EVOLUTION_PATH",
        "class": ViolationClass.INTENT,
        "severity": SemanticSeverity.WARNING,
        "fix_owner": "Product",
        "fix_action": "Declare maturity stage and prerequisites",
        "description": (
            "An intent lacks evolution/maturity declaration. "
            "The system cannot track readiness or dependencies."
        ),
    },
    "INT-006": {
        "name": "UNBOUNDED_INTENT_SCOPE",
        "class": ViolationClass.INTENT,
        "severity": SemanticSeverity.WARNING,
        "fix_owner": "Architecture",
        "fix_action": "Bound the intent scope (max signals, pagination)",
        "description": (
            "An intent can grow without limit. "
            "Unbounded intents are unmanageable and should be paginated or split."
        ),
    },
    "INT-007": {
        "name": "MISSING_SEMANTIC_CONTRACT",
        "class": ViolationClass.INTENT,
        "severity": SemanticSeverity.BLOCKING,
        "fix_owner": "Product",
        "fix_action": "Declare semantic contract in INTENT_LEDGER.md",
        "description": (
            "A panel is referenced but has no semantic contract. "
            "Every panel must be declared in the intent registry."
        ),
    },
    "INT-008": {
        "name": "INVALID_CAPABILITY_REFERENCE",
        "class": ViolationClass.INTENT,
        "severity": SemanticSeverity.BLOCKING,
        "fix_owner": "Architecture",
        "fix_action": "Reference a valid capability ID from registry",
        "description": (
            "An intent references a capability that doesn't exist. "
            "Every capability must be registered before use."
        ),
    },

    # =========================================================================
    # PHASE B: Semantic Reality (SEM-*) — Proof-time, System-facing
    # =========================================================================
    "SEM-001": {
        "name": "SIGNAL_NOT_TRANSLATED",
        "class": ViolationClass.SEMANTIC,
        "severity": SemanticSeverity.BLOCKING,
        "fix_owner": "Panel Adapter",
        "fix_action": "Add signal translation to SIGNAL_TRANSLATIONS in panel_signal_translator.py",
        "description": (
            "A signal is declared in the panel spec but has no translation mapping. "
            "The adapter cannot convert spec signal name to API field name."
        ),
    },
    "SEM-002": {
        "name": "CAPABILITY_NOT_OBSERVED",
        "class": ViolationClass.SEMANTIC,
        "severity": SemanticSeverity.BLOCKING,
        "fix_owner": "SDSR",
        "fix_action": "Run SDSR scenario to observe capability, OR downgrade panel to DRAFT state",
        "description": (
            "A capability is consumed by a panel but is not OBSERVED or TRUSTED. "
            "Only OBSERVED/TRUSTED capabilities may be called. "
            "DECLARED/ASSUMED capabilities require SDSR verification first."
        ),
    },
    "SEM-003": {
        "name": "API_FIELD_MISSING",
        "class": ViolationClass.SEMANTIC,
        "severity": SemanticSeverity.BLOCKING,
        "fix_owner": "Backend",
        "fix_action": "Add field to API response OR correct the translation mapping",
        "description": (
            "The translated API field does not exist in the API response. "
            "Either the API needs to return this field, or the translation is wrong."
        ),
    },
    "SEM-004": {
        "name": "SIGNAL_TYPE_MISMATCH",
        "class": ViolationClass.SEMANTIC,
        "severity": SemanticSeverity.WARNING,
        "fix_owner": "Backend",
        "fix_action": "Fix API response schema OR update expected type in spec",
        "description": (
            "The signal value type does not match the expected type. "
            "Example: expected integer but got string."
        ),
    },
    "SEM-005": {
        "name": "SEMANTIC_CONTRACT_MISSING",
        "class": ViolationClass.SEMANTIC,
        "severity": SemanticSeverity.BLOCKING,
        "fix_owner": "Intent",
        "fix_action": "Declare signal in INTENT_LEDGER.md OR remove usage from panel",
        "description": (
            "A signal is used but has no semantic contract. "
            "Every signal must be declared in intent before use."
        ),
    },
    "SEM-006": {
        "name": "CROSS_PANEL_INCONSISTENCY",
        "class": ViolationClass.SEMANTIC,
        "severity": SemanticSeverity.WARNING,
        "fix_owner": "System",
        "fix_action": "Resolve semantic contradiction between panels",
        "description": (
            "Two panels show contradictory information. "
            "Example: Overview shows 'attention required' but Activity shows '0 at-risk runs'."
        ),
    },
    "SEM-007": {
        "name": "REQUIRED_SIGNAL_NO_DEFAULT",
        "class": ViolationClass.SEMANTIC,
        "severity": SemanticSeverity.WARNING,
        "fix_owner": "Panel Adapter",
        "fix_action": "Add appropriate default value in SIGNAL_TRANSLATIONS",
        "description": (
            "A required signal has no default value defined. "
            "If the API field is missing, the signal will be None instead of a safe default."
        ),
    },
    "SEM-008": {
        "name": "COMPUTED_SIGNAL_NO_FUNCTION",
        "class": ViolationClass.SEMANTIC,
        "severity": SemanticSeverity.BLOCKING,
        "fix_owner": "Panel Adapter",
        "fix_action": "Add compute function to COMPUTED_SIGNALS in panel_signal_translator.py",
        "description": (
            "A signal is marked as computed but has no compute function. "
            "Computed signals require a function that derives the value from API response."
        ),
    },
}

# Backwards compatibility alias
SEMANTIC_FAILURE_TAXONOMY = {
    k: v for k, v in FAILURE_TAXONOMY.items() if k.startswith("SEM-")
}

# Intent failure taxonomy alias
INTENT_FAILURE_TAXONOMY = {
    k: v for k, v in FAILURE_TAXONOMY.items() if k.startswith("INT-")
}


def get_failure_info(code: FailureCode) -> Dict[str, Any]:
    """Get failure taxonomy info for a code (INT-* or SEM-*)."""
    code_str = code.value if hasattr(code, 'value') else str(code)
    return FAILURE_TAXONOMY.get(code_str, {
        "name": "UNKNOWN",
        "class": ViolationClass.SEMANTIC,
        "severity": SemanticSeverity.WARNING,
        "fix_owner": "Unknown",
        "fix_action": "Investigate",
        "description": "Unknown failure code",
    })


def get_fix_owner(code: FailureCode) -> str:
    """Get the fix owner for a failure code."""
    return get_failure_info(code).get("fix_owner", "Unknown")


def get_fix_action(code: FailureCode) -> str:
    """Get the fix action for a failure code."""
    return get_failure_info(code).get("fix_action", "Investigate")


def get_violation_class(code: FailureCode) -> ViolationClass:
    """Get the violation class for a failure code."""
    return get_failure_info(code).get("class", ViolationClass.SEMANTIC)


def format_violation_message(code: FailureCode, context_msg: str) -> str:
    """Format a violation message with context."""
    info = get_failure_info(code)
    return f"{info['name']}: {context_msg}"
