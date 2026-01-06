# P1.1-1.1 Frontend Legacy Surface Inventory

**Generated:** 2026-01-06
**Phase:** Phase 1.1 - Legacy Resolution & Structural Hardening
**Reference:** PIN-317

---

## Summary

| Category | Page Count | Route Namespace | Target Domain |
|----------|------------|-----------------|---------------|
| Auth | 1 | `/login` | SHARED |
| Onboarding | 5 | `/onboarding/*` | SHARED |
| Customer Console | 10 | `/guard/*` | console.agenticverz.com |
| **Founder Pages (LEGACY ROUTES)** | **18** | **Various** | **fops.agenticverz.com** |
| Credits | 1 | `/credits` | DISPUTED |

**Critical Finding:** 18 Founder pages are mounted at legacy routes (not under `fops/*`), making them potentially discoverable by customers.

---

## Definition of "Legacy" in This Context

**"Legacy" does NOT mean deprecated.** It means:

1. **Wrong namespace** - Founder pages not under `fops/*`
2. **Mixed entry** - Founder pages accessible via AppLayout (same as customer)
3. **Discovery risk** - Customer could navigate to founder pages via URL manipulation

---

## CANONICAL Pages (No Action Required)

### Auth Pages
| Page | Path | Route | Backend APIs | Status |
|------|------|-------|--------------|--------|
| LoginPage | `pages/auth/LoginPage.tsx` | `/login` | `/api/v1/auth/*` | CANONICAL |

### Onboarding Pages
| Page | Path | Route | Backend APIs | Status |
|------|------|-------|--------------|--------|
| ConnectPage | `pages/onboarding/ConnectPage.tsx` | `/onboarding/connect` | `/api/v1/tenants/*` | CANONICAL |
| SafetyPage | `pages/onboarding/SafetyPage.tsx` | `/onboarding/safety` | - | CANONICAL |
| AlertsPage | `pages/onboarding/AlertsPage.tsx` | `/onboarding/alerts` | - | CANONICAL |
| VerifyPage | `pages/onboarding/VerifyPage.tsx` | `/onboarding/verify` | `/api/v1/onboarding/*` | CANONICAL |
| CompletePage | `pages/onboarding/CompletePage.tsx` | `/onboarding/complete` | - | CANONICAL |

### Customer Console Pages (`products/ai-console/`)
| Page | Path | Route | Backend APIs | Status |
|------|------|-------|--------------|--------|
| OverviewPage | `products/ai-console/pages/overview/` | `/guard/overview` | `/guard/status`, `/guard/snapshot/today` | CANONICAL |
| ActivityPage | `products/ai-console/pages/activity/` | `/guard/activity` | `/api/v1/customer/activity` | CANONICAL |
| IncidentsPage | `products/ai-console/pages/incidents/` | `/guard/incidents` | `/guard/incidents` | CANONICAL |
| IncidentDetailPage | `products/ai-console/pages/incidents/` | `/guard/incidents/:id` | `/guard/incidents/:id`, `/guard/incidents/:id/timeline` | CANONICAL |
| PoliciesPage | `products/ai-console/pages/policies/` | `/guard/policies` | `/guard/policies/*` | CANONICAL |
| LogsPage | `products/ai-console/pages/logs/` | `/guard/logs` | `/guard/logs/*` | CANONICAL |
| IntegrationsPage | `products/ai-console/integrations/` | `/guard/integrations` | - | CANONICAL |
| KeysPage | `products/ai-console/integrations/` | `/guard/keys` | `/guard/keys` | CANONICAL |
| SettingsPage | `products/ai-console/account/` | `/guard/settings` | `/guard/settings` | CANONICAL |
| AccountPage | `products/ai-console/account/` | `/guard/account` | - | CANONICAL |

---

## FOUNDER Pages at LEGACY Routes (ACTION REQUIRED)

### Ops Console (`pages/ops/`)

**Current Route:** `/ops/*`
**Target Route:** `/fops/ops/*`
**Capability:** CAP-005 (Founder Console)

| Page | File | Current Route | Backend APIs | Plane |
|------|------|---------------|--------------|-------|
| OpsConsoleEntry | `OpsConsoleEntry.tsx` | `/ops`, `/ops/*` | `/ops/pulse` | Visibility |
| FounderOpsConsole | `FounderOpsConsole.tsx` | (internal) | `/ops/*` | Visibility |
| FounderPulsePage | `FounderPulsePage.tsx` | (internal) | `/ops/pulse`, `/ops/infra`, `/ops/customers`, `/guard/incidents` | Visibility |

**Backend APIs Used:**
- `GET /ops/pulse` - System health metrics
- `GET /ops/infra` - Infrastructure metrics
- `GET /ops/customers` - Customer segments
- `POST /ops/jobs/compute-stickiness` - Trigger stickiness job

---

### Traces (`pages/traces/`)

**Current Route:** `/traces`, `/traces/:runId`
**Target Route:** `/fops/traces/*`
**Capability:** CAP-001 (Execution Replay)

| Page | File | Current Route | Backend APIs | Plane |
|------|------|---------------|--------------|-------|
| TracesPage | `TracesPage.tsx` | `/traces` | `/api/v1/runtime/traces` | Visibility |
| TraceDetailPage | `TraceDetailPage.tsx` | `/traces/:runId` | `/api/v1/traces/:id` | Visibility |

**Backend APIs Used:**
- `GET /api/v1/runtime/traces` - List traces
- `GET /api/v1/traces/:id` - Trace detail

---

### Workers (`pages/workers/`)

**Current Route:** `/workers`, `/workers/console`
**Target Route:** `/fops/workers/*`
**Capability:** CAP-012 (Workflow Engine)

| Page | File | Current Route | Backend APIs | Plane |
|------|------|---------------|--------------|-------|
| WorkerStudioHomePage | `WorkerStudioHome.tsx` | `/workers` | `/api/v1/worker/*` | Visibility |
| WorkerExecutionConsolePage | `WorkerExecutionConsole.tsx` | `/workers/console` | `/api/v1/worker/*` | Execution |

**Backend APIs Used:**
- `GET /api/v1/worker/runs` - List worker runs
- `GET /api/v1/worker/health` - Worker health
- `POST /api/v1/worker/start` - Start worker run
- `POST /api/v1/worker/replay` - Replay worker run

---

### Recovery (`pages/recovery/`)

**Current Route:** `/recovery`
**Target Route:** `/fops/recovery`
**Capability:** CAP-011 (Governance Orchestration)

| Page | File | Current Route | Backend APIs | Plane |
|------|------|---------------|--------------|-------|
| RecoveryPage | `RecoveryPage.tsx` | `/recovery` | `/api/v1/recovery/*` | Visibility |

**Backend APIs Used:**
- `GET /api/v1/recovery/candidates` - List candidates
- `GET /api/v1/recovery/stats` - Recovery stats
- `POST /api/v1/recovery/approve` - Approve candidate
- `DELETE /api/v1/recovery/candidates/:id` - Reject candidate

---

### SBA Inspector (`pages/sba/`)

**Current Route:** `/sba`
**Target Route:** `/fops/sba`
**Capability:** CAP-008 (Multi-Agent)

| Page | File | Current Route | Backend APIs | Plane |
|------|------|---------------|--------------|-------|
| SBAInspectorPage | `SBAInspectorPage.tsx` | `/sba` | `/api/v1/sba/*` | Visibility |

**Supporting Components:** 18 files in `pages/sba/components/`

**Backend APIs Used:**
- `GET /api/v1/sba` - List SBAs
- `GET /api/v1/sba/:id` - SBA detail
- `GET /api/v1/sba/fulfillment/aggregated` - Fulfillment data
- `POST /api/v1/sba/check-spawn` - Spawn eligibility
- `GET /api/v1/agents/:id/health/check` - Agent health

---

### Integration (`pages/integration/`)

**Current Route:** `/integration`, `/integration/loop/:id`
**Target Route:** `/fops/integration/*`
**Capability:** CAP-013 (Learning Pipeline)

| Page | File | Current Route | Backend APIs | Plane |
|------|------|---------------|--------------|-------|
| IntegrationDashboard | `IntegrationDashboard.tsx` | `/integration` | `/api/v1/integration/*` | Visibility |
| LoopStatusPage | `LoopStatusPage.tsx` | `/integration/loop/:id` | `/api/v1/integration/loop/*` | Visibility |

**Backend APIs Used:**
- `GET /api/v1/integration/stats` - Integration stats
- `GET /api/v1/integration/checkpoints` - Checkpoints
- `GET /api/v1/integration/graduation` - Graduation status
- `POST /api/v1/integration/resolve` - Resolve checkpoint

---

### Founder Tools (`pages/founder/`)

**Current Routes:** `/founder/timeline`, `/founder/controls`, `/founder/replay/*`, `/founder/scenarios`, `/founder/explorer`
**Target Routes:** `/fops/founder/*`
**Capability:** CAP-005 (Founder Console), CAP-001 (Replay), CAP-002 (CostSim)

| Page | File | Current Route | Backend APIs | Plane |
|------|------|---------------|--------------|-------|
| FounderTimelinePage | `FounderTimelinePage.tsx` | `/founder/timeline` | `/api/v1/founder/timeline/*` | Visibility |
| FounderControlsPage | `FounderControlsPage.tsx` | `/founder/controls` | `/api/v1/killswitch/*` | Execution |
| ReplayIndexPage | `ReplayIndexPage.tsx` | `/founder/replay` | `/api/v1/replay/*` | Visibility |
| ReplaySliceViewer | `ReplaySliceViewer.tsx` | `/founder/replay/:id` | `/api/v1/replay/:id/*` | Visibility |
| ScenarioBuilderPage | `ScenarioBuilderPage.tsx` | `/founder/scenarios` | `/api/v1/scenarios/*` | Advisory |
| FounderExplorerPage | `FounderExplorerPage.tsx` | `/founder/explorer` | `/api/v1/explorer/*` | Visibility |

**Supporting Components:** 2 files in `pages/founder/components/`

**Backend APIs Used:**
- `GET /api/v1/founder/timeline/*` - Decision timeline
- `POST /api/v1/killswitch/*` - Kill-switch controls
- `GET /api/v1/replay/:id/slice` - Replay slice
- `GET /api/v1/scenarios` - Scenario list
- `POST /api/v1/scenarios/simulate` - Run simulation
- `GET /api/v1/explorer/*` - Cross-tenant explorer

---

### Credits (`pages/credits/`)

**Current Route:** `/credits`
**Disputed:** Should be Customer or Founder?
**Capability:** Billing

| Page | File | Current Route | Backend APIs | Plane |
|------|------|---------------|--------------|-------|
| CreditsPage | `CreditsPage.tsx` | `/credits` | `/api/v1/credits/*` | Visibility |

**Backend APIs Used:**
- `GET /api/v1/runtime/capabilities` - Credit balance
- `GET /api/v1/traces` - Usage history

**Decision Required:** Is billing Customer-facing (`/guard/billing`) or Founder-only (`/fops/billing`)?

---

## Speculative Pages (From Phase 1)

| Page | File | Status | Reason |
|------|------|--------|--------|
| SupportPage | `products/ai-console/account/SupportPage.tsx` | SPECULATIVE | Imported but no route |

---

## Route Namespace Analysis

### Current State (PROBLEMATIC)
```
/login                    → Auth (SHARED)
/onboarding/*             → Onboarding (SHARED)
/guard/*                  → Customer Console (CORRECT)
/ops/*                    → Founder Ops (WRONG - should be /fops/ops/*)
/traces/*                 → Founder (WRONG - should be /fops/traces/*)
/workers/*                → Founder (WRONG - should be /fops/workers/*)
/recovery                 → Founder (WRONG - should be /fops/recovery)
/sba                      → Founder (WRONG - should be /fops/sba)
/integration/*            → Founder (WRONG - should be /fops/integration/*)
/founder/*                → Founder (WRONG - should be /fops/founder/*)
/credits                  → DISPUTED
/*                        → AppLayout fallback (DANGEROUS)
```

### Target State (REQUIRED)
```
/login                    → Auth (SHARED)
/onboarding/*             → Onboarding (SHARED)
/guard/*                  → Customer Console (console.agenticverz.com)
/fops/*                   → Founder Console (fops.agenticverz.com)
  /fops/ops/*             → Founder Ops
  /fops/traces/*          → Traces
  /fops/workers/*         → Workers
  /fops/recovery          → Recovery
  /fops/sba               → SBA
  /fops/integration/*     → Integration
  /fops/founder/*         → Founder Tools
  /fops/credits           → Billing (if founder-only)
```

---

## Acceptance Criteria

- [x] Every legacy page listed
- [x] Path documented for each page
- [x] Original intent identified (founder-only)
- [x] Current routes documented
- [x] Backend APIs traced
- [x] Capability assigned where applicable
- [x] Plane assigned where applicable
- [x] No "unknown" without explanation

---

## Next Steps (P1.1-1.2)

Map backend support code that exists ONLY for these legacy frontend pages to determine if backend APIs also need namespace migration.
