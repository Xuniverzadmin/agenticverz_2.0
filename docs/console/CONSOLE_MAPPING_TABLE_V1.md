# Console Mapping Table: Customer Console v1

**Status:** CLASSIFICATION (Read-Only)
**Date:** 2025-12-29
**Auditor:** Claude (BL-CONSOLE-001 compliant)
**Reference:** `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`

---

## Purpose

This document provides the authoritative mapping of:
- **Page** → **Domain/Section** → **Console Jurisdiction**

Every discovered page is classified exactly once.

---

## Jurisdiction Key

| Code | Console | Scope | Data Boundary |
|------|---------|-------|---------------|
| **CUST** | Customer Console | Single tenant | Tenant-isolated |
| **FNDR** | Founder Console | Cross-tenant | Founder-only |
| **OPS** | Ops Console | Infrastructure | Operator-only |
| **SHARED** | Shared | Pre-assignment | No tenant context |
| **ORPHAN** | Unassigned | — | Needs classification |

---

## Section Key (Customer Console Only)

| Code | Section | Position |
|------|---------|----------|
| **CORE** | Core Lenses | Top |
| **CONN** | Connectivity | Middle |
| **ADMIN** | Administration | Bottom |

---

## 1. CUSTOMER CONSOLE PAGES

### Core Lenses Section

| Route | Page Component | Domain | Section | Jurisdiction | Status |
|-------|----------------|--------|---------|--------------|--------|
| `/guard` | `CustomerHomePage.tsx` | Overview | CORE | CUST | OK |
| `/guard/runs` | `CustomerRunsPage.tsx` | Activity | CORE | CUST | OK |
| `/guard/limits` | `CustomerLimitsPage.tsx` | Policies | CORE | CUST | OK |
| `/guard/incidents` | `IncidentsPage.tsx` | Incidents | CORE | CUST | OK |
| `/guard/incidents/:id` | `IncidentDetailPage.tsx` | Incidents | CORE | CUST | OK (O3) |
| — | — | Logs | CORE | CUST | **MISSING** |

### Connectivity Section

| Route | Page Component | Domain | Section | Jurisdiction | Status |
|-------|----------------|--------|---------|--------------|--------|
| `/guard/keys` | `CustomerKeysPage.tsx` | API Keys | CONN | CUST | OK |
| — | — | Integrations | CONN | CUST | **MISSING** |

### Administration Section

| Route | Page Component | Domain | Section | Jurisdiction | Status |
|-------|----------------|--------|---------|--------------|--------|
| `/guard/settings` | `GuardSettingsPage.tsx` | Settings | ADMIN | CUST | OK |
| `/guard/account` | `AccountPage.tsx` | Account | ADMIN | CUST | OK |
| `/credits` | `CreditsPage.tsx` | Billing | ADMIN | CUST | MISPLACED |
| — | — | Users | ADMIN | CUST | **MISSING** |

### Not In Constitution (Customer Console)

| Route | Page Component | Current Label | Jurisdiction | Action |
|-------|----------------|---------------|--------------|--------|
| `/guard/support` | `SupportPage.tsx` | Support | CUST | REMOVE FROM NAV |

---

## 2. FOUNDER CONSOLE PAGES

### Primary Entry Points

| Route | Page Component | View | Jurisdiction | Status |
|-------|----------------|------|--------------|--------|
| `/ops` | `OpsConsoleEntry.tsx` | Entry | FNDR | OK |
| `/ops` (default) | `FounderPulsePage.tsx` | Pulse | FNDR | OK |
| `/ops/console` | `FounderOpsConsole.tsx` | Dashboard | FNDR | OK |

### Founder Features (Phase 5E)

| Route | Page Component | Purpose | Jurisdiction | Status |
|-------|----------------|---------|--------------|--------|
| `/fdr/timeline` | `FounderTimelinePage.tsx` | Decision Timeline | FNDR | OK |
| `/fdr/controls` | `FounderControlsPage.tsx` | Kill-Switch Controls | FNDR | OK |

### Founder Execution

| Route | Page Component | Purpose | Jurisdiction | Status |
|-------|----------------|---------|--------------|--------|
| `/traces` | `TracesPage.tsx` | All Traces | FNDR | NEEDS PROTECTION |
| `/traces/:runId` | `TraceDetailPage.tsx` | Trace Detail | FNDR | NEEDS PROTECTION |
| `/workers` | `WorkerStudioHome.tsx` | Worker Studio | FNDR | NEEDS PROTECTION |
| `/workers/console` | `WorkerExecutionConsole.tsx` | Execution Console | FNDR | NEEDS PROTECTION |

### Founder Integration (M25)

| Route | Page Component | Purpose | Jurisdiction | Status |
|-------|----------------|---------|--------------|--------|
| `/integration` | `IntegrationDashboard.tsx` | Integration Loop | FNDR | NEEDS PROTECTION |
| `/integration/loop/:id` | `LoopStatusPage.tsx` | Loop Status | FNDR | NEEDS PROTECTION |

### Founder Reliability

| Route | Page Component | Purpose | Jurisdiction | Status |
|-------|----------------|---------|--------------|--------|
| `/recovery` | `RecoveryPage.tsx` | Recovery Dashboard | FNDR | NEEDS PROTECTION |

### Founder Governance (SBA)

| Route | Page Component | Purpose | Jurisdiction | Status |
|-------|----------------|---------|--------------|--------|
| `/sba` | `SBAInspectorPage.tsx` | SBA Inspector | FNDR | NEEDS PROTECTION |

---

## 3. SHARED PAGES

### Authentication

| Route | Page Component | Purpose | Jurisdiction | Status |
|-------|----------------|---------|--------------|--------|
| `/login` | `LoginPage.tsx` | Entry Point | SHARED | OK |

### Onboarding Flow

| Route | Page Component | Step | Jurisdiction | Status |
|-------|----------------|------|--------------|--------|
| `/onboarding/connect` | `ConnectPage.tsx` | 1 | SHARED | OK |
| `/onboarding/safety` | `SafetyPage.tsx` | 2 | SHARED | OK |
| `/onboarding/alerts` | `AlertsPage.tsx` | 3 | SHARED | OK |
| `/onboarding/verify` | `VerifyPage.tsx` | 4 | SHARED | OK |
| `/onboarding/complete` | `CompletePage.tsx` | 5 | SHARED | OK |

---

## 4. LAYOUT COMPONENTS

| Component | Console | Purpose |
|-----------|---------|---------|
| `GuardLayout.tsx` | CUST | Customer sidebar + header |
| `GuardConsoleEntry.tsx` | CUST | Customer entry point |
| `GuardConsoleApp.tsx` | CUST | Alternative entry (dev/backup) |
| `OpsConsoleEntry.tsx` | FNDR | Founder entry point |
| `OnboardingLayout.tsx` | SHARED | Onboarding frame |

---

## 5. COMPLETE PAGE COUNT

| Jurisdiction | Count | Notes |
|--------------|-------|-------|
| CUST (Customer) | 11 | 3 missing (Logs, Integrations, Users) |
| FNDR (Founder) | 14 | 7 need access protection |
| SHARED | 6 | OK |
| **Total** | **31** | — |

---

## 6. DOMAIN COVERAGE BY CONSOLE

### Customer Console

| Domain | Has Page | Has Route | In Sidebar | Complete |
|--------|----------|-----------|------------|----------|
| Overview | YES | YES | YES (as Home) | RENAME |
| Activity | YES | YES | YES (as Runs) | RENAME |
| Incidents | YES | YES | YES | OK |
| Policies | YES | YES | YES (as Limits) | RENAME |
| Logs | **NO** | **NO** | **NO** | **GAP** |
| API Keys | YES | YES | YES | OK |
| Integrations | **NO** | **NO** | **NO** | **GAP** |
| Users | **NO** | **NO** | **NO** | **GAP** |
| Settings | YES | YES | YES | OK |
| Billing | YES | MISPLACED | NO | FIX ROUTE |
| Account | YES | YES | YES | OK |

### Founder Console

| View/Feature | Has Page | Has Route | Protected | Complete |
|--------------|----------|-----------|-----------|----------|
| Pulse | YES | YES | YES | OK |
| Console | YES | YES | YES | OK |
| Timeline | YES | YES | PARTIAL | FIX ACCESS |
| Controls | YES | YES | PARTIAL | FIX ACCESS |
| Traces | YES | YES | **NO** | **FIX** |
| Workers | YES | YES | **NO** | **FIX** |
| Integration | YES | YES | **NO** | **FIX** |
| Recovery | YES | YES | **NO** | **FIX** |
| SBA | YES | YES | **NO** | **FIX** |

---

## 7. ROUTE PREFIX MAPPING

| Prefix | Console | Notes |
|--------|---------|-------|
| `/guard/*` | CUST | Customer Console |
| `/ops/*` | FNDR | Founder Console (Pulse + Dashboard) |
| `/fdr/*` | FNDR | Founder Features (Phase 5E) |
| `/traces/*` | FNDR | Should be `/ops/traces/*` |
| `/workers/*` | FNDR | Should be `/ops/workers/*` |
| `/integration/*` | FNDR | Should be `/ops/integration/*` |
| `/recovery` | FNDR | Should be `/ops/recovery` |
| `/sba` | FNDR | Should be `/ops/sba` |
| `/credits` | CUST | Should be `/guard/billing` |
| `/onboarding/*` | SHARED | Pre-console assignment |
| `/login` | SHARED | Entry point |

---

## 8. JURISDICTION VIOLATIONS

### Routes Accessible Cross-Jurisdiction

| Route | Current Access | Should Be | Severity |
|-------|----------------|-----------|----------|
| `/traces` | ALL | FNDR only | HIGH |
| `/traces/:runId` | ALL | FNDR only | HIGH |
| `/workers` | ALL | FNDR only | HIGH |
| `/workers/console` | ALL | FNDR only | HIGH |
| `/integration` | ALL | FNDR only | HIGH |
| `/integration/loop/:id` | ALL | FNDR only | HIGH |
| `/recovery` | ALL | FNDR only | HIGH |
| `/sba` | ALL | FNDR only | HIGH |

### Routes Misplaced

| Route | Current Location | Should Be | Severity |
|-------|------------------|-----------|----------|
| `/credits` | Root | `/guard/billing` | LOW |
| `/fdr/timeline` | Root | `/ops/timeline` | LOW |
| `/fdr/controls` | Root | `/ops/controls` | LOW |

---

## 9. DATA FLOW BOUNDARIES

### Customer Console Data (CUST)

| Data Type | Source | Boundary |
|-----------|--------|----------|
| Status | Own tenant only | Tenant-isolated |
| Runs | Own tenant only | Tenant-isolated |
| Incidents | Own tenant only | Tenant-isolated |
| Policies | Own tenant only | Tenant-isolated |
| Logs | Own tenant only | Tenant-isolated |
| Spend | Own tenant only | Tenant-isolated |

### Founder Console Data (FNDR)

| Data Type | Source | Boundary |
|-----------|--------|----------|
| Pulse | All tenants | Cross-tenant |
| At-Risk Customers | All tenants | Cross-tenant |
| System Metrics | Infrastructure | Cross-tenant |
| Decision Timeline | All tenants | Cross-tenant |
| Kill-Switch State | Global | Cross-tenant |

---

## 10. RECOMMENDED ROUTE RESTRUCTURE

### Target State (Not Applied)

```
/guard/                    → Customer Console Entry
/guard/overview            → Overview (rename from home)
/guard/activity            → Activity (rename from runs)
/guard/incidents           → Incidents
/guard/incidents/:id       → Incident Detail (O3)
/guard/policies            → Policies (rename from limits)
/guard/logs                → Logs (NEW)
/guard/keys                → API Keys
/guard/integrations        → Integrations (NEW)
/guard/users               → Users (NEW)
/guard/settings            → Settings
/guard/billing             → Billing (move from /credits)
/guard/account             → Account

/ops/                      → Founder Console Entry
/ops/pulse                 → Pulse View
/ops/console               → Dashboard View
/ops/timeline              → Decision Timeline (move from /fdr/)
/ops/controls              → Kill-Switch Controls (move from /fdr/)
/ops/traces                → Traces (move from root)
/ops/traces/:id            → Trace Detail
/ops/workers               → Worker Studio (move from root)
/ops/workers/console       → Execution Console
/ops/integration           → Integration Loop (move from root)
/ops/integration/loop/:id  → Loop Status
/ops/recovery              → Recovery (move from root)
/ops/sba                   → SBA Inspector (move from root)

/login                     → Shared Login
/onboarding/*              → Shared Onboarding
```

---

## 11. SUMMARY MATRIX

### Customer Console v1 Completeness

| Section | Expected | Implemented | Gap |
|---------|----------|-------------|-----|
| Core Lenses | 5 | 4 | Logs |
| Connectivity | 2 | 1 | Integrations |
| Administration | 4 | 3 | Users |
| **Total** | **11** | **8** | **3 missing** |

### Jurisdiction Compliance

| Requirement | Status |
|-------------|--------|
| Customer pages tenant-isolated | OK |
| Founder pages protected | **7 VIOLATIONS** |
| No cross-jurisdiction data | OK (data layer) |
| No cross-jurisdiction routes | **VIOLATED** |

---

## CONSOLE CONSTITUTION CHECK

```
- Constitution loaded: YES
- Page → Domain mapping complete: YES
- Page → Console mapping complete: YES
- Jurisdiction boundaries documented: YES
- Violations identified: 8 routes, 3 missing pages
- Human approval required: YES (before any changes)
- Auto-applied: NO
```

---

**This is a classification document only. No changes have been made. All changes require human approval.**
