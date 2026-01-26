# Panel Execution Plan

**Status:** ACTIVE
**Created:** 2026-01-20
**Updated:** 2026-01-20
**Reference:** `CROSS_DOMAIN_DATA_ARCHITECTURE.md`, `PANEL_DATA_BINDING.md`

---

## 1. Objective

Populate panels with mock data across all 27 topics, ensuring cross-domain data consistency using shared identifiers.

### 1.1 Backend Gap Awareness

**IMPORTANT:** Backend gaps exist that affect full cross-domain functionality. See `CROSS_DOMAIN_DATA_ARCHITECTURE.md` Section 11 for details.

| Gap ID | Impact on Panels | Interim Strategy |
|--------|------------------|------------------|
| GAP-001 | Activity/Live won't show policy violations during run | Mock shows expected UX |
| GAP-002 | Runs won't stop on violation | Mock simulates stopped runs |
| GAP-003 | Logs won't highlight inflection point | Mock includes inflection_point field |
| GAP-004 | SOC2 export button won't work | Button disabled with "Coming Soon" |
| GAP-005 | Executive Debrief unavailable | Button disabled with "Coming Soon" |

**Strategy:** Mock data simulates the TARGET architecture to demonstrate expected UX while backend is remediated.

---

## 2. Execution Phases

### Phase 1: Foundation (Panel Registration)

**Goal:** Register all panel IDs in `ui_projection_lock.json`

| Domain | Subdomain | Topic | Panel ID | Status |
|--------|-----------|-------|----------|--------|
| Overview | Summary | Highlights | `OVR-SUM-HIGH` | PENDING |
| Overview | Summary | Decisions | `OVR-SUM-DEC` | PENDING |
| Activity | LLM Runs | Live | `ACT-LLM-LIVE` | PENDING |
| Activity | LLM Runs | Completed | `ACT-LLM-COMP` | PENDING |
| Activity | LLM Runs | Signals | `ACT-LLM-SIG` | PENDING |
| Incidents | Events | Active | `INC-EV-ACT` | PENDING |
| Incidents | Events | Resolved | `INC-EV-RES` | PENDING |
| Incidents | Events | Historical | `INC-EV-HIST` | PENDING |
| Policies | Governance | Active | `POL-GOV-ACT` | PENDING |
| Policies | Governance | Lessons | `POL-GOV-LES` | PENDING |
| Policies | Governance | Policy Library | `POL-GOV-LIB` | PENDING |
| Policies | Limits | Controls | `POL-LIM-CTR` | PENDING |
| Policies | Limits | Violations | `POL-LIM-VIO` | PENDING |
| Logs | Records | LLM Runs | `LOG-REC-LLM` | PENDING |
| Logs | Records | System Logs | `LOG-REC-SYS` | PENDING |
| Logs | Records | Audit Logs | `LOG-REC-AUD` | PENDING |
| Analytics | Insights | Cost Intelligence | `ANL-INS-COST` | PENDING |
| Analytics | Usage Stats | Policies Usage | `ANL-USG-POL` | PENDING |
| Analytics | Usage Stats | Productivity | `ANL-USG-PROD` | PENDING |
| Connectivity | Integrations | SDK Integration | `CON-INT-SDK` | PENDING |
| Connectivity | API | API Keys | `CON-API-KEYS` | PENDING |
| Account | Profile | Overview | `ACC-PRO-OVR` | PENDING |
| Account | Billing | Subscription | `ACC-BIL-SUB` | PENDING |
| Account | Billing | Invoices | `ACC-BIL-INV` | PENDING |
| Account | Team | Members | `ACC-TM-MEM` | PENDING |
| Account | Settings | Account Management | `ACC-SET-MGT` | PENDING |

**Deliverable:** 27 panels registered with unique IDs

---

### Phase 2: Mock Data Creation

**Goal:** Create consistent mock data set with cross-domain links

#### 2.1 Core Mock Entities

The mock data simulates the **expected flow** (target architecture):

```
Policy exists → Run starts → Run executes → Violation at step 3 → Run STOPPED → Incident created
```

```yaml
# Tenant
tenant:
  tenant_id: "TNT-DEMO-001"
  name: "Demo Organization"
  plan: "enterprise"

# Agent
agent:
  agent_id: "AGT-DEMO-001"
  tenant_id: "TNT-DEMO-001"
  name: "Code Review Agent"
  status: "active"

# PREREQUISITE: Global Policy (monitors all runs)
policies:
  - policy_id: "POL-DEMO-001"
    name: "Token Limit Policy"
    status: "active"
    rule_type: "token_limit"
    threshold: 10000
    scope: "all_runs"              # Monitors all runs
    incident_count: 2              # Has caught 2 violations

  - policy_id: "POL-DEMO-002"
    name: "Cost Cap Policy"
    status: "active"
    rule_type: "cost_limit"
    threshold_cents: 1000
    scope: "all_runs"
    incident_count: 0

# Runs (showing the violation flow)
runs:
  # Currently running (Activity/Live)
  - run_id: "RUN-DEMO-001"
    agent_id: "AGT-DEMO-001"
    status: "running"
    started_at: "2026-01-20T10:00:00Z"
    current_step: 2
    tokens_used: 5000              # Under limit (10000)

  # Completed successfully (Activity/Completed)
  - run_id: "RUN-DEMO-002"
    agent_id: "AGT-DEMO-001"
    status: "completed"
    started_at: "2026-01-20T09:00:00Z"
    completed_at: "2026-01-20T09:05:00Z"
    tokens_used: 8000              # Under limit

  # STOPPED BY POLICY (Activity/Completed - violation)
  - run_id: "RUN-DEMO-003"
    agent_id: "AGT-DEMO-001"
    status: "failed_policy"        # Stopped by policy
    started_at: "2026-01-20T08:00:00Z"
    stopped_at: "2026-01-20T08:00:30Z"  # Stopped at 30 seconds
    stopped_at_step: 3             # Step where violation occurred
    violation_policy_id: "POL-DEMO-001"
    tokens_used: 15000             # Exceeded limit (10000)

# Incidents (created when policy violated)
incidents:
  - incident_id: "INC-DEMO-001"
    source_run_id: "RUN-DEMO-003"  # Links to stopped run
    policy_id: "POL-DEMO-001"      # Policy that was violated
    tenant_id: "TNT-DEMO-001"
    status: "active"
    severity: "high"
    type: "token_limit_exceeded"
    violation_step: 3              # Step 3 caused violation
    violation_timestamp: "2026-01-20T08:00:30Z"
    description: "Run exceeded token limit of 10,000 at step 3"
    created_at: "2026-01-20T08:00:31Z"

  - incident_id: "INC-DEMO-002"
    source_run_id: "RUN-DEMO-004"  # Historical run
    policy_id: "POL-DEMO-001"
    tenant_id: "TNT-DEMO-001"
    status: "resolved"
    severity: "medium"
    type: "token_limit_exceeded"
    resolved_at: "2026-01-20T07:30:00Z"
    resolution: "Policy threshold increased"

# Traces (with inflection point for replay)
traces:
  - trace_id: "TRC-DEMO-001"
    run_id: "RUN-DEMO-003"
    incident_id: "INC-DEMO-001"
    tenant_id: "TNT-DEMO-001"
    total_duration_seconds: 30     # 30 second run
    total_steps: 4

    # INFLECTION POINT (GAP-003 - mock simulates expected behavior)
    violation_step_index: 3        # Step 3 was the violation
    violation_timestamp: "2026-01-20T08:00:30Z"
    violation_policy_id: "POL-DEMO-001"

    steps:
      - step: 1
        type: "input"
        timestamp: "2026-01-20T08:00:00Z"
        tokens: 500
        status: "ok"
      - step: 2
        type: "llm_call"
        timestamp: "2026-01-20T08:00:15Z"
        tokens: 5000
        status: "ok"
      - step: 3
        type: "llm_call"
        timestamp: "2026-01-20T08:00:30Z"
        tokens: 9500                # This pushed total over 10000
        status: "violation"         # INFLECTION POINT
        violation_reason: "Token limit exceeded"
      - step: 4
        type: "stopped"
        timestamp: "2026-01-20T08:00:30Z"
        status: "stopped_by_policy"

    # Export options (GAP-004, GAP-005 - buttons disabled in UI)
    exports_available:
      - format: "json"
        enabled: true
      - format: "csv"
        enabled: true
      - format: "soc2_pdf"
        enabled: false             # GAP-004: Not implemented
        disabled_reason: "Coming Soon"
      - format: "executive_debrief"
        enabled: false             # GAP-005: Not implemented
        disabled_reason: "Coming Soon"

# Cost Records
cost_records:
  - run_id: "RUN-DEMO-002"
    tenant_id: "TNT-DEMO-001"
    cost_cents: 150
    model: "claude-sonnet-4"
    input_tokens: 3000
    output_tokens: 5000

  - run_id: "RUN-DEMO-003"
    tenant_id: "TNT-DEMO-001"
    cost_cents: 450                # Cost incurred before stop
    model: "claude-sonnet-4"
    input_tokens: 5000
    output_tokens: 10000
```

#### 2.2 Cross-Domain Link Validation

| Source Entity | Target Entity | Link Field | Flow Step | Validated |
|--------------|---------------|------------|-----------|-----------|
| POL-DEMO-001 | (monitors) | scope: all_runs | 0. Prerequisite | PENDING |
| RUN-DEMO-003 | POL-DEMO-001 | violation_policy_id | 1. Run violates | PENDING |
| RUN-DEMO-003 | INC-DEMO-001 | source_run_id | 2. Incident created | PENDING |
| INC-DEMO-001 | POL-DEMO-001 | policy_id | 3. Policy recorded | PENDING |
| TRC-DEMO-001 | RUN-DEMO-003 | run_id | 4. Trace linked | PENDING |
| TRC-DEMO-001 | INC-DEMO-001 | incident_id | 4. Trace linked | PENDING |
| COST-DEMO-002 | RUN-DEMO-003 | run_id | 5. Cost attributed | PENDING |

#### 2.3 Mock Data Flow Visualization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MOCK DATA CROSS-DOMAIN FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   POL-DEMO-001 (Token Limit Policy)                                         │
│        │ scope: all_runs                                                    │
│        │ threshold: 10000                                                   │
│        │                                                                    │
│        ▼ monitors                                                           │
│   RUN-DEMO-003 (Activity/Live → Activity/Completed)                         │
│        │ tokens_used: 15000 (exceeded!)                                     │
│        │ stopped_at_step: 3                                                 │
│        │                                                                    │
│        ├──────────────────► INC-DEMO-001 (Incidents/Active)                 │
│        │                         │ violation_step: 3                        │
│        │                         │ severity: high                           │
│        │                         │                                          │
│        │                         └──► POL-DEMO-001.incident_count++         │
│        │                                                                    │
│        ├──────────────────► TRC-DEMO-001 (Logs/LLM Runs)                    │
│        │                         │ violation_step_index: 3 ⚡               │
│        │                         │ 30s timeline, inflection at 30s          │
│        │                         │                                          │
│        │                         ├──► Export: JSON ✅                       │
│        │                         ├──► Export: CSV ✅                        │
│        │                         ├──► Export: SOC2 PDF ❌ (GAP-004)         │
│        │                         └──► Export: Exec Debrief ❌ (GAP-005)     │
│        │                                                                    │
│        └──────────────────► COST-DEMO-002 (Analytics/Cost)                  │
│                                   cost_cents: 450                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 3: Panel Component Implementation

**Goal:** Create React components for each panel

#### 3.1 Component Structure

```
src/components/panels/
├── PanelContentRegistry.tsx    # Panel → Component mapping
├── common/
│   ├── LoadingSkeleton.tsx
│   ├── EmptyState.tsx
│   └── ErrorBoundary.tsx
├── overview/
│   ├── HighlightsPanel.tsx
│   └── DecisionsPanel.tsx
├── activity/
│   ├── LiveRunsPanel.tsx
│   ├── CompletedRunsPanel.tsx
│   └── SignalsPanel.tsx
├── incidents/
│   ├── ActiveIncidentsPanel.tsx
│   ├── ResolvedIncidentsPanel.tsx
│   └── HistoricalIncidentsPanel.tsx
├── policies/
│   ├── ActivePoliciesPanel.tsx
│   ├── LessonsPanel.tsx
│   ├── PolicyLibraryPanel.tsx
│   ├── ControlsPanel.tsx
│   └── ViolationsPanel.tsx
├── logs/
│   ├── LLMRunLogsPanel.tsx
│   ├── SystemLogsPanel.tsx
│   └── AuditLogsPanel.tsx
├── analytics/
│   ├── CostIntelligencePanel.tsx
│   ├── PoliciesUsagePanel.tsx
│   └── ProductivityPanel.tsx
├── connectivity/
│   ├── SDKIntegrationPanel.tsx
│   └── APIKeysPanel.tsx
└── account/
    ├── ProfileOverviewPanel.tsx
    ├── SubscriptionPanel.tsx
    ├── InvoicesPanel.tsx
    ├── TeamMembersPanel.tsx
    └── AccountManagementPanel.tsx
```

#### 3.2 Panel Registry

```typescript
// src/components/panels/PanelContentRegistry.tsx
export const PANEL_COMPONENTS: Record<string, React.ComponentType<PanelProps>> = {
  // Overview
  'OVR-SUM-HIGH': HighlightsPanel,
  'OVR-SUM-DEC': DecisionsPanel,

  // Activity
  'ACT-LLM-LIVE': LiveRunsPanel,
  'ACT-LLM-COMP': CompletedRunsPanel,
  'ACT-LLM-SIG': SignalsPanel,

  // Incidents
  'INC-EV-ACT': ActiveIncidentsPanel,
  'INC-EV-RES': ResolvedIncidentsPanel,
  'INC-EV-HIST': HistoricalIncidentsPanel,

  // Policies
  'POL-GOV-ACT': ActivePoliciesPanel,
  'POL-GOV-LES': LessonsPanel,
  'POL-GOV-LIB': PolicyLibraryPanel,
  'POL-LIM-CTR': ControlsPanel,
  'POL-LIM-VIO': ViolationsPanel,

  // Logs
  'LOG-REC-LLM': LLMRunLogsPanel,
  'LOG-REC-SYS': SystemLogsPanel,
  'LOG-REC-AUD': AuditLogsPanel,

  // Analytics
  'ANL-INS-COST': CostIntelligencePanel,
  'ANL-USG-POL': PoliciesUsagePanel,
  'ANL-USG-PROD': ProductivityPanel,

  // Connectivity
  'CON-INT-SDK': SDKIntegrationPanel,
  'CON-API-KEYS': APIKeysPanel,

  // Account
  'ACC-PRO-OVR': ProfileOverviewPanel,
  'ACC-BIL-SUB': SubscriptionPanel,
  'ACC-BIL-INV': InvoicesPanel,
  'ACC-TM-MEM': TeamMembersPanel,
  'ACC-SET-MGT': AccountManagementPanel,
};
```

---

### Phase 4: O-Level Rendering

**Goal:** Implement O-level aware rendering for each panel

#### 4.1 O-Level Component Mapping

| O-Level | Purpose | Component | Controls |
|---------|---------|-----------|----------|
| O1 | Summary | `<SummaryCard />` | Refresh |
| O2 | List | `<DataTable />` | Filter, Sort, Paginate |
| O3 | Detail | `<DetailView />` | Actions |
| O4 | Context | `<ContextTimeline />` | Navigate |
| O5 | Evidence | `<TraceViewer />` | Export |

#### 4.2 Default O-Level by Panel

| Panel Category | Default O-Level | Rationale |
|----------------|-----------------|-----------|
| Overview panels | O1 | Summary dashboards |
| Activity/Live | O2 | List of running items |
| Activity/Completed | O2 → O3 | List with detail drill-down |
| Incidents | O2 → O3 | List with detail drill-down |
| Policies | O2 → O3 | List with detail drill-down |
| Logs | O2 → O5 | List with evidence drill-down |
| Analytics | O1 → O2 | Summary with breakdown |
| Connectivity | O2 → O3 | List with detail |
| Account | O3 | Detail forms |

---

### Phase 5: Cross-Domain Navigation

**Goal:** Implement cross-domain links in panels

#### 5.1 Link Components

```typescript
// Cross-domain link from Incident to Run
<CrossDomainLink
  domain="Activity"
  subdomain="llm_runs"
  topic="completed"
  entityId="RUN-DEMO-003"
  label="View Run"
/>

// Cross-domain link from Incident to Policy
<CrossDomainLink
  domain="Policies"
  subdomain="governance"
  topic="active"
  entityId="POL-DEMO-001"
  label="View Policy"
/>
```

#### 5.2 Navigation Matrix

| From Panel | To Panel | Link Field | Action |
|------------|----------|------------|--------|
| INC-EV-ACT | ACT-LLM-COMP | source_run_id | View source run |
| INC-EV-ACT | POL-GOV-ACT | policy_id | View policy |
| INC-EV-ACT | LOG-REC-LLM | trace_id | View trace |
| ACT-LLM-COMP | INC-EV-ACT | run_id | View incidents |
| ACT-LLM-COMP | LOG-REC-LLM | run_id | View logs |
| ACT-LLM-COMP | ANL-INS-COST | run_id | View cost |
| POL-GOV-ACT | INC-EV-ACT | policy_id | View incidents |
| LOG-REC-LLM | ACT-LLM-COMP | run_id | View run |

---

### Phase 6: Mock Data Service

**Goal:** Create mock data service for development

#### 6.1 Service Structure

```typescript
// src/services/mockData/index.ts
export const MockDataService = {
  // Core entities
  getTenant: () => MOCK_TENANT,
  getAgent: (id: string) => MOCK_AGENTS[id],

  // Domain-specific
  getRuns: (filters: RunFilters) => filterMockRuns(MOCK_RUNS, filters),
  getIncidents: (filters: IncidentFilters) => filterMockIncidents(MOCK_INCIDENTS, filters),
  getPolicies: (filters: PolicyFilters) => filterMockPolicies(MOCK_POLICIES, filters),
  getTraces: (filters: TraceFilters) => filterMockTraces(MOCK_TRACES, filters),
  getCostRecords: (filters: CostFilters) => filterMockCosts(MOCK_COSTS, filters),

  // Cross-domain lookups
  getRunById: (runId: string) => MOCK_RUNS.find(r => r.run_id === runId),
  getIncidentsByRunId: (runId: string) => MOCK_INCIDENTS.filter(i => i.source_run_id === runId),
  getPolicyById: (policyId: string) => MOCK_POLICIES.find(p => p.policy_id === policyId),
  getTraceByRunId: (runId: string) => MOCK_TRACES.find(t => t.run_id === runId),
};
```

#### 6.2 Mock Data Files

```
src/services/mockData/
├── index.ts              # Service exports
├── tenant.mock.ts        # Tenant data
├── agents.mock.ts        # Agent data
├── runs.mock.ts          # Run data
├── incidents.mock.ts     # Incident data
├── policies.mock.ts      # Policy data
├── traces.mock.ts        # Trace data
├── costs.mock.ts         # Cost data
└── crossDomain.mock.ts   # Cross-domain validators
```

---

## 3. Execution Order

| Order | Phase | Deliverable | Dependencies |
|-------|-------|-------------|--------------|
| 1 | Foundation | Panel IDs in projection | None |
| 2 | Mock Data | Consistent mock entities | Phase 1 |
| 3 | Components | Panel React components | Phase 1, 2 |
| 4 | O-Levels | O-level rendering | Phase 3 |
| 5 | Navigation | Cross-domain links | Phase 3, 4 |
| 6 | Service | Mock data service | Phase 2 |

---

## 4. Success Criteria

### 4.1 Phase Completion Criteria

| Phase | Criteria |
|-------|----------|
| 1 | 27 panel IDs registered in ui_projection_lock.json |
| 2 | Mock data passes cross-domain validation |
| 3 | All 27 panels render without errors |
| 4 | O-level switching works for all panels |
| 5 | Cross-domain links navigate correctly |
| 6 | Mock service returns consistent data |

### 4.2 Cross-Domain Validation

```typescript
// Validation: All incidents reference valid runs
MOCK_INCIDENTS.forEach(incident => {
  const run = MOCK_RUNS.find(r => r.run_id === incident.source_run_id);
  assert(run !== undefined, `Incident ${incident.incident_id} references invalid run`);
});

// Validation: All incidents reference valid policies
MOCK_INCIDENTS.forEach(incident => {
  const policy = MOCK_POLICIES.find(p => p.policy_id === incident.policy_id);
  assert(policy !== undefined, `Incident ${incident.incident_id} references invalid policy`);
});

// Validation: All traces reference valid runs
MOCK_TRACES.forEach(trace => {
  const run = MOCK_RUNS.find(r => r.run_id === trace.run_id);
  assert(run !== undefined, `Trace ${trace.trace_id} references invalid run`);
});
```

---

## 5. Deferred (Out of Scope)

| Item | Reason | Future Phase |
|------|--------|--------------|
| Real backend binding | Mock data first | Post-visualization |
| SDSR capability observation | Panel UI must work first | Post-mock |
| AURORA registry integration | Binding strategy TBD | Post-evaluation |
| Real-time WebSocket updates | Core panels first | Future |

---

## 6. Backend Gap Impact on Panels

Reference: `CROSS_DOMAIN_DATA_ARCHITECTURE.md` Section 11

### 6.1 Panel-by-Panel Impact Assessment

| Panel ID | Panel Name | Gap Impact | Mock Workaround |
|----------|------------|------------|-----------------|
| `ACT-LLM-LIVE` | Live Runs | GAP-001: No policy check during run | Mock shows policy status column (simulated) |
| `ACT-LLM-COMP` | Completed Runs | GAP-002: Runs not stopped on violation | Mock shows `stopped_at_step` field |
| `INC-EV-ACT` | Active Incidents | None (works with post-hoc) | Full functionality |
| `INC-EV-RES` | Resolved Incidents | None | Full functionality |
| `POL-GOV-ACT` | Active Policies | None (counts work) | Full functionality |
| `POL-LIM-VIO` | Limit Violations | GAP-001: Violations post-hoc only | Mock shows expected UX |
| `LOG-REC-LLM` | LLM Run Logs | GAP-003: No inflection point | Mock highlights violation step |
| `LOG-REC-AUD` | Audit Logs | GAP-004, GAP-005: Export disabled | Buttons show "Coming Soon" |
| `ANL-INS-COST` | Cost Intelligence | None (cost attribution works) | Full functionality |

### 6.2 UI Components Affected by Gaps

| Component | Gap | Current State | Expected State |
|-----------|-----|---------------|----------------|
| `PolicyStatusBadge` (Activity/Live) | GAP-001 | Not shown | Shows "Checking..." during run |
| `StoppedAtStep` (Activity/Completed) | GAP-002 | N/A | Shows step where run stopped |
| `InflectionMarker` (Logs/Replay) | GAP-003 | Not highlighted | Red marker on violation step |
| `ExportSOC2Button` | GAP-004 | Disabled | Generates compliance PDF |
| `ExportDebriefButton` | GAP-005 | Disabled | Generates executive summary |

### 6.3 Mock Data Behavior vs Real Backend

| Scenario | Mock Behavior | Real Backend (Current) | Real Backend (Target) |
|----------|---------------|------------------------|----------------------|
| Run violates policy | Run stops at step 3 | Run completes, violation logged after | Run stops at step 3 |
| Trace replay | Highlights step 3 as violation | No highlighting | Highlights step 3 |
| SOC2 export | Button shows "Coming Soon" | Endpoint 404 | PDF generated |
| Policy during run | Shows "Checking" badge | No indication | Shows "Checking" badge |

---

## 7. References

| Document | Purpose |
|----------|---------|
| `CROSS_DOMAIN_DATA_ARCHITECTURE.md` | Data linking architecture |
| `PANEL_DATA_BINDING.md` | Panel → Topic → Data Shape |
| `PANEL_CREATION_PLAN.md` | Original panel plan |
| `CUSTOMER_CONSOLE_V2_CONSTITUTION.md` | Domain definitions |
| `ui_projection_lock.json` | Projection structure |

