# PIN-273: RBAC Authority Core (Phase 1) Complete

**Status:** ACTIVE
**Category:** Architecture / Authorization
**Created:** 2026-01-02
**Milestone:** Phase 1 Authority Core
**Related PINs:** PIN-271, PIN-272

---

## Summary

Phase 1 Authority Core is complete. The system now has:
- A canonical ActorContext (L6)
- A single AuthorizationEngine (L4)
- A real IdentityChain with production adapters
- RBACv2 Reference Mode integration with RBACv1 enforcement

**RBACv1 remains the Enforcement Authority.** RBACv2 is the Reference Authority operating in shadow mode. What remains is governed evolution, not migration hack.

---

## Terminology (LOCKED)

| Concept | Name |
|---------|------|
| Existing enforcement path | **RBACv1** (Enforcement Authority) |
| ActorContext + AuthEngine | **RBACv2** (Reference Authority) |
| Shadow comparison | RBACv2 Reference Mode |
| Cutover | RBACv2 Enforcement Promotion |

**Critical Distinction:**
- RBACv1 is the active enforcement authority
- RBACv2 is the reference authorization engine operating in shadow mode
- Promotion from reference → enforcement occurs only after equivalence is proven

---

## Coexistence Invariants (MANDATORY)

These invariants MUST hold during coexistence:

1. **RBACv2 MUST NEVER enforce while RBACv1 is active**
2. **RBACv2 MUST ALWAYS run when shadow mode is enabled**
3. **Any discrepancy MUST be observable** (log + metric)
4. **No endpoint may bypass the integration layer**
5. **Promotion is a HUMAN-GOVERNED action**, not a code flag
6. **RBACv1 and RBACv2 MUST NEVER co-decide** (no hybrid decisions)

---

## What Was Built

### Core Components (L4/L6)

| File | Layer | Purpose |
|------|-------|---------|
| `backend/app/auth/actor.py` | L6 | ActorContext, ActorType, IdentitySource, SYSTEM_ACTORS |
| `backend/app/auth/authorization.py` | L4 | AuthorizationEngine, Decision, AuthorizationResult |
| `backend/app/auth/identity_adapter.py` | L3 | ClerkAdapter, SystemIdentityAdapter, DevIdentityAdapter |
| `backend/app/auth/identity_chain.py` | L6 | IdentityChain, get_current_actor dependency |
| `backend/app/auth/rbac_integration.py` | L6 | Bridge layer for shadow mode |

### Test Coverage

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/auth/test_actor.py` | 21 | PASS |
| `tests/auth/test_authorization.py` | 24 | PASS |
| `tests/auth/test_rbac_integration.py` | 26 | PASS |
| **Total new tests** | **71** | **PASS** |

### RBACv2 Reference Mode Integration

RBACv2 runs **alongside** RBACv1 in Reference Mode:
- Every request: RBACv1 decides enforcement (Enforcement Authority)
- In parallel: RBACv2 runs and compares decisions (Reference Authority)
- Discrepancies logged as `rbac_v1_v2_discrepancy`
- Prometheus metrics track match/mismatch rates

**Environment variable:** `NEW_AUTH_SHADOW_ENABLED=true` (default)

---

## What Was Proven

| Invariant | Test Evidence |
|-----------|---------------|
| Tenant isolation | `test_tenant_isolation_different_tenant` |
| Operator bypass | `test_operator_bypass`, `test_operator_bypass_tenant_isolation` |
| Role → permission derivation | `test_compute_developer_permissions`, `test_compute_multiple_roles` |
| No JWT leakage | Identity adapters only, no JWT in L4 |
| System actors are first-class | `test_ci_actor_exists`, `test_worker_actor_exists` |
| ActorType restrictions | `test_external_paid_forbidden_actions`, `test_system_cannot_delete` |
| Wildcard matching | `test_global_wildcard_matches_all`, `test_action_wildcard_matches_action` |

---

## Promotion Strategy: Reference → Assert → Enforce

### Phase 1.1: Reference Mode (COMPLETE)

```
Status: ✅ IMPLEMENTED

- RBACv2 runs in parallel with RBACv1
- RBACv1 controls enforcement (Enforcement Authority)
- RBACv2 computes decisions (Reference Authority)
- Discrepancies logged as `rbac_v1_v2_discrepancy`
- Metrics: `rbac_v1_v2_comparison_total`, `rbac_v2_latency_seconds`
- Security alert on v2_more_permissive discrepancies
```

### Phase 1.2: Confidence Accumulation (IN PROGRESS)

```
Status: ⏳ IN PROGRESS

Objective: Make RBACv2 provably trustworthy before promotion.

Steps:
1. Dashboard observability (metrics breakdown by endpoint, actor_type, resource)
2. Classify all discrepancies (expected_tightening | expected_loosening | bug | spec_gap)
3. Promotion readiness guard (see below)
4. Zero v2_more_permissive unclassified discrepancies

The blocker to promotion is CONFIDENCE, not code.
```

### Phase 1.4: Enforcement Promotion (FUTURE)

```
Status: ⏳ BLOCKED BY 1.2

Prerequisites:
- Zero reference mismatches for N days
- Every intentional difference understood
- Rollback plan tested

Then:
- Promote RBACv2 to Enforcement Authority
- Demote RBACv1 to Reference (or remove)
- Middleware becomes: IdentityChain → AuthorizationEngine → done
```

---

## Prometheus Metrics

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `rbac_v1_v2_comparison_total` | Counter | resource, action, match, discrepancy_type, actor_type | Track decision parity |
| `rbac_v2_latency_seconds` | Histogram | - | Monitor RBACv2 performance |

### Discrepancy Types

| Type | Meaning | Action | Security |
|------|---------|--------|----------|
| `none` | Decisions match | Good | OK |
| `v2_more_restrictive` | RBACv1 allows, RBACv2 denies | Investigate - may break clients | OK |
| `v2_more_permissive` | RBACv1 denies, RBACv2 allows | **SECURITY ALERT** - immediate investigation | CRITICAL |

---

## Promotion Readiness Guard

RBACv2 is eligible for Enforcement Promotion ONLY when ALL conditions are met:

| Condition | Threshold | Rationale |
|-----------|-----------|-----------|
| Discrepancy rate | < 1% for 7 days | Proves equivalence |
| All discrepancies classified | 100% | No unknowns |
| No unclassified `v2_more_permissive` | 0 | Security risk |
| Rollback path tested | YES | Safety net |
| Human approval | REQUIRED | Governance |

### Discrepancy Classification

Every discrepancy MUST be tagged as one of:

| Classification | Meaning | Resolution |
|----------------|---------|------------|
| `expected_tightening` | RBACv2 is correct, RBACv1 was too loose | Accept RBACv2 behavior |
| `expected_loosening` | RBACv1 was over-restrictive | Accept RBACv2 behavior |
| `bug` | RBACv2 is wrong | Fix RBACv2 |
| `spec_gap` | Policy not yet defined | Define policy first |

### Promotion Invariant (CRITICAL)

> **RBACv2 may only become stricter than RBACv1 during promotion, never more permissive.**

This invariant protects against accidental privilege escalation during cutover.

---

## Golden Snippet (Muscle Memory)

Every new endpoint should use this pattern:

```python
from fastapi import Depends
from app.auth.identity_chain import get_current_actor
from app.auth.authorization import get_authorization_engine

@router.get("/resource")
async def get_resource(actor: ActorContext = Depends(get_current_actor)):
    authz = get_authorization_engine()
    authz.authorize(actor, "resource", "read").raise_if_denied()

    # ... business logic
```

---

## Search & Destroy List

Before RBACv2 Enforcement Promotion, eliminate these RBACv1 patterns:

| Pattern | Why | Replace With |
|---------|-----|--------------|
| `if "admin" in roles` | Direct role check | `authz.authorize(actor, resource, action)` |
| `X-Roles` header | Testing backdoor | `DevIdentityAdapter` or `SystemIdentityAdapter` |
| `request.state.roles` | Implicit state | `ActorContext` from dependency |
| `RBAC_MATRIX[role]` | Legacy permission lookup | `AuthorizationEngine.ROLE_PERMISSIONS` |

---

## Blockers for Phase 2 (Applicability Engine)

Do NOT start Phase 2 until:
- [ ] RBACv2 Enforcement Promotion is complete
- [ ] Reference audit shows 100% match rate
- [ ] Answer is deterministic: "who can do what"

**Authorization before visibility. Always.**

---

## File Manifest

### Created Phase 1.1

```
backend/app/auth/actor.py              # ActorContext, ActorType, IdentitySource
backend/app/auth/authorization.py      # AuthorizationEngine, Decision
backend/app/auth/identity_adapter.py   # ClerkAdapter, SystemIdentityAdapter
backend/app/auth/identity_chain.py     # IdentityChain, get_current_actor
backend/app/auth/rbac_integration.py   # RBACv1 ↔ RBACv2 bridge layer
backend/tests/auth/test_actor.py       # 21 tests
backend/tests/auth/test_authorization.py # 24 tests
backend/tests/auth/test_rbac_integration.py # 26 tests
```

### Created Phase 1.2

```
monitoring/grafana/rbac_v1_v2_comparison_dashboard.json  # Promotion gate dashboard
monitoring/rules/rbac_v1_v2_comparison_alerts.yml        # Alerting rules
```

### Modified This Phase

```
backend/app/auth/rbac_middleware.py    # RBACv2 Reference Mode comparison
docs/governance/RBAC_AUTHORITY_SEPARATION_DESIGN.md
docs/governance/PERMISSION_TAXONOMY_V1.md
CLAUDE.md                              # Added RBAC directive
```

---

## Next Concrete Task

**Phase 1.2: Confidence Accumulation**

1. Build discrepancy dashboard (Grafana)
   - `rbac_v1_v2_comparison_total` by endpoint, actor_type, resource
   - Alert on `v2_more_permissive` (security risk)
2. Classify existing discrepancies
   - Tag each as: expected_tightening | expected_loosening | bug | spec_gap
3. Monitor discrepancy rate until < 1% for 7 days
4. Achieve zero unclassified `v2_more_permissive` cases

Only then proceed to Assert Mode.

---

## What NOT To Do Next

- Do NOT rush RBACv2 promotion
- Do NOT start Applicability Engine wiring everywhere
- Do NOT touch L1 UI permissions
- Do NOT add more role types
- Do NOT add policy editors
- Do NOT add per-team complexity

**You are now operating an authorization system, not building auth.**

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-02 | Phase 1.2 started - Confidence Accumulation mode |
| 2026-01-02 | Metrics renamed: `rbac_v1_v2_comparison_total`, `rbac_v2_latency_seconds` |
| 2026-01-02 | Promotion Readiness Guard defined |
| 2026-01-02 | Phase 1.1 complete - RBACv2 Reference Mode live |
| 2026-01-02 | Terminology fixed: RBACv1/RBACv2 framing locked |
