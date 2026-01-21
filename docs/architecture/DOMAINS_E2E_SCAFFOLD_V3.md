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

**Overall Completeness:** ~60% implemented, 69 gaps identified (2 CRITICAL, 33 HIGH, 25 MEDIUM, 9 LOW).

**Revision:** v3.1 — Added GAP-069 (Runtime Kill Switch), GAP-070 (Degraded Mode), INV-005 (Conflict Determinism) per GPT review.

---

## 0. Design Invariants (Non-Negotiable Rules)

**Purpose:** These invariants constrain HOW gaps are implemented. They are not gaps themselves — they are rules that govern implementation.

### INV-001: SPINE vs EVENT Separation

> **SPINE operations are deterministic and synchronous. EVENT operations are reactive and asynchronous. Never let EVENT leak into SPINE.**

| Path | Characteristics | Example |
|------|-----------------|---------|
| **SPINE** | Deterministic, blocking, enforcement | Policy check before skill execution |
| **EVENT** | Reactive, non-blocking, observability | Alert emission on threshold crossing |
| **STARTUP** | Initialization, invariant validation | EventReactor creation at boot |

### INV-002: Hallucination Detection is Non-Blocking (HALLU-INV-001)

> **Hallucination incidents are ALWAYS non-blocking unless explicitly configured by customer.**

**Rationale:**
- Hallucination detection is **probabilistic** (ML-based confidence scores)
- Policy violations (cost, rate, PII) are **deterministic** (facts)
- False positives on hallucination blocking destroy customer trust
- Blocking requires opt-in, not opt-out

| Detection Type | Certainty | Default Behavior |
|----------------|-----------|------------------|
| Cost exceeded | 100% (fact) | BLOCKING |
| Rate limit hit | 100% (fact) | BLOCKING |
| PII regex match | 100% (fact) | BLOCKING |
| Hallucination detected | 60-90% (guess) | NON-BLOCKING (observability only) |

**Implementation Rule:** GAP-023 (Hallucination detection) MUST respect this invariant.

### INV-003: Tenant Isolation at Connector Level (CONN-INV-001)

> **All connector services MUST enforce tenant isolation at execution time. Cross-tenant data access MUST fail hard.**

**Applies to:** GAP-059 through GAP-064 (all connector services)

| Requirement | Enforcement Point |
|-------------|-------------------|
| Connector credentials scoped to tenant | Credential lookup |
| `tenant_id` validated on every request | Service entry point |
| Cross-tenant access attempt | Hard failure, audit log |
| Connection pool isolation | Per-tenant or validated |

### INV-004: Boot-Fail Policy

> **If any SPINE invariant fails at startup, the system MUST refuse to accept new runs.**

**Covered by:** GAP-067 (Boot-Fail Policy)

| Failure Type | Required Behavior |
|--------------|-------------------|
| EventReactor fails to initialize | Block run acceptance |
| RAC fails durability check | Block run acceptance |
| Policy snapshot DB trigger missing | Block run acceptance |
| Governance profile invalid | Block run acceptance |

### INV-005: Policy Conflict Determinism (CONFLICT-DET-001)

> **When multiple policies apply to the same action, the most restrictive action wins. If two policies have equal restrictiveness, the policy with the lowest policy_id wins (deterministic tiebreaker).**

**Covered by:** GAP-068 (Policy Conflict Resolution)

| Rule | Description |
|------|-------------|
| Restrictiveness order | STOP > PAUSE > WARN > ALLOW |
| Tiebreaker | Lowest `policy_id` wins |
| Order-independence | Evaluation order MUST NOT affect outcome |
| Determinism | Same inputs → same winner, always |

**Implementation Rule:** GAP-068 MUST enforce this invariant. Order-dependent behavior is a governance violation.

---

## 0.1 Gap Tiering System

**Purpose:** Not all gaps are equal. Tiering prevents execution stall by clarifying dependencies.

| Tier | Purpose | Ship Condition |
|------|---------|----------------|
| **T0** | Enforcement works at runtime | MUST complete before ANY customer |
| **T1** | System can explain and prove decisions | MUST complete before SOC2 audit |
| **T2** | System can operate at scale | Complete before growth phase |
| **T3** | Product completeness | Ongoing improvement |

### Tier Definitions

**T0 — Enforcement Foundation (CRITICAL)**
> If these aren't done, nothing else matters. Exports, alerts, and incidents are theatre without enforcement.

**T1 — Explainability & Proof**
> System can prove what happened and why. Required for compliance and customer trust.

**T2 — Scale & Operations**
> System can handle alert storms, stale runs, and operational complexity.

**T3 — Product Polish**
> UI refinements, multi-tier alerts, executive summaries.

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

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-001 | API key targeting | Not supported | `scope_type: API_KEY` with `api_key_ids[]` | HIGH | T3 |
| GAP-002 | Human actor targeting | Not supported | `scope_type: HUMAN_ACTOR` with `human_actor_ids[]` | HIGH | T3 |
| GAP-003 | ALL_RUNS scope | Implicit via GLOBAL | Explicit `scope_type: ALL_RUNS` for clarity | LOW | T3 |
| GAP-004 | Scope resolution snapshot | No snapshot on run | Store resolved scope on run at start | MEDIUM | T3 |

**Current PolicyScope enum:** `GLOBAL | TENANT | PROJECT | AGENT`
**Required PolicyScope enum:** `ALL_RUNS | TENANT | PROJECT | AGENT | API_KEY | HUMAN_ACTOR`

---

### 7.2 Monitor Gaps

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-005 | Explicit monitor config | Implicit via limit types | Explicit `MonitorConfig` object | MEDIUM | T3 |
| GAP-006 | RAG access monitoring | Not supported | `monitor_rag_access: { enabled, allowed_sources[] }` | HIGH | T3 |
| GAP-007 | Burn rate monitoring | Not supported | `monitor_burn_rate: true` | MEDIUM | T3 |
| GAP-008 | Monitor → Limit binding | Implicit | Explicit: "If not monitored, cannot trigger limit" | MEDIUM | T3 |

**Principle:** If something is not monitored, it cannot trigger a limit or action.

---

### 7.3 Limit Gaps

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-009 | RAG access boolean | Not supported | `rag_access: { allowed: boolean }` | HIGH | T3 |
| GAP-010 | DB query limit | Not supported | `db_query_limit: { max_queries, window_seconds }` | HIGH | T3 |
| GAP-011 | PER_SESSION vs TEMPORAL clarity | Unclear distinction | Explicit `limit_window: PER_SESSION | TEMPORAL` | MEDIUM | T3 |
| GAP-012 | Limit separation principle | Limits can have actions | Limits emit NEAR/BREACH only, actions separate | LOW | T3 |

**Principle:** Limits do not decide outcomes. They only emit `NEAR` or `BREACH`.

---

### 7.4 Control Action Gaps

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-013 | PAUSE action (resumable) | Not supported | `action: PAUSE` - suspend, can resume | HIGH | T3 |
| GAP-014 | STOP vs KILL semantics | Unclear (ABORT exists) | `STOP` = graceful, `KILL` = immediate | MEDIUM | T3 |
| GAP-015 | requires_ack flag | Not supported | `requires_ack: boolean` for enforcement | LOW | T3 |
| GAP-016 | Same-step enforcement | Not guaranteed | "STOP/KILL must halt within same step" | HIGH | **T0** |

**Current actions:** `BLOCK | WARN | REJECT | QUEUE | DEGRADE | ALERT | ABORT`
**Required actions:** `CONTINUE | WARN | PAUSE | STOP | KILL`

---

### 7.5 Alerting Gaps

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-017 | Notify channels | Not configurable | `notify: [UI, WEBHOOK, EMAIL]` | MEDIUM | T2 |
| GAP-018 | Multi-tier alerts | Only NEAR/BREACH | Support 50%, 70%, 80%, 90% tiers | LOW | T3 |
| GAP-019 | Alert → Log linking | Implicit | Explicit: near-control events in LLM Runs log | MEDIUM | T2 |

---

### 7.6 Policy Lifecycle Gaps

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-020 | DRAFT state | Not supported | `status: DRAFT` before activation | MEDIUM | T3 |
| GAP-021 | SUSPENDED state | Not supported | `status: SUSPENDED` (temporary disable) | LOW | T3 |
| GAP-022 | threshold_snapshot_hash | Not stored | Hash of threshold config for audit | MEDIUM | T1 |

**Current lifecycle:** `ACTIVE | RETIRED | DISABLED`
**Required lifecycle:** `DRAFT → ACTIVE → SUSPENDED → RETIRED`

---

### 7.7 Incident Gaps

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-023 | Hallucination detection | Not supported | Incident category `HALLUCINATION` | HIGH | T1 |
| GAP-024 | Inflection point metadata | Partial | Full inflection capture in incident | MEDIUM | T1 |

**⚠️ GAP-023 Implementation Constraint (INV-002):**
> Hallucination detection MUST be non-blocking by default. See **INV-002: HALLU-INV-001**.
> - Creates incident with `blocking=False`
> - Feeds OBSERVABILITY path, not SPINE
> - Customer opt-in required for blocking behavior

---

### 7.8 Logs & Export Gaps

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-025 | SOC2 control mapping | Partial | Complete SOC2 control objective mapping | MEDIUM | T1 |
| GAP-026 | Executive debrief export | Declared | Verified working | LOW | T3 |
| GAP-027 | Evidence PDF completeness | Exists | Verify all fields included | LOW | T1 |

---

### 7.9 Runtime Integration Gaps

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-028 | Scope resolution at run start | Implicit | Explicit scope resolution, snapshot stored | MEDIUM | T3 |
| GAP-029 | Policy snapshot immutability | Exists | Verify snapshot cannot be modified | LOW | T1 |
| GAP-030 | Step-level enforcement guarantee | Not verified | Enforcement within same step guaranteed | HIGH | **T0** |

---

### 7.10 Policy Framing Gaps (GPT Reference Design Analysis)

These gaps were identified by analyzing the system against 6 framing elements from a GPT reference design.

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-031 | Binding Moment Enforcement | `bind_at` field exists in `PolicyPrecedence` but not consulted | Prevention engine must respect `bind_at: RUN_START \| FIRST_TOKEN \| EACH_STEP` | HIGH | **T0** |
| GAP-032 | Snapshot DB-Level Immutability | Software immutability only (verify_integrity) | Add DB trigger to REJECT UPDATE on `policy_snapshots` table | MEDIUM | T1 |
| GAP-033 | Inspection Constraint Enforcement | `MonitorConfig` has `allow_prompt_logging`, `allow_pii_capture` etc. but not enforced | Runner/prevention engine must check inspection constraints before logging | HIGH | T1 |
| GAP-034 | Override Authority Integration | `OverrideAuthority` model complete but not wired | Prevention engine must check `is_override_active()` before enforcing policy | HIGH | T1 |
| GAP-035 | Failure Mode Enforcement | `failure_mode` field stored per-policy but ignored | Prevention engine must respect `fail_closed \| fail_open` per-policy instead of hardcoded fail-open | HIGH | **T0** |

**Analysis Details:**

- **GAP-031:** The `BindingMoment` enum (`RUN_START`, `FIRST_TOKEN`, `EACH_STEP`) exists in `policy_precedence.py:43-49` but `prevention_engine.py` evaluates at every step regardless of setting.

- **GAP-032:** `PolicySnapshot.verify_integrity()` exists and is called at line 198, but no database trigger prevents UPDATE mutations.

- **GAP-033:** `MonitorConfig` (lines 80-85) declares `allow_prompt_logging`, `allow_response_logging`, `allow_pii_capture`, `allow_secret_access` but these are not checked during execution.

- **GAP-034:** `OverrideAuthority` in `override_authority.py` has complete role-based override logic (`can_override()`, `is_override_active()`) but no integration with policy enforcement.

- **GAP-035:** `PolicyPrecedence.failure_mode` defaults to `fail_closed` but `prevention_engine.py:237-239` hardcodes fail-open: "If no snapshot loaded, allow (graceful degradation)".

---

### 7.11 Knowledge Domain Gaps (GPT Reference Design Analysis)

These gaps were identified by analyzing the system against a GPT Knowledge Onboarding reference design.

**Key Finding:** The system has LLM provider integrations (`CusIntegration` for OpenAI/Anthropic) but **no knowledge base integrations**. The `allowed_rag_sources` field in `MonitorConfig` suggests intent, but no backing system exists.

| ID | Gap | Current State | Required State | Priority | Tier |
|----|-----|---------------|----------------|----------|------|
| GAP-036 | Knowledge Asset Model | Not implemented | `KnowledgeAsset` model: asset_type (S3/SQL/VECTOR_DB/WEB), visibility, auth_ref, status | HIGH | T3 |
| GAP-037 | Knowledge Plane Model | Not implemented | `KnowledgePlane` model: policy-aware abstraction with sensitivity, allowed_use, default_policy | HIGH | T3 |
| GAP-038 | Knowledge Onboarding Lifecycle | No pipeline exists | REGISTER → VERIFY → INGEST → INDEX → CLASSIFY → ACTIVATE → GOVERN | HIGH | T3 |
| GAP-039 | Asset Verification Gate | No ownership/access verification | Validate credentials, test read-only access, enforce least privilege before ingestion | HIGH | T3 |
| GAP-040 | Ingestion & Indexing Pipeline | Only internal vector memory exists | Chunking, PII detection, content hashing, external source indexing | HIGH | T3 |
| GAP-041 | Plane Activation Gate | No activation concept | Owner confirmation, default=DENY, audit log on activation | MEDIUM | T3 |
| GAP-042 | Policy → Plane Binding | `allowed_rag_sources` is unbacked string list | Policies reference `KnowledgePlane.plane_id`, runtime validates at retrieval | HIGH | T3 |
| GAP-043 | Knowledge Plane Selection UI | No UI for knowledge management | Asset onboarding wizard, plane management, ingestion job status | MEDIUM | T3 |
| GAP-044 | Public vs Private Knowledge Defaults | No distinction | Public=allow by default, Private=deny by default | MEDIUM | T3 |
| GAP-045 | Multi-Asset Single-Plane Aggregation | Not supported | Single plane can aggregate multiple assets for policy continuity | LOW | T3 |

**Analysis Details:**

- **GAP-036/037:** `CusIntegration` exists for LLM providers but no equivalent for knowledge sources. Policies reference `allowed_rag_sources` (strings) with no backing model.

- **GAP-038:** No onboarding pipeline. Compare to `CusIntegration` which has `created → enabled ↔ disabled → error` lifecycle.

- **GAP-039:** `cus_credential_service.py` handles LLM credentials but no verification for knowledge source access.

- **GAP-040:** `memory/vector_store.py` is for internal agent memory (pgvector), not for customer knowledge onboarding.

- **GAP-042:** `MonitorConfig.allowed_rag_sources` at line 72 is a JSON string list. No `KnowledgePlane` model validates these IDs.

---

---

### 7.12 Governance Spine Wiring Gaps (Orphan Analysis)

These gaps were identified by tracing the execution flow and finding components that are implemented but never initialized or called.

| ID | Gap | Purpose | Current State | Required State | Priority | Tier |
|----|-----|---------|---------------|----------------|----------|------|
| GAP-046 | EventReactor Not Initialized | Central event bus for governance events (heartbeats, audit events, alerts) | Full implementation in `events/subscribers.py` with heartbeat monitoring, but `get_event_reactor()` never called in `main.py` | Add to startup: `reactor = get_event_reactor(); register_audit_handlers(reactor); reactor.start()` | **CRITICAL** | T0 |
| GAP-047 | Audit Handlers Not Registered | React to audit events (failures, reconciliation issues, liveness violations) | `register_audit_handlers()` exported from `events/__init__.py` but never called anywhere | Call `register_audit_handlers(reactor)` after EventReactor creation | **HIGH** | T2 |
| GAP-048 | Heartbeat Monitoring Dormant | Periodic health checks to detect stale/crashed runs via `_heartbeat_loop()` | Full implementation in `events/subscribers.py:398-444` but thread never started | Depends on GAP-046 fix; heartbeat starts automatically when reactor.start() called | **HIGH** | T2 |
| GAP-049 | AlertFatigueController Orphaned | Deduplicate alerts to prevent alert flooding during incident storms | `get_alert_fatigue_controller()` at `services/alert_fatigue.py:508` only referenced in docstring example | Wire to incident creation and alert emission paths | **MEDIUM** | T2 |
| GAP-050 | RAC Durability Enforcement Flag Unused | Enforce that audit contracts are persisted durably before acknowledgment | `rac_durability_enforce` flag defined in `GovernanceConfig` but no code checks or enforces it | Add durability checks in RAC operations that verify persistence before ack | **MEDIUM** | T1 |
| GAP-051 | Phase-Status Invariant Enforcement Flag Unused | Block invalid phase-status combinations (e.g., EXECUTING+COMPLETED) | `phase_status_invariant_enforce` flag defined but `PhaseStatusInvariantError` never raised in enforcement | Add enforcement checks in ROK phase transitions when flag is true | **MEDIUM** | T1 |
| GAP-052 | Jobs Module No Scheduler Wired | Scheduled background tasks (cleanup, maintenance, stale run detection) | `app/jobs/__init__.py` explicitly states "NOT currently scheduled" and "No scheduler is wired" | Add APScheduler or Celery Beat; wire job definitions to scheduler | **LOW** | T2 |
| GAP-054 | MidExecutionPolicyChecker Requires EventReactor | Check policies during execution (not just at run start) to catch policy changes | `MID_EXECUTION_POLICY_CHECK_ENABLED` flag exists but MidExecutionPolicyChecker depends on EventReactor for triggering | Depends on GAP-046; once EventReactor runs, mid-execution checks can subscribe to events | **HIGH** | T2 |
| GAP-067 | Boot-Fail Policy Missing | If SPINE invariants fail at startup, system should refuse new runs | No guard exists. If EventReactor/RAC/governance profile fails to initialize, system still accepts runs | Add startup guard: check all SPINE components initialized, block `/runs` endpoint if not | **HIGH** | T0 |
| GAP-068 | Policy Conflict Resolution Undefined | When multiple policies trigger different actions (STOP vs PAUSE), resolution order unclear | `PolicyPrecedence` has ordering but no explicit conflict resolution rule. Implicit "first wins" | Define explicit resolution: precedence order → action severity → fail-closed. **Must implement INV-005.** | **HIGH** | T0 |
| GAP-069 | Runtime Governance Kill Switch Missing | No way to disable governance mid-flight without restart. If failure occurs during operation, no panic lever. | Only boot-fail policy (startup guard) exists | Add runtime toggle: `is_governance_active()` flag with OPS endpoint, critical audit logging | **HIGH** | T0 |
| GAP-070 | Governance Degraded Mode Missing | Only full-stop or silent failure modes exist. Need middle state for incident response. | Binary options only: governance active (full enforcement) or governance disabled (no enforcement) | Add DEGRADED mode: block new runs, complete existing with WARN, full audit emitted | **MEDIUM** | T1 |

**Wiring Analysis:**

| Component | File | Wired? | Called From | Gap |
|-----------|------|--------|-------------|-----|
| ROK | `worker/orchestration/run_orchestration_kernel.py` | ✅ YES | `pool.py:216-241` | - |
| RAC (AuditReconciler) | `services/audit/reconciler.py` | ✅ YES | ROK governance check | - |
| Transaction Coordinator | `services/governance/transaction_coordinator.py` | ✅ YES | `runner.py:424` | - |
| Run Governance Facade | `services/governance/run_governance_facade.py` | ✅ YES | `runner.py:492,640,676` | - |
| EventReactor | `events/subscribers.py` | ❌ **ORPHAN** | Never initialized | GAP-046 |
| Audit Handlers | `events/audit_handlers.py` | ❌ **ORPHAN** | `register_audit_handlers()` never called | GAP-047 |
| Heartbeat Monitoring | `events/subscribers.py:367-532` | ❌ **DORMANT** | Thread never started | GAP-048 |
| AlertFatigueController | `services/alert_fatigue.py` | ❌ **ORPHAN** | Only in docstring example | GAP-049 |
| RAC Durability Enforce | `services/governance/profile.py:119` | ⚠️ **FLAG ONLY** | Flag stored, never checked | GAP-050 |
| Phase-Status Invariant Enforce | `services/governance/profile.py:120` | ⚠️ **FLAG ONLY** | Flag stored, never checked | GAP-051 |
| Jobs Scheduler | `app/jobs/` | ❌ **ORPHAN** | "No scheduler is wired" | GAP-052 |
| MidExecutionPolicyChecker | `worker/policy_checker.py:542` | ⚠️ **CONDITIONAL** | Requires EventReactor | GAP-054 |

**Cascade Analysis (GAP-046 Impact):**

```
GAP-046: EventReactor Not Initialized
    └─▶ GAP-047: Audit Handlers Never Fire
    └─▶ GAP-048: Heartbeat Monitoring Never Runs
    └─▶ GAP-054: MidExecutionPolicyChecker Cannot Subscribe to Events
```

**Impact Summary:**
- Heartbeat monitoring never runs → stale run detection disabled
- Audit event handlers never fire → no alerts on audit failures
- Mid-execution policy checks via events disabled → policy changes during run not caught
- `EVENT_REACTOR_ENABLED` flag is checked but reactor never created
- Alert deduplication disabled → potential alert storms during incidents

---

### Gap Summary by Priority (Updated)

| Priority | Count | Gap IDs |
|----------|-------|---------|
| **CRITICAL** | 2 | GAP-046, GAP-065 |
| **HIGH** | 33 | GAP-001, GAP-002, GAP-006, GAP-009, GAP-010, GAP-013, GAP-016, GAP-023, GAP-030, GAP-031, GAP-033, GAP-034, GAP-035, GAP-036, GAP-037, GAP-038, GAP-039, GAP-040, GAP-042, GAP-047, GAP-048, GAP-054, GAP-055, GAP-056, GAP-057, GAP-058, GAP-060, GAP-063, GAP-066, GAP-067, GAP-068, **GAP-069** |
| **MEDIUM** | 25 | GAP-004, GAP-005, GAP-007, GAP-008, GAP-011, GAP-014, GAP-017, GAP-019, GAP-020, GAP-022, GAP-024, GAP-025, GAP-028, GAP-032, GAP-041, GAP-043, GAP-044, GAP-049, GAP-050, GAP-051, GAP-059, GAP-061, GAP-062, GAP-064, **GAP-070** |
| **LOW** | 9 | GAP-003, GAP-012, GAP-015, GAP-018, GAP-021, GAP-026, GAP-027, GAP-029, GAP-045, GAP-052 |

**Total Gaps:** 69

### Gap Summary by Tier (Execution Order)

| Tier | Purpose | Count | Gap IDs |
|------|---------|-------|---------|
| **T0** | Enforcement Foundation | 13 | GAP-016, GAP-030, GAP-031, GAP-035, GAP-046, GAP-065, GAP-066, GAP-067, GAP-068, **GAP-069**, GAP-059, GAP-060, GAP-063 |
| **T1** | Explainability & Proof | 11 | GAP-022, GAP-023, GAP-024, GAP-025, GAP-027, GAP-033, GAP-034, GAP-050, GAP-051, GAP-058, **GAP-070** |
| **T2** | Scale & Operations | 14 | GAP-017, GAP-019, GAP-047, GAP-048, GAP-049, GAP-052, GAP-054, GAP-055, GAP-056, GAP-057, GAP-061, GAP-062, GAP-064, GAP-029 |
| **T3** | Product Polish | 31 | All remaining gaps (UI, lifecycle, scope enhancements, knowledge domain features) |

**Tier Distribution:** T0=13 (19%), T1=11 (16%), T2=14 (20%), T3=31 (45%)

**Note:** GAP-053 intentionally skipped (EmailVerificationService is dead code for pre-Clerk OTP flow, not a gap - Clerk handles email verification natively).

---

### 7.13 Gap Audit Summary (Implementation Review Guide)

**Date:** 2026-01-20
**Purpose:** Pre-implementation review notes to avoid confusion during gap resolution.

#### Section 7.10: Policy Framing Gaps (GAP-031 to GAP-035)

| Gap | Type | Verdict | Implementation Note |
|-----|------|---------|---------------------|
| GAP-031 | Field exists, ignored | ✅ VALID | `bind_at` field in model, prevention_engine ignores it |
| GAP-032 | Defense-in-depth | ✅ VALID | Software check exists, DB trigger adds protection |
| GAP-033 | Privacy/compliance | ✅ VALID | `MonitorConfig` flags exist, runtime ignores them |
| GAP-034 | Model not wired | ✅ VALID | `OverrideAuthority` complete with methods, not integrated |
| GAP-035 | Field exists, ignored | ✅ VALID | `failure_mode` stored, hardcoded fail-open in engine |

**Section 7.10 Status:** All 5 gaps identify fields/models that exist but are not respected by execution engine. Fix by wiring existing code, not building new.

---

#### Section 7.11: Knowledge Domain Gaps (GAP-036 to GAP-045)

| Gap | Type | Verdict | Implementation Note |
|-----|------|---------|---------------------|
| GAP-036 | Future feature | ⚠️ NOT BROKEN CODE | No `KnowledgeAsset` model - needs to be built |
| GAP-037 | Future feature | ⚠️ NOT BROKEN CODE | No `KnowledgePlane` model - needs to be built |
| GAP-038 | Future feature | ⚠️ NOT BROKEN CODE | No onboarding pipeline - needs to be built |
| GAP-039 | Future feature | ⚠️ NOT BROKEN CODE | No verification gate - needs to be built |
| GAP-040 | Future feature | ⚠️ NOT BROKEN CODE | Only internal vector memory exists |
| GAP-041 | Future feature | ⚠️ NOT BROKEN CODE | No activation concept - needs to be built |
| GAP-042 | Stub field | ✅ VALID | `allowed_rag_sources` field exists with no backing system |
| GAP-043 | Future feature | ⚠️ NOT BROKEN CODE | No UI - needs to be built |
| GAP-044 | Future feature | ⚠️ NOT BROKEN CODE | No public/private distinction |
| GAP-045 | Future feature | ⚠️ NOT BROKEN CODE | Multi-asset aggregation not supported |

**Section 7.11 Status:** 9 of 10 gaps describe **unbuilt features**, not broken code. Only GAP-042 is a true gap (stub field with no backing). When implementing, treat GAP-036-041, GAP-043-045 as **new feature development**, not bug fixes.

---

#### Section 7.12: Governance Spine Wiring Gaps (GAP-046 to GAP-054)

| Gap | Type | Verdict | Implementation Note |
|-----|------|---------|---------------------|
| GAP-046 | Orphan code | ✅ CRITICAL | EventReactor never initialized - ROOT CAUSE |
| GAP-047 | Cascade | ⚠️ DEPENDS ON 046 | Audit handlers auto-fix when EventReactor wired |
| GAP-048 | Cascade | ⚠️ DEPENDS ON 046 | Heartbeat auto-starts when reactor.start() called |
| GAP-049 | Orphan code | ⚠️ VERIFY INTENT | AlertFatigueController may be intentionally unused |
| GAP-050 | Config flag unused | ✅ VALID | `rac_durability_enforce` defined, no enforcement code |
| GAP-051 | Config flag unused | ✅ VALID | `phase_status_invariant_enforce` defined, never checked |
| GAP-052 | Acknowledged gap | ✅ VALID | Jobs module explicitly states "No scheduler wired" |
| GAP-054 | Dependency | ⚠️ DEPENDS ON 046 | MidExecutionPolicyChecker needs EventReactor |

**Section 7.12 Status:**
- **Fix GAP-046 first** - it cascades to GAP-047, GAP-048, GAP-054
- GAP-049 needs investigation: was AlertFatigueController ever intended to be wired?
- GAP-050, GAP-051 are config flags that do nothing - need enforcement code
- GAP-052 is explicitly documented as missing

---

#### Implementation Priority Recommendation

```
PHASE 1: Fix GAP-046 (EventReactor)
         └─▶ Auto-resolves: GAP-047, GAP-048, GAP-054

PHASE 2: Wire existing code (no new models needed)
         - GAP-031 (bind_at enforcement)
         - GAP-033 (inspection constraints)
         - GAP-034 (override authority)
         - GAP-035 (failure mode)
         - GAP-050 (RAC durability)
         - GAP-051 (phase-status invariants)

PHASE 3: Investigate
         - GAP-049 (AlertFatigueController intent)
         - GAP-052 (scheduler priority)

PHASE 4: New feature development (Knowledge Domain)
         - GAP-036 to GAP-045 (treat as feature, not fix)
```

---

### 7.14 DO NOT SHIP BEFORE (T0 Checklist)

**Purpose:** These gaps MUST be closed before accepting any customer traffic. If any are open, governance is theatre.

**Gate:** No customer onboarding until ALL T0 gaps are verified.

#### T0 Critical Path

| Gap ID | Gap | Why T0 | Verification |
|--------|-----|--------|--------------|
| **GAP-016** | Same-step enforcement | Without this, STOP/KILL actions may not halt run in time | Test: policy violation → verify run halts within same step |
| **GAP-030** | Step-level enforcement guarantee | Enforcement timing must be deterministic | Test: inject violation mid-step → verify enforcement point |
| **GAP-031** | Binding moment enforcement | `bind_at` must be respected, not ignored | Test: RUN_START binding → verify no mid-run re-eval |
| **GAP-035** | Failure mode enforcement | No hardcoded fail-open on missing policy | Test: missing policy → verify fail-closed behavior |
| **GAP-046** | EventReactor initialization | Central event bus for all governance events | Test: startup → verify reactor running |
| **GAP-065** | Retrieval mediation layer | All data access must route through governance | Test: aos.access() → verify policy check → evidence |
| **GAP-066** | Ungoverned LLM path deprecated | Only governed invocation allowed | Test: verify `llm_invoke` not in registry when governed |
| **GAP-067** | Boot-fail policy | System must refuse runs if SPINE fails | Test: break EventReactor → verify `/runs` returns 503 |
| **GAP-068** | Policy conflict resolution | Explicit resolution when policies conflict (INV-005) | Test: STOP vs PAUSE → verify defined winner via INV-005 |
| **GAP-069** | Runtime governance kill switch | Emergency disable without restart | Test: call `/ops/governance/disable` → verify bypass + audit log |
| **GAP-059** | HTTP connector governance | HTTP access must be mediated | Test: aos.access(http) → verify policy gate |
| **GAP-060** | SQL gateway | No raw SQL from LLM | Test: verify template-only queries |
| **GAP-063** | MCP tool invocation | MCP must be governed | Test: MCP call → verify policy enforcement |

#### T0 Verification Script

```bash
#!/bin/bash
# scripts/preflight/t0_governance_gate.sh

echo "=== T0 GOVERNANCE GATE CHECK ==="

# 1. Check EventReactor is running
echo "Checking EventReactor..."
curl -s http://localhost:8000/health | jq '.components.event_reactor.healthy' | grep "true" || exit 1

# 2. Check ungoverned llm_invoke is NOT in skill registry
echo "Checking ungoverned paths removed..."
python -c "from app.skills import SKILL_REGISTRY; assert 'llm_invoke' not in SKILL_REGISTRY" || exit 1

# 3. Check boot-fail policy is active
echo "Checking boot-fail policy..."
curl -s http://localhost:8000/health | jq '.components.boot_guard.validated' | grep "true" || exit 1

# 4. Check fail-closed is default
echo "Checking fail-closed default..."
curl -s http://localhost:8000/api/v1/governance/config | jq '.default_failure_mode == "fail_closed"' || exit 1

# 5. GAP-069: Check runtime kill switch endpoint exists
echo "Checking runtime kill switch (GAP-069)..."
curl -s http://localhost:8000/api/v1/ops/governance/state | jq '.active' | grep "true" || exit 1

# 6. Check conflict resolution follows INV-005
echo "Checking conflict resolution (INV-005)..."
# This would be validated by unit tests, but we verify the module exists
python -c "from app.services.policy.conflict_resolver import resolve_policy_conflict" || exit 1

echo "=== T0 GATE PASSED (13 GAPS VERIFIED) ==="
```

#### Ship Decision Matrix

| Condition | Ship? | Action |
|-----------|-------|--------|
| All T0 gaps closed | ✅ YES | Proceed to customer onboarding |
| Any T0 gap open | ❌ NO | Fix T0 gaps before ANY customer traffic |
| T1 gaps open | ⚠️ CONDITIONAL | Can ship for beta, not SOC2 audit |
| T2 gaps open | ✅ YES | Can ship, monitor for scale issues |
| T3 gaps open | ✅ YES | Product polish, ship whenever ready |

---

### 7.15 Integration Domain Gaps (Customer Environment Mediation)

**Date:** 2026-01-20
**Reference:** GPT Integration Domain Design (RAG, MCP, Serverless)

**Key Insight:** The system has skills that CAN access external resources (HTTP, Postgres) but lacks:
- Registration of customer data sources as governed connectors
- Policy binding to specific data sources (knowledge planes)
- Retrieval evidence logging for audit
- MCP or serverless support

**Governing Principle:** Govern retrieval ex-ante (before access), not ex-post (inspecting output).

#### Core Models (GAP-055 to GAP-058)

These gaps create the foundational models for the Integration Domain.

**Internal Code Foundations:**
> These models can leverage existing deterministic internal code as foundations, but MUST be forked into separate customer-facing artifacts with strict separation from internal use.

| Gap ID | Model | Purpose | Internal Foundation | Separation Rule |
|--------|-------|---------|--------------------|-----------------|
| **GAP-055** | `CustomerDataSource` | Register external data sources (DB, API, Vector, File) | `CusIntegration` (✅ FORK) | New table `customer_data_sources`, new service |
| **GAP-056** | `KnowledgePlane` | Policy-aware abstraction over data sources | None (NEW) | No internal equivalent exists |
| **GAP-057** | `ConnectorRegistry` | Central registry with encrypted credentials | `CusCredentialService` (✅ WRAP) | Separate vault prefix `customer/` |
| **GAP-058** | `RetrievalEvidence` | Audit log for every mediated data access | None (NEW) | No internal equivalent exists |

**Model Details:**

| Gap ID | Model | Fields/Structure | Priority | Tier |
|--------|-------|------------------|----------|------|
| **GAP-055** | `CustomerDataSource` | `id`, `tenant_id`, `asset_type` (SQL/HTTP/VECTOR/FILE/MCP/SERVERLESS), `connection_config`, `auth_ref`, `status`, `health_state` | **HIGH** | T2 |
| **GAP-056** | `KnowledgePlane` | `plane_id`, `tenant_id`, `name`, `sensitivity` (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED), `default_policy` (ALLOW/DENY), `bound_source_ids[]` | **HIGH** | T2 |
| **GAP-057** | `ConnectorRegistry` | Extends `CustomerDataSource` with `credential_ref` (vault), `last_health_check`, `health_status`, tenant isolation | **HIGH** | T2 |
| **GAP-058** | `RetrievalEvidence` | `evidence_id`, `run_id`, `plane_id`, `connector_id`, `query_hash`, `doc_ids[]`, `token_count`, `policy_snapshot_id`, `timestamp` | **HIGH** | T1 |

**Core Model Implementation Notes:**

| Gap | Implementation Guidance |
|-----|------------------------|
| GAP-055 | Fork `CusIntegration` lifecycle model (created → enabled ↔ disabled → error). Create new table `customer_data_sources` — NEVER reuse `cus_integrations` table. |
| GAP-056 | Build from scratch. No internal equivalent exists. This is the policy binding layer. |
| GAP-057 | Wrap `CusCredentialService` in new `ConnectorCredentialService`. Use separate vault namespace (`customer/connectors/` not `internal/llm/`). |
| GAP-058 | Build from scratch. This is the audit trail — new table `retrieval_evidence`. |

#### Connector Wiring (GAP-059 to GAP-064)

These gaps wire the core models to specific integration archetypes.

**Internal Code Reuse Policy:**
> ✅ = Deterministic internal code CAN be forked as customer-facing (with separation)
> ❌ = LLM-controlled code CANNOT be used — build new deterministic service

| Gap ID | Connector Type | Coverage | Internal Code | Reuse? | Required State | Priority | Tier |
|--------|----------------|----------|---------------|--------|----------------|----------|------|
| **GAP-059** | HTTP/REST Connector | ~40% | `HttpCallSkill` | ❌ NEW | Build `HttpConnectorService` — machine-controlled, plane-bound, policy-gated | **MEDIUM** | **T0** |
| **GAP-060** | SQL Query Gateway | ~20% | `PostgresQuerySkill` | ❌ NEW | Build `SqlGatewayService` — template registry, no raw SQL, parameterized only | **HIGH** | **T0** |
| **GAP-061** | Vector Store Connector | ~15% | `VectorMemoryStore` | ✅ FORK | Fork as `CustomerVectorConnector` — separate schema, plane binding | **MEDIUM** | T2 |
| **GAP-062** | File/Object Store Connector | ~10% | None | NEW | Build `FileStoreConnector` for S3/GCS/Azure Blob with plane binding | **MEDIUM** | T2 |
| **GAP-063** | MCP Tool Invocation | ~5% | None | NEW | Build `McpConnectorService` — tool registry, plane binding, policy enforcement | **HIGH** | **T0** |
| **GAP-064** | Serverless Function Invocation | ~5% | None | NEW | Build `FunctionConnectorService` for Lambda/Cloud Functions with plane binding | **MEDIUM** | T2 |

**Gap Implementation Notes:**

| Gap | Implementation Guidance |
|-----|------------------------|
| GAP-059 | `HttpCallSkill` is LLM-controlled (LLM sets URL). Build new `HttpConnectorService` where machine resolves URL from `ConnectorRegistry` based on `plane_id`. |
| GAP-060 | `PostgresQuerySkill` accepts raw SQL from LLM. Build new `SqlGatewayService` with pre-registered query templates. LLM selects template ID, machine fills parameters. |
| GAP-061 | `VectorMemoryStore` is deterministic (pgvector ops). Fork as `CustomerVectorConnector` with separate schema (`customer_vectors` not `agent_memory`). |
| GAP-062 | No internal code exists. Build from scratch. |
| GAP-063 | No internal code exists. Build MCP client following MCP spec. |
| GAP-064 | No internal code exists. Build with timeout caps and policy gates. |

#### Mediation Orchestration (GAP-065)

| Gap ID | Component | Purpose | Current State | Required State | Priority | Tier |
|--------|-----------|---------|---------------|----------------|----------|------|
| **GAP-065** | Retrieval Mediation Layer | Unified `aos.access()` interface with deny-by-default | Skills execute directly without policy gate | All data access routes through mediation layer: policy check → connector resolution → evidence emission | **CRITICAL** | **T0** |

#### Dependency Graph

```
                    GAP-065: Retrieval Mediation Layer (CRITICAL)
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
    ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
    │   GAP-055     │        │   GAP-056     │        │   GAP-058     │
    │ CustomerData  │◄───────│ KnowledgePlane│───────►│  Retrieval    │
    │    Source     │        │ (policy bind) │        │   Evidence    │
    └───────────────┘        └───────────────┘        └───────────────┘
            │                         │
            ▼                         │
    ┌───────────────┐                 │
    │   GAP-057     │                 │
    │  Connector    │◄────────────────┘
    │   Registry    │
    └───────────────┘
            │
            ├──► GAP-059 (HTTP)
            ├──► GAP-060 (SQL)
            ├──► GAP-061 (Vector)
            ├──► GAP-062 (File)
            ├──► GAP-063 (MCP)
            └──► GAP-064 (Serverless)
```

#### Architecture Target

```
LLM
 ↓
aos_sdk.access({ plane, action, payload })
 ↓
┌─────────────────────────────────────────────────────────────┐
│            GAP-065: Retrieval Mediation Layer               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 1. Policy Check (GAP-056: plane → allowed?)             ││
│  │ 2. Connector Resolution (GAP-057: plane → source)       ││
│  │ 3. Evidence Emission (GAP-058: audit trail)             ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
 ↓
┌─────────────────────────────────────────────────────────────┐
│                    Connector Layer                          │
│  HTTP (059) │ SQL (060) │ Vector (061) │ File (062)        │
│  MCP (063)  │ Serverless (064)                              │
└─────────────────────────────────────────────────────────────┘
 ↓
Customer Environment (DB, API, Vector Store, S3, Lambda, MCP Server)
```

#### CRITICAL: Deterministic Mediation vs LLM Skills

**Architectural Principle:**
> LLM skills are LLM-controlled (LLM decides what, when, how).
> Mediation must be machine-controlled (machine decides whether, how, logs).

**DO NOT use LLM skills for customer data access governance:**

| Approach | Who Controls? | Governable? | Use For |
|----------|---------------|-------------|---------|
| **LLM Skills** (HttpCallSkill, etc.) | LLM controls params | ❌ NO | LLM-owned tasks (compose, analyze) |
| **Deterministic Connectors** | Machine code | ✅ YES | Customer data access |

**Wrong Architecture (LLM-controlled):**
```
Customer LLM → Plan with skills → HttpCallSkill(url=???) → Customer DB
                                  ↑ LLM controls target
```

**Correct Architecture (Machine-controlled):**
```
Customer LLM → aos_sdk.access(plane, action) → Mediation Layer → Connector → Customer DB
              ↑ LLM requests only             ↑ Machine decides
```

**GAP-059 to GAP-064 are DETERMINISTIC SERVICES, not skill extensions.**

#### Existing Code Classification

**Internal Script Repurposing Policy:**
> Internal scripts that are DETERMINISTIC (machine-controlled) MAY be repurposed for customer-facing use.
> However, they MUST be explicitly declared as customer-facing and MUST NOT be mangled with internal consumption.
> Separation is absolute — internal and customer-facing code paths must never share mutable state.

| Existing | Location | Classification | Repurpose Decision | Separation Rule |
|----------|----------|----------------|-------------------|-----------------|
| `CusIntegration` | `models/cus_models.py:120` | **DETERMINISTIC** | ✅ REPURPOSE as `CustomerDataSource` base | Fork model, new table `customer_data_sources` |
| `CusCredentialService` | `services/cus_credential_service.py` | **DETERMINISTIC** | ✅ REPURPOSE for connector credentials | Wrap in `ConnectorCredentialService`, separate vault namespace |
| `VectorMemoryStore` | `memory/vector_store.py:130` | **DETERMINISTIC** | ✅ REPURPOSE for customer vector connector | Fork as `CustomerVectorConnector`, separate pgvector schema |
| `HttpCallSkill` | `skills/http_call.py:34` | **LLM-CONTROLLED** | ❌ PATTERN ONLY | Cannot repurpose — LLM controls params |
| `PostgresQuerySkill` | `skills/postgres_query.py:98` | **LLM-CONTROLLED** | ❌ PATTERN ONLY | Cannot repurpose — LLM controls SQL |
| `allowed_rag_sources` | `models/monitor_config.py:72` | **STUB FIELD** | ❌ REPLACE with `KnowledgePlane` | Delete after migration |

**Separation Constraints (MANDATORY for REPURPOSE items):**

| Component | Internal Use | Customer-Facing Use | Separation Mechanism |
|-----------|--------------|---------------------|---------------------|
| `CusIntegration` → `CustomerDataSource` | LLM provider tracking | Customer data source tracking | Separate table, separate service |
| `CusCredentialService` → `ConnectorCredentialService` | LLM API keys | Customer connector credentials | Separate vault prefix (`internal/` vs `customer/`) |
| `VectorMemoryStore` → `CustomerVectorConnector` | Agent memory (ephemeral) | Customer knowledge (persistent) | Separate pgvector schema (`agent_memory` vs `customer_vectors`) |

**Why Separation Matters:**
1. **Internal state is ephemeral** — can be purged, rebuilt, experimented on
2. **Customer state is persistent** — governed, audited, cannot be accidentally purged
3. **Mixing creates governance holes** — internal code paths bypass customer policy checks
4. **Debugging is impossible** — "whose data is this?" becomes unanswerable

#### LLM Governance Gap

| Gap ID | Gap | Current State | Required State | Priority | Tier |
|--------|-----|---------------|----------------|----------|------|
| **GAP-066** | Ungoverned LLM Path Must Be Deprecated | `LLMInvokeGovernedSkill` exists at `agents/skills/llm_invoke_governed.py:300` with budget/safety governance, but regular `llm_invoke` is used in plans | **DEPRECATE regular `llm_invoke`** — only `LLMInvokeGovernedSkill` allowed in governed environments | **HIGH** | T0 |

**⚠️ GAP-066 Reframing (Critical):**

The original framing was: "Route all LLM calls through governed skill"
The correct framing is: **"DISABLE the ungoverned path entirely"**

| Path | Status | Action Required |
|------|--------|-----------------|
| `llm_invoke` (regular) | **DEPRECATED** | Remove from skill registry in governed mode |
| `LLMInvokeGovernedSkill` | **REQUIRED** | Make this the ONLY allowed LLM invocation |

**Why This Matters:**
- If both paths exist, enforcement will be bypassed accidentally
- Audits will fail silently (ungoverned calls leave no trail)
- Dual-path creates a governance hole that cannot be closed by policy

**GAP-066 Evidence:**
- `LLMInvokeGovernedSkill` has: budget enforcement, risk scoring, parameter clamping, blocked item tracking
- Only exported from `agents/skills/__init__.py`, never imported/used elsewhere
- Plans use regular `llm_invoke` skill which bypasses governance

**Implementation:**
1. Add governance profile check at skill registry load
2. If `GOVERNANCE_PROFILE != OBSERVE_ONLY`, exclude `llm_invoke` from registry
3. All plans forced to use `LLMInvokeGovernedSkill`

#### Implementation Priority

```
PHASE 1: Core Models (foundation)
         - GAP-055 (CustomerDataSource)
         - GAP-056 (KnowledgePlane)
         - GAP-057 (ConnectorRegistry)
         - GAP-058 (RetrievalEvidence)

PHASE 2: SQL Gateway (highest risk connector)
         - GAP-060 (prevents SQL injection, enables governed DB access)

PHASE 3: HTTP + MCP (broadest coverage)
         - GAP-059 (HTTP connector governance)
         - GAP-063 (MCP tool invocation)

PHASE 4: Remaining Connectors
         - GAP-061 (Vector)
         - GAP-062 (File)
         - GAP-064 (Serverless)

PHASE 5: Mediation Layer (ties everything together)
         - GAP-065 (unified aos.access() interface)
```

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
| 2026-01-20 | Systems Architect | Added Section 7.10: Policy Framing Gaps (GAP-031 to GAP-035) from GPT reference design analysis |
| 2026-01-20 | Systems Architect | Added Section 7.11: Knowledge Domain Gaps (GAP-036 to GAP-045) from GPT Knowledge Onboarding design |
