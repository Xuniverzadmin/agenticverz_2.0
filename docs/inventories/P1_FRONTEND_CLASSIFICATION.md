# P1-2.2 Frontend Canonical vs Legacy Classification

**Generated:** 2026-01-06
**Phase:** Phase 1 - Repository Reality Alignment
**Reference:** PIN-316

---

## Summary

| Classification | Count | Status |
|---------------|-------|--------|
| Canonical | 34 pages | ACTIVE |
| Legacy | 0 | - |
| Speculative | 1 | REVIEW |
| Orphaned | 0 | - |
| Supporting Components | 23 | INTERNAL |

---

## Classification Definitions

| Classification | Definition |
|----------------|------------|
| **Canonical** | Actively mounted in routes, part of M28 architecture |
| **Legacy** | Deprecated, scheduled for removal (PIN-145 deletions done) |
| **Speculative** | Added for future features not yet live |
| **Orphaned** | File exists but not imported/mounted anywhere |
| **Supporting** | Internal components, not standalone pages |

---

## Customer Console Pages (AIConsoleApp)

**Domain:** /guard/* (Target: console.agenticverz.com)
**Entry:** `products/ai-console/app/AIConsoleApp.tsx`

| Page | Route | Classification | Evidence |
|------|-------|----------------|----------|
| OverviewPage | /guard/overview | **CANONICAL** | Mounted in AIConsoleApp |
| ActivityPage | /guard/activity | **CANONICAL** | Mounted in AIConsoleApp |
| IncidentsPage | /guard/incidents | **CANONICAL** | Mounted in AIConsoleApp |
| IncidentDetailPage | /guard/incidents/:id | **CANONICAL** | Mounted in AIConsoleApp |
| PoliciesPage | /guard/policies | **CANONICAL** | Mounted in AIConsoleApp |
| LogsPage | /guard/logs | **CANONICAL** | Mounted in AIConsoleApp |
| IntegrationsPage | /guard/integrations | **CANONICAL** | Mounted in AIConsoleApp |
| KeysPage | /guard/keys | **CANONICAL** | Mounted in AIConsoleApp |
| SettingsPage | /guard/settings | **CANONICAL** | Mounted in AIConsoleApp |
| AccountPage | /guard/account | **CANONICAL** | Mounted in AIConsoleApp |
| SupportPage | - | **SPECULATIVE** | Imported but no route |

### Customer Supporting Components
| File | Type | Used By |
|------|------|---------|
| IncidentFilters.tsx | Component | IncidentsPage |
| IncidentSearchBar.tsx | Component | IncidentsPage |
| DecisionTimeline.tsx | Component | IncidentDetailPage |
| AIConsoleLayout.tsx | Layout | AIConsoleApp |
| main.tsx | Entry | Standalone mount |

---

## Founder Pages (AppLayout)

**Domain:** Various routes (Target: fops.agenticverz.com)
**Entry:** `routes/index.tsx` → AppLayout

### Execution Domain
| Page | Route | Classification | Phase |
|------|-------|----------------|-------|
| TracesPage | /traces | **CANONICAL** | M28 |
| TraceDetailPage | /traces/:runId | **CANONICAL** | M28 |
| WorkerStudioHomePage | /workers | **CANONICAL** | M28 |
| WorkerExecutionConsolePage | /workers/console | **CANONICAL** | M28 |

### Reliability Domain
| Page | Route | Classification | Phase |
|------|-------|----------------|-------|
| RecoveryPage | /recovery | **CANONICAL** | M10 |

### Integration Domain
| Page | Route | Classification | Phase |
|------|-------|----------------|-------|
| IntegrationDashboard | /integration | **CANONICAL** | M25 |
| LoopStatusPage | /integration/loop/:id | **CANONICAL** | M25 |

### Founder Tools Domain
| Page | Route | Classification | Phase |
|------|-------|----------------|-------|
| FounderTimelinePage | /founder/timeline | **CANONICAL** | 5E-1 |
| FounderControlsPage | /founder/controls | **CANONICAL** | 5E-2 |
| ReplayIndexPage | /founder/replay | **CANONICAL** | H1 |
| ReplaySliceViewer | /founder/replay/:id | **CANONICAL** | H1 |
| ScenarioBuilderPage | /founder/scenarios | **CANONICAL** | H2 |
| FounderExplorerPage | /founder/explorer | **CANONICAL** | H3 |

### Governance Domain
| Page | Route | Classification | Phase |
|------|-------|----------------|-------|
| SBAInspectorPage | /sba | **CANONICAL** | M15 |
| CreditsPage | /credits | **CANONICAL** | - |

### Founder Supporting Components
| File | Type | Used By |
|------|------|---------|
| DecisionTimeline.tsx | Component | FounderTimelinePage |
| ReplayTimeline.tsx | Component | ReplaySliceViewer |
| SBADetailModal.tsx | Component | SBAInspectorPage |
| FulfillmentHeatmap.tsx | Component | SBAInspectorPage |
| SBAFilters.tsx | Component | SBAInspectorPage |
| ProfileTab.tsx | Component | SBAInspectorPage |
| ActivityTab.tsx | Component | SBAInspectorPage |
| HealthTab.tsx | Component | SBAInspectorPage |
| CostRiskOverview.tsx | Component | ActivityTab |
| IssuesBlockers.tsx | Component | ActivityTab |
| RetryLog.tsx | Component | ActivityTab |
| SpendingTracker.tsx | Component | ActivityTab |
| PermissionsPanel.tsx | Component | ProfileTab |
| TaskChecklist.tsx | Component | ProfileTab |
| PurposeCard.tsx | Component | ProfileTab |
| CompletionScore.tsx | Component | ProfileTab |
| HealthSummary.tsx | Component | HealthTab |
| HealthWarning.tsx | Component | HealthTab |
| ExecutionTimeline.tsx | Component | WorkerExecutionConsole |
| ArtifactPreview.tsx | Component | WorkerExecutionConsole |
| FailuresRecoveryPanel.tsx | Component | WorkerExecutionConsole |
| LiveLogStream.tsx | Component | WorkerExecutionConsole |
| RoutingDashboard.tsx | Component | WorkerStudioHome |

---

## Ops Console (OpsConsoleEntry)

**Domain:** /ops/*
**Entry:** `pages/ops/OpsConsoleEntry.tsx`

| Page | Route | Classification | Evidence |
|------|-------|----------------|----------|
| OpsConsoleEntry | /ops, /ops/* | **CANONICAL** | Mounted in routes |
| FounderOpsConsole | (internal) | **CANONICAL** | Loaded by OpsConsoleEntry |
| FounderPulsePage | (internal) | **CANONICAL** | Loaded by OpsConsoleEntry |

---

## Onboarding Pages

**Domain:** /onboarding/*

| Page | Route | Classification | Evidence |
|------|-------|----------------|----------|
| ConnectPage | /onboarding/connect | **CANONICAL** | Mounted in routes |
| SafetyPage | /onboarding/safety | **CANONICAL** | Mounted in routes |
| AlertsPage | /onboarding/alerts | **CANONICAL** | Mounted in routes |
| VerifyPage | /onboarding/verify | **CANONICAL** | Mounted in routes |
| CompletePage | /onboarding/complete | **CANONICAL** | Mounted in routes |

### Onboarding Supporting Components
| File | Type | Used By |
|------|------|---------|
| OnboardingLayout.tsx | Layout | All onboarding pages |

---

## Auth Pages

| Page | Route | Classification | Evidence |
|------|-------|----------------|----------|
| LoginPage | /login | **CANONICAL** | Mounted in routes (public) |

---

## Legacy/Deleted Pages (PIN-145)

The following pages were **permanently deleted** in M28:
- DashboardPage
- SkillsPage
- JobSimulatorPage
- FailuresPage
- BlackboardPage
- MetricsPage

**Status:** REMOVED - No files exist, no quarantine needed.

---

## Speculative Code Analysis

### SupportPage (SPECULATIVE)

**File:** `products/ai-console/account/SupportPage.tsx`

**Status:** SPECULATIVE - Imported in AIConsoleApp but no route exists.

**Evidence:**
- Line 65: `import { SupportPage } from '@ai-console/account/SupportPage';`
- No `/guard/support` route in AIConsoleApp routes
- Not in any fallback or catch-all

**Recommendation:** Either add route or remove import.

---

## Acceptance Criteria

- [x] Every page file classified
- [x] No ambiguous classifications
- [x] Legacy code identified (none found - already deleted)
- [x] Speculative code flagged (1 file)
- [x] Supporting components separated from pages

---

## Summary by Console

| Console | Canonical Pages | Speculative | Orphaned |
|---------|-----------------|-------------|----------|
| Customer (/guard/*) | 10 | 1 | 0 |
| Founder (AppLayout) | 14 | 0 | 0 |
| Ops (/ops/*) | 3 | 0 | 0 |
| Onboarding | 5 | 0 | 0 |
| Auth | 1 | 0 | 0 |
| **Total** | **33** | **1** | **0** |

---

## Next Steps (P1-2.3)

1. **SupportPage:** Decide to either:
   - Add `/guard/support` route to AIConsoleApp
   - Remove unused import

No quarantine needed - all legacy code was already deleted per PIN-145.
