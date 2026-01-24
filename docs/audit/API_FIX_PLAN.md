# API ↔ SDSR Fix Plan

**Created:** 2026-01-16
**Mode:** Surgical (investigate → fix → verify → next)
**Reference:** API_SDSR_AUDIT_REPORT.md, PANEL_STRUCTURE_PIPELINE.md

---

## ⚠️ SCOPE EXCLUSION: ops.py

**`/ops/*` endpoints are OUT OF SCOPE for this audit.**

| Router | Path Prefix | Audience | Status |
|--------|-------------|----------|--------|
| `ops.py` | `/ops/*` | Founder/Backend teams ONLY | **EXCLUDED** |
| `founder_actions.py` | `/ops/actions/*` | Founder/Backend teams ONLY | **EXCLUDED** |
| `cost_ops.py` | `/ops/cost/*` | Founder/Backend teams ONLY | **EXCLUDED** |

These are internal operations endpoints, NOT customer-facing. Customer Console panels should NEVER point to `/ops/*` routes.

**Customer-facing routes:** `/guard/*`, `/api/v1/cus/*`, `/api/v1/runtime/*`

---

## Architecture Clarification

### Current Layer Stack

```
┌──────────────────────────────────────────────────────────────┐
│  PANEL (UI)                                                  │
│    ↓                                                         │
│  L2 API Route (e.g., /guard/*, /api/v1/cus/*)          │
│    ↓                                                         │
│  L3 ADAPTER (e.g., CustomerActivityAdapter)                  │
│    ↓                                                         │
│  L4 Service (e.g., CustomerActivityReadService)              │
│    ↓                                                         │
│  L6 DB                                                       │
└──────────────────────────────────────────────────────────────┘
```

### Existing Adapters (13)

| Adapter | File | Purpose |
|---------|------|---------|
| CustomerActivityAdapter | customer_activity_adapter.py | Activity → Customer |
| CustomerIncidentsAdapter | customer_incidents_adapter.py | Incidents → Customer |
| CustomerKillswitchAdapter | customer_killswitch_adapter.py | Killswitch → Customer |
| CustomerKeysAdapter | customer_keys_adapter.py | API Keys → Customer |
| CustomerLogsAdapter | customer_logs_adapter.py | Logs → Customer |
| CustomerPoliciesAdapter | customer_policies_adapter.py | Policies → Customer |
| FounderOpsAdapter | founder_ops_adapter.py | Ops → Founder |
| FounderContractReviewAdapter | founder_contract_review_adapter.py | Contract Review → Founder |
| PolicyAdapter | policy_adapter.py | Policy Layer |
| RuntimeAdapter | runtime_adapter.py | Runtime projections |
| WorkersAdapter | workers_adapter.py | Worker operations |
| PlatformEligibilityAdapter | platform_eligibility_adapter.py | Eligibility |

### Runtime Projections (/api/v1/runtime/*)

O2 schema endpoints providing enriched data:
- `/api/v1/runtime/activity/runs` → Advanced activity with risk_level, evidence_health
- `/api/v1/runtime/incidents` → O2 incident list
- `/api/v1/runtime/policies/limits` → O2 limits
- `/api/v1/runtime/policies/governance` → O2 governance
- `/api/v1/runtime/overview/*` → Cross-domain summaries

---

## Route Disambiguation

Several intent YAMLs point to routes that exist in MULTIPLE places:

| Path | Router 1 | Router 2 | Status |
|------|----------|----------|--------|
| `/v1/incidents` | v1_killswitch.py (tenant SDK) | - | CORRECT for that panel |
| `/api/v1/incidents` | incidents.py (SDSR) | - | CORRECT for that panel |
| `/v1/policies/active` | v1_killswitch.py | - | CORRECT |
| `/cost/anomalies` | cost_intelligence.py | - | CORRECT (prefix="/cost") |
| `/cost/budgets` | cost_intelligence.py | - | CORRECT |
| `/status_history` | status_history.py | - | CORRECT (prefix="/status_history") |

**Conclusion:** The "misplaced" paths from the initial audit are actually **CORRECT**. Each router has its own prefix and the intent YAMLs match.

---

## FIX QUEUE: Missing Endpoints

### FIX-001: /api/v1/ops/incidents/patterns

| Field | Value |
|-------|-------|
| Panel | INC-EV-ACT-O4 |
| Facet | incident_resolution |
| Criticality | HIGH |
| Expected Path | `/api/v1/ops/incidents/patterns` |
| Current State | **PATH MISMATCH** (endpoint exists at different path) |
| Router | ops.py |
| Investigation | COMPLETE |

**Investigation Findings (2026-01-16):**

| Finding | Detail |
|---------|--------|
| Endpoint EXISTS | YES - at `app/api/ops.py:1353` |
| Actual Path | `/ops/incidents/patterns` |
| Router Prefix | `prefix="/ops"` (NOT `/api/v1/ops`) |
| Data Source | `ops_events` table (event-sourced) |
| Pattern Types | `policy_block`, `llm_failure`, `infra_limit`, `freeze` |

**Investigation Steps:**
1. [x] Check `ops.py` for existing pattern aggregation - **FOUND at line 1353**
2. [x] Check if `incident_patterns` table exists - **No table, derived from ops_events**
3. [x] Review what data shape the panel expects - **See actual shape below**
4. [x] Determine if this should be an adapter endpoint or direct - **See resolution options**

**Actual Response Shape (from ops.py:375):**
```python
class IncidentPattern(BaseModel):
    pattern_type: str  # 'policy_block', 'llm_failure', 'rate_limit', 'budget'
    count_24h: int
    count_7d: int
    trend: str  # 'increasing', 'stable', 'decreasing'
    top_tenants: List[str]
    sample_ids: List[str]
```

**Resolution Options:**

| Option | Description | Recommendation |
|--------|-------------|----------------|
| A | Update intent YAML to `/ops/incidents/patterns` | **RECOMMENDED** - Minimal change |
| B | Create adapter at `/api/v1/ops/incidents/patterns` | More work, maintains L3 pattern |

**Status:** INVESTIGATION COMPLETE - Awaiting decision on resolution option

---

### FIX-002: /api/v1/cus/activity (Path Collision)

| Field | Value |
|-------|-------|
| Panel | LOG-REC-LLM-O3 |
| Facet | llm_record_keeping |
| Criticality | MEDIUM |
| Expected Path | `/api/v1/cus/activity` |
| Current State | **FALSE POSITIVE** - Endpoint exists at correct path |
| Router | customer_activity.py |
| Investigation | COMPLETE |

**Investigation Findings (2026-01-16):**

| Finding | Detail |
|---------|--------|
| Endpoint EXISTS | YES - at `app/api/customer_activity.py:56` |
| Actual Path | `/api/v1/cus/activity` |
| Router Prefix | `prefix="/api/v1/customer"` |
| Endpoint Definition | `@router.get("/activity", ...)` |
| Full Path | `/api/v1/customer` + `/activity` = `/api/v1/cus/activity` ✅ |

**Investigation Steps:**
1. [x] Read `customer_activity.py` to check route definition - **Found at line 56**
2. [x] Check if router has nested prefix - **NO nested prefix, correct path**
3. [x] Verify the intent YAML expected path - **Matches actual path**

**Root Cause of False Alarm:**
The original audit incorrectly stated path was `/api/v1/cus/activity/activity`. Re-verification shows:
- Router prefix: `/api/v1/customer` (line 48)
- Endpoint: `/activity` (line 56)
- Full path: `/api/v1/cus/activity` (MATCHES intent YAML)

**Status:** NO ACTION NEEDED - Endpoint exists at correct path

---

### FIX-003: /guard/costs/incidents

| Field | Value |
|-------|-------|
| Panel | POL-LIM-VIO-O2 |
| Facet | violation_tracking |
| Criticality | MEDIUM |
| Expected Path | `/guard/costs/incidents` |
| Current State | **FALSE POSITIVE** - Endpoint exists at correct path |
| Router | cost_guard.py |
| Investigation | COMPLETE |

**Investigation Findings (2026-01-16):**

| Finding | Detail |
|---------|--------|
| Endpoint EXISTS | YES - at `app/api/cost_guard.py:437` |
| Actual Path | `/guard/costs/incidents` |
| Router Prefix | `prefix="/guard/costs"` |
| Endpoint Definition | `@router.get("/incidents", ...)` |
| Full Path | `/guard/costs` + `/incidents` = `/guard/costs/incidents` ✅ |

**Investigation Steps:**
1. [x] Read `cost_guard.py` to see existing endpoints - **Found at line 437**
2. [x] Check what data shape the panel expects - **See actual shape below**
3. [x] Determine if this needs an adapter - **NO - endpoint uses DTOs from `app.contracts.guard`**

**Actual Response Shape (from cost_guard.py):**
```python
class CustomerCostIncidentDTO(BaseModel):
    id: str
    title: str
    status: Literal["protected", "attention_needed", "resolved"]
    trigger_type: Literal["budget_exceeded", "budget_warning", "cost_spike"]
    cost_at_trigger_cents: int
    cost_avoided_cents: int
    threshold_cents: Optional[int]
    action_taken: str
    recommendation: str
    detected_at: str
    resolved_at: Optional[str]

class CustomerCostIncidentListDTO(BaseModel):
    incidents: List[CustomerCostIncidentDTO]
    total: int
    has_more: bool
```

**Status:** NO ACTION NEEDED - Endpoint exists at correct path with proper contract DTOs

---

### FIX-004: /ops/actions/audit

| Field | Value |
|-------|-------|
| Panel | LOG-REC-AUD-O3 |
| Facet | audit_trail |
| Criticality | MEDIUM |
| Expected Path | `/ops/actions/audit` |
| Current State | **FALSE POSITIVE** - Endpoint exists at correct path |
| Router | founder_actions.py |
| Investigation | COMPLETE |

**Investigation Findings (2026-01-16):**

| Finding | Detail |
|---------|--------|
| Endpoint EXISTS | YES - at `app/api/founder_actions.py:725` |
| Actual Path | `/ops/actions/audit` |
| Router Prefix | `prefix="/ops/actions"` |
| Endpoint Definition | `@router.get("/audit", ...)` |
| Full Path | `/ops/actions` + `/audit` = `/ops/actions/audit` ✅ |

**Investigation Steps:**
1. [x] Check if `ops_action_audit` table exists - **Data stored in `founder_actions` table**
2. [x] Check `founder_actions.py` for action tracking - **Found at line 725**
3. [x] Determine audit trail requirements - **Implemented with pagination and filters**

**Actual Response Shape (from founder_actions.py):**
```python
class FounderActionSummaryDTO(BaseModel):
    action_id: str
    action_type: str  # "FREEZE_TENANT", "THROTTLE_TENANT", etc.
    target_type: str  # "TENANT", "API_KEY"
    target_id: str
    target_name: Optional[str]
    reason_code: Optional[str]
    founder_email: str
    applied_at: datetime
    is_active: bool
    is_reversed: bool

class FounderActionListDTO(BaseModel):
    actions: List[FounderActionSummaryDTO]
    total: int
    page: int
    page_size: int
```

**Features:**
- Pagination support (`page`, `page_size`)
- Filtering by `target_id` and `action_type`
- Returns audit trail with action details

**Status:** NO ACTION NEEDED - Endpoint exists at correct path with comprehensive audit trail

---

## FIX QUEUE: NULL Endpoints (Composite Panels)

These panels have `assumed_endpoint: null` and require composite data assembly.

### NULL-001: Activity Signals (O2-O5)

| Panels | Purpose |
|--------|---------|
| ACT-LLM-SIG-O2 | Signal details |
| ACT-LLM-SIG-O3 | Signal correlation |
| ACT-LLM-SIG-O4 | Signal history |
| ACT-LLM-SIG-O5 | Signal trends |

**Status:** Use runtime projection `/api/v1/runtime/activity/runs` which returns O2 schema with `risk_level`, `evidence_health`, `attention_reasons`.

**Action:** Update intent YAMLs to point to runtime projection OR create Signal Assembler adapter.

---

### NULL-002: Live Execution (O3-O5)

| Panels | Purpose |
|--------|---------|
| ACT-LLM-LIVE-O3 | Execution context |
| ACT-LLM-LIVE-O4 | Execution drill-down |
| ACT-LLM-LIVE-O5 | Execution timeline |

**Status:** Requires WebSocket + trace data. May need dedicated assembler.

**Action:** Investigate if `/workers/stream/{run_id}` can serve this or create LiveExecutionAssembler.

---

### NULL-003: Completion Analysis (O2-O5)

| Panels | Purpose |
|--------|---------|
| ACT-LLM-COMP-O2 | Completion analysis |
| ACT-LLM-COMP-O4 | Completion context |
| ACT-LLM-COMP-O5 | Completion provenance |

**Status:** Requires multiple run comparison + trace chain.

**Action:** Create CompletionAnalysisAssembler that fetches from `/api/v1/activity/runs` + `/api/v1/traces`.

---

### NULL-004: Overview Highlights (O2-O4)

| Panels | Purpose |
|--------|---------|
| OVR-SUM-HL-O2 | Highlight details |
| OVR-SUM-HL-O4 | Highlight context |

**Status:** Runtime projection exists at `/api/v1/runtime/overview/highlights`.

**Action:** Update intent YAMLs to use runtime projection.

---

### NULL-005: Decision Queue (O1-O4)

| Panels | Purpose |
|--------|---------|
| OVR-SUM-DC-O1 | Decision summary |
| OVR-SUM-DC-O2 | Decision details |
| OVR-SUM-DC-O3 | Decision context |
| OVR-SUM-DC-O4 | Decision provenance |

**Status:** Runtime projection exists at `/api/v1/runtime/overview/decisions`.

**Action:** Update intent YAMLs to use runtime projection.

---

### NULL-006: Cost Intelligence (O2-O4)

| Panels | Purpose |
|--------|---------|
| OVR-SUM-CI-O1 | Cost snapshot |
| OVR-SUM-CI-O2 | Cost details |
| OVR-SUM-CI-O3 | Cost breakdown |
| OVR-SUM-CI-O4 | Cost context |

**Status:** Runtime projection exists at `/api/v1/runtime/overview/costs`.

**Action:** Update intent YAMLs to use runtime projection.

---

## Adapter Gap Analysis

### Adapter Status Update (Post-Investigation)

The following adapters were originally flagged as "missing" but are NOT needed:

| Original Proposal | Status | Reason |
|-------------------|--------|--------|
| CustomerCostIncidentsAdapter | **NOT NEEDED** | `cost_guard.py` implements directly with frozen DTOs |
| OpsActionsAuditAdapter | **NOT NEEDED** | `founder_actions.py` implements directly with DTOs |
| IncidentPatternsAdapter | **REVIEW** | Endpoint at `/ops/incidents/patterns` - may benefit from adapter for L3 boundary |

### Panels Without Adapter (Direct API)

These panels talk directly to APIs without going through L3 adapters:

| Panel | Route | Needs Adapter? |
|-------|-------|----------------|
| POL-GOV-* | /policy-layer/* | Review - may be acceptable as internal |
| LOG-REC-AUD-* | /api/v1/traces | Review - may be acceptable as internal |
| LOG-REC-AUD-O2 | /api/v1/rbac/audit | Review - may be acceptable as internal |

**Note:** Not all endpoints need L3 adapters. Adapters are primarily needed when:
1. Customer-facing panels need data transformation for safety
2. Multiple callers need consistent boundary enforcement
3. L4 service contracts differ from L2 API contracts

---

## Work Procedure

For each FIX item:

```
1. INVESTIGATE
   - Read the relevant backend files
   - Check if data source exists
   - Check if adapter exists
   - Document findings

2. PROPOSE
   - Define the fix (new endpoint vs adapter vs intent YAML update)
   - Define the response schema
   - Get approval

3. IMPLEMENT
   - Create adapter if needed
   - Create endpoint if needed
   - Update intent YAML
   - Run SDSR scenario to observe

4. VERIFY
   - Run Phase A validation
   - Verify endpoint returns expected shape
   - Mark as COMPLETE
```

---

## Progress Tracker

| ID | Status | Description | Finding |
|----|--------|-------------|---------|
| FIX-001 | **PATH MISMATCH** | /api/v1/ops/incidents/patterns | Endpoint exists at `/ops/incidents/patterns` - intent YAML needs update |
| FIX-002 | ✅ FALSE POSITIVE | /api/v1/cus/activity | Endpoint exists at correct path - no action needed |
| FIX-003 | ✅ FALSE POSITIVE | /guard/costs/incidents | Endpoint exists at correct path - no action needed |
| FIX-004 | ✅ FALSE POSITIVE | /ops/actions/audit | Endpoint exists at correct path - no action needed |
| NULL-001 | PENDING | Activity Signals Assembler | Use runtime projection |
| NULL-002 | PENDING | Live Execution Assembler | May need WebSocket |
| NULL-003 | PENDING | Completion Analysis Assembler | Multi-source composite |
| NULL-004 | PENDING | Overview Highlights | Use runtime projection |
| NULL-005 | PENDING | Decision Queue | Use runtime projection |
| NULL-006 | PENDING | Cost Intelligence | Use runtime projection |

---

## Investigation Summary (2026-01-16)

### Key Findings

Out of 4 FIX items originally flagged as "missing":

| Category | Count | Items |
|----------|-------|-------|
| **Actual Issues** | 1 | FIX-001 (path mismatch) |
| **False Positives** | 3 | FIX-002, FIX-003, FIX-004 |

### Root Cause of False Positives

The original audit incorrectly flagged endpoints as "missing" because:

1. **FIX-002**: Audit misread path as `/api/v1/cus/activity/activity` - actual path is `/api/v1/cus/activity`
2. **FIX-003**: Endpoint exists at `/guard/costs/incidents` with comprehensive cost incident data
3. **FIX-004**: Endpoint exists at `/ops/actions/audit` with pagination and filtering

### Remaining Actions

| Priority | Item | Action Required |
|----------|------|-----------------|
| **P0** | FIX-001 | Update intent YAML from `/api/v1/ops/incidents/patterns` to `/ops/incidents/patterns` |
| - | FIX-002 | NO ACTION - endpoint exists correctly |
| - | FIX-003 | NO ACTION - endpoint exists correctly |
| - | FIX-004 | NO ACTION - endpoint exists correctly |
| P2 | NULL-* | Investigate composite panels (lower priority) |

---

## Next Steps

1. **FIX-001**: Decide resolution approach (update intent YAML vs create adapter)
2. **NULL items**: Can be deferred - these are composite panels that may already work with runtime projections
3. **Adapter Gap Analysis**: Update based on findings (most "missing" adapters are actually not needed)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial plan created |
| 2026-01-16 | Investigation complete: 3 of 4 FIX items are false positives |
