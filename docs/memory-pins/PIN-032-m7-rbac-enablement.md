# PIN-032: M7 RBAC Enablement & Production Hardening

**Status:** ✅ COMPLETE
**Date:** 2025-12-05
**Category:** Milestone / Operations / Security

---

## Summary

This PIN documents the RBAC enablement session for M7, transitioning from `RBAC_ENFORCE=false` to `RBAC_ENFORCE=true` with full middleware integration, smoke testing, and production readiness verification.

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| RBAC Middleware Integration | ✅ COMPLETE | Added to `main.py` |
| docker-compose.yml Updates | ✅ COMPLETE | Added RBAC_ENFORCE, MACHINE_SECRET_TOKEN |
| One-Click Enablement Script | ✅ COMPLETE | `scripts/ops/rbac_oneclick_enable.sh` |
| Smoke Tests | ✅ PASS | 12 passed, 0 failed, 3 warnings |
| PgBouncer Load Test | ✅ PASS | 50 clients, 400 TPS, 0 failures |
| Grafana Dashboard | ✅ COMPLETE | `monitoring/dashboards/m7_rbac_memory_dashboard.json` |
| Integration Tests | ✅ COMPLETE | `backend/tests/integration/test_m7_rbac_memory.py` |
| Drift Metrics | ✅ COMPLETE | Added to memory_service.py, costsim.py |
| RBAC Enforcement | ✅ ENABLED | `enforce_mode: true` |

---

## Issues Encountered & Fixes Applied

### Issue 1: RBAC_ENFORCE Not Passed to Container

- **Problem:** Setting `RBAC_ENFORCE=true` in `.env` had no effect
- **Root Cause:** `docker-compose.yml` did not include `RBAC_ENFORCE` in environment section
- **Fix:** Added `RBAC_ENFORCE: ${RBAC_ENFORCE:-false}` to docker-compose.yml

### Issue 2: MACHINE_SECRET_TOKEN Not Available in Container

- **Problem:** Machine token authentication failed inside container
- **Root Cause:** Token not passed through docker-compose environment
- **Fix:** Added `MACHINE_SECRET_TOKEN: ${MACHINE_SECRET_TOKEN:-}` to docker-compose.yml

### Issue 3: RBACMiddleware Not Enforcing

- **Problem:** Even with `RBAC_ENFORCE=true`, unauthorized requests succeeded
- **Root Cause:** `RBACMiddleware` was defined but never registered in FastAPI app
- **Fix:** Added import and `app.add_middleware(RBACMiddleware)` to `main.py`

### Issue 4: pgbench Tables Not Initialized

- **Problem:** Load test failed with "relation pgbench_branches does not exist"
- **Root Cause:** pgbench requires `-i` flag to create test tables before benchmarking
- **Fix:** Ran `pgbench -i -s 10` before load test

### Issue 5: Smoke Script RBAC Status Unknown

- **Problem:** Smoke script reported `enforce_mode: UNKNOWN`
- **Root Cause:** `/api/v1/rbac/info` now requires authentication when RBAC enforced
- **Impact:** Low (script still validates core functionality)

---

## Decisions Made

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Add env vars to docker-compose.yml | Required for container to read `.env` values |
| 2 | Register RBACMiddleware in main.py | Middleware must be explicitly added to intercept requests |
| 3 | Create one-click script with manual gates | Prevents accidental full enablement; allows review at each step |
| 4 | 15-minute observation period in script | Provides time to detect regressions before declaring success |
| 5 | Auto-rollback on Ctrl+C interrupt | Safety net for interrupted enablement |

---

## Files Created

| File | Purpose |
|------|---------|
| `scripts/ops/rbac_oneclick_enable.sh` | Complete 7-step enablement with manual gates |
| `monitoring/dashboards/m7_rbac_memory_dashboard.json` | Grafana dashboard for RBAC & Memory metrics |
| `backend/tests/integration/test_m7_rbac_memory.py` | Integration tests for RBAC, memory pins, TTL |

---

## Files Modified

| File | Change |
|------|--------|
| `docker-compose.yml` | Added RBAC_ENFORCE, MACHINE_SECRET_TOKEN env vars (lines 46-47) |
| `backend/app/main.py` | Added RBACMiddleware import and registration (lines 37, 252-254) |
| `backend/app/memory/memory_service.py` | Added drift detection metrics |
| `backend/app/api/costsim.py` | Added context injection failure and drift metrics |
| `.env` | Set RBAC_ENFORCE=true |

---

## Verification Results

### RBAC Enforcement Test

```
1. Unauthorized write (no token) - HTTP 403 [PASS]
2. Authorized write (machine token) - HTTP 201 [PASS]
3. RBAC Info shows enforce_mode: true [PASS]
```

### Smoke Test Summary

```
Passed:   12
Failed:   0
Warnings: 3

RESULT: PASSED - Safe to proceed with RBAC enablement
```

### PgBouncer Load Test

```
Configuration: 50 clients, 60 seconds, scale factor 10
Results:
  - Transactions processed: 24,015
  - Failed transactions: 0 (0.000%)
  - Avg latency: 124.9 ms
  - TPS: 400.2
  - PgBouncer pool: 20 connections (healthy)

Verdict: PASS - PgBouncer handles concurrent load with zero failures
```

### Prometheus Metrics Verification

```prometheus
rbac_decisions_total{decision="denied",reason="no-credentials",resource="memory_pin"} 2.0
rbac_decisions_total{decision="allowed",reason="role:machine",resource="memory_pin"} 2.0
memory_pins_operations_total{operation="upsert",status="success"} 2.0
```

---

## Current System State

```
RBAC Status:
├─ enforce_mode: true
├─ fail_open: false
├─ hash: 4c4628adb05888a6
└─ roles: [infra, admin, machine, dev, readonly]

Container Environment:
├─ RBAC_ENABLED=true
├─ RBAC_ENFORCE=true
└─ MACHINE_SECRET_TOKEN=46bff817...

Backup:
└─ /root/agenticverz2.0/backups/m7_pre_enable_20251205T052016Z.dump (3.5M)
```

---

## Rollback Procedure

### Quick Rollback

```bash
./scripts/ops/rbac_enable.sh disable
```

### Manual Rollback

```bash
# 1. Update .env
sed -i 's/^RBAC_ENFORCE=.*/RBAC_ENFORCE=false/' /root/agenticverz2.0/.env

# 2. Restart backend
cd /root/agenticverz2.0
docker compose up -d backend

# 3. Verify
curl -s http://127.0.0.1:8000/api/v1/rbac/info | jq '.enforce_mode'
# Should return: false
```

---

## Operational Scripts

### One-Click Enablement

```bash
# Full enablement with manual confirmation gates
./scripts/ops/rbac_oneclick_enable.sh

# Dry run (no changes)
./scripts/ops/rbac_oneclick_enable.sh --dry-run
```

### Step-by-Step

```bash
# Pre-flight checks
./scripts/ops/rbac_enable.sh preflight

# Create backup
./scripts/ops/rbac_enable.sh backup

# Enable RBAC
./scripts/ops/rbac_enable.sh enable

# Run smoke tests
./scripts/ops/rbac_enable.sh smoke

# Verification queries
./scripts/ops/rbac_enable.sh verify

# Check status
./scripts/ops/rbac_enable.sh status
```

---

## Monitoring Checklist

After enabling RBAC, monitor:

- [ ] `rbac_decisions_total` counter incrementing
- [ ] `rbac_decisions_total{decision="deny"}` near zero (or expected)
- [ ] `memory_pins_operations_total` counter incrementing
- [ ] No elevated error rates in logs
- [ ] No unusual latency spikes in p99 histograms

### Grafana Dashboard

Import `monitoring/dashboards/m7_rbac_memory_dashboard.json` for:

- RBAC Decisions (allow/deny by resource)
- Memory Pin Operations
- Cache Hit Rate
- Drift Score

---

## Pending Items

| # | Task | Priority | Notes |
|---|------|----------|-------|
| 1 | Monitor for 24-48 hours | P0 | Watch for unexpected denials |
| 2 | ~~Investigate RBAC audit write errors~~ | ~~P1~~ | ✅ Fixed - generator session handling |
| 3 | ~~Update smoke script auth~~ | ~~P2~~ | ✅ Fixed - uses machine token |
| 4 | Run chaos micro-experiments | P2 | After stabilization period |

---

## Related PINs

- PIN-031: M7 Memory Integration (prerequisite)
- PIN-030: M6.5 Webhook Externalization
- PIN-021: M5 Policy API Completion

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-05 | PIN-032 created: M7 RBAC Enablement session |
| 2025-12-05 | Fixed docker-compose.yml: added RBAC_ENFORCE, MACHINE_SECRET_TOKEN |
| 2025-12-05 | Fixed main.py: registered RBACMiddleware |
| 2025-12-05 | Created one-click enablement script |
| 2025-12-05 | Created Grafana M7 dashboard |
| 2025-12-05 | Created integration tests for RBAC/Memory |
| 2025-12-05 | Added drift detection metrics |
| 2025-12-05 | Ran PgBouncer load test: 400 TPS, 0 failures |
| 2025-12-05 | Enabled RBAC_ENFORCE=true |
| 2025-12-05 | Smoke tests: 12 passed, 0 failed |
| 2025-12-05 | Status: ✅ COMPLETE - RBAC enforced in production |
| 2025-12-05 | **Session 2:** Fixed RBAC audit write errors (generator session handling) |
| 2025-12-05 | **Session 2:** Fixed smoke script auth (uses machine token for RBAC info) |
| 2025-12-05 | **Session 2:** Added --non-interactive mode to one-click script (for CI/CD) |
| 2025-12-05 | **Session 2:** Fixed one-click script RBAC info calls to use machine token |
| 2025-12-05 | **Session 2:** Fixed integration tests for RBAC enforcement (18 passed, 2 skipped) |
| 2025-12-05 | **Session 2:** Created chaos experiment scripts (kill_child, redis_stall, cpu_spike) |
| 2025-12-05 | **Session 2:** Created GitHub Actions nightly smoke workflow |
| 2025-12-05 | **Session 2:** Created runbooks (RBAC_INCIDENTS.md, MEMORY_PIN_CLEANUP.md) |
| 2025-12-05 | **Session 2:** Decision: Drift detection deferred to post-M8 (collect metrics, alerts disabled) |
| 2025-12-05 | **Session 2:** Decision: Machine role keeps least privilege (no delete permission) |
