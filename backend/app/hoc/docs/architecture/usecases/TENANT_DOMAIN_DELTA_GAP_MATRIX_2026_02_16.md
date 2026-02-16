# TENANT_DOMAIN_DELTA_GAP_MATRIX_2026_02_16

**Created:** 2026-02-16
**Scope:** tenant.create, tenant.delete, project.create (anchor)
**Method:** Cross-reference business_invariants.py, operation specs, replay fixtures, property tests, failure injection, mutation gate

## Gap Matrix

| Operation | Invariants | Specs | Runtime Assertions | Mutation | Property | Replay | Failure Injection |
|-----------|-----------|-------|-------------------|----------|----------|--------|-------------------|
| `tenant.create` | **MISSING** — no BI-TENANT for tenant.create; _default_check has no handler | PRESENT_REUSED — SPEC-001 in registry | **MISSING** — no test_tenant_runtime_delta.py | PRESENT_REUSED — shadow_compare.py scope | **MISSING** — no tenant lifecycle state machine | PRESENT_REUSED — REPLAY-001 (needs invariant ref fix: `INV-TENANT-001` → `BI-TENANT-002`) | **MISSING** — no tenant fault injection |
| `tenant.delete` | **MISSING** — no BI-TENANT for tenant.delete; _default_check has no handler | PRESENT_REUSED — SPEC-002 in registry | **MISSING** — no test_tenant_runtime_delta.py | PRESENT_REUSED — shadow_compare.py scope | **MISSING** — no tenant lifecycle state machine | PRESENT_REUSED — REPLAY-003 (needs invariant ref once BI-TENANT-003 exists) | **MISSING** — no tenant fault injection |
| `project.create` (anchor) | PRESENT_REUSED — BI-TENANT-001 (CRITICAL) guards tenant-must-be-ACTIVE | PRESENT_REUSED — in registry | **MISSING** — no dispatch assertion tests | PRESENT_REUSED — shadow_compare.py scope | **MISSING** — no tenant lifecycle state machine covers project anchor | PRESENT_REUSED — REPLAY-004 references BI-TENANT-001 | **MISSING** — no project.create fault injection |

## Summary

| Classification | Count | Details |
|---------------|-------|---------|
| PRESENT_REUSED | 9 | BI-TENANT-001, SPEC-001/002, REPLAY-001/003/004, mutation gate (×3) |
| PRESENT_STRENGTHEN | 2 | REPLAY-001 invariant ref fix, REPLAY-003 add invariant ref |
| MISSING | 10 | BI-TENANT-002 (tenant.create), BI-TENANT-003 (tenant.delete), _default_check handlers (×2), runtime assertion tests, tenant lifecycle property tests, fault injection tests (×3), project.create dispatch assertions |

## Delta Plan

1. **BI-TENANT-002** (tenant.create, HIGH): tenant_id + org_id required, tenant_name non-empty
2. **BI-TENANT-003** (tenant.delete, HIGH): tenant must exist, tenant must not be in CREATING state (incomplete lifecycle)
3. **_default_check handlers**: Add `tenant.create` and `tenant.delete` branches
4. **test_tenant_runtime_delta.py**: Contract tests + OperationRegistry dispatch assertions (MONITOR/STRICT mode)
5. **Tenant lifecycle property tests**: State machine (CREATING → ACTIVE → SUSPENDED → DELETED)
6. **Tenant fault injection**: Timeouts, missing fields, stale state, connection failures
7. **REPLAY-001 fixture fix**: Update invariant ref from `INV-TENANT-001` to `BI-TENANT-002`
8. **REPLAY-003 fixture update**: Add `BI-TENANT-003` to invariants_checked once invariant exists
