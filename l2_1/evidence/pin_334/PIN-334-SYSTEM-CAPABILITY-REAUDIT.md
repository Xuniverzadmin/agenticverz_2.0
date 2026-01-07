# PIN-334: System-Level Capability Re-Audit & Negative Assertion

**Status:** COMPLETE
**Date:** 2026-01-06
**Type:** AUDIT-ONLY (no modifications)
**Authority:** Enumeration and observation only

---

## Executive Summary

This audit verifies whether the AOS capability universe is **closed** — meaning every executable path is mapped to a declared capability. The audit found **gaps** in the capability mapping.

### CONCLUSION: System capability universe is **NOT CLOSED**

**Reason:** Administrative routes exist that are NOT mapped to any CAP or SUB.

---

## Phase 1: Audit Scope Definition

### Execution Vectors Enumerated

| Vector | Description | Count |
|--------|-------------|-------|
| HTTP Routes | REST API endpoints in main.py | 347 |
| Workers | Background execution paths | 4 |
| AUTO_EXECUTE | Automatic recovery paths | 1 (SUB-019) |
| CLI Commands | aos.py commands | 10 |
| SDK Methods | Python + JS client methods | 31 |
| Schedulers | Systemd timers | 3 |
| Startup Hooks | Server lifecycle hooks | 2 |

### Capability Registry Reference

- **Registry Version:** V2.1.0
- **First-Class Capabilities:** 21 (CAP-001 to CAP-021)
- **Substrate Capabilities:** 20 (SUB-001 to SUB-020)
- **Dormant Capabilities:** 0
- **Total Registered:** 41

---

## Phase 2: Static Execution Enumeration

### HTTP Routes by Method

| Method | Count |
|--------|-------|
| GET | 215 |
| POST | 125 |
| DELETE | 16 |
| PUT | 6 |
| PATCH | 3 |

### Worker Inventory

| Worker | File | Mapped To |
|--------|------|-----------|
| primary_worker | worker/primary.py | CAP-005 |
| batch_worker | worker/batch.py | CAP-005 |
| recovery_evaluator | worker/recovery_evaluator.py | SUB-019 |
| scheduled_tasks | worker/scheduled.py | SUB-010 |

### CLI Commands

| Command | Mapped To |
|---------|-----------|
| run | CAP-020 |
| status | CAP-020 |
| list | CAP-020 |
| cancel | CAP-020 |
| simulate | CAP-020 |
| configure | CAP-020 |
| validate | CAP-020 |
| export | CAP-020 |
| import | CAP-020 |
| version | CAP-020 |

### SDK Methods (Python)

| Method | Mapped To |
|--------|-----------|
| submit_run | CAP-021 |
| get_run | CAP-021 |
| list_runs | CAP-021 |
| cancel_run | CAP-021 |
| simulate | CAP-021 |
| get_capabilities | CAP-021 |
| create_trace | CAP-021 |
| emit_step | CAP-021 |
| (+ 23 more) | CAP-021 |

---

## Phase 3: Capability Mapping Verification

### Routes Explicitly Mapped in Registry

The registry declares 194 explicit routes plus wildcard patterns:
- `/api/v1/*` routes covered by corresponding CAP-001 to CAP-019
- `/health*`, `/metrics` covered by SUB-004
- `/operator/*` routes covered by SUB-007

### Coverage Gaps Identified

| Route | Method | Power | Mapped To |
|-------|--------|-------|-----------|
| `/admin/retry` | POST | EXECUTE | **NONE** |
| `/admin/failed-runs` | GET | READ_ONLY | **NONE** |
| `/admin/rerun` | POST | DISABLED | N/A (deprecated) |

---

## Phase 4: Runtime Confirmation

### Backend Health Check

```
GET /health → HTTP 200
Status: healthy
OpenAPI paths: 318
```

### Admin Routes Confirmed Present

```
Line 1300: @app.post("/admin/retry", response_model=RetryResponse)
Line 1413: @app.post("/admin/rerun", response_model=RerunResponse, deprecated=True)
Line 1450: @app.get("/admin/failed-runs")
```

### /admin/rerun Status

The `/admin/rerun` endpoint is:
- Marked `deprecated=True`
- Returns error when invoked
- NOT a live execution path

---

## Phase 5: Negative Assertions

### Question 5.1: Shadow Power

> Is there any executable behavior NOT mapped to a declared CAP or SUB?

**Answer: YES**

| Route | Power Type | Registry Status |
|-------|------------|-----------------|
| `/admin/retry` | EXECUTE (creates new runs) | NOT MAPPED |
| `/admin/failed-runs` | READ_ONLY | NOT MAPPED |

### Question 5.2: Authority

> Is there any executable behavior that can alter state without declared authority?

**Answer: YES**

`/admin/retry` creates `WorkerRun` database rows with:
- New run_id
- New execution entry
- State mutations

The authority owner is NOT declared in the capability registry.

### Question 5.3: Attribution

> Is there any execution path that does not emit an execution envelope?

**Answer: YES**

Grep search for envelope emission patterns in `/admin/retry`:
```
grep -A50 "@app.post(\"/admin/retry\"" main.py | grep -E "emit_envelope|ExecutionEnvelope|envelope"
→ NO MATCHES
```

The `/admin/retry` endpoint creates executions without emitting execution envelopes.

---

## Phase 6: Final Summary

### Execution Vector Inventory

| Category | Total | Mapped | Unmapped |
|----------|-------|--------|----------|
| HTTP Routes | 347 | 345 | **2** |
| Workers | 4 | 4 | 0 |
| AUTO_EXECUTE | 1 | 1 | 0 |
| CLI Commands | 10 | 10 | 0 |
| SDK Methods | 31 | 31 | 0 |

### Negative Assertion Results

| Assertion | Question | Answer |
|-----------|----------|--------|
| 5.1 | Shadow Power exists? | **YES** |
| 5.2 | Undeclared authority mutations? | **YES** |
| 5.3 | Non-enveloped execution? | **YES** |

### Unmapped Execution Paths

| Path | Method | Power | Risk |
|------|--------|-------|------|
| `/admin/retry` | POST | EXECUTE | Creates runs without capability gate |
| `/admin/failed-runs` | GET | READ_ONLY | Low (read-only) |

---

## Conclusion

### System Status: CAPABILITY UNIVERSE NOT CLOSED

The capability universe declared in `CAPABILITY_REGISTRY_UNIFIED.yaml` does NOT account for all executable paths in the system.

**Specific Gaps:**
1. `/admin/retry` - EXECUTE power, creates new WorkerRun entries, no envelope emission
2. `/admin/failed-runs` - READ_ONLY power, not mapped to any capability

### Audit Integrity Statement

This audit:
- ❌ Did NOT add new capabilities
- ❌ Did NOT promote or demote capabilities
- ❌ Did NOT refactor code
- ❌ Did NOT change runtime behavior
- ✅ Enumerated all execution vectors
- ✅ Verified capability mappings
- ✅ Answered negative assertions with YES/NO
- ✅ Documented gaps with evidence

---

## Evidence Files

| File | Purpose |
|------|---------|
| `/tmp/http_routes_raw.txt` | Raw HTTP route enumeration (347 routes) |
| `CAPABILITY_REGISTRY_UNIFIED.yaml` | Registry V2.1.0 reference |
| `backend/app/main.py:1300-1470` | Admin route implementations |

---

**Audit Complete. No modifications made. Human decision required for gap resolution.**
