# PIN-412: Domain Design — Incidents & Policies (O1-O5 Architecture)

**Status:** V1_FROZEN
**Category:** Architecture / Domain Design / Aurora Runtime
**Created:** 2026-01-13
**Frozen:** 2026-01-13
**Author:** System
**Related:** PIN-411 (Activity Domain), PIN-370 (SDSR), PIN-352 (L2.1 Pipeline)
**Release:** `docs/releases/CUSTOMER_CONSOLE_V1.md`

---

## Summary

Comprehensive domain design for **Incidents** and **Policies** domains following the O1-O5 epistemic depth model established in PIN-411. This PIN tracks the architecture design and implementation progress for these domains.

**v1 Freeze Complete (2026-01-13):**
- Schema foundation: Migrations 087-090 applied
- O2 Runtime Projection APIs: INC-RT-O2, GOV-RT-O2, LIM-RT-O2
- Integrity architecture: Option C (separate tables per entity type)
- UX invariants: ACKED as badge inside Active topic

---

## Terminology Lock (FROZEN)

| Old Term | New Term | Rationale |
|----------|----------|-----------|
| Runs | **LLM Runs** | Removes ambiguity, anchors product around what is governed |

This applies across all domains:
- Activity → LLM Runs (subdomain)
- Incidents → linked to LLM Runs
- Policies → govern LLM Runs

---

## Domain Overview

### Five Frozen Domains (Customer Console v1)

| Domain | Question | Status |
|--------|----------|--------|
| Overview | Is the system okay right now? | Future |
| **Activity** | What ran / is running? | **CLOSED** (PIN-411) |
| **Incidents** | What went wrong? | **V1_FROZEN** |
| **Policies** | How is behavior defined? | **V1_FROZEN** |
| Logs | What is the raw truth? | Future |

---

## Domain 1: Incidents

### Purpose

What went wrong, what is being handled, what was handled before.

### Mental Model

> Incidents are **effects**, not executions.
> They are downstream of **LLM Runs**, **Policies**, and **Limits**.

### Structure

```
Incidents (Domain)
└── Events (Subdomain)
    ├── Active      ← Unresolved, may require attention
    ├── Resolved    ← Handled and closed
    └── Historical  ← Pattern recognition, not action
```

---

### Topic 1: Active

#### O1 — Navigation Only

| Panel | Description | CTA |
|-------|-------------|-----|
| Active Incident Overview | Unresolved incidents affecting LLM Runs | View Active Incidents |
| Severity Distribution | How incidents are distributed by severity | Inspect by Severity |
| Impact Scope | Which LLM Runs are affected | See Impacted LLM Runs |
| Decision Required | Incidents needing human decision | Review Required Actions |

**Invariant:** No counts. No metrics. No loading states.

#### O2 — List/Table (INC-RT-O2 — IMPLEMENTED)

**Endpoint:**
```
GET /api/v1/runtime/incidents?topic=ACTIVE
```

**Topic Mapping (FROZEN):**
- `topic=ACTIVE` → returns ACTIVE + ACKED lifecycle states
- `topic=RESOLVED` → returns RESOLVED only
- ACKED shown as badge in UI (not separate topic)

**Columns (locked):**

| Column | Source | Description |
|--------|--------|-------------|
| incident_id | incidents | Primary key |
| lifecycle_state | incidents | ACTIVE, ACKED, RESOLVED |
| severity | incidents | critical, high, medium, low |
| category | incidents | Incident category |
| title | incidents | Incident title |
| llm_run_id | incidents | Linked LLM Run |
| cause_type | incidents | LLM_RUN, SYSTEM, HUMAN |
| created_at | incidents | When created |
| resolved_at | incidents | When resolved (nullable) |

**Filters:**
- severity
- category
- cause_type
- created_after / created_before

#### O3 — Incident Detail

**Sections:**
1. Incident summary
2. Timeline (created → escalated → mitigated?)
3. Affected **LLM Runs** (links)
4. Triggering policy / limit
5. Current handling state

#### O4 — Evidence (Preflight only)

| Category | Evidence Type |
|----------|---------------|
| D | Policy decisions that triggered |
| B | Activity evidence of offending LLM Runs |
| G | Provider evidence (timeouts, errors) |
| H | Environment context |

#### O5 — Proof (Preflight only)

- Raw trace spans
- Hash chain
- Integrity verification
- Non-repudiable record

---

### Topic 2: Resolved

#### O1 — Navigation Only

| Panel | Description | CTA |
|-------|-------------|-----|
| Resolution Summary | What has been closed | View Resolved |
| Resolution Time Trends | Time-to-resolve patterns | Analyze Trends |
| Mitigation Types | How incidents were resolved | View by Mitigation |
| Policy Effectiveness | Did policies help? | Analyze Effectiveness |

#### O2 — List/Table

**Endpoint:**
```
GET /api/v1/runtime/incidents?state=RESOLVED
```

**Additional Columns:**

| Column | Source |
|--------|--------|
| resolution_type | incidents |
| time_to_resolve | derived |
| resolved_at | incidents |
| resolved_by | incidents |
| linked_policy_change | policy_proposals |

#### O3 — Detail

Adds:
- Resolution notes
- Decisions made
- Post-mortem summary (if any)

---

### Topic 3: Historical

#### O1 — Navigation Only

| Panel | Description | CTA |
|-------|-------------|-----|
| Incident Volume Over Time | Pattern recognition | View Trends |
| Repeated Causes | Recurring issues | Analyze Causes |
| Provider Correlation | Provider-specific patterns | View by Provider |
| Limit Effectiveness | Are limits preventing incidents? | Analyze Limits |

#### O2 — List/Table

**Endpoint:**
```
GET /api/v1/runtime/incidents?state=HISTORICAL
```

**Additional Columns:**

| Column | Source |
|--------|--------|
| recurrence_count | derived |
| similar_incident_group_id | incidents |

---

## Domain 2: Policies

### Purpose

How is behavior defined, constrained, and evolved?

### Mental Model

> Policies are **causes**, not effects.
> They govern **LLM Runs** and create **Incidents** when violated.

### Structure

```
Policies (Domain)
├── Governance (Subdomain)    ← IN DESIGN
│   ├── Active Rules
│   ├── Proposals
│   └── Retired
└── Limits (Subdomain)        ← PENDING
    ├── Budget Limits
    ├── Rate Limits
    └── Threshold Limits
```

---

### Subdomain: Governance

#### Topic 1: Active Rules

##### O1 — Navigation Only

| Panel | Description | CTA |
|-------|-------------|-----|
| Active Policy Overview | Rules currently enforcing constraints | View Active Policies |
| Enforcement Distribution | By enforcement mode | Inspect by Mode |
| Recent Triggers | Recently triggered policies | View Recently Triggered |
| Coverage Gaps | Areas without coverage | Review Uncovered |

##### O2 — List/Table (GOV-RT-O2 — IMPLEMENTED)

**Endpoint:**
```
GET /api/v1/runtime/policies/rules?status=ACTIVE
```

**Columns (locked):**

| Column | Source | Description |
|--------|--------|-------------|
| rule_id | policy_rules | Primary key |
| name | policy_rules | Human-readable name |
| description | policy_rules | Rule description |
| rule_type | policy_rules | Rule type |
| enforcement_mode | policy_rules | BLOCK, WARN, LOG, DRY_RUN |
| scope | policy_rules | GLOBAL, TENANT, PROJECT, AGENT |
| status | policy_rules | ACTIVE, RETIRED |
| trigger_count_30d | derived | Triggers in last 30 days |
| last_triggered_at | derived | Most recent trigger |
| created_at | policy_rules | When created |
| integrity_status | policy_rule_integrity | VERIFIED, DEGRADED, FAILED |
| integrity_score | policy_rule_integrity | 0.000-1.000 |

**Filters:**
- enforcement_mode
- scope
- created_after / created_before

##### O3 — Rule Detail

**Sections:**
1. Rule Definition (name, description, mode, scope, conditions)
2. Provenance (created by, source proposal, parent rule)
3. Enforcement History (timeline, affected LLM Runs)
4. Current Status (active since, last modified, pending proposals)

##### O4 — Evidence (Preflight only)

| Category | Evidence Type |
|----------|---------------|
| D | Decisions this rule caused |
| B | LLM Runs affected by this rule |
| G | Incidents prevented/caused |
| H | Evolution history |

##### O5 — Proof (Preflight only)

- Rule definition hash at creation
- Modification hashes with timestamps
- Enforcement decision hashes
- Hash chain verification

---

#### Topic 2: Proposals

##### O1 — Navigation Only

| Panel | Description | CTA |
|-------|-------------|-----|
| Pending Proposals | Changes being considered | Review Pending |
| System-Generated | Auto-recommended policies | View Recommendations |
| Awaiting Approval | Need human decision | Review Decisions |
| Recently Rejected | Rejected proposals | View Rejected |

##### O2 — List/Table

**Endpoint:**
```
GET /api/v1/runtime/policies/proposals?status=PENDING
```

**Columns:**

| Column | Source | Description |
|--------|--------|-------------|
| proposal_id | policy_proposals | Primary key |
| proposal_type | policy_proposals | CREATE, MODIFY, RETIRE |
| target_rule_id | policy_proposals | NULL for CREATE |
| proposed_by | policy_proposals | SYSTEM, HUMAN |
| reason | policy_proposals | Trigger reason |
| triggering_run_id | policy_proposals | LLM Run that prompted this |
| triggering_incident_id | policy_proposals | Incident that prompted this |
| status | policy_proposals | PENDING, APPROVED, REJECTED, EXPIRED |
| created_at | policy_proposals | When proposed |
| expires_at | policy_proposals | Auto-expire timestamp |
| confidence_score | policy_proposals | For system-generated (0.0-1.0) |

##### O3 — Proposal Detail

**Sections:**
1. Proposal Summary (what, why, diff view for MODIFY)
2. Impact Analysis (affected LLM Runs, trigger frequency, false positive rate)
3. Evidence (triggering LLM Run, triggering Incident, pattern analysis)
4. Decision History (status, reviewer, notes)

---

#### Topic 3: Retired

##### O1 — Navigation Only

| Panel | Description | CTA |
|-------|-------------|-----|
| Recently Retired | What was retired | View Recently Retired |
| Retirement Reasons | Why rules were retired | Analyze Patterns |
| Superseded Rules | Evolution chains | View Chains |
| Reactivation Candidates | Candidates for reactivation | Review Candidates |

##### O2 — List/Table

**Endpoint:**
```
GET /api/v1/runtime/policies/rules?status=RETIRED
```

**Additional Columns:**

| Column | Source |
|--------|--------|
| retired_at | policy_rules |
| retired_by | policy_rules |
| retirement_reason | policy_rules |
| superseded_by | policy_rules (FK) |
| total_triggers | derived |
| false_positive_rate | derived |

---

### Subdomain: Limits

#### Purpose

Quantitative constraints that implement governance intent.

#### Mental Model

> Limits are **numbers with consequences**.
> They enforce what Governance declares.
> Violations create **Incidents**, not warnings.

#### Structure

```
Policies (Domain)
├── Governance (Subdomain)    ← DESIGNED
└── Limits (Subdomain)        ← THIS DESIGN
    ├── Budget Limits         ← Cost, token allocation
    ├── Rate Limits           ← Requests per time window
    └── Threshold Limits      ← Latency, duration, retry
```

---

#### Topic 1: Budget Limits

##### O1 — Navigation Only

| Panel | Description | CTA |
|-------|-------------|-----|
| Budget Overview | Active cost and token limits | View Budget Limits |
| Utilization Status | How close to limits across scopes | Inspect Utilization |
| Near-Threshold Alerts | Budgets approaching exhaustion | View At-Risk Budgets |
| Recently Breached | Limits that were exceeded | View Breaches |

##### O2 — List/Table (LIM-RT-O2 — IMPLEMENTED)

**Endpoint:**
```
GET /api/v1/runtime/policies/limits?type=BUDGET
```

**Columns (locked):**

| Column | Source | UI Label |
|--------|--------|----------|
| limit_id | limits | ID |
| name | limits | Name |
| limit_category | limits | Category |
| limit_type | limits | Type |
| scope | limits | Scope |
| enforcement | limits | Enforcement |
| status | limits | Status |
| max_value | limits | **Limit Value** |
| window_seconds | limits | Window (for RATE) |
| reset_period | limits | Reset Period (for BUDGET) |
| integrity_status | limit_integrity | Integrity |
| integrity_score | limit_integrity | Integrity Score |
| breach_count_30d | derived | Breaches (30d) |
| last_breached_at | derived | Last Breached |
| created_at | limits | Created |

**Filters:**
- scope
- enforcement
- created_after / created_before

##### O3 — Budget Limit Detail

**Sections:**
1. Limit Definition (name, type, scope, max value, reset period)
2. Current Status (utilization, timeline, time to reset)
3. Breach History (timeline, affected LLM Runs, recovery actions)
4. Linked Governance (policy rules that reference this limit)

---

#### Topic 2: Rate Limits

##### O1 — Navigation Only

| Panel | Description | CTA |
|-------|-------------|-----|
| Rate Limit Overview | Active rate limits | View Rate Limits |
| Current Throughput | Real-time request rates | Monitor Throughput |
| Throttling Active | Limits currently throttling | View Throttled |
| Provider Limits | External provider rate limits | View Provider Limits |

##### O2 — List/Table

**Endpoint:**
```
GET /api/v1/runtime/policies/limits?type=RATE
```

**Columns:**

| Column | Source | Description |
|--------|--------|-------------|
| limit_id | limits | Primary key |
| name | limits | Human-readable name |
| limit_type | limits | REQUESTS_PER_SECOND, REQUESTS_PER_MINUTE, REQUESTS_PER_HOUR |
| scope | limits | GLOBAL, TENANT, PROJECT, AGENT, PROVIDER |
| max_value | limits | Max requests in window |
| window_seconds | limits | Time window size |
| current_rate | derived | Current request rate |
| utilization_pct | derived | current_rate / max_value |
| throttle_count_30d | derived | Times throttled |
| last_throttle_at | derived | Most recent throttle |
| status | derived | OK, NEAR_THRESHOLD, THROTTLING |
| enforcement | limits | REJECT, QUEUE, DEGRADE |

##### O3 — Rate Limit Detail

**Sections:**
1. Limit Definition (name, type, scope, provider, max value, window)
2. Current Status (current rate vs max, queue depth, degradation level)
3. Throttle History (timeline, duration, affected LLM Runs)
4. Provider Context (external provider limits, headroom)

---

#### Topic 3: Threshold Limits

##### O1 — Navigation Only

| Panel | Description | CTA |
|-------|-------------|-----|
| Threshold Overview | Active performance limits | View Thresholds |
| SLA Status | Thresholds tied to SLAs | View SLA Thresholds |
| Violation Patterns | Recurring threshold violations | Analyze Patterns |
| Retry Limits | Retry budget exhaustion | View Retry Limits |

##### O2 — List/Table

**Endpoint:**
```
GET /api/v1/runtime/policies/limits?type=THRESHOLD
```

**Columns:**

| Column | Source | Description |
|--------|--------|-------------|
| limit_id | limits | Primary key |
| name | limits | Human-readable name |
| limit_type | limits | LATENCY_MS, DURATION_MS, RETRY_COUNT, ERROR_RATE_PCT |
| scope | limits | GLOBAL, TENANT, PROJECT, AGENT |
| max_value | limits | Threshold ceiling |
| measurement_window | limits | Time window for measurement |
| current_value | derived | Current measured value |
| violation_count_30d | derived | Violations in 30 days |
| last_violation_at | derived | Most recent violation |
| status | derived | OK, NEAR_THRESHOLD, VIOLATED |
| consequence | limits | ALERT, INCIDENT, ABORT |

##### O3 — Threshold Limit Detail

**Sections:**
1. Limit Definition (name, type, scope, max value, measurement window)
2. Current Status (current value, trend, percentiles p50/p95/p99)
3. Violation History (timeline, root cause distribution, affected LLM Runs)
4. SLA Context (linked SLA, impact if violated, escalation path)

---

## Schema Foundation (Phase 1 Complete)

### Migration 087: Incidents Lifecycle Repair

**File:** `backend/alembic/versions/087_incidents_lifecycle_repair.py`

Normalizes the incidents table for domain admission:

| Column | Type | Description |
|--------|------|-------------|
| lifecycle_state | VARCHAR(16) | ACTIVE, ACKED, RESOLVED |
| llm_run_id | VARCHAR FK | Link to runs.id |
| cause_type | VARCHAR(16) | LLM_RUN, SYSTEM, HUMAN |

**Indexes Added:**
- `idx_incidents_tenant_lifecycle` (tenant_id, lifecycle_state)
- `idx_incidents_tenant_severity` (tenant_id, severity)
- `idx_incidents_llm_run` (llm_run_id)
- `idx_incidents_created_at` (created_at)

### Migration 088: Policy Control-Plane

**File:** `backend/alembic/versions/088_policy_control_plane.py`

Creates foundational tables for Policies domain:

**policy_rules Table:**
| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR PK | Rule ID |
| tenant_id | VARCHAR FK | Link to tenants.id |
| name | VARCHAR(256) | Rule name |
| enforcement_mode | VARCHAR(16) | BLOCK, WARN, AUDIT, DISABLED |
| scope | VARCHAR(16) | GLOBAL, TENANT, PROJECT, AGENT |
| status | VARCHAR(16) | ACTIVE, RETIRED |
| source | VARCHAR(16) | MANUAL, SYSTEM, LEARNED |

**policy_enforcements Table:**
| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR PK | Enforcement ID |
| rule_id | VARCHAR FK | Link to policy_rules.id |
| run_id | VARCHAR FK | Link to runs.id |
| action_taken | VARCHAR(16) | BLOCKED, WARNED, AUDITED |
| triggered_at | TIMESTAMP | When triggered |

**limits Table:**
| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR PK | Limit ID |
| tenant_id | VARCHAR FK | Link to tenants.id |
| limit_category | VARCHAR(16) | BUDGET, RATE, THRESHOLD |
| limit_type | VARCHAR(32) | COST_USD, TOKENS_*, etc. |
| max_value | NUMERIC(18,4) | Limit ceiling |
| enforcement | VARCHAR(16) | BLOCK, WARN, REJECT, etc. |

**limit_breaches Table:**
| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR PK | Breach ID |
| limit_id | VARCHAR FK | Link to limits.id |
| breach_type | VARCHAR(16) | BREACHED, EXHAUSTED, etc. |
| breached_at | TIMESTAMP | When breached |

---

## Data Grounding Verification

### Incidents Domain

| Field | Table | Status |
|-------|-------|--------|
| incident_id, severity, status | incidents | EXISTS |
| lifecycle_state | incidents | **ADDED (087)** |
| llm_run_id | incidents | **ADDED (087)** |
| cause_type | incidents | **ADDED (087)** |
| first_seen_at, last_updated_at | incidents | EXISTS |
| resolution_type, resolved_at | incidents | EXISTS |
| source_run_id | incidents | EXISTS |
| affected_llm_runs | derived (JOIN) | QUERY |
| integrity_status | integrity_evidence | EXISTS |

### Policies Domain

| Field | Table | Status |
|-------|-------|--------|
| rule_id, name, enforcement_mode | policy_rules | **ADDED (088)** |
| scope, conditions | policy_rules | **ADDED (088)** |
| created_by, source | policy_rules | **ADDED (088)** |
| proposal_id, proposal_type | policy_proposals | EXISTS |
| status, reason | policy_proposals | EXISTS |
| triggering_run_id | policy_proposals | EXISTS |
| triggering_incident_id | policy_proposals | EXISTS |
| trigger_count, last_triggered | policy_enforcements | **ADDED (088)** |

### Limits Domain

| Field | Table | Status |
|-------|-------|--------|
| limit_id, name, limit_type | limits | **ADDED (088)** |
| scope, max_value | limits | **ADDED (088)** |
| reset_period, window_seconds | limits | **ADDED (088)** |
| enforcement, consequence | limits | **ADDED (088)** |
| current_value | derived (SUM from runs) | QUERY |
| utilization_pct | derived (current/max) | QUERY |
| breach_count, throttle_count | limit_breaches | **ADDED (088)** |
| status | derived (threshold logic) | QUERY |
| integrity_status | integrity_evidence | EXISTS |

**Schema foundation complete. Tables created by migrations 087, 088.**

### Migration 089: Policy Rule Integrity + Indexes

**File:** `backend/alembic/versions/089_policy_rule_integrity_and_indexes.py`

Creates integrity infrastructure for governance rules:

**policy_rule_integrity Table:**
| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR PK | Integrity record ID |
| rule_id | VARCHAR FK UNIQUE | Link to policy_rules.id |
| integrity_status | VARCHAR(16) | VERIFIED, DEGRADED, FAILED |
| integrity_score | NUMERIC(4,3) | 0.000 - 1.000 |
| hash_root | VARCHAR(64) | Merkle root |
| details | JSONB | Integrity metadata |
| computed_at | TIMESTAMP | When computed |

**Indexes Added:**
- `idx_policy_rules_source` (tenant_id, source)
- `idx_policy_enforcements_rule_triggered` (rule_id, triggered_at)

**Trigger:** `trg_policy_rule_integrity_required` — enforces that every ACTIVE rule has integrity row.

### Migration 090: Limit Integrity + Indexes

**File:** `backend/alembic/versions/090_limit_integrity_and_indexes.py`

Creates integrity infrastructure for limits:

**limit_integrity Table:**
| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR PK | Integrity record ID |
| limit_id | VARCHAR FK UNIQUE | Link to limits.id |
| integrity_status | VARCHAR(16) | VERIFIED, DEGRADED, FAILED |
| integrity_score | NUMERIC(5,4) | 0.0000 - 1.0000 |
| computed_at | TIMESTAMP | When computed |

**Indexes Added:**
- `idx_limit_breaches_limit_breached` (limit_id, breached_at)

**Trigger:** `trg_enforce_limit_integrity` — enforces that every ACTIVE limit has integrity row.

---

## Terminology Lock (Policies Domain)

### Governance Terms

| Term | Definition |
|------|------------|
| **Rule** | An active policy definition |
| **Proposal** | A pending change to create/modify/retire a rule |
| **Enforcement Mode** | BLOCK, WARN, AUDIT, DISABLED |
| **Scope** | GLOBAL, TENANT, PROJECT, AGENT |
| **Source** | MANUAL, SYSTEM, LEARNED |

### Limits Terms

| Term | Definition |
|------|------------|
| **Budget Limit** | Cost or token allocation constraint |
| **Rate Limit** | Throughput constraint (requests/time) |
| **Threshold Limit** | Quality/performance constraint |
| **Breach** | Exceeding a budget limit |
| **Throttle** | Rate limit enforcement |
| **Violation** | Threshold limit exceeded |
| **Reset Period** | When budget resets (DAILY, WEEKLY, MONTHLY, NONE) |
| **Enforcement** | What happens on breach (BLOCK, WARN, REJECT, QUEUE, DEGRADE) |
| **Consequence** | What happens on violation (ALERT, INCIDENT, ABORT) |

---

## Implementation Progress

### v1 Freeze Status (2026-01-13)

| Component | Status | Notes |
|-----------|--------|-------|
| Migration 087 - Incidents | **APPLIED** | lifecycle_state, llm_run_id, cause_type |
| Migration 088 - Policy Control Plane | **APPLIED** | policy_rules, limits, enforcements, breaches |
| Migration 089 - Rule Integrity | **APPLIED** | policy_rule_integrity + indexes + trigger |
| Migration 090 - Limit Integrity | **APPLIED** | limit_integrity + indexes + trigger |
| INC-RT-O2 API | **IMPLEMENTED** | `GET /api/v1/runtime/incidents` |
| GOV-RT-O2 API | **IMPLEMENTED** | `GET /api/v1/runtime/policies/rules` |
| LIM-RT-O2 API | **IMPLEMENTED** | `GET /api/v1/runtime/policies/limits` |
| UX Invariants | **FROZEN** | `docs/contracts/UX_INVARIANTS_CHECKLIST.md` |
| Release Doc | **CREATED** | `docs/releases/CUSTOMER_CONSOLE_V1.md` |

### Backend Files Delivered

```
backend/app/runtime_projections/
├── __init__.py
├── router.py
├── incidents/
│   ├── __init__.py
│   └── router.py          # INC-RT-O2
└── policies/
    ├── __init__.py
    ├── governance/
    │   ├── __init__.py
    │   └── router.py      # GOV-RT-O2
    └── limits/
        ├── __init__.py
        └── router.py      # LIM-RT-O2
```

### Architectural Decisions (Locked)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Integrity tables | Option C: Separate per entity | Rules and limits do not share lifecycle semantics |
| ACKED state | Badge inside Active topic | Not a separate topic; UI badge when lifecycle_state=ACKED |
| Topic parameter | Replace `state` with `topic` | UX-driven filtering (ACTIVE includes ACTIVE + ACKED) |

### Frontend Tasks Remaining (Post-Freeze)

| Task | Priority | Notes |
|------|----------|-------|
| Column label: max_value → "Limit Value" | P1 | UI-only |
| Empty state copy consistency | P2 | Use `{entity_plural}` pattern |
| ACKED badge rendering | P1 | Show badge when lifecycle_state === "ACKED" |
| O3 Detail pages | P2 | Future sprint |
| O4/O5 Preflight-only | P3 | Future sprint |

---

## Completed Steps

1. ~~**Design Policies › Limits**~~ — COMPLETE
2. ~~**Cross-domain UX consistency review**~~ — COMPLETE (UX_INVARIANTS_CHECKLIST.md)
3. ~~**Update Activity Domain**~~ — COMPLETE (Runs → LLM Runs)
4. ~~**Implement Incidents O1**~~ — COMPLETE (Navigation panels)
5. ~~**Schema Foundation - Incidents**~~ — COMPLETE (Migration 087)
6. ~~**Schema Foundation - Policies**~~ — COMPLETE (Migration 088)
7. ~~**Apply Migrations**~~ — **COMPLETE** (087-090 applied to Neon)
8. ~~**Implement Incidents O2**~~ — **COMPLETE** (INC-RT-O2)
9. ~~**Implement Policies › Governance O1**~~ — COMPLETE (Navigation panels)
10. ~~**Implement Policies › Governance O2**~~ — **COMPLETE** (GOV-RT-O2)
11. ~~**Implement Policies › Limits O1**~~ — COMPLETE (Navigation panels)
12. ~~**Implement Policies › Limits O2**~~ — **COMPLETE** (LIM-RT-O2)
13. ~~**Integrity tables (Option C)**~~ — **COMPLETE** (Migrations 089-090)
14. ~~**v1 Freeze documentation**~~ — **COMPLETE**

---

## Invariants

### INV-DOMAIN-001: O1 Navigation Purity

> O1 panels are navigation-only. No data fetch. No counts. No loading states.

### INV-DOMAIN-002: O2 Pure Render

> O2 tables render 1:1 from API payload. No client-side aggregation.

### INV-DOMAIN-003: O4/O5 Preflight Gate

> O4 (Evidence) and O5 (Proof) endpoints return 403 outside preflight console.

### INV-DOMAIN-004: Terminology Consistency

> "LLM Runs" used everywhere. Never "Runs" alone.

### INV-DOMAIN-005: Data Grounding

> Every column must map to an existing or planned table. No UI-only fields.

---

## Post-Freeze Discovery (PIN-545, 2026-02-09)

Migration 087 introduced `llm_run_id` as the canonical FK to `runs.id`, but L5 incident engines
were **never updated** to write it. All writes and reads still use `source_run_id` (legacy field).
Post-087 incidents have `llm_run_id = NULL`.

**Resolution:** FK added on `source_run_id` via migration 123 (NOT VALID). Model updated.
Long-term plan: rewire engines to write `llm_run_id` (Option A — deferred).

See [PIN-545](PIN-545-guardrail-violations-data-001-limits-001-analysis.md) for full analysis.

---

## References

- PIN-411: Activity Domain (CLOSED)
- PIN-370: SDSR System Contract
- PIN-352: L2.1 UI Projection Pipeline
- PIN-545: Guardrail Violations DATA-001 & LIMITS-001 Analysis (post-freeze discovery)
- `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`
- `docs/contracts/UX_INVARIANTS_CHECKLIST.md` — Cross-domain UX consistency (FROZEN)
