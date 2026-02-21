# HOC_CUS_Pre_Wave0_Auth_Audit_2026-02-21

**Created:** 2026-02-21
**Task:** T1 — Auth Audit
**Status:** DONE

---

## 1. Objective

Inventory current auth behavior end-to-end: frontend flows, backend providers, guards, machine path, and route surfaces. Produce a deterministic map of what exists before Wave A implementation begins.

---

## 2. Frontend Auth Inventory

### 2.1 Provider: Clerk (Active)

| File | Line | Role |
|------|------|------|
| `website/app-shell/src/main.tsx:4,29-33` | 4,29 | `ClerkProvider` wrapping entire app |
| `website/app-shell/src/api/client.ts:7-8,65-78` | 7 | Token attachment via `ClerkAuthSync` component |
| `website/app-shell/src/stores/authStore.ts:4-47` | 4 | Deprecated auth store — redirects to Clerk hooks |
| `website/app-shell/src/hooks/useSessionContext.ts:53-86` | 53 | Session context fetch after Clerk authentication |
| `website/app-shell/src/pages/auth/LoginPage.tsx:2-8` | 2 | Custom login UI using Clerk headless hooks |

### 2.2 Route Guards

| Guard | File | Line | Usage |
|-------|------|------|-------|
| `ProtectedRoute` | `routes/ProtectedRoute.tsx:18` | 18 | Customer routes (`/cus/*`) — checks Clerk `isSignedIn` |
| `FounderRoute` | `routes/FounderRoute.tsx:66` | 66 | Founder routes (`/prefops/*`, `/fops/*`) — checks Clerk + backend `actor_type` |
| `OnboardingRoute` | `routes/OnboardingRoute.tsx:23` | 23 | Onboarding flow — checks Clerk + metadata |

### 2.3 Frontend API Call-Site Inventory

**Legacy `/api/v1/` call-sites: 69** (across `website/app-shell/src/`)

Key auth-related calls:
- `api/auth.ts:10` — `POST /api/v1/auth/login`
- `api/auth.ts:19` — `POST /api/v1/auth/logout`
- `api/auth.ts:23` — `POST /api/v1/auth/refresh`
- `api/auth.ts:28` — `GET /api/v1/users/me`
- `api/auth.ts:33` — `GET /api/v1/tenants`
- `api/auth.ts:38` — `POST /api/v1/tenants/switch`

**HOC `/hoc/api/` call-sites: 30** (all in scaffold catalog + stagetest client)
- `features/scaffold/scaffoldCatalog.ts:29-198` — 18 scaffold facade paths
- `features/stagetest/stagetestClient.ts:108` — Stagetest base URL

### 2.4 HOC Auth Adapters (Scaffold — NOT WIRED)

| Adapter | File | Status |
|---------|------|--------|
| `ClerkAuthAdapter` | `src/auth/adapters/ClerkAuthAdapter.ts:30-89` | Scaffold — all methods throw "not yet wired" |
| `CloveAuthAdapter` | `src/auth/adapters/CloveAuthAdapter.ts:33-109` | Scaffold — TODOs for `/hoc/api/auth/*` calls |
| `AuthTokenSync` | `src/auth/AuthTokenSync.ts:37-57` | Scaffold — axios interceptor for Bearer token |

**Key finding:** Frontend is 100% Clerk-dependent. `HocAuthProvider` + adapters are scaffold structure only.

---

## 3. Backend Auth Provider Architecture

### 3.1 Provider Seam (Factory Pattern)

| Component | File | Line | Role |
|-----------|------|------|------|
| `HumanAuthProvider` ABC | `app/auth/auth_provider.py:84` | 84 | Abstract interface: `verify_bearer_token()` |
| `HumanPrincipal` | `app/auth/auth_provider.py:46` | 46 | Provider-neutral identity (frozen dataclass) |
| `get_human_auth_provider()` | `app/auth/auth_provider.py:135` | 135 | Factory — returns `CloveHumanAuthProvider` singleton |
| `AUTH_PROVIDER_ENV` | `app/auth/auth_provider.py:126` | 126 | `os.getenv("AUTH_PROVIDER", "clove")` — canonical default |

**Provider selection policy:**
- `clove` (default) → `CloveHumanAuthProvider`
- `hoc_identity` → silent upgrade to `clove`
- `clerk` → deprecated (non-prod: warning, prod: `RuntimeError`)
- Other → forced to `clove` with warning (non-prod), `RuntimeError` (prod)

### 3.2 Clove Provider (Canonical)

| Config | Env Var | Default |
|--------|---------|---------|
| Issuer | `CLOVE_ISSUER` | `https://auth.agenticverz.com` |
| Audience | `CLOVE_AUDIENCE` | `clove` |
| JWKS URL | `CLOVE_JWKS_URL` | None |
| JWKS File | `CLOVE_JWKS_FILE` | None |
| Algorithm | — | EdDSA (Ed25519) |

**Token verification:** `auth_provider_clove.py:125+` — EdDSA via PyJWT + JWKS (URL with TTL cache or static file).

**Readiness checks:** `readiness_checks()` validates issuer, audience, jwks_source. Startup gate in `main.py:687-735` enforces readiness (prod=fatal, non-prod=warning).

### 3.3 JWT Claims Contract

From `auth_constants.py:37-63`:

| Claim | Field | Mandatory |
|-------|-------|-----------|
| `iss` | Issuer | YES |
| `aud` | Audience | YES |
| `sub` | Subject (user ID) | YES |
| `tid` | Tenant ID | YES |
| `sid` | Session ID | YES |
| `tier` | Tenant tier | YES |
| `iat` | Issued at | YES |
| `exp` | Expires at | YES |
| `jti` | JWT ID | YES |
| `email` | Email | Optional |
| `roles` | Roles array | Optional |

---

## 4. Gateway Architecture

### 4.1 Central Gateway (`app/auth/gateway.py`)

**Invariants:**
1. Mutual exclusivity: JWT XOR API Key (both = `MIXED_AUTH` error)
2. Human flow: Clove JWT (EdDSA) → `HumanAuthContext`
3. Machine flow: API key → `MachineCapabilityContext`
4. Founder flow: FOPS JWT → `FounderAuthContext`
5. Session revocation checked per human request
6. Auth headers stripped after gateway

**Flow:**
```
Request → AuthGatewayMiddleware.dispatch()
  ├─ Public path check → bypass
  ├─ Sandbox auth check (dev only, PIN-439)
  ├─ Extract Authorization + X-AOS-Key headers
  └─ gateway.authenticate()
      ├─ Mutual exclusivity check
      ├─ _authenticate_human() → _route_by_issuer()
      │   ├─ FOPS issuer → FounderAuthContext
      │   ├─ CLOVE issuer → CloveHumanAuthProvider.verify_bearer_token() → HumanAuthContext
      │   └─ Other → REJECT (JWT_INVALID)
      └─ _authenticate_machine() → api_key_service.validate_key() → MachineCapabilityContext
  → request.state.auth_context = result
```

### 4.2 Auth Context Types

| Context | Injected As | Key Fields | Plane |
|---------|-------------|------------|-------|
| `HumanAuthContext` | `request.state.auth_context` | `actor_id`, `session_id`, `tenant_id`, `auth_source=CLOVE` | HUMAN |
| `MachineCapabilityContext` | `request.state.auth_context` | `key_id`, `tenant_id`, `scopes: FrozenSet[str]`, `rate_limit` | MACHINE |
| `FounderAuthContext` | `request.state.auth_context` | `actor_id`, `reason` (audit) | HUMAN (control) |

### 4.3 Auth Deny Reasons

From `auth_constants.py:70-93`: `NOT_AUTHENTICATED`, `TOKEN_EXPIRED`, `TOKEN_INVALID_SIGNATURE`, `ISSUER_UNTRUSTED`, `SESSION_REVOKED`, `TENANT_MISSING`, `TENANT_MISMATCH`, `TIER_INSUFFICIENT`, `MIXED_AUTH`, `PROVIDER_UNAVAILABLE`, `INTERNAL_ERROR`.

---

## 5. Machine Auth Path (X-AOS-Key)

| Step | File | Line | Description |
|------|------|------|-------------|
| Header extraction | `gateway_middleware.py` | 159 | `X-AOS-Key` header parsed |
| Mutual exclusivity | `gateway.py` | 182-189 | Both JWT + API key = fail |
| Production validation | `gateway.py` | 431-458 | `api_key_service.validate_key()` → DB lookup |
| Legacy fallback | `gateway.py` | 406-407 | `AOS_API_KEY` env var comparison |
| Context creation | `gateway.py` | 446-454 | `MachineCapabilityContext` with scopes + rate_limit |

**SDK usage:**
- `sdk/python/aos_sdk/aos_sdk_client.py:138` — attaches `X-AOS-Key: {api_key}`
- `sdk/python/aos_sdk/aos_sdk_cus_enforcer.py:322,444` — request headers

---

## 6. Route Surface Map

### 6.1 HOC Auth Endpoints (Scaffold — 501)

All at prefix `/hoc/api/auth` (`app/hoc/api/auth/routes.py:54`):

| Method | Path | Status |
|--------|------|--------|
| POST | `/hoc/api/auth/register` | 501 scaffold |
| POST | `/hoc/api/auth/login` | 501 scaffold |
| POST | `/hoc/api/auth/refresh` | 501 scaffold |
| POST | `/hoc/api/auth/switch-tenant` | 501 scaffold |
| POST | `/hoc/api/auth/logout` | 501 scaffold |
| GET | `/hoc/api/auth/me` | 501 scaffold |
| GET | `/hoc/api/auth/provider/status` | 200 (implemented) |
| POST | `/hoc/api/auth/password/reset/request` | 501 scaffold |
| POST | `/hoc/api/auth/password/reset/confirm` | 501 scaffold |

### 6.2 Public Path Policy

**Source of truth (runtime):** `gateway_policy.py` PUBLIC_PATHS → `get_gateway_policy_config()` → `AuthGatewayMiddleware(public_paths=[...])`.

**RBAC schema (declarative):** `design/auth/RBAC_RULES.yaml` — `HOC_AUTH_PROVIDER_STATUS` rule added (commit `e88f5964`).

### 6.3 Legacy vs Canonical Route Usage

| Surface | Frontend Calls | Backend Status |
|---------|---------------|----------------|
| `/api/v1/` | 69 call-sites | Legacy — tombstoned (PIN-526, 2026-03-04) |
| `/hoc/api/` | 30 call-sites | Canonical — scaffold + implemented |

---

## 7. Middleware Stack (Request Order)

From `main.py` startup:

1. `AuthGatewayMiddleware` — JWT/API key validation, context injection
2. `RBACMiddleware` — role-based access control enforcement
3. `OnboardingGateMiddleware` — onboarding state enforcement
4. Route handlers — access `request.state.auth_context`

---

## 8. Key Findings

1. **Frontend is 100% Clerk-dependent.** All auth state flows through Clerk hooks. HOC adapters are scaffold only.
2. **Backend Clove provider is canonical and operational** (EdDSA/JWKS, readiness gate, startup fail-fast).
3. **HOC auth endpoints are scaffold (501)** — no real identity management yet.
4. **Machine auth (X-AOS-Key) is fully operational** via database-backed `api_key_service`.
5. **Three auth contexts** (Human, Machine, Founder) — all frozen, immutable, injected into `request.state`.
6. **69 legacy `/api/v1/` call-sites** in frontend must migrate to `/hoc/api/` before Clerk can be removed.
7. **Public path policy is dual-source** — `gateway_policy.py` (runtime) + `RBAC_RULES.yaml` (declarative). Both now consistent.
8. **No `/api/v1/auth` routes mounted** in current HOC surface — legacy mount point being phased out.
