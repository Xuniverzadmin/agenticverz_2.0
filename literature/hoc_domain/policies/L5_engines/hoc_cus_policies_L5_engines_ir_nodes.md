# hoc_cus_policies_L5_engines_ir_nodes

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/ir_nodes.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy IR node definitions (pure data structures)

## Intent

**Role:** Policy IR node definitions (pure data structures)
**Reference:** PIN-470, Policy System
**Callers:** policy/ir/*

## Purpose

IR nodes for PLang v2.0 compilation.

---

## Classes

### `IRType(Enum)`
- **Docstring:** IR value types.

### `IRGovernance`
- **Docstring:** Governance metadata for IR nodes.
- **Methods:** from_ast, to_dict
- **Class Variables:** category: PolicyCategory, priority: int, source_policy: Optional[str], source_rule: Optional[str], requires_approval: bool, audit_level: int

### `IRNode(ABC)`
- **Docstring:** Base class for all IR nodes.
- **Methods:** __str__
- **Class Variables:** id: int, governance: Optional[IRGovernance]

### `IRInstruction(IRNode)`
- **Docstring:** Base class for IR instructions.
- **Class Variables:** result_type: IRType

### `IRLoadConst(IRInstruction)`
- **Docstring:** Load constant value.
- **Methods:** __str__
- **Class Variables:** value: Any

### `IRLoadVar(IRInstruction)`
- **Docstring:** Load variable value.
- **Methods:** __str__
- **Class Variables:** name: str

### `IRStoreVar(IRInstruction)`
- **Docstring:** Store value to variable.
- **Methods:** __str__
- **Class Variables:** name: str, value_id: int

### `IRBinaryOp(IRInstruction)`
- **Docstring:** Binary operation.
- **Methods:** __str__
- **Class Variables:** op: str, left_id: int, right_id: int

### `IRUnaryOp(IRInstruction)`
- **Docstring:** Unary operation.
- **Methods:** __str__
- **Class Variables:** op: str, operand_id: int

### `IRCompare(IRInstruction)`
- **Docstring:** Comparison operation.
- **Methods:** __str__
- **Class Variables:** op: str, left_id: int, right_id: int, result_type: IRType

### `IRJump(IRInstruction)`
- **Docstring:** Unconditional jump.
- **Methods:** __str__
- **Class Variables:** target_block: str

### `IRJumpIf(IRInstruction)`
- **Docstring:** Conditional jump.
- **Methods:** __str__
- **Class Variables:** condition_id: int, true_block: str, false_block: str

### `IRCall(IRInstruction)`
- **Docstring:** Function call.
- **Methods:** __str__
- **Class Variables:** callee: str, args: List[int]

### `IRReturn(IRInstruction)`
- **Docstring:** Return from function.
- **Methods:** __str__
- **Class Variables:** value_id: Optional[int]

### `IRAction(IRInstruction)`
- **Docstring:** Policy action instruction.
- **Methods:** __str__
- **Class Variables:** action: ActionType, target: Optional[str], reason_id: Optional[int]

### `IRCheckPolicy(IRInstruction)`
- **Docstring:** Check against M19 policy engine.
- **Methods:** __str__
- **Class Variables:** policy_id: str, context_id: Optional[int], result_type: IRType

### `IREmitIntent(IRInstruction)`
- **Docstring:** Emit intent to M18 execution layer.
- **Methods:** __str__
- **Class Variables:** intent_type: str, payload_ids: List[int], priority: int, requires_confirmation: bool

### `IRBlock`
- **Docstring:** Basic block in IR.
- **Methods:** add_instruction, is_terminated, __str__
- **Class Variables:** name: str, instructions: List[IRInstruction], predecessors: List[str], successors: List[str], governance: Optional[IRGovernance]

### `IRFunction`
- **Docstring:** Function in IR.
- **Methods:** add_block, get_block, __str__
- **Class Variables:** name: str, params: List[str], return_type: IRType, blocks: Dict[str, IRBlock], entry_block: str, governance: Optional[IRGovernance]

### `IRModule`
- **Docstring:** Module in IR.
- **Methods:** add_function, get_function, get_functions_by_category, __str__
- **Class Variables:** name: str, functions: Dict[str, IRFunction], globals: Dict[str, Any], imports: List[str], governance: Optional[IRGovernance], functions_by_category: Dict[PolicyCategory, List[str]]

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.compiler.grammar` |

## Callers

policy/ir/*

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: IRType
      methods: []
    - name: IRGovernance
      methods: [from_ast, to_dict]
    - name: IRNode
      methods: []
    - name: IRInstruction
      methods: []
    - name: IRLoadConst
      methods: []
    - name: IRLoadVar
      methods: []
    - name: IRStoreVar
      methods: []
    - name: IRBinaryOp
      methods: []
    - name: IRUnaryOp
      methods: []
    - name: IRCompare
      methods: []
    - name: IRJump
      methods: []
    - name: IRJumpIf
      methods: []
    - name: IRCall
      methods: []
    - name: IRReturn
      methods: []
    - name: IRAction
      methods: []
    - name: IRCheckPolicy
      methods: []
    - name: IREmitIntent
      methods: []
    - name: IRBlock
      methods: [add_instruction, is_terminated]
    - name: IRFunction
      methods: [add_block, get_block]
    - name: IRModule
      methods: [add_function, get_function, get_functions_by_category]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
