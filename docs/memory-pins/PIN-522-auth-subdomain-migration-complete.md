# PIN-522: Auth Subdomain Migration Complete

**Status:** ✅ COMPLETE
**Created:** 2026-02-04
**Category:** Architecture
**Reference:** PIN-271 (RBAC Authority Separation)
**Commit:** b17e0b59

---

## Summary

Migrated RBAC engine and identity adapters to HOC account/auth subdomain per PIN-271. Clean cut - no backward compat shims.

---

## New Structure

```
hoc/cus/account/auth/
├── __init__.py                    # Subdomain package
├── L5_engines/
│   ├── __init__.py
│   ├── rbac_engine.py            # RBAC authorization (M7 Legacy)
│   └── identity_adapter.py       # Identity extraction adapters
└── L6_drivers/
    └── __init__.py               # Future: audit logging, token storage
```

## Canonical Import Path

```python
from app.hoc.cus.account.auth import (
    RBACEngine, PolicyObject, Decision, PolicyConfig,
    ClerkAdapter, IdentityAdapter, SystemIdentityAdapter,
    DevIdentityAdapter, AuthenticationError
)
```

## Files Deleted (No Shims)

| Deleted Path | Reason |
|--------------|--------|
| `app/auth/rbac_engine.py` | Moved to canonical location |
| `app/auth/identity_adapter.py` | Moved to canonical location |
| `hoc/int/policies/engines/rbac_engine.py` | Orphan duplicate |
| `hoc/int/general/facades/identity_adapter.py` | Moved to canonical location |

## Import Rewiring

| File | Old Import | New Import |
|------|-----------|------------|
| `app/auth/identity_chain.py` | `app.auth.identity_adapter` | `app.hoc.cus.account.auth` |
| `hoc/int/general/engines/identity_chain.py` | `app.auth.identity_adapter` | `app.hoc.cus.account.auth` |
| `tests/auth/test_rbac_engine.py` | `app.auth.rbac_engine` | `app.hoc.cus.account.auth` |

## Verification

- 33/33 RBAC tests pass
- Health check: healthy
- All imports verified working

## Key Decision

**No backward compatibility shims.** Old import paths (`app.auth.rbac_engine`, `app.auth.identity_adapter`) immediately error. This forces all code to use the canonical HOC path.
