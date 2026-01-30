# hoc_cus_policies_L5_engines_ir_compiler

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/ir_compiler.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy DSL IR Compiler (AST → bytecode) - pure compilation logic

## Intent

**Role:** Policy DSL IR Compiler (AST → bytecode) - pure compilation logic
**Reference:** PIN-470, PIN-341 Section 1.8, PIN-345
**Callers:** policy engine

## Purpose

Policy DSL Intermediate Representation (IR) Compiler

---

## Functions

### `compile_policy(ast: PolicyAST, optimize: bool) -> PolicyIR`
- **Async:** No
- **Docstring:** Compile PolicyAST to PolicyIR.  Args:
- **Calls:** IRCompiler, OptimizingIRCompiler, compile

### `ir_hash(ast: PolicyAST) -> str`
- **Async:** No
- **Docstring:** Convenience function to get IR hash from AST.  This is the audit identity of the policy.
- **Calls:** compile_policy, compute_hash

## Classes

### `OpCode(str, Enum)`
- **Docstring:** Closed instruction set for Policy IR.

### `Instruction`
- **Docstring:** A single IR instruction.
- **Methods:** to_dict
- **Class Variables:** opcode: OpCode, operands: tuple[Any, ...]

### `CompiledClause`
- **Docstring:** Compiled form of a single when-then clause.
- **Methods:** to_dict
- **Class Variables:** condition_ir: tuple[Instruction, ...], action_ir: tuple[Instruction, ...]

### `PolicyIR`
- **Docstring:** Complete IR for a policy.
- **Methods:** to_dict, to_json, compute_hash, instruction_count
- **Class Variables:** name: str, version: int, scope: str, mode: str, clauses: tuple[CompiledClause, ...], ir_version: str

### `IRCompiler`
- **Docstring:** Compiles PolicyAST to PolicyIR.
- **Methods:** __init__, compile, _compile_clause, _compile_condition, _emit_condition, _emit_predicate, _emit_exists, _emit_logical, _compile_actions

### `OptimizingIRCompiler(IRCompiler)`
- **Docstring:** IR Compiler with safe optimizations.
- **Methods:** __init__, compile

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.dsl.ast` |

## Callers

policy engine

## Export Contract

```yaml
exports:
  functions:
    - name: compile_policy
      signature: "compile_policy(ast: PolicyAST, optimize: bool) -> PolicyIR"
    - name: ir_hash
      signature: "ir_hash(ast: PolicyAST) -> str"
  classes:
    - name: OpCode
      methods: []
    - name: Instruction
      methods: [to_dict]
    - name: CompiledClause
      methods: [to_dict]
    - name: PolicyIR
      methods: [to_dict, to_json, compute_hash, instruction_count]
    - name: IRCompiler
      methods: [compile]
    - name: OptimizingIRCompiler
      methods: [compile]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
