# OpenAPI-Safe Model Checklist

**Status:** ACTIVE
**Effective:** 2026-01-19
**Reference:** PIN-444

---

## Prime Directive

> **OpenAPI is not a domain engine. Treat it like a dumb documentation serializer.**

Response models used in `response_model=` MUST be OpenAPI-safe.
OpenAPI generation is a **static graph expansion**, not runtime logic.

---

## The 3 Patterns That ALWAYS Cause OpenAPI Hangs

### Pattern A: Recursive Reference (Most Common)

```python
# ❌ FORBIDDEN - Causes infinite loop
class SignalProjection(BaseModel):
    feedback: SignalFeedbackModel

class SignalFeedbackModel(BaseModel):
    signal: SignalProjection  # Recursion!
```

**Fix:** Break the cycle with a flat summary model:

```python
# ✅ CORRECT
class SignalProjection(BaseModel):
    feedback: SignalFeedbackSummary | None

class SignalFeedbackSummary(BaseModel):
    acknowledged: bool
    suppressed_until: datetime | None
    # NO back-reference to SignalProjection
```

### Pattern B: Union Explosion

```python
# ❌ DANGEROUS - Combinatorial explosion
metadata: PolicyMetadata | ThresholdMetadata | LessonMetadata | ViolationMetadata
```

OpenAPI tries to enumerate **every branch** with nested models.

**Fix:** Use discriminated unions or flatten:

```python
# ✅ CORRECT
class BaseMetadata(BaseModel):
    kind: Literal["policy", "threshold", "lesson", "violation"]
    # Common fields only

metadata: BaseMetadata
```

### Pattern C: Executable Defaults

```python
# ❌ FORBIDDEN in response models
metadata: PolicyMetadata = Field(default_factory=build_policy_metadata)
created_at: datetime = Field(default_factory=datetime.utcnow)
```

OpenAPI **evaluates** defaults. If your factory:
- Touches env vars
- Touches DB
- Constructs nested models

This causes **non-terminating generation**.

**Fix:** No default_factory in API models:

```python
# ✅ CORRECT
metadata: PolicyMetadata | None = None
created_at: datetime | None = None
# Populate in endpoint code, not model defaults
```

---

## OpenAPI-Safe Model Rules

### Rule 1: Facade Models Must Be FLAT

Response models may contain ONLY:
- Primitives (str, int, float, bool)
- Enums
- Timestamps (datetime as str)
- IDs / refs (strings)
- **Non-recursive** nested models

### Rule 2: NO default_factory in API Models

This is **non-negotiable**.

| ❌ Forbidden | ✅ Correct |
|-------------|-----------|
| `Field(default_factory=build_x)` | `x: X \| None = None` |
| `Field(default_factory=datetime.utcnow)` | `created_at: str \| None = None` |
| `Field(default_factory=list)` | `items: list = []` |

### Rule 3: NO Union-Heavy Response Models

| ❌ Dangerous | ✅ Safe |
|-------------|---------|
| `Union[A, B, C]` with nested models | `BaseModel` with `kind: Literal[...]` |
| `A \| B \| C` in response | Single flat model per endpoint |

### Rule 4: Max 3 Levels of Nesting

```python
# ❌ Too deep
class Response(BaseModel):
    data: DataWrapper
        # -> nested: NestedData
        #    -> deep: DeepData
        #       -> deeper: DeeperData  # TOO DEEP

# ✅ Flatten
class Response(BaseModel):
    data_id: str
    nested_summary: str
    deep_value: int
```

---

## Model Location Rule

> **Only models under `api/schemas/` may be used as `response_model`**

Create a clear boundary:

```
backend/app/
├── api/
│   ├── schemas/           # OpenAPI-safe response models ONLY
│   │   ├── activity.py
│   │   ├── incidents.py
│   │   └── ...
│   └── routers/
├── domain/                # Domain models (NOT for response_model)
└── models/                # ORM models (NEVER for response_model)
```

---

## Debugging OpenAPI Hangs

### Step 1: Use Debug Endpoints

```bash
# Cache-free generation (if this hangs → schema problem)
curl http://localhost:8000/__debug/openapi_nocache

# Schema inspection (shows potential issues)
curl http://localhost:8000/__debug/openapi_inspect
```

### Step 2: Binary Search Routers

```python
# In main.py, comment out routers one by one
# app.include_router(activity.router)
# app.include_router(policy.router)
# app.include_router(incidents.router)
```

Enable one at a time, test `/openapi.json`.

### Step 3: Binary Search Response Models

Inside the guilty router:

```python
# Remove response_model temporarily
@router.get("/signals")
async def get_signals():
    # If OpenAPI works now → response model is the problem
    ...
```

### Step 4: Simplify the Bad Model

Replace with dummy:

```python
class Dummy(BaseModel):
    ok: bool
```

If OpenAPI works → the original model is broken.

Recursively simplify:
1. Remove nested models
2. Remove unions
3. Remove default values
4. Find the exact field

---

## CI Enforcement

Add to CI pipeline:

```yaml
- name: OpenAPI Health Check
  run: |
    pytest tests/test_openapi_health.py -v --timeout=30
```

This catches:
- Generation timeout (> 5s)
- Excessive recursion
- Union explosion
- Cache issues

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAPI_TIMEOUT_THRESHOLD` | `10.0` | Log CRITICAL if exceeded |
| `OPENAPI_HARD_FAIL_ON_SLOW` | `false` | Fail startup if exceeded |
| `WARM_OPENAPI_ON_STARTUP` | `true` | Pre-generate at startup |

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│           OPENAPI-SAFE MODEL CHECKLIST                      │
├─────────────────────────────────────────────────────────────┤
│  ☐ No recursive references (A → B → A)                      │
│  ☐ No Union[A, B, C] with nested models                     │
│  ☐ No default_factory in response models                    │
│  ☐ Max 3 levels of nesting                                  │
│  ☐ Flat facade models only                                  │
│  ☐ Model in api/schemas/ (not domain/ or models/)          │
│  ☐ Tested: pytest tests/test_openapi_health.py             │
└─────────────────────────────────────────────────────────────┘
```

---

## Reference

- **PIN-444:** OpenAPI Health Monitoring
- **Debug Endpoints:** `/__debug/openapi_nocache`, `/__debug/openapi_inspect`
- **Test File:** `backend/tests/test_openapi_health.py`
- **Main Implementation:** `backend/app/main.py` (custom_openapi function)
