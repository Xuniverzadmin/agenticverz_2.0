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

## 7. Gap Summary

### 7.1 Critical Gaps (HIGH Priority)

| Gap | Domain | Impact | Effort |
|-----|--------|--------|--------|
| API key targeting | Policies | Cannot scope policies to API keys | MEDIUM |
| Human actor_id targeting | Policies | Cannot scope to human users | MEDIUM |
| RAG access controls | Policies | No RAG governance | HIGH |
| Database access controls | Policies | No DB query limits | HIGH |
| Hallucination detection | Incidents | No hallucination incidents | HIGH |

### 7.2 Medium Gaps

| Gap | Domain | Impact | Effort |
|-----|--------|--------|--------|
| Kill/Terminate action | Policies | ABORT not fully wired | LOW |
| Multi-tier alerts | Policies | Only NEAR/BREACH states | MEDIUM |
| SOC2 export completeness | Logs | Control mapping incomplete | MEDIUM |

### 7.3 Low Gaps

| Gap | Domain | Impact | Effort |
|-----|--------|--------|--------|
| Executive debrief export | Logs | Not verified working | LOW |
| Terminology (threshold→control) | All | Naming inconsistency | LOW |

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
