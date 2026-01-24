# Layer: L2.1 — Panel Adapter Layer
# Product: ai-console
# Role: Resolve panel dependencies and evaluation order
# Reference: L2_1_PANEL_DEPENDENCY_GRAPH.yaml

"""
Panel Dependency Resolver — Resolve evaluation order for panels

Determines which panels must be evaluated before others based on
the dependency graph. Supports short-circuit evaluation.
"""

from typing import Dict, List, Optional, Set

from .panel_types import DependencySpec


class PanelDependencyResolver:
    """
    Resolves panel evaluation order from dependency graph.

    Usage:
        resolver = PanelDependencyResolver(dependencies)
        order = resolver.resolve_order("OVR-SUM-HL")
    """

    def __init__(self, dependencies: Dict[str, DependencySpec]):
        self.dependencies = dependencies

    def resolve_order(self, panel_id: str) -> List[str]:
        """
        Get evaluation order for a panel.

        Returns list of panel_ids in the order they should be evaluated.
        The target panel is last.
        """
        chain: List[str] = []
        visited: Set[str] = set()

        def visit(pid: str):
            if pid in visited:
                return
            visited.add(pid)

            dep = self.dependencies.get(pid)
            if dep:
                for upstream in dep.depends_on:
                    visit(upstream)

            chain.append(pid)

        visit(panel_id)
        return chain

    def get_upstream_panels(self, panel_id: str) -> List[str]:
        """Get direct upstream dependencies for a panel."""
        dep = self.dependencies.get(panel_id)
        return dep.depends_on if dep else []

    def get_evaluation_tier(self, panel_id: str) -> int:
        """Get evaluation tier (order) for a panel."""
        dep = self.dependencies.get(panel_id)
        return dep.evaluation_order if dep else 99

    def can_short_circuit(self, panel_id: str) -> bool:
        """Check if panel can short-circuit on upstream failure."""
        dep = self.dependencies.get(panel_id)
        return dep.can_short_circuit if dep else False

    def get_all_tiers(self) -> List[List[str]]:
        """
        Get all panels organized by evaluation tier.

        Returns list of tiers, each containing panel_ids.
        Tier 0 = no dependencies, evaluated first.
        """
        tiers: Dict[int, List[str]] = {}

        for panel_id, dep in self.dependencies.items():
            tier = dep.evaluation_order
            if tier not in tiers:
                tiers[tier] = []
            tiers[tier].append(panel_id)

        return [tiers[t] for t in sorted(tiers.keys())]
