# P1.1-1.2 Backend Legacy Support Inventory

**Generated:** 2026-01-06
**Phase:** Phase 1.1 - Legacy Resolution & Structural Hardening
**Reference:** PIN-317

---

## Summary

| Category | API Files | Route Prefix | Status |
|----------|-----------|--------------|--------|
| Founder-Only APIs | 10 | Various (non-/guard/) | LEGACY ROUTES |
| Customer APIs | 4 | `/guard/*` | CANONICAL |
| Shared APIs | 8 | `/api/v1/*` | CANONICAL |
| Legacy/Deprecated | 1 | Various | QUARANTINE |

**Critical Finding:** 10 backend API files exist ONLY for founder UI and are not under a protected namespace.

---

## Founder-Only Backend APIs (LEGACY ROUTES)

These APIs support founder pages and have NO customer console consumers.

### Ops Console APIs

| File | Prefix | Routes | Frontend Consumer | Capability |
|------|--------|--------|-------------------|------------|
| `ops.py` | `/ops` | 14 | FounderPulsePage, OpsConsoleEntry | CAP-005 |
| `cost_ops.py` | `/ops/cost` | 6 | (ops internal) | CAP-002 |
| `founder_actions.py` | `/ops/actions` | 4 | FounderControlsPage | CAP-005 |

**Routes Exposed:**
- `GET /ops/pulse` - System pulse
- `GET /ops/infra` - Infrastructure status
- `GET /ops/customers` - Customer segments
- `GET /ops/customers/at-risk` - At-risk customers
- `GET /ops/playbooks` - Playbooks
- `POST /ops/jobs/compute-stickiness` - Trigger job
- `GET /ops/cost/*` - Cost operations
- `POST /ops/actions/*` - Founder actions

---

### Founder Tools APIs

| File | Prefix | Routes | Frontend Consumer | Capability |
|------|--------|--------|-------------------|------------|
| `founder_timeline.py` | `/founder/timeline` | 4 | FounderTimelinePage | CAP-005 |
| `founder_explorer.py` | `/explorer` | 5 | FounderExplorerPage | CAP-005 |
| `founder_review.py` | `/founder/contracts` | 6 | (founder review gate) | CAP-005 |

**Routes Exposed:**
- `GET /founder/timeline/*` - Decision timeline
- `GET /explorer/*` - Cross-tenant explorer
- `POST /founder/contracts/*` - Contract review

---

### Execution & Replay APIs

| File | Prefix | Routes | Frontend Consumer | Capability |
|------|--------|--------|-------------------|------------|
| `replay.py` | `/replay` | 5 | ReplayIndexPage, ReplaySliceViewer | CAP-001 |
| `traces.py` | `/traces` | 4 | TracesPage, TraceDetailPage | CAP-001 |
| `scenarios.py` | `/scenarios` | 4 | ScenarioBuilderPage | CAP-002 |

**Routes Exposed:**
- `GET /replay/:id/*` - Replay data
- `GET /traces` - Trace list
- `GET /traces/:id` - Trace detail
- `GET /scenarios` - Scenario list
- `POST /scenarios/simulate` - Run simulation

---

### Integration APIs

| File | Prefix | Routes | Frontend Consumer | Capability |
|------|--------|--------|-------------------|------------|
| `integration.py` | `/integration` | 8 | IntegrationDashboard, LoopStatusPage | CAP-013 |

**Routes Exposed:**
- `GET /integration/stats` - Integration stats
- `GET /integration/checkpoints` - Checkpoints
- `GET /integration/graduation` - Graduation status
- `GET /integration/loop/:id` - Loop status
- `POST /integration/resolve` - Resolve checkpoint

---

## Customer APIs (CANONICAL)

These APIs are correctly namespaced under `/guard/` and serve customer console.

| File | Prefix | Routes | Frontend Consumer | Capability |
|------|--------|--------|-------------------|------------|
| `guard.py` | `/guard` | 18 | AIConsoleApp (all pages) | CAP-001 |
| `guard_policies.py` | `/guard/policies` | 6 | PoliciesPage | CAP-009 |
| `guard_logs.py` | `/guard/logs` | 4 | LogsPage | CAP-001 |
| `cost_guard.py` | `/guard/costs` | 5 | (cost visibility) | CAP-002 |

**Status:** CANONICAL - No action required.

---

## Shared APIs (CANONICAL)

These APIs serve both founder and customer or have public access.

| File | Prefix | Routes | Consumers | Capability |
|------|--------|--------|-----------|------------|
| `runtime.py` | `/api/v1/runtime` | 8 | AIConsoleApp, SDK | - |
| `recovery.py` | `/api/v1/recovery` | 6 | RecoveryPage | CAP-011 |
| `workers.py` | `/api/v1/workers` | 5 | WorkerStudioHome | CAP-012 |
| `v1_killswitch.py` | `/v1` | 10 | SDK, FounderControls | CAP-022 |
| `policy.py` | `/api/v1/policy` | 8 | Multiple | CAP-009 |
| `customer_activity.py` | `/api/v1/customer` | 4 | ActivityPage | CAP-001 |
| `onboarding.py` | `/api/v1/auth` | 6 | Onboarding | CAP-006 |
| `tenants.py` | `/api/v1` | 8 | Onboarding, SDK | CAP-006 |

**Status:** CANONICAL - No action required.

---

## Legacy/Deprecated APIs (QUARANTINE)

| File | Prefix | Routes | Status |
|------|--------|--------|--------|
| `legacy_routes.py` | Various | 23 | Returns 410 Gone |

**Status:** Already quarantined - returns 410 for deprecated paths.

---

## Frontend ↔ Backend Dependency Map

### Founder Pages → Backend APIs

| Frontend Page | Backend APIs Used |
|---------------|-------------------|
| OpsConsoleEntry | `/ops/pulse` |
| FounderPulsePage | `/ops/pulse`, `/ops/infra`, `/ops/customers`, `/guard/incidents` |
| FounderOpsConsole | `/ops/*` |
| TracesPage | `/api/v1/runtime/traces` |
| TraceDetailPage | `/api/v1/traces/:id` |
| WorkerStudioHomePage | `/api/v1/worker/*` |
| WorkerExecutionConsolePage | `/api/v1/worker/*` |
| RecoveryPage | `/api/v1/recovery/*` |
| SBAInspectorPage | `/api/v1/sba/*` |
| IntegrationDashboard | `/integration/*` |
| LoopStatusPage | `/integration/loop/*` |
| FounderTimelinePage | `/founder/timeline/*` |
| FounderControlsPage | `/api/v1/killswitch/*`, `/ops/customers` |
| ReplayIndexPage | `/api/v1/replay/*` |
| ReplaySliceViewer | `/api/v1/replay/:id/*` |
| ScenarioBuilderPage | `/scenarios/*` |
| FounderExplorerPage | `/explorer/*` |

### Cross-Boundary Concern

**FounderPulsePage calls `/guard/incidents`** - This is a cross-boundary access where founder page calls customer API. This should be acceptable (founder can see all) but needs explicit documentation.

---

## Backend Code Without Canonical Consumer

These backend files have NO canonical (customer) frontend consumer:

| File | Evidence | Recommendation |
|------|----------|----------------|
| `ops.py` | Only called by founder pages | Keep - founder-only |
| `cost_ops.py` | Only called by ops pages | Keep - founder-only |
| `founder_actions.py` | Only called by founder controls | Keep - founder-only |
| `founder_timeline.py` | Only called by founder timeline | Keep - founder-only |
| `founder_explorer.py` | Only called by founder explorer | Keep - founder-only |
| `founder_review.py` | Not called by any page (just mounted) | Review - possibly unused |
| `replay.py` | Only called by replay pages | Keep - founder-only |
| `scenarios.py` | Only called by scenario builder | Keep - founder-only |
| `integration.py` | Only called by integration pages | Keep - founder-only |

---

## Namespace Migration Recommendation

### Current State
```
/ops/*                    → No protection
/explorer                 → No protection
/founder/*                → Partial (prefix only)
/replay                   → No protection
/scenarios                → No protection
/traces                   → No protection (but /api/v1/traces exists)
/integration              → No protection
```

### Target State
All founder-only APIs should:
1. Be under `/fops/` or `/api/v1/founder/` namespace
2. Require founder RBAC role
3. Not appear in OpenAPI for customer audience

---

## Acceptance Criteria

- [x] Frontend ↔ Backend legacy dependency map complete
- [x] Backend code paths without canonical consumer identified
- [x] API prefix analysis complete
- [x] Cross-boundary accesses documented
- [x] Migration recommendations provided

---

## Next Steps (P1.1-2.1)

Classify each legacy artifact as DELETE, QUARANTINE, or RETAIN based on this inventory.
