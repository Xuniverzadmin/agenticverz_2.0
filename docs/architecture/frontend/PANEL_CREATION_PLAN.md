# Panel Creation & Project Plan — AI Governance Console

**Status:** DRAFT
**Created:** 2026-01-20
**Reference:** `CUSTOMER_CONSOLE_V2_CONSTITUTION.md`, `BACKEND_DOMAIN_INVENTORY.md`, `FRONTEND_PROJECTION_ARCHITECTURE.md`

---

## 1. Executive Summary

This document defines the panel creation strategy for the AI Governance Console. It determines:
1. **How many panels per topic** — based on O-level depth and data coverage
2. **Navigation patterns** — based on information depth (O1-O5)
3. **Priority and phasing** — based on user value and backend readiness

---

## 2. Panel Architecture Principles

### 2.1 O-Level (Epistemic Depth) Model

Every topic has panels at different depth levels:

| Order | Name | Purpose | Navigation Pattern |
|-------|------|---------|-------------------|
| **O1** | Summary | Scannable snapshot | Default view on topic load |
| **O2** | List | Collection of instances | Table/grid with filters |
| **O3** | Detail | Single instance explanation | Drill-down from O2 |
| **O4** | Context | Cross-domain impact | Sidebar panels, links |
| **O5** | Evidence | Raw proof/traces | Modal or dedicated view |

### 2.2 Panel Count Formula

```
Panels per Topic = O-levels × Data Objects

Where:
- O-levels: 1-5 (based on topic complexity)
- Data Objects: Distinct entity types in the topic
```

**Classification:**

| Topic Complexity | O-levels | Panel Range |
|-----------------|----------|-------------|
| **Simple** | O1-O2 | 2-3 panels |
| **Standard** | O1-O3 | 3-5 panels |
| **Complex** | O1-O5 | 5-8 panels |
| **Critical** | O1-O5 + Actions | 6-10 panels |

### 2.3 Panel ID Convention

```
{DOMAIN_PREFIX}-{SUBDOMAIN}-{TOPIC}-O{level}[-{variant}]

Examples:
- ACT-LLM-LIVE-O1      → Activity > LLM Runs > Live > Summary
- ACT-LLM-LIVE-O2      → Activity > LLM Runs > Live > List
- POL-GOV-ACT-O3       → Policies > Governance > Active > Detail
- INC-EV-ACT-O4-TL     → Incidents > Events > Active > Context (Timeline variant)
```

---

## 3. Domain-by-Domain Panel Plan

### 3.1 OVERVIEW Domain (Simple)

**Purpose:** System health at a glance — primarily O1-O2 depth.

| Subdomain | Topic | O-Levels | Panels | Notes |
|-----------|-------|----------|--------|-------|
| Summary | Highlights | O1-O2 | 3 | Pulse card, activity summary, incident summary |
| Summary | Decisions | O1-O2 | 3 | Decision queue, approval cards, action links |

**Panel Inventory:**

| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| OVR-SUM-HL-O1 | O1 | `PulseCard` | `/overview/pulse` |
| OVR-SUM-HL-O2 | O1 | `HighlightsSummary` | `/overview/highlights` |
| OVR-SUM-HL-O3 | O2 | `RecentActivityList` | `/overview/recent-activity` |
| OVR-SUM-DEC-O1 | O1 | `DecisionsSummary` | `/overview/decisions` |
| OVR-SUM-DEC-O2 | O2 | `ApprovalsQueue` | `/overview/approvals` |
| OVR-SUM-DEC-O3 | O2 | `ActionItems` | `/overview/decisions` |

**Total Panels:** 6

---

### 3.2 ACTIVITY Domain (Critical)

**Purpose:** Execution visibility — full O1-O5 depth for runs.

| Subdomain | Topic | O-Levels | Panels | Notes |
|-----------|-------|----------|--------|-------|
| LLM Runs | Live | O1-O4 | 5 | Real-time monitoring, no O5 (still running) |
| LLM Runs | Completed | O1-O5 | 8 | Full depth with trace evidence |
| LLM Runs | Signals | O1-O3 | 4 | Predictions, anomalies, risk alerts |

**Panel Inventory:**

**Live Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ACT-LLM-LIVE-O1 | O1 | `LiveRunsSummary` | `/activity/runs/live/count` |
| ACT-LLM-LIVE-O2 | O2 | `LiveRunsList` | `/activity/runs/live` |
| ACT-LLM-LIVE-O2-DIM | O2 | `LiveRunsByDimension` | `/activity/runs/live/by-dimension` |
| ACT-LLM-LIVE-O3 | O3 | `LiveRunDetail` | `/activity/runs/{id}` |
| ACT-LLM-LIVE-O4 | O4 | `WorkerHealth` | `/activity/health` |

**Completed Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ACT-LLM-COMP-O1 | O1 | `CompletedRunsSummary` | `/activity/runs/completed/summary` |
| ACT-LLM-COMP-O2 | O2 | `CompletedRunsList` | `/activity/runs/completed` |
| ACT-LLM-COMP-O2-DIM | O2 | `CompletedByDimension` | `/activity/runs/completed/by-dimension` |
| ACT-LLM-COMP-O3 | O3 | `RunDetail` | `/activity/runs/{id}` |
| ACT-LLM-COMP-O4 | O4 | `RunImpact` | Computed from run data |
| ACT-LLM-COMP-O5 | O5 | `RunTrace` | `/activity/runs/{id}/traces` |
| ACT-LLM-COMP-O5-STEPS | O5 | `TraceSteps` | `/traces/{id}/steps` |
| ACT-LLM-COMP-O5-COST | O5 | `CostBreakdown` | `/activity/runs/{id}/cost` |

**Signals Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ACT-LLM-SIG-O1 | O1 | `SignalsSummary` | `/activity/predictions/summary` |
| ACT-LLM-SIG-O2 | O2 | `SignalsList` | `/activity/signals` |
| ACT-LLM-SIG-O2-PRED | O2 | `PredictionsList` | `/activity/predictions` |
| ACT-LLM-SIG-O3 | O3 | `SignalDetail` | `/activity/anomalies` |

**Total Panels:** 17

---

### 3.3 INCIDENTS Domain (Critical)

**Purpose:** Failure understanding — full O1-O5 depth.

| Subdomain | Topic | O-Levels | Panels | Notes |
|-----------|-------|----------|--------|-------|
| Events | Active | O1-O4 | 6 | Real-time attention items |
| Events | Resolved | O1-O5 | 6 | Resolution details + evidence |
| Events | Historical | O1-O3 | 4 | Trends and patterns |

**Panel Inventory:**

**Active Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| INC-EV-ACT-O1 | O1 | `ActiveIncidentsSummary` | `/incidents/active` count |
| INC-EV-ACT-O2 | O2 | `ActiveIncidentsList` | `/incidents/active` |
| INC-EV-ACT-O2-SEV | O2 | `IncidentsBySeverity` | `/incidents/active/by-severity` |
| INC-EV-ACT-O3 | O3 | `IncidentDetail` | `/incidents/{id}` |
| INC-EV-ACT-O4-TL | O4 | `IncidentTimeline` | `/incidents/{id}/timeline` |
| INC-EV-ACT-O4-IMP | O4 | `IncidentImpact` | Computed |

**Resolved Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| INC-EV-RES-O1 | O1 | `ResolvedSummary` | `/incidents/resolved/stats` |
| INC-EV-RES-O2 | O2 | `ResolvedList` | `/incidents/resolved` |
| INC-EV-RES-O3 | O3 | `ResolutionDetail` | `/incidents/resolved/{id}` |
| INC-EV-RES-O4 | O4 | `ResolutionTimeline` | Resolution events |
| INC-EV-RES-O5 | O5 | `ResolutionEvidence` | Linked traces |
| INC-EV-RES-O5-ROOT | O5 | `RootCauseAnalysis` | Computed |

**Historical Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| INC-EV-HIST-O1 | O1 | `HistoricalSummary` | `/incidents/historical` summary |
| INC-EV-HIST-O2 | O2 | `HistoricalList` | `/incidents/historical` |
| INC-EV-HIST-O2-TREND | O2 | `IncidentTrends` | `/incidents/trends` |
| INC-EV-HIST-O3 | O3 | `PatternDetail` | `/incidents/patterns` |

**Total Panels:** 16

---

### 3.4 POLICIES Domain (Complex)

**Purpose:** Behavior governance — full depth with actions.

| Subdomain | Topic | O-Levels | Panels | Notes |
|-----------|-------|----------|--------|-------|
| Governance | Active | O1-O4 | 5 | Active policy management |
| Governance | Lessons | O1-O3 | 5 | Proposals with actions |
| Governance | Policy Library | O1-O2 | 3 | Templates and constraints |
| Limits | Controls | O1-O3 | 4 | Limit configuration |
| Limits | Violations | O1-O3 | 4 | Violation tracking |

**Panel Inventory:**

**Active Policies Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| POL-GOV-ACT-O1 | O1 | `ActivePoliciesSummary` | `/policies/active` count |
| POL-GOV-ACT-O2 | O2 | `ActivePoliciesList` | `/policies/active` |
| POL-GOV-ACT-O2-TYPE | O2 | `PoliciesByType` | `/policies/by-type` |
| POL-GOV-ACT-O3 | O3 | `PolicyDetail` | `/policies/{id}` |
| POL-GOV-ACT-O4 | O4 | `PolicyCoverage` | `/policies/coverage` |

**Lessons Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| POL-GOV-LES-O1 | O1 | `LessonsSummary` | `/policies/lessons/stats` |
| POL-GOV-LES-O2 | O2 | `LessonsList` | `/policies/lessons` |
| POL-GOV-LES-O2-PROP | O2 | `ProposalsList` | `/policy-proposals` |
| POL-GOV-LES-O3 | O3 | `LessonDetail` | `/policies/lessons/{id}` |
| POL-GOV-LES-O3-ACT | O3 | `ProposalActions` | Accept/Defer controls |

**Policy Library Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| POL-GOV-LIB-O1 | O1 | `LibrarySummary` | `/policies/library/templates` count |
| POL-GOV-LIB-O2 | O2 | `TemplatesList` | `/policies/library/templates` |
| POL-GOV-LIB-O2-ETH | O2 | `EthicalConstraints` | `/policies/library/ethical` |

**Controls Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| POL-LIM-CTR-O1 | O1 | `ControlsSummary` | `/policy-limits` count |
| POL-LIM-CTR-O2 | O2 | `ControlsList` | `/policy-limits` |
| POL-LIM-CTR-O3 | O3 | `ControlDetail` | `/policy-limits/{id}` |
| POL-LIM-CTR-O3-SIM | O3 | `ControlSimulator` | `/limits/simulate` |

**Violations Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| POL-LIM-VIO-O1 | O1 | `ViolationsSummary` | `/policies/violations` count |
| POL-LIM-VIO-O2 | O2 | `ViolationsList` | `/policies/violations` |
| POL-LIM-VIO-O2-LIM | O2 | `ViolationsByLimit` | `/policies/violations/by-limit` |
| POL-LIM-VIO-O3 | O3 | `ViolationDetail` | `/policies/violations/{id}` |

**Total Panels:** 21

---

### 3.5 LOGS Domain (Complex)

**Purpose:** Raw evidence trail — full O1-O5 depth.

| Subdomain | Topic | O-Levels | Panels | Notes |
|-----------|-------|----------|--------|-------|
| Records | LLM Runs | O1-O5 | 5 | Execution logs with traces |
| Records | System Logs | O1-O3 | 4 | Worker/infra events |
| Records | Audit Logs | O1-O5 | 5 | Governance actions |

**Panel Inventory:**

**LLM Runs Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| LOG-REC-LLM-O1 | O1 | `LlmLogsSummary` | `/logs/llm-runs` count |
| LOG-REC-LLM-O2 | O2 | `LlmLogsList` | `/logs/llm-runs` |
| LOG-REC-LLM-O3 | O3 | `LlmLogDetail` | `/logs/llm-runs/{id}` |
| LOG-REC-LLM-O4 | O4 | `LlmLogContext` | Cross-links |
| LOG-REC-LLM-O5 | O5 | `LlmLogTrace` | `/logs/llm-runs/{id}/trace` |

**System Logs Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| LOG-REC-SYS-O1 | O1 | `SystemLogsSummary` | `/logs/system` |
| LOG-REC-SYS-O2 | O2 | `SystemLogsList` | `/logs/system/entries` |
| LOG-REC-SYS-O3 | O3 | `SystemLogDetail` | `/logs/system/{id}` |
| LOG-REC-SYS-O4 | O4 | `SystemLogContext` | Worker correlation |

**Audit Logs Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| LOG-REC-AUD-O1 | O1 | `AuditLogsSummary` | `/logs/audit` count |
| LOG-REC-AUD-O2 | O2 | `AuditLogsList` | `/logs/audit` |
| LOG-REC-AUD-O2-ACT | O2 | `AuditByActor` | `/logs/audit/by-actor` |
| LOG-REC-AUD-O3 | O3 | `AuditDetail` | `/logs/audit/{id}` |
| LOG-REC-AUD-O5 | O5 | `AuditEvidence` | Evidence links |

**Total Panels:** 14

---

### 3.6 ANALYTICS Domain (Standard)

**Purpose:** Cost and usage intelligence — O1-O3 depth (insights, not raw data).

| Subdomain | Topic | O-Levels | Panels | Notes |
|-----------|-------|----------|--------|-------|
| Insights | Cost Intelligence | O1-O3 | 6 | Charts, trends, forecasts |
| Usage Statistics | Policies Usage | O1-O2 | 3 | Effectiveness metrics |
| Usage Statistics | Productivity | O1-O2 | 3 | Time saved, efficiency |

**Panel Inventory:**

**Cost Intelligence Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ANA-INS-CST-O1 | O1 | `CostSummary` | `/analytics/cost/summary` |
| ANA-INS-CST-O2-MOD | O2 | `CostByModel` | `/analytics/cost/by-model` |
| ANA-INS-CST-O2-FEA | O2 | `CostByFeature` | `/analytics/cost/by-feature` |
| ANA-INS-CST-O2-TRD | O2 | `CostTrend` | `/analytics/cost/trend` |
| ANA-INS-CST-O3-ANO | O3 | `CostAnomalies` | `/analytics/cost/anomalies` |
| ANA-INS-CST-O3-FOR | O3 | `CostForecast` | `/analytics/cost/forecast` |

**Policies Usage Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ANA-USG-POL-O1 | O1 | `PolicyUsageSummary` | `/analytics/policies/usage` |
| ANA-USG-POL-O2 | O2 | `PolicyEffectiveness` | `/analytics/policies/effectiveness` |
| ANA-USG-POL-O2-COV | O2 | `PolicyCoverage` | `/analytics/policies/coverage` |

**Productivity Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ANA-USG-PRD-O1 | O1 | `ProductivitySummary` | `/analytics/productivity/saved-time` |
| ANA-USG-PRD-O2 | O2 | `EfficiencyGains` | `/analytics/productivity/efficiency` |
| ANA-USG-PRD-O2-TRD | O2 | `ProductivityTrend` | `/analytics/productivity/trend` |

**Total Panels:** 12

---

### 3.7 CONNECTIVITY Domain (Simple)

**Purpose:** Integration and API access — O1-O2 depth with actions.

| Subdomain | Topic | O-Levels | Panels | Notes |
|-----------|-------|----------|--------|-------|
| Integrations | SDK Integration | O1-O2 | 3 | Setup status, providers |
| API | API Keys | O1-O2 | 3 | Key management |

**Panel Inventory:**

**SDK Integration Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| CON-INT-SDK-O1 | O1 | `IntegrationStatus` | `/connectivity/integrations` |
| CON-INT-SDK-O2 | O2 | `SdkSetupWizard` | `/connectivity/integrations/sdk` |
| CON-INT-SDK-O2-PROV | O2 | `ProvidersList` | `/connectivity/providers` |

**API Keys Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| CON-API-KEY-O1 | O1 | `ApiKeysSummary` | `/connectivity/api-keys` count |
| CON-API-KEY-O2 | O2 | `ApiKeysList` | `/connectivity/api-keys` |
| CON-API-KEY-O2-ACT | O2 | `ApiKeyActions` | Create/Rotate/Revoke |

**Total Panels:** 6

---

### 3.8 ACCOUNT Domain (Standard)

**Purpose:** Account management — O1-O2 depth with actions.

| Subdomain | Topic | O-Levels | Panels | Notes |
|-----------|-------|----------|--------|-------|
| Profile | Overview | O1-O2 | 2 | Org profile, contacts |
| Billing | Subscription | O1-O2 | 2 | Plan, usage |
| Billing | Invoices | O1-O2 | 2 | Invoice list, detail |
| Team | Members | O1-O2 | 3 | Admin-only RBAC |
| Settings | Account Management | O1-O2 | 2 | Support, settings |

**Panel Inventory:**

**Profile Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ACC-PRO-OV-O1 | O1 | `ProfileSummary` | `/accounts/profile` |
| ACC-PRO-OV-O2 | O2 | `ProfileEdit` | PUT `/accounts/profile` |

**Subscription Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ACC-BIL-SUB-O1 | O1 | `PlanSummary` | `/accounts/billing/plan` |
| ACC-BIL-SUB-O2 | O2 | `UsageSummary` | `/accounts/billing/usage` |

**Invoices Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ACC-BIL-INV-O1 | O1 | `InvoicesSummary` | `/accounts/billing/invoices` count |
| ACC-BIL-INV-O2 | O2 | `InvoicesList` | `/accounts/billing/invoices` |

**Members Topic (Admin):**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ACC-USR-MEM-O1 | O1 | `MembersSummary` | `/accounts/users` count |
| ACC-USR-MEM-O2 | O2 | `MembersList` | `/accounts/users` |
| ACC-USR-MEM-O2-INV | O2 | `InvitationsList` | `/accounts/invitations` |

**Account Management Topic:**
| Panel ID | O-Level | Component | Data Source |
|----------|---------|-----------|-------------|
| ACC-MGT-SET-O1 | O1 | `SupportInfo` | `/accounts/support` |
| ACC-MGT-SET-O2 | O2 | `SupportTickets` | `/accounts/support/tickets` |

**Total Panels:** 11

---

## 4. Panel Summary

### 4.1 Total Panel Count by Domain

| Domain | Topics | Panels | Complexity |
|--------|--------|--------|------------|
| Overview | 2 | 6 | Simple |
| Activity | 3 | 17 | Critical |
| Incidents | 3 | 16 | Critical |
| Policies | 5 | 21 | Complex |
| Logs | 3 | 14 | Complex |
| Analytics | 3 | 12 | Standard |
| Connectivity | 2 | 6 | Simple |
| Account | 5 | 11 | Standard |
| **TOTAL** | **26** | **103** | - |

### 4.2 Panels by O-Level

| O-Level | Purpose | Count | % of Total |
|---------|---------|-------|------------|
| O1 | Summary | 26 | 25% |
| O2 | List | 42 | 41% |
| O3 | Detail | 21 | 20% |
| O4 | Context | 8 | 8% |
| O5 | Evidence | 6 | 6% |

---

## 5. Navigation Architecture

### 5.1 Default View per Topic

Every topic loads its **O1 panel** by default. O1 panels contain:
- Summary statistics
- Status indicators
- Quick navigation to O2

### 5.2 Navigation Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                    NAVIGATION FLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  O1 (Summary)                                               │
│    │                                                        │
│    ├──→ Click "View All" → O2 (List)                        │
│    │                        │                               │
│    │                        ├──→ Click Row → O3 (Detail)    │
│    │                        │                  │            │
│    │                        │                  ├──→ O4 (Context)
│    │                        │                  │    (sidebar)
│    │                        │                  │            │
│    │                        │                  └──→ O5 (Evidence)
│    │                        │                       (modal/tab)
│    │                        │                               │
│    └──→ Click Metric → O2 (Filtered by dimension)           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Component Patterns by O-Level

| O-Level | Component Type | Navigation Element |
|---------|----------------|-------------------|
| O1 | `SummaryCard`, `MetricCard` | "View All" button |
| O2 | `DataTable`, `FilterBar` | Row click → O3 |
| O3 | `DetailView`, `TabGroup` | Sidebar → O4, Tab → O5 |
| O4 | `ContextSidebar`, `LinkList` | Cross-domain links |
| O5 | `CodeBlock`, `Timeline`, `JsonViewer` | Download, copy |

### 5.4 URL Strategy

```
/precus/{domain}?subdomain={sd}&topic={t}&view={o-level}&id={entity_id}

Examples:
/precus/activity                           → O1 default
/precus/activity?topic=completed           → O1 of Completed topic
/precus/activity?topic=completed&view=list → O2 list
/precus/activity?topic=completed&view=detail&id=run_123 → O3 detail
```

---

## 6. Project Phases

### Phase 1: Foundation (O1 Views) — Week 1-2

**Goal:** All 26 O1 summary panels working.

| Domain | O1 Panels | Priority |
|--------|-----------|----------|
| Overview | 2 | P0 |
| Activity | 3 | P0 |
| Incidents | 3 | P0 |
| Policies | 5 | P1 |
| Logs | 3 | P1 |
| Analytics | 3 | P2 |
| Connectivity | 2 | P2 |
| Account | 5 | P2 |

**Deliverables:**
- [ ] All O1 panels render with real data
- [ ] Navigation works for all topics
- [ ] Empty state UX for missing data

### Phase 2: Lists (O2 Views) — Week 3-4

**Goal:** All 42 O2 list panels with filters.

| Domain | O2 Panels | Priority |
|--------|-----------|----------|
| Activity | 6 | P0 |
| Incidents | 5 | P0 |
| Policies | 8 | P1 |
| Logs | 5 | P1 |
| Analytics | 5 | P2 |
| Overview | 3 | P2 |
| Connectivity | 4 | P2 |
| Account | 6 | P2 |

**Deliverables:**
- [ ] Shared `DataTable` component
- [ ] Shared `FilterBar` component
- [ ] Pagination working
- [ ] URL-synced filters

### Phase 3: Details (O3 Views) — Week 5-6

**Goal:** All 21 O3 detail panels.

| Domain | O3 Panels | Priority |
|--------|-----------|----------|
| Activity | 4 | P0 |
| Incidents | 4 | P0 |
| Policies | 5 | P1 |
| Logs | 4 | P1 |
| Analytics | 4 | P2 |

**Deliverables:**
- [ ] Shared `DetailView` component
- [ ] Drill-down navigation from O2
- [ ] Breadcrumb updates

### Phase 4: Context & Evidence (O4-O5) — Week 7-8

**Goal:** 14 deep-dive panels for critical paths.

| Domain | O4/O5 Panels | Priority |
|--------|--------------|----------|
| Activity | 5 | P0 |
| Incidents | 5 | P1 |
| Logs | 4 | P1 |

**Deliverables:**
- [ ] Context sidebar component
- [ ] Evidence modal/tab
- [ ] Cross-domain links working
- [ ] Trace viewer

---

## 7. Shared Components

### 7.1 Required Components

| Component | Used By | Phase |
|-----------|---------|-------|
| `SummaryCard` | O1 panels | 1 |
| `MetricCard` | O1 panels | 1 |
| `DataTable` | O2 panels | 2 |
| `FilterBar` | O2 panels | 2 |
| `Pagination` | O2 panels | 2 |
| `DetailView` | O3 panels | 3 |
| `TabGroup` | O3 panels | 3 |
| `ContextSidebar` | O4 panels | 4 |
| `JsonViewer` | O5 panels | 4 |
| `Timeline` | O4/O5 panels | 4 |
| `EmptyState` | All panels | 1 |
| `LoadingSkeleton` | All panels | 1 |
| `StatusBadge` | Multiple | 1 |

### 7.2 Action Components

| Component | Used By | Phase |
|-----------|---------|-------|
| `ApprovalButton` | Policies | 2 |
| `AcknowledgeButton` | Incidents | 2 |
| `CreateKeyForm` | Connectivity | 2 |
| `InviteUserForm` | Account | 3 |

---

## 8. Success Criteria

### 8.1 Phase 1 Complete When:
- [ ] All 26 O1 panels render
- [ ] Navigation between topics works
- [ ] No console errors
- [ ] Data loads from real APIs

### 8.2 Phase 2 Complete When:
- [ ] All 42 O2 panels render
- [ ] Filters work (date, status, type)
- [ ] Pagination works
- [ ] Row click navigates to O3

### 8.3 Phase 3 Complete When:
- [ ] All 21 O3 panels render
- [ ] Detail view shows complete entity
- [ ] Actions work (acknowledge, approve, etc.)

### 8.4 Phase 4 Complete When:
- [ ] All 14 O4/O5 panels render
- [ ] Cross-domain links work
- [ ] Evidence traces display correctly
- [ ] SDSR validation passes

### 8.5 Full Build Complete When:
- [ ] 103 panels implemented
- [ ] All O-levels navigable
- [ ] Performance < 3s load
- [ ] SDSR E2E tests pass

---

## 9. References

| Document | Purpose |
|----------|---------|
| `CUSTOMER_CONSOLE_V2_CONSTITUTION.md` | Domain/subdomain definitions |
| `BACKEND_DOMAIN_INVENTORY.md` | API endpoint mapping |
| `FRONTEND_PROJECTION_ARCHITECTURE.md` | Projection source |
| `FRONTEND_L1_BUILD_PLAN.md` | Build strategy |
| `AURORA_L2_DOMAIN_INTENT_REGISTRY.yaml` | Panel ID patterns |

---

**This plan is the execution guide for panel creation.**

**Build O1 first. Add depth progressively. Test with SDSR.**
