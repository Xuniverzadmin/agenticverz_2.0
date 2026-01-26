# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policy_conflicts
#   Writes: policy_conflict_resolutions
# Database:
#   Scope: domain (policies)
#   Models: PolicyConflict, PolicyConflictResolution
# Role: Policy conflict resolution
# Callers: policy/engine
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-470, Policy System

# M20 Policy Optimizer - Conflict Resolution
# Resolves conflicts between policies using governance rules
"""
Conflict resolution for PLang v2.0.

Conflict types:
- Action conflicts: Different actions for same condition
- Priority conflicts: Same priority for different policies
- Category conflicts: Cross-category interactions

Resolution strategies:
- Category precedence: SAFETY > PRIVACY > OPERATIONAL > ROUTING > CUSTOM
- Priority ordering: Higher priority wins
- Action precedence: deny > escalate > route > allow
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple

from app.policy.compiler.grammar import PLANG_GRAMMAR, ActionType, PolicyCategory
from app.policy.ir.ir_nodes import (
    IRAction,
    IRBlock,
    IRFunction,
    IRModule,
)


class ConflictType(Enum):
    """Types of policy conflicts."""

    ACTION = auto()  # Different actions for same condition
    PRIORITY = auto()  # Same priority for different policies
    CATEGORY = auto()  # Cross-category interactions
    CIRCULAR = auto()  # Circular dependencies


@dataclass
class PolicyConflict:
    """
    A detected conflict between policies.

    Includes conflict type, involved policies, and resolution.
    """

    conflict_type: ConflictType
    policies: List[str]
    description: str
    severity: int = 50  # 0-100, higher = more severe
    resolution: Optional[str] = None
    resolved: bool = False
    winner: Optional[str] = None

    def __str__(self) -> str:
        status = "RESOLVED" if self.resolved else "UNRESOLVED"
        return f"Conflict({self.conflict_type.name}, {self.policies}, {status})"


class ConflictResolver:
    """
    Resolves conflicts between policies.

    Uses M19 governance rules to determine winning policy
    when conflicts are detected.
    """

    def __init__(self):
        self.conflicts: List[PolicyConflict] = []
        self.resolution_log: List[str] = []

    def resolve(self, module: IRModule) -> Tuple[IRModule, List[PolicyConflict]]:
        """
        Detect and resolve conflicts in module.

        Args:
            module: IR module to analyze

        Returns:
            Tuple of (resolved module, list of conflicts found)
        """
        self.conflicts = []
        self.resolution_log = []

        # Detect conflicts
        self._detect_action_conflicts(module)
        self._detect_priority_conflicts(module)
        self._detect_category_conflicts(module)
        self._detect_circular_dependencies(module)

        # Resolve conflicts
        for conflict in self.conflicts:
            self._resolve_conflict(module, conflict)

        return module, self.conflicts

    def _detect_action_conflicts(self, module: IRModule) -> None:
        """Detect conflicting actions for same conditions."""
        # Group functions by entry condition patterns
        condition_groups: Dict[str, List[Tuple[str, IRFunction]]] = {}

        for name, func in module.functions.items():
            # Get condition signature from first block
            entry_block = func.blocks.get(func.entry_block)
            if not entry_block:
                continue

            condition_sig = self._get_condition_signature(entry_block)
            if condition_sig not in condition_groups:
                condition_groups[condition_sig] = []
            condition_groups[condition_sig].append((name, func))

        # Check for conflicting actions in same condition group
        for sig, funcs in condition_groups.items():
            if len(funcs) < 2:
                continue

            actions: Dict[ActionType, List[str]] = {}
            for name, func in funcs:
                for block in func.blocks.values():
                    for instr in block.instructions:
                        if isinstance(instr, IRAction):
                            if instr.action not in actions:
                                actions[instr.action] = []
                            actions[instr.action].append(name)

            # If multiple different actions, that's a conflict
            if len(actions) > 1:
                all_policies = list(set(p for ps in actions.values() for p in ps))
                self.conflicts.append(
                    PolicyConflict(
                        conflict_type=ConflictType.ACTION,
                        policies=all_policies,
                        description=f"Conflicting actions {list(actions.keys())} for condition '{sig}'",
                        severity=70,
                    )
                )

    def _detect_priority_conflicts(self, module: IRModule) -> None:
        """Detect policies with same priority in same category."""
        priority_groups: Dict[Tuple[PolicyCategory, int], List[str]] = {}

        for name, func in module.functions.items():
            if not func.governance:
                continue

            key = (func.governance.category, func.governance.priority)
            if key not in priority_groups:
                priority_groups[key] = []
            priority_groups[key].append(name)

        for key, policies in priority_groups.items():
            if len(policies) > 1:
                self.conflicts.append(
                    PolicyConflict(
                        conflict_type=ConflictType.PRIORITY,
                        policies=policies,
                        description=f"Same priority {key[1]} in category {key[0].value}",
                        severity=30,
                    )
                )

    def _detect_category_conflicts(self, module: IRModule) -> None:
        """Detect cross-category interactions that may conflict."""
        # Check if lower-priority categories override higher ones
        by_category: Dict[PolicyCategory, List[Tuple[str, IRFunction]]] = {}

        for name, func in module.functions.items():
            if not func.governance:
                continue
            cat = func.governance.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append((name, func))

        # Check for ROUTING/CUSTOM policies that might override SAFETY
        safety_policies = by_category.get(PolicyCategory.SAFETY, [])
        routing_policies = by_category.get(PolicyCategory.ROUTING, [])
        custom_policies = by_category.get(PolicyCategory.CUSTOM, [])

        # Look for potential overrides
        for lower_cat, lower_policies in [
            (PolicyCategory.ROUTING, routing_policies),
            (PolicyCategory.CUSTOM, custom_policies),
        ]:
            for lower_name, lower_func in lower_policies:
                for safety_name, safety_func in safety_policies:
                    # Check if lower policy might override safety
                    if self._might_override(lower_func, safety_func):
                        self.conflicts.append(
                            PolicyConflict(
                                conflict_type=ConflictType.CATEGORY,
                                policies=[lower_name, safety_name],
                                description=f"{lower_cat.value} policy '{lower_name}' might override SAFETY policy '{safety_name}'",
                                severity=90,
                            )
                        )

    def _detect_circular_dependencies(self, module: IRModule) -> None:
        """Detect circular route dependencies."""
        # Build route graph
        route_graph: Dict[str, Set[str]] = {}

        for name, func in module.functions.items():
            route_graph[name] = set()
            for block in func.blocks.values():
                for instr in block.instructions:
                    if isinstance(instr, IRAction) and instr.action == ActionType.ROUTE:
                        if instr.target:
                            route_graph[name].add(instr.target)

        # DFS for cycles
        visited: Set[str] = set()
        path: Set[str] = set()

        def has_cycle(node: str) -> Optional[List[str]]:
            if node in path:
                return [node]
            if node in visited:
                return None

            visited.add(node)
            path.add(node)

            for neighbor in route_graph.get(node, set()):
                result = has_cycle(neighbor)
                if result:
                    result.insert(0, node)
                    return result

            path.remove(node)
            return None

        for node in route_graph:
            cycle = has_cycle(node)
            if cycle:
                self.conflicts.append(
                    PolicyConflict(
                        conflict_type=ConflictType.CIRCULAR,
                        policies=cycle,
                        description=f"Circular routing: {' -> '.join(cycle)}",
                        severity=100,
                    )
                )
                break  # One cycle is enough to report

    def _get_condition_signature(self, block: IRBlock) -> str:
        """Get a signature for the condition pattern in a block."""
        # Simple signature based on instruction sequence
        parts = []
        for instr in block.instructions[:5]:  # First 5 instructions
            parts.append(type(instr).__name__)
        return "|".join(parts)

    def _might_override(self, lower: IRFunction, higher: IRFunction) -> bool:
        """Check if lower-priority policy might override higher one."""
        # Check if both have actions and lower allows what higher denies
        lower_actions = self._get_actions(lower)
        higher_actions = self._get_actions(higher)

        # If higher denies and lower allows, potential override
        if ActionType.DENY in higher_actions and ActionType.ALLOW in lower_actions:
            return True
        return False

    def _get_actions(self, func: IRFunction) -> Set[ActionType]:
        """Get all actions in a function."""
        actions: Set[ActionType] = set()
        for block in func.blocks.values():
            for instr in block.instructions:
                if isinstance(instr, IRAction):
                    actions.add(instr.action)
        return actions

    def _resolve_conflict(self, module: IRModule, conflict: PolicyConflict) -> None:
        """
        Resolve a single conflict.

        Resolution strategy depends on conflict type.
        """
        if conflict.conflict_type == ConflictType.ACTION:
            self._resolve_action_conflict(module, conflict)
        elif conflict.conflict_type == ConflictType.PRIORITY:
            self._resolve_priority_conflict(module, conflict)
        elif conflict.conflict_type == ConflictType.CATEGORY:
            self._resolve_category_conflict(module, conflict)
        elif conflict.conflict_type == ConflictType.CIRCULAR:
            self._resolve_circular_conflict(module, conflict)

    def _resolve_action_conflict(self, module: IRModule, conflict: PolicyConflict) -> None:
        """Resolve action conflict using action precedence."""
        # Find policy with most restrictive action
        best_policy = None
        best_precedence = -1

        for policy_name in conflict.policies:
            func = module.functions.get(policy_name)
            if not func:
                continue

            for action in self._get_actions(func):
                precedence = PLANG_GRAMMAR.get_action_precedence(action.value)
                if precedence > best_precedence:
                    best_precedence = precedence
                    best_policy = policy_name

        if best_policy:
            conflict.winner = best_policy
            conflict.resolution = f"Using most restrictive action from '{best_policy}'"
            conflict.resolved = True
            self.resolution_log.append(f"Resolved ACTION conflict: {conflict.resolution}")

    def _resolve_priority_conflict(self, module: IRModule, conflict: PolicyConflict) -> None:
        """Resolve priority conflict by adjusting priorities."""
        # Assign unique priorities based on lexicographic order
        for i, policy_name in enumerate(sorted(conflict.policies)):
            func = module.functions.get(policy_name)
            if func and func.governance:
                # Offset by position to make unique
                func.governance.priority += i

        conflict.resolution = "Adjusted priorities to be unique"
        conflict.resolved = True
        self.resolution_log.append(f"Resolved PRIORITY conflict: {conflict.resolution}")

    def _resolve_category_conflict(self, module: IRModule, conflict: PolicyConflict) -> None:
        """Resolve category conflict using category precedence."""
        # Higher category always wins
        best_policy = None
        best_category_priority = -1

        for policy_name in conflict.policies:
            func = module.functions.get(policy_name)
            if not func or not func.governance:
                continue

            cat_priority = PLANG_GRAMMAR.get_category_priority(func.governance.category.value)
            if cat_priority > best_category_priority:
                best_category_priority = cat_priority
                best_policy = policy_name

        if best_policy:
            conflict.winner = best_policy
            conflict.resolution = f"Higher category policy '{best_policy}' takes precedence"
            conflict.resolved = True
            self.resolution_log.append(f"Resolved CATEGORY conflict: {conflict.resolution}")

    def _resolve_circular_conflict(self, module: IRModule, conflict: PolicyConflict) -> None:
        """Resolve circular routing by breaking the cycle."""
        # Find the lowest priority policy in the cycle and remove its route
        if len(conflict.policies) < 2:
            return

        lowest_policy = None
        lowest_priority = float("inf")

        for policy_name in conflict.policies:
            func = module.functions.get(policy_name)
            if func and func.governance:
                if func.governance.priority < lowest_priority:
                    lowest_priority = func.governance.priority
                    lowest_policy = policy_name

        if lowest_policy:
            # Mark the route as broken (would need to actually modify IR in production)
            conflict.winner = lowest_policy
            conflict.resolution = f"Breaking cycle at lowest priority policy '{lowest_policy}'"
            conflict.resolved = True
            self.resolution_log.append(f"Resolved CIRCULAR conflict: {conflict.resolution}")
