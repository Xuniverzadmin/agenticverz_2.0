# PIN-274: RBACv2 Promotion via Neon + Synthetic Load

**Status:** ACTIVE
**Category:** Authorization / Promotion Gate
**Created:** 2026-01-02
**Milestone:** Phase 1.3 Confidence Proof
**Related PINs:** PIN-271, PIN-272, PIN-273

---

## Summary

RBACv2 has production-grade **engineering** but not yet production-grade **operation**.

This PIN defines the path from engineering complete to operationally proven:
- Replace "7 days of users" with synthetic traffic at scale
- Execute shadow mode against Neon DB (not localhost)
- Achieve the three hard proofs required for promotion

**Key Insight:** Time is a proxy. Coverage is the invariant.

---

## Neon Cost Estimate (Validated)

### What Actually Costs Money in Neon

Neon pricing is driven by **compute time + storage + I/O**, not request count directly.

RBAC synthetic load does:
- **SELECT-heavy** queries (authorization checks)
- Minimal writes (metrics/logs)
- No large result sets

This is *cheap* relative to normal workloads.

### Cost Estimate

| Item | Estimate |
|------|----------|
| Compute time | ~0.5–1.0 compute-hours |
| Storage | negligible (already exists) |
| I/O | light (mostly cached index reads) |

**Expected cost for full promotion run: $0.50 – $2.00 USD**

Worst-case safety cap (2 compute-hours): **under $5**

---

## Tuned-Down Plan (Safe + Cheap)

### Coverage Math

RBAC correctness depends on **combinations**, not volume:

```
ActorType (5) × Roles (8) × Resources (12) × Actions (6) × Scopes (3) ≈ 8,640 combinations
```

Running each combo 50–100 times with parallelism provides statistical confidence.

### Phased Execution Plan

| Phase | Requests | Purpose |
|-------|----------|---------|
| Dry run | 50k | Validate wiring + metrics |
| Coverage run | 250k | Full matrix × repetition |
| Stress run | 500k | Concurrency + race exposure |
| **Total** | **~800k** | Equivalent to 1M confidence |

**Early exit permitted when:**
- `v2_more_permissive = 0`
- Discrepancy rate < 1%
- No new discrepancy types appearing

---

## Current State (Objective Truth)

### What Is Done (Solid)

| Component | Status | Evidence |
|-----------|--------|----------|
| RBACv2 authority core | COMPLETE | ActorContext, AuthorizationEngine, IdentityChain |
| RBACv1 ↔ RBACv2 shadow comparison | WIRED | `rbac_middleware.py` |
| Strict invariant (never more permissive) | ENFORCED | Alert on `v2_more_permissive` |
| Metrics + alerts + dashboard | DEPLOYED | PIN-273 artifacts |
| Promotion criteria | DEFINED | PIN-273 Promotion Readiness Guard |
| Tests pass | YES | 290 tests |
| Terminology locked | YES | RBACv1/RBACv2 framing |
| Rollback path defined | YES | Env var toggle |

### What Is NOT Done

| Gap | Why It Matters |
|-----|----------------|
| Shadow mode only runs on localhost | Tenancy semantics untested |
| No synthetic authorization load | Edge cases not exercised |
| Discrepancies not classified | Promotion blocked |
| CI Phase B not closed | Original goal incomplete |

---

## The Three Hard Proofs (Replace "7 Days of Users")

Real users don't hit edge cases. Synthetic traffic does.

### Proof A: Synthetic Traffic at Scale

**Requirement:** Run load that simulates the full authorization matrix.

| Dimension | Coverage Required |
|-----------|-------------------|
| ActorType | HUMAN, SERVICE, SYSTEM, EXTERNAL |
| Role | developer, admin, operator, owner, viewer |
| Resource | agent, run, policy, trace, incident, billing, team, account |
| Action | create, read, update, delete, execute, approve, export |
| Tenant | Cross-tenant attempts (MUST fail) |
| Operator | Bypass paths (MUST succeed) |
| Machine actors | CI, worker, replay |

**Success Criteria:**
- N million simulated requests executed
- `v2_more_permissive == 0`
- Discrepancy rate < 1%
- All discrepancies classified

### Proof B: Real Database with Real Tenancy

**Requirement:** RBAC shadow mode must run against Neon DB.

| Component | Localhost | Neon (Required) |
|-----------|-----------|-----------------|
| Authorization logic | Infra-independent | Infra-independent |
| Identity resolution | Adapter-based | Adapter-based |
| Tenancy correctness | UNTESTED | TESTED |
| Row-level filters | UNTESTED | TESTED |
| Multi-tenant isolation | UNTESTED | TESTED |

**What's NOT Required:**
- Clerk live auth (DevIdentityAdapter is sufficient)
- Payment integration
- Prometheus/Grafana running (observability, not correctness)

**What IS Required:**
- Neon DB connection
- Seeded tenants/accounts/teams
- Real tenant IDs in test data

### Proof C: Discrepancy Classification Complete

Every discrepancy must be tagged:

| Classification | Meaning | Count Target |
|----------------|---------|--------------|
| `expected_tightening` | RBACv2 correct, RBACv1 too loose | Document and accept |
| `expected_loosening` | RBACv1 over-restrictive | Document and accept |
| `bug` | RBACv2 is wrong | Fix before promotion |
| `spec_gap` | Policy not defined | Define before promotion |
| `v2_more_permissive` | SECURITY RISK | **MUST BE 0** |

---

## Synthetic Authorization Load Plan

### Phase 1: Test Data Setup (Neon)

```sql
-- Seed test tenants
INSERT INTO tenants (id, name, plan) VALUES
  ('tenant-alpha', 'Alpha Corp', 'enterprise'),
  ('tenant-beta', 'Beta Inc', 'starter'),
  ('tenant-gamma', 'Gamma LLC', 'professional');

-- Seed test accounts
INSERT INTO accounts (id, tenant_id, name) VALUES
  ('acct-alpha-1', 'tenant-alpha', 'Alpha Main'),
  ('acct-beta-1', 'tenant-beta', 'Beta Main'),
  ('acct-gamma-1', 'tenant-gamma', 'Gamma Main');

-- Seed test teams
INSERT INTO teams (id, account_id, name) VALUES
  ('team-alpha-dev', 'acct-alpha-1', 'Alpha Dev Team'),
  ('team-alpha-ops', 'acct-alpha-1', 'Alpha Ops Team'),
  ('team-beta-main', 'acct-beta-1', 'Beta Main Team');
```

### Phase 2: Authorization Matrix Script

```python
# scripts/load/rbac_synthetic_load.py

ACTOR_TYPES = ["human", "service", "system", "external"]
ROLES = ["developer", "admin", "operator", "owner", "viewer"]
RESOURCES = ["agent", "run", "policy", "trace", "incident", "billing", "team", "account"]
ACTIONS = ["create", "read", "update", "delete", "execute", "approve", "export"]
TENANTS = ["tenant-alpha", "tenant-beta", "tenant-gamma"]

def generate_authorization_matrix():
    """Generate all possible authorization combinations."""
    cases = []
    for actor_type in ACTOR_TYPES:
        for role in ROLES:
            for resource in RESOURCES:
                for action in ACTIONS:
                    for tenant in TENANTS:
                        cases.append({
                            "actor_type": actor_type,
                            "role": role,
                            "resource": resource,
                            "action": action,
                            "tenant_id": tenant,
                        })
    return cases

def generate_cross_tenant_cases():
    """Generate cross-tenant access attempts (MUST all fail)."""
    return [
        {"actor_tenant": "tenant-alpha", "target_tenant": "tenant-beta"},
        {"actor_tenant": "tenant-beta", "target_tenant": "tenant-gamma"},
        {"actor_tenant": "tenant-gamma", "target_tenant": "tenant-alpha"},
    ]

def generate_operator_bypass_cases():
    """Generate operator bypass attempts (MUST all succeed)."""
    return [
        {"actor_type": "operator", "resource": "any", "action": "any"},
    ]
```

### Phase 3: Load Execution

```bash
# Run against Neon
DATABASE_URL="postgresql://...:5432/nova_aos" \
PYTHONPATH=. \
python3 scripts/load/rbac_synthetic_load.py \
  --requests 1000000 \
  --parallel 10 \
  --output /tmp/rbac_load_results.json
```

### Phase 4: Results Analysis

```bash
# Analyze discrepancies
python3 scripts/load/analyze_rbac_results.py \
  --input /tmp/rbac_load_results.json \
  --dashboard-export /tmp/discrepancy_report.json
```

---

## Promotion Checklist (Signoff Required)

### Pre-Promotion Gate

| # | Condition | Threshold | Verified |
|---|-----------|-----------|----------|
| 1 | Shadow mode running against Neon DB | YES | [ ] |
| 2 | Test tenants/accounts/teams seeded | 3+ each | [ ] |
| 3 | Synthetic load executed | 800k+ requests | [ ] |
| 4 | `v2_more_permissive` count | = 0 | [ ] |
| 5 | Discrepancy rate | < 1% | [ ] |
| 6 | All discrepancies classified | 100% | [ ] |
| 7 | Cross-tenant isolation verified | 100% fail rate | [ ] |
| 8 | Operator bypass verified | 100% success rate | [ ] |
| 9 | Machine actor permissions verified | CI, worker, replay | [ ] |
| 10 | Rollback tested | Toggle works | [ ] |

### Promotion Signoff

```
RBAC_V2_PROMOTION_SIGNOFF

Date: ____________
Authorized by: ____________

Pre-conditions verified: [ ] YES
Load results attached: [ ] YES
Discrepancy report attached: [ ] YES

Decision: [ ] PROMOTE  [ ] DEFER

If DEFER, blockers:
_________________________________
```

---

## Parallel Tracks (No Drift)

### Track A: RBAC Promotion (This PIN)

```
1. Deploy shadow mode with Neon DB ← NEXT
2. Seed test tenants/accounts/teams
3. Run synthetic authorization load
4. Analyze discrepancies
5. Classify all discrepancies
6. Achieve 0 v2_more_permissive
7. Signoff and promote
```

**Timeline:** Achievable in days, not weeks.

### Track B: CI Closure (Resume Original Goal)

| North Star Invariant | Status | Action |
|----------------------|--------|--------|
| I1: No mystery failures | ACHIEVED | Maintain |
| I2: No silent skips | MOSTLY | Final audit needed |
| I3: No flaky tests | IMPROVED | Isolation fixes pending |
| I4: No human memory | ACHIEVED | Maintain |

**CI Phase B is NOT closed yet.** RBAC work enables it safely.

---

## What NOT To Do

| Don't | Why |
|-------|-----|
| Start Applicability UI | Sits on top of promoted RBAC |
| Start teams UI | Requires RBAC promotion first |
| Start enterprise settings | Requires RBAC promotion first |
| Promote on localhost evidence | Tenancy semantics untested |
| Wait for real users | Synthetic load is better coverage |
| Abandon CI closure | Original goal, not replaced |

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| `scripts/load/rbac_synthetic_load.py` | Authorization matrix generator | CREATED |
| `scripts/load/analyze_rbac_results.py` | Discrepancy analyzer | CREATED |
| `scripts/load/seed_neon_test_data.sql` | Neon test data | CREATED |

---

## Success Criteria

RBACv2 is **promotion-ready** when:

1. Shadow mode has run against Neon DB
2. 800k+ synthetic requests executed (coverage-equivalent to 1M)
3. `v2_more_permissive == 0` (non-negotiable)
4. Discrepancy rate < 1%
5. All discrepancies classified
6. Cross-tenant isolation proven
7. Operator bypass verified
8. Rollback tested
9. Human signoff obtained

**At that point:**
- Flip RBACv2 to enforcement
- Demote RBACv1 to reference (or remove)
- Proceed to Applicability Engine
- Onboard users safely

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-02 | Added Neon cost estimate ($0.50-$2.00), tuned-down plan (800k), scripts created |
| 2026-01-02 | PIN created - Neon + synthetic load plan defined |
