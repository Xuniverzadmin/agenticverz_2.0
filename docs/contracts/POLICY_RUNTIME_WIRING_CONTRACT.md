# Policy Runtime Wiring Contract

**Status:** ACTIVE
**Version:** 1.0
**Effective:** 2026-02-03
**Last Updated:** 2026-02-03
**Scope:** Policy Runtime (M18/M19/M20)
**Reference:** PIN-514, PIN-515

---

## 0. Prime Invariant (LOCKED)

> **Enforcement intents block without explicit validator wiring.**

The policy runtime implements fail-closed semantics. Any intent that could cause real-world actions (EXECUTE, ROUTE, ESCALATE) is blocked unless a validator is explicitly wired.

---

## 1. Injection Points

| Injection Point | Protocol | Location | Default (None) |
|-----------------|----------|----------|----------------|
| `intent_validator` | `PolicyIntentValidator` | `IntentEmitter.__init__` | BLOCK enforcement intents |
| `emission_sink` | `Callable[[dict], Awaitable[None]]` | `IntentEmitter.__init__` | Structured logging only |
| `policy_validator` | `PolicyCheckValidator` | `DeterministicEngine.__init__` | `register=False` (deny) |

### 1.1 Protocol Definitions

```python
# app/hoc/cus/policies/L5_schemas/intent_validation.py
class PolicyIntentValidator(Protocol):
    async def validate_intent(self, intent: Any) -> PolicyIntentValidationResult:
        """Validate an intent before emission."""
        ...

PolicyIntentValidationResult = TypedDict("PolicyIntentValidationResult", {
    "allowed": bool,
    "errors": List[str],
})

# app/hoc/cus/policies/L5_schemas/policy_check.py
class PolicyCheckValidator(Protocol):
    async def validate_policy(
        self, policy_id: str, context: Dict[str, Any]
    ) -> PolicyCheckResult:
        """Validate a policy check instruction."""
        ...
```

---

## 2. Intent Type Classification

| Type | Category | Validation | Default Behavior |
|------|----------|------------|------------------|
| EXECUTE | Enforcement | Requires M19 validator | BLOCKED if no validator |
| ROUTE | Enforcement | Requires M19 validator | BLOCKED if no validator |
| ESCALATE | Enforcement | Requires M19 validator | BLOCKED if no validator |
| ALLOW | Observability | Structural only | PASSES (no side effects) |
| DENY | Observability | Structural only | PASSES (no side effects) |
| LOG | Observability | Structural only | PASSES (no side effects) |
| ALERT | Observability | Structural only | PASSES (no side effects) |

### 2.1 Enforcement vs Observability

**Enforcement intents** (EXECUTE, ROUTE, ESCALATE):
- Can cause real-world actions
- Require explicit M19 validation
- Fail-closed: blocked without validator

**Observability intents** (ALLOW, DENY, LOG, ALERT):
- Record decisions only
- No side effects beyond logging
- Pass with structural validation only

---

## 3. Environment Wiring Matrix

| Environment | `intent_validator` | `emission_sink` | `policy_validator` |
|-------------|-------------------|-----------------|-------------------|
| Unit tests | Permissive stub | `None` (log) | `None` or permissive |
| Integration tests | Real M19 or stub | Test sink | Real or stub |
| Staging | Real M19 | Real M18 queue | Real M19 |
| Production | Real M19 | Real M18 queue | Real M19 |

### 3.1 Environment Rationale

- **Unit tests**: Fast, isolated. Permissive stubs allow testing intent creation logic.
- **Integration tests**: Validate real M19 behavior. Test sinks capture intents for assertions.
- **Staging**: Full production wiring. Catches integration issues before prod.
- **Production**: Full governance enforcement. Real M19 validation, real M18 execution.

---

## 4. Fail-Closed Semantics

### 4.1 Why Fail-Closed?

Enforcement intents can cause real actions:
- EXECUTE → triggers agent execution
- ROUTE → redirects to agents
- ESCALATE → involves human reviewers

Permitting these without validation would bypass governance.

### 4.2 What Gets Blocked?

When `intent_validator` is `None`:
- All EXECUTE intents → blocked with error
- All ROUTE intents → blocked with error
- All ESCALATE intents → blocked with error

The error message:
```
"No M19 validator configured for enforcement intent {type}"
```

### 4.3 What Passes?

Observability intents always pass structural validation:
- LOG → records audit entry
- ALLOW → records permission grant
- DENY → records permission denial
- ALERT → records alert without blocking

---

## 5. Wiring Code Examples

### 5.1 Permissive Validator (Tests)

```python
from app.hoc.cus.policies.L5_engines.intent import IntentEmitter

class PermissiveValidator:
    """Permissive validator for unit tests."""

    async def validate_intent(self, intent):
        return {"allowed": True, "errors": []}

# Usage
emitter = IntentEmitter(intent_validator=PermissiveValidator())
```

### 5.2 Production Wiring (Real M19)

```python
from app.hoc.cus.policies.L5_engines.intent import IntentEmitter
from app.policy.m19 import M19PolicyValidator

# Wire real M19 validator
validator = M19PolicyValidator(config=app_config)
sink = create_m18_queue_sink(config=app_config)

emitter = IntentEmitter(
    intent_validator=validator,
    emission_sink=sink,
)
```

### 5.3 Full Engine Wiring

```python
from app.hoc.cus.policies.L5_engines.deterministic_engine import DeterministicEngine
from app.hoc.cus.policies.L5_engines.intent import IntentEmitter

# Production
engine = DeterministicEngine(
    policy_validator=m19_policy_validator,
    intent_validator=m19_intent_validator,
    emission_sink=m18_queue_sink,
)

# Tests
engine = DeterministicEngine(
    policy_validator=PermissivePolicyValidator(),
    intent_validator=PermissiveIntentValidator(),
    emission_sink=None,  # Log only
)
```

---

## 6. Validation Behavior Matrix

| Scenario | `intent_validator` | Intent Type | Result |
|----------|-------------------|-------------|--------|
| Production | Real M19 | EXECUTE | Validated by M19 |
| Production | Real M19 | LOG | Structural only |
| Test | Permissive | EXECUTE | Always allowed |
| Test | `None` | EXECUTE | **BLOCKED** |
| Test | `None` | LOG | Passes |
| Misconfigured | `None` | ROUTE | **BLOCKED** |

---

## 7. Error Messages Reference

| Condition | Error Message |
|-----------|---------------|
| No validator for enforcement | `"No M19 validator configured for enforcement intent {type}"` |
| Validator exception | `"M19 validation error (fail-closed): {exception}"` |
| Missing required field | `"{type} intent requires {field}"` |

---

## 8. Canonical Runtime Location

```
app/hoc/cus/policies/L5_engines/
├── __init__.py              # Exports all runtime components
├── intent.py                # IntentEmitter, Intent, IntentPayload, IntentType
├── deterministic_engine.py  # DeterministicEngine, ExecutionContext, ExecutionResult
└── dag_executor.py          # DAGExecutor, StageResult, ExecutionTrace
```

Import path: `from app.hoc.cus.policies.L5_engines.intent import IntentEmitter`

---

## 9. Related Documents

- **PIN-514**: Runtime Convergence (eliminated dual copies)
- **PIN-515**: Production Wiring Contract (this document's PIN)
- `app/hoc/cus/policies/L5_schemas/intent_validation.py`: Protocol definitions
- `app/hoc/cus/policies/L5_schemas/policy_check.py`: Policy check protocol

---

## 10. Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-02-03 | 1.0 | Initial contract creation |
