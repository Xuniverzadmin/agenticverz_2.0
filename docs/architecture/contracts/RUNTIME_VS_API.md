# RUNTIME VS API CONTRACT

**Status:** ENFORCED
**Effective:** 2026-01-17
**Scope:** All L4 schemas, L2 API responses, L3 adapters
**Reference:** PIN-LIM Post-Implementation Design Fix

---

## Prime Directive

> **Runtime owns truth. API owns presentation. Never cross the streams.**

---

## 1. Ownership Boundaries

| Layer | Owns | Does Not Own |
|-------|------|--------------|
| **L4 Runtime** | Domain truth, business logic, canonical schemas | Wire format, HTTP concerns, client naming |
| **L2 API** | Request/response shape, HTTP status codes, client experience | Business rules, validation logic, data transformation |
| **L3 Adapter** | Translation between L4 and L2 | Business decisions, direct DB access |

---

## 2. Schema Ownership Rules

### Runtime Schemas (L4) — `app/schemas/{domain}/`

**Responsibility:**
- Define canonical data structures
- Enforce domain invariants via Pydantic validators
- Provide type safety for service layer

**Characteristics:**
- Field names are semantic (see NAMING.md)
- No HTTP-specific fields (`status_code`, `error`, `message`)
- No client-context fields (`_remaining`, `_current`)
- Immutable after domain stabilization

**Example:**

```python
# app/schemas/limits/simulation.py
class HeadroomInfo(BaseModel):
    tokens: int
    runs: int
    cost_cents: int
```

### API Schemas (L2) — `app/api/{domain}/` or inline

**Responsibility:**
- Define wire format for HTTP responses
- Add client-friendly naming
- Include HTTP-specific metadata

**Characteristics:**
- May rename fields for client clarity
- May add computed fields
- May flatten/nest structures for wire efficiency

**Example:**

```python
# app/api/limits/simulate.py
class SimulateResponse(BaseModel):
    decision: str
    allowed: bool
    headroom: dict[str, int] | None  # Adapted from HeadroomInfo
```

---

## 3. The Adapter Pattern (MANDATORY)

### Location

```
app/api/_adapters/{domain}.py
```

### Purpose

Adapters are the **only** place where runtime schemas transform into API responses.

### Structure

```python
# app/api/_adapters/limits.py

from app.schemas.limits.simulation import HeadroomInfo, SimulationResult

def adapt_headroom(headroom: HeadroomInfo | None) -> dict[str, int] | None:
    """Transform runtime HeadroomInfo to API response shape."""
    if headroom is None:
        return None
    return {
        "tokens_remaining": headroom.tokens,
        "runs_remaining": headroom.runs,
        "cost_remaining_cents": headroom.cost_cents,
    }

def adapt_simulation_result(result: SimulationResult) -> dict:
    """Transform runtime SimulationResult to API response."""
    return {
        "decision": result.decision.value,
        "allowed": result.decision == SimulationDecision.ALLOW,
        "blocking_limit_id": result.blocking_limit_id,
        "headroom": adapt_headroom(result.headroom),
        # ... other fields
    }
```

### Usage in API Endpoints

```python
# app/api/limits/simulate.py

from app.api._adapters.limits import adapt_simulation_result

@router.post("/simulate")
async def simulate_execution(...):
    result = await service.simulate(tenant_id, request)
    return adapt_simulation_result(result)  # Single transformation point
```

---

## 4. Forbidden Patterns

### Direct Field Access in API (VIOLATION)

```python
# WRONG — API directly accesses runtime field names
return {
    "tokens_remaining": result.headroom.tokens,  # Coupling to runtime schema
}
```

```python
# RIGHT — API uses adapter
return adapt_headroom(result.headroom)
```

### Runtime Schema with API Naming (VIOLATION)

```python
# WRONG — Runtime schema polluted with API naming
class HeadroomInfo(BaseModel):
    tokens_remaining: int  # This belongs in API layer
```

```python
# RIGHT — Runtime schema is pure
class HeadroomInfo(BaseModel):
    tokens: int  # Semantic, no context
```

### Business Logic in Adapter (VIOLATION)

```python
# WRONG — Adapter making business decisions
def adapt_headroom(headroom):
    if headroom.tokens < 100:
        return {"warning": "low tokens"}  # Business logic!
```

```python
# RIGHT — Adapter only transforms
def adapt_headroom(headroom):
    return {"tokens_remaining": headroom.tokens}
```

---

## 5. Drift Detection

### CI Check: `scripts/ci/check_runtime_api_boundary.py`

Detects:
- API endpoints directly accessing `.tokens`, `.runs`, `.cost_cents` on runtime objects
- Runtime schemas with `_remaining`, `_current`, `_total` suffixes
- Adapters with conditional business logic

### Grep Patterns

```bash
# Find direct runtime access in API layer
grep -rn "\.tokens\b" app/api/ --include="*.py"
grep -rn "\.runs\b" app/api/ --include="*.py"
grep -rn "\.cost_cents\b" app/api/ --include="*.py"

# Should only appear in _adapters/
```

---

## 6. Migration Path (Existing Code)

When fixing existing violations:

1. **Create adapter** in `app/api/_adapters/{domain}.py`
2. **Move transformation** from endpoint to adapter function
3. **Update endpoint** to call adapter
4. **Add test** verifying adapter output matches expected API shape
5. **Verify** runtime schema is pure (no API naming)

---

## 7. Violation Response

```
RUNTIME/API BOUNDARY VIOLATION

Location: {file}:{line}
Pattern: {violation_type}

Found: {code_snippet}
Expected: Use adapter from app/api/_adapters/

Fix:
1. Create adapter function in app/api/_adapters/{domain}.py
2. Move field mapping to adapter
3. Call adapter from endpoint

Reference: docs/architecture/contracts/RUNTIME_VS_API.md
```

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│              RUNTIME VS API BOUNDARY RULES                  │
├─────────────────────────────────────────────────────────────┤
│  L4 Runtime:                                                │
│    - Owns: domain truth, canonical schemas                  │
│    - Names: semantic (tokens, runs, cost_cents)             │
│    - Location: app/schemas/{domain}/                        │
│                                                             │
│  L3 Adapter:                                                │
│    - Owns: transformation only                              │
│    - Location: app/api/_adapters/{domain}.py                │
│    - Rule: no business logic                                │
│                                                             │
│  L2 API:                                                    │
│    - Owns: wire format, client naming                       │
│    - Names: client-friendly (tokens_remaining)              │
│    - Rule: always use adapters                              │
└─────────────────────────────────────────────────────────────┘
```
