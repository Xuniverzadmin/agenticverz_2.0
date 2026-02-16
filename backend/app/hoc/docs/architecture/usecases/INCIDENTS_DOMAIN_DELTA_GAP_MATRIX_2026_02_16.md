# INCIDENTS_DOMAIN_DELTA_GAP_MATRIX_2026_02_16

**Created:** 2026-02-16
**Purpose:** Delta gap matrix for incidents domain runtime correctness iteration
**Parent:** `HOC_INCIDENTS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan.md`

## Coverage Matrix

| Operation | Invariant | Spec | Runtime Assertion | Mutation | Property | Replay | Failure Injection |
|-----------|-----------|------|-------------------|----------|----------|--------|-------------------|
| incident.create | MISSING | PRESENT_REUSED (SPEC-012) | MISSING | MISSING | MISSING | PRESENT_REUSED (REPLAY-013) | MISSING |
| incident.resolve | MISSING | PRESENT_REUSED (SPEC-013) | MISSING | MISSING | MISSING | PRESENT_REUSED (REPLAY-002) | MISSING |
| incident.transition | PRESENT_REUSED (BI-INCIDENT-001) | MISSING | MISSING | MISSING | PRESENT_REUSED | MISSING | MISSING |

## Dimension Details

### 1. Business Invariants

| Invariant | Operation | Status | Action |
|-----------|-----------|--------|--------|
| BI-INCIDENT-001 | incident.transition | PRESENT_REUSED | RESOLVED→ACTIVE blocked, must reopen. Already enforced. Strengthen with runtime test. |
| (none) | incident.create | MISSING | Incident must have tenant_id and severity. Add BI-INCIDENT-002. |
| (none) | incident.resolve | MISSING | Cannot resolve non-existent or already-resolved incident. Add BI-INCIDENT-003. |

### 2. Operation Specs

| Spec | Operation | Status | Action |
|------|-----------|--------|--------|
| SPEC-012 | incident.create | PRESENT_REUSED | Already in spec registry. No changes needed. |
| SPEC-013 | incident.resolve | PRESENT_REUSED | Already in spec registry. No changes needed. |

### 3. Runtime Assertions (In-Process)

| Test Suite | Status | Action |
|------------|--------|--------|
| Real OperationRegistry dispatch for incident.create | MISSING | Add test: register handler, dispatch, assert ALLOW + result structure |
| Real OperationRegistry dispatch for incident.resolve | MISSING | Add test: register handler, dispatch, assert ALLOW |
| Fail-closed assertion: incident.create missing tenant_id | MISSING | Add test: missing tenant_id → STRICT mode blocks (BI-INCIDENT-002) |
| Fail-closed assertion: incident.resolve already-resolved | MISSING | Add test: already-resolved → STRICT mode blocks (BI-INCIDENT-003) |
| Mode behavior: MONITOR allows violations | MISSING | Add test: MONITOR mode logs but does not block |

### 4. Mutation Resistance

| Target | Status | Action |
|--------|--------|--------|
| shadow_compare.py | PRESENT_REUSED | 76.7% kill rate, strict threshold met |
| business_invariants.py (incident checks) | MISSING | Not in mutmut scope — document gap, defer to future iteration |

Note: Adding incident L5/L6 code to mutation scope is out-of-scope per pyproject.toml. Current gate remains green.

### 5. Property-Based Tests

| File | Status | Action |
|------|--------|--------|
| test_lifecycle_state_machine_properties.py | PRESENT_REUSED | 9 tests exist (state transitions, forbidden paths, reachability). Already covers incident lifecycle. |

### 6. Differential Replay

| Fixture | Status | Action |
|---------|--------|--------|
| REPLAY-002 (incident.resolve, DENY) | PRESENT_REUSED | Valid fixture, no changes needed. |
| REPLAY-013 (incident.create, ALLOW) | PRESENT_REUSED | Valid fixture, no changes needed. |

### 7. Failure Injection

| Scenario | Status | Action |
|----------|--------|--------|
| Incident driver DB timeout | MISSING | Add fault test: driver raises timeout → handler returns safe error |
| Incident resolve on non-existent incident | MISSING | Add fault test: resolve non-existent → structured error, not crash |
| Incident create with missing required fields | MISSING | Add fault test: missing tenant_id/severity → structured error |
| Incident stale read (concurrent resolution) | MISSING | Add fault test: stale state → safe fallback behavior |

## Summary

| Dimension | PRESENT_REUSED | PRESENT_STRENGTHEN | MISSING |
|-----------|----------------|-------------------|---------|
| Invariants | 1 (BI-INCIDENT-001) | 0 | 2 (create + resolve) |
| Specs | 2 (SPEC-012, SPEC-013) | 0 | 0 |
| Runtime Assertions | 0 | 0 | 5 |
| Mutation | 1 (shadow_compare) | 0 | 0 (accepted risk) |
| Property | 1 (lifecycle state machine) | 0 | 0 |
| Replay | 2 (REPLAY-002, REPLAY-013) | 0 | 0 |
| Failure Injection | 0 | 0 | 4 |

**Total deltas to implement:** 2 invariants + 5 runtime assertions + 4 failure injection tests = 11 items
