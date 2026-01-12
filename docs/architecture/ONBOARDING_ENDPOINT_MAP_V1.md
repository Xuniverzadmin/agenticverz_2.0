# Endpoint → Onboarding State Mapping (v1)

**Status:** APPROVED
**PIN:** PIN-399
**Date:** 2026-01-12
**Applies to:** `/api/v1/*`
**Authority:** `Tenant.onboarding_state` only
**Founders:** No exceptions

---

## Legend

- **MIN STATE** = lowest state allowed to call the endpoint
- Calls from a lower state **must return 403 with explicit state error**
- Higher states may call lower-gated endpoints (monotonic)

---

## 1. Public / Pre-Tenant Endpoints

These do **not** depend on tenant onboarding state.

| Endpoint | Method | MIN STATE | Notes |
|----------|--------|-----------|-------|
| `/healthz` | GET | — | Infra only |
| `/readyz` | GET | — | Infra only |
| `/metrics` | GET | — | Infra / ops |
| `/auth/*` (Clerk redirects, callbacks) | * | — | Identity only |

These must **never** touch tenant context.

---

## 2. Tenant Bootstrap (CREATED)

These endpoints are allowed **immediately after tenant creation**.

| Endpoint | Method | MIN STATE | Purpose |
|----------|--------|-----------|---------|
| `/tenants/self` | GET | CREATED | Fetch tenant metadata |
| `/tenants/self/status` | GET | CREATED | Read onboarding_state |
| `/onboarding/status` | GET | CREATED | UX polling |
| `/onboarding/verify` | POST | CREATED | Triggers IDENTITY_VERIFIED transition |

No side effects beyond state transition.

---

## 3. Identity Verified (IDENTITY_VERIFIED)

This is the **bootstrap zone**. If this is wrong, onboarding breaks.

| Endpoint | Method | MIN STATE | Purpose |
|----------|--------|-----------|---------|
| `/api-keys` | GET | IDENTITY_VERIFIED | List keys |
| `/api-keys` | POST | IDENTITY_VERIFIED | Create first key |
| `/api-keys/{id}` | DELETE | IDENTITY_VERIFIED | Rotate/delete |
| `/sdk/instructions` | GET | IDENTITY_VERIFIED | Show setup steps |
| `/onboarding/advance/api-key` | POST | IDENTITY_VERIFIED | Optional explicit transition |

**No permissions, no roles, no plans apply here.**

---

## 4. API Key Created (API_KEY_CREATED)

Machine identity now exists.

| Endpoint | Method | MIN STATE | Purpose |
|----------|--------|-----------|---------|
| `/sdk/handshake` | POST | API_KEY_CREATED | First authenticated SDK call |
| `/sdk/register` | POST | API_KEY_CREATED | Confirms SDK connectivity |
| `/api-keys` | GET | API_KEY_CREATED | Ongoing management |
| `/api-keys/{id}` | DELETE | API_KEY_CREATED | Rotation |

**No business workloads yet.**

---

## 5. SDK Connected (SDK_CONNECTED)

Tenant is now operational.

| Endpoint | Method | MIN STATE | Purpose |
|----------|--------|-----------|---------|
| `/policies/*` | * | SDK_CONNECTED | Policy engine |
| `/costsim/*` | * | SDK_CONNECTED | Cost simulation |
| `/incidents/*` | * | SDK_CONNECTED | Incident tracking |
| `/telemetry/*` | * | SDK_CONNECTED | Metrics |
| `/traces/*` | * | SDK_CONNECTED | Tracing |
| `/checkpoints/*` | * | SDK_CONNECTED | State persistence |
| `/reports/*` | * | SDK_CONNECTED | Reporting |
| `/runs/*` | * | SDK_CONNECTED | Execution |
| `/agents/*` | * | SDK_CONNECTED | Agent management |
| `/workers/*` | * | SDK_CONNECTED | Worker management |

This is where **real usage begins**.

---

## 6. Complete (COMPLETE)

Production tenant.

| Endpoint | Method | MIN STATE | Purpose |
|----------|--------|-----------|---------|
| `/billing/*` | * | COMPLETE | Billing & plans |
| `/limits/*` | * | COMPLETE | Rate limits |
| `/org/users/*` | * | COMPLETE | Multi-user |
| `/roles/*` | * | COMPLETE | RBAC roles |
| `/support/*` | * | COMPLETE | Support tooling |

Only **after** this do roles and plans matter.

---

## 7. Explicitly Forbidden (All States < COMPLETE)

These must hard-fail if called early.

| Endpoint | Reason |
|----------|--------|
| Any `/billing/*` | No billing before onboarding |
| Any `/limits/*` | Limits apply post-onboarding |
| Any `/admin/*` | No admin surface during onboarding |
| Cross-tenant endpoints | Never allowed |

---

## 8. Failure Contract (Must Be Uniform)

Every gated endpoint **must fail like this**:

```json
{
  "error": "onboarding_state_violation",
  "current_state": "CREATED",
  "required_state": "IDENTITY_VERIFIED",
  "endpoint": "/api/v1/api-keys"
}
```

**Invariants:**
- No generic 403s
- No permission language
- No RBAC leakage

---

## 9. Design Invariants Reinforced

| ID | Invariant |
|----|-----------|
| ONBOARD-001 | State is the only authority |
| ONBOARD-002 | Roles ignored pre-COMPLETE |
| ONBOARD-003 | Founders == customers |
| ONBOARD-004 | No inference |
| ONBOARD-005 | API keys are bootstrap artifacts |

---

## 10. Unclassified Endpoints

Any endpoint not listed above is **implicitly forbidden** until classified.

See Section 11 for the gap analysis.

---

## 11. Gap Analysis (Completed 2026-01-12)

### Critical Finding: /api-keys Router DISABLED

The tenants router containing `/api-keys` endpoints is currently **DISABLED** in main.py:
```python
# app.include_router(tenants_router)  # M21 - DISABLED: Premature for beta stage
```

**Action Required:** Enable and gate with IDENTITY_VERIFIED state.

---

### Router Classification Summary

#### Founder-Only (FOPS Token - Outside Onboarding Scope)
These use `verify_fops_token` dependency and are founder-only access.

| Router | Prefix | Classification |
|--------|--------|----------------|
| ops.py | `/ops/*` | FOPS_ONLY |
| cost_ops.py | `/ops/cost/*` | FOPS_ONLY |
| founder_actions.py | `/ops/actions/*` | FOPS_ONLY |
| founder_timeline.py | `/founder/timeline/*` | FOPS_ONLY |
| founder_review.py | `/founder/review/*` | FOPS_ONLY |
| founder_contract_review.py | `/founder/contracts/*` | FOPS_ONLY |
| platform.py | `/platform/*` | FOPS_ONLY |
| founder_explorer.py | `/explorer/*` | FOPS_ONLY |
| integration.py | `/integration/*` | FOPS_ONLY |
| scenarios.py | `/scenarios/*` | FOPS_ONLY |
| recovery.py | `/api/v1/recovery/*` | FOPS_ONLY |

**Status:** These do NOT need onboarding state gating (separate auth).

---

#### Customer Console (Requires Classification)
These need onboarding state gating.

| Router | Prefix | Proposed MIN STATE |
|--------|--------|-------------------|
| guard.py | `/guard/*` | SDK_CONNECTED |
| guard_logs.py | `/guard/logs/*` | SDK_CONNECTED |
| guard_policies.py | `/guard/policies/*` | SDK_CONNECTED |
| cost_guard.py | `/guard/costs/*` | SDK_CONNECTED |
| customer_visibility.py | `/customer/*` | SDK_CONNECTED |
| customer_activity.py | `/api/v1/customer/*` | SDK_CONNECTED |

**Action Required:** Add onboarding state gate.

---

#### SDK/Runtime Endpoints

| Router | Prefix | Proposed MIN STATE |
|--------|--------|-------------------|
| activity.py | `/api/v1/activity/*` | SDK_CONNECTED |
| incidents.py | `/api/v1/incidents/*` | SDK_CONNECTED |
| traces.py | `/api/v1/traces/*` | SDK_CONNECTED |
| policy.py | `/api/v1/policy/*` | SDK_CONNECTED |
| policy_layer.py | `/api/v1/policy-layer/*` | SDK_CONNECTED |
| policy_proposals.py | `/api/v1/policy-proposals` | SDK_CONNECTED |
| runtime.py | `/api/v1/runtime/*` | SDK_CONNECTED |
| feedback.py | `/api/v1/feedback` | SDK_CONNECTED |
| predictions.py | `/api/v1/predictions` | SDK_CONNECTED |
| discovery.py | `/api/v1/discovery` | SDK_CONNECTED |
| replay.py | `/api/v1/replay/*` | SDK_CONNECTED |
| costsim.py | `/costsim/*` | SDK_CONNECTED |
| embedding.py | `/api/v1/embedding/*` | SDK_CONNECTED |
| memory_pins.py | `/api/v1/memory/*` | SDK_CONNECTED |
| agents.py | `/api/v1/agents/*` | SDK_CONNECTED |
| workers.py | `/api/v1/workers/*` | SDK_CONNECTED |

**Action Required:** Add onboarding state gate.

---

#### Onboarding Flow

| Router | Prefix | Current State |
|--------|--------|---------------|
| onboarding.py | `/api/v1/auth/*` | CREATED (already onboarding) |
| tenants.py | `/api/v1/api-keys` | **DISABLED** |

**Action Required:**
1. Enable tenants_router
2. Gate `/api-keys` with IDENTITY_VERIFIED

---

#### Internal/System

| Router | Prefix | Classification |
|--------|--------|----------------|
| authz_status.py | `/internal/authz/*` | INTERNAL_ONLY |
| rbac_api.py | `/api/v1/rbac/*` | INTERNAL_ONLY |

**Status:** Internal endpoints, not customer-facing.

---

#### Legacy/Deprecated

| Router | Prefix | Action |
|--------|--------|--------|
| status_history.py | `/status_history/*` | Deprecate or gate SDK_CONNECTED |
| c2_predictions.py | `/api/v1/c2/predictions` | Gate SDK_CONNECTED |
| recovery_ingest.py | `/api/v1/recovery-ingest/*` | Gate SDK_CONNECTED |
| v1_proxy.py | `/v1/chat/completions` | Machine auth only |
| v1_killswitch.py | `/v1/killswitch/*` | Gate SDK_CONNECTED |
| legacy_routes.py | `/dashboard`, `/operator/*` | Deprecate |

---

### Implementation Priority

1. **P0: Enable /api-keys** - Currently DISABLED, blocking onboarding
2. **P1: Gate onboarding endpoints** - /api/v1/auth/*, /api-keys
3. **P2: Gate customer console** - /guard/*, /customer/*
4. **P3: Gate SDK endpoints** - All /api/v1/* business endpoints

---

## References

- PIN-399: Onboarding State Machine v1
- PIN-398: Auth Design Sanitization
- docs/architecture/ONBOARDING_STATE_MACHINE_V1.md
