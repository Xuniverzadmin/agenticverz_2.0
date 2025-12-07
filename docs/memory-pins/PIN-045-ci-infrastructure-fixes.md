# PIN-045: CI Infrastructure Fixes & Stability Session

**Date:** 2025-12-07
**Status:** COMPLETE
**Category:** Infrastructure / CI / Operations
**Impact:** Blocking CI Pipeline → Fully Passing

---

## Summary

This PIN documents the resolution of multiple CI pipeline failures during M8 development. All issues were infrastructure-related, not code defects. The fixes establish a more robust and observable CI environment.

---

## Issues Resolved

### 1. Concurrency Limiter Race Condition

| Attribute | Value |
|-----------|-------|
| **Job** | integration |
| **Test** | `test_concurrent_limiter_respects_max_slots` |
| **Root Cause** | TOCTOU between ZCARD and ZADD |
| **Fix** | Atomic Lua script |
| **Commit** | `77f1773` |

**Technical Detail:**
The ConcurrentRunsLimiter used separate Redis operations for check and add:
```python
# Vulnerable: Race window between lines
current = client.zcard(slot_key)
if current >= max_slots:
    return None
client.zadd(slot_key, {token: now})
```

Replaced with atomic Lua script:
```lua
local current = redis.call('ZCARD', slot_key)
if current >= max_slots then
    return 0
end
redis.call('ZADD', slot_key, now, token)
return 1
```

**File:** `backend/app/utils/concurrent_runs.py:25-46`

---

### 2. Redis Service Configuration Mismatch

| Attribute | Value |
|-----------|-------|
| **Job** | integration |
| **Test** | Multiple concurrency tests |
| **Root Cause** | UPSTASH_REDIS_URL secret overriding Docker Redis |
| **Fix** | Explicit REDIS_URL in CI env |
| **Commit** | `e9cdd50` |

**Technical Detail:**
CI had `UPSTASH_REDIS_URL` secret which the app tried to use. But this external Redis was not accessible from the CI runner.

Docker Redis service container was running on `localhost:6379` but not being used.

Fix explicitly sets `REDIS_URL=redis://localhost:6379/0` in the integration job.

**File:** `.github/workflows/ci.yml` (integration job)

---

### 3. Worker Output Buffering

| Attribute | Value |
|-----------|-------|
| **Job** | e2e-tests |
| **Symptom** | "Run still running after 120s" |
| **Root Cause** | Python stdout buffering with nohup |
| **Fix** | PYTHONUNBUFFERED=1 + python -u flag |
| **Commit** | `b0e0ea0` |

**Technical Detail:**
When running with `nohup`, Python defaults to fully-buffered stdout. Worker logs were never written to disk, making debugging impossible.

```yaml
# Before (buffered)
nohup python -m app.worker.pool > worker.log 2>&1 &

# After (unbuffered)
env:
  PYTHONUNBUFFERED: "1"
run: |
  nohup python -u -m app.worker.pool > worker.log 2>&1 &
```

**File:** `.github/workflows/ci.yml` (e2e-tests job)

---

### 4. WireMock Mapping Files (Previous Session)

| Attribute | Value |
|-----------|-------|
| **Job** | costsim-wiremock |
| **Root Cause** | Missing mapping files |
| **Fix** | Created mapping files |
| **Status** | Fixed before this session |

**File:** `tools/wiremock/mappings/`

---

## Commits

| SHA | Description |
|-----|-------------|
| `77f1773` | fix(concurrency): use atomic Lua script to prevent race condition |
| `e9cdd50` | fix(ci): use Docker Redis for integration tests |
| `b0e0ea0` | fix(ci): improve worker startup with unbuffered output |

---

## CI Run Results

**Final Run:** `20003884770`
**Conclusion:** SUCCESS

All 11 jobs passed:
- migration-check
- unit-tests
- lint-alerts
- determinism
- costsim
- costsim-wiremock
- costsim-integration
- e2e-tests
- integration
- workflow-engine
- workflow-golden-check

---

## Prevention Mechanisms

The following prevention mechanisms were proposed (see PIN-046):

1. **CI Consistency Checker Script** - Pre-flight verification of CI configuration
2. **Service Connectivity Matrix** - Document which services are Docker vs cloud
3. **Mandatory Observability** - All background processes must have health endpoints
4. **Atomic Operation Tests** - Test concurrent slot acquisition to catch races

---

## Related Documents

- **RCA Report:** `docs/RCA-CI-FIXES-2025-12-07.md`
- **Prevention Script:** `scripts/ops/ci_consistency_check.sh`
- **CI Workflow:** `.github/workflows/ci.yml`

---

## M8 Context

This work is part of M8 infrastructure stabilization. M8 focuses on:
- Demo + SDK Packaging
- Auth Integration
- Production hardening

CI stability is a prerequisite for reliable M8 deliverables.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-07 | Initial creation - 4 issues documented |
| 2025-12-07 | All issues resolved, CI fully passing |
