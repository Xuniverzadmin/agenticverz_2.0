# Auth Semantic Contract (Phase 3.1)

**Status:** APPROVED
**Created:** 2025-12-30
**Phase:** 3.1 — Auth Semantics (L3 ↔ L4)
**Reference:** PIN-251, PHASE3_SEMANTIC_CHARTER.md

---

## Purpose

This contract defines **what the auth system means** — the semantic boundaries between verification, policy, decision, and enforcement.

**Core Question:**
> What is verification vs policy vs decision vs enforcement?
> Where do these semantic responsibilities live?
> Who is allowed to decide vs enforce?

---

## The Four Semantic Axes of Auth

### Axis 1: Verification (WHO)

**Definition:** Verification is the act of proving identity. It answers: **"Who are you?"**

**Semantic Invariants:**
- Verification MUST be stateless (no DB writes)
- Verification MUST NOT make policy decisions
- Verification MUST return identity claims OR reject
- Verification MUST NOT log business events (only security events)

**Verification Files (L3 + L6):**

| File | Layer | Verification Type | Claims Produced |
|------|-------|-------------------|-----------------|
| `auth.py` | L6 | API Key (env-based) | None (simple gate) |
| `jwt_auth.py` | L6 | JWT/JWKS | TokenPayload |
| `tenant_auth.py` | L6 | API Key (DB-based) | TenantContext |
| `console_auth.py` | L6 | Console JWT | CustomerToken / FounderToken |
| `clerk_provider.py` | L3 | Clerk JWT + API | ClerkUser |
| `oidc_provider.py` | L3 | Keycloak JWKS | Dict[str, Any] (raw claims) |
| `oauth_providers.py` | L3 | OAuth2 Flow | OAuthUserInfo |

**Semantic Boundary:**
> Verification files produce **identity claims**. They do NOT evaluate policy.
> A verification failure is a **401 Unauthorized** (identity unknown).

---

### Axis 2: Policy (WHAT)

**Definition:** Policy is the declaration of rules. It answers: **"What is allowed?"**

**Semantic Invariants:**
- Policy MUST be declarative (data, not behavior)
- Policy MUST NOT execute decisions
- Policy MUST be hot-reloadable without code deploy
- Policy definitions MUST be auditable

**Policy Files (L4):**

| File | Layer | Policy Type | Policy Structure |
|------|-------|-------------|------------------|
| `rbac.py` | L4 | Approval Levels | ApprovalLevel enum (1-5) |
| `rbac_engine.py` | L4 | Policy Rules | JSON-based PolicyObject |
| `tier_gating.py` | L4 | Feature Tiers | FEATURE_TIER_MAP dict |
| `rbac_middleware.py` | L6 | RBAC Matrix | RBAC_MATRIX dict |

**Policy Hierarchy (AUTHORITATIVE):**

```
Tier Gating (Feature Access)
    ↓ (Tier passes → check RBAC)
RBAC Matrix (Role + Resource + Action)
    ↓ (RBAC passes → check Approval)
Approval Levels (Action-specific thresholds)
```

**Semantic Boundary:**
> Policy files define **what is allowed**. They do NOT check identity or enforce.
> A policy violation is a **403 Forbidden** (you are known, but not allowed).

---

### Axis 3: Decision (SHOULD)

**Definition:** Decision is the evaluation of rules against claims. It answers: **"Should this be allowed?"**

**Semantic Invariants:**
- Decision MUST be pure (no side effects)
- Decision MUST return allow/deny with reason
- Decision MUST be auditable (shadow audit)
- Decision MUST NOT modify request or state

**Decision Files (L4):**

| File | Layer | Decision Function | Returns |
|------|-------|-------------------|---------|
| `rbac_engine.py` | L4 | `RBACEngine.evaluate()` | PolicyDecision |
| `role_mapping.py` | L4 | `map_console_role_to_rbac()` | RBACRole |
| `tier_gating.py` | L4 | `check_tier_access()` | TierAccessResult |
| `shadow_audit.py` | L4 | `shadow_audit.log_decision()` | None (logging only) |

**Single Decision Authority (MANDATORY):**

> **`rbac_engine.py` is the sole Decision Authority.**
> Tier gating and role mapping are **inputs**; they never return final allow/deny.
> All final allow/deny decisions flow through `RBACEngine.evaluate()`.

| Component | Role | Final Authority? |
|-----------|------|------------------|
| `role_mapping.py` | Maps console roles → RBAC roles | NO (input) |
| `tier_gating.py` | Checks feature tier eligibility | NO (input) |
| `rbac.py` | Defines approval levels | NO (data) |
| **`rbac_engine.py`** | **Evaluates all inputs → PolicyDecision** | **YES (sole authority)** |

**Decision Flow:**

```
1. Identity claims arrive (from Verification)
2. Role mapping: Console role → RBAC role (INPUT)
3. Tier check: TenantTier >= required tier? (INPUT)
4. RBAC check: Role has permission for resource + action? (INPUT)
5. Approval check: Level >= required level? (INPUT)
6. rbac_engine.py: Combine all inputs → PolicyDecision (FINAL)
```

**Semantic Boundary:**
> Decision files evaluate **should this be allowed**. They do NOT block or modify.
> Decision is pure computation. Enforcement is separate.
> Only `rbac_engine.py` may return a final allow/deny decision.

---

### Axis 4: Enforcement (DO)

**Definition:** Enforcement is acting on a decision. It answers: **"Block or allow?"**

**Semantic Invariants:**
- Enforcement MUST be at request boundary (middleware)
- Enforcement MUST consume a Decision, not compute it
- Enforcement MUST be configurable (shadow vs hard)
- Enforcement MUST NOT modify decision logic

**Enforcement Files (L6):**

| File | Layer | Enforcement Type | Behavior |
|------|-------|------------------|----------|
| `rbac_middleware.py` | L6 | RBAC Middleware | HTTP 403 on deny |
| `console_auth.py` | L6 | Console Middleware | HTTP 401/403 |
| `tenant_auth.py` | L6 | Tenant Dependency | HTTP 401/403 |
| `tier_gating.py` | L4 | `requires_tier()` | HTTP 403 |

**Enforcement Modes:**

| Mode | Env Vars | Behavior |
|------|----------|----------|
| **Shadow** | `RBAC_SHADOW_AUDIT=true`, `RBAC_ENFORCE=false` | Log only, never block |
| **Soft** | `RBAC_SHADOW_AUDIT=true`, `RBAC_ENFORCE=true` | Log + block |
| **Hard** | `RBAC_SHADOW_AUDIT=false`, `RBAC_ENFORCE=true` | Block only (no log) |
| **Off** | `RBAC_SHADOW_AUDIT=false`, `RBAC_ENFORCE=false` | Neither |

**Semantic Boundary:**
> Enforcement files act on **decisions already made**. They do NOT compute policy.
> Enforcement is the HTTP-level gate.

---

## Semantic Ambiguities Resolved

### Ambiguity 1: Role Hierarchy Conflict

**Problem:** Multiple role hierarchies exist:
- `role_mapping.py`: founder(100) > operator(50) > admin(40) > ...
- `rbac.py`: ApprovalLevel 1-5
- `clerk_provider.py`: owner(5) > admin(5) > manager(4) > ...

**Resolution:**

| Hierarchy | Purpose | Scope |
|-----------|---------|-------|
| `role_mapping.py` | Request-level role precedence | Which role "wins" when multiple assigned |
| `rbac.py` ApprovalLevel | Action-specific approval gates | High-risk actions (budget changes, policy edits) |
| `clerk_provider.py` | Clerk-specific mapping | Translates Clerk metadata to AOS roles |

**Semantic Contract:**
> `role_mapping.py` is **authoritative** for role precedence.
> ApprovalLevel is a **secondary gate** for sensitive operations.
> Clerk/OIDC hierarchies are **input mappings** only.

---

### Ambiguity 2: Tier vs RBAC Overlap

**Problem:** Two gating systems:
- `tier_gating.py`: Feature gating by subscription tier
- `rbac_middleware.py`: Permission gating by role

**Resolution:**

```
Request arrives
    ↓
[1] Tier Gate: Does tenant tier allow this feature?
    ├─ NO → 403 "Upgrade required"
    └─ YES ↓
[2] RBAC Gate: Does user role allow this action?
    ├─ NO → 403 "Permission denied"
    └─ YES → Proceed
```

**Semantic Contract:**
> Tier gates **features** (product-level).
> RBAC gates **actions** (user-level).
> Tier is checked FIRST. If tier fails, RBAC is never evaluated.

---

### Ambiguity 3: Founder Isolation Scope

**Problem:** Founder isolation is defined in multiple places.

**Resolution:**

| Component | Isolation Mechanism |
|-----------|---------------------|
| `role_mapping.py` | `guard_founder_isolation()` — requires tenant_id=None |
| `console_auth.py` | Separate cookies (aos_console_session vs aos_fops_session) |
| `rbac_middleware.py` | Founder roles excluded from RBAC_MATRIX |
| `tier_gating.py` | N/A — founders don't have tiers |

**Semantic Contract:**
> Founder isolation is **complete** when ALL of:
> 1. Token has audience = "fops" (not "console")
> 2. tenant_id = None (not any tenant)
> 3. Role is founder or operator (not admin/dev/etc)
> Violation of ANY of these is a **security incident**.

---

### Ambiguity 4: Shadow vs Enforcement Mode

**Problem:** What's the relationship between shadow audit and enforcement?

**Resolution:**

| RBAC_SHADOW_AUDIT | RBAC_ENFORCE | Behavior |
|-------------------|--------------|----------|
| true | false | **Learning Mode**: Log decisions, never block |
| true | true | **Production Mode**: Log + enforce |
| false | true | **Quiet Mode**: Enforce without logging |
| false | false | **Off**: No auth checks |

**Semantic Contract:**
> Shadow audit is **orthogonal** to enforcement.
> Shadow audit is for learning. Enforcement is for protecting.
> Both can be enabled simultaneously.

---

### Ambiguity 5: Multiple Verification Paths

**Problem:** Multiple verification mechanisms exist.

**Resolution — Verification Priority Order:**

```
1. X-AOS-Key header (tenant_auth.py — DB lookup)
2. Authorization: Bearer (jwt_auth.py — JWT)
3. Cookie: aos_console_session (console_auth.py — Customer Console)
4. Cookie: aos_fops_session (console_auth.py — Founder Ops Console)
5. AOS_API_KEY env fallback (auth.py — legacy, deprecated)
```

**Verification Context Constraints (MANDATORY):**

| Verification Method | Allowed Contexts | Forbidden Contexts | Notes |
|---------------------|------------------|-------------------|-------|
| DB API Key (`tenant_auth.py`) | API, Worker | Console | Requires tenant binding |
| JWT (`jwt_auth.py`) | API | Worker (unless explicit), Console | Short-lived tokens |
| Console Cookie (`console_auth.py`) | Console only | API, Worker | UI scope only |
| Founder Cookie (`console_auth.py`) | Founder Console only | API, Worker, Customer Console | MFA required |
| Env Fallback (`auth.py`) | **Local dev only** | **ALL production** | Must be compile-time guarded |

**Production Safety Rule:**
> **Env-based API key fallback (auth.py) is FORBIDDEN in production.**
> This MUST be guarded by `AOS_USE_LEGACY_AUTH=true` AND `ENV != production`.
> Violation of this is a **security incident**.

**Semantic Contract:**
> First successful verification wins **within allowed context**.
> Verification outside allowed context MUST fail, not fall through.
> Console cookies are **console-specific** paths — never valid for API/Worker.

---

### Ambiguity 6: Context Object Proliferation

**Problem:** Multiple context types exist.

**Resolution — Canonical Context:**

| Context | Purpose | Canonical? |
|---------|---------|------------|
| `TenantContext` | API key auth | YES (API paths) |
| `AuthContext` | RBAC evaluation | YES (RBAC paths) |
| `TokenPayload` | JWT claims | NO (intermediate) |
| `ClerkUser` | Clerk-specific | NO (provider-specific) |
| `CustomerToken` | Console claims | YES (Console paths) |
| `FounderToken` | Founder claims | YES (Founder paths) |

**Semantic Contract:**
> `TenantContext` is canonical for **API key auth**.
> `AuthContext` is canonical for **RBAC decisions**.
> `CustomerToken` / `FounderToken` are canonical for **console auth**.
> All others are intermediate or provider-specific.

---

## Layer Assignment (Authoritative)

| File | Semantic Role | Layer | Justification |
|------|---------------|-------|---------------|
| `auth.py` | Verification | L6 | Platform-level key check |
| `auth/__init__.py` | Module exports | N/A | No semantic role |
| `clerk_provider.py` | Verification | L3 | External provider adapter |
| `console_auth.py` | Verification + Enforcement | L6 | Platform-level console auth |
| `jwt_auth.py` | Verification | L6 | Platform-level JWT parsing |
| `oauth_providers.py` | Verification | L3 | External OAuth adapter |
| `oidc_provider.py` | Verification | L3 | External OIDC adapter |
| `rbac.py` | Policy + Decision | L4 | Domain-level approval logic |
| `rbac_engine.py` | Policy + Decision | L4 | Domain-level policy engine |
| `rbac_middleware.py` | Enforcement | L6 | Platform-level request gate |
| `role_mapping.py` | Decision | L4 | Domain-level role mapping |
| `shadow_audit.py` | Decision (audit) | L4 | Domain-level audit logging |
| `tenant_auth.py` | Verification + Enforcement | L6 | Platform-level tenant auth |
| `tier_gating.py` | Policy + Decision + Enforcement | L4 | Feature tier gating |

---

## Forbidden Cross-Boundary Violations

| Violation | Example | Why Forbidden |
|-----------|---------|---------------|
| Verification doing policy | `auth.py` checking roles | Conflates identity with permission |
| Policy doing enforcement | `rbac_engine.py` raising HTTPException | Policy is data, not action |
| Decision modifying state | `role_mapping.py` writing to DB | Decision must be pure |
| Enforcement computing policy | `rbac_middleware.py` defining new roles | Enforcement consumes, not creates |

---

## Completion Criteria

Phase 3.1 Auth Semantics is **COMPLETE** when:

1. All 14 auth files have semantic roles assigned
2. All ambiguities documented and resolved
3. Layer assignments are authoritative (no conflicts)
4. Forbidden violations are documented
5. Human review approves this contract

---

## Tightenings Applied (Phase 3.1 Review)

1. **Verification Context Constraints** — Each verification method explicitly constrained to allowed/forbidden contexts. Env fallback explicitly forbidden in production.
2. **Single Decision Authority** — `rbac_engine.py` declared as sole final authority. Tier gating and role mapping are inputs only.

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-30 | Contract drafted | Discovery phase complete |
| 2025-12-30 | 6 ambiguities resolved | Clear semantic boundaries |
| 2025-12-30 | Layer assignments finalized | Based on semantic role |
| 2025-12-30 | Tightening 1 applied | Verification context constraints table added |
| 2025-12-30 | Tightening 2 applied | Single Decision Authority declared (rbac_engine.py) |
| 2025-12-30 | Contract resubmitted | Awaiting final approval |

---

## Review Required

**Status:** REVISED — Tightenings applied, awaiting final approval

**Tightenings Applied:**
1. Verification Context Constraints table (Ambiguity 5)
2. Single Decision Authority declaration (Axis 3)

**To Approve:** Say "Auth Semantic Contract approved — proceed to Phase 3.2"

**To Revise:** Say "Auth Semantics needs revision — [specify concerns]"
