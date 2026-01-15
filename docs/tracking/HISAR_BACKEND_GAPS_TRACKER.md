# HISAR Backend Gaps Tracker

**Status:** ACTIVE
**Last Updated:** 2026-01-15
**Related PIN:** PIN-427
**Sweep Date:** 2026-01-15T07:58:01

---

## Purpose

This document tracks all backend gaps discovered by HISAR/SDSR verification.
Gaps are reported here for backend team to resolve. Once fixed, re-run SDSR.

---

## Summary Dashboard

| Domain | Total Panels | BOUND | BLOCKED | Completion |
|--------|--------------|-------|---------|------------|
| OVERVIEW | 12 | 4 | 8 | 33% |
| ACTIVITY | 15 | 6 | 9 | 40% |
| INCIDENTS | 15 | 6 | 9 | 40% |
| POLICIES | 30 | 4 | 26 | 13% |
| LOGS | 15 | 3 | 12 | 20% |
| **TOTAL** | **87** | **23** | **64** | **26%** |

---

## Gap Taxonomy

| Code | Count | Meaning | Resolution |
|------|-------|---------|------------|
| AUTH_FAILURE | 24 | Endpoint requires auth, SDSR lacks credentials | Add SDSR public path or service account |
| ENDPOINT_MISSING | 23 | Route doesn't exist in backend | Create the endpoint |
| SDSR_FAILED | 13 | SDSR ran but failed verification | Fix response format or data |
| PROVENANCE_MISSING | 2 | HIL v1 provenance block not in response | Add provenance to response model |
| COHERENCY_FAILED | 2 | Route format doesn't match expected | Fix endpoint path |

---

## BOUND Panels (23)

| Domain | Panel | Endpoint | Capability |
|--------|-------|----------|------------|
| OVR | OVR-SUM-HL-O1 | `/api/v1/overview` | overview.highlights |
| OVR | OVR-SUM-HL-O2 | `/api/v1/overview` | overview.highlights |
| OVR | OVR-SUM-HL-O3 | `/api/v1/overview` | overview.highlights |
| OVR | OVR-SUM-HL-O4 | `/api/v1/overview` | overview.highlights |
| ACT | ACT-LLM-COMP-O2 | `/api/v1/activity/summary` | activity.summary |
| ACT | ACT-LLM-COMP-O5 | `/api/v1/runtime/traces` | activity.runtime_traces |
| ACT | ACT-LLM-LIVE-O1 | `/api/v1/activity/runs` | activity.live_runs |
| ACT | ACT-LLM-LIVE-O5 | `/health` | activity.health_status |
| ACT | ACT-LLM-SIG-O4 | `/api/v1/discovery` | activity.discovery_list |
| ACT | ACT-LLM-SIG-O5 | `/api/v1/discovery/stats` | activity.discovery_stats |
| INC | INC-EV-ACT-O1 | `/api/v1/incidents` | incidents.list |
| INC | INC-EV-ACT-O2 | `/api/v1/incidents/summary` | incidents.summary |
| INC | INC-EV-ACT-O3 | `/api/v1/incidents/metrics` | incidents.metrics |
| INC | INC-EV-HIST-O1 | `/api/v1/incidents` | incidents.historical_list |
| INC | INC-EV-RES-O1 | `/api/v1/incidents` | incidents.resolved_list |
| POL | POL-GOV-ACT-O1 | `/api/v1/policy-proposals` | policies.proposals_list |
| POL | POL-GOV-ACT-O2 | `/api/v1/policy-proposals/stats/summary` | policies.proposals_summary |
| POL | POL-GOV-DFT-O1 | `/api/v1/policy-proposals` | policies.drafts_list |
| LOG | LOG-REC-AUD-O4 | `/status_history` | logs.status_history |
| LOG | LOG-REC-AUD-O5 | `/status_history/stats` | logs.status_stats |
| LOG | LOG-REC-LLM-O1 | `/api/v1/runtime/traces` | logs.runtime_traces |
| LOG | LOG-REC-LLM-O2 | `/api/v1/activity/runs` | logs.activity_runs |
| LOG | LOG-REC-SYS-O2 | `/health` | logs.health_check |

---

## Active Gaps by Domain

### OVERVIEW Domain (8 BLOCKED)

| Panel | Endpoint | Gap | Status |
|-------|----------|-----|--------|
| OVR-SUM-CI-O1 | `/cost/summary` | PROVENANCE_MISSING | BLOCKED |
| OVR-SUM-CI-O2 | `/cost/by-feature` | SDSR_FAILED | BLOCKED |
| OVR-SUM-CI-O3 | `/cost/by-model` | SDSR_FAILED | BLOCKED |
| OVR-SUM-CI-O4 | `/cost/anomalies` | SDSR_FAILED | BLOCKED |
| OVR-SUM-DC-O1 | `/founder/timeline/decisions` | AUTH_FAILURE | BLOCKED |
| OVR-SUM-DC-O2 | `/founder/timeline/count` | AUTH_FAILURE | BLOCKED |
| OVR-SUM-DC-O3 | `/api/v1/recovery/stats` | AUTH_FAILURE | BLOCKED |
| OVR-SUM-DC-O4 | `/api/v1/feedback/stats/summary` | SDSR_FAILED | BLOCKED |

---

### ACTIVITY Domain (9 BLOCKED)

| Panel | Endpoint | Gap | Status |
|-------|----------|-----|--------|
| ACT-LLM-COMP-O1 | `/api/v1/activity/runs` | PROVENANCE_MISSING | BLOCKED |
| ACT-LLM-COMP-O3 | `/api/v1/tenants/runs` | ENDPOINT_MISSING | BLOCKED |
| ACT-LLM-COMP-O4 | `/api/v1/customer/activity` | SDSR_FAILED | BLOCKED |
| ACT-LLM-LIVE-O2 | `/api/v1/agents/agents` | ENDPOINT_MISSING | BLOCKED |
| ACT-LLM-LIVE-O3 | `/api/v1/agents/jobs` | COHERENCY_FAILED | BLOCKED |
| ACT-LLM-LIVE-O4 | `/api/v1/workers/business-builder/runs` | AUTH_FAILURE | BLOCKED |
| ACT-LLM-SIG-O1 | `/api/v1/feedback` | SDSR_FAILED | BLOCKED |
| ACT-LLM-SIG-O2 | `/api/v1/predictions` | AUTH_FAILURE | BLOCKED |
| ACT-LLM-SIG-O3 | `/api/v1/predictions/stats/summary` | AUTH_FAILURE | BLOCKED |

---

### INCIDENTS Domain (9 BLOCKED)

| Panel | Endpoint | Gap | Status |
|-------|----------|-----|--------|
| INC-EV-ACT-O4 | `/api/v1/ops/incidents/patterns` | ENDPOINT_MISSING | BLOCKED |
| INC-EV-ACT-O5 | `/api/v1/ops/incidents/infra-summary` | ENDPOINT_MISSING | BLOCKED |
| INC-EV-HIST-O2 | `/api/v1/guard/incidents` | ENDPOINT_MISSING | BLOCKED |
| INC-EV-HIST-O3 | `/v1/incidents` | AUTH_FAILURE | BLOCKED |
| INC-EV-HIST-O4 | `/api/v1/ops/incidents` | ENDPOINT_MISSING | BLOCKED |
| INC-EV-HIST-O5 | `/integration/stats` | AUTH_FAILURE | BLOCKED |
| INC-EV-RES-O2 | `/api/v1/recovery/actions` | AUTH_FAILURE | BLOCKED |
| INC-EV-RES-O3 | `/api/v1/recovery/candidates` | AUTH_FAILURE | BLOCKED |
| INC-EV-RES-O4 | `/integration/graduation` | AUTH_FAILURE | BLOCKED |
| INC-EV-RES-O5 | `/replay/{incident_id}/summary` | AUTH_FAILURE | BLOCKED |

---

### POLICIES Domain (26 BLOCKED)

| Panel | Endpoint | Gap | Status |
|-------|----------|-----|--------|
| POL-GOV-ACT-O3 | `/api/v1/policies/requests` | AUTH_FAILURE | BLOCKED |
| POL-GOV-ACT-O4 | `/policy-layer/state` | ENDPOINT_MISSING | BLOCKED |
| POL-GOV-ACT-O5 | `/policy-layer/metrics` | ENDPOINT_MISSING | BLOCKED |
| POL-GOV-DFT-O2 | `/policy-layer/versions` | ENDPOINT_MISSING | BLOCKED |
| POL-GOV-DFT-O3 | `/policy-layer/versions/current` | ENDPOINT_MISSING | BLOCKED |
| POL-GOV-DFT-O4 | `/policy-layer/conflicts` | ENDPOINT_MISSING | BLOCKED |
| POL-GOV-DFT-O5 | `/policy-layer/dependencies` | ENDPOINT_MISSING | BLOCKED |
| POL-GOV-LIB-O1 | `/policy-layer/safety-rules` | ENDPOINT_MISSING | BLOCKED |
| POL-GOV-LIB-O2 | `/policy-layer/ethical-constraints` | ENDPOINT_MISSING | BLOCKED |
| POL-GOV-LIB-O3 | `/v1/policies/active` | AUTH_FAILURE | BLOCKED |
| POL-GOV-LIB-O4 | `/guard/policies` | AUTH_FAILURE | BLOCKED |
| POL-GOV-LIB-O5 | `/policy-layer/temporal-policies` | ENDPOINT_MISSING | BLOCKED |
| POL-LIM-THR-O1 | `/policy-layer/risk-ceilings` | ENDPOINT_MISSING | BLOCKED |
| POL-LIM-THR-O2 | `/cost/budgets` | SDSR_FAILED | BLOCKED |
| POL-LIM-THR-O3 | `/api/v1/tenants/tenant/quota/runs` | ENDPOINT_MISSING | BLOCKED |
| POL-LIM-THR-O4 | `/api/v1/tenants/tenant/quota/tokens` | ENDPOINT_MISSING | BLOCKED |
| POL-LIM-THR-O5 | `/policy-layer/cooldowns` | ENDPOINT_MISSING | BLOCKED |
| POL-LIM-USG-O1 | `/api/v1/tenants/tenant/usage` | ENDPOINT_MISSING | BLOCKED |
| POL-LIM-USG-O2 | `/cost/dashboard` | SDSR_FAILED | BLOCKED |
| POL-LIM-USG-O3 | `/cost/by-user` | SDSR_FAILED | BLOCKED |
| POL-LIM-USG-O4 | `/cost/projection` | SDSR_FAILED | BLOCKED |
| POL-LIM-USG-O5 | `/billing/status` | ENDPOINT_MISSING | BLOCKED |
| POL-LIM-VIO-O1 | `/policy-layer/violations` | ENDPOINT_MISSING | BLOCKED |
| POL-LIM-VIO-O2 | `/guard/costs/incidents` | AUTH_FAILURE | BLOCKED |
| POL-LIM-VIO-O3 | `/costsim/v2/incidents` | AUTH_FAILURE | BLOCKED |
| POL-LIM-VIO-O4 | `/cost/anomalies` | SDSR_FAILED | BLOCKED |
| POL-LIM-VIO-O5 | `/costsim/divergence` | AUTH_FAILURE | BLOCKED |

---

### LOGS Domain (12 BLOCKED)

| Panel | Endpoint | Gap | Status |
|-------|----------|-----|--------|
| LOG-REC-AUD-O1 | `/api/v1/traces` | AUTH_FAILURE | BLOCKED |
| LOG-REC-AUD-O2 | `/api/v1/rbac/audit` | SDSR_FAILED | BLOCKED |
| LOG-REC-AUD-O3 | `/ops/actions/audit` | AUTH_FAILURE | BLOCKED |
| LOG-REC-LLM-O3 | `/api/v1/customer/activity` | SDSR_FAILED | BLOCKED |
| LOG-REC-LLM-O4 | `/api/v1/tenants/runs` | ENDPOINT_MISSING | BLOCKED |
| LOG-REC-LLM-O5 | `/api/v1/traces/mismatches/bulk-report` | COHERENCY_FAILED | BLOCKED |
| LOG-REC-SYS-O1 | `/guard/logs` | AUTH_FAILURE | BLOCKED |
| LOG-REC-SYS-O3 | `/health/ready` | AUTH_FAILURE | BLOCKED |
| LOG-REC-SYS-O4 | `/health/adapters` | AUTH_FAILURE | BLOCKED |
| LOG-REC-SYS-O5 | `/health/skills` | AUTH_FAILURE | BLOCKED |

---

## HIL v1 Provenance Standard

All interpretation panels require HIL v1 provenance metadata in responses.

### Required Fields

```yaml
provenance:
  generated_at: <ISO 8601 timestamp>
  aggregation: <list | summary | count | detail>
  source: <engine name>
  tenant_id: <optional, for scoped data>
  period: <optional, for time-bounded queries>
```

### Aggregation Types

| Type | Use Case | Example Endpoints |
|------|----------|-------------------|
| list | Paginated collections | /runs, /incidents |
| summary | Aggregated metrics | /summary, /stats |
| count | Simple counts | /count endpoints |
| detail | Single entity | /runs/{id} |

---

## Resolution Process

1. Backend team picks a gap from Active Gaps
2. Implements the required fix
3. Re-runs SDSR: `python3 aurora_sdsr_runner.py --panel <PANEL_ID>`
4. If PASS -> Gap moves to Resolved section
5. If FAIL -> Update gap details with new failure

---

## Priority Fixes

### P0: AUTH_FAILURE (24 panels)

Add these endpoints to public paths in `gateway_config.py`:

```python
# Recovery/Replay API
"/api/v1/recovery/",
"/replay/",

# Founder Timeline
"/founder/timeline/",

# Guards API
"/guard/",

# Policies API
"/v1/policies/",
"/api/v1/policies/",

# CostSim API
"/costsim/",

# Integration API
"/integration/",

# Health detailed endpoints
"/health/ready",
"/health/adapters",
"/health/skills",
```

### P1: ENDPOINT_MISSING (23 panels)

These endpoints need to be created:

| Endpoint | Purpose |
|----------|---------|
| `/api/v1/tenants/runs` | Tenant-scoped runs list |
| `/api/v1/agents/agents` | Active agents list |
| `/api/v1/ops/incidents/patterns` | Incident patterns analysis |
| `/api/v1/ops/incidents/infra-summary` | Infrastructure incidents |
| `/api/v1/guard/incidents` | Guard-generated incidents |
| `/api/v1/ops/incidents` | Ops view of incidents |
| `/policy-layer/*` | Policy layer endpoints (10+) |
| `/api/v1/tenants/tenant/usage` | Tenant usage stats |
| `/api/v1/tenants/tenant/quota/*` | Quota management |

### P2: PROVENANCE_MISSING (2 panels)

Add HIL v1 provenance to:
- `GET /api/v1/activity/runs`
- `GET /cost/summary`

### P3: COHERENCY_FAILED (2 panels)

Fix route format for:
- `/api/v1/agents/jobs` (ACT-LLM-LIVE-O3)
- `/api/v1/traces/mismatches/bulk-report` (LOG-REC-LLM-O5)

---

## Resolved Gaps

| Panel | Endpoint | Gap | Resolved Date | Fix |
|-------|----------|-----|---------------|-----|
| (none yet) | | | | |

---

## References

- `docs/memory-pins/PIN-422-hisar-execution-doctrine.md`
- `docs/memory-pins/PIN-427-hisar-backend-gaps-tracker.md` (Summary PIN)
- `docs/governance/SDSR_SYSTEM_CONTRACT.md`
- `backend/aurora_l2/tools/aurora_full_sweep.py`
- `backend/aurora_l2/tools/aurora_sdsr_runner.py`
