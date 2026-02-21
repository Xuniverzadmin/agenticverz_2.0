# HOC Platform Auth Provider Seam Cutover (2026-02-21)

**Domain:** platform
**Capability:** CAP-006 (authentication)
**Status:** IMPLEMENTED — Clove is canonical, Clerk is deprecated

---

## Intent

Remove Clerk-first runtime behavior from the auth seam and make Clove (formerly "HOC Identity") the canonical human-auth path, while preserving machine API-key authentication behavior.

---

## Naming Decision (2026-02-21)

The in-house auth system is canonically named **Clove**. The prior name "HOC Identity" is treated as a legacy alias. Clerk is explicitly deprecated.

| Identity | Status | Notes |
|----------|--------|-------|
| `clove` | CANONICAL | Default `AUTH_PROVIDER` value |
| `hoc_identity` | LEGACY ALIAS | Silently upgraded to `clove` |
| `clerk` | DEPRECATED | Warning in non-prod, fail-fast in prod |

---

## Scope Implemented

### 1. Provider selection default switched to Clove

- File: `backend/app/auth/auth_provider.py`
- Change:
  - `AUTH_PROVIDER` default changed to `clove`.
  - Factory now forces `clove` if any unsupported value is provided.
  - `hoc_identity` is silently upgraded via `_LEGACY_ALIASES`.
  - `clerk` triggers explicit deprecation warning (non-prod) or RuntimeError (prod).
  - `get_human_auth_provider_status()` reports `canonical_provider`, `deprecation` metadata.

### 2. Human JWT routing switched to Clove issuer only

- File: `backend/app/auth/gateway.py`
- Change:
  - Uses `CLOVE_ISSUER` (was `HOC_IDENTITY_ISSUER`).
  - Human path now accepts only `CLOVE_ISSUER` for tenant-scoped user auth.
  - Provider-to-context source uses `AuthSource.CLOVE`.
  - FOPS founder-token route remains unchanged.

### 3. Provider implementation renamed

- File: `backend/app/auth/auth_provider_clove.py` (was `auth_provider_hoc_identity.py`)
- Class: `CloveHumanAuthProvider` (was `HocIdentityHumanAuthProvider`)
- Change:
  - Full EdDSA/JWKS verification implemented.
  - Env vars accept both `CLOVE_*` (canonical) and `HOC_IDENTITY_*` (legacy fallback).
  - `provider_type` returns `AuthProviderType.CLOVE`.

### 4. Auth constants updated

- File: `backend/app/auth/auth_constants.py`
- Change:
  - `AuthProviderType.CLOVE = "clove"` is canonical; `CLERK = "clerk"` marked deprecated.
  - `CLOVE_ISSUER`, `CLOVE_AUDIENCE` are canonical constants.
  - `HOC_IDENTITY_ISSUER`, `HOC_IDENTITY_AUDIENCE` are backward-compatible aliases.

### 5. Auth contexts updated

- File: `backend/app/auth/contexts.py`
- Change:
  - `AuthSource.CLOVE = "clove"` is canonical; `CLERK = "clerk"` marked deprecated.

### 6. Frontend adapter renamed

- File: `website/app-shell/src/auth/adapters/CloveAuthAdapter.ts` (was `HocIdentityAuthAdapter.ts`)
- Class: `CloveAuthAdapter` (was `HocIdentityAuthAdapter`)
- Provider type: `'clove'` (was `'hoc_identity'`)
- Type union: `'clove' | 'clerk'` (was `'clerk' | 'hoc_identity'`)

### 7. Provider status endpoint enriched

- File: `backend/app/hoc/api/auth/routes.py`
- Response schema: Added `canonical_provider` and `deprecation` fields.

---

## Runtime Behavior After This Change

### Human auth

- Canonical route: `Authorization: Bearer <jwt>` with `iss == CLOVE_ISSUER`.
- Provider: `CloveHumanAuthProvider` — fully implements EdDSA/JWKS verification.
- Status endpoint: `GET /hoc/api/auth/provider/status` → `effective_provider=clove`, includes deprecation metadata.

### Machine auth

- Unchanged:
  - `X-AOS-Key` and DB API-key validation path remain active.

---

## Verification Evidence

- Auth seam tests:
  - Command: `PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py tests/auth/test_auth_identity_routes.py -v`
  - Result: `49 passed`
- Capability registry enforcer (changed files):
  - Result: `CI PASSED` with non-blocking `MISSING_EVIDENCE` warnings.

---

## Explicit Non-Goals (Not Implemented in This Cutover)

1. Clerk module deletion across the entire repository.
2. Production login/refresh/switch/logout business logic (routes remain scaffold-level).
3. JWKS key rotation strategy (deferred to identity lifecycle phase).
