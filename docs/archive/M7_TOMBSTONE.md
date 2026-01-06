# M7 RBAC Engine - Tombstone

**Status:** DEPRECATED (Authorization Superseded)
**Date:** 2026-01-05
**Reference:** PIN-310 (Fast-Track M7 Closure)

---

## Summary

The M7 RBAC Engine (`backend/app/auth/rbac_engine.py`) has been superseded by M28 (`backend/app/auth/authorization.py`) for all **authorization decisions**.

As of PIN-310, all authorization paths route through `authorization_choke.py`, which directs traffic to M28.

---

## What M7 Was

M7 provided:
1. **Authorization Engine** - Role-based access control decisions
2. **Policy Management** - Loading, reloading, and introspecting RBAC policies
3. **RBAC Middleware** - FastAPI middleware for request authorization
4. **Integration Layer** - Bridging old and new authorization systems

---

## Why Was It Replaced?

| Problem | Solution (M28) |
|---------|----------------|
| Scattered permission checks | Single `authorize_action()` entry point |
| No tenant isolation | ActorContext with tenant_id |
| No actor type restrictions | ActorType-based restrictions |
| No phased enforcement | AUTHZ_PHASE environment control |
| No metrics | Prometheus counters and histograms |
| Hard to audit | Source tracking (m28_direct, m28_via_mapping) |

---

## What Was Deprecated

### Deprecated for Authorization (Route to M28)

| Function | M7 Location | M28 Replacement |
|----------|-------------|-----------------|
| `check_permission()` | `rbac_engine.py` | `authorization_choke.check_permission_request()` |
| `require_permission()` | `rbac_engine.py` | `authorization_choke.require_permission()` |
| `RBACEngine.check()` | `rbac_engine.py` | `AuthorizationEngine.authorize()` |

### Deprecated Role Utilities (Moved to role_mapping.py)

| Function | Old Location | New Location |
|----------|--------------|--------------|
| `get_max_approval_level()` | `rbac_engine.py` | `role_mapping.py` |
| `get_role_approval_level()` | `rbac_engine.py` | `role_mapping.py` |
| `map_external_role_to_aos()` | `rbac_engine.py` | `role_mapping.py` |
| `map_external_roles_to_aos()` | `rbac_engine.py` | `role_mapping.py` |
| `ROLE_APPROVAL_LEVELS` | `rbac_engine.py` | `role_mapping.py` |
| `EXTERNAL_TO_AOS_ROLE_MAP` | `rbac_engine.py` | `role_mapping.py` |

---

## What Remains Active (Admin Only)

The following M7 functions are still active for **policy management** (not authorization):

| Function | Purpose | Used By |
|----------|---------|---------|
| `init_rbac_engine()` | Initialize engine on startup | `main.py` |
| `get_rbac_engine()` | Get singleton instance | `rbac_api.py` |
| `RBACEngine.get_policy_info()` | Policy introspection | Admin API |
| `RBACEngine.reload_policy()` | Hot-reload policies | Admin API |

These functions provide **read-only administrative visibility** and do NOT make authorization decisions.

---

## Evidence of M28 Completeness

### T12: Authority Exhaustion Tests
- **Total tests:** 780
- **M28 Direct:** 507
- **M28 via Mapping:** 104 (M7 legacy resources)
- **Failures:** 0
- **Tripwire hits:** 0

### T14: Strict Mode Verification
- **M28 native resources:** 507 ALLOWED
- **M7 legacy resources:** 273 BLOCKED (strict mode)
- **Unexpected allows:** 0

---

## Timeline

| Date | Event |
|------|-------|
| Pre-2026 | M7 created as original RBAC system |
| 2026-01-05 | M28 promoted, M7 marked for removal |
| 2026-01-05 | T0-T7 completed (mapping, choke point, metrics) |
| 2026-01-05 | T9 completed (tripwire mode) |
| 2026-01-05 | T10 completed (authority matrix) |
| 2026-01-05 | T11 completed (synthetic principals) |
| 2026-01-05 | T12 completed (authority exhaustion - 780 tests) |
| 2026-01-05 | T13 completed (resolution loop - 104 mapped) |
| 2026-01-05 | T14 completed (strict mode - 273 blocked) |
| 2026-01-05 | T15 completed (M7 tombstone created) |
| 2026-01-05 | T16 pending (final lock) |

---

## Files Affected

### Deprecated Files (Authorization Only)

| File | Status | Notes |
|------|--------|-------|
| `rbac_engine.py` | DEPRECATED | Auth routes to M28, admin functions remain |
| `rbac_middleware.py` | DEPRECATED | Replaced by authorization_choke middleware |
| `rbac_integration.py` | DEPRECATED | Integration layer superseded |

### Updated Files (PIN-310)

| File | Change |
|------|--------|
| `clerk_provider.py` | Import from `role_mapping` instead of `rbac_engine` |
| `oidc_provider.py` | Import from `role_mapping` instead of `rbac_engine` |
| `rbac_api.py` | Use `check_permission_request` from `authorization_choke` |
| `authorization_choke.py` | Added `check_permission_request()`, added "rbac" to native resources |
| `role_mapping.py` | Added M7 legacy functions (approval levels, external role mapping) |

---

## Migration Path

### For Authorization Checks

**Before (M7):**
```python
from app.auth.rbac_engine import check_permission

decision = check_permission("resource", "action", request)
```

**After (M28):**
```python
from app.auth.authorization_choke import check_permission_request

decision = await check_permission_request("resource", "action", request)
```

### For Role Utilities

**Before (M7):**
```python
from app.auth.rbac_engine import get_max_approval_level

level = get_max_approval_level(roles)
```

**After (role_mapping.py):**
```python
from app.auth.role_mapping import get_max_approval_level

level = get_max_approval_level(roles)
```

---

## Invariants Established

1. **I-AUTH-001:** All authorization routes through `authorization_choke.py`
2. **I-AUTH-002:** M28 is authoritative for all authorization decisions
3. **I-AUTH-003:** M7 is deprecated for authorization, active for admin introspection only
4. **I-AUTH-004:** No new M7 authorization paths may be added

---

## Deletion Timeline

Full deletion of M7 files is blocked until:
1. Policy management migrates to M28 or a dedicated service
2. `init_rbac_engine()` is removed from `main.py`
3. Admin API endpoints are updated or deprecated

Until then, M7 remains in a **tombstone state** - present but not authoritative.

---

## Lessons Learned

1. **Single entry point** - Authorization must have one choke point
2. **Phased rollout** - Don't replace auth systems all at once
3. **Metrics first** - Track fallback before removal
4. **Mapping layer** - Translation layer enables gradual migration
5. **CI guards** - Prevent regression during migration
6. **Authority exhaustion** - Test every permission combination before deletion

---

## Final Attestation

**M7 served AOS well. It is now superseded by M28.**

```
RIP M7 (rbac_engine.py)
"You gave us roles. M28 gives us actors."
```

---

## Author

Claude Opus 4.5
PIN-310: Fast-Track M7 Closure
