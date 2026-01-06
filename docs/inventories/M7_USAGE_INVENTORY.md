# M7 Usage Inventory

**Date:** 2026-01-05
**Purpose:** Document all M7 (legacy RBAC) usage for migration to M28

---

## Summary

| Category | Count |
|----------|-------|
| Production Imports | 7 files |
| Test Imports | 4 files |
| Inline Role Checks | 1 file |
| PolicyObject Patterns | ~30 patterns |

---

## Production Code Imports

### rbac_engine.py Imports

| Location | Import | Usage Kind | Risk |
|----------|--------|------------|------|
| `app/auth/oidc_provider.py` | `map_external_roles_to_aos` | Role translation | LOW - can delegate to M28 |
| `app/auth/clerk_provider.py` | `get_max_approval_level` | Approval level calculation | MEDIUM - domain logic |
| `app/api/rbac_api.py` | `check_permission`, `get_rbac_engine` | API endpoint | HIGH - direct M7 dependency |
| `app/main.py` | `init_rbac_engine` | Startup initialization | MEDIUM - can be M28 init |

### rbac_middleware.py Imports

| Location | Import | Usage Kind | Risk |
|----------|--------|------------|------|
| `app/main.py` | `RBACMiddleware` | Middleware registration | HIGH - core flow |
| `app/auth/rbac_integration.py` | Multiple | Integration layer | MEDIUM - translation shim |

### rbac.py Imports

| Location | Import | Usage Kind | Risk |
|----------|--------|------------|------|
| `app/auth/__init__.py` | Module exports | Re-export | LOW - can redirect |
| `app/api/policy.py` | `check_approver_permission`, `RBACError` | Approval flow | MEDIUM - domain logic |

---

## Inline Role Checks (Outside M7)

### app/api/traces.py

| Line Pattern | Check | Classification |
|--------------|-------|----------------|
| `user.has_role("admin")` | Admin bypass | Write authority |
| `user.has_role("operator")` | Operator bypass | Write authority |
| `if tenant_id != user.tenant_id` | Tenant isolation | Read-only gate |

**Assessment:** This file has 15+ inline role checks. Should migrate to `authorize()` calls.

---

## PolicyObject Patterns (M7)

From `app/auth/rbac_middleware.py`:

| Resource | Actions | Usage |
|----------|---------|-------|
| `memory_pin` | read, write, delete, admin | Memory PIN operations |
| `prometheus` | reload, query | Metrics operations |
| `costsim` | read, write | Cost simulation |
| `policy` | read, write, approve | Policy management |
| `agent` | read, write, delete, heartbeat, register | Agent lifecycle |
| `runtime` | simulate, capabilities, query | Runtime operations |
| `recovery` | suggest, execute | Recovery suggestions |

---

## Test File Imports

| File | Type | Notes |
|------|------|-------|
| `tests/auth/test_rbac_engine.py` | Unit tests | Test M7 engine |
| `tests/auth/test_rbac_middleware.py` | Unit tests | Test M7 middleware |
| `tests/auth/test_rbac_integration.py` | Integration | Test M7↔M28 |
| `tests/auth/test_rbac_path_mapping.py` | Unit tests | Test path→policy mapping |

---

## Classification Summary

### Read-Only Gates (LOW priority to migrate)
- Tenant isolation checks
- Read permission checks on traces
- Query operations

### Write Authority (HIGH priority to migrate)
- Policy approval flows
- Agent registration
- Recovery execution
- Memory PIN writes

### Flow/UI Convenience (RECLASSIFY)
- Prometheus query (operational, not auth)
- Costsim read (informational)

---

## Migration Priority

### P0 - Critical (Block new features)
1. `app/api/rbac_api.py` - Direct M7 API exposure
2. `app/main.py` - M7 middleware registration

### P1 - High (Migrate next)
1. `app/api/traces.py` - 15+ inline checks
2. `app/api/policy.py` - Approval authority

### P2 - Medium (After P1)
1. `app/auth/clerk_provider.py` - Role translation
2. `app/auth/oidc_provider.py` - Role translation
3. `app/auth/rbac_integration.py` - Integration shim

### P3 - Low (Cleanup)
1. `app/auth/__init__.py` - Re-exports
2. Test files - Update after production

---

## Next Steps

1. Create `auth/mappings/m7_to_m28.py` mapping file
2. Implement `authorize()` choke point
3. Migrate P0 files first
4. Add CI guards to prevent new M7 imports

---

## Changelog

| Date | Action | Author |
|------|--------|--------|
| 2026-01-05 | Initial inventory | Claude Opus 4.5 |
