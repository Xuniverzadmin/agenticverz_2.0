# dag_sorter.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/dag_sorter.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            dag_sorter.py
Lives in:        services/
Role:            Services
Inbound:         policy/optimizer
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         DAG-based execution ordering for PLang v2.0.
Violations:      none
```

## Purpose

DAG-based execution ordering for PLang v2.0.

Features:
- Topological sort for dependency-respecting execution
- Category-aware ordering (SAFETY first)
- Priority-based tie breaking
- Deterministic execution plan generation

## Import Analysis

**External:**
- `app.policy.compiler.grammar`
- `app.policy.ir.ir_nodes`
- `app.policy.compiler.grammar`
- `app.policy.ir.ir_nodes`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `ExecutionPhase(Enum)`

Execution phases in deterministic order.

### `ExecutionNode`

A node in the execution DAG.

Represents a policy/rule to execute with its dependencies
and governance metadata.

#### Methods

- `__hash__() -> int` — _No docstring._
- `__eq__(other: Any) -> bool` — _No docstring._

### `ExecutionDAG`

Directed Acyclic Graph of policy execution.

Provides deterministic ordering for policy evaluation.

#### Methods

- `add_node(node: ExecutionNode) -> None` — Add a node to the DAG.
- `add_edge(from_node: str, to_node: str) -> None` — Add a dependency edge (from depends on to).
- `get_roots() -> List[ExecutionNode]` — Get nodes with no dependencies (execution starts here).
- `get_leaves() -> List[ExecutionNode]` — Get nodes with no dependents (execution ends here).

### `ExecutionPlan`

A deterministic execution plan.

Contains ordered list of policies to execute with
parallel execution opportunities.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary for serialization.

### `DAGSorter`

Sorts policies into deterministic execution order.

Uses topological sort with governance-aware ordering:
1. SAFETY policies always execute first
2. Higher priority policies execute before lower
3. Dependencies are respected
4. Parallelizable policies grouped into stages

#### Methods

- `__init__()` — _No docstring._
- `build_dag(module: IRModule) -> ExecutionDAG` — Build execution DAG from IR module.
- `_get_phase(func: IRFunction) -> ExecutionPhase` — Map function governance category to execution phase.
- `_add_category_dependencies() -> None` — Add dependencies based on category precedence.
- `_add_routing_dependencies(module: IRModule) -> None` — Add dependencies from routing targets.
- `sort() -> ExecutionPlan` — Perform topological sort to get execution plan.
- `get_execution_order(module: IRModule) -> List[str]` — Get flat execution order (convenience method).
- `visualize() -> str` — Generate text visualization of the DAG.

## Domain Usage

**Callers:** policy/optimizer

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ExecutionPhase
      methods: []
      consumers: ["orchestrator"]
    - name: ExecutionNode
      methods:
      consumers: ["orchestrator"]
    - name: ExecutionDAG
      methods:
        - add_node
        - add_edge
        - get_roots
        - get_leaves
      consumers: ["orchestrator"]
    - name: ExecutionPlan
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: DAGSorter
      methods:
        - build_dag
        - sort
        - get_execution_order
        - visualize
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['app.policy.compiler.grammar', 'app.policy.ir.ir_nodes', 'app.policy.compiler.grammar', 'app.policy.ir.ir_nodes']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

