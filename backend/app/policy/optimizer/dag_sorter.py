# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Policy DAG topological sorting
# Callers: policy/optimizer
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Policy System

# M20 Policy Optimizer - DAG Sorter
# Topological ordering for deterministic execution
"""
DAG-based execution ordering for PLang v2.0.

Features:
- Topological sort for dependency-respecting execution
- Category-aware ordering (SAFETY first)
- Priority-based tie breaking
- Deterministic execution plan generation
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

from app.policy.compiler.grammar import PolicyCategory
from app.policy.ir.ir_nodes import IRFunction, IRGovernance, IRModule


class ExecutionPhase(Enum):
    """Execution phases in deterministic order."""

    SAFETY_CHECK = auto()  # SAFETY policies first
    PRIVACY_CHECK = auto()  # Then PRIVACY
    OPERATIONAL = auto()  # Business rules
    ROUTING = auto()  # Routing decisions
    CUSTOM = auto()  # Custom policies last


@dataclass
class ExecutionNode:
    """
    A node in the execution DAG.

    Represents a policy/rule to execute with its dependencies
    and governance metadata.
    """

    name: str
    phase: ExecutionPhase
    priority: int
    governance: Optional[IRGovernance] = None
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ExecutionNode):
            return self.name == other.name
        return False


@dataclass
class ExecutionDAG:
    """
    Directed Acyclic Graph of policy execution.

    Provides deterministic ordering for policy evaluation.
    """

    nodes: Dict[str, ExecutionNode] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)

    def add_node(self, node: ExecutionNode) -> None:
        """Add a node to the DAG."""
        self.nodes[node.name] = node

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add a dependency edge (from depends on to)."""
        self.edges.append((from_node, to_node))
        if from_node in self.nodes:
            self.nodes[from_node].dependencies.add(to_node)
        if to_node in self.nodes:
            self.nodes[to_node].dependents.add(from_node)

    def get_roots(self) -> List[ExecutionNode]:
        """Get nodes with no dependencies (execution starts here)."""
        return [n for n in self.nodes.values() if not n.dependencies]

    def get_leaves(self) -> List[ExecutionNode]:
        """Get nodes with no dependents (execution ends here)."""
        return [n for n in self.nodes.values() if not n.dependents]


@dataclass
class ExecutionPlan:
    """
    A deterministic execution plan.

    Contains ordered list of policies to execute with
    parallel execution opportunities.
    """

    stages: List[List[str]] = field(default_factory=list)
    total_policies: int = 0
    parallel_stages: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "stages": self.stages,
            "total_policies": self.total_policies,
            "parallel_stages": self.parallel_stages,
        }


class DAGSorter:
    """
    Sorts policies into deterministic execution order.

    Uses topological sort with governance-aware ordering:
    1. SAFETY policies always execute first
    2. Higher priority policies execute before lower
    3. Dependencies are respected
    4. Parallelizable policies grouped into stages
    """

    def __init__(self):
        self.dag: Optional[ExecutionDAG] = None

    def build_dag(self, module: IRModule) -> ExecutionDAG:
        """
        Build execution DAG from IR module.

        Args:
            module: IR module containing policies

        Returns:
            ExecutionDAG with all policies and dependencies
        """
        self.dag = ExecutionDAG()

        # Add nodes for each function
        for name, func in module.functions.items():
            phase = self._get_phase(func)
            priority = func.governance.priority if func.governance else 50

            node = ExecutionNode(
                name=name,
                phase=phase,
                priority=priority,
                governance=func.governance,
            )
            self.dag.add_node(node)

        # Add implicit category-based dependencies
        self._add_category_dependencies()

        # Add explicit dependencies from routing
        self._add_routing_dependencies(module)

        return self.dag

    def _get_phase(self, func: IRFunction) -> ExecutionPhase:
        """Map function governance category to execution phase."""
        if not func.governance:
            return ExecutionPhase.CUSTOM

        phase_map = {
            PolicyCategory.SAFETY: ExecutionPhase.SAFETY_CHECK,
            PolicyCategory.PRIVACY: ExecutionPhase.PRIVACY_CHECK,
            PolicyCategory.OPERATIONAL: ExecutionPhase.OPERATIONAL,
            PolicyCategory.ROUTING: ExecutionPhase.ROUTING,
            PolicyCategory.CUSTOM: ExecutionPhase.CUSTOM,
        }
        return phase_map.get(func.governance.category, ExecutionPhase.CUSTOM)

    def _add_category_dependencies(self) -> None:
        """Add dependencies based on category precedence."""
        # Group nodes by phase
        by_phase: Dict[ExecutionPhase, List[str]] = {phase: [] for phase in ExecutionPhase}

        for name, node in self.dag.nodes.items():
            by_phase[node.phase].append(name)

        # Add dependencies: each phase depends on previous phases
        phases = list(ExecutionPhase)
        for i in range(1, len(phases)):
            current_phase = phases[i]
            previous_phase = phases[i - 1]

            # All nodes in current phase depend on all nodes in previous phase
            for current in by_phase[current_phase]:
                for previous in by_phase[previous_phase]:
                    self.dag.add_edge(current, previous)

    def _add_routing_dependencies(self, module: IRModule) -> None:
        """Add dependencies from routing targets."""
        from app.policy.compiler.grammar import ActionType
        from app.policy.ir.ir_nodes import IRAction

        for name, func in module.functions.items():
            for block in func.blocks.values():
                for instr in block.instructions:
                    if isinstance(instr, IRAction) and instr.action == ActionType.ROUTE:
                        assert instr is not None
                        if instr.target and instr.target in self.dag.nodes:
                            # Target must exist before we can route to it
                            self.dag.add_edge(name, instr.target)

    def sort(self) -> ExecutionPlan:
        """
        Perform topological sort to get execution plan.

        Returns:
            ExecutionPlan with deterministic ordering
        """
        if not self.dag:
            return ExecutionPlan()

        plan = ExecutionPlan()
        visited: Set[str] = set()
        in_degree: Dict[str, int] = {name: len(node.dependencies) for name, node in self.dag.nodes.items()}

        # Process in stages (allows parallel execution within stage)
        while len(visited) < len(self.dag.nodes):
            # Find all nodes with no unvisited dependencies
            ready = []
            for name, node in self.dag.nodes.items():
                if name in visited:
                    continue
                if all(dep in visited for dep in node.dependencies):
                    ready.append((name, node))

            if not ready:
                # Cycle detected - should not happen after conflict resolution
                remaining = set(self.dag.nodes.keys()) - visited
                plan.stages.append(list(remaining))
                break

            # Sort ready nodes by phase, then priority
            ready.sort(key=lambda x: (x[1].phase.value, -x[1].priority))

            # Group by phase for parallel execution
            stage: List[str] = []
            current_phase = ready[0][1].phase

            for name, node in ready:
                if node.phase == current_phase:
                    stage.append(name)
                    visited.add(name)
                else:
                    break  # Start new stage for different phase

            if stage:
                plan.stages.append(stage)
                if len(stage) > 1:
                    plan.parallel_stages += 1

        plan.total_policies = len(self.dag.nodes)
        return plan

    def get_execution_order(self, module: IRModule) -> List[str]:
        """
        Get flat execution order (convenience method).

        Args:
            module: IR module to sort

        Returns:
            List of policy names in execution order
        """
        self.build_dag(module)
        plan = self.sort()
        return [name for stage in plan.stages for name in stage]

    def visualize(self) -> str:
        """
        Generate text visualization of the DAG.

        Returns:
            ASCII representation of the execution graph
        """
        if not self.dag:
            return "Empty DAG"

        lines = ["Execution DAG:", ""]

        # Group by phase
        by_phase: Dict[ExecutionPhase, List[ExecutionNode]] = {phase: [] for phase in ExecutionPhase}

        for node in self.dag.nodes.values():
            by_phase[node.phase].append(node)

        for phase in ExecutionPhase:
            nodes = by_phase[phase]
            if not nodes:
                continue

            lines.append(f"[{phase.name}]")
            for node in sorted(nodes, key=lambda n: -n.priority):
                deps = ", ".join(node.dependencies) if node.dependencies else "none"
                lines.append(f"  {node.name} (p={node.priority}) <- {deps}")
            lines.append("")

        return "\n".join(lines)
