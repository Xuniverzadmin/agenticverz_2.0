# Layer: L4 — HOC Spine (Utility)
# AUDIENCE: SHARED
# Product: system-wide
# Role: Pure recovery decision functions — cross-domain policy (no DB, no side effects)
# Callers: policies/L5_engines/recovery_evaluation_engine.py, incidents/L5_engines/recovery_rule_engine.py
# Reference: PIN-507 (Law 6 remediation — moved from hoc_spine/schemas/recovery_decisions.py)
# artifact_class: CODE

"""
Recovery Decision Utilities (Spine Utility)

Pure decision functions for recovery confidence and threshold logic.
Moved from hoc_spine/schemas/recovery_decisions.py (PIN-507 Law 6):
schemas must be declarative only; executable logic is policy, not contract.

These are cross-domain pure decision functions shared between
incidents and policies domains. They contain no DB access or side effects.
"""


# =============================================================================
# Thresholds (L4 domain rules)
# =============================================================================

# Auto-execute confidence threshold (L4 domain rule)
# This is the authoritative threshold for automatic recovery execution.
# Reference: PIN-254 Phase A Fix (SHADOW-001)
AUTO_EXECUTE_CONFIDENCE_THRESHOLD: float = 0.8

# Action selection threshold (L4 domain rule)
# This is the authoritative threshold for action selection.
# Reference: PIN-257 Phase E-4 Extraction #3
ACTION_SELECTION_THRESHOLD: float = 0.3


# =============================================================================
# Pure Decision Functions
# =============================================================================


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


__all__ = [
    "AUTO_EXECUTE_CONFIDENCE_THRESHOLD",
    "ACTION_SELECTION_THRESHOLD",
    "combine_confidences",
    "should_select_action",
    "should_auto_execute",
]
