# HOC_CUS_FirstParty_Auth_Architecture_2026-02-21

**Created:** 2026-02-21
**Task:** T2 — Auth Design
**Status:** DONE

---

## 1. Objective

Define the first-party auth architecture spec and API contract for canonical `hoc/*` endpoints. Select auth model with rationale against alternatives.

---

## 2. Selected Auth Model

### 2.1 Decision: EdDSA JWT + HttpOnly Cookie Refresh

**Model:** Stateless access tokens (EdDSA-signed JWT, short-lived) with stateful refresh tokens (HttpOnly cookie, DB-backed session).

**Rationale against alternatives:**

| Alternative | Rejected Because |
|-------------|-----------------|
| Session-only (server-side) | Doesn't scale horizontally without sticky sessions; adds DB lookup per request |
| OAuth2 + OIDC (external IDP) | Adds external dependency; Clerk removal is the goal, not IDP replacement |
| Opaque tokens only | Requires DB lookup per request; high latency at scale |
| RSA JWT | EdDSA (Ed25519) is faster signing/verification, smaller keys (32 bytes vs 2048+ bits) |
| Symmetric JWT (HMAC) | Cannot separate signing (server) from verification (edge/CDN); secret distribution risk |

### 2.2 Architecture Summary

```
Client → POST /hoc/api/auth/login → Server
  ← 200 { access_token (JWT, 15min) }
  ← Set-Cookie: __Host-refresh=<token>; HttpOnly; Secure; SameSite=Strict; Path=/hoc/api/auth

Client → GET /hoc/api/cus/* (Authorization: Bearer <access_token>)
  → AuthGatewayMiddleware → CloveHumanAuthProvider.verify_bearer_token()
  → HumanAuthContext injected into request.state

Client → POST /hoc/api/auth/refresh (cookie auto-sent)
  → Validate refresh token + session not revoked
  ← 200 { access_token (new JWT) }
  ← Set-Cookie: __Host-refresh=<rotated_token>
```

---

## 3. Token Specifications

### 3.1 Access Token (JWT)

| Property | Value |
|----------|-------|
| Algorithm | EdDSA (Ed25519) |
| Lifetime | 15 minutes |
| Storage | In-memory (frontend), never persisted to localStorage |
| Signing key | Private key (server-only) |
| Verification key | Public key via JWKS endpoint |
| JWKS endpoint | `/.well-known/jwks.json` (static or URL-based) |

**Mandatory claims** (from `auth_constants.py`):

| Claim | Type | Description |
|-------|------|-------------|
| `iss` | string | `https://auth.agenticverz.com` |
| `aud` | string | `clove` |
| `sub` | string | User ID |
| `tid` | string | Active tenant ID |
| `sid` | string | Session ID (revocation key) |
| `tier` | string | Tenant tier (free/pro/enterprise) |
| `iat` | number | Issued at (Unix epoch) |
| `exp` | number | Expires at (Unix epoch) |
| `jti` | string | JWT ID (replay protection) |

### 3.2 Refresh Token

| Property | Value |
|----------|-------|
| Format | Opaque random (32 bytes, base64url) |
| Lifetime | 7 days (configurable) |
| Storage | HttpOnly Secure cookie (`__Host-refresh`) |
| DB backing | `user_sessions` table (session_id, refresh_hash, revoked_at) |
| Rotation | On every refresh — old token invalidated |
| CSRF | Double-submit cookie pattern (csrf_token in cookie + header) |

---

## 4. API Contract

### 4.1 Identity Endpoints (already scaffolded at `/hoc/api/auth`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | PUBLIC | Create user account |
| POST | `/login` | PUBLIC | Authenticate, return tokens |
| POST | `/refresh` | COOKIE | Rotate refresh, issue new access token |
| POST | `/switch-tenant` | SESSION | Switch active tenant, re-issue tokens |
| POST | `/logout` | SESSION | Revoke session, clear cookie |
| GET | `/me` | SESSION | Current authenticated principal |
| GET | `/provider/status` | PUBLIC | Auth provider diagnostics |
| POST | `/password/reset/request` | PUBLIC | Request password reset email |
| POST | `/password/reset/confirm` | PUBLIC | Confirm reset with token |

### 4.2 Password Hashing

| Property | Value |
|----------|-------|
| Algorithm | Argon2id |
| Memory cost | 64 MB |
| Time cost | 3 iterations |
| Parallelism | 1 |
| Salt | 16 bytes random |
| Output | 32 bytes |

---

## 5. Session Model

### 5.1 Session Lifecycle

```
Login → Create session row (DB) → Issue access + refresh tokens
  → ...requests use access token...
  → Refresh → Rotate refresh token, extend session
  → ...
  → Logout → Revoke session (set revoked_at) → Clear cookie
```

### 5.2 Session Revocation

| Check Point | Mechanism |
|-------------|-----------|
| Gateway (every request) | Redis set lookup: `revoked_sessions:{session_id}` |
| Refresh endpoint | DB lookup: `user_sessions.revoked_at IS NOT NULL` |
| Logout | Write to DB + publish to Redis |
| Password change | Revoke ALL sessions for user |

### 5.3 Required Tables

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `users` | id, email, password_hash, created_at | User identity |
| `user_sessions` | id, user_id, tenant_id, refresh_hash, created_at, revoked_at, last_used_at | Session tracking |
| `user_tenant_memberships` | user_id, tenant_id, roles, joined_at | Multi-tenant membership |

---

## 6. Tenant-Bound Auth Context

### 6.1 Invariants

1. Every access token contains exactly ONE `tid` (tenant ID)
2. `switch-tenant` creates a new session with the target tenant
3. `HumanAuthContext.tenant_id` is the authoritative tenant scope for all downstream operations
4. No cross-tenant data access without explicit `switch-tenant` call

### 6.2 Multi-Tenant Flow

```
User authenticates → default tenant selected (first membership or last-used)
  → Access token contains tid=<default_tenant>
  → POST /switch-tenant { tenant_id: "other_tenant" }
  → Verify membership in target tenant
  → New session with tid=<other_tenant>
  → New access + refresh tokens issued
```

---

## 7. Machine Auth Continuity

Machine auth (X-AOS-Key) is **unchanged** by this architecture. The gateway's mutual exclusivity invariant remains:

- Human requests: `Authorization: Bearer <JWT>` → `HumanAuthContext`
- Machine requests: `X-AOS-Key: <api_key>` → `MachineCapabilityContext`
- Both present: `MIXED_AUTH` error (hard fail)

No changes to `api_key_service`, `MachineCapabilityContext`, or SDK authentication patterns.

---

## 8. Frontend Integration Path

### 8.1 Migration Sequence

1. Implement backend `/hoc/api/auth/login|refresh|logout|me` endpoints
2. Wire `CloveAuthAdapter` to call these endpoints (scaffold exists)
3. Switch `App.tsx` from `ClerkProvider` to `HocAuthProvider` with Clove adapter
4. Replace `ClerkAuthSync` with `AuthTokenSync` (scaffold exists)
5. Migrate 69 frontend `/api/v1/` call-sites to `/hoc/api/`
6. Remove Clerk SDK dependency

### 8.2 Token Attachment (Frontend)

`AuthTokenSync.ts:37-57` — axios interceptor attaches `Authorization: Bearer {token}` via adapter's `getAccessToken()`. This scaffold is ready; only needs the adapter to return real tokens.

---

## 9. JWKS Key Management

| Concern | Approach |
|---------|----------|
| Key generation | Ed25519 keypair generated offline, stored as env vars or secrets |
| Key rotation | Add new key to JWKS with new `kid`; old key remains for token lifetime |
| JWKS distribution | Static file (`CLOVE_JWKS_FILE`) or URL (`CLOVE_JWKS_URL`) with TTL cache |
| Key storage | Private key: env var or vault; Public key: JWKS endpoint |
