# HOC Auth Clerk Replacement Design V1

**Date:** 2026-02-21  
**Status:** DRAFT FOR IMPLEMENTATION  
**Scope:** Preserve existing auth topology; replace Clerk with in-house identity and RBAC-compatible human auth provider.

## 1) Goal

Replace Clerk-based human authentication with first-party HOC Identity while preserving existing runtime topology and machine-auth behavior.

Target line:

`Gateway Auth Middleware -> Onboarding Gate -> RBAC Middleware -> Veil Policy -> Route Handler`

## 2) Hard Invariants

1. Do not change middleware ordering in `backend/app/main.py`.
2. Keep API key machine auth path intact (`X-AOS-Key`).
3. Keep onboarding gate behavior and account APIs intact.
4. Keep veil/sandbox controls behaviorally equivalent.
5. Human auth replacement must be provider-swappable through a single backend seam.

## 3) Current Runtime Seams (Authoritative)

1. Wiring aggregator: `backend/app/hoc/cus/hoc_spine/auth_wiring.py`
2. Auth gateway setup: `backend/app/auth/gateway_config.py`
3. Human + machine auth core: `backend/app/auth/gateway.py`
4. Gateway middleware: `backend/app/auth/gateway_middleware.py`
5. RBAC enforcement: `backend/app/auth/rbac_middleware.py`
6. Onboarding gate: `backend/app/auth/onboarding_gate.py`

## 4) Target Architecture

## 4.1 HumanAuthProvider seam

Introduce backend interface:

1. `verify_bearer_token(token: str) -> HumanPrincipal`
2. `resolve_tenant(principal: HumanPrincipal, requested_tenant: str | None = None) -> TenantContext`
3. `session_state(principal: HumanPrincipal) -> SessionInfo | None` (optional helper)

`AuthGateway` calls provider for human auth only; machine auth remains as-is.

## 4.2 HumanPrincipal contract

Required fields:

1. `subject_user_id: str`
2. `email: str | None`
3. `tenant_id: str | None`
4. `roles_or_groups: list[str]` (optional, not direct authority)
5. `session_id: str | None`
6. `issued_at: datetime`
7. `expires_at: datetime`
8. `auth_provider: str` (`clerk`, `hoc_identity`)

## 4.3 Context emission requirements (drop-in compatibility)

Gateway must continue emitting existing context types:

1. `HumanAuthContext` with `actor_id`, `session_id`, `tenant_id`, `auth_source`
2. `MachineCapabilityContext` unchanged
3. `FounderAuthContext` unchanged

Downstream consumers depend on these:

1. RBAC derives capabilities by context type in `backend/app/auth/rbac_middleware.py`
2. Onboarding gate requires `tenant_id` in `backend/app/auth/onboarding_gate.py`
3. Session context endpoint reads context in `backend/app/hoc/api/cus/integrations/session_context.py`

## 4.4 Provider implementations

1. `ClerkHumanAuthProvider` (compat provider; existing behavior wrapped)
2. `HocIdentityHumanAuthProvider` (target provider)

Provider selection via config, defaulting to current provider until cutover.

## 5) Identity Strategy (V1)

Recommended mode: JWT verification via JWKS (local signature validation, no per-request introspection call).

Token requirements:

1. `sub` (user id)
2. `sid` or `jti` (session id for revocation checks)
3. `tenant_id` (preferred) or deterministic tenant selection mechanism
4. `exp`, `iat`, `iss`, `aud`

Do not accept tenant from header without membership validation.

## 6) Frontend Replacement Design

## 6.1 Adapter boundary

Create app auth boundary:

1. `AuthProvider` component
2. `useAuth()` hook with:
   - `isAuthenticated`
   - `user`
   - `getAccessToken()`
   - `signIn()`
   - `signOut()`

## 6.2 Adapter implementations

1. `ClerkAuthAdapter` (temporary)
2. `HocIdentityAuthAdapter` (target)

Switch using config (e.g., `AUTH_PROVIDER=clerk|hoc_identity`).

## 6.3 Client token injection

Replace Clerk-specific sync with generic token sync:

1. Keep request interceptor model in `website/app-shell/src/api/client.ts`
2. Inject token from `useAuth().getAccessToken()`
3. Remove Clerk coupling from client and route guards.

## 7) RBAC Tightening During Replacement

Current risk: `access_tier` is schema metadata but enforcement is capability-based.

V1 tightening without RBAC rewrite:

1. Preserve capability-based decision path.
2. Introduce deterministic tier-to-capability derivation contract.
3. Enforce that effective capabilities cannot violate declared tier constraints.
4. Add negative tests for tier breach cases.

## 8) Migration Plan

## Phase 0: Seam extraction (no behavior change)

1. Add `HumanAuthProvider` interface.
2. Wrap current Clerk path in `ClerkHumanAuthProvider`.
3. Refactor gateway to call provider interface only.
4. Add frontend `AuthProvider` wrapper backed by Clerk adapter.

Exit: behavior unchanged.

## Phase 1: Parallel in-house provider

1. Implement `HocIdentityHumanAuthProvider`.
2. Add backend provider flag selection in auth wiring/config.
3. Add frontend `HocIdentityAuthAdapter`.

Exit: stagetest can run either provider.

## Phase 2: Tenant and session correctness

1. Enforce tenant binding from HOC identity claims/membership.
2. Confirm revocation semantics with `sid/jti` integration.
3. Validate onboarding/account flows with in-house auth principal.

Exit: CUS protected routes return correct 200/401/403 with tenant-bound behavior.

## Phase 3: Clerk decommission

1. Remove Clerk provider wiring and unused hooks/components.
2. Keep compatibility flag disabled for one release cycle.
3. Remove residual Clerk code after stability window.

Exit: no active Clerk dependency in runtime paths.

## 9) Minimal Vertical Slice Acceptance

Run first replacement slice on stagetest:

1. Login via in-house auth
2. Acquire token/session
3. Call CUS activity endpoint with valid tenant context
4. Confirm 200 response for authorized tenant
5. Revoke session and confirm denial (401/403 depending policy)

## 10) Observability Requirements

Every auth decision event should carry:

1. `request_id`
2. auth plane (`human`, `machine`, `sandbox`)
3. auth source (`hoc_identity`, `api_key`, `fops`)
4. tenant_id (if present)
5. decision + error class

Must support end-to-end trace:

`login -> gateway authenticate -> onboarding gate -> RBAC decision -> route response`

## 11) Open Clarifications Required Before Build Start

1. Multi-tenant user handling:
   - token-bound `tenant_id` only, or
   - selectable active tenant with membership validation
2. Refresh strategy:
   - rotating refresh tokens vs fixed session tokens
3. Session store authority:
   - Redis-only vs DB-backed revocation source of truth
4. Password policy and MFA:
   - V1 scope explicitly password-only or include MFA bootstrap

## 12) Non-Goals (V1)

1. Full RBAC engine rewrite
2. Complete `/api/v1/*` migration in same auth PR
3. Re-architecting onboarding/account domains
4. Replacing machine API key auth model

## 13) Implementation Note

This design intentionally minimizes risk by changing identity-provider internals only, not middleware topology or machine auth contract.

## 14) Locked Design Decisions (Added 2026-02-21)

The following are now treated as V1 design locks unless explicitly changed by governance review.

### D1. Active tenant model

1. Every human access token carries exactly one active `tenant_id`.
2. Per-request tenant override is not allowed for CUS route authorization.
3. Tenant switch is explicit via `POST /auth/switch-tenant` and issues a new session/token set.

### D2. Access + refresh token handling

1. Access token is short-lived (target 5-15 minutes).
2. Access token is held in frontend memory only.
3. Refresh token is rotating and stored in `HttpOnly Secure SameSite` cookie.
4. Frontend refresh path is single-canonical flow through auth adapter (`useAuth().getAccessToken()` orchestration).

### D3. Revocation model

1. DB is durable source of truth for session state.
2. Redis is low-latency revocation cache/index.
3. Logout/revoke writes durable state and updates cache/index.
4. Gateway revocation path remains in current seam (`session_id`/`sid`-based check).

### D4. V1 identity scope

1. V1 includes password login, email verification, and password reset.
2. MFA is deferred to V1.1 unless compliance gate mandates earlier inclusion.

### D5. Token claim contract baseline

Required claims for human access token:

1. `sub` (user id)
2. `sid` (session id) or equivalent revocation-key claim
3. `tenant_id` (active tenant)
4. `iat`
5. `exp`
6. `iss`
7. `aud`

Optional claims:

1. `tenant_slug` (display only)
2. `tier` (if used by RBAC tier precheck)
3. provider marker (e.g., `provider=hoc_identity`)

### D6. Cutover strategy

1. Stagetest uses HOC Identity as default with temporary fallback window.
2. Production uses staged rollout (shadow/parallel verification where needed, then allowlisted tenant rollout).
3. No big-bang production cutover.

### D7. Frontend auth state contract

The auth adapter exposes deterministic states:

1. `anonymous`
2. `authenticating`
3. `authenticated`
4. `expired`
5. `unauthorized`

Deterministic redirect posture:

1. `anonymous` -> `/login`
2. `authenticating` -> no redirect; loading state
3. `expired` -> `/login?reason=expired`
4. `unauthorized` -> `/403` (or equivalent product denial route)

### D8. RBAC hardening in same release

1. Add explicit tier compatibility gate before capability allow.
2. Keep existing capability-based enforcement model (no full RBAC rewrite in V1).
3. Add negative tests for tier mismatch denial (`low-tier` principal against higher-tier surface).

## 15) Identity Endpoints (V1 Canonical)

Primary auth endpoints:

1. `POST /hoc/api/auth/register`
2. `POST /hoc/api/auth/login`
3. `POST /hoc/api/auth/refresh`
4. `POST /hoc/api/auth/switch-tenant`
5. `POST /hoc/api/auth/logout`
6. `GET /hoc/api/auth/me`
7. `POST /hoc/api/auth/password/reset/request`
8. `POST /hoc/api/auth/password/reset/confirm`

Compatibility bridge:

1. Preserve `GET /session/context` behavior while replacing identity source.
2. Add canonical alias under `hoc/*` when cutover sequence requires it.

## 16) Error Taxonomy (Operational Contract)

Internal reason codes for deterministic troubleshooting:

1. `NOT_AUTHENTICATED`
2. `TOKEN_EXPIRED`
3. `TOKEN_INVALID_SIGNATURE`
4. `SESSION_REVOKED`
5. `TENANT_MISSING`
6. `TIER_INSUFFICIENT`
7. `CAPABILITY_DENIED`
8. `ONBOARDING_INCOMPLETE`

Notes:

1. External response may still be veiled (404 posture) by policy.
2. Internal logs/metrics/audit events must preserve true deny reason.

## 17) Rollout Flags (Control Plane)

Suggested rollout controls:

1. `AUTH_PROVIDER=clerk|hoc_identity`
2. `ENABLE_SHADOW_VERIFY=true|false`
3. `TENANT_ROLLOUT_ALLOWLIST=<csv|set>`

Flag intent:

1. Provider flip without topology changes.
2. Safe staged rollout by tenant scope.
3. Controlled fallback during transition.

## 18) Minimal Vertical Slice (Lock)

First slice proving criteria:

1. In-house login issues valid access and refresh credentials.
2. Authenticated call to `/hoc/api/cus/activity/runs` returns 200 for valid tenant context.
3. Session revocation causes subsequent denial.
4. Request trace contains request id and auth decision metadata.

## 19) Remaining Pre-Build Gates (Not Yet Locked)

These are still open and must be finalized before implementation begins:

1. Crypto profile detail (algorithms, JWKS rotation cadence, cache invalidation TTL).
2. CSRF strategy for cookie-backed refresh/switch/logout endpoints.
3. Revocation dependency failure policy (Redis/DB degraded behavior).
4. Identity migration exact method for existing Clerk users (JIT and/or staged backfill mechanics).
5. Abuse/rate-limit controls for login and reset endpoints.

## 20) V1 Security/Identity Decisions (Locked From Latest Review)

### 20.1 Deployment and migration scope

1. No Clerk user migration is required for V1 bootstrap (fresh in-house identity bootstrap).
2. Legacy session surfaces are decommission targets; remove or explicitly return legacy-removed behavior.
3. Machine auth path remains untouched during human-auth replacement.

### 20.2 Crypto and key distribution

1. Access tokens are locally verifiable JWTs through JWKS.
2. Key publication endpoint: `GET /.well-known/jwks.json`.
3. Two-key active window policy:
   - one current signing key
   - one previous verification key retained through token expiry window
4. Rotation cadence target: every 30 days, with emergency out-of-band rotation support.
5. Gateway JWKS cache behavior:
   - cache TTL target: 10 minutes
   - on unknown `kid`, force one refresh and retry once before deny.

### 20.3 Token/session model

1. Access token lifetime target: 5-15 minutes.
2. Access token is stored in frontend memory only.
3. Refresh token is opaque, rotating, and stored in `HttpOnly Secure SameSite` cookie.
4. Refresh token material in storage is hashed (no plaintext persistence).

### 20.4 CSRF controls for cookie-auth endpoints

Double-submit model is locked for V1:

1. CSRF cookie: readable cookie (non-HttpOnly) with secure attributes.
2. Header requirement: `X-CSRF` must match CSRF cookie value.
3. Mandatory on:
   - `POST /hoc/api/auth/refresh`
   - `POST /hoc/api/auth/switch-tenant`
   - `POST /hoc/api/auth/logout`
4. Add origin validation (`Origin`/`Referer`) and CORS allowlist enforcement for defense in depth.

### 20.5 Access token claim contract (V1 canonical)

Required claims:

1. `iss` (issuer)
2. `aud` (audience)
3. `sub` (user id)
4. `tid` (active tenant id)
5. `sid` (session id for revocation lookup)
6. `tier` (tier fact for tier gate)
7. `iat`
8. `exp`
9. `jti`

Optional claims:

1. `email`
2. `roles`
3. `caps` (optional snapshot only; backend remains authority for final permissioning)

### 20.6 Revocation dependency failure policy

V1 protected-route policy is fail-closed when revocation cannot be reliably evaluated:

1. Redis unavailable + DB available -> fallback to DB revocation check.
2. Redis unavailable + DB unavailable -> deny protected request with dependency-unavailable reason.
3. Identity endpoints requiring state change (`refresh`, `switch-tenant`, `logout`) require durable backend availability.

### 20.7 Abuse controls (login/reset)

Minimum V1 controls:

1. Per-IP rate limit.
2. Per-identifier (email) rate limit.
3. Progressive backoff on repeated failures.
4. Optional short lock window after threshold failures.
5. Uniform external credential error response to prevent user enumeration.
6. Internal audit logs include request id, IP, user agent, and reject reason.

### 20.8 Legacy endpoint purge policy

For removed legacy session routes (including `/api/v1/session/context` replacement path):

1. Prefer explicit decommission response (`410`) with stable legacy-removed error code, or
2. veil-compatible `404` where policy requires nondisclosure.

Canonical frontend target remains `hoc/*` surfaces.

## 21) JWT Algorithm Lock (Final)

V1 algorithm is locked:

1. `alg`: `EdDSA`
2. curve: `Ed25519`

Operational lock:

1. JWKS endpoint remains `/.well-known/jwks.json`.
2. Two-key active window policy remains mandatory (current + previous).
3. Gateway JWKS cache TTL remains 10 minutes.
4. On unknown `kid`, gateway refreshes JWKS once and retries once before deny.

Token/header lock:

1. JWT header includes `kid`.
2. JWT header includes `typ=JWT`.
3. Required claims remain: `iss`, `aud`, `sub`, `tid`, `sid`, `tier`, `iat`, `exp`, `jti`.

Compatibility note:

1. `RS256` is only a contingency for proven interoperability blockers in external dependencies.
