# P1-2.1 Frontend Route & Page Inventory

**Generated:** 2026-01-06
**Phase:** Phase 1 - Repository Reality Alignment
**Reference:** PIN-316

---

## Summary

| Metric | Count |
|--------|-------|
| Total page files | 34 |
| Customer pages (console.agenticverz.com target) | 11 |
| Founder pages (fops.agenticverz.com target) | 18 |
| Onboarding pages | 5 |

## Route Architecture

### URL Structure
```
/login                    → LoginPage (Public)
/onboarding/*             → Onboarding flow (Pre-console)
/guard/*                  → Customer Console (AIConsoleApp)
/ops/*                    → Founder Ops Console (OpsConsoleEntry)
/*                        → Protected Founder routes (legacy, migrating)
```

### Target Architecture (M28 PIN-147)
| Domain | Routes | Owner |
|--------|--------|-------|
| console.agenticverz.com | /guard/*, billing, keys | CUSTOMER |
| fops.agenticverz.com | /ops/*, traces, workers, sba | FOUNDER |

---

## Customer Console Pages (AIConsoleApp)

**Entry Point:** `/guard/*`
**Target Domain:** console.agenticverz.com

| Route | Page | Capability | Plane |
|-------|------|------------|-------|
| /guard/overview | OverviewPage | Overview | Visibility |
| /guard/activity | ActivityPage | CAP-001 | Visibility |
| /guard/incidents | IncidentsPage | CAP-001 | Visibility |
| /guard/incidents/:id | IncidentDetailPage | CAP-001 | Visibility |
| /guard/policies | PoliciesPage | CAP-009 | Visibility |
| /guard/logs | LogsPage | CAP-001 | Visibility |
| /guard/integrations | IntegrationsPage | CAP-018 | Visibility |
| /guard/keys | KeysPage | CAP-006 | Visibility |
| /guard/settings | SettingsPage | Account | Visibility |
| /guard/account | AccountPage | Account | Visibility |

---

## Founder Pages

**Entry Point:** `/ops/*` + legacy routes
**Target Domain:** fops.agenticverz.com

### Ops Console (OpsConsoleEntry)
| Route | Page | Capability |
|-------|------|------------|
| /ops | OpsConsoleEntry | CAP-005 |
| /ops/* | OpsConsoleEntry (nested) | CAP-005 |

### Protected Founder Routes (AppLayout)
| Route | Page | Capability | Phase |
|-------|------|------------|-------|
| /traces | TracesPage | CAP-001 | M28 |
| /traces/:runId | TraceDetailPage | CAP-001 | M28 |
| /workers | WorkerStudioHomePage | CAP-012 | M28 |
| /workers/console | WorkerExecutionConsolePage | CAP-012 | M28 |
| /recovery | RecoveryPage | CAP-011 | M10 |
| /integration | IntegrationDashboard | CAP-013 | M25 |
| /integration/loop/:id | LoopStatusPage | CAP-013 | M25 |
| /fdr/timeline | FounderTimelinePage | CAP-005 | 5E-1 |
| /fdr/controls | FounderControlsPage | CAP-005 | 5E-2 |
| /fdr/replay | ReplayIndexPage | CAP-001 | H1 |
| /fdr/replay/:id | ReplaySliceViewer | CAP-001 | H1 |
| /fdr/scenarios | ScenarioBuilderPage | CAP-002 | H2 |
| /fdr/explorer | FounderExplorerPage | CAP-005 | H3 |
| /sba | SBAInspectorPage | CAP-008 | M15 |
| /credits | CreditsPage | Billing | - |

---

## Onboarding Pages

| Route | Page |
|-------|------|
| /onboarding/connect | ConnectPage |
| /onboarding/safety | SafetyPage |
| /onboarding/alerts | AlertsPage |
| /onboarding/verify | VerifyPage |
| /onboarding/complete | CompletePage |

---

## L2 API Consumption Mapping

### Customer Console API Dependencies
| Page | API Endpoints |
|------|---------------|
| OverviewPage | /guard/status, /guard/snapshot/today |
| ActivityPage | /api/v1/cus/activity |
| IncidentsPage | /guard/incidents |
| PoliciesPage | /guard/policies/* |
| LogsPage | /guard/logs/* |
| KeysPage | /guard/keys |

### Founder Console API Dependencies
| Page | API Endpoints |
|------|---------------|
| TracesPage | /api/v1/runtime/traces |
| RecoveryPage | /api/v1/recovery/* |
| ReplayIndexPage | /api/v1/replay/* |
| ScenarioBuilderPage | /api/v1/scenarios/* |
| FounderExplorerPage | /api/v1/explorer/* |

---

## Deleted Routes (M28 PIN-145)

The following pages were permanently removed:
- DashboardPage
- SkillsPage
- JobSimulatorPage
- FailuresPage
- BlackboardPage
- MetricsPage

---

## Acceptance Criteria

- [x] All frontend routes enumerated
- [x] Capability mapping for each page
- [x] L2 API consumption identified
- [x] Terminology alignment documented
