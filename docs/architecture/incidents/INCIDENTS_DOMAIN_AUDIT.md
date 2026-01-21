# Incidents Domain Audit

**Status:** POST-MIGRATION (V2 Complete)
**Last Updated:** 2026-01-18
**Reference:** INCIDENTS_DOMAIN_MIGRATION_PLAN.md (LOCKED)

---

## Migration Summary

The Incidents domain underwent a **complete architectural migration** on 2026-01-18:

| Before | After |
|--------|-------|
| Query-param topic filtering | Endpoint-scoped topic boundaries |
| Generic `/incidents` endpoint | Topic-scoped `/incidents/{topic}` endpoints |
| Frontend aggregation | Backend analytics endpoints |
| 5 capabilities (some 0/3 invariants) | 7 new OBSERVED capabilities |

**Full details:** See `INCIDENTS_DOMAIN_MIGRATION_PLAN.md`

---

## 1. Current Capability Registry (Post-Migration)

### Active Capabilities (OBSERVED - Use These)

| Capability | Endpoint | Invariants | Panels |
|------------|----------|------------|--------|
| `incidents.active_list` | `/api/v1/incidents/active` | 3/3 | INC-EV-ACT-O1, O2 |
| `incidents.resolved_list_v2` | `/api/v1/incidents/resolved` | 3/3 | INC-EV-RES-O1 |
| `incidents.historical_list_v2` | `/api/v1/incidents/historical` | 3/3 | INC-EV-HIST-O1 |
| `incidents.metrics_v2` | `/api/v1/incidents/metrics` | 3/3 | INC-EV-ACT-O3, RES-O3 |
| `incidents.historical_trend` | `/api/v1/incidents/historical/trend` | 3/3 | INC-EV-HIST-O1 |
| `incidents.historical_distribution` | `/api/v1/incidents/historical/distribution` | 3/3 | INC-EV-HIST-O2 |
| `incidents.historical_cost_trend` | `/api/v1/incidents/historical/cost-trend` | 3/3 | INC-EV-HIST-O4 |
| `incidents.detail` | `/api/v1/incidents/{id}` | 3/3 | Detail views |
| `incidents.evidence` | `/api/v1/incidents/{id}/evidence` | 3/3 | INC-EV-ACT-O5 |
| `incidents.proof` | `/api/v1/incidents/{id}/proof` | 3/3 | INC-EV-RES-O5 |
| `incidents.by_run` | `/api/v1/incidents/by-run/{run_id}` | 3/3 | Cross-domain |
| `incidents.patterns` | `/api/v1/incidents/patterns` | 3/3 | INC-EV-ACT-O4 |
| `incidents.recurring` | `/api/v1/incidents/recurring` | 3/3 | INC-EV-HIST-O3 |
| `incidents.cost_impact` | `/api/v1/incidents/cost-impact` | 3/3 | INC-EV-RES-O3 |

### Deprecated Capabilities (Do NOT Use)

| Capability | Previous Endpoint | Reason | Replaced By |
|------------|-------------------|--------|-------------|
| `incidents.list` | `/incidents` | Generic endpoint deprecated | `incidents.active_list` |
| `incidents.resolved_list` | `/incidents` | Wrong endpoint (0/3) | `incidents.resolved_list_v2` |
| `incidents.historical_list` | `/incidents` | Wrong endpoint | `incidents.historical_*` |
| `incidents.metrics` | `/incidents/cost-impact` | Wrong endpoint (0/3) | `incidents.metrics_v2` |
| `incidents.summary` | `/incidents` | Generic endpoint deprecated | `incidents.active_list` |
| `incidents.learnings` | `/incidents` | Failed invariants (0/3) | Needs proper endpoint |

---

## 2. API Routes (Current State)

### Topic-Scoped Endpoints (PRIMARY - Use These)

| Endpoint | Method | Topic | Purpose | Status |
|----------|--------|-------|---------|--------|
| `/api/v1/incidents/active` | GET | ACTIVE | List active incidents | OBSERVED |
| `/api/v1/incidents/resolved` | GET | RESOLVED | List resolved incidents | OBSERVED |
| `/api/v1/incidents/historical` | GET | HISTORICAL | List archived incidents | OBSERVED |
| `/api/v1/incidents/metrics` | GET | N/A | Incident metrics | OBSERVED |
| `/api/v1/incidents/historical/trend` | GET | HISTORICAL | Volume trend | OBSERVED |
| `/api/v1/incidents/historical/distribution` | GET | HISTORICAL | Type distribution | OBSERVED |
| `/api/v1/incidents/historical/cost-trend` | GET | HISTORICAL | Cost trend | OBSERVED |

### Instance Endpoints (SECONDARY)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/incidents/{id}` | GET | Incident detail | OBSERVED |
| `/api/v1/incidents/{id}/evidence` | GET | Cross-domain impact | OBSERVED |
| `/api/v1/incidents/{id}/proof` | GET | Raw evidence | OBSERVED |
| `/api/v1/incidents/{id}/learnings` | GET | Post-mortem | OBSERVED |

### Cross-Domain Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/incidents/by-run/{run_id}` | GET | Incidents by run | OBSERVED |
| `/api/v1/incidents/patterns` | GET | Pattern detection | OBSERVED |
| `/api/v1/incidents/recurring` | GET | Recurrence analysis | OBSERVED |
| `/api/v1/incidents/cost-impact` | GET | Cost impact analysis | OBSERVED |

### Deprecated Endpoint (Do NOT Use)

| Endpoint | Method | Status | Replacement |
|----------|--------|--------|-------------|
| `/api/v1/incidents` | GET | DEPRECATED | Use topic-scoped endpoints above |

**CI Guard:** `scripts/preflight/check_incidents_deprecation.py`
**Registry Lock:** `backend/AURORA_L2_CAPABILITY_REGISTRY/REGISTRY_LOCKS.yaml`

---

## 3. Panel Coverage Matrix (Post-Migration)

### ACTIVE Topic

| O-Level | Panel ID | Question | Capability | Endpoint | Status |
|---------|----------|----------|------------|----------|--------|
| O1 | INC-EV-ACT-O1 | What active incidents exist? | `incidents.active_list` | `/incidents/active` | BOUND |
| O2 | INC-EV-ACT-O2 | How many by severity? | `incidents.active_list` | `/incidents/active` | BOUND |
| O3 | INC-EV-ACT-O3 | Incident metrics? | `incidents.metrics_v2` | `/incidents/metrics` | BOUND |
| O4 | INC-EV-ACT-O4 | Incident patterns? | `incidents.patterns` | `/incidents/patterns` | BOUND |
| O5 | INC-EV-ACT-O5 | Attribution context? | `incidents.evidence` | `/incidents/{id}/evidence` | BOUND |

### RESOLVED Topic

| O-Level | Panel ID | Question | Capability | Endpoint | Status |
|---------|----------|----------|------------|----------|--------|
| O1 | INC-EV-RES-O1 | Resolved list? | `incidents.resolved_list_v2` | `/incidents/resolved` | BOUND |
| O2 | INC-EV-RES-O2 | Resolution method? | `incidents.detail` | `/incidents/{id}` | BOUND |
| O3 | INC-EV-RES-O3 | Cost impact? | `incidents.cost_impact` | `/incidents/cost-impact` | BOUND |
| O4 | INC-EV-RES-O4 | Learnings? | `incidents.detail` | `/incidents/{id}/learnings` | BOUND |
| O5 | INC-EV-RES-O5 | Raw proof? | `incidents.proof` | `/incidents/{id}/proof` | BOUND |

### HISTORICAL Topic

| O-Level | Panel ID | Question | Capability | Endpoint | Status |
|---------|----------|----------|------------|----------|--------|
| O1 | INC-EV-HIST-O1 | Historical trend? | `incidents.historical_trend` | `/incidents/historical/trend` | BOUND |
| O2 | INC-EV-HIST-O2 | Type distribution? | `incidents.historical_distribution` | `/incidents/historical/distribution` | BOUND |
| O3 | INC-EV-HIST-O3 | Recurring incidents? | `incidents.recurring` | `/incidents/recurring` | BOUND |
| O4 | INC-EV-HIST-O4 | Cost trend? | `incidents.historical_cost_trend` | `/incidents/historical/cost-trend` | BOUND |
| O5 | INC-EV-HIST-O5 | Pattern analysis? | `incidents.patterns` | `/incidents/patterns` | BOUND |

### Coverage Summary

```
Panels with BOUND capability:  15/15 (100%)
Panels with 3/3 invariants:    15/15 (100%)
```

---

## 4. Known Schema Gaps (Future Enhancement)

These are documented gaps that do NOT block the migration:

| Field | Status | Required For | Planned Fix |
|-------|--------|--------------|-------------|
| `contained_at` | NULL | Containment metrics | Future schema migration |
| `sla_target_seconds` | NULL | SLA metrics | Future schema migration |

**Important:** These are **schema enhancements**, not migration blockers.
Do NOT reopen the migration for these. Treat as separate workstream.

---

## 5. Data Flow (Post-Migration)

```
IncidentEngine.create_incident()
        │
        ▼
   incidents table (L6)
        │
        ├──────────────────────────────────────────────────┐
        │                                                  │
        ▼                                                  ▼
/api/v1/incidents/active (ACTIVE topic)    /api/v1/incidents/resolved (RESOLVED topic)
        │                                                  │
        ▼                                                  ▼
   UI Panel (INC-EV-ACT-*)                 UI Panel (INC-EV-RES-*)
```

**Cross-Domain Propagation (SDSR Contract):**
```
Failed Run (Activity) → IncidentEngine → Incident Created → Policy Triggered
```

---

## 6. Related Files

| File | Purpose |
|------|---------|
| `backend/app/api/incidents.py` | Incidents facade (L2) |
| `backend/app/services/incident_engine.py` | Incident creation (L4) |
| `backend/app/services/incidents/` | Domain services (L4) |
| `backend/app/models/killswitch.py` | Incident model (L6) |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_incidents.*.yaml` | Capabilities |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/REGISTRY_LOCKS.yaml` | Endpoint locks |
| `scripts/preflight/check_incidents_deprecation.py` | CI guard |
| `docs/architecture/incidents/INCIDENTS_DOMAIN_MIGRATION_PLAN.md` | Migration plan (LOCKED) |
| `docs/architecture/DOMAIN_MIGRATION_PLAYBOOK.md` | Reusable pattern |

---

## 7. Architecture Notes

### Incidents Domain Question
> "What went wrong?"

### Object Family
- Incidents
- Violations
- Failures

### Topic Model (Enforced at Boundary)
| Topic | Endpoint | Semantics |
|-------|----------|-----------|
| ACTIVE | `/incidents/active` | Unresolved, requires attention |
| RESOLVED | `/incidents/resolved` | Closed with resolution |
| HISTORICAL | `/incidents/historical` | Archived (>30 days) |

### Lifecycle States
```
ACTIVE → ACKED → RESOLVED → (HISTORICAL after retention window)
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

---

## 8. Migration History

| Date | Change | Reference |
|------|--------|-----------|
| 2026-01-18 | V2 migration LOCKED | INCIDENTS_DOMAIN_MIGRATION_PLAN.md |
| 2026-01-17 | Phase 2-3 endpoints added | Migration 096 |
| 2026-01-16 | Wrong capabilities cleaned up | Cleanup Log |
| 2026-01-15 | Initial audit | PIN-411 |

---

## 9. Maintenance Rules

### Do NOT
- Use generic `/incidents` endpoint for new panels
- Create capabilities that bind to `/incidents`
- "Simplify" registry locks
- Merge deprecated capabilities back
- Treat CI guards as optional

### DO
- Use topic-scoped endpoints for all new work
- Run CI guard before merging incidents changes
- Add new capabilities via SDSR observation
- Reference this audit before making changes
