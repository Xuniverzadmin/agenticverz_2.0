# PIN-166: M10 Services Health & Fixes

**Status:** COMPLETE
**Category:** Bug Fix / Authentication / Observability / Operations
**Created:** 2025-12-25
**Updated:** 2025-12-25
**Incident:** Multiple M10 service failures including auth issues and SQL syntax errors

---

## Executive Summary

The M10 Observability Validation service was sending false-positive alert emails because the `api_capabilities` scenario was failing due to authentication issues, not actual skill availability problems.

**Root Cause:** Triple authentication mismatch:
1. Wrong header name (`X-API-Key` vs `X-AOS-Key`)
2. Legacy auth fallback disabled (`AOS_USE_LEGACY_AUTH=false`)
3. Legacy fallback missing from `get_tenant_context()` function

---

## Issue Details

### Symptoms
- Email alerts sent from `alerts@agenticverz.com` to `admin1@agenticverz.com`
- Subject: `[CRITICAL] M10 Validation Failed`
- Failed scenario: `api_capabilities: Expected >=5 skills, got 0`

### Trigger
- Systemd timer: `m10-observability-validation.timer`
- Service: `m10-observability-validation.service`
- Script: `scripts/ops/m10_observability_validation.py`

---

## Root Cause Analysis

### RC1: Wrong Header Name

**Location:** `scripts/ops/m10_observability_validation.py:843`

```python
# Before (wrong)
headers={"X-API-Key": api_key}

# After (correct)
headers={"X-AOS-Key": api_key}
```

**Evidence:** `tenant_auth.py:254` expects `X-AOS-Key` header.

### RC2: Legacy Auth Disabled

**Location:** `.env` file

```bash
# Was missing
AOS_USE_LEGACY_AUTH=true

# Also missing from docker-compose.yml environment section
```

### RC3: Legacy Fallback Missing from get_tenant_context

**Location:** `backend/app/auth/tenant_auth.py`

The `get_tenant_context()` function called `validate_api_key_db()` which checks for `aos_` prefix. If that failed, there was no fallback to legacy auth.

**Fix:** Added legacy fallback to `get_tenant_context()` at lines 304-317.

---

## Fixes Applied

### 1. Updated Header Name
```diff
- headers={"X-API-Key": api_key}
+ headers={"X-AOS-Key": api_key},  # Fixed: was X-API-Key
```

### 2. Added AOS_USE_LEGACY_AUTH to .env
```bash
echo "AOS_USE_LEGACY_AUTH=true" >> /root/agenticverz2.0/.env
```

### 3. Added to docker-compose.yml
```yaml
environment:
  AOS_USE_LEGACY_AUTH: ${AOS_USE_LEGACY_AUTH:-false}
```

### 4. Added Legacy Fallback to get_tenant_context
```python
# If DB validation fails, try legacy fallback
if error and _USE_LEGACY_AUTH and _LEGACY_API_KEY and api_key == _LEGACY_API_KEY:
    context = TenantContext(
        tenant_id="legacy",
        tenant_slug="legacy",
        tenant_name="Legacy API Key",
        plan="enterprise",
        api_key_id="legacy",
        api_key_name="Environment API Key",
        permissions=["*"],
    )
    request.state.tenant_context = context
    return context
```

---

## Verification

After fix, all 8 scenarios pass:

```
[OK] neon_write_read
[OK] neon_referential_integrity
[OK] neon_latency_threshold
[OK] redis_stream_operations
[OK] redis_hash_operations
[OK] redis_latency
[OK] api_health
[OK] api_capabilities - API returned 7 skills
```

---

## Prevention Mechanisms

| ID | Prevention | Implementation |
|----|------------|----------------|
| **PREV-20** | API key pre-flight validation | Add check in M10 script to verify auth before running scenarios |
| **PREV-21** | Header name consistency | Document canonical header name in CLAUDE.md |
| **PREV-22** | Alerting self-test | Before alerting on failures, verify test harness can authenticate |

### Recommended Future Improvements

1. **Create proper API key** - Generate an `aos_xxx` prefixed key, store in database, avoid legacy fallback
2. **Add auth validation scenario** - Explicit scenario that tests authentication before other scenarios
3. **Improve error messages** - If auth fails, return clear "authentication failed" not empty skills

---

## Files Changed

| File | Change |
|------|--------|
| `scripts/ops/m10_observability_validation.py` | Changed `X-API-Key` to `X-AOS-Key` (line 843) |
| `backend/app/auth/tenant_auth.py` | Added legacy fallback to `get_tenant_context()` (lines 304-317) |
| `docker-compose.yml` | Added `AOS_USE_LEGACY_AUTH` env var (line 39) |
| `.env` | Added `AOS_USE_LEGACY_AUTH=true` |

---

## Related PINs

- PIN-032: M7 RBAC Enablement (auth system)
- PIN-050: M10 Recovery Suggestion Engine (M10 validation origin)

---

## Additional Fix: Synthetic Traffic SQL Error

### Issue
`m10-synthetic-traffic.service` failing with SQL syntax error:
```
syntax error at or near ":"
LINE 6: :payload::jsonb
```

### Root Cause
SQLAlchemy `text()` interprets `:payload` as a named parameter, but `::jsonb` is PostgreSQL cast syntax. The double colon conflicts with parameter parsing.

### Fix
Changed from `::jsonb` cast syntax to `CAST()` function:
```diff
- :payload::jsonb
+ CAST(:payload AS jsonb)
```

**File:** `scripts/ops/m10_synthetic_traffic.py:109`

---

## M10 Services Summary

| Service | Status | Schedule | Purpose |
|---------|--------|----------|---------|
| `m10-observability-validation` | **FIXED** | 2x/day (08:00, 20:00) | Neon, Redis, API health checks |
| `m10-synthetic-traffic` | **FIXED** | 2x/day (09:00, 21:00) | Generate test events for outbox |
| `m10-metrics-collector` | Running | Daemon (30s interval) | Collect Prometheus metrics |
| `m10-maintenance` | OK | Every 5 min | Lock cleanup, maintenance tasks |
| `m10-48h-health` | OK | Every 15 min | Pager window health check |
| `m10-daily-stats` | OK | Daily (01:05) | Export daily stats to CSV |
| `m10-synthetic-validation` | OK | Every 30 min | Validate synthetic data in Neon/Upstash |

### Timer Frequency Optimization

Reduced frequencies to conserve resources and Resend email quota:

| Timer | Before | After | Reason |
|-------|--------|-------|--------|
| `m10-observability-validation` | Every 1 hour | 2x/day | Save Resend emails |
| `m10-synthetic-traffic` | Every 30 min | 2x/day | Reduce DB load |

---

## Metrics Collector Warning

The `m10-metrics-collector` shows non-fatal warnings:
```
Failed to collect candidate stats: No module named 'app.database'
```

**Impact:** Low - metrics collector continues running, some stats unavailable.
**Status:** Known limitation, not blocking.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-25 | Added synthetic traffic SQL fix, timer optimizations, full service summary |
| 2025-12-25 | Initial creation - Auth fix for M10 validation |
