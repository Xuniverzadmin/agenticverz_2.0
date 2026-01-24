# ============================================================
# ⚠️ DUPLICATE — QUARANTINED (POLICIES DOMAIN)
#
# This file is NOT authoritative and MUST NOT be used.
#
# Canonical Type:
#   houseofcards/customer/policies/engines/policy_graph_engine.py
#   Class: PolicyConflict (line 73)
#
# Duplicate Of:
#   Originally defined in facade for response shaping
#   houseofcards/customer/policies/facades/policies_facade.py:205
#
# Audit Reference:
#   POL-DUP-004
#
# Status:
#   FROZEN — retained for historical traceability only
#
# Removal:
#   Eligible after Phase 2 DTO unification
# ============================================================

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PolicyConflictResult:
    """
    QUARANTINED — Use PolicyConflict from policy_graph_engine.py instead.

    Policy conflict summary (DFT-O4).

    Fields (100% overlap with canonical PolicyConflict):
        - policy_a_id: str
        - policy_b_id: str
        - policy_a_name: str
        - policy_b_name: str
        - conflict_type: str (SCOPE_OVERLAP, THRESHOLD_CONTRADICTION, TEMPORAL_CONFLICT, PRIORITY_OVERRIDE)
        - severity: str (BLOCKING, WARNING)
        - explanation: str
        - recommended_action: str
        - detected_at: datetime
    """

    policy_a_id: str
    policy_b_id: str
    policy_a_name: str
    policy_b_name: str
    conflict_type: str
    severity: str
    explanation: str
    recommended_action: str
    detected_at: datetime
