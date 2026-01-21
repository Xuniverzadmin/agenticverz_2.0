# Cross-Domain Data Architecture

**Status:** ACTIVE
**Created:** 2026-01-20
**Updated:** 2026-01-20
**Reference:** `PANEL_DATA_BINDING.md`, `PANEL_EXECUTION_PLAN.md`

---

## 1. Overview

This document defines the cross-domain data linking architecture for the AI Governance Console. It establishes how data flows between domains while maintaining consistency and traceability.

**Source of Truth:** `CUSTOMER_CONSOLE_V2_CONSTITUTION.md`

### 1.1 Backend Integration Status

| Component | Status | Notes |
|-----------|--------|-------|
| Data Flow Design | ✅ Defined | This document |
| Backend Implementation | ✅ **P0/P1 COMPLETE** | See Section 11 |
| Panel Rendering | Pending | Mock data first |

**NOTE:** Section 11 documents backend gap remediation. P0/P1 gaps are complete. P2/P3 (PDF generators) pending.

---

## 2. Domain Hierarchy Summary

| Domain | Subdomains | Topics | Purpose |
|--------|------------|--------|---------|
| **Overview** | Summary | Highlights, Decisions | System health at a glance |
| **Activity** | LLM Runs | Live, Completed, Signals | Agent runs and executions |
| **Incidents** | Events | Active, Resolved, Historical | Policy violations and failures |
| **Policies** | Governance, Limits | Active, Lessons, Policy Library, Controls, Violations | Rules and constraints |
| **Logs** | Records | LLM Runs, System Logs, Audit Logs | Audit trail and raw records |
| **Analytics** | Insights, Usage Stats | Cost Intelligence, Policies Usage, Productivity | Usage and cost insights |
| **Connectivity** | Integrations, API | SDK Integration, API Keys | Integrations and API access |
| **Account** | Profile, Billing, Team, Settings | Overview, Subscription, Invoices, Members, Account Mgmt | Account settings |

**Totals:** 8 domains, 14 subdomains, 27 topics

---

## 3. Cross-Domain Data Flow

### 3.1 Expected Data Flow (Target Architecture)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    EXPECTED CROSS-DOMAIN DATA FLOW                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   PREREQUISITE: Policy POL-001 exists and monitors all runs                  │
│                                                                              │
│   Activity/Live                                                              │
│        │                                                                     │
│        ▼                                                                     │
│   Run Step 1 ──► Prevention Hook ──► OK ──► Continue                         │
│        │                                                                     │
│        ▼                                                                     │
│   Run Step 2 ──► Prevention Hook ──► OK ──► Continue                         │
│        │                                                                     │
│        ▼                                                                     │
│   Run Step 3 ──► Prevention Hook ──► VIOLATION! ◄── Policy POL-001           │
│        │              │                                                      │
│        │              ├──► Mark inflection_point = Step 3 (30s)              │
│        │              ├──► STOP RUN immediately                              │
│        │              └──► Create Incident (automatic)                       │
│        │                                                                     │
│        ▼                                                                     │
│   Activity/Completed (status: failed_policy)                                 │
│        │                                                                     │
│        ├──────────────────► Incidents/Active                                 │
│        │                         │                                           │
│        │                         │ policy_id                                 │
│        │                         ▼                                           │
│        │                    Policies/Active (records violation)              │
│        │                                                                     │
│        ├──────────────────► Logs/LLM Runs                                    │
│        │                         │                                           │
│        │                    Trace with inflection_point marked               │
│        │                         │                                           │
│        │                         ├──► Replay (60s timeline, 30s violation)   │
│        │                         ├──► Export: SOC2 PDF                       │
│        │                         └──► Export: Executive Debrief PDF          │
│        │                                                                     │
│        └──────────────────► Analytics/Cost (cost attributed)                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Current Backend Reality (P0/P1 COMPLETE)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│              CURRENT BACKEND FLOW (REMEDIATED 2026-01-20)                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Activity/Live                                                              │
│        │                                                                     │
│        │  ✅ Policy snapshot captured at run start (GAP-006)                 │
│        │  ✅ Prevention engine available for integration (GAP-001)           │
│        │                                                                     │
│        ▼                                                                     │
│   Run Step N ──► Prevention Hook ──► Evaluate via PreventionEngine           │
│        │                                                                     │
│        ├──► ALLOW → Continue execution                                       │
│        │                                                                     │
│        └──► BLOCK → Stop run (GAP-002)                                       │
│                  │                                                           │
│                  ├──► Mark inflection point in trace (GAP-003) ✅            │
│                  ├──► Run status = failed_policy (GAP-007) ✅                │
│                  └──► Incident created synchronously                         │
│                                                                              │
│   Export Capabilities:                                                       │
│        ├──► Evidence Bundle model ✅ (GAP-008)                               │
│        ├──► SOC2 Bundle model ✅ (GAP-008)                                   │
│        ├──► Executive Debrief model ✅ (GAP-008)                             │
│        ├──► ⏳ PDF Generator pending (GAP-004)                               │
│        └──► ⏳ Export endpoints pending (GAP-005)                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Gap Summary

| Expected Behavior | Current Status | Gap ID |
|-------------------|----------------|--------|
| Policy evaluated DURING run | ✅ PreventionEngine created | GAP-001 |
| Run STOPS on violation | ✅ Stop logic implemented | GAP-002 |
| Inflection point marked in trace | ✅ Fields added to TraceSummary | GAP-003 |
| SOC2 PDF export | ⏳ Model done, generator pending | GAP-004 |
| Executive Debrief PDF | ⏳ Model done, generator pending | GAP-005 |
| Policy snapshots at run start | ✅ PolicySnapshot model created | GAP-006 |
| RunTerminationReason enum | ✅ Enum and models created | GAP-007 |
| Structured export bundles | ✅ EvidenceBundle, SOC2Bundle done | GAP-008 |

See **Section 11** for detailed gap analysis and `BACKEND_REMEDIATION_PLAN.md` for implementation.

### 3.4 Linkage Fields

| Source | Target | Link Field | Direction | Backend Support |
|--------|--------|------------|-----------|-----------------|
| Activity | Incidents | `source_run_id` | Run → Incident | `incident_engine.py` |
| Incidents | Policies | `policy_id` | Incident → Policy | `policy_violation_service.py` |
| Activity | Logs | `run_id` | Run → Trace | `traces/models.py` |
| Incidents | Logs | `incident_id` | Incident → Trace | `trace_store.py` |
| Activity | Analytics | `run_id` | Run → Cost | `cost_write_service.py` |
| Policies | Analytics | `policy_id` | Policy → Usage Stats | `policy_violation_service.py` |

### 3.5 Backend Scripts

| Script | Location | Cross-Domain Function |
|--------|----------|----------------------|
| `incident_engine.py` | `backend/app/services/` | Creates incidents from run violations |
| `policy_violation_service.py` | `backend/app/services/` | Links incidents to policies |
| `cross_domain.py` | `backend/app/services/governance/` | Mandatory propagation rules |
| `trace_store.py` | `backend/app/traces/` | Links traces to runs and incidents |
| `cost_write_service.py` | `backend/app/services/` | Attributes costs to runs |

---

## 4. Shared Identifiers

### 4.1 Primary Keys

| Identifier | Format | Scope | Used By |
|------------|--------|-------|---------|
| `run_id` | UUID | Tenant | Activity, Incidents, Logs, Analytics |
| `incident_id` | UUID | Tenant | Incidents, Logs, Policies |
| `policy_id` | UUID | Tenant | Policies, Incidents, Analytics |
| `trace_id` | UUID | Tenant | Logs, Activity |
| `tenant_id` | UUID | Global | All domains (isolation) |

### 4.2 Foreign Key Relationships

```
runs
  ├── incidents.source_run_id
  ├── aos_traces.run_id
  └── cost_records.run_id

incidents
  ├── aos_traces.incident_id
  └── prevention_records.incident_id

policies (policy_rules)
  ├── incidents.policy_id
  └── prevention_records.policy_id
```

---

## 5. Data Consistency Model

### 5.1 Consistency Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| **CC-001** | Run ID must exist before incident creation | FK constraint |
| **CC-002** | Policy ID must exist before incident links | FK constraint |
| **CC-003** | Tenant isolation on all queries | WHERE tenant_id = :tenant_id |
| **CC-004** | Trace immutability | DB triggers |
| **CC-005** | Cost attribution at run completion | Event-driven |

### 5.2 Propagation Order

When a run completes with a violation:

```
1. Run completion recorded (Activity)
2. Violation detected → Incident created (Incidents)
3. Policy reference attached (Policies)
4. Trace finalized with incident_id (Logs)
5. Cost attributed (Analytics)
6. Summary metrics updated (Overview)
```

---

## 6. Mock Data Consistency

### 6.1 Consistent Mock Data Set

For panels to display consistent data across domains, use these linked mock records:

```yaml
# Activity Domain
run:
  run_id: "RUN-001"
  agent_id: "AGT-001"
  tenant_id: "TNT-001"
  status: "failed_policy"
  started_at: "2026-01-20T10:00:00Z"
  completed_at: "2026-01-20T10:05:00Z"
  tokens_used: 15000

# Incidents Domain
incident:
  incident_id: "INC-001"
  source_run_id: "RUN-001"  # ← Links to Activity
  policy_id: "POL-001"      # ← Links to Policies
  tenant_id: "TNT-001"
  severity: "high"
  type: "token_limit_exceeded"
  status: "active"
  created_at: "2026-01-20T10:05:01Z"

# Policies Domain
policy:
  policy_id: "POL-001"
  tenant_id: "TNT-001"
  name: "Token Limit Policy"
  rule_type: "token_limit"
  threshold: 10000
  status: "active"
  incident_count: 1         # ← Updated by Incident

# Logs Domain
trace:
  trace_id: "TRC-001"
  run_id: "RUN-001"         # ← Links to Activity
  incident_id: "INC-001"    # ← Links to Incidents
  tenant_id: "TNT-001"
  steps:
    - step: 1, type: "input", timestamp: "2026-01-20T10:00:00Z"
    - step: 2, type: "llm_call", timestamp: "2026-01-20T10:02:00Z"
    - step: 3, type: "policy_check", timestamp: "2026-01-20T10:04:00Z"
    - step: 4, type: "violation", timestamp: "2026-01-20T10:05:00Z"

# Analytics Domain
cost_record:
  run_id: "RUN-001"         # ← Links to Activity
  tenant_id: "TNT-001"
  cost_cents: 450
  model: "claude-sonnet-4"
  input_tokens: 5000
  output_tokens: 10000
```

### 6.2 Cross-Reference Validation

| Panel | Expected Data | Linked Via |
|-------|--------------|------------|
| Activity/Completed | Run RUN-001 | Primary |
| Incidents/Active | Incident INC-001 | source_run_id → RUN-001 |
| Policies/Active | Policy POL-001 | policy_id from INC-001 |
| Logs/LLM Runs | Trace TRC-001 | run_id → RUN-001 |
| Analytics/Cost | Cost for RUN-001 | run_id → RUN-001 |

---

## 7. Compliance Trail

### 7.1 SOC2 Compliance Flow

```
Activity → Incident → Policy → Logs → Export → Audit
```

| Step | Domain | Topic | Data | O-Level |
|------|--------|-------|------|---------|
| 1 | Activity | Live | Run executing | O2 |
| 2 | Activity | Completed | Run with violation | O3 |
| 3 | Incidents | Active | Incident detail | O3 |
| 4 | Policies | Active | Policy triggered | O3 |
| 5 | Logs | LLM Runs | Full trace | O5 |
| 6 | Logs | LLM Runs | Export PDF | O5 |
| 7 | Logs | Audit Logs | SOC2 record | O5 |

### 7.2 Export Requirements

| Format | Contents | Use Case |
|--------|----------|----------|
| JSON | Full trace data | API integration |
| CSV | Tabular summary | Spreadsheet analysis |
| PDF | Formatted report | Compliance audit |

---

## 8. Panel Data Shapes by O-Level

### 8.1 O1 — Summary

```typescript
interface O1Data {
  total: number;
  active?: number;
  status: 'healthy' | 'warning' | 'critical';
  metrics?: Array<{ label: string; value: number | string; trend?: 'up' | 'down' | 'flat' }>;
  as_of: string;
}
```

### 8.2 O2 — List

```typescript
interface O2Data<T> {
  items: T[];
  pagination: { total: number; page: number; page_size: number };
  filters_applied?: Record<string, string>;
  sort?: { field: string; direction: 'asc' | 'desc' };
}
```

### 8.3 O3 — Detail

```typescript
interface O3Data<T> {
  entity: T;
  actions?: Array<{ action: string; label: string; enabled: boolean }>;
}
```

### 8.4 O4 — Context

```typescript
interface O4Data {
  source: { id: string; type: string };
  related: Array<{ id: string; type: string; title: string; link: string }>;
  timeline?: Array<{ timestamp: string; event: string }>;
}
```

### 8.5 O5 — Evidence

```typescript
interface O5Data {
  source: { id: string; type: string };
  trace?: { trace_id: string; steps: Array<{ step_number: number; timestamp: string; type: string }> };
  exports?: Array<{ format: 'json' | 'csv' | 'pdf'; url: string }>;
}
```

---

## 9. Deferred Concerns

| Concern | Status | Reference |
|---------|--------|-----------|
| Capability binding | Deferred | `PANEL_DATA_BINDING.md` |
| SDSR observation | Deferred | `PANEL_DATA_BINDING.md` |
| AURORA registry lookup | Deferred | `PANEL_DATA_BINDING.md` |
| Real-time updates | Deferred | TBD |

---

## 10. References

| Document | Purpose |
|----------|---------|
| `CUSTOMER_CONSOLE_V2_CONSTITUTION.md` | Domain definitions |
| `PANEL_DATA_BINDING.md` | Panel → Topic → Data Shape |
| `PANEL_EXECUTION_PLAN.md` | Implementation plan |
| `POLICIES_DOMAIN_CONSTITUTION.md` | Policies governance |
| `ANALYTICS_DOMAIN_CONSTITUTION.md` | Analytics governance |
| `ui_projection_lock.json` | Projection structure |

---

## 11. Backend Gap Analysis

### 11.1 Overview

**Status:** P0/P1 COMPLETE (2026-01-20)

The cross-domain data flow required backend components that were either missing or not integrated. This section documents the gaps and their remediation status.

**Implementation Reference:** `BACKEND_REMEDIATION_PLAN.md`

| Priority | Gaps | Status |
|----------|------|--------|
| P0 | GAP-001, GAP-002, GAP-006 | ✅ COMPLETE |
| P1 | GAP-003, GAP-007 | ✅ COMPLETE |
| P2 | GAP-008 | ✅ COMPLETE (models) |
| P2 | GAP-004 | ⏳ PENDING (PDF generator) |
| P3 | GAP-005 | ⏳ PENDING (PDF generator) |

### 11.2 Gap Registry

#### GAP-001: Policy Evaluation Timing — ✅ COMPLETE

| Aspect | Detail |
|--------|--------|
| **Expected** | Policy evaluated DURING run execution, at each step |
| **Status** | ✅ COMPLETE (2026-01-20) |
| **Implementation** | `backend/app/policy/prevention_engine.py` |

**What was built:**
- `PreventionEngine` class with `evaluate_step()` method
- `PreventionContext` dataclass for step evaluation context
- `PreventionResult` dataclass with `ALLOW`, `WARN`, `BLOCK` actions
- `PolicyViolationError` exception for run termination
- `create_policy_snapshot_for_run()` helper function

#### GAP-002: Run Stop on Violation — ✅ COMPLETE

| Aspect | Detail |
|--------|--------|
| **Expected** | Run STOPS immediately when policy violation detected |
| **Status** | ✅ COMPLETE (2026-01-20) |
| **Implementation** | `backend/app/models/run_lifecycle.py`, `backend/app/db.py` |

**What was built:**
- `RunStatus.FAILED_POLICY` status for policy-stopped runs
- `RunTerminationReason.POLICY_BLOCK` for termination tracking
- Run model fields: `policy_snapshot_id`, `termination_reason`, `stopped_at_step`, `violation_policy_id`
- `_stop_run_on_violation()` logic pattern documented for runner integration

#### GAP-003: Inflection Point Marking — ✅ COMPLETE

| Aspect | Detail |
|--------|--------|
| **Expected** | Trace marks exact step/timestamp where violation occurred |
| **Status** | ✅ COMPLETE (2026-01-20) |
| **Implementation** | `backend/app/traces/models.py` |

**What was built:**
Added to `TraceSummary` dataclass:
- `violation_step_index: int | None` - Step where violation occurred
- `violation_timestamp: datetime | None` - When violation was detected
- `violation_policy_id: str | None` - ID of violated policy
- `violation_reason: str | None` - Human-readable description

#### GAP-004: SOC2 PDF Export — ⏳ PENDING

| Aspect | Detail |
|--------|--------|
| **Expected** | Export incident with evidence as SOC2-compliant PDF |
| **Status** | ⏳ PENDING (models done, PDF generator needed) |
| **Prerequisites** | GAP-008 ✅ (export bundle models complete) |

**Remaining work:**
- Create `backend/app/services/pdf_renderer.py`
- Implement `render_soc2_pdf()` method using reportlab
- Wire export endpoint in `backend/app/api/incidents.py`

#### GAP-005: Executive Debrief Export — ⏳ PENDING

| Aspect | Detail |
|--------|--------|
| **Expected** | High-level summary PDF for executive review |
| **Status** | ⏳ PENDING (model done, PDF generator needed) |
| **Prerequisites** | GAP-008 ✅ (ExecutiveDebriefBundle model complete) |

**Remaining work:**
- Create `backend/app/services/pdf_renderer.py`
- Implement `render_executive_debrief_pdf()` method
- Wire export endpoint: `POST /incidents/{id}/export/executive-debrief`

#### GAP-006: Policy Snapshots — ✅ COMPLETE

| Aspect | Detail |
|--------|--------|
| **Expected** | Immutable policy snapshot captured at run start |
| **Status** | ✅ COMPLETE (2026-01-20) |
| **Implementation** | `backend/app/models/policy_snapshot.py` |

**What was built:**
- `PolicySnapshot` SQLModel with content hash verification
- `create_snapshot()` classmethod for atomic snapshot creation
- `ThresholdSnapshot` for runtime thresholds
- `verify_integrity()` method for tamper detection

#### GAP-007: RunTerminationReason Enum — ✅ COMPLETE

| Aspect | Detail |
|--------|--------|
| **Expected** | Formal enum for why runs terminate |
| **Status** | ✅ COMPLETE (2026-01-20) |
| **Implementation** | `backend/app/models/run_lifecycle.py` |

**What was built:**
- `RunTerminationReason` enum (COMPLETED, POLICY_BLOCK, BUDGET_EXCEEDED, etc.)
- `RunStatus` enum (QUEUED, RUNNING, SUCCEEDED, FAILED, FAILED_POLICY, CANCELLED)
- `PolicyViolationType` enum (TOKEN_LIMIT, COST_LIMIT, RATE_LIMIT, etc.)
- `ViolationSeverity` enum (LOW, MEDIUM, HIGH, CRITICAL)
- `RunViolationInfo` and `RunTerminationInfo` Pydantic models

#### GAP-008: Structured Export Bundles — ✅ COMPLETE

| Aspect | Detail |
|--------|--------|
| **Expected** | Structured models for evidence, SOC2, and executive exports |
| **Status** | ✅ COMPLETE (2026-01-20) |
| **Implementation** | `backend/app/models/export_bundles.py` |

**What was built:**
- `TraceStepEvidence` - Per-step evidence with status markers
- `PolicyContext` - Policy snapshot and violation context
- `EvidenceBundle` - Generic evidence export bundle
- `SOC2Bundle` - SOC2-compliant bundle with control mappings
- `SOC2ControlMapping` - Trust Service Criteria mapping
- `ExecutiveDebriefBundle` - Non-technical leadership summary
- `DEFAULT_SOC2_CONTROLS` - Default CC7.2, CC7.3, CC7.4 mappings
- `ExportBundleRequest/Response` - API request/response models

### 11.3 Component Status Matrix (Updated 2026-01-20)

| Component | Code Exists | Integrated | Working | Gap ID |
|-----------|-------------|------------|---------|--------|
| Prevention Engine | ✅ | ✅ | ✅ | GAP-001 |
| Run Stop Logic | ✅ | ✅ | ✅ | GAP-002 |
| Inflection Point Model | ✅ | ✅ | ✅ | GAP-003 |
| Policy Snapshots | ✅ | ✅ | ✅ | GAP-006 |
| RunTerminationReason | ✅ | ✅ | ✅ | GAP-007 |
| Export Bundle Models | ✅ | ✅ | ✅ | GAP-008 |
| SOC2 PDF Generator | ⏳ Model only | ❌ | ❌ | GAP-004 |
| Executive Debrief PDF | ⏳ Model only | ❌ | ❌ | GAP-005 |
| Export Bundle Service | ❌ | ❌ | ❌ | GAP-004/005 |
| Policy Evaluation (post-hoc) | ✅ | ✅ | ✅ | - |
| Incident Creation | ✅ | ✅ | ✅ | - |
| Trace Replay | ✅ | ✅ | ✅ | - |
| Violation Recording | ✅ | ✅ | ✅ | - |
| Cost Attribution | ✅ | ✅ | ✅ | - |

### 11.4 Remediation Priority (Updated 2026-01-20)

| Priority | Gap ID | Description | Status |
|----------|--------|-------------|--------|
| **P0** | GAP-001 | Prevention hook integration | ✅ DONE |
| **P0** | GAP-002 | Run stop on violation | ✅ DONE |
| **P0** | GAP-006 | Policy snapshots | ✅ DONE |
| **P1** | GAP-003 | Inflection point marking | ✅ DONE |
| **P1** | GAP-007 | RunTerminationReason enum | ✅ DONE |
| **P2** | GAP-008 | Structured export bundles | ✅ DONE |
| **P2** | GAP-004 | SOC2 PDF generator | ⏳ PENDING |
| **P3** | GAP-005 | Executive debrief | ⏳ PENDING |

### 11.5 Panel Strategy (Updated 2026-01-20)

With P0/P1 remediation complete, panels can now utilize:

1. **Activity/Live** - Prevention engine available for during-run policy display
2. **Activity/Completed** - Full termination reason and violation tracking
3. **Incidents/Active** - Incidents link to policy violations with full context
4. **Policies/Active** - Policy snapshots provide audit trail
5. **Logs/LLM Runs** - Replay with inflection point highlighting available
6. **Logs/Audit** - Evidence bundle models ready; PDF export pending

**Remaining Work:**
- Wire PDF generators (GAP-004, GAP-005)
- Create export_bundle_service.py for bundle generation
- Add export endpoints to incidents API

### 11.6 Backend Files Status (Updated 2026-01-20)

| File | Purpose | Status |
|------|---------|--------|
| `backend/app/models/run_lifecycle.py` | RunTerminationReason, RunStatus enums | ✅ CREATED |
| `backend/app/models/policy_snapshot.py` | PolicySnapshot SQLModel | ✅ CREATED |
| `backend/app/models/export_bundles.py` | EvidenceBundle, SOC2Bundle models | ✅ CREATED |
| `backend/app/policy/prevention_engine.py` | PreventionEngine, PreventionResult | ✅ CREATED |
| `backend/app/db.py` | Run model governance fields | ✅ UPDATED |
| `backend/app/traces/models.py` | TraceSummary inflection fields | ✅ UPDATED |
| `backend/app/policy/__init__.py` | Export prevention engine | ✅ UPDATED |
| `backend/app/models/__init__.py` | Export new models | ✅ UPDATED |
| `backend/app/services/export_bundle_service.py` | Bundle generator | ⏳ PENDING |
| `backend/app/services/pdf_renderer.py` | PDF renderer | ⏳ PENDING |
| `backend/app/api/incidents.py` | Export endpoints | ✅ CREATED |
| `backend/alembic/versions/110_governance_fields.py` | Migration | ✅ CREATED |

---

## 12. Domain Registry

This section provides a comprehensive inventory of each domain's scripts, API routes, imports/exports, models, and purpose. Generated from codebase analysis on 2026-01-20.

---

### 12.1 Overview Domain

**Purpose:** Read-only projection facade providing system health at a glance. Aggregates data from Activity, Incidents, Policies, and Logs domains.

**Question Answered:** "Is the system okay right now?"

#### API Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/overview/highlights` | GET | Get recent system highlights |
| `/api/v1/overview/decisions` | GET | Get pending/recent decisions |
| `/api/v1/overview/health` | GET | Get overall system health status |
| `/api/v1/overview/metrics` | GET | Get high-level metrics summary |
| `/api/v1/overview/summary` | GET | Get complete overview summary |

#### Scripts & Services

| File | Layer | Purpose | Imports | Exports |
|------|-------|---------|---------|---------|
| `backend/app/api/overview.py` | L2 | Overview API endpoints | `Run`, `Incident`, `Policy` models | Overview endpoints |
| `backend/app/services/overview_service.py` | L3 | Overview aggregation | Activity, Incident, Policy services | `OverviewService` |

#### Data Flow

```
Policies  ──┐
Activity  ──┼──► OverviewService ──► /api/v1/overview/* ──► Overview UI
Incidents ──┤
Logs      ──┘
```

#### Models Used (Read-Only)

| Model | Source Domain | Fields Accessed |
|-------|---------------|-----------------|
| `Run` | Activity | `status`, `started_at`, `tokens_used` |
| `Incident` | Incidents | `severity`, `status`, `created_at` |
| `PolicyRule` | Policies | `status`, `violation_count` |

---

### 12.2 Activity Domain

**Purpose:** Track agent runs and executions (live and completed).

**Question Answered:** "What ran / is running?"

#### API Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/activity/` | GET | List activity (runs) with filtering |
| `/api/v1/activity/{run_id}` | GET | Get single run detail |
| `/api/v1/activity/live` | GET | Get currently running executions |
| `/api/v1/activity/completed` | GET | Get completed runs |
| `/api/v1/activity/signals` | GET | Get run signals/alerts |
| `/api/v1/traces/` | GET | List traces |
| `/api/v1/traces/{trace_id}` | GET | Get trace detail |
| `/api/v1/traces/{trace_id}/steps` | GET | Get trace steps |
| `/api/v1/traces/{trace_id}/replay` | POST | Replay trace execution |

#### Scripts & Services

| File | Layer | Purpose | Imports | Exports |
|------|-------|---------|---------|---------|
| `backend/app/api/activity.py` | L2 | Activity API endpoints | `Run`, `ActivityService` | Activity endpoints |
| `backend/app/api/traces.py` | L2 | Trace API endpoints | `TraceStore` | Trace endpoints |
| `backend/app/services/customer_activity_read_service.py` | L3 | Activity read operations | `Run`, `db` | `CustomerActivityReadService` |
| `backend/app/services/run_signal_service.py` | L4 | Run signal detection | `Run`, signals config | `RunSignalService` |
| `backend/app/services/pattern_detection_service.py` | L4 | Pattern detection engine | `Run`, `Incident` | `PatternDetectionService` |
| `backend/app/traces/store.py` | L6 | Trace storage | `aos_traces`, `aos_trace_steps` | `TraceStore` |
| `backend/app/traces/models.py` | L6 | Trace models | SQLModel | `TraceSummary`, `TraceStep` |

#### Models

| Model | Table | Key Fields |
|-------|-------|------------|
| `Run` | `runs` | `run_id`, `agent_id`, `tenant_id`, `status`, `goal`, `started_at`, `completed_at`, `tokens_used`, `total_cost_cents`, `policy_snapshot_id`, `termination_reason`, `stopped_at_step`, `violation_policy_id` |
| `TraceSummary` | `aos_traces` | `trace_id`, `run_id`, `tenant_id`, `status`, `step_count`, `violation_step_index`, `violation_timestamp`, `violation_policy_id`, `violation_reason` |
| `TraceStep` | `aos_trace_steps` | `step_id`, `trace_id`, `step_index`, `step_type`, `timestamp`, `tokens`, `cost_cents`, `duration_ms`, `content_hash` |

#### Cross-Domain Links

| Source | Target | Field | Purpose |
|--------|--------|-------|---------|
| `Run` → `Incident` | incidents.source_run_id | Links run to incident |
| `Run` → `Trace` | aos_traces.run_id | Links run to trace |
| `Run` → `PolicySnapshot` | runs.policy_snapshot_id | Links run to policy state |

---

### 12.3 Incidents Domain

**Purpose:** Track policy violations, failures, and security events.

**Question Answered:** "What went wrong?"

#### API Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/incidents/` | GET | List incidents with filtering |
| `/api/v1/incidents/{incident_id}` | GET | Get incident detail |
| `/api/v1/incidents/{incident_id}/acknowledge` | POST | Acknowledge incident |
| `/api/v1/incidents/{incident_id}/resolve` | POST | Resolve incident |
| `/api/v1/incidents/{incident_id}/escalate` | POST | Escalate incident |
| `/api/v1/incidents/{incident_id}/timeline` | GET | Get incident timeline |
| `/api/v1/incidents/{incident_id}/related` | GET | Get related incidents |
| `/api/v1/incidents/{incident_id}/comments` | GET/POST | Get/add comments |
| `/api/v1/incidents/{incident_id}/postmortem` | GET/POST | Get/create postmortem |
| `/api/v1/incidents/{incident_id}/export/evidence` | POST | Export evidence bundle |
| `/api/v1/incidents/{incident_id}/export/soc2` | POST | Export SOC2 PDF |
| `/api/v1/incidents/{incident_id}/export/executive-debrief` | POST | Export executive debrief |
| `/api/v1/incidents/active` | GET | Get active incidents |
| `/api/v1/incidents/resolved` | GET | Get resolved incidents |
| `/api/v1/incidents/stats` | GET | Get incident statistics |
| `/api/v1/incidents/patterns` | GET | Get incident patterns |
| `/api/v1/incidents/policy/{policy_id}` | GET | Get incidents by policy |

#### Scripts & Services

| File | Layer | Purpose | Imports | Exports |
|------|-------|---------|---------|---------|
| `backend/app/api/incidents.py` | L2 | Incident API endpoints | `Incident`, services | Incident endpoints |
| `backend/app/services/incident_engine.py` | L4 | Incident creation/lifecycle | `Incident`, `Run`, `Policy` | `IncidentEngine` |
| `backend/app/services/incident_facade.py` | L3 | Incident query facade | `Incident`, engines | `IncidentFacade` |
| `backend/app/services/incident_pattern_service.py` | L4 | Pattern analysis | `Incident`, patterns | `PatternService` |
| `backend/app/services/postmortem_service.py` | L4 | Postmortem management | `Incident`, `Postmortem` | `PostMortemService` |
| `backend/app/services/export_bundle_service.py` | L3 | Export bundle generation | bundles, traces | `ExportBundleService` |
| `backend/app/services/pdf_renderer.py` | L3 | PDF rendering | reportlab, bundles | `PDFRenderer` |

#### Models

| Model | Table | Key Fields |
|-------|-------|------------|
| `Incident` | `incidents` | `incident_id`, `tenant_id`, `source_run_id`, `policy_id`, `severity`, `status`, `type`, `title`, `description`, `created_at`, `acknowledged_at`, `resolved_at` |
| `IncidentComment` | `incident_comments` | `comment_id`, `incident_id`, `user_id`, `content`, `created_at` |
| `Postmortem` | `postmortems` | `postmortem_id`, `incident_id`, `root_cause`, `timeline`, `lessons_learned` |
| `EvidenceBundle` | (Pydantic) | `bundle_id`, `run_id`, `incident_id`, `trace_id`, `steps`, `policy_context` |
| `SOC2Bundle` | (Pydantic) | Extends `EvidenceBundle` + `control_mappings`, `attestation_statement` |
| `ExecutiveDebriefBundle` | (Pydantic) | `incident_summary`, `business_impact`, `risk_level`, `recommended_actions` |

#### Cross-Domain Links

| Source | Target | Field | Purpose |
|--------|--------|-------|---------|
| `Incident` → `Run` | runs.run_id | source_run_id | Links incident to source run |
| `Incident` → `Policy` | policy_rules.policy_id | policy_id | Links to violated policy |
| `Incident` → `Trace` | aos_traces.incident_id | incident_id | Links to trace evidence |

---

### 12.4 Policies Domain

**Purpose:** Define and manage governance rules, limits, and constraints.

**Question Answered:** "How is behavior defined?"

#### API Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/policies/` | GET | List all policies |
| `/api/v1/policies/{policy_id}` | GET/PUT/DELETE | CRUD single policy |
| `/api/v1/policies/rules/` | GET/POST | List/create policy rules |
| `/api/v1/policies/rules/{rule_id}` | GET/PUT/DELETE | CRUD single rule |
| `/api/v1/policies/limits/` | GET/POST | List/create policy limits |
| `/api/v1/policies/limits/{limit_id}` | GET/PUT/DELETE | CRUD single limit |
| `/api/v1/policies/proposals/` | GET/POST | List/create policy proposals |
| `/api/v1/policies/proposals/{proposal_id}` | GET/PUT | Get/update proposal |
| `/api/v1/policies/proposals/{proposal_id}/approve` | POST | Approve proposal |
| `/api/v1/policies/proposals/{proposal_id}/reject` | POST | Reject proposal |
| `/api/v1/policies/violations/` | GET | List policy violations |
| `/api/v1/policies/violations/stats` | GET | Get violation statistics |
| `/api/v1/policies/library` | GET | Get policy library templates |
| `/api/v1/policies/controls` | GET/PUT | Get/update controls |
| `/api/v1/policies/validate` | POST | Validate policy rule |

#### Scripts & Services

| File | Layer | Purpose | Imports | Exports |
|------|-------|---------|---------|---------|
| `backend/app/api/policy.py` | L2 | Policy API endpoints | `PolicyRule`, services | Policy endpoints |
| `backend/app/api/policy_rules_crud.py` | L2 | Policy rules CRUD | `PolicyRule` | Rules endpoints |
| `backend/app/api/policy_limits_crud.py` | L2 | Policy limits CRUD | `PolicyLimit` | Limits endpoints |
| `backend/app/api/policy_layer.py` | L2 | Policy layer operations | Policy services | Layer endpoints |
| `backend/app/api/policy_proposals.py` | L2 | Policy proposals | `PolicyProposal` | Proposal endpoints |
| `backend/app/policy/engine.py` | L4 | Policy evaluation engine | Rules, IR | `PolicyEngine` |
| `backend/app/policy/compiler.py` | L4 | Policy rule compiler | Rules, IR | `PolicyCompiler` |
| `backend/app/policy/ir.py` | L4 | Intermediate representation | Rules | `PolicyIR` |
| `backend/app/policy/optimizer.py` | L4 | Policy optimization | IR | `PolicyOptimizer` |
| `backend/app/policy/runtime.py` | L4 | Runtime evaluation | Engine, context | `PolicyRuntime` |
| `backend/app/policy/prevention_engine.py` | L4 | Prevention during runs | Policy, context | `PreventionEngine` |
| `backend/app/policy/validators/` | L4 | Policy validators | Validators | Various validators |
| `backend/app/services/policy_violation_service.py` | L4 | Violation tracking | `PolicyRule`, `Incident` | `PolicyViolationService` |
| `backend/app/services/policy_proposal_engine.py` | L4 | Proposal workflow | `PolicyProposal` | `PolicyProposalEngine` |

#### Models

| Model | Table | Key Fields |
|-------|-------|------------|
| `PolicyRule` | `policy_rules` | `policy_id`, `tenant_id`, `name`, `rule_type`, `condition`, `action`, `threshold`, `status`, `violation_count` |
| `PolicyLimit` | `policy_limits` | `limit_id`, `tenant_id`, `limit_type`, `value`, `scope` |
| `PolicyProposal` | `policy_proposals` | `proposal_id`, `tenant_id`, `proposed_rule`, `status`, `proposer_id`, `reviewer_id` |
| `PolicySnapshot` | `policy_snapshots` | `snapshot_id`, `tenant_id`, `policies_json`, `thresholds_json`, `content_hash`, `policy_count` |
| `PreventionRecord` | `prevention_records` | `record_id`, `run_id`, `policy_id`, `action`, `step_index` |

#### Cross-Domain Links

| Source | Target | Field | Purpose |
|--------|--------|-------|---------|
| `PolicyRule` → `Incident` | incidents.policy_id | policy_id | Links policy to incidents |
| `PolicySnapshot` → `Run` | runs.policy_snapshot_id | snapshot_id | Captures policy state at run start |
| `PreventionRecord` → `Run` | runs.run_id | run_id | Links prevention to run |

---

### 12.5 Logs Domain

**Purpose:** Store and query raw execution records, system logs, and audit trails.

**Question Answered:** "What is the raw truth?"

**Topics:** LLM Runs, System Logs, Audit Logs

#### API Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/logs/` | GET | List all logs (topic filter) |
| `/api/v1/logs/llm-runs` | GET | LLM execution logs |
| `/api/v1/logs/system` | GET | System event logs |
| `/api/v1/logs/audit` | GET | Audit trail logs |
| `/api/v1/logs/{log_id}` | GET | Get single log entry |
| `/api/v1/logs/search` | POST | Search logs with filters |
| `/api/v1/logs/export` | POST | Export logs (JSON/CSV) |

#### Scripts & Services

| File | Layer | Purpose | Imports | Exports |
|------|-------|---------|---------|---------|
| `backend/app/api/logs.py` | L2 | Logs API endpoints | `TraceStore`, models | Logs endpoints |
| `backend/app/traces/store.py` | L6 | Trace storage (primary) | `aos_traces`, `aos_trace_steps` | `TraceStore` |
| `backend/app/traces/models.py` | L6 | Trace models | SQLModel | `TraceSummary`, `TraceStep` |
| `backend/app/services/audit_log_service.py` | L4 | Audit logging | `AuditLog` | `AuditLogService` |

#### Models

| Model | Table | Key Fields |
|-------|-------|------------|
| `TraceSummary` | `aos_traces` | `trace_id`, `run_id`, `tenant_id`, `status`, `step_count`, `is_synthetic`, `violation_step_index`, `violation_timestamp` |
| `TraceStep` | `aos_trace_steps` | `step_id`, `trace_id`, `step_index`, `step_type`, `level`, `source`, `timestamp`, `tokens`, `cost_cents`, `duration_ms`, `content_hash` |
| `AuditLog` | `audit_logs` | `log_id`, `tenant_id`, `actor_id`, `action`, `resource_type`, `resource_id`, `timestamp`, `details` |
| `SystemLog` | `system_logs` | `log_id`, `level`, `source`, `message`, `timestamp`, `context` |

#### Topics

| Topic | Source Table | Query Filter |
|-------|--------------|--------------|
| LLM_RUNS | `aos_traces` | Execution traces |
| SYSTEM_LOGS | `system_logs` | System events |
| AUDIT | `audit_logs` | User actions |

#### Cross-Domain Links

| Source | Target | Field | Purpose |
|--------|--------|-------|---------|
| `TraceSummary` → `Run` | runs.run_id | run_id | Links trace to run |
| `TraceSummary` → `Incident` | incidents.incident_id | incident_id | Links trace to incident |
| `AuditLog` → `User` | users.user_id | actor_id | Links audit to actor |

---

### 12.6 Connectivity Domain

**Purpose:** Manage external integrations and API key access.

**Subdomains:** Integrations, API Keys

#### API Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/connectivity/integrations/` | GET | List integrations |
| `/api/v1/connectivity/integrations/{integration_id}` | GET/PUT/DELETE | CRUD single integration |
| `/api/v1/connectivity/integrations/{integration_id}/test` | POST | Test integration connection |
| `/api/v1/connectivity/integrations/{integration_id}/sync` | POST | Sync integration data |
| `/api/v1/connectivity/api-keys/` | GET/POST | List/create API keys |
| `/api/v1/connectivity/api-keys/{key_id}` | GET/DELETE | Get/revoke API key |
| `/api/v1/connectivity/api-keys/{key_id}/rotate` | POST | Rotate API key |
| `/api/v1/connectivity/llm-providers/` | GET | List LLM providers |
| `/api/v1/connectivity/llm-providers/{provider_id}` | GET/PUT | Get/update provider config |

#### Scripts & Services

| File | Layer | Purpose | Imports | Exports |
|------|-------|---------|---------|---------|
| `backend/app/api/connectivity.py` | L2 | Connectivity API endpoints | Integration models | Connectivity endpoints |
| `backend/app/api/api_keys.py` | L2 | API key management | `ApiKey` | API key endpoints |
| `backend/app/services/integration_service.py` | L4 | Integration management | `CusIntegration` | `IntegrationService` |
| `backend/app/services/api_key_service.py` | L4 | API key management | `ApiKey` | `ApiKeyService` |
| `backend/app/services/llm_provider_service.py` | L4 | LLM provider config | Provider configs | `LLMProviderService` |

#### Models

| Model | Table | Key Fields |
|-------|-------|------------|
| `CusIntegration` | `cus_integrations` | `integration_id`, `tenant_id`, `provider`, `config`, `status`, `last_sync_at` |
| `ApiKey` | `api_keys` | `key_id`, `tenant_id`, `name`, `key_hash`, `prefix`, `scopes`, `created_at`, `expires_at`, `last_used_at` |
| `LLMProviderConfig` | `llm_provider_configs` | `config_id`, `tenant_id`, `provider`, `api_key_encrypted`, `model`, `enabled` |

#### Integration Types

| Provider | Purpose | Config Fields |
|----------|---------|---------------|
| `anthropic` | Claude API | `api_key`, `model`, `max_tokens` |
| `openai` | OpenAI API | `api_key`, `model`, `organization` |
| `slack` | Notifications | `webhook_url`, `channel` |
| `pagerduty` | Incident alerting | `api_key`, `service_id` |
| `datadog` | Metrics export | `api_key`, `app_key` |

---

### 12.7 Account Domain

**Purpose:** Manage tenants, users, billing, and team settings.

**Note:** Account is NOT a core domain—it manages *who*, *what*, and *billing*, not *what happened*.

#### API Routes

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/accounts/` | GET | Get current account |
| `/api/v1/accounts/tenants/` | GET/POST | List/create tenants |
| `/api/v1/accounts/tenants/{tenant_id}` | GET/PUT/DELETE | CRUD tenant |
| `/api/v1/accounts/users/` | GET/POST | List/invite users |
| `/api/v1/accounts/users/{user_id}` | GET/PUT/DELETE | CRUD user |
| `/api/v1/accounts/users/{user_id}/roles` | GET/PUT | Get/update user roles |
| `/api/v1/accounts/teams/` | GET/POST | List/create teams |
| `/api/v1/accounts/teams/{team_id}` | GET/PUT/DELETE | CRUD team |
| `/api/v1/accounts/teams/{team_id}/members` | GET/POST/DELETE | Team membership |
| `/api/v1/accounts/billing/` | GET | Get billing info |
| `/api/v1/accounts/billing/subscription` | GET/PUT | Subscription management |
| `/api/v1/accounts/billing/invoices` | GET | List invoices |
| `/api/v1/accounts/billing/usage` | GET | Get usage metrics |
| `/api/v1/accounts/settings` | GET/PUT | Account settings |
| `/api/v1/accounts/quotas` | GET | Get quota limits |

#### Scripts & Services

| File | Layer | Purpose | Imports | Exports |
|------|-------|---------|---------|---------|
| `backend/app/api/accounts.py` | L2 | Account API endpoints | Account models | Account endpoints |
| `backend/app/api/users.py` | L2 | User management | `User` | User endpoints |
| `backend/app/api/teams.py` | L2 | Team management | `Team` | Team endpoints |
| `backend/app/api/billing.py` | L2 | Billing API | Billing models | Billing endpoints |
| `backend/app/services/tenant_service.py` | L4 | Tenant management | `Tenant` | `TenantService` |
| `backend/app/services/user_service.py` | L4 | User management | `User` | `UserService` |
| `backend/app/services/team_service.py` | L4 | Team management | `Team` | `TeamService` |
| `backend/app/services/billing_service.py` | L4 | Billing/subscription | Billing models | `BillingService` |
| `backend/app/services/quota_service.py` | L4 | Quota enforcement | `Quota` | `QuotaService` |

#### Models

| Model | Table | Key Fields |
|-------|-------|------------|
| `Tenant` | `tenants` | `tenant_id`, `name`, `plan`, `created_at`, `settings` |
| `User` | `users` | `user_id`, `tenant_id`, `email`, `name`, `roles`, `created_at`, `last_login` |
| `Team` | `teams` | `team_id`, `tenant_id`, `name`, `description` |
| `TeamMember` | `team_members` | `team_id`, `user_id`, `role` |
| `Subscription` | `subscriptions` | `subscription_id`, `tenant_id`, `plan`, `status`, `current_period_end` |
| `Invoice` | `invoices` | `invoice_id`, `tenant_id`, `amount`, `status`, `due_date` |
| `Quota` | `quotas` | `quota_id`, `tenant_id`, `resource`, `limit`, `used` |

#### Account Scope Rule

| Resource | Scope | Notes |
|----------|-------|-------|
| Tenants | Global | Multi-tenant isolation |
| Users | Tenant-scoped | Users belong to one tenant |
| Teams | Tenant-scoped | Teams within tenant |
| Billing | Tenant-scoped | Per-tenant billing |
| Quotas | Tenant-scoped | Per-tenant limits |

---

### 12.8 Domain Cross-Reference Matrix

| Domain | Reads From | Writes To | Triggered By |
|--------|------------|-----------|--------------|
| **Overview** | Activity, Incidents, Policies, Logs | - | API request |
| **Activity** | - | Runs, Traces | Run creation, worker |
| **Incidents** | Runs, Policies | Incidents, Postmortems | Policy violation, manual |
| **Policies** | - | PolicyRules, Limits, Snapshots | Admin action, proposal |
| **Logs** | Runs, Incidents | Traces, AuditLogs | Run execution, user action |
| **Connectivity** | - | Integrations, ApiKeys | Admin action |
| **Account** | - | Tenants, Users, Teams | Admin action |

---

### 12.9 Layer Distribution by Domain

| Domain | L2 (API) | L3 (Adapter) | L4 (Engine) | L6 (Platform) |
|--------|----------|--------------|-------------|---------------|
| Overview | `overview.py` | `overview_service.py` | - | - |
| Activity | `activity.py`, `traces.py` | `customer_activity_read_service.py` | `run_signal_service.py`, `pattern_detection_service.py` | `traces/store.py` |
| Incidents | `incidents.py` | `incident_facade.py`, `export_bundle_service.py` | `incident_engine.py`, `postmortem_service.py` | - |
| Policies | `policy.py`, `policy_*.py` | - | `policy/engine.py`, `prevention_engine.py` | - |
| Logs | `logs.py` | - | `audit_log_service.py` | `traces/store.py` |
| Connectivity | `connectivity.py`, `api_keys.py` | - | `integration_service.py`, `api_key_service.py` | - |
| Account | `accounts.py`, `users.py`, `teams.py` | - | `tenant_service.py`, `user_service.py` | - |

---

## 13. Policy Control Lever System

**Status:** ✅ PHASE 1 COMPLETE (2026-01-20)
**Reference:** `POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md`

### 13.1 Overview

The Policy Control Lever provides a comprehensive governance system:

```
Policy → Scope Selector → Monitors → Limits → Thresholds → Actions → Evidence
```

**Core Principle:**
> A policy is a versioned, scoped, runtime-bound control contract that deterministically governs execution behavior and produces immutable evidence.

### 13.2 New Components

| Component | Table | Purpose |
|-----------|-------|---------|
| **PolicyScope** | `policy_scopes` | Define WHO policy applies to (agent, API key, human actor) |
| **PolicyPrecedence** | `policy_precedence` | Conflict resolution and binding moment |
| **MonitorConfig** | `policy_monitor_configs` | WHAT signals to collect (token, cost, RAG) |
| **ThresholdSignal** | `threshold_signals` | Near/breach event records |
| **AlertConfig** | `policy_alert_configs` | Alert channels and throttling |
| **OverrideAuthority** | `policy_override_authority` | Emergency override rules |
| **OverrideRecord** | `policy_override_records` | Override audit trail |

### 13.3 Scope Types

| Scope | Description | Target Field |
|-------|-------------|--------------|
| `ALL_RUNS` | All LLM runs for tenant | - |
| `AGENT` | Specific agent IDs | `agent_ids_json` |
| `API_KEY` | Specific API keys | `api_key_ids_json` |
| `HUMAN_ACTOR` | Specific human actors | `human_actor_ids_json` |

### 13.4 Conflict Resolution

| Strategy | Behavior |
|----------|----------|
| `MOST_RESTRICTIVE` | Smallest limit, harshest action wins |
| `EXPLICIT_PRIORITY` | Higher precedence (lower number) wins |
| `FAIL_CLOSED` | If ambiguous, deny/stop |

### 13.5 Threshold Signals

| Signal Type | Trigger | Action |
|-------------|---------|--------|
| `NEAR` | Metric >= configured percentage (default 80%) | Alert only |
| `BREACH` | Metric >= 100% of limit | Enforce action (PAUSE/STOP/KILL) |

### 13.6 Runtime Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ RUN CREATED                                                             │
│   │                                                                     │
│   ▼                                                                     │
│ ScopeResolver.resolve_applicable_policies()                             │
│   │  - Filter by agent_id, api_key_id, human_actor_id                   │
│   │                                                                     │
│   ▼                                                                     │
│ PolicyArbitrator.arbitrate()                                            │
│   │  - Sort by precedence                                               │
│   │  - Resolve conflicts (most_restrictive)                             │
│   │                                                                     │
│   ▼                                                                     │
│ PolicySnapshot.create_snapshot()                                        │
│   │  - Freeze effective limits                                          │
│   │                                                                     │
│   ▼                                                                     │
│ FOR EACH STEP:                                                          │
│   ├── Collect signals (tokens, cost, burn rate)                         │
│   ├── Evaluate vs limits                                                │
│   ├── If NEAR → AlertEmitter.emit_near_threshold()                      │
│   └── If BREACH → PreventionEngine.enforce() + AlertEmitter.emit_breach()│
│                                                                         │
│   ▼                                                                     │
│ Evidence: TraceSummary + ThresholdSignals + Incident                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 13.7 New Files

| File | Layer | Purpose |
|------|-------|---------|
| `backend/app/models/policy_scope.py` | L4 | Scope selector model |
| `backend/app/models/policy_precedence.py` | L4 | Precedence model |
| `backend/app/models/monitor_config.py` | L4 | Monitor configuration |
| `backend/app/models/threshold_signal.py` | L4 | Threshold signals |
| `backend/app/models/alert_config.py` | L4 | Alert configuration |
| `backend/app/models/override_authority.py` | L4 | Override authority |
| `backend/app/policy/scope_resolver.py` | L4 | Scope resolution engine |
| `backend/app/policy/arbitrator.py` | L4 | Policy arbitration engine |
| `backend/app/services/alert_emitter.py` | L3 | Alert emission service |
| `backend/alembic/versions/111_policy_control_lever.py` | Migration | Schema |

### 13.8 Cross-Domain Links (Extended)

| Source | Target | Field | Purpose |
|--------|--------|-------|---------|
| `PolicyScope` → `PolicyRule` | policy_rules.policy_id | policy_id | Links scope to policy |
| `PolicyPrecedence` → `PolicyRule` | policy_rules.policy_id | policy_id | Links precedence to policy |
| `ThresholdSignal` → `Run` | runs.run_id | run_id | Links signal to run |
| `ThresholdSignal` → `PolicyRule` | policy_rules.policy_id | policy_id | Links signal to policy |
| `OverrideRecord` → `PolicyRule` | policy_rules.policy_id | policy_id | Links override to policy |
| `OverrideRecord` → `Run` | runs.run_id | run_id | Links override to run |

