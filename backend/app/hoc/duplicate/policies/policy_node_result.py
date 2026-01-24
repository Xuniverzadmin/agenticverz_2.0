# ============================================================
# ⚠️ DUPLICATE — QUARANTINED (POLICIES DOMAIN)
#
# This file is NOT authoritative and MUST NOT be used.
#
# Canonical Type:
#   hoc/cus/policies/L5_engines/policy_graph_engine.py
#   Class: PolicyNode (line 125)
#
# Duplicate Of:
#   Originally defined in facade for response shaping
#   hoc/cus/policies/facades/policies_facade.py:240
#
# Audit Reference:
#   POL-DUP-001
#
# Status:
#   FROZEN — retained for historical traceability only
#
# Removal:
#   Eligible after Phase 2 DTO unification
# ============================================================

from dataclasses import dataclass


@dataclass
class PolicyDependencyRelation:
    """
    QUARANTINED — Part of PolicyNodeResult structure.

    A dependency relationship.
    """

    policy_id: str
    policy_name: str
    dependency_type: str  # EXPLICIT, IMPLICIT_SCOPE, IMPLICIT_LIMIT
    reason: str


@dataclass
class PolicyNodeResult:
    """
    QUARANTINED — Use PolicyNode from policy_graph_engine.py instead.

    A node in the dependency graph (DFT-O5).

    Fields (100% overlap with canonical PolicyNode):
        - id: str
        - name: str
        - rule_type: str (SYSTEM, SAFETY, ETHICAL, TEMPORAL)
        - scope: str
        - status: str
        - enforcement_mode: str
        - depends_on: list[PolicyDependencyRelation]
        - required_by: list[PolicyDependencyRelation]
    """

    id: str
    name: str
    rule_type: str
    scope: str
    status: str
    enforcement_mode: str
    depends_on: list[PolicyDependencyRelation]
    required_by: list[PolicyDependencyRelation]
