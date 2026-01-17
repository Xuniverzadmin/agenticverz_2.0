# Incidents Domain Audit

**Status:** PHASE 2-3 COMPLETE (Endpoints + Capabilities Implemented)
**Last Updated:** 2026-01-17
**Reference:** PIN-411 (Unified Facades), Migration 096

---

## 1. Panel Questions (15 Panels across 3 Topics)

### ACTIVE Topic (What failures are happening now?)

| O-Level | Panel ID | Panel Question | Status |
|---------|----------|----------------|--------|
| O1 | INC-EV-ACT-O1 | What active incidents exist right now? | DRAFT |
| O2 | INC-EV-ACT-O2 | How many incidents by severity/category? | DRAFT |
| O3 | INC-EV-ACT-O3 | What are the incident metrics? | DRAFT |
| O4 | INC-EV-ACT-O4 | What patterns do incidents show? | **IMPLEMENTED** |
| O5 | INC-EV-ACT-O5 | Attribution and escalation context? | **TODO** |

### HISTORICAL Topic (What failures happened before?)

| O-Level | Panel ID | Panel Question | Status |
|---------|----------|----------------|--------|
| O1 | INC-EV-HIST-O1 | Historical incidents list? | DRAFT |
| O2 | INC-EV-HIST-O2 | Guarded incident types? | **TODO** |
| O3 | INC-EV-HIST-O3 | Which incidents keep recurring? | **IMPLEMENTED** |
| O4 | INC-EV-HIST-O4 | Operational incident costs? | **TODO** |
| O5 | INC-EV-HIST-O5 | Integration statistics? | **TODO** |

### RESOLVED Topic (How were failures fixed?)

| O-Level | Panel ID | Panel Question | Status |
|---------|----------|----------------|--------|
| O1 | INC-EV-RES-O1 | Resolved incidents list? | DRAFT |
| O2 | INC-EV-RES-O2 | How was each incident resolved? | **TODO** |
| O3 | INC-EV-RES-O3 | What could be recovered? (Cost Impact) | **IMPLEMENTED** |
| O4 | INC-EV-RES-O4 | Final incident outcomes / Learnings? | **IMPLEMENTED** |
| O5 | INC-EV-RES-O5 | What should we learn from this? | **TODO** |

---

## 2. Capability Registry (Updated)

**Total:** 9 capabilities (5 existing + 4 new)
**Deleted:** 10 wrong mappings

| Capability | Status | Endpoint | Panel |
|------------|--------|----------|-------|
| `incidents.list` | OBSERVED | `/api/v1/incidents` | ACT-O1 |
| `incidents.summary` | OBSERVED | `/api/v1/incidents/summary` | ACT-O2 |
| `incidents.metrics` | OBSERVED | `/api/v1/incidents/metrics` | ACT-O3 |
| `incidents.historical_list` | OBSERVED | `/api/v1/incidents` | HIST-O1 |
| `incidents.resolved_list` | OBSERVED | `/api/v1/incidents` | RES-O1 |
| `incidents.patterns` | DECLARED | `/api/v1/incidents/patterns` | ACT-O4 |
| `incidents.recurring` | DECLARED | `/api/v1/incidents/recurring` | HIST-O3 |
| `incidents.cost_impact` | DECLARED | `/api/v1/incidents/cost-impact` | RES-O3 |
| `incidents.learnings` | DECLARED | `/api/v1/incidents/{id}/learnings` | RES-O4 |

**Note:** New capabilities are DECLARED (awaiting E2E validation per CAP-E2E-001)

---

## 3. API Routes (Incidents Facade)

| Endpoint | Method | Returns | Panels Served | Status |
|----------|--------|---------|---------------|--------|
| `/api/v1/incidents` | GET | Incidents list with filters | ACT-O1, HIST-O1, RES-O1 | EXISTS |
| `/api/v1/incidents/{id}` | GET | Incident detail | Detail views | EXISTS |
| `/api/v1/incidents/{id}/evidence` | GET | Cross-domain impact | ACT-O5 | EXISTS |
| `/api/v1/incidents/{id}/proof` | GET | Raw evidence | RES-O5 | EXISTS |
| `/api/v1/incidents/by-run/{run_id}` | GET | Incidents by run | Cross-domain | EXISTS |
| `/api/v1/incidents/summary` | GET | Aggregated counts | ACT-O2 | EXISTS |
| `/api/v1/incidents/metrics` | GET | Metrics breakdown | ACT-O3 | EXISTS |
| `/api/v1/incidents/patterns` | GET | Pattern detection | ACT-O4 | **NEW** |
| `/api/v1/incidents/recurring` | GET | Recurrence analysis | HIST-O3 | **NEW** |
| `/api/v1/incidents/cost-impact` | GET | Cost impact analysis | RES-O3 | **NEW** |
| `/api/v1/incidents/{id}/learnings` | GET | Post-mortem learnings | RES-O4 | **NEW** |

### Available Filters on `/api/v1/incidents`

| Filter | Values | Use Case |
|--------|--------|----------|
| `topic` | ACTIVE, RESOLVED | Topic separation |
| `lifecycle_state` | ACTIVE, ACKED, RESOLVED | Direct state filter |
| `severity` | critical, high, medium, low | Severity filter |
| `category` | string | Category filter |
| `cause_type` | LLM_RUN, SYSTEM, HUMAN | Cause type |
| `is_synthetic` | true/false | SDSR filter |
| `created_after` | datetime | Time filter |
| `created_before` | datetime | Time filter |
| `sort_by` | created_at, resolved_at, severity | Ordering |
| `sort_order` | asc, desc | Direction |

---

## 4. Panel Coverage Matrix

| Panel | Question | Capability | Route | Status |
|-------|----------|------------|-------|--------|
| ACT-O1 | Active incidents? | `incidents.list` | `/incidents?topic=ACTIVE` | **EXISTS** |
| ACT-O2 | Counts by severity? | `incidents.summary` | `/incidents/summary` | **EXISTS** |
| ACT-O3 | Incident metrics? | `incidents.metrics` | `/incidents/metrics` | **EXISTS** |
| ACT-O4 | Incident patterns? | `incidents.patterns` | `/incidents/patterns` | **IMPLEMENTED** |
| ACT-O5 | Attribution? | PARTIAL | `/incidents/{id}/evidence` | **PARTIAL** |
| HIST-O1 | Historical list? | `incidents.historical_list` | `/incidents?created_before=...` | **EXISTS** |
| HIST-O2 | Guarded types? | MISSING | Need filter or endpoint | **TODO** |
| HIST-O3 | Recurring incidents? | `incidents.recurring` | `/incidents/recurring` | **IMPLEMENTED** |
| HIST-O4 | Ops costs? | MISSING | Need cost data | **TODO** |
| HIST-O5 | Integration stats? | MISSING | Wrong domain | **TODO** |
| RES-O1 | Resolved list? | `incidents.resolved_list` | `/incidents?topic=RESOLVED` | **EXISTS** |
| RES-O2 | Resolution method? | PARTIAL | Model has `resolution_method` | **PARTIAL** |
| RES-O3 | Cost impact? | `incidents.cost_impact` | `/incidents/cost-impact` | **IMPLEMENTED** |
| RES-O4 | Learnings? | `incidents.learnings` | `/incidents/{id}/learnings` | **IMPLEMENTED** |
| RES-O5 | Raw proof? | PARTIAL | `/incidents/{id}/proof` | **PARTIAL** |

---

## 5. Coverage Summary

```
Panels with working capability:    9/15 (60%)  [was 5/15]
Panels with partial capability:    4/15 (27%)
Panels needing implementation:     2/15 (13%)  [HIST-O2, HIST-O5]
```

**Phase 2-3 Progress:**
- 4 new endpoints implemented (patterns, recurring, cost-impact, learnings)
- 4 new capabilities registered (DECLARED status per CAP-E2E-001)
- Migration 096 applied (new columns + incident_evidence table + v_incidents_o2 view)
- 3 L4 services created (IncidentPatternService, RecurrenceAnalysisService, PostMortemService)

---

## 6. Implementation Status

### 6.1 Implemented Endpoints (Phase 2-3)

| Panel | Endpoint | Service | Status |
|-------|----------|---------|--------|
| ACT-O4 | `/api/v1/incidents/patterns` | IncidentPatternService | **DONE** |
| HIST-O3 | `/api/v1/incidents/recurring` | RecurrenceAnalysisService | **DONE** |
| RES-O3 | `/api/v1/incidents/cost-impact` | Inline SQL | **DONE** |
| RES-O4 | `/api/v1/incidents/{id}/learnings` | PostMortemService | **DONE** |

### 6.2 Registered Capabilities (DECLARED)

| Capability ID | Panel | Description | Status |
|---------------|-------|-------------|--------|
| `incidents.patterns` | ACT-O4 | Pattern detection | DECLARED |
| `incidents.recurring` | HIST-O3 | Recurrence analysis | DECLARED |
| `incidents.cost_impact` | RES-O3 | Cost impact analysis | DECLARED |
| `incidents.learnings` | RES-O4 | Post-mortem learnings | DECLARED |

### 6.3 Model Enhancements (Migration 096)

| Field | Table | Purpose | Status |
|-------|-------|---------|--------|
| `resolution_method` | incidents | How incident was resolved (auto, manual, rollback) | **DONE** |
| `cost_impact` | incidents | USD impact, null if unknown | **DONE** |
| `incident_evidence` | new table | Append-only evidence records | **DONE** |
| `v_incidents_o2` | view | Analytics view with computed fields | **DONE** |

### 6.4 Remaining TODO

| Panel | What's Needed | Priority |
|-------|---------------|----------|
| HIST-O2 | Guarded incident types filter | LOW |
| HIST-O5 | Integration statistics (may belong to different domain) | LOW |
| ACT-O5 | Enhanced attribution context | MEDIUM |

### 6.5 Quick Wins to 75% (PENDING)

**Done:**
- `resolution_method` field added to Incident model
- `resolve()` method updated to accept `resolution_method` parameter
- `IncidentWriteService.resolve_incident()` updated to accept and set `resolution_method`

**Pending:**
1. **Evidence endpoint real data** (`/incidents/{id}/evidence`):
   - Query source run from `source_run_id`
   - Query related incidents (same category)
   - Query policy proposals linked to incident
   - Currently returns stub data

2. **Proof endpoint real data** (`/incidents/{id}/proof`):
   - Query `aos_traces` linked to incident
   - Query `incident_events` timeline
   - Currently returns stub data

3. **Cost impact population**:
   - No UI/API to SET `cost_impact` value on incidents
   - Field exists but always NULL

---

## 7. Data Flow

```
IncidentEngine.create_incident()
        │
        ▼
   incidents table (L6)
        │
        ▼
   /api/v1/incidents/* (L2 facade)
        │
        ▼
   UI Panel renders data
```

**Cross-Domain Propagation (SDSR Contract):**
```
Failed Run (Activity) → IncidentEngine → Incident Created → Policy Triggered
```

---

## 8. Related Files

| File | Purpose |
|------|---------|
| `backend/app/api/incidents.py` | Incidents facade (L2) |
| `backend/app/services/incident_engine.py` | Incident creation (L4) |
| `backend/app/services/incidents/incident_pattern_service.py` | Pattern detection (L4) |
| `backend/app/services/incidents/recurrence_analysis_service.py` | Recurrence analysis (L4) |
| `backend/app/services/incidents/postmortem_service.py` | Post-mortem learnings (L4) |
| `backend/app/models/killswitch.py` | Incident model (L6) |
| `backend/alembic/versions/096_incidents_domain_model.py` | Migration: new columns + table + view |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_incidents.*.yaml` | Capabilities |
| `design/l2_1/intents/AURORA_L2_INTENT_INC-*.yaml` | Panel intents |
| `scripts/preflight/check_incidents_domain.py` | CI check script |

---

## 9. Cleanup Log

**Date:** 2026-01-16

**Deleted Capabilities (wrong console/domain):**
- `incidents.guard_list` → `/api/v1/guard/incidents` - Guard console (founder)
- `incidents.ops_list` → `/api/v1/ops/incidents` - Ops console (operator)
- `incidents.v1_list` → `/v1/incidents` - Legacy endpoint
- `incidents.graduation_list` → `/integration/graduation` - Integration domain
- `incidents.integration_stats` → `/integration/stats` - Integration domain
- `incidents.replay_summary` → `/replay/{incident_id}/summary` - Replay domain
- `incidents.recovery_actions` → `/api/v1/recovery/actions` - Recovery domain
- `incidents.recovery_candidates` → `/api/v1/recovery/candidates` - Recovery domain
- `incidents.patterns` → `/api/v1/ops/incidents/patterns` - Ops console
- `incidents.infra_summary` → `/api/v1/ops/incidents/infra-summary` - Ops console

**Reason:** Customer console Incidents domain should only use `/api/v1/incidents/*` facade. Other consoles (Guard, Ops) and domains (Integration, Replay, Recovery) have separate concerns.

---

## 10. Architecture Notes

### Incidents Domain Question
> "What went wrong?"

### Object Family
- Incidents
- Violations
- Failures

### Lifecycle States
```
ACTIVE → ACKED → RESOLVED
```

### Severity Levels
- critical
- high
- medium
- low

### Cause Types
- LLM_RUN (from failed execution)
- SYSTEM (infrastructure failure)
- HUMAN (manual intervention)
