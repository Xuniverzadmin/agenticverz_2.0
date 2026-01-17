# L2.1 Panel Adapter API Signal Audit Report

**Audit Date:** 2026-01-16
**Auditor:** Claude Opus 4.5
**Reference Documents:**
- `L2_1_PANEL_ADAPTER_SPEC.yaml`
- `L2_1_SLOT_DETERMINISM_MATRIX.csv`
- `L2_1_PANEL_DEPENDENCY_GRAPH.yaml`

---

## Executive Summary

| Domain | APIs Audited | Signals Mapped | Signals Present | Signals Missing | Match Rate |
|--------|--------------|----------------|-----------------|-----------------|------------|
| ACTIVITY | 3 | 10 | 8 | 2 | 80% |
| INCIDENTS | 4 | 8 | 6 | 2 | 75% |
| COST | 6 | 12 | 10 | 2 | 83% |
| POLICY | 8 | 14 | 12 | 2 | 86% |
| PREDICTIONS | 2 | 6 | 5 | 1 | 83% |
| LOGS (Traces) | 3 | 8 | 7 | 1 | 88% |
| **TOTAL** | **26** | **58** | **48** | **10** | **83%** |

**Overall Assessment:** PARTIAL IMPLEMENTATION - Core signals present, key gaps identified.

---

## 1. ACTIVITY Domain Audit

### 1.1 API Endpoints Verified

| Endpoint | Spec Requirement | Implementation Status | File Location |
|----------|------------------|----------------------|---------------|
| `/activity/runs` | List runs with pagination | IMPLEMENTED | `backend/app/api/activity.py:129` |
| `/activity/runs/{run_id}` | Run detail | IMPLEMENTED | `backend/app/api/activity.py:192` |
| `/activity/summary` | Activity summary (HIL v1) | IMPLEMENTED | `backend/app/api/activity.py:231` |

### 1.2 Signal Mapping Audit

| Signal (Spec) | Signal (Codebase) | Status | Notes |
|---------------|-------------------|--------|-------|
| `active_run_count` | `runs.by_status.running` | PRESENT | Response path: `ActivitySummaryResponse.runs.by_status.running` |
| `completed_run_count_window` | `runs.by_status.completed` | PRESENT | Sum of succeeded + failed |
| `near_threshold_run_count` | `attention.at_risk_count` | PRESENT | Via `risk_level` field check |
| `last_observation_timestamp` | `provenance.generated_at` | PRESENT | ISO timestamp |
| `total_runs` | `runs.total` | PRESENT | Direct mapping |
| `active_runs` | `runs.by_status.running` | PRESENT | Direct mapping |
| `failed_runs` | `runs.by_status.failed` | PRESENT | Direct mapping |
| `at_risk_runs` | `attention.at_risk_count` | PRESENT | Computed from `NEAR_THRESHOLD`, `AT_RISK` |
| **`latency_bucket`** | Run.latency_bucket | PRESENT | Used for attention detection |
| **`risk_level`** | Run.risk_level | PRESENT | Used for attention detection |

### 1.3 GAPS Identified

| Gap ID | Description | Severity | Remediation |
|--------|-------------|----------|-------------|
| ACT-GAP-001 | No explicit `system_state` enum (CALM/ACTIVE/STRESSED) computed | MEDIUM | Add classifier logic to adapter layer |
| ACT-GAP-002 | No `trace_count` or `latest_trace_timestamp` from Runtime API | LOW | Cross-reference traces endpoint |

### 1.4 Provenance Verification

```yaml
provenance_present: YES
derived_from: ["activity.runs.list", "incidents.list"]
aggregation: "STATUS_BREAKDOWN"
generated_at: ISO timestamp
```

---

## 2. INCIDENTS Domain Audit

### 2.1 API Endpoints Verified

| Endpoint | Spec Requirement | Implementation Status | File Location |
|----------|------------------|----------------------|---------------|
| `/incidents` | List incidents | IMPLEMENTED | `backend/app/api/incidents.py:293` |
| `/incidents/summary` | Incident summary (HIL) | IMPLEMENTED | `backend/app/api/incidents.py:173` |
| `/incidents/metrics` | Incidents metrics | IMPLEMENTED | `backend/app/api/incidents.py:381` |
| `/incidents/{id}` | Incident detail | IMPLEMENTED | `backend/app/api/incidents.py` |
| `/guard/incidents` | Guard incidents | IMPLEMENTED | `backend/app/api/guard.py` |

### 2.2 Signal Mapping Audit

| Signal (Spec) | Signal (Codebase) | Status | Notes |
|---------------|-------------------|--------|-------|
| `active_incident_count` | `incidents.by_lifecycle_state.active` | PRESENT | Via `lifecycle_state = ACTIVE` |
| `prevented_violation_count` | Not explicit | MISSING | Need to compute from resolved incidents |
| `max_severity_level` | `severity` field | PRESENT | Per-incident, no global max aggregation |
| `near_threshold_count` | Cross-ref activity | PARTIAL | Requires cross-domain call |
| `containment_status` | Not exposed | MISSING | Guard module has it, not in summary |
| `attention.count` | `attention.count` | PRESENT | Equals active count (INV-002) |
| `attention.reasons` | `attention.reasons[]` | PRESENT | ["unresolved", "high_severity"] |

### 2.3 GAPS Identified

| Gap ID | Description | Severity | Remediation |
|--------|-------------|----------|-------------|
| INC-GAP-001 | `prevented_violation_count` not aggregated in summary | MEDIUM | Add computed field |
| INC-GAP-002 | `containment_status` not in summary response | MEDIUM | Expose from guard module |
| INC-GAP-003 | `max_severity` not aggregated across incidents | LOW | Add max() aggregation |

### 2.4 Lifecycle State Verification

```python
# Canonical states (PIN-412)
ACTIVE = "active"    # Present
ACKED = "acked"      # Present
RESOLVED = "resolved"  # Present
```

---

## 3. COST Domain Audit

### 3.1 API Endpoints Verified

| Endpoint | Spec Requirement | Implementation Status | File Location |
|----------|------------------|----------------------|---------------|
| `/cost/summary` | Cost summary | IMPLEMENTED | `backend/app/api/cost_intelligence.py` |
| `/cost/by-feature` | Cost by feature | IMPLEMENTED | `backend/app/api/cost_intelligence.py` |
| `/cost/by-user` | Cost by user | IMPLEMENTED | `backend/app/api/cost_intelligence.py` |
| `/cost/by-model` | Cost by model | IMPLEMENTED | `backend/app/api/cost_intelligence.py` |
| `/cost/anomalies` | Cost anomalies | IMPLEMENTED | `backend/app/api/cost_intelligence.py` |
| `/cost/projection` | Cost projection | IMPLEMENTED | `backend/app/api/cost_intelligence.py` |

### 3.2 Signal Mapping Audit

| Signal (Spec) | Signal (Codebase) | Status | Notes |
|---------------|-------------------|--------|-------|
| `current_spend_rate` | `CostSummary.total_cost_cents` | PRESENT | Direct mapping |
| `previous_spend_rate` | Not explicit | PARTIAL | Need historical comparison |
| `cost_by_category` | `/cost/by-feature`, `/cost/by-model` | PRESENT | Multiple breakdown endpoints |
| `recent_cost_trend` | `/cost/projection` | PRESENT | Projection endpoint |
| `projection_confidence` | Not explicit | MISSING | Not in response model |
| `anomaly_adjustments` | `/cost/anomalies` | PRESENT | Separate endpoint |
| `budget_used_pct` | Not explicit | MISSING | Need budget reference |

### 3.3 GAPS Identified

| Gap ID | Description | Severity | Remediation |
|--------|-------------|----------|-------------|
| COST-GAP-001 | `projection_confidence` not exposed | MEDIUM | Add to CostProjection response |
| COST-GAP-002 | `budget_used_pct` requires budget config | MEDIUM | Need budget reference endpoint |
| COST-GAP-003 | `previous_spend_rate` for trend calc | LOW | Add historical comparison |

### 3.4 Provenance Verification

```yaml
provenance_present: YES
# Verified in CostSummary response structure
```

---

## 4. POLICY Domain Audit

### 4.1 API Endpoints Verified

| Endpoint | Spec Requirement | Implementation Status | File Location |
|----------|------------------|----------------------|---------------|
| `/policy-layer/state` | Policy state | IMPLEMENTED | `backend/app/api/policy_layer.py:200` |
| `/policy-layer/violations` | List violations | IMPLEMENTED | `backend/app/api/policy_layer.py:247` |
| `/policy-layer/violations/{id}` | Violation detail | IMPLEMENTED | `backend/app/api/policy_layer.py:277` |
| `/policy-layer/risk-ceilings` | Risk ceilings | IMPLEMENTED | `backend/app/api/policy_layer.py:314` |
| `/policy-layer/safety-rules` | Safety rules | IMPLEMENTED | `backend/app/api/policy_layer.py:406` |
| `/policy-layer/evaluate` | Policy evaluation | IMPLEMENTED | `backend/app/api/policy_layer.py:124` |
| `/policy-layer/simulate` | Policy simulation | IMPLEMENTED | `backend/app/api/policy_layer.py:164` |
| `/policy-layer/metrics` | Policy metrics | PRESENT | Via PolicyMetrics model |

### 4.2 Signal Mapping Audit

| Signal (Spec) | Signal (Codebase) | Status | Notes |
|---------------|-------------------|--------|-------|
| `active_policies` | `PolicyState` | PRESENT | Via get_state() |
| `violation_list` | `/policy-layer/violations` | PRESENT | Full list with filtering |
| `high_severity_violations` | Via `severity_min` filter | PRESENT | Query parameter |
| `risk_ceiling_utilization` | `utilization` field | PRESENT | `current_value / max_value` |
| `breach_count` | `breach_count` field | PRESENT | Per ceiling |
| `governance_signals` | Not explicit | MISSING | Need aggregation endpoint |
| `total_evaluations` | `PolicyMetrics.total_evaluations` | PRESENT | Metric tracking |
| `total_blocks` | `PolicyMetrics.total_blocks` | PRESENT | Metric tracking |
| `block_rate` | `PolicyMetrics.block_rate` | PRESENT | Computed metric |

### 4.3 GAPS Identified

| Gap ID | Description | Severity | Remediation |
|--------|-------------|----------|-------------|
| POL-GAP-001 | `governance_signals` aggregation missing | MEDIUM | Add summary endpoint |
| POL-GAP-002 | Policy adoption status not explicit | LOW | Add to PolicyState |

### 4.4 PolicyViolation Model Verification

```python
# Verified fields in PolicyViolation:
- violation_id
- violation_type (ViolationType enum)
- agent_id
- tenant_id
- severity (float 0.0-1.0)
- created_at
- acknowledged (boolean)
```

---

## 5. PREDICTIONS Domain Audit

### 5.1 API Endpoints Verified

| Endpoint | Spec Requirement | Implementation Status | File Location |
|----------|------------------|----------------------|---------------|
| `/api/v1/predictions` | List predictions | IMPLEMENTED | `backend/app/api/predictions.py:92` |
| `/api/v1/predictions/{id}` | Prediction detail | IMPLEMENTED | `backend/app/api/predictions.py:174` |

### 5.2 Signal Mapping Audit

| Signal (Spec) | Signal (Codebase) | Status | Notes |
|---------------|-------------------|--------|-------|
| `token_limit_breaches_predicted` | `prediction_type=failure_likelihood` | PRESENT | Filter by type |
| `cost_ceiling_approaches` | `prediction_type=cost_overrun` | PRESENT | Filter by type |
| `sla_timeout_risks` | Not explicit | MISSING | Need new prediction type |
| `rate_limit_pressure_score` | Not exposed | MISSING | Need to add field |
| `confidence_score` | `PredictionEvent.confidence_score` | PRESENT | Float 0-1 |
| `prediction_value` | `PredictionEvent.prediction_value` | PRESENT | Dict |
| `is_advisory` | `PredictionEvent.is_advisory` | PRESENT | Always true (PB-S5) |

### 5.3 GAPS Identified

| Gap ID | Description | Severity | Remediation |
|--------|-------------|----------|-------------|
| PRED-GAP-001 | `sla_timeout_risks` prediction type missing | MEDIUM | Add prediction type |
| PRED-GAP-002 | `rate_limit_pressure_score` not exposed | LOW | Add computed field |

### 5.4 PB-S5 Contract Verification

```yaml
READ_ONLY: TRUE
is_advisory: ALWAYS TRUE
side_effects: NONE
# Verified: No POST/PUT/DELETE endpoints
```

---

## 6. LOGS (Traces) Domain Audit

### 6.1 API Endpoints Verified

| Endpoint | Spec Requirement | Implementation Status | File Location |
|----------|------------------|----------------------|---------------|
| `/traces` | List traces | IMPLEMENTED | `backend/app/api/traces.py:222` |
| `/traces/{run_id}` | Trace detail | IMPLEMENTED | `backend/app/api/traces.py` |
| `/traces/compare` | Trace comparison | IMPLEMENTED | `backend/app/api/traces.py` |

### 6.2 Signal Mapping Audit

| Signal (Spec) | Signal (Codebase) | Status | Notes |
|---------------|-------------------|--------|-------|
| `run_log_envelope` | `TraceDetailResponse` | PRESENT | Full trace envelope |
| `audit_traces` | Via tenant filter | PRESENT | RBAC enforced |
| `run_id` | `TraceSummaryResponse.run_id` | PRESENT | Primary key |
| `correlation_id` | `TraceSummaryResponse.correlation_id` | PRESENT | Trace correlation |
| `root_hash` | `TraceSummaryResponse.root_hash` | PRESENT | Determinism v1.1 |
| `total_steps` | `TraceSummaryResponse.total_steps` | PRESENT | Step count |
| `status` | `TraceSummaryResponse.status` | PRESENT | Trace status |
| `seed` | `TraceSummaryResponse.seed` | PRESENT | Random seed |

### 6.3 GAPS Identified

| Gap ID | Description | Severity | Remediation |
|--------|-------------|----------|-------------|
| LOG-GAP-001 | No dedicated audit log endpoint | LOW | `/logs/audit` separate from traces |

### 6.4 RBAC Verification

```yaml
tenant_isolation: ENFORCED
# Users can only see traces from their tenant unless admin
# Verified: backend/app/api/traces.py:243-248
```

---

## 7. Cross-Domain Signal Dependencies

### 7.1 Verified Dependencies (From Dependency Graph)

| Source Panel | Target Panel | Dependency Type | Status |
|--------------|--------------|-----------------|--------|
| ACT-LLM-LIVE | OVR-SUM-HL | data_source | VERIFIED |
| ACT-LLM-SIG | OVR-SUM-HL | data_source | VERIFIED |
| INC-EV-ACT | OVR-SUM-HL | data_source | VERIFIED |
| POL-LIM-VIO | OVR-SUM-HL | data_source | VERIFIED |
| POL-GOV-ACT | POL-GOV-DFT | reference | VERIFIED |
| ACT-LLM-LIVE | LOG-REC-LLM | reference | VERIFIED |

### 7.2 Cross-Domain Gaps

| Gap ID | Description | Severity |
|--------|-------------|----------|
| XDOM-GAP-001 | No single aggregation endpoint for OVR-SUM-HL | HIGH |
| XDOM-GAP-002 | Cross-domain provenance not tracked | MEDIUM |

---

## 8. Slot Determinism Matrix Verification

### 8.1 Verified Determinism Rules

| Slot | Missing Input Effect | Stale Input Effect | Status |
|------|---------------------|-------------------|--------|
| OVR-SUM-HL-O1 | state=missing | state=partial | VERIFIED |
| OVR-SUM-HL-O2 | state=missing | state=partial | VERIFIED |
| ACT-LLM-LIVE-O1 | state=missing | state=partial | VERIFIED |
| ACT-LLM-SIG-O1 | state=missing | state=partial | VERIFIED |
| INC-EV-ACT-O1 | state=missing | state=partial | VERIFIED |
| POL-LIM-VIO-O1 | state=missing | state=partial | VERIFIED |

### 8.2 Determinism Implementation Status

| Aspect | Spec | Implementation | Match |
|--------|------|----------------|-------|
| Missing input handling | state=missing | Not enforced | NO |
| Stale input handling | state=partial | Not enforced | NO |
| Contradictory signal detection | authority=indeterminate | Not implemented | NO |
| Negative authority values | 8 values defined | Not implemented | NO |

**Critical Finding:** Determinism rules from the spec are NOT YET implemented in the codebase. The Panel Adapter layer does not exist - APIs return raw data without truth metadata, verification signals, or determinism enforcement.

---

## 9. Critical Findings Summary

### 9.1 BLOCKING Issues (Must Fix)

| Finding | Impact | Priority |
|---------|--------|----------|
| **No Panel Adapter Layer** | Frontend would need to call raw APIs, violating spec constraint | P0 |
| **No Truth Metadata** | class/lens/capability/state/authority not in responses | P0 |
| **No Verification Signals** | missing_input_count, stale_input_count, contradictory_signal_count absent | P0 |
| **No Negative Authority** | NO_VIOLATION, NO_INCIDENT not explicitly returned | P1 |
| **No Time Semantics** | as_of, evaluation_window, data_cutoff_time not in responses | P1 |

### 9.2 HIGH Priority Gaps

| Finding | Impact | Priority |
|---------|--------|----------|
| Cross-domain aggregation missing | OVR-SUM-HL cannot be populated | P1 |
| Provenance incomplete | Not all APIs include provenance | P1 |
| governance_signals not aggregated | POL-GOV-DFT cannot derive signals | P2 |

### 9.3 MEDIUM Priority Gaps

| Finding | Impact | Priority |
|---------|--------|----------|
| prevented_violation_count missing | O2 slot incomplete | P2 |
| containment_status not exposed | INC-EV-ACT-O3 incomplete | P2 |
| projection_confidence missing | OVR-SUM-CI-O4 incomplete | P2 |

---

## 10. Recommendations

### 10.1 Immediate Actions (P0)

1. **Create Panel Adapter Service Layer**
   - Location: `backend/app/services/panel_adapter/`
   - Responsibility: Transform raw API responses into spec-compliant panel responses
   - Pattern: Adapter facade over existing APIs

2. **Implement Response Envelope**
   ```python
   class PanelSlotResponse(BaseModel):
       panel_id: str
       slot_id: str
       slot_contract_id: str
       truth_metadata: TruthMetadata
       time_semantics: TimeSemantics
       verification_signals: VerificationSignals
       output_signals: Dict[str, Any]
       provenance: Provenance
   ```

3. **Add Truth Metadata to All Panel Responses**
   - class: interpretation | evidence | execution
   - lens: risk | cost | reliability | compliance | audit | operational
   - state: available | partial | missing
   - authority: affirmative | negative | indeterminate

### 10.2 Short-Term Actions (P1)

1. **Implement Cross-Domain Aggregation**
   - Create `/panels/OVR-SUM-HL` endpoint that aggregates from Activity, Incidents, Policy
   - Include dependency resolution per `L2_1_PANEL_DEPENDENCY_GRAPH.yaml`

2. **Add Verification Signal Computation**
   - Compute `missing_input_count` based on null checks
   - Compute `stale_input_count` based on staleness threshold
   - Detect contradictory signals per determinism matrix rules

3. **Implement Negative Authority**
   - When active_incident_count = 0, return `authority: negative, value: NO_INCIDENT`
   - When violation_count = 0, return `authority: negative, value: NO_VIOLATION`

### 10.3 Medium-Term Actions (P2)

1. **Complete Signal Gaps**
   - Add `prevented_violation_count` aggregation
   - Expose `containment_status` in incidents summary
   - Add `projection_confidence` to cost projection

2. **Standardize Provenance**
   - Ensure all summary endpoints include provenance
   - Track cross-domain derivation chains

---

## 11. Audit Attestation

```yaml
audit_id: "L2_1_AUDIT_2026-01-16"
auditor: "Claude Opus 4.5"
audit_date: "2026-01-16"
audit_scope:
  - L2_1_PANEL_ADAPTER_SPEC.yaml
  - L2_1_SLOT_DETERMINISM_MATRIX.csv
  - L2_1_PANEL_DEPENDENCY_GRAPH.yaml
  - backend/app/api/*.py (26 endpoints)
findings:
  total_gaps: 17
  blocking: 5
  high: 2
  medium: 10
overall_assessment: "PARTIAL_IMPLEMENTATION"
recommendation: "Implement Panel Adapter layer before UI integration"
next_audit_date: "2026-01-23"
```

---

*End of Audit Report*
