# ============================================================
# ⚠️ DUPLICATE — QUARANTINED (POLICIES DOMAIN)
#
# This file is NOT authoritative and MUST NOT be used.
#
# Canonical Type:
#   hoc/cus/policies/L5_engines/policy_graph_engine.py
#   Class: PolicyDependency (line 101)
#
# Duplicate Of:
#   Originally defined in facade for response shaping
#   hoc/cus/policies/facades/policies_facade.py:254
#
# Audit Reference:
#   POL-DUP-002
#
# Status:
#   FROZEN — retained for historical traceability only
#
# Removal:
#   Eligible after Phase 2 DTO unification
# ============================================================

from dataclasses import dataclass


@dataclass
class PolicyDependencyEdge:
    """
    QUARANTINED — Use PolicyDependency from policy_graph_engine.py instead.

    A dependency edge in the graph.

    Fields (100% overlap with canonical PolicyDependency):
        - policy_id: str
        - depends_on_id: str
        - policy_name: str
        - depends_on_name: str
        - dependency_type: str
        - reason: str
    """

    policy_id: str
    depends_on_id: str
    policy_name: str
    depends_on_name: str
    dependency_type: str
    reason: str
