# POLICIES_DOMAIN_DELTA_GAP_MATRIX_2026_02_16

**Created:** 2026-02-16
**Purpose:** Delta gap matrix for policies domain runtime correctness iteration
**Parent:** `HOC_POLICIES_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan.md`

## Coverage Matrix

| Operation | Invariant | Spec | Runtime Assertion | Mutation | Property | Replay | Failure Injection |
|-----------|-----------|------|-------------------|----------|----------|--------|-------------------|
| policy.activate | PRESENT_REUSED (BI-POLICY-001) | PRESENT_REUSED (SPEC-009) | MISSING | MISSING | PRESENT_STRENGTHEN | PRESENT_REUSED (REPLAY-010) | MISSING |
| policy.deactivate | MISSING | PRESENT_REUSED (SPEC-010) | MISSING | MISSING | PRESENT_STRENGTHEN | PRESENT_REUSED (REPLAY-011) | MISSING |
| control.set_threshold | PRESENT_REUSED (BI-CTRL-001) | PRESENT_REUSED (SPEC-011) | MISSING | MISSING | PRESENT_REUSED | PRESENT_REUSED (REPLAY-012) | MISSING |

## Dimension Details

### 1. Business Invariants

| Invariant | Operation | Status | Action |
|-----------|-----------|--------|--------|
| BI-POLICY-001 | policy.activate | PRESENT_REUSED | Schema must be valid non-empty dict. Already enforced. Strengthen with fail-closed runtime test. |
| BI-POLICY-002 | policy.deactivate | MISSING | System policies must not be deactivated by tenant-scoped callers. Add invariant + tests. |

### 2. Operation Specs

| Spec | Operation | Status | Action |
|------|-----------|--------|--------|
| SPEC-009 | policy.activate | PRESENT_REUSED | 5 preconditions, 3 postconditions, 3 forbidden states. No changes needed. |
| SPEC-010 | policy.deactivate | PRESENT_REUSED | 3 preconditions, 3 postconditions, 3 forbidden states. No changes needed. |

### 3. Runtime Assertions (In-Process)

| Test Suite | Status | Action |
|------------|--------|--------|
| Real OperationRegistry dispatch for policy.activate | MISSING | Add test: register handler, dispatch, assert ALLOW + invariant pass |
| Real OperationRegistry dispatch for policy.deactivate | MISSING | Add test: register handler, dispatch, assert ALLOW |
| Fail-closed assertion: policy.activate with invalid schema | MISSING | Add test: missing schema → ENFORCE mode blocks |
| Fail-closed assertion: policy.deactivate system policy | MISSING | Add test: system policy deactivation → BI-POLICY-002 blocks |

### 4. Mutation Resistance

| Target | Status | Action |
|--------|--------|--------|
| shadow_compare.py | PRESENT_REUSED | 76.7% kill rate, strict threshold met |
| business_invariants.py (policy checks) | MISSING | Not in mutmut scope — document gap, defer to future iteration |

Note: Adding L5 policy engines to mutation scope is out-of-scope (mutmut targets shadow_compare.py per pyproject.toml). Current gate remains green. Document as accepted risk.

### 5. Property-Based Tests

| File | Status | Action |
|------|--------|--------|
| test_policies_threshold_properties.py | PRESENT_STRENGTHEN | 6 tests exist (threshold validation, conflict resolution, name sanitization). Add policy lifecycle state transition properties. |

### 6. Differential Replay

| Fixture | Status | Action |
|---------|--------|--------|
| REPLAY-010 (policy.activate, ALLOW) | PRESENT_REUSED | Valid fixture, no changes needed. |
| REPLAY-011 (policy.deactivate, ALLOW) | PRESENT_REUSED | Valid fixture, no changes needed. |

### 7. Failure Injection

| Scenario | Status | Action |
|----------|--------|--------|
| Policy driver DB timeout | MISSING | Add fault test: driver raises timeout → handler returns safe error |
| Policy schema validation failure | MISSING | Add fault test: malformed schema → structured error, not crash |
| Policy stale read (concurrent deactivation) | MISSING | Add fault test: stale state → safe fallback behavior |

## Summary

| Dimension | PRESENT_REUSED | PRESENT_STRENGTHEN | MISSING |
|-----------|----------------|-------------------|---------|
| Invariants | 1 (BI-POLICY-001) | 0 | 1 (BI-POLICY-002) |
| Specs | 2 (SPEC-009, SPEC-010) | 0 | 0 |
| Runtime Assertions | 0 | 0 | 4 |
| Mutation | 1 (shadow_compare) | 0 | 0 (accepted risk) |
| Property | 0 | 1 | 0 |
| Replay | 2 (REPLAY-010, 011) | 0 | 0 |
| Failure Injection | 0 | 0 | 3 |

**Total deltas to implement:** 1 invariant + 4 runtime assertions + 1 property strengthening + 3 failure injection tests = 9 items
