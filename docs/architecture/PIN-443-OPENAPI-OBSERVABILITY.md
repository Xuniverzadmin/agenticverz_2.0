# PIN-443: OpenAPI Cold-Start Observability

**Status:** IMPLEMENTED
**Date:** 2026-01-18
**Category:** Operational Observability

---

## Problem Statement

The VPS appeared to "hang" when accessing `/docs` or `/openapi.json` endpoints. Root cause analysis revealed:

| Metric | Value |
|--------|-------|
| API Paths | 456 |
| Schemas | 493 |
| Schema Size | ~826KB |
| Cold Generation Time | ~1.1-2.7s |

The issue was **not correctness** — it was **cold-start opacity**:
- First `/openapi.json` request blocks while generating schema
- No logging or timing visibility
- Appears like a hang on VPS / docker exec

---

## Design Principles

1. **No impact on request semantics**
2. **No impact on auth, RBAC, or Evidence Plane**
3. **Zero cost when disabled**
4. **Explicitly diagnostic — not "monitoring"**

---

## Solution Components

### 1. Slow Request Timing Middleware

**File:** `backend/app/middleware/slow_requests.py`

Logs warnings for any request exceeding threshold (default 500ms).

```python
if os.getenv("ENABLE_SLOW_REQUEST_LOGS") == "true":
    app.add_middleware(SlowRequestMiddleware, threshold_ms=500)
```

**Log Output:**
```json
{"level": "WARNING", "message": "slow_request", "path": "/openapi.json", "duration_ms": 1500.23}
```

### 2. OpenAPI Generation Tracing

**File:** `backend/app/main.py` (custom_openapi function)

Replaces default FastAPI OpenAPI generator with traced version:

```python
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    logger.info("openapi_generation_started")
    start = time.perf_counter()

    schema = get_openapi(...)

    logger.info("openapi_generation_completed", extra={"duration_ms": ...})

    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi
```

**Log Output:**
```json
{"message": "openapi_generation_started"}
{"message": "openapi_generation_completed", "duration_ms": 1117.75}
```

### 3. Startup Warm-Up Hook

**File:** `backend/app/main.py` (lifespan function)

Pre-generates OpenAPI schema at startup to avoid first-user latency:

```python
if os.getenv("WARM_OPENAPI_ON_STARTUP") == "true":
    logger.info("[BOOT] Warming OpenAPI schema")
    app.openapi()
    logger.info("[BOOT] OpenAPI schema warmed")
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENABLE_SLOW_REQUEST_LOGS` | `false` | Enable slow request logging (> 500ms) |
| `WARM_OPENAPI_ON_STARTUP` | `false` | Pre-generate OpenAPI at startup |

**Recommended Settings:**

| Environment | ENABLE_SLOW_REQUEST_LOGS | WARM_OPENAPI_ON_STARTUP |
|-------------|--------------------------|-------------------------|
| Local/Dev | `true` | `true` |
| Test/CI | `true` | `true` |
| Staging | `true` | `true` |
| Production | `false` | `false` (or `true` for deterministic startup) |

---

## Verification

After deployment, check logs for:

```bash
docker logs nova_agent_manager 2>&1 | grep -E "(Warming|openapi_generation|SlowRequest)"
```

Expected output:
```
[BOOT] SlowRequestMiddleware enabled (threshold=500ms)
[BOOT] Warming OpenAPI schema (WARM_OPENAPI_ON_STARTUP=true)
openapi_generation_completed, duration_ms: 1117.75
[BOOT] OpenAPI schema warmed
```

---

## Performance Impact

| Request | Before | After (warm) |
|---------|--------|--------------|
| First `/openapi.json` | 2.7s | 0.1s |
| Subsequent | 0.1s | 0.1s |
| Startup time | baseline | +1.1s (if warm-up enabled) |

---

## What This Does NOT Do

- Does not reduce schema size
- Does not hide OpenAPI endpoints
- Does not modify routers
- Does not weaken security

The app size is **acceptable** for the domain. This solves a **visibility problem**, not a performance problem.

---

## Files Modified

| File | Change |
|------|--------|
| `backend/app/middleware/slow_requests.py` | NEW - Slow request middleware |
| `backend/app/main.py` | Added custom_openapi, warm-up hook, middleware registration |
| `docker-compose.yml` | Added env var passthrough |
| `.env` | Added default flags |

---

## Part 2: Customer Sandbox Security Hardening

**Added:** 2026-01-18

As part of the same session, customer_sandbox.py was hardened to address 8 edge cases identified during security review.

### Edge Cases Addressed

| Edge Case | Issue | Resolution |
|-----------|-------|------------|
| EC-1 | Environment drift (prod DB + test mode) | Hard-fail startup gate via `_is_prod_database()` |
| EC-2 | RBAC overreach | Permission ceiling already in place (`SANDBOX_ALLOWED_PERMISSIONS`) |
| EC-3 | Token reuse across environments | Environment fingerprinting via `_compute_sandbox_fingerprint()` |
| EC-4 | SDK bypass | Out of scope (SDK auth separate) |
| EC-5 | Telemetry trust confusion | `billable=False` and `caller_type="sandbox_customer"` immutable |
| EC-6 | Rate limit abuse | Added `SANDBOX_RATE_LIMIT_PER_MINUTE` env var (default: 10) |
| EC-7 | Mixed auth headers | Already addressed (`has_conflicting_auth_headers()`) |
| EC-8 | Silent downgrade | Explicit error via `SandboxAuthResult` dataclass |

### New Components

#### 1. Safety Violation Detection

```python
_SAFETY_VIOLATION_DETECTED = False  # Module-level flag

def _check_environment_safety() -> None:
    """HARD-FAIL on safety violations at module load."""
    global _SAFETY_VIOLATION_DETECTED
    if DATABASE_URL and _is_prod_database(DATABASE_URL):
        _SAFETY_VIOLATION_DETECTED = True
        logger.critical("SANDBOX SAFETY VIOLATION [HARD FAIL]...")
```

#### 2. Production Database Heuristic

```python
def _is_prod_database(db_url: str) -> bool:
    """Fail-safe detection of production database URLs."""
    prod_indicators = [
        "prod" in db_lower and "test" not in db_lower,
        "-prod." in db_lower,
        "neon.tech" in db_lower and "test" not in db_lower,
    ]
    return any(prod_indicators)
```

#### 3. Environment Fingerprinting

```python
def _compute_sandbox_fingerprint() -> str:
    """Bind tokens to environment (AOS_MODE + HOSTNAME + DB_AUTHORITY)."""
    fingerprint_data = f"{AOS_MODE}:{HOSTNAME}:{DB_AUTHORITY}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
```

#### 4. Explicit Error Responses

```python
@dataclass
class SandboxAuthResult:
    """Explicit error responses - never silently downgrade."""
    success: bool
    principal: Optional[SandboxCustomerPrincipal] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
```

### Environment Variables (Sandbox)

| Variable | Default | Purpose |
|----------|---------|---------|
| `SANDBOX_RATE_LIMIT_PER_MINUTE` | `10` | Stricter rate limit for sandbox auth |
| `SANDBOX_HEALTH_CHECK_INTERVAL` | `300` | Health check interval (seconds) |

### Verification Checklist

- [x] Sandbox auth fails hard in `AOS_MODE=prod` — returns `sandbox_not_allowed`
- [x] Sandbox auth cannot touch prod DB (heuristic detection) — `_SAFETY_VIOLATION_DETECTED=True`
- [x] Sandbox principals have capped permissions — `SANDBOX_ALLOWED_PERMISSIONS` ceiling enforced
- [x] Sandbox calls are tagged non-billable — `billable=False` immutable
- [x] Mixed auth headers are rejected — `conflicting_auth_headers` error
- [x] Rate limits are stricter than prod — `SANDBOX_RATE_LIMIT_PER_MINUTE=10`
- [x] Telemetry distinguishes sandbox vs real — `caller_type="sandbox_customer"`, `environment_fingerprint`

### Test Results (2026-01-18)

**Environment:** `AOS_MODE=prod`, `CUSTOMER_SANDBOX_ENABLED=false`, `DB_AUTHORITY=neon`

#### Production Mode Tests

| Test Case | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Valid sandbox key | Blocked | `sandbox_not_allowed` | PASS |
| Conflicting headers | Detected | `has_conflicting_auth_headers=True` | PASS |
| No sandbox header | Fall through | `error_code=None` | PASS |

#### Simulated Test Mode Tests

| Test Case | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Valid sandbox key | Success | `success=True`, `billable=False` | PASS |
| Environment fingerprint | Bound | `3822f70882315cce` | PASS |
| Conflicting headers | Error | `conflicting_auth_headers` | PASS |
| Invalid key | Error | `invalid_sandbox_key` | PASS |

#### Safety Violation Tests

| Test Case | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Test mode + prod DB | Hard fail | `_SAFETY_VIOLATION_DETECTED=True` | PASS |
| Auth after violation | Blocked | `sandbox_safety_violation` | PASS |
| `is_sandbox_allowed()` | False | `False` (permanently disabled) | PASS |

#### Prod Database Detection

| URL Pattern | Expected | Actual | Status |
|-------------|----------|--------|--------|
| `prod-db.neon.tech` | is_prod=True | True | PASS |
| `test-db.neon.tech` | is_prod=False | False | PASS |
| `localhost:5432` | is_prod=False | False | PASS |
| `my-prod.cluster.aws.com` | is_prod=True | True | PASS |

### Files Modified (Sandbox)

| File | Change |
|------|--------|
| `backend/app/auth/customer_sandbox.py` | Added safety checks, fingerprinting, explicit errors |

---

## Related

- PIN-413: System Record Capture (startup/shutdown logging)
- PIN-440: Customer Sandbox Authentication Mode
- Layer: L2 (Product APIs / Middleware), L3 (Boundary Adapters)
