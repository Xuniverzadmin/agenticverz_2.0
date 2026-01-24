# API ↔ SDSR Mapping Audit Report

**Generated:** 2026-01-16
**Auditor:** Claude (API investigation based on backend function returns, not filenames)
**Reference:** INTENT_LEDGER.md, PANEL_STRUCTURE_PIPELINE.md Phase 2

---

## Executive Summary

| Status | Count | Description |
|--------|-------|-------------|
| ✅ CORRECT | 42 | Endpoint exists and returns expected data shape |
| ⚠️ MISPLACED | 6 | Endpoint exists but at different path |
| ❌ WRONG PATH | 3 | Path format incorrect (missing `/api` prefix, etc.) |
| 🔴 MISSING | 5 | Endpoint does not exist - needs to be built |
| ⬜ NULL (Composite) | 17 | Panel doesn't map to single endpoint (composite data) |

**Total Intent YAMLs Analyzed:** 73

---

## Category 1: MISSING Endpoints (Need to be Built)

These endpoints are declared in SDSR but do not exist in the backend.

| Panel ID | Declared Endpoint | Expected Data | Priority |
|----------|-------------------|---------------|----------|
| **INC-EV-ACT-O4** | `/api/v1/ops/incidents/patterns` | Incident pattern analysis for operators | HIGH |
| **LOG-REC-LLM-O3** | `/api/v1/cus/activity` | Customer-scoped activity for logs domain | MEDIUM |
| **POL-LIM-VIO-O2** | `/guard/costs/incidents` | Cost-related incidents in guard context | MEDIUM |
| **LOG-REC-AUD-O3** | `/ops/actions/audit` | Operator action audit trail | MEDIUM |
| **OVR-SUM-CI-O1** | (null but needed) | Cost intelligence summary for overview | LOW |

### Recommended Actions:

1. **`/api/v1/ops/incidents/patterns`** - Create endpoint in `ops.py`
   - Backend already has `/api/v1/ops/incidents` returning `FounderIncidentListDTO`
   - Need separate endpoint returning pattern analysis: recurring types, correlation, MTTR
   - Data exists via `incidents` table but aggregation logic missing

2. **`/api/v1/cus/activity`** - Create endpoint in `customer_activity.py`
   - Currently `/api/v1/cus/activity/activity` exists at line 56
   - Path collision - the intent expects `/api/v1/cus/activity` (no duplicate)
   - Returns: `CustomerActivityListResponse`

3. **`/guard/costs/incidents`** - Create endpoint in `cost_guard.py`
   - Currently has `/guard/costs/summary` and `/guard/costs/explained`
   - Need: `/guard/costs/incidents` returning `CustomerCostIncidentListDTO`
   - This is a customer-facing cost incident view

4. **`/ops/actions/audit`** - No ops action audit endpoint exists
   - Need to track operator actions (acknowledge, resolve, etc.)
   - Should record actor, timestamp, action_type, target_entity

---

## Category 2: MISPLACED Endpoints (Wrong Path)

These endpoints exist but at a different path than declared in SDSR.

| Panel ID | Declared Path | Actual Path | Action |
|----------|---------------|-------------|--------|
| **INC-EV-HIST-O3** | `/v1/incidents` | `/api/v1/incidents` | Update intent YAML |
| **POL-LIM-VIO-O4** | `/cost/anomalies` | `/api/v1/cost-intelligence/anomalies` | Update intent YAML |
| **POL-LIM-THR-O2** | `/cost/budgets` | `/api/v1/cost-intelligence/budgets` | Update intent YAML |
| **POL-GOV-LIB-O3** | `/v1/policies/active` | `/api/v1/v1-killswitch/policies/active` | Update intent YAML |
| **POL-GOV-ACT-O3** | `/api/v1/policies/requests` | `/api/v1/policy/requests` | Update intent YAML |
| **LOG-REC-AUD-O4** | `/status_history` | `/api/v1/status-history` | Update intent YAML |

### Root Cause Analysis:

1. **Missing `/api` prefix** - Several intents use `/v1/...` instead of `/api/v1/...`
2. **Inconsistent cost paths** - Cost endpoints live under `/api/v1/cost-intelligence/`, not `/cost/`
3. **Router prefix drift** - Some routers have prefixes not reflected in intent YAMLs

---

## Category 3: WRONG Data Shape (Endpoint Exists but Returns Different Data)

These endpoints exist at the declared path but return data that doesn't match panel expectations.

| Panel ID | Endpoint | Expected by Panel | Actually Returns | Gap |
|----------|----------|-------------------|------------------|-----|
| **ACT-LLM-SIG-O1** | `/api/v1/activity/runs` | Signal breakdown per run | Basic run list | Missing: `risk_signals`, `evidence_health`, `latency_bucket` |
| **LOG-REC-LLM-O4** | `/api/v1/tenants/runs` | LLM-focused run records | Tenant run history | Missing: `llm_model`, `prompt_tokens`, `completion_tokens` |
| **INC-EV-ACT-O5** | `/api/v1/ops/incidents/infra-summary` | Infrastructure correlation | Incident stats | Missing: `infra_component`, `affected_regions`, `blast_radius` |

### Data Shape Gaps:

The `/api/v1/activity/runs` endpoint at `activity.py:129` returns `ActivityResponse` with:
```python
class RunSummary(BaseModel):
    run_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    ...
```

But the O2 projection layer (`runtime_projections/activity/runs.py`) returns:
```python
class RunO2(BaseModel):
    run_id: str
    risk_level: RiskLevel  # NEW
    latency_bucket: LatencyBucket  # NEW
    evidence_health: EvidenceHealth  # NEW
    attention_reasons: List[AttentionReason]  # NEW
    ...
```

**Recommendation:** Use runtime projection endpoints (`/api/v1/runtime/activity/runs`) for O2+ panels.

---

## Category 4: CORRECT Mappings (Verified)

These endpoints exist and return the expected data shape.

| Panel ID | Endpoint | Returns | Status |
|----------|----------|---------|--------|
| OVR-SUM-HL-O1 | `/api/v1/activity/summary` | `ActivitySummaryResponse` | ✅ |
| INC-EV-ACT-O1 | `/api/v1/incidents` | `IncidentsResponse` | ✅ |
| INC-EV-ACT-O2 | `/api/v1/incidents/summary` | `IncidentsSummaryResponse` | ✅ |
| INC-EV-ACT-O3 | `/api/v1/incidents/metrics` | `IncidentsMetricsResponse` | ✅ |
| INC-EV-RES-O1 | `/api/v1/incidents` | `IncidentsResponse` | ✅ |
| INC-EV-RES-O2 | `/api/v1/recovery/actions` | `ActionListResponse` | ✅ |
| INC-EV-RES-O3 | `/api/v1/recovery/candidates` | `CandidateListResponse` | ✅ |
| INC-EV-RES-O4 | `/integration/graduation` | `HardenedGraduationResponse` | ✅ |
| INC-EV-RES-O5 | `/replay/{incident_id}/summary` | `IncidentSummaryResponse` | ✅ |
| INC-EV-HIST-O1 | `/api/v1/incidents` | `IncidentsResponse` | ✅ |
| INC-EV-HIST-O2 | `/api/v1/guard/incidents` | Guard incident list | ✅ |
| INC-EV-HIST-O4 | `/api/v1/ops/incidents` | `FounderIncidentListDTO` | ✅ |
| INC-EV-HIST-O5 | `/integration/stats` | `IntegrationStatsResponse` | ✅ |
| POL-GOV-ACT-O1 | `/api/v1/policy-proposals` | `ProposalListResponse` | ✅ |
| POL-GOV-ACT-O2 | `/api/v1/policy-proposals/stats/summary` | Summary stats | ✅ |
| POL-GOV-ACT-O4 | `/policy-layer/state` | `PolicyState` | ✅ |
| POL-GOV-ACT-O5 | `/policy-layer/metrics` | `PolicyMetrics` | ✅ |
| POL-GOV-DFT-O1 | `/api/v1/policy-proposals` | `ProposalListResponse` | ✅ |
| POL-GOV-DFT-O2 | `/policy-layer/versions` | Version list | ✅ |
| POL-GOV-DFT-O3 | `/policy-layer/versions/current` | Current version | ✅ |
| POL-GOV-DFT-O4 | `/policy-layer/conflicts` | Conflict list | ✅ |
| POL-GOV-DFT-O5 | `/policy-layer/dependencies` | Dependency graph | ✅ |
| POL-GOV-LIB-O1 | `/policy-layer/safety-rules` | Safety rule list | ✅ |
| POL-GOV-LIB-O2 | `/policy-layer/ethical-constraints` | Ethical constraints | ✅ |
| POL-GOV-LIB-O4 | `/guard/policies` | `CustomerPolicyConstraints` | ✅ |
| POL-GOV-LIB-O5 | `/policy-layer/temporal-policies` | Temporal policy list | ✅ |
| POL-LIM-THR-O1 | `/policy-layer/risk-ceilings` | Risk ceiling list | ✅ |
| POL-LIM-THR-O3 | `/api/v1/tenants/tenant/quota/runs` | `QuotaCheckResponse` | ✅ |
| POL-LIM-THR-O4 | `/api/v1/tenants/tenant/quota/tokens` | `QuotaCheckResponse` | ✅ |
| POL-LIM-THR-O5 | `/policy-layer/cooldowns` | `List[CooldownInfo]` | ✅ |
| POL-LIM-VIO-O1 | `/policy-layer/violations` | `List[PolicyViolation]` | ✅ |
| POL-LIM-VIO-O3 | `/costsim/v2/incidents` | CostSim incident list | ✅ |
| POL-LIM-VIO-O5 | `/costsim/divergence` | `DivergenceReportResponse` | ✅ |
| LOG-REC-SYS-O1 | `/guard/logs` | `CustomerLogListResponse` | ✅ |
| LOG-REC-SYS-O2 | `/health` | Health status | ✅ |
| LOG-REC-SYS-O3 | `/health/ready` | Readiness check | ✅ |
| LOG-REC-SYS-O4 | `/health/adapters` | Adapter health | ✅ |
| LOG-REC-SYS-O5 | `/health/skills` | Skill health | ✅ |
| LOG-REC-LLM-O1 | `/api/v1/runtime/traces` | Trace list | ✅ |
| LOG-REC-LLM-O2 | `/api/v1/activity/runs` | `ActivityResponse` | ✅ |
| LOG-REC-LLM-O5 | `/api/v1/traces/mismatches` | Mismatch list | ✅ |
| LOG-REC-AUD-O1 | `/api/v1/traces` | `TraceListResponse` | ✅ |
| LOG-REC-AUD-O2 | `/api/v1/rbac/audit` | `AuditResponse` | ✅ |

---

## Category 5: NULL Endpoints (Composite Panels)

These panels have `assumed_endpoint: null` because they require composite data from multiple sources or are interpretation panels.

| Panel ID | Panel Purpose | Data Sources Needed |
|----------|---------------|---------------------|
| ACT-LLM-SIG-O2 | Signal details | Runtime projection + traces |
| ACT-LLM-SIG-O3 | Signal correlation | Multiple run comparisons |
| ACT-LLM-SIG-O4 | Signal history | Aggregated signal data |
| ACT-LLM-SIG-O5 | Signal trends | Time-series aggregation |
| ACT-LLM-LIVE-O3 | Live execution context | WebSocket + run data |
| ACT-LLM-LIVE-O4 | Execution drill-down | Trace + evidence |
| ACT-LLM-LIVE-O5 | Execution timeline | Step-by-step trace |
| ACT-LLM-COMP-O2 | Completion analysis | Multiple run comparisons |
| ACT-LLM-COMP-O4 | Completion context | Run + agent data |
| ACT-LLM-COMP-O5 | Completion provenance | Full trace chain |
| OVR-SUM-HL-O2 | Highlight details | Multiple domain sources |
| OVR-SUM-HL-O4 | Highlight context | Cross-domain join |
| OVR-SUM-DC-O1 | Decision summary | Overview projections |
| OVR-SUM-DC-O2 | Decision details | Multiple proposal sources |
| OVR-SUM-DC-O3 | Decision context | Cross-domain |
| OVR-SUM-DC-O4 | Decision provenance | Full audit trail |
| OVR-SUM-CI-O2-O4 | Cost intelligence views | Multiple cost endpoints |

**Note:** NULL endpoints are acceptable - these panels will use the projection layer's composite assemblers.

---

## Priority Action Items

### P0 - Must Fix (Blocks SDSR Completion)

1. **Create `/api/v1/ops/incidents/patterns`** in `ops.py`
   - Returns: `List[IncidentPattern]` with `pattern_type`, `occurrence_count`, `correlation_strength`
   - Panel: INC-EV-ACT-O4 (facet: incident_resolution, criticality: HIGH)

### P1 - Should Fix (Affects Customer Experience)

2. **Fix path mismatch for `/api/v1/cus/activity`**
   - Current: `/api/v1/cus/activity/activity` (double segment)
   - Expected: `/api/v1/cus/activity`
   - Panel: LOG-REC-LLM-O3

3. **Create `/guard/costs/incidents`** in `cost_guard.py`
   - Returns: Cost-related incidents for customer console
   - Panel: POL-LIM-VIO-O2

### P2 - Should Fix (Consistency)

4. **Update 6 intent YAMLs** with correct endpoint paths:
   - INC-EV-HIST-O3: `/v1/incidents` → `/api/v1/incidents`
   - POL-LIM-VIO-O4: `/cost/anomalies` → `/api/v1/cost-intelligence/anomalies`
   - POL-LIM-THR-O2: `/cost/budgets` → `/api/v1/cost-intelligence/budgets`
   - POL-GOV-LIB-O3: `/v1/policies/active` → `/api/v1/v1-killswitch/policies/active`
   - POL-GOV-ACT-O3: `/api/v1/policies/requests` → `/api/v1/policy/requests`
   - LOG-REC-AUD-O4: `/status_history` → `/api/v1/status-history`

### P3 - Nice to Have (Advanced Data Shape)

5. **Enhance Activity runs endpoint** to return O2 schema fields:
   - Add `risk_level`, `evidence_health`, `latency_bucket` to `RunSummary`
   - Or: Update intent YAMLs to point to `/api/v1/runtime/activity/runs`

---

## Endpoint Route Map (Backend Truth)

### `/api/v1/activity/*` (activity.py)
- GET `/runs` → `ActivityResponse` ✅
- GET `/runs/{run_id}` → `RunSummary` ✅
- GET `/summary` → `ActivitySummaryResponse` ✅

### `/api/v1/incidents/*` (incidents.py)
- GET `` → `IncidentsResponse` ✅
- GET `/summary` → `IncidentsSummaryResponse` ✅
- GET `/metrics` → `IncidentsMetricsResponse` ✅
- GET `/{incident_id}` → `IncidentSummary` ✅

### `/api/v1/recovery/*` (recovery.py)
- POST `/suggest` → `SuggestResponse` ✅
- GET `/candidates` → `CandidateListResponse` ✅
- GET `/candidates/{id}` → `CandidateDetailResponse` ✅
- GET `/actions` → `ActionListResponse` ✅
- POST `/execute` → `ExecuteResponse` ✅

### `/policy-layer/*` (policy_layer.py)
- POST `/evaluate` → `PolicyEvaluationResult` ✅
- POST `/simulate` → `PolicyEvaluationResult` ✅
- GET `/state` → `PolicyState` ✅
- GET `/violations` → `List[PolicyViolation]` ✅
- GET `/risk-ceilings` → Risk ceiling list ✅
- GET `/safety-rules` → Safety rule list ✅
- GET `/ethical-constraints` → Ethical constraints ✅
- GET `/cooldowns` → `List[CooldownInfo]` ✅
- GET `/metrics` → `PolicyMetrics` ✅
- GET `/versions` → Version list ✅
- GET `/versions/current` → Current version ✅
- GET `/dependencies` → Dependency graph ✅
- GET `/conflicts` → Conflict list ✅
- GET `/temporal-policies` → Temporal policy list ✅

### `/api/v1/ops/*` (ops.py)
- GET `/pulse` → `SystemPulse` ✅
- GET `/customers` → `List[CustomerSegment]` ✅
- GET `/incidents` → `FounderIncidentListDTO` ✅
- GET `/incidents/{id}` → `FounderIncidentDetailDTO` ✅
- GET `/incidents/infra-summary` → Infra summary ✅
- GET `/incidents/patterns` → ❌ MISSING

### `/guard/*` (guard.py)
- GET `/status` → `GuardStatus` ✅
- GET `/incidents` → Incident list ✅
- GET `/incidents/{id}` → `IncidentDetailResponse` ✅
- GET `/logs` → ❌ (in guard_logs.py) ✅
- GET `/keys` → Key list ✅
- GET `/settings` → `TenantSettings` ✅

### `/api/v1/cost-intelligence/*` (cost_intelligence.py)
- GET `/dashboard` → `CostDashboard` ✅
- GET `/summary` → `CostSummary` ✅
- GET `/by-feature` → `CostByFeatureEnvelope` ✅
- GET `/anomalies` → `CostAnomaliesEnvelope` ✅
- GET `/budgets` → `List[BudgetResponse]` ✅

---

## Conclusion

The SDSR mapping has **80%+ coverage** with correct backend endpoints. The main gaps are:

1. **Missing Pattern Analysis** - `/api/v1/ops/incidents/patterns` endpoint
2. **Path Inconsistency** - 6 intent YAMLs have outdated/incorrect paths
3. **Data Shape Gap** - Activity runs endpoint returns basic schema, not O2

**Recommendation:** Fix P0 and P1 items before next SDSR observation cycle.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial audit based on backend function analysis |
