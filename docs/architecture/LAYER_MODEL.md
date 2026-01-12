# Layer Model — Function-Route Separation

**Status:** LOCKED
**Effective:** 2026-01-12
**Reference:** PIN-399, FREEZE.md
**Enforcement:** `scripts/ci/check_layer_boundaries.py`

---

## Prime Directive

> **Functions compute or decide.
> Routes expose or trigger.
> Observability records.
> Enforcement blocks.**

No layer may impersonate another.

---

## 1. Canonical Layer Taxonomy

| Layer | Allowed To | Forbidden To |
|-------|------------|--------------|
| **Domain / Function** | Compute, decide, derive | Know HTTP, request, response |
| **Enforcement** | Allow / block | Persist history, query observability |
| **Observability** | Record events | Block, decide, mutate |
| **API Route** | Orchestrate, validate input | Implement business logic |
| **Founder Ops** | Force terminal actions | Silent mutation, retries |

This is a **shared mental checksum**. If violated, the architecture is broken.

---

## 2. File Placement Rules (Mechanical)

### Hard Rule: File Path = Responsibility

If the path is wrong, the code is wrong.

### Allowed Patterns

```
app/billing/
  provider.py        # functions, no FastAPI
  limits.py          # pure logic
  state.py           # enums only

app/protection/
  provider.py        # decisions only
  decisions.py       # enums

app/observability/
  events.py          # schema
  emitters.py        # helpers (no logic)
  provider.py        # storage/query

app/api/
  billing.py         # routes only
  protection.py      # routes only
```

### Forbidden Patterns

```
app/api/cost_tracker.py      # FORBIDDEN
app/billing/routes.py        # FORBIDDEN
app/observability/api.py     # FORBIDDEN
app/protection/http.py       # FORBIDDEN
```

**If it speaks HTTP, it lives in `app/api/`.**
Nothing else may import FastAPI.

---

## 3. Import Guardrails

### Rule A: Domain Code Must Not Import FastAPI

Enforced by CI: `scripts/ci/check_layer_boundaries.py`

```
FORBIDDEN:
  app/billing/*.py      may not import fastapi
  app/protection/*.py   may not import fastapi
  app/observability/*.py may not import fastapi
```

This single check prevents 80% of future rot.

### Rule B: Routes Must Not Contain Business Logic

Routes may only:
- Validate input
- Call a provider
- Return response

If a route file exceeds 200 lines or defines non-trivial logic → review required.

---

## 4. Dependency Direction (Non-Negotiable)

```
Domain Logic (billing/protection)
        ↓
Enforcement
        ↓
Observability (emit only)
        ↓
API Routes (orchestration only)
```

### Forbidden Imports

```python
# NEVER: Routes importing into domain
from app.api.billing import ...           # FORBIDDEN

# NEVER: Observability queried by domain
from app.observability.provider import query  # FORBIDDEN from domain code
```

Observability is **write-only** from the system's perspective.
Query is allowed **only** from ops/founder routes.

---

## 5. Route Naming Convention

### Rule: Routes Describe Exposure, Not Logic

#### Correct

```
GET  /api/v1/billing/status
GET  /api/v1/billing/limits
GET  /api/v1/observability/events   (internal/founder only)
```

#### Forbidden

```
POST /api/v1/billing/check          # FORBIDDEN
POST /api/v1/cost/calculate         # FORBIDDEN
POST /api/v1/protection/decide      # FORBIDDEN
```

Anything named `check`, `decide`, `calculate` is **not a route** — it's a function.

---

## 6. Single Entry Point per Capability

For each capability, define **exactly one route module**:

| Capability | Route File |
|------------|------------|
| Billing | `app/api/billing.py` |
| Protection | `app/api/protection.py` |
| Observability | `app/api/observability.py` |
| Founder Ops | `app/api/founder_*.py` |

If someone adds `billing_extra.py`, that's a smell. Stop it.

---

## 7. Observability Boundary Rules

### Observability may be:
- **Called from anywhere** (emit)
- **Queried only by ops/founder routes** (query)

### OBSERVE-BOUNDARY Contract

```python
"""
OBSERVE-BOUNDARY:
- Emission allowed anywhere
- Query allowed ONLY from ops/founder routes
- Domain code MUST NOT query observability
"""
```

---

## 8. Test Layer Scoping

### Test Directory Must Match Layer

```
tests/billing/         # logic tests
tests/protection/      # logic tests
tests/observability/   # provider tests
tests/api/             # route tests
tests/e2e/             # cross-layer truth
```

**If a test in `tests/api/` asserts billing math → wrong test.**

---

## 9. Architecture Tripwire Tests

Mechanical verification of layer boundaries.

Located in: `tests/architecture/test_layer_boundaries.py`

These tests:
- Verify domain code doesn't import FastAPI
- Verify routes don't contain business logic
- Verify dependency direction is correct

---

## 10. Self-Check Questions

You should be able to answer **yes** to all:

| Question | Required Answer |
|----------|-----------------|
| Can I run billing logic without HTTP? | **Yes** |
| Can I replay history without re-running logic? | **Yes** |
| Can I add a new route without touching billing logic? | **Yes** |
| Can I swap observability storage without touching routes? | **Yes** |

If any answer becomes "no", mixing has started. **Stop and fix.**

---

## Related Documents

- FREEZE.md: Design freeze status
- PIN-399: Onboarding State Machine (master PIN)
- PHASE_8_OBSERVABILITY_UNIFICATION.md: Observability design
