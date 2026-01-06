# P1-1.3 L2 API I/O Surface Truth

**Generated:** 2026-01-06
**Phase:** Phase 1 - Repository Reality Alignment
**Reference:** PIN-316

---

## Summary

| Metric | Count |
|--------|-------|
| API Files | 41 |
| Total Routes | 369 |
| GET Endpoints | 215 |
| POST Endpoints | 130 |
| PUT Endpoints | 6 |
| PATCH Endpoints | 3 |
| DELETE Endpoints | 15 |

## Routes by Plane Classification

### Execution Plane (Mutating Operations)
Routes that create, modify, or delete state.

| File | POST | PUT | PATCH | DELETE |
|------|------|-----|-------|--------|
| agents.py | 20 | 1 | 0 | 1 |
| recovery.py | 6 | 0 | 1 | 2 |
| policy_layer.py | 14 | 0 | 2 | 1 |
| tenants.py | 1 | 1 | 0 | 1 |
| traces.py | 3 | 0 | 0 | 1 |

### Advisory Plane (READ-ONLY)
Routes that query state without side effects.

| File | GET Routes | Purpose |
|------|------------|---------|
| predictions.py | 3 | C2 predictions (advisory) |
| discovery.py | 2 | Discovery ledger queries |
| feedback.py | 2 | Feedback queries |
| health.py | 5 | Health checks |

### Visibility Plane (Observability)
Routes that expose system state for monitoring.

| File | Routes | Purpose |
|------|--------|---------|
| ops.py | 14 | Ops console visibility |
| guard.py | 18 | Guard/incident visibility |
| founder_timeline.py | 4 | Founder timeline |
| status_history.py | 4 | Status history |

## API Files by Capability

| Capability | Files | Routes |
|------------|-------|--------|
| CAP-001 (Replay) | replay.py, guard.py, runtime.py | 25 |
| CAP-002 (CostSim) | costsim.py, cost_intelligence.py, cost_guard.py | 28 |
| CAP-004 (Predictions) | predictions.py | 3 |
| CAP-005 (Founder) | founder_*.py, ops.py, cost_ops.py | 36 |
| CAP-006 (Auth) | onboarding.py, auth_helpers.py | 11 |
| CAP-007 (RBAC) | rbac_api.py, authz_status.py | 10 |
| CAP-008 (Multi-Agent) | agents.py | 49 |
| CAP-009 (Policy) | policy.py, policy_layer.py, policy_proposals.py | 46 |

## Flagged Routes

### Legacy/Deprecated Routes
Files that should be reviewed for removal or migration:

| File | Routes | Status |
|------|--------|--------|
| legacy_routes.py | 23 | QUARANTINE CANDIDATE |
| v1_killswitch.py | 10 | Review for M22 alignment |
| v1_proxy.py | 3 | Proxy routes - verify need |

### Routes Without Clear Capability
| Route | File | Recommendation |
|-------|------|----------------|
| `/dashboard/*` | legacy_routes.py | Remove or migrate |
| `/demo/*` | legacy_routes.py | Remove or migrate |
| `/operator/*` | legacy_routes.py | Migrate to /ops/* |
| `/simulation/*` | legacy_routes.py | Migrate to /costsim/* |

## Acceptance Criteria

- [x] All L2 endpoints enumerated
- [x] Routes grouped by plane (execution/advisory/visibility)
- [x] No endpoint without capability mapping (flagged if missing)
- [x] Legacy routes identified

## Recommendations

1. **Quarantine legacy_routes.py** - 23 routes with no capability ownership
2. **Verify v1_killswitch.py** alignment with M22 architecture
3. **Add capability_id headers** to files missing them
