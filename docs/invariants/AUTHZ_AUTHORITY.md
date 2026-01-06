# Authorization Authority Invariants

**Status:** ENFORCED
**Effective:** 2026-01-05
**Reference:** M28 Promotion / M7 Pruning

---

## Prime Invariant

> **All authorization decisions originate from M28 (`AuthorizationEngine`).**

The `authorize(actor, resource, action)` function in `backend/app/auth/authorization.py` is the **single source of truth** for all authorization decisions in the system.

---

## System of Record

### M28 (Authoritative)

| Component | File | Role |
|-----------|------|------|
| AuthorizationEngine | `backend/app/auth/authorization.py` | Core decision engine |
| authorize() | `backend/app/auth/authorization.py:455` | Single entry point |
| AuthorityResult | `backend/app/auth/authority.py` | FastAPI dependency wrapper |

**M28 is the authority system of record.**

### M7 (Legacy, Read-Only)

| Component | File | Role |
|-----------|------|------|
| RBACEngine | `backend/app/auth/rbac_engine.py` | Legacy policy evaluation |
| PolicyObject | `backend/app/auth/rbac_engine.py` | Legacy permission pattern |
| RBACMiddleware | `backend/app/auth/rbac_middleware.py` | Legacy middleware |

**M7 is a temporary translation layer only.**

---

## Invariants

### I-AUTH-001: Single Authority Source

All authorization checks MUST flow through `authorize()` from M28.

```python
# CORRECT - Uses M28
from app.auth.authorization import authorize
result = authorize(actor, "runs", "write")

# FORBIDDEN - Direct M7 usage in new code
from app.auth.rbac_engine import RBACEngine
decision = engine.check(PolicyObject(...), request)  # ❌
```

### I-AUTH-002: M7 is Translation Only

M7 may only be used as a **temporary translation layer** during migration. It must:
- Be accessed ONLY through the M7→M28 mapping layer
- Emit fallback telemetry when used
- Never be extended with new capabilities

### I-AUTH-003: No New M7 Dependencies

**No new capability may depend on M7.**

Any code created after 2026-01-05 that imports M7 modules is a violation.

```python
# VIOLATION - New code importing M7
from app.auth.rbac_engine import RBACEngine  # ❌ in new files
from app.auth.rbac_middleware import ...      # ❌ in new files
```

### I-AUTH-004: Fallback Requires Telemetry

Any fallback from M28 to M7 MUST:
1. Be explicitly allowed via allowlist
2. Emit `authz_m7_fallback_total` metric
3. Log the route, service, and principal type

### I-AUTH-005: No Bi-directional Sync

Authorization state must never be synchronized between M7 and M28. M28 is authoritative; M7 reads are for backward compatibility only during migration.

---

## Migration Rules

### Allowed During Migration

1. M28 → M7 fallback (with telemetry) for legacy routes
2. Reading M7 policies to determine M28 equivalents
3. Gradual route-by-route promotion to M28-only

### Forbidden During Migration

1. New M7 roles or permissions
2. New routes using M7 directly
3. Reverse mapping (M28 → M7)
4. Bulk migration (must be route-by-route)

---

## Enforcement

### CI Guards

```yaml
# .github/workflows/authz-integrity.yml
- name: Check for new M7 imports
  run: |
    # Fail if new files import M7 modules
    git diff --name-only origin/main... | xargs grep -l "from app.auth.rbac_engine" && exit 1 || true
```

### Runtime

```python
# AUTHZ_STRICT_MODE environment variable
AUTHZ_STRICT_MODE=true   # Disable M7 fallback (hard fail)
AUTHZ_STRICT_MODE=false  # Allow M7 fallback (logged)
```

---

## Verification Checklist

Before any authorization-related PR:

- [ ] Does this use `authorize()` from M28?
- [ ] Does this avoid importing M7 modules?
- [ ] If fallback is needed, is it on the explicit allowlist?
- [ ] Are metrics being emitted for any M7 usage?

---

## File Locations

| Purpose | File |
|---------|------|
| M28 Engine | `backend/app/auth/authorization.py` |
| M28 Dependencies | `backend/app/auth/authority.py` |
| M7 Engine (legacy) | `backend/app/auth/rbac_engine.py` |
| M7 Middleware (legacy) | `backend/app/auth/rbac_middleware.py` |
| M7→M28 Mapping | `backend/app/auth/mappings/m7_to_m28.py` (to be created) |
| This Invariant | `docs/invariants/AUTHZ_AUTHORITY.md` |

---

## Changelog

| Date | Action | Author |
|------|--------|--------|
| 2026-01-05 | Initial invariant declaration | Claude Opus 4.5 |
