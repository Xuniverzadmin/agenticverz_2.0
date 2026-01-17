# ACTIVITY Domain API Audit

**Created:** 2026-01-16
**Domain:** ACTIVITY
**Subdomain:** LLM_RUNS
**Topics:** COMPLETED, LIVE, SIGNALS

---

## Available Endpoints (Customer-Facing)

| Endpoint | File | Schema Level | Purpose |
|----------|------|--------------|---------|
| `/api/v1/activity/runs` | `activity.py:129` | O1 | Basic run list |
| `/api/v1/activity/summary` | `activity.py:231` | O1 | Run summary stats |
| `/api/v1/customer/activity` | `customer_activity.py:56` | Customer-safe | L3 adapter pattern |
| `/api/v1/customer/activity/{run_id}` | `customer_activity.py:99` | Customer-safe | Run detail |
| `/api/v1/runtime/activity/runs` | `runtime_projections/activity/runs.py` | O2 | Enhanced with risk_level, evidence_health |

---

## Panel → Endpoint Mapping

### Topic: COMPLETED (ACT-LLM-COMP-*)

| Panel | Order | Expected Endpoint | Status | Action |
|-------|-------|-------------------|--------|--------|
| ACT-LLM-COMP-O1 | O1 | `/api/v1/activity/runs` | ✅ CORRECT | None |
| ACT-LLM-COMP-O2 | O2 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/activity/runs` |
| ACT-LLM-COMP-O4 | O4 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/activity/runs` |
| ACT-LLM-COMP-O5 | O5 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/activity/runs` |

### Topic: LIVE (ACT-LLM-LIVE-*)

| Panel | Order | Expected Endpoint | Status | Action |
|-------|-------|-------------------|--------|--------|
| ACT-LLM-LIVE-O1 | O1 | `/api/v1/activity/runs` | ✅ CORRECT | None |
| ACT-LLM-LIVE-O3 | O3 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/activity/runs` |
| ACT-LLM-LIVE-O4 | O4 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/activity/runs` |
| ACT-LLM-LIVE-O5 | O5 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/activity/runs` |

### Topic: SIGNALS (ACT-LLM-SIG-*)

| Panel | Order | Expected Endpoint | Status | Action |
|-------|-------|-------------------|--------|--------|
| ACT-LLM-SIG-O1 | O1 | `/api/v1/activity/runs` | ✅ CORRECT | None |
| ACT-LLM-SIG-O2 | O2 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/activity/runs` |
| ACT-LLM-SIG-O3 | O3 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/activity/runs` |
| ACT-LLM-SIG-O4 | O4 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/activity/runs` |
| ACT-LLM-SIG-O5 | O5 | `null` | ⚠️ NEEDS BINDING | Point to `/api/v1/runtime/activity/runs` |

---

## Summary

| Category | Count |
|----------|-------|
| Total Panels | 13 |
| ✅ Correct | 3 (O1 panels) |
| ⚠️ Needs Binding | 10 (O2+ panels with null) |
| ❌ Wrong Path | 0 |
| 🔴 Missing Endpoint | 0 |

---

## Data Shape Comparison

### O1 Schema (activity.py)

```python
class RunSummary(BaseModel):
    run_id: str
    status: str
    goal: str
    agent_id: str
    tenant_id: Optional[str]
    parent_run_id: Optional[str]
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    is_synthetic: bool
    synthetic_scenario_id: Optional[str]
```

### O2 Schema (runtime_projections/activity/runs.py)

```python
class RunSummary(BaseModel):
    # Identity & Scope
    run_id: str
    tenant_id: str | None
    project_id: str | None
    is_synthetic: bool
    source: str
    provider_type: str

    # Execution State
    state: str
    status: str
    started_at: datetime | None
    last_seen_at: datetime | None
    completed_at: datetime | None
    duration_ms: float | None

    # Risk & Health (Derived, pre-computed)
    risk_level: str           # O2 enhancement
    latency_bucket: str       # O2 enhancement
    evidence_health: str      # O2 enhancement
    integrity_status: str     # O2 enhancement

    # Impact Signals
    incident_count: int       # O2 enhancement
    policy_draft_count: int   # O2 enhancement
    policy_violation: bool    # O2 enhancement

    # Cost / Volume
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
```

---

## Recommended Actions

### Priority 1: Update O2+ Intent YAMLs

The O2, O3, O4, O5 panels currently have `assumed_endpoint: null`. They should point to the runtime projection endpoint which provides the enhanced O2 schema:

```yaml
capability:
  assumed_endpoint: /api/v1/runtime/activity/runs
  assumed_method: GET
```

### Affected Files (10 total)

```
design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-COMP-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-COMP-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-COMP-O5.yaml
design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-LIVE-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-LIVE-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-LIVE-O5.yaml
design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-SIG-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-SIG-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-SIG-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_ACT-LLM-SIG-O5.yaml
```

---

## Alternative: Customer Activity Adapter

For stricter L3 boundary enforcement, O1 panels could point to `/api/v1/customer/activity` instead of `/api/v1/activity/runs`. The customer activity adapter provides:

- Tenant isolation enforcement
- Customer-safe DTO transformation
- L2→L3→L4 layer compliance

This is optional but aligns with the adapter pattern documented in the fix plan.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial audit created |
