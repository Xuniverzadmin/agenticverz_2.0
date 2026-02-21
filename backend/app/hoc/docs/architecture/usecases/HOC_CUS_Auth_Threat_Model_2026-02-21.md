# HOC_CUS_Auth_Threat_Model_2026-02-21

**Created:** 2026-02-21
**Task:** T3 — Security
**Status:** DONE

---

## 1. Objective

Produce threat model, minimum baseline controls, and enforcement map for the first-party Clove auth architecture (T2).

---

## 2. Threat Model

### 2.1 Attack Surface

| Surface | Entry Point | Auth Required | Data Exposed |
|---------|-------------|---------------|--------------|
| Login endpoint | `POST /hoc/api/auth/login` | No | Tokens on success |
| Refresh endpoint | `POST /hoc/api/auth/refresh` | Cookie | New access token |
| Register endpoint | `POST /hoc/api/auth/register` | No | Account creation |
| Password reset | `POST /hoc/api/auth/password/reset/*` | No | Reset flow |
| Provider status | `GET /hoc/api/auth/provider/status` | No | Operational diagnostics |
| Protected API | `GET/POST /hoc/api/cus/*` | JWT | Tenant data |
| Machine API | `GET/POST /* with X-AOS-Key` | API Key | Tenant data |
| JWKS endpoint | `GET /.well-known/jwks.json` | No | Public keys |

### 2.2 Threats

| ID | Threat | STRIDE | Severity | Mitigation |
|----|--------|--------|----------|------------|
| TH-01 | Credential stuffing on login | Spoofing | HIGH | Rate limiting (10 attempts/min/IP), account lockout after 5 failures |
| TH-02 | JWT token theft (XSS) | Spoofing | HIGH | Short-lived tokens (15min), no localStorage, Content-Security-Policy headers |
| TH-03 | Refresh token theft (cookie) | Spoofing | HIGH | HttpOnly + Secure + SameSite=Strict + __Host- prefix |
| TH-04 | CSRF on refresh/logout | Tampering | MEDIUM | Double-submit cookie pattern (csrf_token in cookie + X-CSRF-Token header) |
| TH-05 | JWT signature bypass | Tampering | CRITICAL | Algorithm pinned to EdDSA only; reject `alg: none`, `alg: HS256` |
| TH-06 | Cross-tenant data access | Elevation | CRITICAL | `tid` claim validated against session; tenant_id from JWT is authoritative |
| TH-07 | Session fixation | Spoofing | MEDIUM | New session ID on login; rotate refresh token on every refresh |
| TH-08 | Password hash brute-force | Info Disclosure | HIGH | Argon2id with 64MB memory cost; hash stored server-side only |
| TH-09 | Email enumeration via register/reset | Info Disclosure | LOW | Constant-time response for all register/reset requests |
| TH-10 | API key brute-force | Spoofing | MEDIUM | Keys are 32 bytes random (256 bits entropy); rate limiting on key validation |
| TH-11 | Mixed auth confusion | Elevation | HIGH | Mutual exclusivity enforced in gateway (JWT XOR API Key, never both) |
| TH-12 | JWKS key confusion | Tampering | HIGH | `kid` required in JWT header; strict key matching; no algorithm negotiation |

---

## 3. Baseline Controls

### 3.1 Authentication Controls

| Control | Implementation | Enforcement Point |
|---------|---------------|-------------------|
| Password hashing | Argon2id (64MB, 3 iterations, 1 parallelism) | `POST /register`, `POST /password/reset/confirm` |
| Token signing | EdDSA (Ed25519) only | `CloveHumanAuthProvider.verify_bearer_token()` |
| Token lifetime | Access: 15min, Refresh: 7 days | Token issuance at login/refresh |
| Session revocation | DB + Redis revocation check | `AuthGateway.authenticate()` per request |
| Refresh rotation | Old refresh invalidated on use | `POST /refresh` handler |
| JWKS validation | `kid` matching, no algorithm negotiation | `CloveHumanAuthProvider` |

### 3.2 Authorization Controls

| Control | Implementation | Enforcement Point |
|---------|---------------|-------------------|
| Tenant isolation | `tid` claim in JWT, validated per request | `HumanAuthContext.tenant_id` |
| Scope enforcement | `MachineCapabilityContext.scopes` checked | `has_scope()` method |
| Mutual exclusivity | JWT XOR API Key | `AuthGateway.authenticate():182-189` |
| RBAC enforcement | Role-based rules from `RBAC_RULES.yaml` | `RBACMiddleware` |
| Onboarding gate | State-based endpoint access | `OnboardingGateMiddleware` |

### 3.3 Transport Controls

| Control | Implementation | Enforcement Point |
|---------|---------------|-------------------|
| HTTPS only | TLS termination at Apache | Reverse proxy |
| Cookie security | `__Host-refresh; HttpOnly; Secure; SameSite=Strict` | `POST /login` response |
| CSRF protection | Double-submit cookie | `POST /refresh`, `/switch-tenant`, `/logout` |
| CORS | Strict origin allowlist | Middleware |
| Header stripping | Auth headers removed post-gateway | `AuthGatewayMiddleware` |

---

## 4. Deny Reason Taxonomy

From `auth_constants.py:70-93` — deterministic, machine-parseable denial codes:

| Deny Reason | HTTP Status | Trigger |
|-------------|-------------|---------|
| `NOT_AUTHENTICATED` | 401 | No auth header present |
| `TOKEN_EXPIRED` | 401 | JWT `exp` < now |
| `TOKEN_INVALID_SIGNATURE` | 401 | EdDSA signature verification failed |
| `ISSUER_UNTRUSTED` | 401 | `iss` not in trusted issuers list |
| `SESSION_REVOKED` | 401 | Session in revocation set |
| `TENANT_MISSING` | 401 | JWT missing `tid` claim |
| `TENANT_MISMATCH` | 403 | Requested tenant != JWT tenant |
| `TIER_INSUFFICIENT` | 403 | Operation requires higher tier |
| `MIXED_AUTH` | 400 | Both JWT + API Key present |
| `PROVIDER_UNAVAILABLE` | 503 | Auth provider not configured |
| `INTERNAL_ERROR` | 500 | Unexpected auth system error |

---

## 5. Enforcement Map

```
Request
  │
  ├─ [L2] AuthGatewayMiddleware
  │   ├─ Public path check → BYPASS
  │   ├─ Header extraction (Authorization / X-AOS-Key)
  │   ├─ Mutual exclusivity check → TH-11
  │   ├─ JWT verification (EdDSA, iss, aud, exp, kid) → TH-05, TH-12
  │   ├─ Session revocation check → TH-07
  │   └─ Context injection (HumanAuthContext / MachineCapabilityContext)
  │
  ├─ [L2] RBACMiddleware
  │   ├─ Rule resolution from RBAC_RULES.yaml
  │   ├─ Access tier check (PUBLIC / SESSION / PRIVILEGED / MACHINE)
  │   └─ Console/environment validation
  │
  ├─ [L2] OnboardingGateMiddleware
  │   └─ State-based endpoint access enforcement
  │
  └─ [L4+] Route handler
      ├─ Tenant-scoped data access (auth_context.tenant_id)
      ├─ Scope check for machine callers (has_scope())
      └─ Operation-level authorization
```

---

## 6. Security Testing Requirements

| Test Category | Count | Coverage |
|---------------|-------|----------|
| Provider seam tests | 70 (current) | Factory, interface, readiness, startup gate |
| Public path policy tests | 7 (current) | Dual-source consistency, RBAC loader |
| Route scaffold tests | 14 (current) | Registration, 501 responses, schema validation |
| Gateway integration tests | 3 (current) | Provider routing, error mapping, issuer rejection |

**Required additions for Wave A:**
- Credential stuffing rate limit tests
- CSRF validation tests
- Cookie security attribute tests
- Cross-tenant isolation tests
- Session revocation propagation tests
