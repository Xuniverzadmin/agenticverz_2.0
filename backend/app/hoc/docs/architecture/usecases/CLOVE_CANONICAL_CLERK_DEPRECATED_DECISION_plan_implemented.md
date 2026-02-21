# Clove Canonical / Clerk Deprecated — Execution Evidence

**Created:** 2026-02-21
**Executor:** Claude
**Status:** DONE
**PIN:** PIN-606

---

## Task Completion Matrix

| Task ID | Status | Evidence |
|---------|--------|----------|
| T1 | DONE | `auth_constants.py`, `auth_provider.py`, `auth_provider_clove.py`, `contexts.py`, `gateway.py`, `CloveAuthAdapter.ts`, `types.ts` |
| T2 | DONE | Clerk deprecation warning + prod fail-fast in `auth_provider.py` factory |
| T3 | DONE | `canonical_provider` + `deprecation` fields in status endpoint and schema |
| T4 | DONE | 49/49 tests pass (see pytest output below) |
| T5 | DONE | `SOFTWARE_BIBLE.md`, cutover doc, decision doc updated |
| T6 | DONE | `PIN-606` created, `INDEX.md` updated (active row + changelog + chronological) |
| T7 | DONE | This file — pytest + enforcer evidence attached |
| T8 | DONE | Commit + push + PR |

---

## Commands Executed

### Final pytest

```
$ cd /root/agenticverz2.0/backend
$ PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py tests/auth/test_auth_identity_routes.py -v

49 passed in 2.46s
```

### Capability enforcer

```
$ python3 scripts/ops/capability_registry_enforcer.py check-pr --files \
    backend/app/auth/auth_constants.py \
    backend/app/auth/auth_provider.py \
    backend/app/auth/auth_provider_clove.py \
    backend/app/auth/gateway.py \
    backend/app/auth/contexts.py \
    backend/app/hoc/api/auth/routes.py \
    backend/app/hoc/api/auth/schemas.py \
    backend/tests/auth/test_auth_provider_seam.py \
    backend/tests/auth/test_auth_identity_routes.py

✅ CI PASSED (with warnings)
```

5 advisory MISSING_EVIDENCE warnings (non-blocking). 0 blocking violations.

---

## Before/After Behavior Summary

| Aspect | Before | After |
|--------|--------|-------|
| Default `AUTH_PROVIDER` | `hoc_identity` | `clove` |
| Canonical enum | `AuthProviderType.HOC_IDENTITY` | `AuthProviderType.CLOVE` |
| Auth source | `AuthSource.HOC_IDENTITY` | `AuthSource.CLOVE` |
| Provider class | `HocIdentityHumanAuthProvider` | `CloveHumanAuthProvider` |
| Provider file | `auth_provider_hoc_identity.py` | `auth_provider_clove.py` |
| Frontend adapter | `HocIdentityAuthAdapter` | `CloveAuthAdapter` |
| Issuer constant | `HOC_IDENTITY_ISSUER` | `CLOVE_ISSUER` (alias retained) |
| `AUTH_PROVIDER=clerk` | Warning + force to hoc_identity | **DEPRECATED** warning + force to clove |
| `AUTH_PROVIDER=hoc_identity` | Accepted directly | Silently upgraded to clove |
| Status endpoint `effective_provider` | `hoc_identity` | `clove` |
| Status endpoint `canonical_provider` | N/A | `clove` (new field) |
| Status endpoint `deprecation` | N/A | Clerk deprecation metadata (new field) |
| Test count | 42 | 49 (+7 new: alias, deprecation, canonical, status tests) |

---

## Files Changed

### Code (7 files)
1. `backend/app/auth/auth_constants.py`
2. `backend/app/auth/auth_provider.py`
3. `backend/app/auth/auth_provider_clove.py` (renamed from `auth_provider_hoc_identity.py`)
4. `backend/app/auth/contexts.py`
5. `backend/app/auth/gateway.py`
6. `backend/app/hoc/api/auth/routes.py`
7. `backend/app/hoc/api/auth/schemas.py`

### Tests (2 files)
8. `backend/tests/auth/test_auth_provider_seam.py`
9. `backend/tests/auth/test_auth_identity_routes.py`

### Frontend (3 files)
10. `website/app-shell/src/auth/adapters/CloveAuthAdapter.ts` (renamed from `HocIdentityAuthAdapter.ts`)
11. `website/app-shell/src/auth/types.ts`
12. `website/app-shell/src/auth/index.ts`

### Docs (3 files)
13. `literature/hoc_domain/platform/SOFTWARE_BIBLE.md`
14. `literature/hoc_domain/platform/HOC_PLATFORM_AUTH_PROVIDER_SEAM_CUTOVER_2026-02-21.md`
15. `backend/app/hoc/docs/architecture/usecases/CLOVE_CANONICAL_CLERK_DEPRECATED_DECISION_2026-02-21.md` (new)

### PIN (2 files)
16. `docs/memory-pins/PIN-606-clove-canonical-clerk-deprecated.md` (new)
17. `docs/memory-pins/INDEX.md`

---

## Deviations

None. All 8 tasks completed as planned.

## Residual Risks

1. Old `auth_provider_hoc_identity.py` file should be deleted from version control (git mv handled by rename).
2. Legacy `HOC_IDENTITY_*` env var aliases remain for backward compat — can be removed in a future sweep.
3. 5 advisory MISSING_EVIDENCE warnings in capability enforcer — non-blocking, deferred.
