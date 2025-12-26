# PIN-169: M7-M28 RBAC Integration Plan

**Status:** SHADOW AUDIT ACTIVE - OBSERVING (24-48h until Phase 4)
**Category:** Architecture / Auth / Security
**Created:** 2025-12-25
**Milestone:** P2FC Item 5 (Deferred from PIN-161)
**Parent:** PIN-161 (P2FC - Partial to Full Consume)
**Related:** PIN-032 (M7 RBAC Enablement), PIN-147 (M28 Route Migration)

---

## Implementation Status (2025-12-25)

| Phase | Status | Evidence |
|-------|--------|----------|
| Phase 1: Role Mapping | ✅ COMPLETE | `role_mapping.py` - 45 tests |
| Phase 2: Resource Expansion | ✅ COMPLETE | 7 roles × 18 resources |
| Phase 2.5: Principal Model | ✅ COMPLETE | `Principal`, `AuthContext` dataclasses |
| Phase 3: Founder Isolation | ✅ COMPLETE | `guard_founder_isolation()` |
| Phase 3: Shadow Audit | ✅ COMPLETE | `shadow_audit.py` with rollout gates |
| Phase 3: Middleware Wiring | ✅ COMPLETE | Shadow audit wired into `dispatch()` |
| Phase 4: Enforcement | ⏳ PENDING | Requires 48h shadow audit data |

**Total Tests:** 202 passing

### Shadow Audit Status: VERIFIED WORKING (2025-12-25 15:36 UTC)

**Confirmed logging:**
```
shadow_audit_allowed                 # Allowed decisions
shadow_audit_would_block             # Would-be-blocked decisions
SHADOW_AUDIT [WOULD_BLOCK] GET /api/v1/memory/pins/key2 - resource=memory_pin action=read roles=[] reason=no-credentials
```

**Observation Period:** 2025-12-25 15:36 UTC → 2025-12-27 15:36 UTC (48h)

---

### Operational Commands (Use During Observation)

**Daily monitoring:**
```bash
# Count decisions
docker logs nova_agent_manager --since 24h 2>&1 | grep "shadow_audit_allowed" | wc -l
docker logs nova_agent_manager --since 24h 2>&1 | grep "shadow_audit_would_block" | wc -l

# See WHO would be blocked and WHY
docker logs nova_agent_manager --since 24h 2>&1 | grep "WOULD_BLOCK"
```

**Check rollout gates (after 24h):**
```bash
docker exec nova_agent_manager python -c "
from app.auth.shadow_audit import shadow_aggregator
import json
result = shadow_aggregator.check_rollout_gates()
print(json.dumps(result, indent=2))
if result['ready_for_enforcement']:
    print('READY TO ENFORCE')
else:
    print('NOT READY - check gate_details')
"
```

**DO NOT during observation:**
- Loosen RBAC matrix
- Add bypass paths
- Suppress logs
- Lower thresholds

**FIX if you see would-block entries:**
| Problem | Fix |
|---------|-----|
| `no-credentials` | Add auth header to caller |
| `role mismatch` | Grant correct role to caller |
| `machine denied` | Use correct endpoint or role |

---

### Shadow Audit Wiring (Completed 2025-12-25)

The RBAC middleware `dispatch()` method now records **all** decisions to shadow audit:

```python
# In rbac_middleware.py dispatch()
shadow_audit.log_decision(...)      # Persistent logging
shadow_aggregator.record_decision(...)  # In-memory stats for fast queries
record_shadow_audit_metric(...)     # Prometheus metrics
```

**Shadow Aggregator Capabilities:**
- `check_rollout_gates()` - Returns dict with gate status and pass/fail
- `get_who_would_be_blocked(limit=20)` - Answers "who would be blocked" in <10s
- `get_stats()` - Real-time decision counts by action and resource

### Rollout Gates (must pass before Phase 4)

| Gate | Threshold | Query |
|------|-----------|-------|
| `read_would_block_rate` | < 0.1% | Low-risk: reads rarely denied |
| `write_would_block_rate` | < 0.01% | High-risk: writes need precision |
| `founder_tenant_violations` | = 0 | Zero tolerance for founder leakage |
| `min_observation_hours` | >= 24 | Minimum data collection period |

**Run gates check:**
```python
from app.auth.shadow_audit import shadow_aggregator
result = shadow_aggregator.check_rollout_gates()
# Returns: {"gates_passed": True/False, "gate_details": {...}, "ready_for_enforcement": bool}
```

### Key Files Modified/Created

| File | Purpose |
|------|---------|
| `backend/app/auth/role_mapping.py` | One-way mapping + AuthContext |
| `backend/app/auth/shadow_audit.py` | Audit logging + rollout gates + aggregator |
| `backend/app/auth/rbac_middleware.py` | Dispatch wiring + machine lockdown |
| `backend/tests/auth/test_role_mapping.py` | 45 tests |
| `backend/tests/auth/test_rbac_path_mapping.py` | 95 tests (incl. future-proof guard) |
| `backend/tests/auth/test_rbac_middleware.py` | 62 tests (machine lockdown verified)

---

## Summary

Assessment of M7 RBAC and M28 Console Auth systems, identifying integration gaps and recommending a unification strategy to satisfy the P2FC invariant: "All permission checks must route through M7 RBAC layer."

---

## Current State Assessment

### M28: Console Auth (`console_auth.py`)

| Property | Value |
|----------|-------|
| Status | ENFORCING |
| Domains | 2 (Customer Console, Founder Ops) |
| Token Types | CustomerToken (aud=console), FounderToken (aud=fops) |
| Customer Roles | OWNER, ADMIN, DEV, VIEWER |
| Founder Roles | FOUNDER, OPERATOR |
| MFA Required | Yes (FOPS only) |

**Protected Endpoints (M28):**

| Router | Prefix | Auth Type | Roles |
|--------|--------|-----------|-------|
| guard.py | `/guard/*` | verify_console_token | CustomerRole.* |
| ops.py | `/ops/*` | verify_fops_token | FounderRole.* |
| cost_guard.py | `/guard/costs/*` | verify_console_token | CustomerRole.* |
| cost_ops.py | `/ops/cost/*` | verify_fops_token | FounderRole.* |
| founder_actions.py | `/ops/actions/*` | verify_fops_token | FounderRole.* |

---

### M7: RBAC Middleware (`rbac_middleware.py`)

| Property | Value |
|----------|-------|
| Status | ENABLED, ENFORCING |
| Resources | 4 (memory_pin, prometheus, costsim, policy) |
| Roles | 5 (infra, admin, machine, dev, readonly) |
| Auth Methods | X-Machine-Token, JWT Bearer, X-Roles |
| Metrics | Prometheus (rbac_decisions_total, rbac_latency_seconds) |

**RBAC Matrix:**

```
Resource     | infra        | admin        | machine     | dev    | readonly
-------------|--------------|--------------|-------------|--------|----------
memory_pin   | CRUD + admin | CRUD + admin | read, write | read   | read
prometheus   | reload,query | reload,query | reload      | query  | query
costsim      | RWA          | RWA          | read        | read   | read
policy       | RW + approve | RW + approve | read        | read   | read
```

**Protected Paths (M7):**

| Path Pattern | Resource | Actions |
|--------------|----------|---------|
| `/api/v1/memory/pins*` | memory_pin | read, write, delete, admin |
| `/-/reload`, `/api/observability/prom-reload` | prometheus | reload |
| `/api/v1/query`, `/api/prometheus` | prometheus | query |
| `/api/v1/costsim*` | costsim | read, write |
| `/api/v1/policy*` | policy | read, write, approve |

---

## Gap Analysis

### 1. Parallel Auth Systems (No Integration)

M28 and M7 operate as **completely separate** authorization systems with no integration:

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Request                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐        ┌─────────┐        ┌─────────┐
   │ M28     │        │ M7      │        │ None    │
   │ Console │        │ RBAC    │        │ (Gap)   │
   │ Auth    │        │ Middle  │        │         │
   └─────────┘        └─────────┘        └─────────┘
        │                  │                  │
   /guard/*           /api/v1/          Most other
   /ops/*             memory/pins       endpoints
                      /api/v1/costsim
                      /api/v1/policy
```

**Problem:** No role mapping between:
- CustomerRole (OWNER/ADMIN/DEV/VIEWER) → RBAC Roles (infra/admin/machine/dev/readonly)
- FounderRole (FOUNDER/OPERATOR) → RBAC Roles

---

### 2. Unprotected Endpoints (Critical Gap)

27 API files exist with routers, but protection covers only a small subset:

| API File | Prefix | Current Auth | Status |
|----------|--------|--------------|--------|
| agents.py | `/api/v1/agents` | X-AOS-Key only | **UNPROTECTED** |
| runtime.py | `/api/v1/runtime` | X-AOS-Key only | **UNPROTECTED** |
| recovery.py | `/api/v1/recovery` | X-AOS-Key only | **UNPROTECTED** |
| workers.py | `/api/v1/workers` | X-AOS-Key only | **UNPROTECTED** |
| traces.py | `/api/v1/traces` | JWT (partial) | **PARTIAL** |
| embedding.py | `/api/v1/embedding` | Unknown | **UNKNOWN** |
| policy_layer.py | `/api/v1/policy-layer` | Unknown | **UNKNOWN** |
| v1_killswitch.py | `/v1/*` | Unknown | **UNKNOWN** |
| v1_proxy.py | `/v1/*` | Unknown | **UNKNOWN** |
| integration.py | `/integration/*` | Unknown | **UNKNOWN** |
| cost_intelligence.py | `/cost/*` | Unknown | **UNKNOWN** |
| health.py | `/health` | None (public) | OK (intentional) |
| onboarding.py | `/api/v1/auth` | None (public) | OK (intentional) |
| memory_pins.py | `/api/v1/memory/pins` | M7 RBAC | **PROTECTED** |
| costsim.py | `/api/v1/costsim` | M7 RBAC | **PROTECTED** |
| policy.py | `/api/v1/policy` | M7 RBAC | **PROTECTED** |
| guard.py | `/guard/*` | M28 Console | **PROTECTED** |
| ops.py | `/ops/*` | M28 FOPS | **PROTECTED** |
| cost_guard.py | `/guard/costs/*` | M28 Console | **PROTECTED** |
| cost_ops.py | `/ops/cost/*` | M28 FOPS | **PROTECTED** |
| founder_actions.py | `/ops/actions/*` | M28 FOPS | **PROTECTED** |
| rbac_api.py | `/api/v1/rbac` | M7 RBAC | **PROTECTED** |

---

### 3. Role Fragmentation

Three separate role systems exist with no mapping:

| System | Roles | Used By |
|--------|-------|---------|
| M7 RBAC | infra, admin, machine, dev, readonly | rbac_middleware.py |
| M28 Customer | OWNER, ADMIN, DEV, VIEWER | console_auth.py |
| M28 Founder | FOUNDER, OPERATOR | console_auth.py |

**Missing:** Unified role hierarchy or mapping rules.

---

## Integration Recommendations (REVISED)

> **Reviewer Feedback Incorporated:** 2025-12-25
> This section has been hardened based on security architecture review.

---

### Core Principles (Non-Negotiable)

1. **M7 RBAC roles are CANONICAL** — M28 roles are presentation aliases only
2. **X-AOS-Key = identity, not authorization** — Keys identify *who*, RBAC decides *what*
3. **Founder paths NEVER flow through tenant RBAC** — Nuclear isolation required
4. **One-way mapping only** — Console roles → RBAC. Never bidirectional.
5. **No fallbacks in enforcement** — Fail closed, always

---

### Phase 1: Canonical Role Mapping (DO FIRST)

**Rule:** M7 RBAC is the source of truth. M28 roles are cosmetic labels.

```python
# role_mapping.py — ONE-WAY MAPPING ONLY

# M28 Customer roles → M7 RBAC roles (CANONICAL)
CUSTOMER_TO_RBAC: Dict[CustomerRole, str] = {
    CustomerRole.OWNER:  "admin",     # Full tenant control
    CustomerRole.ADMIN:  "infra",     # Ops + policy within tenant
    CustomerRole.DEV:    "dev",       # Build + runtime
    CustomerRole.VIEWER: "readonly",  # Read-only
}

# M28 Founder roles → M7 RBAC roles (ISOLATED PATH)
# NOTE: Founder auth terminates early — these never flow through tenant RBAC
FOUNDER_TO_RBAC: Dict[FounderRole, str] = {
    FounderRole.FOUNDER:  "founder",   # Global, non-tenant (new role)
    FounderRole.OPERATOR: "operator",  # Scoped ops (new role)
}

def map_console_to_rbac(token: CustomerToken) -> str:
    """
    Map console token to SINGLE canonical RBAC role.

    INVARIANT: This is one-way. Never invert this mapping.
    If M28 invents authority, the invariant is broken.
    """
    return CUSTOMER_TO_RBAC.get(token.role, "readonly")
```

**Phase 1 Deliverables:**

- [ ] Create `role_mapping.py` with strict one-way mapping
- [ ] Add `founder` and `operator` to M7 RBAC_MATRIX (isolated resources)
- [ ] **Shadow audit mode** — log every mapped decision WITHOUT enforcement
- [ ] Collect 48h of shadow logs before proceeding to Phase 2

---

### Phase 2: Expand RBAC Resources (14 minimum)

**Rule:** If it can mutate state or leak data, it needs a resource.

| Resource | Actions | Path Pattern | Notes |
|----------|---------|--------------|-------|
| `agent` | read, write, register, heartbeat, delete | `/api/v1/agents` | Multi-agent system |
| `runtime` | simulate, query, capabilities | `/api/v1/runtime` | Core execution |
| `recovery` | read, write, execute, suggest | `/api/v1/recovery` | M10 recovery engine |
| `worker` | read, run, stream, cancel | `/api/v1/workers` | Worker execution |
| `trace` | read, write, delete, export | `/api/v1/traces` | Execution history |
| `embedding` | read, embed, query | `/api/v1/embedding` | Vector operations |
| `killswitch` | read, activate, reset | `/v1/killswitch` | Emergency stop |
| `integration` | read, checkpoint, resolve | `/integration` | M25 loop |
| `cost` | read, simulate, forecast | `/cost` | Cost intelligence |
| `policy` | read, write, approve | `/api/v1/policy` | Already exists |
| `checkpoint` | read, write, restore | `/api/v1/checkpoints` | Workflow state |
| `memory` | read, write, delete, admin | `/api/v1/memory` | Already exists |
| `event` | read, subscribe, publish | `/api/v1/events` | Event streaming |
| `incident` | read, write, resolve | `/api/v1/incidents` | Incident tracking |
| `health` | read | `/health`, `/metrics` | Public (no auth) |

---

### Phase 2.5: X-AOS-Key Identity Reclassification (CRITICAL)

**Current problem:** X-AOS-Key is doing *authorization by presence*. Wrong.

**Correct model:**
- `X-AOS-Key` = "who is calling" (identity)
- `RBAC` = "what they're allowed to do" (authorization)

```python
# Every protected router MUST call RBAC even if key-authenticated

@dataclass
class Principal:
    """Unified identity model extracted from request."""
    principal_id: str         # Key ID, user ID, or machine ID
    principal_type: str       # "machine" | "integration" | "console" | "fops"
    tenant_id: Optional[str]  # None for founder paths
    effective_roles: List[str]  # RBAC roles (single or derived)

def extract_principal(request: Request) -> Principal:
    """
    Extract identity from request headers.

    X-AOS-Key → principal_type = "machine", principal_id = key_fingerprint
    Console JWT → principal_type = "console", principal_id = user_id
    FOPS JWT → principal_type = "fops", principal_id = founder_id
    """
    ...
```

**Invariant:** If a key bypasses RBAC, the P2FC invariant is already broken.

---

### Phase 3: Console-RBAC Bridge (Point of No Return)

**Rule:** RBAC decision called **per request**, not per session. No caching initially.

Token extraction MUST yield:

```python
@dataclass
class AuthContext:
    """Complete auth context for every request."""
    principal_id: str           # Who
    principal_type: str         # machine | console | fops
    tenant_id: Optional[str]    # Tenant scope (None for founders)
    effective_roles: List[str]  # M7 RBAC roles
    source_token_type: str      # "jwt" | "api_key" | "machine_token"

def build_auth_context(request: Request) -> AuthContext:
    """
    Build complete auth context from request.

    INVARIANT: Every request has exactly one AuthContext.
    INVARIANT: Founders have tenant_id = None (enforced, not trusted).
    """
    # 1. Extract principal
    principal = extract_principal(request)

    # 2. Map to RBAC roles (one-way only)
    if principal.principal_type == "console":
        token = validate_console_token(request)
        roles = [map_console_to_rbac(token)]
    elif principal.principal_type == "fops":
        # FOUNDER PATH TERMINATES HERE
        # Founders do NOT flow through tenant RBAC
        assert principal.tenant_id is None, "Founder must not have tenant_id"
        token = validate_fops_token(request)
        roles = [FOUNDER_TO_RBAC[token.role]]
    elif principal.principal_type == "machine":
        roles = ["machine"]  # Machine token = machine role
    else:
        roles = []

    return AuthContext(
        principal_id=principal.principal_id,
        principal_type=principal.principal_type,
        tenant_id=principal.tenant_id,
        effective_roles=roles,
        source_token_type=principal.source_token_type,
    )
```

**Founder Isolation Guard:**

```python
# MANDATORY: Founder access is nuclear privilege. Treat like root.
def guard_founder_access(ctx: AuthContext):
    """
    Founder paths must NEVER touch tenant data accidentally.
    """
    if ctx.principal_type == "fops":
        assert ctx.tenant_id is None, "SECURITY: Founder leaked into tenant context"
        # Founder actions explicit: /ops/customers/{id}, /ops/incidents/{id}
        # Never implicit tenant elevation
```

---

### Phase 4: Unified Middleware (BREAK CLEANLY)

**Rule:** When you flip this switch:
- Delete old checks
- Fail closed
- No fallback paths
- One middleware, one decision point

```python
class UnifiedAuthMiddleware(BaseHTTPMiddleware):
    """
    THE ONLY AUTH MIDDLEWARE.

    If something breaks, that's signal — not a bug.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Public paths — no auth required
        if self.is_public_path(path):
            return await call_next(request)

        # Build auth context (extracts identity + maps roles)
        try:
            ctx = build_auth_context(request)
        except AuthError as e:
            logger.warning("auth_failed", extra={"path": path, "error": str(e)})
            return JSONResponse(401, {"error": "authentication_required"})

        # Get RBAC policy for this path
        policy = get_policy_for_path(path, request.method)

        # No policy = bug in route registration
        if policy is None and not self.is_public_path(path):
            logger.error("missing_rbac_policy", extra={"path": path})
            return JSONResponse(500, {"error": "internal_auth_config_error"})

        # Enforce RBAC
        decision = enforce(policy, ctx.effective_roles)

        # Audit log EVERY decision
        self.log_decision(ctx, policy, decision)

        if not decision.allowed:
            return JSONResponse(403, {
                "error": "forbidden",
                "reason": decision.reason,
                "resource": policy.resource,
            })

        # Attach context to request state for downstream use
        request.state.auth_context = ctx

        return await call_next(request)
```

---

### Path-to-Domain Ownership (Final State)

| Path Pattern | Domain | Auth | RBAC Decision Point | Notes |
|--------------|--------|------|---------------------|-------|
| `/guard/*` | console | verify_console_token | UnifiedAuthMiddleware | Customer-facing |
| `/ops/*` | fops | verify_fops_token | Founder-isolated path | Nuclear privilege |
| `/api/v1/*` | machine | X-AOS-Key or JWT | UnifiedAuthMiddleware | Machine-native |
| `/v1/*` | machine | X-AOS-Key or JWT | UnifiedAuthMiddleware | Proxy/killswitch |
| `/health`, `/metrics` | public | None | Skip | Intentional |
| `/api/v1/auth/*` | public | None | Skip | Login/register |

---

## Implementation Checklist (Revised)

### Phase 1: Canonical Role Mapping
- [ ] Create `role_mapping.py` with **one-way** mapping (M28 → M7 only)
- [ ] Add `founder` and `operator` roles to M7 RBAC_MATRIX
- [ ] Enable shadow audit logging (log decisions without enforcing)
- [ ] Collect 48h of shadow audit data
- [ ] Unit tests for mapping (no bidirectional leakage)

### Phase 2: Resource Expansion
- [ ] Add 14 new resources to RBAC_MATRIX (agent, runtime, recovery, worker, trace, embedding, killswitch, integration, cost, checkpoint, event, incident, policies, health)
- [ ] Update `get_policy_for_path()` for ALL paths (no gaps allowed)
- [ ] Add Prometheus metrics for new resources
- [ ] Ensure NO path returns `policy = None` for protected routes

### Phase 2.5: X-AOS-Key Reclassification
- [ ] Create `Principal` dataclass with `principal_id`, `principal_type`, `tenant_id`
- [ ] Update key extraction to return identity, not authorization
- [ ] Force RBAC check on ALL key-authenticated routes
- [ ] Test: key alone should NOT grant access without RBAC

### Phase 3: Console-RBAC Bridge
- [ ] Create `AuthContext` dataclass with full extraction
- [ ] Implement `build_auth_context()` with per-request evaluation
- [ ] Add founder isolation guard (`assert tenant_id is None`)
- [ ] Test: founder token MUST NOT acquire tenant context
- [ ] Enable decision logging for all requests (correctness > performance)

### Phase 4: Unified Middleware (Clean Break)
- [ ] Replace dual middleware with `UnifiedAuthMiddleware`
- [ ] **DELETE** old auth checks (no fallbacks)
- [ ] Fail closed on missing policy
- [ ] Attach `auth_context` to request state
- [ ] Run full regression suite
- [ ] Monitor for 24h before declaring stable

---

## Risk Assessment (Updated)

| Risk | Severity | Mitigation | Phase |
|------|----------|------------|-------|
| Role escalation via bidirectional mapping | **CRITICAL** | One-way mapping only, tests enforce | 1 |
| X-AOS-Key bypass of RBAC | **CRITICAL** | Keys = identity only, RBAC enforced | 2.5 |
| Founder tenant leakage | **CRITICAL** | `assert tenant_id is None` guard | 3 |
| Breaking console apps | HIGH | Shadow audit → phased enforcement | 1→4 |
| Performance regression | MEDIUM | Per-request eval, no caching initially | 3 |
| Missing policy for route | MEDIUM | Fail 500 on `policy = None` | 4 |

---

## Success Criteria (Hard Requirements)

- [ ] **P2FC Invariant:** ALL permission checks route through M7 RBAC
- [ ] **One-Way:** No M28 → M7 inversion possible
- [ ] **Identity Separation:** X-AOS-Key = who, RBAC = what
- [ ] **Founder Isolation:** FOPS tokens never have `tenant_id`
- [ ] **No Gaps:** Every non-public path has RBAC policy
- [ ] **Audit Trail:** Every decision logged with principal + resource + action + outcome
- [ ] **Fail Closed:** Missing policy = 500 (bug), not pass-through

---

## Strategic Verdict

**You are at a platform maturity inflection point.**

| Before This Work | After This Work |
|------------------|-----------------|
| Features with implied governance | Enforceable authority |
| Demoable AI console | Auditable platform |
| Role theater | Real permission model |

**Execution Guidance:**

1. Freeze feature work for **1-2 weeks**
2. Complete Phases 1-3 with shadow logging
3. Analyze shadow logs for unexpected denials
4. Then decide when to execute Phase 4 (clean break)

> This is one of the rare moments where slowing down actually makes you faster.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-25 | **SHADOW AUDIT VERIFIED** - Rebuilt containers, confirmed logging working. Observation period started 15:36 UTC. Collecting: allowed vs would-block, reasons (no-credentials, role mismatch). 202 auth tests passing. Next: check rollout gates after 24-48h. |
| 2025-12-25 | **SHADOW AUDIT WIRED** - Completed middleware dispatch integration: (1) All decisions logged to shadow_audit, (2) In-memory aggregator for fast "who would be blocked" queries, (3) Prometheus metrics for observability, (4) Machine role locked down (read-only memory_pin, explicit killswitch/tenant/rbac denials), (5) 202 tests passing |
| 2025-12-25 | **REVISED** - Incorporated security architecture review: (1) One-way role mapping only, (2) X-AOS-Key as identity not auth, (3) Founder isolation guards, (4) 14 resources instead of 9, (5) Phase 2.5 for key reclassification, (6) Clean break requirements for Phase 4, (7) Shadow audit before enforcement |
| 2025-12-25 | Created PIN-169 with assessment and integration plan |
