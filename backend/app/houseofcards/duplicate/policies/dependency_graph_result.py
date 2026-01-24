# ============================================================
# ⚠️ DUPLICATE — QUARANTINED (POLICIES DOMAIN)
#
# This file is NOT authoritative and MUST NOT be used.
#
# Canonical Type:
#   houseofcards/customer/policies/engines/policy_graph_engine.py
#   Class: DependencyGraphResult (line 151)
#
# Duplicate Of:
#   Originally defined in facade for response shaping
#   houseofcards/customer/policies/facades/policies_facade.py:266
#
# Audit Reference:
#   POL-DUP-003
#
# Status:
#   FROZEN — retained for historical traceability only
#
# Note:
#   This facade version adds nodes_count and edges_count fields
#   not present in the canonical engine version. These are
#   presentation-only fields that should be computed at usage site.
#
# Removal:
#   Eligible after Phase 2 DTO unification
# ============================================================

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .policy_node_result import PolicyNodeResult
    from .policy_dependency_edge import PolicyDependencyEdge


@dataclass
class DependencyGraphResult:
    """
    QUARANTINED — Use DependencyGraphResult from policy_graph_engine.py instead.

    Policy dependency graph response.

    Facade-added presentation fields (not in canonical):
        - nodes_count: int
        - edges_count: int

    Canonical fields:
        - nodes: list[PolicyNodeResult]
        - edges: list[PolicyDependencyEdge]
        - computed_at: datetime
    """

    nodes: list["PolicyNodeResult"]
    edges: list["PolicyDependencyEdge"]
    nodes_count: int
    edges_count: int
    computed_at: datetime
