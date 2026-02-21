# Clove Canonical / Clerk Deprecated — Naming Decision (2026-02-21)

**Decision ID:** AUTH-NAMING-001
**Status:** RATIFIED
**Effective:** 2026-02-21
**PIN:** PIN-605

---

## Decision

The in-house authentication system is canonically named **Clove**. The prior name "HOC Identity" is treated as a legacy alias that is silently upgraded. Clerk is explicitly deprecated.

---

## Rationale

1. **Brand clarity:** "Clove" is a concise, unique name that avoids confusion with the generic "HOC Identity" label.
2. **Deprecation signal:** Making Clerk explicitly deprecated (rather than silently absent) prevents accidental re-adoption.
3. **Migration path:** Legacy `AUTH_PROVIDER=hoc_identity` is silently upgraded via alias mapping, avoiding breakage for existing deployments.

---

## Provider Identity Matrix

| Value | Status | Behavior |
|-------|--------|----------|
| `clove` | CANONICAL | Default. Factory selects `CloveHumanAuthProvider`. |
| `hoc_identity` | LEGACY ALIAS | Silently upgraded to `clove`. No warning. |
| `clerk` | DEPRECATED | Warning in non-prod. `RuntimeError` in prod. |
| any other | INVALID | Warning in non-prod. `RuntimeError` in prod. |

---

## Enum / Constant Changes

| Before | After | Notes |
|--------|-------|-------|
| `AuthProviderType.HOC_IDENTITY` | `AuthProviderType.CLOVE` | Canonical |
| `AuthProviderType.CLERK` | `AuthProviderType.CLERK` | Retained, marked deprecated |
| `AuthSource.HOC_IDENTITY` | `AuthSource.CLOVE` | Canonical |
| `AuthSource.CLERK` | `AuthSource.CLERK` | Retained, marked deprecated |
| `HOC_IDENTITY_ISSUER` | `CLOVE_ISSUER` | Backward-compat alias retained |
| `HOC_IDENTITY_AUDIENCE` | `CLOVE_AUDIENCE` | Backward-compat alias retained |
| `HocIdentityHumanAuthProvider` | `CloveHumanAuthProvider` | File: `auth_provider_clove.py` |
| `HocIdentityAuthAdapter` | `CloveAuthAdapter` | File: `CloveAuthAdapter.ts` |

---

## Env Var Migration

| Canonical (new) | Legacy (still accepted) |
|-----------------|------------------------|
| `CLOVE_ISSUER` | `HOC_IDENTITY_ISSUER` |
| `CLOVE_AUDIENCE` | `HOC_IDENTITY_AUDIENCE` |
| `CLOVE_JWKS_URL` | `HOC_IDENTITY_JWKS_URL` |
| `CLOVE_JWKS_FILE` | `HOC_IDENTITY_JWKS_FILE` |
| `CLOVE_JWKS_ENDPOINT` | `HOC_IDENTITY_JWKS_ENDPOINT` |
| `CLOVE_JWKS_CACHE_TTL_SECONDS` | `HOC_IDENTITY_JWKS_CACHE_TTL_SECONDS` |
| `CLOVE_JWKS_TIMEOUT_SECONDS` | `HOC_IDENTITY_JWKS_TIMEOUT_SECONDS` |

Canonical env vars take precedence. Legacy env vars are used as fallback.

---

## Files Changed

### Code
- `backend/app/auth/auth_constants.py` — enum + constant rename
- `backend/app/auth/auth_provider.py` — factory default, alias map, status contract
- `backend/app/auth/auth_provider_clove.py` — renamed from `auth_provider_hoc_identity.py`
- `backend/app/auth/contexts.py` — `AuthSource.CLOVE` canonical
- `backend/app/auth/gateway.py` — `CLOVE_ISSUER`, `AuthSource.CLOVE`
- `backend/app/hoc/api/auth/routes.py` — docstring update
- `backend/app/hoc/api/auth/schemas.py` — `canonical_provider` + `deprecation` fields

### Tests
- `backend/tests/auth/test_auth_provider_seam.py` — 49 tests (all clove-centric)
- `backend/tests/auth/test_auth_identity_routes.py` — provider status asserts `clove`

### Frontend
- `website/app-shell/src/auth/adapters/CloveAuthAdapter.ts` — renamed
- `website/app-shell/src/auth/types.ts` — `'clove' | 'clerk'`
- `website/app-shell/src/auth/index.ts` — import example updated

### Literature
- `literature/hoc_domain/platform/SOFTWARE_BIBLE.md` — reality delta
- `literature/hoc_domain/platform/HOC_PLATFORM_AUTH_PROVIDER_SEAM_CUTOVER_2026-02-21.md` — full update

### PIN
- `docs/memory-pins/PIN-605-clove-canonical-clerk-deprecated.md`

---

## Validation Results

- Tests: 49/49 PASSED
- Capability enforcer: CI PASSED (0 blocking, 5 advisory MISSING_EVIDENCE)

---

## Migration Notes for Downstream Consumers

1. Replace `AuthProviderType.HOC_IDENTITY` with `AuthProviderType.CLOVE`.
2. Replace `AuthSource.HOC_IDENTITY` with `AuthSource.CLOVE`.
3. Replace `from app.auth.auth_provider_hoc_identity import HocIdentityHumanAuthProvider` with `from app.auth.auth_provider_clove import CloveHumanAuthProvider`.
4. Replace `HOC_IDENTITY_ISSUER` with `CLOVE_ISSUER` (alias still works).
5. Update env vars from `HOC_IDENTITY_*` to `CLOVE_*` (legacy still accepted as fallback).
