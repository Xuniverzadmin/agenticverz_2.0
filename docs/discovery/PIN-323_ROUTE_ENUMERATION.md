# PIN-323: Route Enumeration Analysis

**Reference:** PIN-323 (L2-L2.1 Audit Reinforcement)
**Generated:** 2026-01-06
**Status:** Phase 2 Analysis

---

## Route Discovery Summary

### Frontend API Clients Analyzed

| Client | Routes Found | Capability |
|--------|--------------|------------|
| costsim.ts | 10 | CAP-002 |
| guard.ts | 10 | CAP-001/CAP-009 |
| scenarios.ts | 4 | CAP-002 |
| integration.ts | 5 | CAP-018 |
| timeline.ts | 2 | CAP-005 |
| ops.ts | 6 | CAP-005 |
| recovery.ts | 4 | CAP-018 |
| traces.ts | 3 | GAP (Activity) |
| memory.ts | 3 | CAP-014 |
| health.ts | 7 | PLATFORM |
| explorer.ts | 4 | CAP-005 |
| killswitch.ts | 8 | CAP-009/PLATFORM |
| failures.ts | 3 | GAP (Activity) |
| metrics.ts | 9 | PLATFORM |
| sba.ts | 4 | CAP-011 |
| runtime.ts | 4 | PLATFORM |
| auth.ts | 6 | CAP-006 |
| operator.ts | 8 | FOUNDER-ONLY |

---

## Route Classification

### Routes to ADD to allowed_routes

#### CAP-002 (Cost Simulation)

| Route | Method | Reason | Action |
|-------|--------|--------|--------|
| `/costsim/v2/status` | GET | Safe status check | ADD |
| `/costsim/v2/incidents` | GET | Read-only incidents | ADD |
| `/costsim/datasets` | GET | Read-only datasets | ADD |
| `/costsim/datasets/{id}` | GET | Read-only dataset | ADD |

#### CAP-001 (Replay) / CAP-009 (Policy Engine)

| Route | Method | Reason | Action |
|-------|--------|--------|--------|
| `/guard/status` | GET | Safe status check | ADD |
| `/guard/snapshot/today` | GET | Read-only snapshot | ADD |
| `/guard/incidents` | GET | Read-only list | ADD |
| `/guard/incidents/search` | POST | Search query | ADD |
| `/guard/keys` | GET | Read-only list | ADD |
| `/guard/settings` | GET | Read-only settings | ADD |
| `/guard/policies/active` | GET | Already in CAP-009 | OK |

#### CAP-018 (Integration Platform)

| Route | Method | Reason | Action |
|-------|--------|--------|--------|
| `/integration/checkpoints` | GET | Read-only | ADD |
| `/integration/stats` | GET | Read-only | ADD |
| `/integration/graduation` | GET | Read-only | ADD |

---

### Routes FLAGGED for Review

#### CAP-002 (Cost Simulation) - Founder/Ops Only

| Route | Method | Reason | Action |
|-------|--------|--------|--------|
| `/costsim/v2/reset` | POST | Circuit breaker reset | FOUNDER_ONLY |
| `/costsim/datasets/{id}/validate` | POST | Validation trigger | FOUNDER_ONLY |
| `/costsim/canary/run` | POST | Canary trigger | FOUNDER_ONLY |
| `/costsim/canary/reports` | GET | Canary reports | FOUNDER_ONLY |

#### CAP-001/CAP-009 - Mutation Operations

| Route | Method | Reason | Action |
|-------|--------|--------|--------|
| `/guard/killswitch/activate` | POST | Killswitch mutation | FOUNDER_ONLY |
| `/guard/killswitch/deactivate` | POST | Killswitch mutation | FOUNDER_ONLY |
| `/guard/demo/seed-incident` | POST | Demo only | FORBIDDEN |
| `/guard/incidents/{id}/acknowledge` | POST | State mutation | FOUNDER_ONLY |
| `/guard/keys/{id}/freeze` | POST | State mutation | FOUNDER_ONLY |

---

### GAP Routes (No Capability Assigned)

#### Activity Domain (traces.ts, failures.ts)

| Route | Method | Gap Type | Recommendation |
|-------|--------|----------|----------------|
| `/api/v1/traces` | GET | DOMAIN_GAP | Assign to new Activity capability |
| `/api/v1/traces` | POST | DOMAIN_GAP | FOUNDER_ONLY (trace creation) |
| `/api/v1/traces/cleanup` | POST | DOMAIN_GAP | FORBIDDEN (ops only) |
| `/api/v1/failures` | GET | DOMAIN_GAP | Assign to Activity capability |
| `/api/v1/failures/stats` | GET | DOMAIN_GAP | Assign to Activity capability |
| `/api/v1/failures/unrecovered` | GET | DOMAIN_GAP | Assign to Activity capability |

---

### Platform Routes (No Capability - System Wide)

| Route | Method | Type | Notes |
|-------|--------|------|-------|
| `/health` | GET | PUBLIC | No auth required |
| `/health/ready` | GET | PUBLIC | No auth required |
| `/health/adapters` | GET | PUBLIC | No auth required |
| `/health/skills` | GET | PUBLIC | No auth required |
| `/health/determinism` | GET | PUBLIC | No auth required |
| `/healthz/worker_pool` | GET | PUBLIC | No auth required |
| `/version` | GET | PUBLIC | No auth required |

---

## Summary

| Category | Count |
|----------|-------|
| Routes to ADD | 12 |
| Routes FOUNDER_ONLY | 10 |
| Routes FORBIDDEN | 2 |
| GAP Routes | 6 |
| Platform Routes | 7 |

---

## Phase 2 Actions

1. **Update CAPABILITY_REGISTRY.yaml** - Add 12 routes to allowed_routes
2. **Create CONSOLE_CLASSIFICATION.yaml** - Classify founder vs customer
3. **Document Activity Domain Gap** - Phase 3 will address

