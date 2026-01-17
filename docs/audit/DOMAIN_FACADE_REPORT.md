# Domain-Wise Facade Report

**Created:** 2026-01-16
**Purpose:** Map all facade adapters to actual backend APIs by domain

---

## Summary

| Domain | Facade File | Panels Fixed | Issue Resolved |
|--------|-------------|--------------|----------------|
| INCIDENTS | `guard_incidents_facade.py` | 8 | Decoupled from ops.py/FOPS |
| POLICIES | `guard_policy_layer_facade.py` | 13 | Added /api/v1 prefix |
| ACTIVITY | `guard_activity_facade.py` | 10 | Bound O2+ panels |
| OVERVIEW | `guard_overview_facade.py` | 11 | Bound all panels |
| **TOTAL** | **4 facades** | **42 panels** | |

---

## INCIDENTS Domain

### Facade: `/guard/*` (guard_incidents_facade.py)

| Panel | Old Endpoint (Founder-Only) | New Facade Endpoint | Actual API |
|-------|------------------------------|---------------------|------------|
| INC-EV-ACT-O4 | `/api/v1/ops/incidents/patterns` | `/guard/incidents/patterns` | `customer_incidents_facade.get_incident_patterns()` |
| INC-EV-ACT-O5 | `/api/v1/ops/incidents/infra-summary` | `/guard/incidents/summary` | `customer_incidents_facade.get_infra_summary()` |
| INC-EV-HIST-O2 | `/api/v1/guard/incidents` | `/guard/incidents` | Existing `guard.py:list_incidents()` |
| INC-EV-HIST-O4 | `/api/v1/ops/incidents` | `/api/v1/incidents` | Existing `incidents.py:list_incidents()` |
| INC-EV-HIST-O5 | `/integration/stats` | `/guard/integration/stats` | `customer_incidents_facade.get_integration_stats()` |
| INC-EV-RES-O2 | `/api/v1/recovery/actions` | `/guard/recovery/actions` | `customer_incidents_facade.get_recovery_actions()` |
| INC-EV-RES-O3 | `/api/v1/recovery/candidates` | `/guard/recovery/candidates` | `customer_incidents_facade.get_recovery_candidates()` |
| INC-EV-RES-O4 | `/integration/graduation` | `/guard/graduation` | `customer_incidents_facade.get_graduation_status()` |

### Files Created

```
backend/app/adapters/customer_incidents_facade.py  (L3 Adapter)
backend/app/api/guard_incidents_facade.py          (L2 API Route)
```

### Response Models

| Endpoint | Response Model |
|----------|---------------|
| `/guard/incidents/patterns` | `IncidentPatternsResponse` |
| `/guard/incidents/summary` | `IncidentInfraSummaryResponse` |
| `/guard/recovery/actions` | `RecoveryActionsResponse` |
| `/guard/recovery/candidates` | `RecoveryCandidatesResponse` |
| `/guard/integration/stats` | `IntegrationStatsResponse` |
| `/guard/graduation` | `GraduationStatusResponse` |

---

## POLICIES Domain

### Facade: `/api/v1/policy-layer/*` (Documentation Only)

No new facade code needed - just intent YAML corrections to add `/api/v1` prefix.

| Panel | Old Endpoint | Corrected Endpoint | Actual Router |
|-------|--------------|-------------------|---------------|
| POL-GOV-ACT-O4 | `/policy-layer/state` | `/api/v1/policy-layer/state` | `policy_layer.py` |
| POL-GOV-ACT-O5 | `/policy-layer/metrics` | `/api/v1/policy-layer/metrics` | `policy_layer.py` |
| POL-GOV-DFT-O2 | `/policy-layer/versions` | `/api/v1/policy-layer/versions` | `policy_layer.py` |
| POL-GOV-DFT-O3 | `/policy-layer/versions/current` | `/api/v1/policy-layer/versions/current` | `policy_layer.py` |
| POL-GOV-DFT-O4 | `/policy-layer/conflicts` | `/api/v1/policy-layer/conflicts` | `policy_layer.py` |
| POL-GOV-DFT-O5 | `/policy-layer/dependencies` | `/api/v1/policy-layer/dependencies` | `policy_layer.py` |
| POL-GOV-LIB-O1 | `/policy-layer/safety-rules` | `/api/v1/policy-layer/safety-rules` | `policy_layer.py` |
| POL-GOV-LIB-O2 | `/policy-layer/ethical-constraints` | `/api/v1/policy-layer/ethical-constraints` | `policy_layer.py` |
| POL-GOV-LIB-O5 | `/policy-layer/temporal-policies` | `/api/v1/policy-layer/temporal-policies` | `policy_layer.py` |
| POL-LIM-THR-O1 | `/policy-layer/risk-ceilings` | `/api/v1/policy-layer/risk-ceilings` | `policy_layer.py` |
| POL-LIM-THR-O5 | `/policy-layer/cooldowns` | `/api/v1/policy-layer/cooldowns` | `policy_layer.py` |
| POL-LIM-VIO-O1 | `/policy-layer/violations` | `/api/v1/policy-layer/violations` | `policy_layer.py` |
| POL-GOV-ACT-O3 | `/api/v1/policies/requests` | `/api/v1/policy/requests` | `policy.py` |

### Files Created

```
backend/app/api/guard_policy_layer_facade.py  (Documentation file with endpoint map)
```

---

## ACTIVITY Domain

### Facade: `/guard/activity/*` (guard_activity_facade.py)

| Panel | Old Endpoint | New Facade Endpoint | Schema Level |
|-------|--------------|---------------------|--------------|
| ACT-LLM-COMP-O1 | `/api/v1/activity/runs` | `/api/v1/activity/runs` | O1 (basic) |
| ACT-LLM-COMP-O2 | `null` | `/guard/activity/runs/o2` | O2 (enhanced) |
| ACT-LLM-COMP-O4 | `null` | `/guard/activity/runs/o2` | O2 (enhanced) |
| ACT-LLM-COMP-O5 | `null` | `/guard/activity/runs/o2` | O2 (enhanced) |
| ACT-LLM-LIVE-O1 | `/api/v1/activity/runs` | `/api/v1/activity/runs` | O1 (basic) |
| ACT-LLM-LIVE-O3 | `null` | `/guard/activity/runs/o2` | O2 (enhanced) |
| ACT-LLM-LIVE-O4 | `null` | `/guard/activity/runs/o2` | O2 (enhanced) |
| ACT-LLM-LIVE-O5 | `null` | `/guard/activity/runs/o2` | O2 (enhanced) |
| ACT-LLM-SIG-O1 | `/api/v1/activity/runs` | `/api/v1/activity/runs` | O1 (basic) |
| ACT-LLM-SIG-O2 | `null` | `/guard/activity/runs/o2` | O2 (enhanced) |
| ACT-LLM-SIG-O3 | `null` | `/guard/activity/runs/o2` | O2 (enhanced) |
| ACT-LLM-SIG-O4 | `null` | `/guard/activity/runs/o2` | O2 (enhanced) |
| ACT-LLM-SIG-O5 | `null` | `/guard/activity/runs/o2` | O2 (enhanced) |

### Files Created

```
backend/app/api/guard_activity_facade.py  (L2 API Route with O2 endpoint)
```

### O2 Schema Enhancements

The O2 endpoint (`/guard/activity/runs/o2`) provides enhanced fields:

```python
class ActivityRunO2(BaseModel):
    # Standard fields
    run_id: str
    status: str
    started_at: datetime
    completed_at: datetime

    # O2 Enhancements
    risk_level: str        # low, medium, high, critical
    latency_bucket: str    # fast, normal, slow, timeout
    evidence_health: str   # healthy, degraded, missing
    integrity_status: str  # verified, unverified, compromised
    incident_count: int
    policy_draft_count: int
    policy_violation: bool
```

---

## OVERVIEW Domain

### Facade: `/guard/overview/*` (guard_overview_facade.py)

| Panel | Old Endpoint | New Facade Endpoint | Topic |
|-------|--------------|---------------------|-------|
| OVR-SUM-HL-O1 | `/api/v1/activity/summary` | `/guard/overview/highlights` | HIGHLIGHTS |
| OVR-SUM-HL-O2 | `null` | `/guard/overview/highlights` | HIGHLIGHTS |
| OVR-SUM-HL-O4 | `null` | `/guard/overview/highlights` | HIGHLIGHTS |
| OVR-SUM-DC-O1 | `null` | `/guard/overview/decisions` | DECISIONS |
| OVR-SUM-DC-O2 | `null` | `/guard/overview/decisions` | DECISIONS |
| OVR-SUM-DC-O3 | `null` | `/guard/overview/decisions` | DECISIONS |
| OVR-SUM-DC-O4 | `null` | `/guard/overview/decisions` | DECISIONS |
| OVR-SUM-CI-O1 | `null` | `/guard/overview/costs` | COST_INTELLIGENCE |
| OVR-SUM-CI-O2 | `null` | `/guard/overview/costs` | COST_INTELLIGENCE |
| OVR-SUM-CI-O3 | `null` | `/guard/overview/costs` | COST_INTELLIGENCE |
| OVR-SUM-CI-O4 | `null` | `/guard/overview/costs` | COST_INTELLIGENCE |

### Files Created

```
backend/app/api/guard_overview_facade.py  (L2 API Route with 3 endpoints)
```

### Response Models

| Endpoint | Response Model | Data Sources |
|----------|---------------|--------------|
| `/guard/overview/highlights` | `HighlightsResponse` | incidents, policy_proposals, limit_breaches |
| `/guard/overview/decisions` | `DecisionsResponse` | incidents (pending ACK), policy_proposals (drafts) |
| `/guard/overview/costs` | `CostIntelligenceResponse` | limit_breaches, worker_runs |

---

## Router Registration

The new facade routers need to be registered in `main.py`:

```python
# In backend/app/main.py

from app.api.guard_incidents_facade import router as guard_incidents_facade_router
from app.api.guard_activity_facade import router as guard_activity_facade_router
from app.api.guard_overview_facade import router as guard_overview_facade_router

# Register facade routers
app.include_router(guard_incidents_facade_router)    # /guard/*
app.include_router(guard_activity_facade_router)     # /guard/activity/*
app.include_router(guard_overview_facade_router)     # /guard/overview/*
```

---

## Intent YAMLs Updated

### INCIDENTS Domain (8 files)

```
design/l2_1/intents/AURORA_L2_INTENT_INC-EV-ACT-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_INC-EV-ACT-O5.yaml
design/l2_1/intents/AURORA_L2_INTENT_INC-EV-HIST-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_INC-EV-HIST-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_INC-EV-HIST-O5.yaml
design/l2_1/intents/AURORA_L2_INTENT_INC-EV-RES-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_INC-EV-RES-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_INC-EV-RES-O4.yaml
```

### POLICIES Domain (13 files)

```
design/l2_1/intents/AURORA_L2_INTENT_POL-GOV-ACT-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-GOV-ACT-O5.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-GOV-DFT-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-GOV-DFT-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-GOV-DFT-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-GOV-DFT-O5.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-GOV-LIB-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-GOV-LIB-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-GOV-LIB-O5.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-LIM-THR-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-LIM-THR-O5.yaml
design/l2_1/intents/AURORA_L2_INTENT_POL-LIM-VIO-O1.yaml
(+ POL-GOV-ACT-O3 for path fix)
```

### ACTIVITY Domain (10 files)

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

### OVERVIEW Domain (11 files)

```
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-HL-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-HL-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-HL-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-DC-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-DC-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-DC-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-DC-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-CI-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-CI-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-CI-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-CI-O4.yaml
```

---

## Next Steps

1. **Register Routers**: Add the new facade routers to `main.py`
2. **Run Tests**: Verify facade endpoints work correctly
3. **Run Pipeline**: Execute `run_aurora_l2_pipeline.sh` to regenerate projection
4. **Frontend Wiring**: Update PanelContentRegistry with new endpoints

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-16 | Initial facade implementation and intent YAML updates |
