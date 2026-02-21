# PIN-606: Clove Canonical / Clerk Deprecated

**Created:** 2026-02-21
**Category:** Auth / Platform / Naming Decision
**Status:** COMPLETE

---

## Decision

The in-house authentication system is canonically named **Clove**. The prior name "HOC Identity" (`hoc_identity`) is treated as a legacy alias that is silently upgraded. Clerk is explicitly deprecated.

## Deprecation Policy

| AUTH_PROVIDER value | Status | Runtime behavior |
|---------------------|--------|-----------------|
| `clove` | CANONICAL | Factory returns `CloveHumanAuthProvider` |
| `hoc_identity` | LEGACY ALIAS | Silently upgraded to `clove` via `_LEGACY_ALIASES` |
| `clerk` | DEPRECATED | Warning (non-prod) / `RuntimeError` (prod) |
| anything else | INVALID | Warning (non-prod) / `RuntimeError` (prod) |

## Files Changed

### Code (7 files)
- `backend/app/auth/auth_constants.py` — `AuthProviderType.CLOVE`, `CLOVE_ISSUER`, `CLOVE_AUDIENCE`
- `backend/app/auth/auth_provider.py` — factory default `clove`, alias map, deprecation policy, status contract
- `backend/app/auth/auth_provider_clove.py` — renamed from `auth_provider_hoc_identity.py`, class `CloveHumanAuthProvider`
- `backend/app/auth/contexts.py` — `AuthSource.CLOVE` canonical
- `backend/app/auth/gateway.py` — `CLOVE_ISSUER`, `AuthSource.CLOVE`
- `backend/app/hoc/api/auth/routes.py` — docstring update
- `backend/app/hoc/api/auth/schemas.py` — `canonical_provider` + `deprecation` fields

### Tests (2 files)
- `backend/tests/auth/test_auth_provider_seam.py` — 49 tests, all clove-centric
- `backend/tests/auth/test_auth_identity_routes.py` — provider status asserts `clove`

### Frontend (3 files)
- `website/app-shell/src/auth/adapters/CloveAuthAdapter.ts` — renamed from `HocIdentityAuthAdapter.ts`
- `website/app-shell/src/auth/types.ts` — `'clove' | 'clerk'`
- `website/app-shell/src/auth/index.ts` — import example updated

### Documentation (3 files)
- `literature/hoc_domain/platform/SOFTWARE_BIBLE.md` — reality delta
- `literature/hoc_domain/platform/HOC_PLATFORM_AUTH_PROVIDER_SEAM_CUTOVER_2026-02-21.md` — full update
- `backend/app/hoc/docs/architecture/usecases/CLOVE_CANONICAL_CLERK_DEPRECATED_DECISION_2026-02-21.md` — decision doc

## Validation Results

- Tests: 49/49 PASSED
- Capability enforcer: CI PASSED (0 blocking)

## Backward Compatibility

- `HOC_IDENTITY_ISSUER` / `HOC_IDENTITY_AUDIENCE` constants remain as aliases to `CLOVE_ISSUER` / `CLOVE_AUDIENCE`
- Env vars `HOC_IDENTITY_*` are accepted as fallback when `CLOVE_*` is not set
- `AUTH_PROVIDER=hoc_identity` is silently upgraded (no warning)
