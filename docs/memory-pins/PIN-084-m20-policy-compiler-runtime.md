# PIN-084: M20 Policy Compiler & Deterministic Runtime

**Date:** 2025-12-15
**Status:** COMPLETE
**Milestone:** M20 / MN-OS Layer 0
**Dependency:** M19 Policy Layer (PIN-078)

---

## Overview

M20 implements the Policy Compiler and Deterministic Runtime for MN-OS, providing:

- **PLang v2.0**: Policy language with M19 category support
- **AST with Governance**: Abstract syntax tree with M19 metadata
- **IR v2.0**: Category-aware intermediate representation
- **Governance-Aware Optimizer**: Conflict resolution and DAG sorting
- **Deterministic Runtime**: No randomness, reproducible execution

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PLang Source                             │
│   policy safety_check: SAFETY { when blocked then deny }        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TOKENIZER                                  │
│   Keywords: policy, rule, when, then, deny, allow, ...          │
│   Categories: SAFETY, PRIVACY, OPERATIONAL, ROUTING, CUSTOM     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        PARSER                                   │
│   Produces AST with GovernanceMetadata attached                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      IR BUILDER                                 │
│   AST → IR with governance propagation                          │
│   Symbol table with category indexing                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OPTIMIZER                                  │
│   - Constant folding (preserve governance)                      │
│   - Dead code elimination (preserve audit)                      │
│   - Conflict resolution (category precedence)                   │
│   - DAG sorting (execution order)                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DETERMINISTIC RUNTIME                          │
│   - No randomness                                               │
│   - Reproducible execution                                      │
│   - Intent emission to M18                                      │
│   - Full audit trail                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## PLang v2.0 Grammar

```ebnf
program         ::= statement*
statement       ::= policy_decl | rule_decl | import_stmt
policy_decl     ::= 'policy' IDENT ':' category '{' policy_body '}'
category        ::= 'SAFETY' | 'PRIVACY' | 'OPERATIONAL' | 'ROUTING' | 'CUSTOM'
policy_body     ::= (rule_ref | condition_block | action_block)*
rule_ref        ::= 'rule' IDENT
condition_block ::= 'when' expr 'then' action_block
action_block    ::= 'deny' | 'allow' | 'escalate' | 'route' route_target
route_target    ::= 'to' IDENT
expr            ::= or_expr
or_expr         ::= and_expr ('or' and_expr)*
and_expr        ::= not_expr ('and' not_expr)*
not_expr        ::= 'not' not_expr | comparison
comparison      ::= value (comp_op value)?
comp_op         ::= '==' | '!=' | '<' | '>' | '<=' | '>='
value           ::= IDENT | NUMBER | STRING | 'true' | 'false' | func_call | attr_access
```

---

## M19 Category Integration

| Category | Priority | Execution Phase | Description |
|----------|----------|-----------------|-------------|
| SAFETY | 100 | SAFETY_CHECK | Safety rules execute first |
| PRIVACY | 90 | PRIVACY_CHECK | Data protection |
| OPERATIONAL | 50 | OPERATIONAL | Business logic |
| ROUTING | 30 | ROUTING | Agent routing |
| CUSTOM | 10 | CUSTOM | User-defined |

### Category Precedence Rules

1. **Execution Order**: SAFETY → PRIVACY → OPERATIONAL → ROUTING → CUSTOM
2. **Conflict Resolution**: Higher category wins
3. **Action Precedence**: DENY > ESCALATE > ROUTE > ALLOW

---

## Components

### 1. Compiler (`app/policy/compiler/`)

| File | Purpose |
|------|---------|
| `grammar.py` | PLang v2.0 grammar definition |
| `tokenizer.py` | Lexical analysis |
| `parser.py` | Syntax analysis → AST |

### 2. AST (`app/policy/ast/`)

| File | Purpose |
|------|---------|
| `nodes.py` | AST node definitions with governance |
| `visitors.py` | AST traversal patterns |

### 3. IR (`app/policy/ir/`)

| File | Purpose |
|------|---------|
| `ir_nodes.py` | IR instruction definitions |
| `symbol_table.py` | Symbol management with category indexing |
| `ir_builder.py` | AST → IR transformation |

### 4. Optimizer (`app/policy/optimizer/`)

| File | Purpose |
|------|---------|
| `folds.py` | Constant folding, dead code elimination |
| `conflict_resolver.py` | Category-based conflict resolution |
| `dag_sorter.py` | Topological sort for execution order |

### 5. Runtime (`app/policy/runtime/`)

| File | Purpose |
|------|---------|
| `deterministic_engine.py` | Deterministic execution engine |
| `dag_executor.py` | DAG-based parallel execution |
| `intent.py` | M18 intent emission |

---

## Example Usage

### PLang Policy

```plang
# Safety check first
policy security_check: SAFETY {
    when user.role == "blocked" then deny
    when contains(request.data, "secret") then escalate
}

# Routing logic
policy route_complex: ROUTING {
    when agent.type == "specialist" then route to expert_handler
}

# Default allow
policy default_policy: CUSTOM {
    allow
}
```

### Python API

```python
from app.policy.compiler import Parser
from app.policy.ir import IRBuilder
from app.policy.runtime import DAGExecutor, ExecutionContext

# Compile
parser = Parser.from_source(source)
ast = parser.parse()

builder = IRBuilder()
module = builder.build(ast)

# Execute
executor = DAGExecutor()
ctx = ExecutionContext(
    request_id="req_123",
    user_id="user_456",
)
ctx.variables["user"] = {"role": "admin"}
ctx.variables["agent"] = {"type": "basic"}

trace = await executor.execute(module, ctx)

print(f"Action: {trace.final_action}")
print(f"Intents: {len(trace.all_intents)}")
```

---

## Intent System

Intents bridge policy decisions to M18 execution:

| Intent Type | Purpose |
|-------------|---------|
| DENY | Block request with reason |
| ALLOW | Permit request |
| ESCALATE | Require approval |
| ROUTE | Route to specific agent |
| EXECUTE | Execute with constraints |
| LOG | Audit only |
| ALERT | Alert without blocking |

### Intent Structure

```python
Intent(
    id="int_abc123...",
    intent_type=IntentType.ROUTE,
    payload=IntentPayload(
        target_agent="expert_handler",
        request_id="req_123",
        budget_limit=100.0,
    ),
    priority=80,
    governance={
        "source_policy": "route_complex",
        "category": "ROUTING",
    },
)
```

---

## Deterministic Execution

### Principles

1. **No Randomness**: Every execution path is reproducible
2. **Step Counting**: Time measured in steps, not wall clock
3. **Governance First**: Safety checks before any action
4. **Full Audit**: Every instruction traced

### Execution Context

```python
ctx = ExecutionContext(
    execution_id="exec_...",  # Deterministic from inputs
    request_id="req_123",
    user_id="user_456",
    variables={...},
    max_steps=10000,  # Prevent infinite loops
)
```

### Execution Trace

```python
trace = ExecutionTrace(
    execution_id="exec_...",
    total_stages=3,
    stage_results=[...],
    final_action=ActionType.ALLOW,
    all_intents=[...],
    total_steps=42,
    safety_checks_passed=1,
    privacy_checks_passed=1,
)
```

---

## Tests

| Test File | Coverage |
|-----------|----------|
| `test_m20_parser.py` | Tokenizer, parser, AST |
| `test_m20_ir.py` | IR nodes, symbol table, builder |
| `test_m20_optimizer.py` | Folds, conflict resolution, DAG |
| `test_m20_runtime.py` | Engine, executor, intents |

Run tests:

```bash
PYTHONPATH=. python -m pytest tests/test_m20_*.py -v
```

---

## Integration Points

### M18 Integration

```python
# Intent emitted by policy runtime
intent = Intent(
    intent_type=IntentType.ROUTE,
    payload=IntentPayload(target_agent="expert"),
)

# M18 receives and executes
await m18_executor.execute_intent(intent)
```

### M19 Integration

```python
# IR builder uses M19 categories
governance = IRGovernance.from_ast(node.governance)
# Category: SAFETY
# Priority: 100

# Conflict resolver uses M19 precedence
resolver = ConflictResolver()
resolved_module, conflicts = resolver.resolve(module)
```

### M4 Integration

```python
# DAG sorter produces ExecutionPlan for M4
plan = executor.get_execution_plan(module)
# ExecutionPlan:
#   stages: [["safety_check"], ["route_complex"], ["default_policy"]]
#   total_policies: 3
```

---

## Files Created

```
backend/app/policy/
├── compiler/
│   ├── __init__.py
│   ├── grammar.py
│   ├── tokenizer.py
│   └── parser.py
├── ast/
│   ├── __init__.py
│   ├── nodes.py
│   └── visitors.py
├── ir/
│   ├── __init__.py
│   ├── ir_nodes.py
│   ├── symbol_table.py
│   └── ir_builder.py
├── optimizer/
│   ├── __init__.py
│   ├── folds.py
│   ├── conflict_resolver.py
│   └── dag_sorter.py
└── runtime/
    ├── __init__.py
    ├── deterministic_engine.py
    ├── dag_executor.py
    └── intent.py

backend/tests/
├── test_m20_parser.py
├── test_m20_ir.py
├── test_m20_optimizer.py
└── test_m20_runtime.py
```

---

## MN-OS Subsystem

| Attribute | Value |
|-----------|-------|
| Milestone | M20 |
| MN-OS Name | Policy Execution Core |
| Acronym | **PXC** |
| Layer | 0 (Foundation) |

---

## Next Steps

1. **M20.1**: API endpoints for policy compilation
2. **M20.2**: Policy hot-reload support
3. **M20.3**: Policy versioning and rollback
4. **IAEC v4.0**: Integration with multi-agent slot negotiation (PIN-083)

---

*PIN-084 created 2025-12-15 (M20 Implementation Complete)*
