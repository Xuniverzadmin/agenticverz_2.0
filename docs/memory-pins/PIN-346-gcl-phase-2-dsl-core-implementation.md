# PIN-346: GC_L Phase 2 DSL Core Implementation

**Status:** 🏗️ FROZEN
**Created:** 2026-01-07
**Category:** GC_L / DSL Implementation
**Milestone:** Phase 2

---

## Summary

Complete implementation of GC_L Policy DSL core services: AST, Parser, Validator, IR Compiler, Interpreter, and comprehensive test suite (250 tests).

---

## Details

## Overview

Phase 2 of the GC_L (Governed Control with Learning) system implements the core DSL services for policy evaluation. This is a pure, deterministic, non-Turing-complete policy language designed for customer self-governance within bounded policies.

## Implementation Summary

### Files Created

| File | Layer | Purpose | LOC |
|------|-------|---------|-----|
| `app/dsl/__init__.py` | L4 | Module exports | 126 |
| `app/dsl/ast.py` | L4 | Immutable AST definitions | ~400 |
| `app/dsl/parser.py` | L4 | Hand-written recursive descent parser | ~600 |
| `app/dsl/validator.py` | L4 | Semantic validation | ~350 |
| `app/dsl/ir_compiler.py` | L4 | AST → Bytecode compiler | ~450 |
| `app/dsl/interpreter.py` | L4 | Pure IR evaluation | ~550 |

### Test Files Created

| File | Tests | Coverage |
|------|-------|----------|
| `tests/dsl/__init__.py` | - | Package init |
| `tests/dsl/test_ast.py` | 45 | AST immutability, serialization, hashing |
| `tests/dsl/test_parser.py` | 43 | Parsing, conditions, errors, round-trip |
| `tests/dsl/test_validator.py` | 32 | Mode enforcement, metric validation |
| `tests/dsl/test_ir_compiler.py` | 32 | Compilation, opcodes, hash stability |
| `tests/dsl/test_interpreter.py` | 55 | Evaluation, stack ops, error handling |
| `tests/dsl/test_roundtrip.py` | 23 | Determinism across pipeline |
| `tests/dsl/test_replay.py` | 20 | Replay independence |
| **TOTAL** | **250** | All passing |

## Architecture

### Layer Classification

All DSL components are **L4 — Domain Engines**:
- Pure functions, no I/O
- No database access
- No network calls
- No side effects

### Design Constraints (Binding)

1. **Non-Turing-Complete**: No loops, functions, recursion, or unbounded computation
2. **Closed Instruction Set**: Exactly 10 opcodes, frozen
3. **Determinism**: Same input → identical output, always
4. **Purity**: Interpreter has no side effects
5. **Descriptive Output**: Says what is true, not what to do

### Closed Instruction Set (10 Opcodes)

```python
class OpCode(str, Enum):
    LOAD_METRIC = "LOAD_METRIC"        # Push facts[metric] to stack
    LOAD_CONST = "LOAD_CONST"          # Push constant to stack
    COMPARE = "COMPARE"                 # Pop 2, push comparison result
    EXISTS = "EXISTS"                   # Push whether metric exists
    AND = "AND"                         # Pop 2 bools, push AND result
    OR = "OR"                           # Pop 2 bools, push OR result
    EMIT_WARN = "EMIT_WARN"             # Emit warning action
    EMIT_BLOCK = "EMIT_BLOCK"           # Emit block action
    EMIT_REQUIRE_APPROVAL = "EMIT_REQUIRE_APPROVAL"  # Emit approval action
    END = "END"                         # End of instruction sequence
```

## DSL Syntax

```
policy <name>
version <int>
scope ORG | PROJECT
mode MONITOR | ENFORCE

when <condition>
then <action>+

# Conditions
metric > | >= | < | <= | == | != value
exists(metric)
condition AND condition
condition OR condition
(condition)

# Actions
WARN "message"
BLOCK
REQUIRE_APPROVAL
```

## Key Guarantees Proven

### 1. Round-trip Determinism
- Same DSL → Same AST hash
- Same AST → Same IR hash
- Same IR + facts → Same result

### 2. Replay Independence
Replay requires ONLY:
- IR (or IR hash for lookup)
- Fact snapshot
- Interpreter

Replay does NOT require:
- L2.1 (API layer)
- GC_L (governance layer)
- FACILITATION
- UI
- Database state

### 3. Error Reproducibility
- Same inputs produce same errors
- Errors occur at same instruction points
- Error messages are deterministic

### 4. IR Hash as Audit Key
- SHA256 hash of canonical IR JSON
- 64 hex characters
- Stable across compilations
- Uniquely identifies policy content

## API Surface

### Public Functions

```python
# Parser
parse(source: str) -> PolicyAST
parse_condition(source: str) -> Condition

# Validator
validate(policy: PolicyAST, allowed_metrics: set[str] | None = None) -> ValidationResult
is_valid(policy: PolicyAST) -> bool

# IR Compiler
compile_policy(ast: PolicyAST, optimize: bool = False) -> PolicyIR
ir_hash(ast: PolicyAST) -> str

# Interpreter
evaluate(ir: PolicyIR, facts: dict[str, Any]) -> EvaluationResult
evaluate_policy(ir: PolicyIR, facts: dict[str, Any], strict: bool = True) -> EvaluationResult
```

### Result Types

```python
@dataclass(frozen=True)
class EvaluationResult:
    any_matched: bool
    clauses: tuple[ClauseResult, ...]
    all_actions: tuple[ActionResult, ...]
    
    @property
    def has_block(self) -> bool
    @property
    def has_require_approval(self) -> bool
    @property
    def warnings(self) -> list[str]
```

## Phase 2 Completion Status

| Phase | Status | Gate Review |
|-------|--------|-------------|
| 2.1 AST | ✅ COMPLETE | - |
| 2.2 Parser | ✅ COMPLETE | - |
| 2.3 Validator | ✅ COMPLETE | ✅ APPROVED |
| 2.4 IR Compiler | ✅ COMPLETE | ✅ APPROVED |
| 2.5 Interpreter | ✅ COMPLETE | ✅ APPROVED |
| 2.6 Round-trip Tests | ✅ COMPLETE | ✅ APPROVED |
| 2.7 Governance Self-check | ✅ COMPLETE | ✅ APPROVED |

**PHASE 2: FORMALLY CLOSED** (2026-01-07)

## References

- PIN-341: GC_L Specification
- PIN-345: DSL Syntax and Semantics
- PIN-339 through PIN-344: GC_L Foundation Specs
- Migrations 068-072: GC_L Database Schema

## Next Steps (Post-Closure)

1. ~~Complete Phase 2.7 Governance self-check~~ ✅ DONE
2. **Phase 3: GC_L API Layer (L2.1)** — Ready to begin
3. Phase 4: GC_L Integration with existing systems
4. Wire FACILITATION to read policy truth
5. Build customer console policy management UI

---


---

## Phase 2 Closure

### Update (2026-01-07)

## Phase 2 Closure Declaration

**Status:** ✅ PHASE 2 FORMALLY CLOSED
**Closure Date:** 2026-01-07
**Authority:** Founder Gate Review

---

### Semantic Baseline Established

Phase 2 of the GC_L DSL implementation is now **frozen**. The following are now immutable semantic truth:

| Component | Status | Governance |
|-----------|--------|------------|
| DSL Grammar | FROZEN | No changes without Phase 2 reopen |
| AST Semantics | FROZEN | No changes without Phase 2 reopen |
| IR Instruction Set | FROZEN | 10 opcodes, closed |
| Interpreter Logic | FROZEN | Canonical, no alternatives |
| Replay Contract | FROZEN | IR + Facts + Interpreter only |

---

### Governance Self-Check Attestation (Immutable Evidence)

```
PHASE 2 GOVERNANCE SELF-CHECK ATTESTATION

Date: 2026-01-07
Phase: 2.7 (Final)
Scope: GC_L Policy DSL Core Services

CERTIFICATIONS:

[✅] No authority encoded in Phase 2
[✅] No execution semantics present
[✅] No FACILITATION logic present
[✅] No GC_L writes or decisions present
[✅] Interpreter remains canonical
[✅] Replay is self-sufficient

ADDITIONAL VERIFICATIONS:

[✅] All 19 dataclasses are frozen=True (immutable)
[✅] All imports are pure (no I/O, no DB, no network)
[✅] Lenient mode explicitly marked non-authoritative
[✅] 250 tests pass covering all guarantees

GOVERNANCE STATUS: COMPLIANT
PHASE 2 STATUS: CLOSED
```

---

### ⚠️ SEMANTIC FREEZE NOTE (TRIPWIRE)

> **Any change to DSL grammar, AST semantics, IR opcodes, or interpreter logic
> requires reopening Phase 2 governance and issuing a new governance PIN.**
>
> This includes but is not limited to:
> - Adding new opcodes to the instruction set
> - Modifying comparison or logical operators
> - Changing serialization format affecting hash stability
> - Adding new action types
> - Modifying evaluation order or stack semantics
>
> Phase 2 reopening requires:
> 1. Explicit founder approval
> 2. New governance PIN documenting the change
> 3. Re-execution of all governance self-checks
> 4. Re-certification of replay independence

---

### What Closure Means

| ✔ Frozen | ❌ Not Frozen |
|----------|---------------|
| Policy meaning | Authority/permissions |
| Truth definition | Console evolution |
| Replay guarantees | FACILITATION growth |
| IR hash identity | UI/UX improvements |

---

### Forward Contract

**L2.1 (Orchestration Layer) may now:**
- Consume interpreter output
- Route results to FACILITATION, GC_L, UI

**L2.1 must NEVER:**
- Reinterpret truth
- Add conditional evaluation paths
- Modify IR before evaluation
- Cache results with different semantics

---

### Files Frozen by This Closure

| File | Hash Stability |
|------|----------------|
| `app/dsl/ast.py` | IR hash depends on AST structure |
| `app/dsl/parser.py` | AST structure depends on parser |
| `app/dsl/validator.py` | Validation rules frozen |
| `app/dsl/ir_compiler.py` | 10-opcode set frozen |
| `app/dsl/interpreter.py` | Canonical evaluation frozen |
| `app/dsl/__init__.py` | Public API frozen |

## Related PINs

- [PIN-339](PIN-339-gcl-specification-foundation.md) — GC_L Foundation
- [PIN-340](PIN-340-gcl-policy-lifecycle.md) — Policy Lifecycle
- [PIN-341](PIN-341-gcl-dsl-specification.md) — DSL Specification
- [PIN-342](PIN-342-gcl-ui-interpreter-hashchain.md) — UI, Interpreter, Hash-Chain
- [PIN-343](PIN-343-gcl-ir-optimizer-confidence-anchoring.md) — IR, Optimizer, Anchoring
- [PIN-344](PIN-344-gcl-facilitation-compiler.md) — FACILITATION Compiler
- [PIN-345](PIN-345-gcl-dsl-syntax-semantics.md) — DSL Syntax & Semantics
