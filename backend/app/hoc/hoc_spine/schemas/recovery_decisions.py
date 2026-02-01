# Layer: L4 — HOC Spine (Schema)
# AUDIENCE: CUSTOMER
# Role: Recovery decision re-exports — declarative surface only
# Callers: policies/L5_engines/recovery_evaluation_engine.py
# Reference: PIN-507 (Law 6 remediation), PIN-504
# artifact_class: CODE

"""
Recovery Decisions (Spine Schema) — Re-export Surface

TOMBSTONE (PIN-507 Law 6, 2026-02-01):
Pure decision functions moved to hoc_spine/utilities/recovery_decisions.py.
Canonical import: app.hoc.hoc_spine.utilities.recovery_decisions

evaluate_rules() DELETED — it was hidden cross-domain orchestration
(schemas → incidents L5_engines). Callers must import evaluate_rules
directly from incidents/L5_engines/recovery_rule_engine.

This file re-exports constants and functions for backward compatibility only.
Remove re-exports after cleansing cycle.
"""

# Re-export from utilities (PIN-507 Law 6)
from app.hoc.hoc_spine.utilities.recovery_decisions import (  # noqa: F401
    ACTION_SELECTION_THRESHOLD,
    AUTO_EXECUTE_CONFIDENCE_THRESHOLD,
    combine_confidences,
    should_auto_execute,
    should_select_action,
)

# TOMBSTONE: evaluate_rules() deleted (PIN-507 Law 6, 2026-02-01).
# It was hidden cross-domain orchestration (schemas → incidents L5_engines).
# Callers must import evaluate_rules directly from:
#   app.hoc.cus.incidents.L5_engines.recovery_rule_engine
# Do NOT recreate. See PIN-507 Law 6 remediation.

__all__ = [
    "AUTO_EXECUTE_CONFIDENCE_THRESHOLD",
    "ACTION_SELECTION_THRESHOLD",
    "combine_confidences",
    "should_select_action",
    "should_auto_execute",
]
