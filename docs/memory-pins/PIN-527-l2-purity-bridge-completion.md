# PIN-527: L2 Purity Bridge Completion

**Date:** 2026-02-06  
**Status:** COMPLETE  
**Scope:** HOC L2 API purity (L2 → L4 only), bridge capability additions

---

## Summary

All L2 API routers under `backend/app/hoc/api/**` now satisfy first-principles
purity: no DB/ORM imports, no L5/L6 imports, and no remaining
`TODO(PIN-L2-PURITY)` tags. L2 access to policy engines, RBAC, and worker
registry functions is routed through L4 bridge capabilities.

---

## Evidence (Audit Results)

- **L5_engines/L6_drivers imports:** 0 (actual import lines)
- **DB/ORM imports:** 0 (actual import lines)
- **TODO(PIN-L2-PURITY) tags:** 0
- **L5_schemas imports:** 13 (allowed, schema-only)
- **Comment-only L5_engines mentions:** 2 (informational)

---

## Bridge Capability Additions

### Policies Bridge

- `PoliciesEngineBridge` added to keep base bridge within 5-method limit.
- Capabilities:
  - `prevention_hook_capability()`
  - `policy_engine_capability()`
  - `policy_engine_class_capability()`

### Account Bridge

- Added `rbac_engine_capability()` for L2 RBAC endpoints.

### Integrations Bridge

- Added `IntegrationsDriverBridge` with:
  - `worker_registry_capability(session)`
  - `worker_registry_exceptions()`

---

## L2 API Changes (Bypass Removal)

| File | Change |
|------|--------|
| `backend/app/hoc/api/cus/policies/policy.py` | Replaced policy engine imports with `get_policies_engine_bridge()` |
| `backend/app/hoc/api/cus/policies/workers.py` | Replaced PolicyEngine import with bridge capability |
| `backend/app/hoc/api/cus/policies/rbac_api.py` | Replaced RBAC engine import with account bridge |
| `backend/app/hoc/api/cus/logs/tenants.py` | Replaced worker registry driver imports with integrations driver bridge |

---

## Follow-ups

None required for L2 purity. Future work should preserve the bridge pattern
and keep L2 free of DB/ORM and L5/L6 imports.
