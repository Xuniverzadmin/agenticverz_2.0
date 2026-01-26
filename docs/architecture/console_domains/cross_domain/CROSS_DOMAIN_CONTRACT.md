# Cross-Domain Contract

**Status:** ENFORCED
**Effective:** 2026-01-17
**Scope:** Activity ↔ Incidents ↔ Policies domain boundaries
**Reference:** SDSR System Contract, Domain Audits

---

## 0. Prime Directive

> **Domains own data. Engines create effects. Cross-domain links are references, not copies.**

Each domain answers a different question:
- **Activity:** What ran / is running?
- **Incidents:** What went wrong?
- **Policies:** How is behavior defined?

No domain may:
- Recompute another domain's facts
- Write to another domain's tables
- Bypass cross-domain links with inferred data

---

## 1. Domain Ownership (Authoritative)

### 1.1 Activity Domain

**Question:** What executions occurred?

**Owns:**
| Table | Purpose |
|-------|---------|
| `runs` | Execution records |
| `aos_traces` | Trace data |
| `aos_trace_steps` | Step-level telemetry |
| `v_runs_o2` | Pre-computed run analytics |

**Creates via Engine:**
| Engine | Effect |
|--------|--------|
| WorkerRunner | runs, aos_traces, aos_trace_steps |

**References from:**
| Field | Points To |
|-------|-----------|
| `incidents.source_run_id` | `runs.run_id` |
| `policy_proposals.triggering_run_id` | `runs.run_id` |

---

### 1.2 Incidents Domain

**Question:** What failures occurred?

**Owns:**
| Table | Purpose |
|-------|---------|
| `incidents` | Failure records |
| `incident_evidence` | Supporting evidence |
| `incident_events` | Timeline events |
| `v_incidents_o2` | Pre-computed incident analytics |

**Creates via Engine:**
| Engine | Effect |
|--------|--------|
| IncidentEngine | incidents, incident_events |

**References from:**
| Field | Points To |
|-------|-----------|
| `policy_proposals.triggering_incident_id` | `incidents.id` |

**References to:**
| Field | Points To |
|-------|-----------|
| `incidents.source_run_id` | `runs.run_id` (Activity) |
| `incidents.llm_run_id` | `runs.id` (Activity) |

---

### 1.3 Policies Domain

**Question:** What rules govern behavior?

**Owns:**
| Table | Purpose |
|-------|---------|
| `policy_proposals` | Proposed policies |
| `policy_rules` | Active rules |
| `prevention_records` | Enforcement records |
| `default_guardrails` | Default policy pack |

**Creates via Engine:**
| Engine | Effect |
|--------|--------|
| PolicyProposalEngine | policy_proposals |
| PolicyEngine | policy_rules, prevention_records |

**References to:**
| Field | Points To |
|-------|-----------|
| `policy_proposals.triggering_incident_id` | `incidents.id` (Incidents) |
| `policy_proposals.triggering_run_id` | `runs.run_id` (Activity) |
| `prevention_records.run_id` | `runs.run_id` (Activity) |

---

## 2. Cross-Domain Propagation Rules

### Rule XD-001: Engines Create Cross-Domain Effects

> **Scenarios inject causes. Engines create effects.**

The causal chain is:
```
Failed Run (Activity)
    → IncidentEngine detects failure
    → Incident created (Incidents)
    → PolicyProposalEngine detects incident
    → Policy proposal created (Policies)
```

**Enforcement:**
- SDSR scenarios MUST NOT write to `incidents` or `policy_proposals`
- Cross-domain effects MUST be created by their owning engines
- If effect is missing → engine is broken, not scenario

---

### Rule XD-002: References, Not Copies

> **Never recompute another domain's facts.**

| Wrong | Right |
|-------|-------|
| Incidents stores `run_status` | Incidents stores `source_run_id`, queries `runs` |
| Policies stores `incident_severity` | Policies stores `triggering_incident_id`, queries `incidents` |
| Activity stores `policy_violation` | Activity stores `policy_violation` boolean (derived by PolicyEngine) |

**Exception:** Denormalized flags like `runs.policy_violation` are set BY the owning engine (PolicyEngine), not copied.

---

### Rule XD-003: No Cross-Domain Writes from Facades

> **L2 facades are read-only within their domain.**

| Facade | May Query | May NOT Query | May NOT Write |
|--------|-----------|---------------|---------------|
| `/api/v1/activity/*` | `runs`, `aos_traces`, `v_runs_o2` | — | Any table |
| `/api/v1/incidents/*` | `incidents`, `incident_evidence`, `v_incidents_o2` | — | Any table |
| `/api/v1/policy-proposals/*` | `policy_proposals`, `policy_rules` | — | Any table |

**Cross-domain queries for context** (e.g., `/incidents/{id}/evidence` querying `runs` for linked run) are **allowed** but must be read-only.

---

### Rule XD-004: Foreign Key Integrity

> **All cross-domain links MUST use proper foreign keys.**

| Link | From | To | Constraint |
|------|------|-----|------------|
| `incidents.source_run_id` | incidents | runs | FK or NULL |
| `incidents.llm_run_id` | incidents | runs | FK or NULL |
| `policy_proposals.triggering_incident_id` | policy_proposals | incidents | FK or NULL |
| `policy_proposals.triggering_run_id` | policy_proposals | runs | FK or NULL |
| `prevention_records.run_id` | prevention_records | runs | FK or NULL |

**Enforcement:** Migrations MUST define foreign keys. Orphaned references are data corruption.

---

## 3. Cross-Domain Query Patterns

### 3.1 Activity → Incidents (One-to-Many)

```sql
-- Find incidents caused by a run
SELECT i.*
FROM v_incidents_o2 i
WHERE i.source_run_id = :run_id
  AND i.tenant_id = :tenant_id;
```

**Use Case:** `/activity/runs/{id}/evidence` showing linked incidents

---

### 3.2 Incidents → Activity (Many-to-One)

```sql
-- Get run details for incident context
SELECT r.*
FROM v_runs_o2 r
WHERE r.run_id = (
    SELECT source_run_id FROM incidents WHERE id = :incident_id
);
```

**Use Case:** `/incidents/{id}/evidence` showing source run

---

### 3.3 Incidents → Policies (One-to-Many)

```sql
-- Find policy proposals triggered by an incident
SELECT pp.*
FROM policy_proposals pp
WHERE pp.triggering_incident_id = :incident_id
  AND pp.tenant_id = :tenant_id;
```

**Use Case:** `/incidents/{id}/evidence` showing triggered policies

---

### 3.4 Policies → Incidents (Many-to-One)

```sql
-- Get incident that triggered a policy proposal
SELECT i.*
FROM v_incidents_o2 i
WHERE i.incident_id = (
    SELECT triggering_incident_id FROM policy_proposals WHERE id = :proposal_id
);
```

**Use Case:** `/policy-proposals/{id}` showing root cause

---

## 4. SDSR Cross-Domain Expectations

### 4.1 Expected Propagation Chain

```yaml
# In SDSR scenario YAML
expected_propagation:
  - domain: activity
    assertion: run_exists
    run_id: ${run_id}
    status: failed

  - domain: incidents
    assertion: incident_created
    source_run_id: ${run_id}
    severity: high

  - domain: policies
    assertion: proposal_created
    triggering_incident_id: ${incident_id}
    status: pending
```

**Enforcement:**
- Scenarios DEFINE expectations
- Assertions VERIFY propagation
- Missing propagation = engine failure

---

### 4.2 Propagation Ownership Matrix

| Cause (Domain) | Effect (Domain) | Responsible Engine |
|----------------|-----------------|-------------------|
| Run failed (Activity) | Incident created (Incidents) | IncidentEngine |
| Incident HIGH/CRITICAL (Incidents) | Proposal created (Policies) | PolicyProposalEngine |
| Proposal approved (Policies) | Rule created (Policies) | PolicyEngine |
| Rule violated (Policies) | Prevention record (Policies) | PolicyEngine |
| Rule violated (Policies) | run.policy_violation = true (Activity) | PolicyEngine |

---

## 5. Forbidden Cross-Domain Actions

| Action | Why Forbidden |
|--------|---------------|
| Activity API writes to `incidents` | Incidents owns incidents |
| Incidents API writes to `policy_proposals` | Policies owns proposals |
| SDSR scenario writes to `incidents` | Engine creates effects |
| Facade computes cross-domain aggregate | Use pre-computed view or join |
| UI polls multiple domains for one panel | Single endpoint per panel |

---

## 6. Domain Boundary Enforcement

### CI Checks

| Check | Rule | Severity |
|-------|------|----------|
| XD-001 | No cross-domain writes in facades | ERROR |
| XD-002 | FK constraints defined for links | ERROR |
| XD-003 | Propagation expectations in SDSR | WARNING |
| XD-004 | No `INSERT INTO <other_domain_table>` | ERROR |

### Claude Constraints

Claude MUST NOT:
- Create endpoints that write to other domains
- Add fields that duplicate other domain's data
- Bypass engines for cross-domain effects
- Infer cross-domain state from UI requirements

Claude MUST:
- Use foreign keys for cross-domain links
- Query other domains read-only for context
- Stop and ask when cross-domain behavior is unclear

---

## 7. Cross-Domain API Allowlist

| Endpoint | May Reference |
|----------|---------------|
| `GET /incidents/{id}/evidence` | `runs` (source), `policy_proposals` (triggered) |
| `GET /activity/runs/{id}/evidence` | `incidents` (caused), `policy_proposals` (triggered) |
| `GET /policy-proposals/{id}` | `incidents` (trigger), `runs` (trigger) |

All other endpoints MUST stay within their domain.

---

## 8. Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CROSS-DOMAIN DATA FLOW                           │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │    ACTIVITY     │
    │  (What ran?)    │
    │                 │
    │  runs           │◄────────────────────────────┐
    │  aos_traces     │                             │
    │  aos_trace_steps│                             │
    │  v_runs_o2      │                             │
    └────────┬────────┘                             │
             │                                      │
             │ source_run_id                        │ triggering_run_id
             │ (FK)                                 │ run_id (FK)
             ▼                                      │
    ┌─────────────────┐                             │
    │    INCIDENTS    │                             │
    │ (What broke?)   │                             │
    │                 │                             │
    │  incidents      │◄─────────────────┐          │
    │  incident_evid. │                  │          │
    │  incident_events│                  │          │
    │  v_incidents_o2 │                  │          │
    └────────┬────────┘                  │          │
             │                           │          │
             │ triggering_incident_id    │          │
             │ (FK)                      │          │
             ▼                           │          │
    ┌─────────────────┐                  │          │
    │    POLICIES     │──────────────────┴──────────┘
    │(How defined?)   │
    │                 │
    │ policy_proposals│
    │ policy_rules    │
    │ prevention_rec. │
    └─────────────────┘

    ARROWS = Foreign Key References (read-only traversal)
    EFFECTS = Created by Engines only
```

---

## 9. Related Documents

| Document | Purpose |
|----------|---------|
| `SDSR_SYSTEM_CONTRACT.md` | Engine ownership rules |
| `ACTIVITY_DOMAIN_SQL.md` | Activity SQL definitions |
| `INCIDENTS_DOMAIN_SQL.md` | Incidents SQL definitions |
| `CROSS_DOMAIN_AUDIT_SUMMARY.md` | Current state audit |
| `check_cross_domain.py` | CI enforcement (TODO) |
