# Topology Audit: Customer Console v1

**Status:** AUDIT (Read-Only)
**Date:** 2025-12-29
**Auditor:** Claude (BL-CONSOLE-001 compliant)
**Reference:** `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`

---

## Audit Scope

This document maps all discovered pages/routes to:
1. One of the 5 frozen domains (Overview, Activity, Incidents, Policies, Logs)
2. Connectivity section (Integrations, API Keys)
3. Administration section (Users, Settings, Billing, Account)
4. OR marks as "Out of Scope" (not Customer Console jurisdiction)

---

## Summary Counts

| Category | Count | Status |
|----------|-------|--------|
| Customer Console Pages | 15 | In scope |
| Founder/Ops Pages | 31 | Out of scope |
| Shared Pages | 7 | Partial scope |
| Onboarding Pages | 6 | Pre-console |
| **Total Discovered** | **59** | — |

---

## 1. CUSTOMER CONSOLE PAGES (Guard)

### Current Guard Navigation (8 items)

| Current Label | Route | Frozen Domain | Section | Fit Status |
|---------------|-------|---------------|---------|------------|
| Home | `/guard` | **Overview** | Core Lenses | PARTIAL FIT |
| Runs | `/guard/runs` | **Activity** | Core Lenses | FIT |
| Limits & Usage | `/guard/limits` | **Policies** | Core Lenses | PARTIAL FIT |
| Incidents | `/guard/incidents` | **Incidents** | Core Lenses | FIT |
| API Keys | `/guard/keys` | — | Connectivity | FIT |
| Settings | `/guard/settings` | — | Administration | FIT |
| Account | `/guard/account` | — | Administration | FIT |
| Support | `/guard/support` | — | Administration | GAP |

### Domain Assignment Details

#### Overview Domain
| Page | Component | Current State | Notes |
|------|-----------|---------------|-------|
| Home | `CustomerHomePage.tsx` | Exists as "Home" | Should be "Overview" |

**Fit Analysis:**
- Current: Called "Home", shows status overview
- Expected: Called "Overview", answers "Is the system okay right now?"
- Gap: Name mismatch, but function matches

#### Activity Domain
| Page | Component | Current State | Notes |
|------|-----------|---------------|-------|
| Runs | `CustomerRunsPage.tsx` | Exists as "Runs" | Vocabulary correct |

**Fit Analysis:**
- Current: Shows run history & outcomes
- Expected: Shows "What ran / is running?"
- Status: FIT

#### Incidents Domain
| Page | Component | Current State | Notes |
|------|-----------|---------------|-------|
| Incidents List | `IncidentsPage.tsx` | Exists | O2 list view |
| Incident Detail | `IncidentDetailPage.tsx` | Exists | O3 detail view |

**Fit Analysis:**
- Current: Search & investigate incidents
- Expected: "What went wrong?"
- Status: FIT
- Note: O3 detail exists via route `/guard/incidents/:incidentId`

#### Policies Domain
| Page | Component | Current State | Notes |
|------|-----------|---------------|-------|
| Limits & Usage | `CustomerLimitsPage.tsx` | Exists as "Limits & Usage" | Vocabulary needs alignment |

**Fit Analysis:**
- Current: Budget & rate limits
- Expected: "How is behavior defined?" (Rules, Limits, Constraints, Approvals)
- Status: PARTIAL FIT
- Gap: Called "Limits & Usage" but Policies is the frozen domain
- Note: Limits is a subset of Policies (Risk Ceilings)

#### Logs Domain
| Page | Component | Current State | Notes |
|------|-----------|---------------|-------|
| — | — | **MISSING** | No Logs page exists |

**Fit Analysis:**
- Current: No dedicated Logs page
- Expected: "What is the raw truth?" (Traces, Audit, Proof)
- Status: GAP
- Note: Critical missing domain

---

## 2. CONNECTIVITY SECTION

| Page | Component | Current State | Notes |
|------|-----------|---------------|-------|
| API Keys | `CustomerKeysPage.tsx` | Exists | Correct placement |
| Integrations | — | **MISSING** | Not implemented |

**Analysis:**
- API Keys: FIT (correct section)
- Integrations: GAP (missing, but not blocking for v1)

---

## 3. ADMINISTRATION SECTION

| Page | Component | Current State | Notes |
|------|-----------|---------------|-------|
| Settings | `GuardSettingsPage.tsx` | Exists | Correct placement |
| Account | `AccountPage.tsx` | Exists | Correct placement |
| Billing | — | Partial | Via `/credits` route |
| Users | — | **MISSING** | Not implemented |
| Support | `SupportPage.tsx` | Exists | **VIOLATION** - Not in constitution |

**Analysis:**
- Settings: FIT
- Account: FIT
- Billing: PARTIAL (exists as "Credits", route at `/credits`)
- Users: GAP (not implemented)
- Support: VIOLATION (not in frozen sidebar structure)

---

## 4. OUT OF SCOPE (Founder/Ops Jurisdiction)

These pages exist but belong to Founder or Ops Console, NOT Customer Console.

### Ops Console Entry Points

| Route | Component | Jurisdiction | Notes |
|-------|-----------|--------------|-------|
| `/ops` | `OpsConsoleEntry.tsx` | FOUNDER | Ops console entry |
| `/ops/*` | `OpsConsoleEntry.tsx` | FOUNDER | Wildcard catch |

### Founder Pulse & Console

| Route | Component | Jurisdiction | Notes |
|-------|-----------|--------------|-------|
| `/ops` (pulse) | `FounderPulsePage.tsx` | FOUNDER | 10-sec situation view |
| `/ops/console` | `FounderOpsConsole.tsx` | FOUNDER | 2x2 dashboard |

### Founder Features (Phase 5E)

| Route | Component | Jurisdiction | Notes |
|-------|-----------|--------------|-------|
| `/founder/timeline` | `FounderTimelinePage.tsx` | FOUNDER | Decision timeline |
| `/founder/controls` | `FounderControlsPage.tsx` | FOUNDER | Kill-switch controls |

### Founder Execution

| Route | Component | Jurisdiction | Notes |
|-------|-----------|--------------|-------|
| `/traces` | `TracesPage.tsx` | FOUNDER | All traces |
| `/traces/:runId` | `TraceDetailPage.tsx` | FOUNDER | Trace detail |
| `/workers` | `WorkerStudioHome.tsx` | FOUNDER | Worker studio |
| `/workers/console` | `WorkerExecutionConsole.tsx` | FOUNDER | Execution console |

### Founder Integration (M25)

| Route | Component | Jurisdiction | Notes |
|-------|-----------|--------------|-------|
| `/integration` | `IntegrationDashboard.tsx` | FOUNDER | Integration loop |
| `/integration/loop/:id` | `LoopStatusPage.tsx` | FOUNDER | Loop status |

### Founder Reliability

| Route | Component | Jurisdiction | Notes |
|-------|-----------|--------------|-------|
| `/recovery` | `RecoveryPage.tsx` | FOUNDER | Recovery dashboard |

### Founder Governance (SBA)

| Route | Component | Jurisdiction | Notes |
|-------|-----------|--------------|-------|
| `/sba` | `SBAInspectorPage.tsx` | FOUNDER | 17 sub-components |

---

## 5. SHARED / PRE-CONSOLE

### Authentication

| Route | Component | Scope | Notes |
|-------|-----------|-------|-------|
| `/login` | `LoginPage.tsx` | SHARED | Entry point |

### Onboarding (Pre-Console Assignment)

| Route | Component | Scope | Notes |
|-------|-----------|-------|-------|
| `/onboarding/connect` | `ConnectPage.tsx` | SHARED | Step 1 |
| `/onboarding/safety` | `SafetyPage.tsx` | SHARED | Step 2 |
| `/onboarding/alerts` | `AlertsPage.tsx` | SHARED | Step 3 |
| `/onboarding/verify` | `VerifyPage.tsx` | SHARED | Step 4 |
| `/onboarding/complete` | `CompletePage.tsx` | SHARED | Step 5 |

### Billing

| Route | Component | Scope | Notes |
|-------|-----------|-------|-------|
| `/credits` | `CreditsPage.tsx` | CUSTOMER | Should be `/guard/billing` |

---

## 6. JURISDICTION VIOLATIONS

| Item | Current State | Violation | Severity |
|------|---------------|-----------|----------|
| Support page | In Customer sidebar | Not in constitution | MEDIUM |
| Credits route | At `/credits` | Should be under `/guard/` | LOW |
| Traces route | Accessible to all | Should be Founder-only | HIGH |
| Workers route | Accessible to all | Should be Founder-only | HIGH |
| SBA route | Accessible to all | Should be Founder-only | HIGH |
| Recovery route | Accessible to all | Should be Founder-only | HIGH |
| Integration route | Accessible to all | Should be Founder-only | HIGH |

---

## 7. DOMAIN COVERAGE MATRIX

| Frozen Domain | Pages Exist | Route Exists | Sidebar Item | Status |
|---------------|-------------|--------------|--------------|--------|
| Overview | YES (as "Home") | `/guard` | YES (as "Home") | RENAME NEEDED |
| Activity | YES | `/guard/runs` | YES (as "Runs") | OK |
| Incidents | YES | `/guard/incidents` | YES | OK |
| Policies | YES (as "Limits") | `/guard/limits` | YES (as "Limits & Usage") | RENAME NEEDED |
| Logs | **NO** | **MISSING** | **MISSING** | **GAP** |

---

## 8. SIDEBAR ALIGNMENT

### Constitution Requirement

```
┌─────────────────────────────┐
│ CORE LENSES (Top)           │
│   Overview                  │
│   Activity                  │
│   Incidents                 │
│   Policies                  │
│   Logs                      │
├─────────────────────────────┤
│ CONNECTIVITY (Middle)       │
│   Integrations              │
│   API Keys                  │
├─────────────────────────────┤
│ ADMINISTRATION (Bottom)     │
│   Users                     │
│   Settings                  │
│   Billing                   │
│   Account                   │
└─────────────────────────────┘
```

### Current State

```
┌─────────────────────────────┐
│ NO SECTION SEPARATION       │
│   Home          → Overview  │
│   Runs          → Activity  │
│   Limits & Usage→ Policies  │
│   Incidents     → OK        │
│   API Keys      → OK        │
│   Settings      → OK        │
│   Account       → OK        │
│   Support       → REMOVE    │
│   [Logs MISSING]            │
│   [Integrations MISSING]    │
│   [Users MISSING]           │
│   [Billing at wrong route]  │
└─────────────────────────────┘
```

---

## 9. GAPS SUMMARY

| Gap ID | Description | Domain | Severity |
|--------|-------------|--------|----------|
| GAP-001 | Logs page missing | Logs | **HIGH** |
| GAP-002 | Integrations page missing | Connectivity | MEDIUM |
| GAP-003 | Users page missing | Administration | MEDIUM |
| GAP-004 | No sidebar section separation | Structure | LOW |
| GAP-005 | Support page not in constitution | Structure | MEDIUM |
| GAP-006 | Credits route misplaced | Administration | LOW |

---

## 10. TERMINOLOGY VIOLATIONS

| Current Term | Frozen Term | Location | Action |
|--------------|-------------|----------|--------|
| Home | Overview | Sidebar label | RENAME |
| Runs | Activity | Sidebar label | RENAME |
| Limits & Usage | Policies | Sidebar label | RENAME |
| Credits | Billing | Route name | MOVE |

---

## 11. AUDIT CONCLUSION

### Fit Score

| Category | Score | Notes |
|----------|-------|-------|
| Frozen Domains Present | 4/5 | Logs missing |
| Terminology Aligned | 1/5 | 4 renames needed |
| Sidebar Structure | 0/3 | No section separation |
| Jurisdiction Clean | 0/7 | 7 routes accessible cross-jurisdiction |

### Recommended Priority

1. **CRITICAL:** Add Logs page (GAP-001)
2. **HIGH:** Fix jurisdiction access controls
3. **MEDIUM:** Rename sidebar labels to frozen vocabulary
4. **MEDIUM:** Add sidebar section separation
5. **LOW:** Remove Support, add Integrations/Users

---

## CONSOLE CONSTITUTION CHECK

```
- Constitution loaded: YES
- Frozen domains respected: PARTIAL (4/5)
- Sidebar structure correct: NO (no sections, wrong labels)
- Jurisdiction boundaries maintained: NO (7 violations)
- Claude role acknowledged: Auditor and mapper, not designer
- Deviations identified: 10+ (see above)
- Human approval required: YES (before any changes)
```

---

**This is a read-only audit. No changes have been made. All deviations require human approval before action.**
