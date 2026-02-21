# HOC Auth System Baseline And In-House Replacement Report

**Date:** 2026-02-21  
**Scope:** `hoc/*` canonical runtime with active app wiring  
**Intent:** Preserve existing auth/RBAC wiring structure, remove Clerk dependency, and introduce in-house auth plus onboarding/account management flows.

## 1. Executive Summary

This report confirms that the active runtime auth path is already centralized and modular enough for controlled Clerk removal without rewriting the entire stack.

The architecture should retain:
- `AuthGatewayMiddleware` as the authentication entrypoint
- `RBACMiddleware` as authorization enforcement
- `OnboardingGateMiddleware` as state gating
- `hoc_spine` authority policies as canonical policy sources

The architecture should replace:
- Clerk provider/token verification and frontend Clerk hooks
- Clerk-based login/session assumptions in frontend API client behavior

Primary blockers to address during replacement:
1. Access-tier label enforcement gap (`access_tier` in schema is not enforced in RBAC decision path).
2. Auth audit event does not currently propagate request ID.
3. Legacy `/api/v1/*` surface remains large in frontend and requires phased migration to canonical `hoc/*` routes.

## 2. Verified Runtime Wiring (Current State)

### 2.1 Main middleware stack and order

- `backend/app/main.py:928` adds `RBACMiddleware`
- `backend/app/main.py:945` adds `OnboardingGateMiddleware`
- `backend/app/main.py:948` invokes `setup_auth_middleware(app)` when gateway enabled
- `backend/app/main.py:940` documents reverse execution order (Auth -> Onboarding -> RBAC -> Tenant)

Conclusion: gateway-first auth context creation is already in place.

### 2.2 Auth wiring aggregator (keep this seam)

- `backend/app/hoc/cus/hoc_spine/auth_wiring.py:31` exports policy and app-auth shims
- `backend/app/hoc/cus/hoc_spine/auth_wiring.py:36` routes startup wiring through `app.auth.gateway_config`
- `backend/app/hoc/cus/hoc_spine/auth_wiring.py:42` routes RBAC middleware from `app.auth.rbac_middleware`

Conclusion: this file is the right stable seam for replacement; do not break it.

### 2.3 Gateway policy source and public-path behavior

- Canonical policy fallback list: `backend/app/hoc/cus/hoc_spine/authority/gateway_policy.py:46`
- App gateway config delegates to canonical policy: `backend/app/auth/gateway_config.py:77`
- Middleware default path source comes from schema loader at init: `backend/app/auth/gateway_middleware.py:59`

Conclusion: runtime uses schema-driven public paths by default, with canonical fallback policy still important as resilience/policy contract.

## 3. Current Authentication Planes

### 3.1 Gateway entrypoint and exclusivity rules

- JWT/API key mutual exclusivity: `backend/app/auth/gateway.py:191`
- Missing both headers => unauthenticated error: `backend/app/auth/gateway.py:196`
- Human flow via bearer token: `backend/app/auth/gateway.py:200`
- Machine flow via API key: `backend/app/auth/gateway.py:203`

### 3.2 Human auth (currently Clerk)

- Human path is Clerk-centric in gateway: `backend/app/auth/gateway.py:329`
- Tenant derived from `org_id` claim: `backend/app/auth/gateway.py:380`

### 3.3 Machine auth (must be preserved)

- Production key validation via service: `backend/app/auth/gateway.py:422`
- Machine context requires tenant/scopes from key service: `backend/app/auth/gateway.py:467`
- Legacy env key fallback exists (backward-compat path): `backend/app/auth/gateway.py:426`

### 3.4 Session revocation path

- Session store initialized in startup config: `backend/app/auth/gateway_config.py:35`
- Gateway checks revocation if store available: `backend/app/auth/gateway.py:372`

Conclusion: revocation is wired in code; runtime behavior depends on store availability.

### 3.5 Veil and sandbox planes

- Veil policy (`AOS_MODE=prod` + `HOC_DENY_AS_404`) in authority policy: `backend/app/hoc/cus/hoc_spine/authority/veil_policy.py:42`
- Middleware applies veil when no credentials: `backend/app/auth/gateway_middleware.py:166`
- Sandbox auth executes before normal gateway auth in local/test: `backend/app/auth/gateway_middleware.py:142`

## 4. Authorization and RBAC Reality

### 4.1 RBAC schema counts (authoritative current)

From `design/auth/RBAC_RULES.yaml`:
- Total rules: **73**
- Access tiers:
  - `PUBLIC`: **43**
  - `SESSION`: **24**
  - `MACHINE`: **4**
  - `PRIVILEGED`: **2**

Environment view:
- Preflight: 69 rules (PUBLIC 43, SESSION 20, MACHINE 4, PRIVILEGED 2)
- Production: 50 rules (PUBLIC 20, SESSION 24, MACHINE 4, PRIVILEGED 2)

### 4.2 Enforcement model (important gap)

- RBAC enforcement derives capabilities from auth context and checks `resource:action`: `backend/app/auth/rbac_middleware.py:371`
- Schema `access_tier` is not directly checked in RBAC `enforce()` path.

Risk: route tier labels can become descriptive rather than enforced if capabilities permit access.

## 5. Frontend Coupling Baseline (Clerk Removal Surface)

### 5.1 Clerk integration facts

- Files importing `@clerk/clerk-react`: **11 files** in `website/app-shell/src`
- Hook invocation lines (`useAuth/useUser/useClerk/useSignIn`) in code: **19**
- Plus top-level `ClerkProvider` in app bootstrap: `website/app-shell/src/main.tsx:29`

### 5.2 Auth client behavior

- API client contract and 401 redirect are Clerk-oriented:
  - `website/app-shell/src/api/client.ts:7`
  - `website/app-shell/src/api/client.ts:74`
- Token injection done by `ClerkAuthSync` interceptor:
  - `website/app-shell/src/components/auth/ClerkAuthSync.tsx:27`
  - `website/app-shell/src/components/auth/ClerkAuthSync.tsx:31`

### 5.3 Legacy path footprint

- `/api/v1/` references in `website/app-shell/src`: **193** across **45** files

Implication: frontend canonicalization must be phased, not big-bang.

## 6. Onboarding And Account Management Baseline

### 6.1 Onboarding gate middleware already exists

- Gate checks required state from canonical onboarding policy: `backend/app/auth/onboarding_gate.py:51`
- Gate reads tenant onboarding state and blocks with 403 when unmet: `backend/app/auth/onboarding_gate.py:64`

### 6.2 Onboarding status API already exists

- API surface for status/next action/capability gating: `backend/app/hoc/api/int/agent/onboarding.py:49`
- Uses auth context tenant binding and DB-backed onboarding state: `backend/app/hoc/api/int/agent/onboarding.py:243`

### 6.3 Account management surface already exists

- Unified accounts API for projects/users/profile/billing: `backend/app/hoc/api/cus/account/aos_accounts.py:71`
- Tenant scoping from auth context: `backend/app/hoc/api/cus/account/aos_accounts.py:82`
- L5 facade and L6 driver layering already structured: `backend/app/hoc/cus/account/L5_engines/accounts_facade.py:50`

Conclusion: onboarding/account domain surfaces are present and reusable for in-house auth rollout.

## 7. In-House Replacement Design (Preserve Wiring, Remove Clerk)

## 7.1 Keep unchanged (structural)

1. `app.hoc.cus.hoc_spine.auth_wiring` as single import seam.
2. Middleware order and gateway->onboarding->RBAC flow.
3. `MachineCapabilityContext` and API key service path.
4. `OnboardingGateMiddleware` and existing onboarding/account APIs.

## 7.2 Replace (auth provider internals)

1. Replace Clerk provider verification in gateway human path with in-house identity/session provider.
2. Replace frontend Clerk hooks/provider with in-house auth SDK/store.
3. Replace Clerk-centric login UX with first-party auth endpoints and session handling.

## 7.3 Proposed in-house auth V1 contract

Canonical auth API (new):
1. `POST /hoc/api/auth/register`
2. `POST /hoc/api/auth/login`
3. `POST /hoc/api/auth/refresh`
4. `POST /hoc/api/auth/logout`
5. `GET /hoc/api/auth/me`
6. `POST /hoc/api/auth/password/reset/request`
7. `POST /hoc/api/auth/password/reset/confirm`

Session/context bridge (keep/align):
- Continue `GET /session/context` behavior, but source identity from in-house auth.
- Add canonical alias endpoint under `hoc/*` if needed, then deprecate `/api/v1/session/context` path.

## 7.4 Token/session strategy (V1 recommendation)

1. Use short-lived access token + refresh token with server-side revocation checks.
2. Keep session revocation store integration in `gateway_config`/`gateway` path.
3. Keep gateway XOR rule: bearer OR API key, never both.
4. Preserve machine key auth unchanged during human auth migration.

## 7.5 Tenant and role mapping in-house

1. Human auth must always resolve stable internal `user_id`.
2. Tenant membership must resolve to `tenant_id` in `HumanAuthContext`.
3. RBAC capabilities for humans should be derived from internal role/membership records, not JWT role claims.

## 8. Required Security And Governance Remediations During Replacement

1. Enforce `access_tier` semantics in authorization flow (not just capabilities).
2. Add `request_id` propagation into auth audit emit calls.
3. Remove or quarantine legacy frontend auth store usage (`localStorage`) for auth authority.
4. Keep veil and sandbox behavior explicitly environment-gated and audited during migration.

## 9. Migration Plan (Implementation-Oriented)

### Phase 1: Provider abstraction without behavior change

1. Introduce `HumanAuthProvider` interface used by gateway.
2. Adapt current Clerk path behind interface.
3. Add in-house provider implementation scaffold (disabled).

**Exit gate:** no behavior change in staging; existing auth tests still pass.

### Phase 2: In-house auth backend active (dual-run option)

1. Enable in-house login/register/session endpoints.
2. Route gateway human verification through feature flag to in-house provider.
3. Keep machine path untouched.

**Exit gate:** tenant-bound CUS access works with in-house human auth and with API keys.

### Phase 3: Frontend cutover

1. Replace `ClerkProvider` and hook usage in app-shell.
2. Replace `ClerkAuthSync` with in-house token/session synchronizer.
3. Keep route guard semantics but use new auth context source.

**Exit gate:** protected routes work with in-house auth; no Clerk runtime dependency.

### Phase 4: Canonicalization and cleanup

1. Migrate prioritized frontend `/api/v1/*` calls to canonical `hoc/*` endpoints.
2. Deprecate/remove Clerk provider code paths.
3. Remove dead compatibility paths post-observability verification.

**Exit gate:** Clerk removed from active code path; release checks pass.

## 10. Observability And Debug Requirements For Replacement

Minimum must-have for each auth request:
1. `request_id`
2. auth plane (human/machine/sandbox)
3. auth source (inhouse/api_key/fops)
4. tenant_id (if applicable)
5. decision result and failure class

Required outcomes:
1. Trace failed login -> gateway decision -> RBAC decision with single correlation ID.
2. Distinguish unauthenticated vs unauthorized vs onboarding-state violations.
3. Emit metrics for auth success/failure by plane/source and route class.

## 11. Concrete Next Steps (Execution Ready)

1. Add provider abstraction in gateway and create in-house provider skeleton.
2. Add request_id propagation into `emit_auth_audit` call in gateway middleware.
3. Add explicit access-tier enforcement check in RBAC decision path.
4. Draft frontend replacement map for 11 Clerk files and 193 `/api/v1/` call sites.
5. Implement in-house auth endpoints and wire `/session/context` to in-house identity.
6. Execute staged cutover with machine auth continuity probes and onboarding/account regression tests.

## 12. Final Recommendation

Proceed with in-house auth replacement using existing wiring and middleware topology. Do not rewrite auth architecture from scratch.

The current system already has:
- centralized auth gateway,
- layered middleware ordering,
- onboarding gate,
- account management surfaces,
- machine auth service path.

The right strategy is controlled provider replacement + RBAC hardening + frontend coupling removal.
