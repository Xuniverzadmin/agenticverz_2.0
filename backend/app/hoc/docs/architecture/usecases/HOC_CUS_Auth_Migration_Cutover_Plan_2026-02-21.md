# HOC_CUS_Auth_Migration_Cutover_Plan_2026-02-21

**Created:** 2026-02-21
**Task:** T4 — Migration
**Status:** DONE

---

## 1. Objective

Define Clerk sunset, phased cutover, rollback strategy, and runtime proof points. Ensure machine-auth continuity at each phase.

---

## 2. Current State (Pre-Migration)

| Component | State | Dependency on Clerk |
|-----------|-------|---------------------|
| Frontend (`ClerkProvider`) | ACTIVE | Hard — all auth flows |
| Frontend route guards | ACTIVE | Hard — `useAuth()`, `useUser()` from Clerk |
| Frontend API client | ACTIVE | Hard — `ClerkAuthSync` attaches Bearer token |
| Backend gateway | ACTIVE | Soft — Clove is canonical, Clerk issuer rejected |
| Backend readiness gate | ACTIVE | None — checks Clove config only |
| Machine auth (X-AOS-Key) | ACTIVE | None — independent path |
| SDK auth | ACTIVE | None — uses X-AOS-Key |

---

## 3. Phased Cutover Plan

### Phase 1: Backend Identity Endpoints (Wave A)

**Goal:** Implement all 8 scaffold endpoints at `/hoc/api/auth/*`.

| Endpoint | Implementation | DB Table |
|----------|---------------|----------|
| `POST /register` | Argon2id hash, create user + session | `users`, `user_sessions` |
| `POST /login` | Verify password, issue JWT + refresh cookie | `users`, `user_sessions` |
| `POST /refresh` | Validate cookie, rotate refresh, issue new JWT | `user_sessions` |
| `POST /switch-tenant` | Verify membership, new session with target tid | `user_tenant_memberships` |
| `POST /logout` | Revoke session (DB + Redis) | `user_sessions` |
| `GET /me` | Read from auth context | — |
| `POST /password/reset/request` | Generate reset token, send email | `password_reset_tokens` |
| `POST /password/reset/confirm` | Verify token, hash new password, revoke sessions | `users`, `user_sessions` |

**Machine-auth continuity check:** X-AOS-Key path is UNCHANGED. Gateway mutual exclusivity remains. No SDK changes.

**Proof points:**
- All 8 endpoints return real responses (not 501)
- JWT tokens issued with EdDSA signature
- Refresh cookie set with `__Host-` prefix + HttpOnly + Secure + SameSite=Strict
- Session revocation propagates to Redis within 1 second
- All existing auth tests pass (70+ tests)

**Rollback:** Revert endpoint implementations to 501 scaffold. No DB migration rollback needed (tables can coexist).

### Phase 2: Frontend Adapter Wiring

**Goal:** Replace Clerk with Clove adapter in frontend.

| Step | Change | Rollback |
|------|--------|----------|
| 2a | Wire `CloveAuthAdapter` to call `/hoc/api/auth/login|refresh|logout` | Revert adapter to scaffold |
| 2b | Switch `App.tsx` from `ClerkProvider` to `HocAuthProvider` | Revert to `ClerkProvider` |
| 2c | Replace `ClerkAuthSync` with `AuthTokenSync` using Clove adapter | Revert to `ClerkAuthSync` |
| 2d | Update route guards to use `useHocAuth()` instead of Clerk hooks | Revert to Clerk hooks |

**Machine-auth continuity check:** SDK and API key auth are completely independent of frontend changes. No impact.

**Proof points:**
- Login → logout → login cycle works in browser
- Token refresh happens silently before access token expiry
- Tenant switch updates JWT `tid` claim
- Route guards enforce auth via Clove adapter
- All existing E2E tests pass

**Rollback:** Feature flag `AUTH_ADAPTER=clerk|clove` in frontend config. Default to `clerk` until Phase 2 is validated.

### Phase 3: Legacy Route Migration

**Goal:** Migrate 69 frontend `/api/v1/` call-sites to `/hoc/api/`.

| Category | Call-Sites | Target |
|----------|-----------|--------|
| Auth | 6 | `/hoc/api/auth/*` (Phase 1 endpoints) |
| Activity | ~10 | `/hoc/api/cus/activity/*` (already implemented) |
| Incidents | ~8 | `/hoc/api/cus/incidents/*` (already implemented) |
| Analytics | ~10 | `/hoc/api/cus/analytics/*` (already implemented) |
| Founder | ~15 | `/hoc/api/fdr/*` (already implemented) |
| Other | ~20 | Various HOC endpoints |

**Machine-auth continuity check:** SDK clients use `/api/v1/` paths. Must maintain backward compatibility or migrate SDK simultaneously.

**Proof points:**
- Zero `/api/v1/` call-sites remain in frontend
- All HOC endpoints return equivalent data
- SDK backward compatibility maintained (or SDK migrated)

**Rollback:** Keep legacy routes mounted alongside HOC routes until migration complete. Tombstone legacy routes after validation.

### Phase 4: Clerk Removal

**Goal:** Remove Clerk SDK dependency from frontend and backend.

| Step | Change |
|------|--------|
| 4a | Remove `@clerk/clerk-react` from `package.json` |
| 4b | Remove `CLERK_PUBLISHABLE_KEY` env var |
| 4c | Remove `ClerkAuthAdapter.ts` |
| 4d | Remove Clerk references from backend (`AUTH_PROVIDER=clerk` deprecation warnings) |
| 4e | Remove `AuthProviderType.CLERK` and `AuthSource.CLERK` (breaking change) |
| 4f | Update `RBAC_RULES.yaml` to remove any Clerk-specific rules |

**Machine-auth continuity check:** Final verification that all SDK and API key paths work without any Clerk dependency.

**Proof points:**
- `grep -r "clerk\|Clerk" website/ backend/` returns 0 results
- All tests pass without Clerk SDK installed
- Production login/logout/refresh cycle works

**Rollback:** Re-add Clerk SDK. This is the point of no return — Phase 4 should only execute after Phase 3 is validated for at least 2 weeks.

---

## 4. Machine-Auth Continuity Matrix

| Phase | X-AOS-Key Path | SDK Auth | Founder Auth | Impact |
|-------|---------------|----------|--------------|--------|
| Phase 1 | UNCHANGED | UNCHANGED | UNCHANGED | NONE |
| Phase 2 | UNCHANGED | UNCHANGED | UNCHANGED | NONE |
| Phase 3 | UNCHANGED | NEEDS MIGRATION if using `/api/v1/` | UNCHANGED | LOW |
| Phase 4 | UNCHANGED | UNCHANGED (post Phase 3 migration) | UNCHANGED | NONE |

---

## 5. Runtime Proof Points

### 5.1 Per-Phase Gate Checks

```bash
# Phase 1 gate
curl -s -X POST https://stagetest.agenticverz.com/hoc/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"..."}' | jq .access_token
# Expected: JWT string (not 501 error)

# Phase 2 gate
# Browser test: Login → navigate to /cus/* → logout → verify redirect
# Check: No Clerk network requests in DevTools

# Phase 3 gate
grep -r "'/api/v1/" website/app-shell/src/ | wc -l
# Expected: 0

# Phase 4 gate
grep -ri "clerk" website/ backend/app/ | grep -v "node_modules\|\.pyc\|__pycache__" | wc -l
# Expected: 0
```

### 5.2 Machine Auth Continuity Checks (Run at EVERY Phase)

```bash
# SDK auth check
curl -s -H "X-AOS-Key: $AOS_API_KEY" https://stagetest.agenticverz.com/health | jq .status
# Expected: "ok"

# API key validation check
curl -s -H "X-AOS-Key: $AOS_API_KEY" https://stagetest.agenticverz.com/api/v1/runs | jq .
# Expected: 200 with runs data

# Mutual exclusivity check
curl -s -H "Authorization: Bearer fake" -H "X-AOS-Key: $AOS_API_KEY" \
  https://stagetest.agenticverz.com/health
# Expected: 400 MIXED_AUTH error
```

---

## 6. Timeline

| Phase | Duration | Start Condition |
|-------|----------|-----------------|
| Phase 1 | 2-3 weeks | Wave A GO decision |
| Phase 2 | 1-2 weeks | Phase 1 all endpoints non-501 |
| Phase 3 | 2-3 weeks | Phase 2 validated on stagetest |
| Phase 4 | 1 week | Phase 3 validated for 2+ weeks |
| **Total** | **6-9 weeks** | — |
