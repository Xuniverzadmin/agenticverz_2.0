# Semantic Artifacts Registry

**Status:** ACTIVE
**Created:** 2026-01-01
**Reference:** PIN-264 (Phase-S)

---

## Purpose

This document defines semantic boundaries for cross-cutting infrastructure artifacts.
It prevents drift, ensures correct layer placement, and forbids misuse.

---

## Phase-S Infrastructure Artifacts

### 1. ErrorEnvelope (`app.infra.error_envelope`)

**Layer:** L6 (Platform Substrate)
**Namespace:** `infra.*`
**Purpose:** Unified forensic error capture

#### Semantic Boundaries

| Constraint | Rule |
|------------|------|
| **Exposure** | NEVER return from L2 APIs, render in UI, or use as product contract |
| **Mutability** | Immutable after creation (frozen dataclass) |
| **Secrets** | NEVER store raw input, only `input_hash` |
| **Persistence** | Append-only, no updates, no deletes |

#### Emission Rules by Layer

| Layer | Allowed `error_class` Prefixes | Forbidden |
|-------|-------------------------------|-----------|
| L2 (API) | `infra.*`, `system.*` | `domain.*` |
| L3 (Adapter) | `infra.*`, `system.*` | `domain.*` |
| L4 (Domain) | `domain.*`, `system.*` | `infra.*` |
| L5 (Worker) | `infra.*`, `system.*` | `domain.*` |
| L6 (Platform) | `infra.*`, `system.*` | `domain.*` |

**Rationale:**
- Workers (L5) execute but do not interpret domain meaning
- Domain engines (L4) own business semantics, not infrastructure failures
- Mixing these collapses diagnostic value

#### Error Class Taxonomy

| Prefix | Semantic Meaning | Owner |
|--------|-----------------|-------|
| `infra.*` | External dependency failures | Platform layer |
| `domain.*` | Business logic violations | Domain engines |
| `system.*` | Internal system failures | Any layer |

---

### 2. CorrelationContext (`app.infra.correlation`)

**Layer:** L6 (Platform Substrate)
**Namespace:** `infra.*`
**Purpose:** Request/workflow tracing

#### Semantic Boundaries

| Constraint | Rule |
|------------|------|
| **Propagation** | Thread-safe via `contextvars` |
| **Hierarchy** | Parent-child spans allowed |
| **Immutability** | Context objects are frozen |
| **Exposure** | Correlation IDs MAY appear in logs, NEVER in product responses |

#### Usage Pattern

```python
from app.infra import correlation_scope, child_span

# API boundary
with correlation_scope(component="api.runs") as ctx:
    # Domain call
    with child_span("domain.budget_check"):
        check_budget(ctx.correlation_id)
    # Worker dispatch
    with child_span("worker.execution"):
        dispatch_run(ctx.correlation_id)
```

---

## Forbidden Patterns

### F1: Infra-to-Product Leak

```python
# FORBIDDEN: Returning ErrorEnvelope to client
@router.post("/runs")
async def create_run():
    try:
        ...
    except Exception as e:
        envelope = ErrorEnvelope.create(...)
        return envelope.to_dict()  # ❌ VIOLATION
```

**Correct Pattern:**
```python
# Product error model at API boundary
class APIError(BaseModel):
    code: str
    message: str
    request_id: str  # Can include correlation_id

@router.post("/runs")
async def create_run():
    try:
        ...
    except Exception as e:
        # Emit infra envelope for forensics
        envelope = ErrorEnvelope.create(...)
        persist_error(envelope)
        # Return product error to client
        return APIError(code="run_failed", message="...", request_id=correlation_id)
```

### F2: Domain Errors from Workers

```python
# FORBIDDEN: Worker emitting domain.* error
class RecoveryWorker:
    def execute(self):
        # ❌ Workers don't own domain semantics
        emit_error(error_class=ErrorClass.DOMAIN_POLICY_VIOLATION)
```

**Correct Pattern:**
```python
# Worker emits system.* or infra.*
class RecoveryWorker:
    def execute(self):
        # ✅ Workers report execution failures
        emit_error(error_class=ErrorClass.SYSTEM_RECOVERY_FAILED)
```

### F3: Infra Errors from Domain Engines

```python
# FORBIDDEN: Domain engine emitting infra.* error
class BudgetEngine:
    def evaluate(self):
        # ❌ Domain engines don't own infrastructure
        emit_error(error_class=ErrorClass.INFRA_TIMEOUT)
```

**Correct Pattern:**
```python
# Domain engine emits domain.* or system.*
class BudgetEngine:
    def evaluate(self):
        # ✅ Domain engines report domain violations
        emit_error(error_class=ErrorClass.DOMAIN_BUDGET_EXCEEDED)
```

---

## Validation

### Mechanical Checks (Future CI)

| Check | Rule | Enforcement |
|-------|------|-------------|
| `SEMANTIC-001` | L2 never returns `ErrorEnvelope` | AST scan |
| `SEMANTIC-002` | L5 never emits `domain.*` | Runtime assertion |
| `SEMANTIC-003` | L4 never emits `infra.*` | Runtime assertion |
| `SEMANTIC-004` | `ErrorEnvelope` never in `__all__` of L2 modules | Import scan |

---

## Related Documents

- PIN-264: Phase-S System Readiness
- PIN-263: Phase R Structural Repair
- PIN-240: Seven-Layer Model
- `docs/playbooks/SESSION_PLAYBOOK.yaml`: Session rules
