# Domains End-to-End Scaffold v3

**Status:** DRAFT
**Date:** 2026-01-20
**Author:** Systems Architect
**Reference:** PIN-454 (Governance), PIN-413 (Logs Domain)

---

## Executive Summary

This document maps the end-to-end data flow across the four core domains when an LLM run executes:

| Domain | Question | Core Objects |
|--------|----------|--------------|
| **Activity** | What ran / is running? | Runs, Traces, Steps |
| **Policies** | How is behavior controlled? | Rules, Limits, Controls |
| **Incidents** | What went wrong? | Incidents, Violations |
| **Logs** | What is the raw truth? | LLMRunRecord, SystemRecord, AuditLedger |

**Overall Completeness:** ~75% implemented, critical gaps identified.

---

## 1. LLM Run Lifecycle

### 1.1 Run Configuration

**Entry Points:**
| Method | Location | Status |
|--------|----------|--------|
| Python SDK | `sdk/python/aos_sdk/client.py` | ✅ EXISTS |
| REST API | `POST /api/v1/runs` | ✅ EXISTS |
| Simulate | `POST /api/v1/runtime/simulate` | ✅ EXISTS |

**SDK Usage:**
```python
from aos_sdk import AOSClient

client = AOSClient(api_key="...", base_url="http://localhost:8000")
caps = client.get_capabilities()
sim = client.simulate(goal="...", agent_id="...")
run = client.post_goal(agent_id="...", goal="...")
result = client.poll_run(run["id"])
```

**Run Model:** `backend/app/db.py` (Line 283+)
- `id`, `agent_id`, `goal`, `status`
- `policy_snapshot_id`, `violation_policy_id`
- `input_tokens`, `output_tokens`, `estimated_cost_usd`
- `is_synthetic`, `synthetic_scenario_id` (SDSR traceability)

### 1.2 Run Status Lifecycle

```
queued → running → succeeded | failed | failed_policy | cancelled | retry
```

**Termination Reasons:** `backend/app/models/run_lifecycle.py`
- `POLICY_BLOCK`, `BUDGET_EXCEEDED`, `RATE_LIMITED`
- `TIMEOUT`, `SYSTEM_FAILURE`, `USER_ABORT`, `COMPLETED`

---

## 2. Policy Domain

### 2.1 Policy Control Lever (Target → Policy → Limit → Alert → Action)

**Desired Flow:**
```
1. Select Target    → Who does this policy apply to?
2. Select Policy    → What to monitor/control?
3. Select Limit     → What are the controls?
4. Near Control     → Alert configuration
5. On Control       → Action to take
6. Save & Activate  → Persist and enable
```

### 2.2 Target Selection

| Target Type | Status | Implementation |
|-------------|--------|----------------|
| All runs (by API key) | ❌ MISSING | No direct API key → policy mapping |
| By agent_id | ✅ EXISTS | `PolicyScope.AGENT` + `scope_id` |
| By human actor_id | ❌ MISSING | Not explicitly modeled |
| By tenant_id | ✅ EXISTS | Core isolation (all policies) |
| By project_id | ✅ EXISTS | `PolicyScope.PROJECT` |

**Gap:** API key and human actor targeting not supported.

**Location:** `backend/app/models/policy_control_plane.py`

### 2.3 Policy Types (What to Monitor)

| Policy Type | Status | Notes |
|-------------|--------|-------|
| Live run monitoring | ✅ EXISTS | `GET /api/v1/activity/live` |
| Token usage logging | ✅ EXISTS | `LLMRunRecord.input_tokens/output_tokens` |
| Cost burn rate | ✅ EXISTS | `estimated_cost_usd`, `cost_cents` |
| RAG access control | ❌ MISSING | No models |
| Database access control | ❌ MISSING | No models |

### 2.4 Limit Types (Controls)

| Limit Type | Status | Location |
|------------|--------|----------|
| Token limit (per-run) | ✅ EXISTS | `limit_type: TOKENS_*` |
| Token limit (per-session) | ✅ EXISTS | Temporal window support |
| Token limit (per-month) | ✅ EXISTS | `measurement_window_seconds` |
| Cost limit (per-session) | ✅ EXISTS | `limit_type: COST_USD` |
| Cost limit (daily/monthly) | ✅ EXISTS | `CostBudget` model |
| Rate limit | ✅ EXISTS | `LimitCategory.RATE` |
| RAG access (boolean) | ❌ MISSING | No model |
| DB query limit | ❌ MISSING | No model |

**Location:** `backend/app/models/policy_control_plane.py` (Line 296+)

### 2.5 Near-Control Alerting

| Capability | Status | Implementation |
|------------|--------|----------------|
| Alert enabled toggle | ✅ EXISTS | `AlertConfig.near_threshold_enabled` |
| Configurable percentage | ✅ EXISTS | `near_threshold_percentage` (default 80%) |
| Multi-tier alerts (50%, 70%, 90%) | ❌ MISSING | Only NEAR/BREACH states |

**Location:** `backend/app/models/alert_config.py`

### 2.6 On-Control Actions

| Action | Status | Implementation |
|--------|--------|----------------|
| Continue | ✅ EXISTS | Default behavior |
| Warn (log only) | ✅ EXISTS | `EnforcementMode.WARN` |
| Pause/Queue | ✅ EXISTS | `LimitEnforcement.QUEUE` |
| Block/Stop | ✅ EXISTS | `EnforcementMode.BLOCK` |
| Kill/Terminate | ⚠️ PARTIAL | `ABORT` enum exists, not fully wired |

**Location:** `backend/app/models/policy_control_plane.py` (Line 55+, 125+)

### 2.7 Policy Activation

| Capability | Status | Implementation |
|------------|--------|----------------|
| Save to library | ✅ EXISTS | `PolicyRule` persistence |
| Draft state | ✅ EXISTS | `source: LEARNED` before approval |
| Activate | ✅ EXISTS | `status: ACTIVE` |
| Deactivate | ✅ EXISTS | `status: DISABLED` |
| Retire (with reason) | ✅ EXISTS | `status: RETIRED` + `retired_reason` |

**Location:** `backend/app/api/policy.py`

---

## 3. Activity Domain

### 3.1 Real-Time Monitoring

**API Endpoints:** `backend/app/api/activity.py`

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `GET /api/v1/activity/live` | Running executions | ✅ EXISTS |
| `GET /api/v1/activity/completed` | Finished runs | ✅ EXISTS |
| `GET /api/v1/activity/signals` | Attention signals | ✅ EXISTS |
| `GET /api/v1/activity/metrics` | Aggregated metrics | ✅ EXISTS |

### 3.2 Trace Recording

**Models:** `backend/app/traces/models.py`
- `TraceRecord`: Complete execution trace
- `TraceStep`: Individual step (skill, params, status, cost, duration)
- `TraceSummary`: Summary with violation tracking

**Storage:** `backend/app/traces/pg_store.py`
- PostgreSQL-backed
- Write-once immutability (DB trigger enforced)

### 3.3 Run ↔ Trace Linking

```
runs.id ←→ aos_traces.run_id ←→ aos_trace_steps.trace_id
```

---

## 4. Incidents Domain

### 4.1 Incident Creation Flow

```
Run fails/violates policy
        ↓
IncidentEngine.create_incident_for_failed_run()
        ↓
Check policy suppression (read-before-write)
        ↓
    ┌───────────────────────────────────┐
    │ Suppressed?                       │
    │   YES → Write prevention_record   │
    │   NO  → Create incident           │
    └───────────────────────────────────┘
        ↓
Link incident_id back to traces (GAP-PROP-001)
        ↓
Maybe create PolicyProposal (HIGH/CRITICAL severity)
```

**Location:** `backend/app/services/incident_engine.py`

### 4.2 Incident Categories

| Category | Trigger | Status |
|----------|---------|--------|
| `EXECUTION_FAILURE` | Run failed | ✅ EXISTS |
| `BUDGET_EXCEEDED` | Cost limit breached | ✅ EXISTS |
| `RATE_LIMIT` | Rate limit hit | ✅ EXISTS |
| `TOKEN_LIMIT` | Token control breached | ✅ EXISTS |
| `CONTENT_POLICY` | Content violation | ✅ EXISTS |
| `PII_DETECTED` | PII in output | ✅ EXISTS |
| `SAFETY_VIOLATION` | Safety rule triggered | ✅ EXISTS |
| `EXECUTION_SUCCESS` | Success tracking (PIN-407) | ✅ EXISTS |
| `HALLUCINATION` | LLM hallucination detected | ❌ MISSING |

### 4.3 Policy Violation Detection

**Mid-Execution Checker:** `backend/app/worker/policy_checker.py`
- Interval-based checks during run execution
- Decisions: `CONTINUE | PAUSE | TERMINATE`

**Violation Service:** `backend/app/services/policy_violation_service.py`
- `ViolationFact`: Persisted violation record
- One incident per (run_id, policy_id) constraint

---

## 5. Logs Domain

### 5.1 Log Types

| Log Type | Model | Purpose | Status |
|----------|-------|---------|--------|
| LLM Run Logs | `LLMRunRecord` | Execution data, tokens, cost | ✅ EXISTS |
| System Logs | `SystemRecord` | Infra events (startup, deploy) | ✅ EXISTS |
| Audit Ledger | `AuditLedger` | Who did what, when | ✅ EXISTS |

**Location:** `backend/app/models/logs_records.py`

### 5.2 LLM Run Record

```python
LLMRunRecord:
    id, tenant_id, run_id, trace_id
    provider, model
    prompt_hash, response_hash  # Verification
    input_tokens, output_tokens, cost_cents
    execution_status, source
    is_synthetic, synthetic_scenario_id
    # WRITE-ONCE (immutable, DB trigger enforced)
```

### 5.3 System Record

```python
SystemRecord:
    id, tenant_id
    component   # API, WORKER, SCHEDULER, etc.
    event_type  # STARTUP, SHUTDOWN, DEPLOYMENT, MIGRATION
    severity    # INFO, WARN, CRITICAL
    summary, details
    caused_by   # SYSTEM, HUMAN, AUTOMATION
    correlation_id
```

### 5.4 Audit Ledger

**Service:** `backend/app/services/logs/audit_ledger_service.py`

Tracks:
- Who created the policy (`actor_id`, `actor_type`)
- For which API key / agent / tenant
- Applied to which run_id
- Before/after state for changes

**Event Types:**
- `INCIDENT_*`: Created, acknowledged, resolved
- `POLICY_*`: Created, updated, activated, retired
- `LIMIT_*`: Created, breached, adjusted
- `SIGNAL_*`: Acknowledged, suppressed

### 5.5 Export Capabilities

| Export Type | Status | Location |
|-------------|--------|----------|
| PDF export | ✅ EXISTS | `pdf_renderer.py` |
| Evidence bundle | ✅ EXISTS | `export_bundles.py` |
| SOC2 bundle | ⚠️ PARTIAL | Declared, mapping incomplete |
| Executive debrief | ⚠️ PARTIAL | Declared, not verified |

---

## 6. Cross-Domain Linking

### 6.1 Entity Relationship

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    runs     │────▶│ aos_traces  │────▶│  incidents  │
│             │     │             │     │             │
│  run_id     │     │  run_id     │     │source_run_id│
│  agent_id   │     │  trace_id   │     │ incident_id │
│  tenant_id  │     │ incident_id │     │  policy_id  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────┐
│                   LLMRunRecord                      │
│         (immutable execution log entry)             │
└─────────────────────────────────────────────────────┘
```

### 6.2 Deep Linking

| From | To | Link Field | Status |
|------|----|-----------:|--------|
| Run → Trace | `aos_traces.run_id` | ✅ EXISTS |
| Trace → Incident | `aos_traces.incident_id` | ✅ EXISTS (GAP-PROP-001 fix) |
| Incident → Run | `incidents.source_run_id` | ✅ EXISTS |
| Incident → Policy | `incidents.violation_policy_id` | ✅ EXISTS |
| Run → Log | `LLMRunRecord.run_id` | ✅ EXISTS |

---

## 7. Gap Ledger (Numbered)

### Reference Design Comparison

The following gaps were identified by comparing the current system against a reference control lever design:

```
Reference Design Structure:
Policy
 └── Scope Selector        ← WHO / WHAT it applies to
 └── Monitors              ← WHAT is observed during run
 └── Limits                ← HARD quantitative constraints
 └── Control Actions       ← WHAT happens near / at breach
 └── Activation State      ← WHEN it is enforced
```

---

### 7.1 Scope Selector Gaps

| ID | Gap | Current State | Required State | Priority |
|----|-----|---------------|----------------|----------|
| GAP-001 | API key targeting | Not supported | `scope_type: API_KEY` with `api_key_ids[]` | HIGH |
| GAP-002 | Human actor targeting | Not supported | `scope_type: HUMAN_ACTOR` with `human_actor_ids[]` | HIGH |
| GAP-003 | ALL_RUNS scope | Implicit via GLOBAL | Explicit `scope_type: ALL_RUNS` for clarity | LOW |
| GAP-004 | Scope resolution snapshot | No snapshot on run | Store resolved scope on run at start | MEDIUM |

**Current PolicyScope enum:** `GLOBAL | TENANT | PROJECT | AGENT`
**Required PolicyScope enum:** `ALL_RUNS | TENANT | PROJECT | AGENT | API_KEY | HUMAN_ACTOR`

---

### 7.2 Monitor Gaps

| ID | Gap | Current State | Required State | Priority |
|----|-----|---------------|----------------|----------|
| GAP-005 | Explicit monitor config | Implicit via limit types | Explicit `MonitorConfig` object | MEDIUM |
| GAP-006 | RAG access monitoring | Not supported | `monitor_rag_access: { enabled, allowed_sources[] }` | HIGH |
| GAP-007 | Burn rate monitoring | Not supported | `monitor_burn_rate: true` | MEDIUM |
| GAP-008 | Monitor → Limit binding | Implicit | Explicit: "If not monitored, cannot trigger limit" | MEDIUM |

**Principle:** If something is not monitored, it cannot trigger a limit or action.

---

### 7.3 Limit Gaps

| ID | Gap | Current State | Required State | Priority |
|----|-----|---------------|----------------|----------|
| GAP-009 | RAG access boolean | Not supported | `rag_access: { allowed: boolean }` | HIGH |
| GAP-010 | DB query limit | Not supported | `db_query_limit: { max_queries, window_seconds }` | HIGH |
| GAP-011 | PER_SESSION vs TEMPORAL clarity | Unclear distinction | Explicit `limit_window: PER_SESSION | TEMPORAL` | MEDIUM |
| GAP-012 | Limit separation principle | Limits can have actions | Limits emit NEAR/BREACH only, actions separate | LOW |

**Principle:** Limits do not decide outcomes. They only emit `NEAR` or `BREACH`.

---

### 7.4 Control Action Gaps

| ID | Gap | Current State | Required State | Priority |
|----|-----|---------------|----------------|----------|
| GAP-013 | PAUSE action (resumable) | Not supported | `action: PAUSE` - suspend, can resume | HIGH |
| GAP-014 | STOP vs KILL semantics | Unclear (ABORT exists) | `STOP` = graceful, `KILL` = immediate | MEDIUM |
| GAP-015 | requires_ack flag | Not supported | `requires_ack: boolean` for enforcement | LOW |
| GAP-016 | Same-step enforcement | Not guaranteed | "STOP/KILL must halt within same step" | HIGH |

**Current actions:** `BLOCK | WARN | REJECT | QUEUE | DEGRADE | ALERT | ABORT`
**Required actions:** `CONTINUE | WARN | PAUSE | STOP | KILL`

---

### 7.5 Alerting Gaps

| ID | Gap | Current State | Required State | Priority |
|----|-----|---------------|----------------|----------|
| GAP-017 | Notify channels | Not configurable | `notify: [UI, WEBHOOK, EMAIL]` | MEDIUM |
| GAP-018 | Multi-tier alerts | Only NEAR/BREACH | Support 50%, 70%, 80%, 90% tiers | LOW |
| GAP-019 | Alert → Log linking | Implicit | Explicit: near-control events in LLM Runs log | MEDIUM |

---

### 7.6 Policy Lifecycle Gaps

| ID | Gap | Current State | Required State | Priority |
|----|-----|---------------|----------------|----------|
| GAP-020 | DRAFT state | Not supported | `status: DRAFT` before activation | MEDIUM |
| GAP-021 | SUSPENDED state | Not supported | `status: SUSPENDED` (temporary disable) | LOW |
| GAP-022 | threshold_snapshot_hash | Not stored | Hash of threshold config for audit | MEDIUM |

**Current lifecycle:** `ACTIVE | RETIRED | DISABLED`
**Required lifecycle:** `DRAFT → ACTIVE → SUSPENDED → RETIRED`

---

### 7.7 Incident Gaps

| ID | Gap | Current State | Required State | Priority |
|----|-----|---------------|----------------|----------|
| GAP-023 | Hallucination detection | Not supported | Incident category `HALLUCINATION` | HIGH |
| GAP-024 | Inflection point metadata | Partial | Full inflection capture in incident | MEDIUM |

---

### 7.8 Logs & Export Gaps

| ID | Gap | Current State | Required State | Priority |
|----|-----|---------------|----------------|----------|
| GAP-025 | SOC2 control mapping | Partial | Complete SOC2 control objective mapping | MEDIUM |
| GAP-026 | Executive debrief export | Declared | Verified working | LOW |
| GAP-027 | Evidence PDF completeness | Exists | Verify all fields included | LOW |

---

### 7.9 Runtime Integration Gaps

| ID | Gap | Current State | Required State | Priority |
|----|-----|---------------|----------------|----------|
| GAP-028 | Scope resolution at run start | Implicit | Explicit scope resolution, snapshot stored | MEDIUM |
| GAP-029 | Policy snapshot immutability | Exists | Verify snapshot cannot be modified | LOW |
| GAP-030 | Step-level enforcement guarantee | Not verified | Enforcement within same step guaranteed | HIGH |

---

### Gap Summary by Priority

| Priority | Count | Gap IDs |
|----------|-------|---------|
| **HIGH** | 10 | GAP-001, GAP-002, GAP-006, GAP-009, GAP-010, GAP-013, GAP-016, GAP-023, GAP-030 |
| **MEDIUM** | 13 | GAP-004, GAP-005, GAP-007, GAP-008, GAP-011, GAP-014, GAP-017, GAP-019, GAP-020, GAP-022, GAP-024, GAP-025, GAP-028 |
| **LOW** | 7 | GAP-003, GAP-012, GAP-015, GAP-018, GAP-021, GAP-026, GAP-027, GAP-029 |

**Total Gaps:** 30

---

## 8. Implementation Roadmap (Proposed)

### Phase 1: Policy Targeting (Week 1-2)
- [ ] Add `api_key_id` to `PolicyScope`
- [ ] Add `actor_id` to `PolicyScope`
- [ ] Update policy evaluation to check new scopes

### Phase 2: RAG/DB Controls (Week 3-4)
- [ ] Define `RAG_ACCESS` limit type
- [ ] Define `DB_QUERY_LIMIT` limit type
- [ ] Wire limits evaluator for new types

### Phase 3: Incident Enhancements (Week 5)
- [ ] Add hallucination detection model
- [ ] Wire hallucination → incident creation

### Phase 4: Export Completeness (Week 6)
- [ ] Complete SOC2 control objective mapping
- [ ] Verify executive debrief export

---

## 9. Key Files Reference

| Purpose | File | Layer |
|---------|------|-------|
| Run model | `backend/app/db.py` | L6 |
| Run lifecycle | `backend/app/models/run_lifecycle.py` | L6 |
| Policy models | `backend/app/models/policy_control_plane.py` | L6 |
| Policy API | `backend/app/api/policy.py` | L2 |
| Limits evaluator | `backend/app/runtime/limits/evaluator.py` | L4 |
| Activity API | `backend/app/api/activity.py` | L2 |
| Trace storage | `backend/app/traces/pg_store.py` | L6 |
| Incident engine | `backend/app/services/incident_engine.py` | L4 |
| Log models | `backend/app/models/logs_records.py` | L6 |
| Audit ledger | `backend/app/services/logs/audit_ledger_service.py` | L4 |
| SDK client | `sdk/python/aos_sdk/client.py` | SDK |

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-01-20 | Systems Architect | Initial draft — Gap analysis from policy control lever review |
| 2026-01-20 | Systems Architect | Added numbered Gap Ledger (GAP-001 to GAP-030) after reference design comparison |
