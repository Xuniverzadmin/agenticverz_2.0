# P1.1-4.2 Frontend Entry Point Verification

**Generated:** 2026-01-06
**Phase:** Phase 1.1 - Legacy Resolution & Structural Hardening
**Reference:** PIN-317

---

## Objective

Verify no orphan UI code exists - every page file has a route, every route has a page.

---

## Entry Point Chain

```
main.tsx
    ↓
App.tsx (BrowserRouter basename="/console")
    ↓
routes/index.tsx (AppRoutes)
    ↓
├── /login                    → LoginPage
├── /onboarding/*             → OnboardingRoute → Pages
├── /guard/*                  → AIConsoleApp → Routes
├── /ops/*                    → OpsConsoleEntry
├── ProtectedRoute            → AppLayout → Founder Pages
└── /* (catch-all)            → Navigate → /guard
```

---

## Page-to-Route Verification

### Customer Console Pages (via AIConsoleApp)

| Page File | Route | Status |
|-----------|-------|--------|
| `products/ai-console/pages/overview/OverviewPage.tsx` | `/guard/overview` | OK |
| `products/ai-console/pages/activity/ActivityPage.tsx` | `/guard/activity` | OK |
| `products/ai-console/pages/incidents/IncidentsPage.tsx` | `/guard/incidents` | OK |
| `products/ai-console/pages/incidents/IncidentDetailPage.tsx` | `/guard/incidents/:id` | OK |
| `products/ai-console/pages/policies/PoliciesPage.tsx` | `/guard/policies` | OK |
| `products/ai-console/pages/logs/LogsPage.tsx` | `/guard/logs` | OK |
| `products/ai-console/integrations/IntegrationsPage.tsx` | `/guard/integrations` | OK |
| `products/ai-console/integrations/KeysPage.tsx` | `/guard/keys` | OK |
| `products/ai-console/account/SettingsPage.tsx` | `/guard/settings` | OK |
| `products/ai-console/account/AccountPage.tsx` | `/guard/account` | OK |

**Customer Console Status:** 10/10 pages routed

---

### Auth & Onboarding Pages

| Page File | Route | Status |
|-----------|-------|--------|
| `pages/auth/LoginPage.tsx` | `/login` | OK |
| `pages/onboarding/ConnectPage.tsx` | `/onboarding/connect` | OK |
| `pages/onboarding/SafetyPage.tsx` | `/onboarding/safety` | OK |
| `pages/onboarding/AlertsPage.tsx` | `/onboarding/alerts` | OK |
| `pages/onboarding/VerifyPage.tsx` | `/onboarding/verify` | OK |
| `pages/onboarding/CompletePage.tsx` | `/onboarding/complete` | OK |
| `pages/onboarding/OnboardingLayout.tsx` | (layout) | OK - Component |

**Auth/Onboarding Status:** 6/6 pages routed

---

### Founder Pages (via AppLayout / ProtectedRoute)

| Page File | Route | Status |
|-----------|-------|--------|
| `pages/traces/TracesPage.tsx` | `/traces` | OK |
| `pages/traces/TraceDetailPage.tsx` | `/traces/:runId` | OK |
| `pages/workers/WorkerStudioHome.tsx` | `/workers` | OK |
| `pages/workers/WorkerExecutionConsole.tsx` | `/workers/console` | OK |
| `pages/recovery/RecoveryPage.tsx` | `/recovery` | OK |
| `pages/sba/SBAInspectorPage.tsx` | `/sba` | OK |
| `pages/integration/IntegrationDashboard.tsx` | `/integration` | OK |
| `pages/integration/LoopStatusPage.tsx` | `/integration/loop/:id` | OK |
| `pages/founder/FounderTimelinePage.tsx` | `/founder/timeline` | OK |
| `pages/founder/FounderControlsPage.tsx` | `/founder/controls` | OK |
| `pages/founder/ReplayIndexPage.tsx` | `/founder/replay` | OK |
| `pages/founder/ReplaySliceViewer.tsx` | `/founder/replay/:id` | OK |
| `pages/founder/ScenarioBuilderPage.tsx` | `/founder/scenarios` | OK |
| `pages/founder/FounderExplorerPage.tsx` | `/founder/explorer` | OK |
| `pages/credits/CreditsPage.tsx` | `/credits` | OK |

**Founder Pages Status:** 15/15 pages routed

---

### Ops Console Pages

| Page File | Route | Status |
|-----------|-------|--------|
| `pages/ops/OpsConsoleEntry.tsx` | `/ops`, `/ops/*` | OK |
| `pages/ops/FounderOpsConsole.tsx` | (component) | OK - used by OpsConsoleEntry |
| `pages/ops/FounderPulsePage.tsx` | (component) | OK - used by OpsConsoleEntry |

**Ops Console Status:** 1 entry + 2 components

---

### Quarantined Pages

| Page File | Previous Route | Status |
|-----------|----------------|--------|
| `quarantine/SupportPage.tsx` | None | QUARANTINED (P1.1-2.2) |

---

## Component Files (Not Pages)

These files are in `pages/` directories but are components, not routable pages:

| File | Type | Used By |
|------|------|---------|
| `pages/sba/components/*.tsx` (18 files) | Components | SBAInspectorPage |
| `pages/workers/components/*.tsx` (5 files) | Components | Worker pages |
| `pages/founder/components/*.tsx` (2 files) | Components | Founder pages |
| `products/ai-console/pages/incidents/IncidentFilters.tsx` | Component | IncidentsPage |
| `products/ai-console/pages/incidents/IncidentSearchBar.tsx` | Component | IncidentsPage |
| `products/ai-console/pages/incidents/DecisionTimeline.tsx` | Component | IncidentDetailPage |
| `products/ai-console/app/AIConsoleLayout.tsx` | Layout | AIConsoleApp |
| `products/ai-console/main.tsx` | Entry | (standalone mode) |

---

## Routes Without Pages

| Route | Target | Status |
|-------|--------|--------|
| `/` | `<Navigate to="/guard">` | OK - Redirect |
| `/guard` | `AIConsoleApp` | OK |
| `/guard/*` | `AIConsoleApp` | OK |
| `/ops` | `OpsConsoleEntry` | OK |
| `/ops/*` | `OpsConsoleEntry` | OK |
| `/*` | `<Navigate to="/guard">` | OK - Catch-all |

**All routes have targets.**

---

## Verification Summary

| Category | Pages | Routed | Orphan | Status |
|----------|-------|--------|--------|--------|
| Customer Console | 10 | 10 | 0 | OK |
| Auth/Onboarding | 6 | 6 | 0 | OK |
| Founder Pages | 15 | 15 | 0 | OK |
| Ops Console | 1 | 1 | 0 | OK |
| Quarantine | 1 | 0 | 0 | EXPECTED |
| **Total** | **33** | **32** | **0** | **PASS** |

---

## Issues Found

### None - All pages are routed

Every page file has a corresponding route. No orphan UI code exists.

---

## Structural Observations

### 1. Two Entry Paradigms

| Console | Entry Pattern |
|---------|---------------|
| Customer (`/guard/*`) | AIConsoleApp handles own routing internally |
| Founder (legacy) | ProtectedRoute → AppLayout → Individual routes |
| Ops (`/ops/*`) | OpsConsoleEntry handles own routing internally |

**Recommendation:** Standardize to entry-point pattern (like AIConsoleApp) for founder pages.

### 2. Product-Based File Structure

```
src/
├── pages/                    # Founder/shared pages
│   ├── auth/
│   ├── onboarding/
│   ├── founder/
│   ├── ops/
│   ├── traces/
│   └── ...
└── products/
    └── ai-console/           # Customer console
        ├── app/
        ├── pages/
        ├── integrations/
        └── account/
```

**Status:** Structure is logical and maintainable.

---

## Acceptance Criteria

- [x] main.tsx → routes traced
- [x] All page files have routes
- [x] All routes have pages (or are redirects)
- [x] No orphan UI code identified
- [x] Quarantined pages excluded from routes

---

## Related Documents

- routes/index.tsx - Main route configuration
- products/ai-console/app/AIConsoleApp.tsx - Customer console routes
- P1_1_CANONICAL_ONBOARDING_FLOW.md - Onboarding journey
