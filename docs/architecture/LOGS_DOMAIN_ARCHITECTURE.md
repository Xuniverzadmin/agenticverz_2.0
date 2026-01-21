# Logs Domain Architecture

**Status:** ACTIVE
**Created:** 2026-01-20
**Updated:** 2026-01-20
**Reference:** `CROSS_DOMAIN_DATA_ARCHITECTURE.md`, `POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md`

---

## 1. Overview

The Logs domain stores and queries raw execution records, system events, and audit trails. It answers the fundamental question:

> **"What is the raw truth?"**

### 1.1 Domain Scope

| Subdomain | Topics | Purpose |
|-----------|--------|---------|
| **Records** | LLM Runs, System Logs, Audit Logs | Raw evidence and proof |

### 1.2 Key Responsibilities

1. **Execution Recording** — Immutable trace storage for LLM runs
2. **System Event Logging** — Platform-level events and diagnostics
3. **Audit Trail** — User actions and governance events
4. **Evidence Production** — Compliance-grade proof for incidents
5. **Replay Support** — Time-travel through execution history
6. **Export** — Structured data export (JSON, CSV, PDF)

### 1.3 Core Principle

> Logs are **immutable evidence**. Once written, they cannot be modified or deleted through normal operations. This guarantees truth-grade audit trails.

---

## 2. Log Categories

### 2.1 Three Pillars

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LOGS DOMAIN PILLARS                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │    LLM RUNS     │  │  SYSTEM LOGS    │  │   AUDIT LOGS    │         │
│  │                 │  │                 │  │                 │         │
│  │  Execution      │  │  Platform       │  │  User Actions   │         │
│  │  traces with    │  │  events and     │  │  and governance │         │
│  │  step-by-step   │  │  diagnostics    │  │  decisions      │         │
│  │  evidence       │  │                 │  │                 │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
│           │                    │                    │                   │
│           ▼                    ▼                    ▼                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     EVIDENCE LAYER                               │   │
│  │                                                                  │   │
│  │  Immutable records, hash-verified integrity, replay capability  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Topic Details

| Topic | Source Table | Query Filter | Purpose |
|-------|--------------|--------------|---------|
| **LLM_RUNS** | `aos_traces`, `aos_trace_steps` | Execution traces | Agent run evidence |
| **SYSTEM_LOGS** | `system_logs` | System events | Platform diagnostics |
| **AUDIT** | `audit_logs` | User actions | Governance proof |

---

## 3. Models

### 3.1 LLM Run Models

#### TraceSummary

| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | UUID | Primary key |
| `run_id` | UUID | FK to runs table |
| `tenant_id` | UUID | Tenant isolation |
| `agent_id` | UUID | FK to agents |
| `status` | str | active, completed, failed, aborted |
| `step_count` | int | Total steps recorded |
| `total_tokens` | int | Cumulative token usage |
| `total_cost_cents` | int | Cumulative cost |
| `total_duration_ms` | int | Total execution time |
| `started_at` | datetime | Trace start |
| `completed_at` | datetime | Trace completion |
| `content_hash` | str | SHA256 hash for integrity |
| `is_synthetic` | bool | SDSR test marker |
| `synthetic_scenario_id` | str | SDSR scenario ID |
| `incident_id` | UUID | FK to incidents (nullable) |
| `violation_step_index` | int | Step where violation occurred (nullable) |
| `violation_timestamp` | datetime | Violation time (nullable) |
| `violation_policy_id` | UUID | Violated policy ID (nullable) |
| `violation_reason` | str | Human-readable violation description |
| `created_at` | datetime | Creation timestamp |

**Table:** `aos_traces`

**Invariant:** Traces are **immutable** after creation. Database triggers prevent UPDATE operations.

#### TraceStep

| Field | Type | Description |
|-------|------|-------------|
| `step_id` | UUID | Primary key |
| `trace_id` | UUID | FK to aos_traces |
| `step_index` | int | Sequential step number |
| `step_type` | str | input, llm_call, tool_call, output, policy_check, violation |
| `level` | str | info, warning, error |
| `source` | str | Component that created step |
| `timestamp` | datetime | Step timestamp |
| `tokens` | int | Tokens for this step |
| `cost_cents` | int | Cost for this step |
| `duration_ms` | int | Step duration |
| `input_data` | JSON | Input to the step |
| `output_data` | JSON | Output from the step |
| `metadata` | JSON | Additional context |
| `content_hash` | str | SHA256 hash of step content |
| `created_at` | datetime | Creation timestamp |

**Table:** `aos_trace_steps`

**Invariant:** Steps are **immutable** after creation.

#### TraceStepEvidence (Pydantic Model)

| Field | Type | Description |
|-------|------|-------------|
| `step_index` | int | Step number |
| `step_type` | str | Type of step |
| `timestamp` | datetime | When step occurred |
| `tokens` | int | Token consumption |
| `cost_cents` | int | Cost at step |
| `is_inflection_point` | bool | Whether this is the violation point |
| `content_hash` | str | Hash for integrity |

### 3.2 System Log Models

#### SystemLog

| Field | Type | Description |
|-------|------|-------------|
| `log_id` | UUID | Primary key |
| `level` | str | debug, info, warning, error, critical |
| `source` | str | Component name |
| `message` | str | Log message |
| `timestamp` | datetime | Event timestamp |
| `context` | JSON | Additional context |
| `trace_id` | str | Correlation ID (nullable) |
| `request_id` | str | HTTP request ID (nullable) |
| `created_at` | datetime | Creation timestamp |

**Table:** `system_logs`

**Log Levels:**

| Level | Purpose | Retention |
|-------|---------|-----------|
| `DEBUG` | Development diagnostics | 24 hours |
| `INFO` | Normal operations | 7 days |
| `WARNING` | Potential issues | 30 days |
| `ERROR` | Failures | 90 days |
| `CRITICAL` | System-wide issues | Permanent |

### 3.3 Audit Log Models

#### AuditLog

| Field | Type | Description |
|-------|------|-------------|
| `log_id` | UUID | Primary key |
| `tenant_id` | UUID | Tenant isolation |
| `actor_id` | UUID | FK to users |
| `actor_type` | str | user, system, api_key |
| `action` | str | Action performed |
| `resource_type` | str | Type of resource affected |
| `resource_id` | UUID | ID of affected resource |
| `timestamp` | datetime | Action timestamp |
| `details` | JSON | Action details |
| `ip_address` | str | Client IP |
| `user_agent` | str | Client user agent |
| `success` | bool | Whether action succeeded |
| `failure_reason` | str | Reason if failed |
| `created_at` | datetime | Creation timestamp |

**Table:** `audit_logs`

**Audited Actions:**

| Category | Actions |
|----------|---------|
| **Auth** | login, logout, token_refresh, api_key_created, api_key_revoked |
| **Policy** | policy_created, policy_updated, policy_deleted, policy_approved |
| **Run** | run_started, run_completed, run_cancelled, run_violated_policy |
| **Incident** | incident_created, incident_acknowledged, incident_resolved |
| **Account** | user_invited, user_removed, role_changed, settings_updated |
| **Override** | override_requested, override_approved, override_revoked |

**Invariant:** Audit logs are **immutable** and cannot be deleted through normal operations.

---

## 4. API Routes

### 4.1 Log Listing

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/logs/` | GET | List all logs (topic filter required) |
| `/api/v1/logs/llm-runs` | GET | LLM execution logs |
| `/api/v1/logs/system` | GET | System event logs |
| `/api/v1/logs/audit` | GET | Audit trail logs |

### 4.2 Log Detail

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/logs/{log_id}` | GET | Get single log entry |
| `/api/v1/logs/llm-runs/{trace_id}` | GET | Get trace detail |
| `/api/v1/logs/llm-runs/{trace_id}/steps` | GET | Get trace steps |

### 4.3 Search & Filter

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/logs/search` | POST | Search logs with filters |
| `/api/v1/logs/llm-runs/search` | POST | Search LLM traces |
| `/api/v1/logs/audit/search` | POST | Search audit logs |

### 4.4 Replay & Export

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/traces/{trace_id}/replay` | POST | Replay trace execution |
| `/api/v1/logs/export` | POST | Export logs (JSON/CSV) |
| `/api/v1/logs/llm-runs/{trace_id}/export` | POST | Export single trace |
| `/api/v1/logs/llm-runs/{trace_id}/export/evidence` | POST | Export evidence bundle |
| `/api/v1/logs/llm-runs/{trace_id}/export/soc2` | POST | Export SOC2 bundle |

### 4.5 Query Parameters

**Common Filters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_id` | UUID | Tenant scope (auto from auth) |
| `topic` | str | llm_runs, system, audit |
| `level` | str | Log level filter |
| `start_time` | datetime | Range start |
| `end_time` | datetime | Range end |
| `search` | str | Full-text search |
| `limit` | int | Page size (default: 50) |
| `offset` | int | Page offset |
| `sort` | str | Sort field |
| `order` | str | asc/desc |

**LLM Runs Filters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | UUID | Filter by run |
| `agent_id` | UUID | Filter by agent |
| `status` | str | Trace status |
| `has_violation` | bool | Only violated traces |
| `policy_id` | UUID | Filter by violated policy |

**Audit Filters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `actor_id` | UUID | Filter by actor |
| `action` | str | Filter by action |
| `resource_type` | str | Filter by resource type |
| `resource_id` | UUID | Filter by resource |
| `success` | bool | Filter by success/failure |

---

## 5. Services & Components

### 5.1 Layer Distribution

| File | Layer | Purpose |
|------|-------|---------|
| `backend/app/api/logs.py` | L2 | Logs API endpoints |
| `backend/app/api/traces.py` | L2 | Trace API endpoints |
| `backend/app/traces/store.py` | L6 | Trace storage (primary) |
| `backend/app/traces/models.py` | L6 | Trace models |
| `backend/app/traces/replay.py` | L4 | Trace replay engine |
| `backend/app/services/audit_log_service.py` | L4 | Audit logging |
| `backend/app/services/system_log_service.py` | L4 | System logging |
| `backend/app/services/log_export_service.py` | L3 | Log export |

### 5.2 Core Services

#### TraceStore

**Location:** `backend/app/traces/store.py`
**Layer:** L6
**Purpose:** Immutable trace storage and retrieval

```python
class TraceStore:
    def create_trace(self, run_id: str, tenant_id: str) -> TraceSummary
    def add_step(self, trace_id: str, step: TraceStep) -> None
    def complete_trace(self, trace_id: str, status: str) -> None
    def get_trace(self, trace_id: str) -> TraceSummary
    def get_steps(self, trace_id: str) -> list[TraceStep]
    def list_traces(self, filters: TraceFilters) -> list[TraceSummary]
```

**Key Behaviors:**

1. **Write-Once**: Steps cannot be modified after creation
2. **Hash Chain**: Each step includes content_hash for integrity
3. **Synthetic Marker**: SDSR tests marked with `is_synthetic=true`

#### AuditLogService

**Location:** `backend/app/services/audit_log_service.py`
**Layer:** L4
**Purpose:** Record governance actions for compliance

```python
class AuditLogService:
    def log_action(
        self,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict,
        success: bool = True
    ) -> AuditLog

    def search_logs(self, filters: AuditFilters) -> list[AuditLog]
```

**Audit Categories:**

| Category | Example Actions |
|----------|-----------------|
| `auth` | login, logout, token_refresh |
| `policy` | policy_created, policy_approved |
| `run` | run_started, run_violated_policy |
| `incident` | incident_created, incident_resolved |
| `override` | override_requested, override_approved |

#### SystemLogService

**Location:** `backend/app/services/system_log_service.py`
**Layer:** L4
**Purpose:** Platform event logging

```python
class SystemLogService:
    def log(
        self,
        level: str,
        source: str,
        message: str,
        context: dict | None = None,
        trace_id: str | None = None
    ) -> SystemLog

    def search_logs(self, filters: SystemLogFilters) -> list[SystemLog]
```

#### LogExportService

**Location:** `backend/app/services/log_export_service.py`
**Layer:** L3
**Purpose:** Export logs in various formats

```python
class LogExportService:
    def export_json(self, logs: list[Log]) -> bytes
    def export_csv(self, logs: list[Log]) -> bytes
    def export_trace_json(self, trace: TraceSummary, steps: list[TraceStep]) -> bytes
    def export_evidence_bundle(self, trace_id: str) -> EvidenceBundle
```

---

## 6. Data Flow

### 6.1 LLM Run Trace Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LLM RUN TRACE FLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Run Created                                                            │
│       │                                                                 │
│       ▼                                                                 │
│  TraceStore.create_trace()                                              │
│       │                                                                 │
│       ├─► TraceSummary created with run_id                              │
│       │                                                                 │
│  For each step:                                                         │
│       │                                                                 │
│       ▼                                                                 │
│  TraceStore.add_step()                                                  │
│       │                                                                 │
│       ├─► TraceStep created with:                                       │
│       │   - step_index (sequential)                                     │
│       │   - step_type (input, llm_call, tool_call, output)              │
│       │   - tokens, cost, duration                                      │
│       │   - content_hash (SHA256)                                       │
│       │                                                                 │
│  If violation detected:                                                 │
│       │                                                                 │
│       ▼                                                                 │
│  TraceStore.mark_violation()                                            │
│       │                                                                 │
│       ├─► violation_step_index set                                      │
│       ├─► violation_timestamp set                                       │
│       ├─► violation_policy_id set                                       │
│       ├─► violation_reason set                                          │
│       │                                                                 │
│  Run Completes                                                          │
│       │                                                                 │
│       ▼                                                                 │
│  TraceStore.complete_trace()                                            │
│       │                                                                 │
│       ├─► status updated                                                │
│       ├─► total_tokens, total_cost computed                             │
│       ├─► completed_at set                                              │
│       ├─► content_hash computed (all steps)                             │
│       │                                                                 │
│  Trace is now IMMUTABLE                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Audit Log Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AUDIT LOG FLOW                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  User Action                                                            │
│       │                                                                 │
│       ▼                                                                 │
│  API Endpoint                                                           │
│       │                                                                 │
│       ├─► Extract actor context (auth middleware)                       │
│       │                                                                 │
│       ▼                                                                 │
│  Domain Service                                                         │
│       │                                                                 │
│       ├─► Perform action                                                │
│       ├─► Call AuditLogService.log_action()                             │
│       │                                                                 │
│       ▼                                                                 │
│  AuditLogService                                                        │
│       │                                                                 │
│       ├─► Create AuditLog record:                                       │
│       │   - actor_id, actor_type                                        │
│       │   - action (e.g., policy_created)                               │
│       │   - resource_type (e.g., policy)                                │
│       │   - resource_id                                                 │
│       │   - details (JSON)                                              │
│       │   - ip_address, user_agent                                      │
│       │   - success/failure                                             │
│       │                                                                 │
│  Audit Log is IMMUTABLE                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Evidence Bundle Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     EVIDENCE BUNDLE FLOW                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Export Request: trace_id, format (evidence/soc2/executive)             │
│       │                                                                 │
│       ▼                                                                 │
│  LogExportService.export_evidence_bundle()                              │
│       │                                                                 │
│       ├─► Load TraceSummary                                             │
│       ├─► Load all TraceSteps                                           │
│       ├─► Load PolicySnapshot (from run)                                │
│       ├─► Load Incident (if exists)                                     │
│       │                                                                 │
│       ▼                                                                 │
│  Assemble EvidenceBundle:                                               │
│       │                                                                 │
│       ├─► bundle_id: UUID                                               │
│       ├─► bundle_type: evidence/soc2/executive                          │
│       ├─► generated_at: datetime                                        │
│       ├─► run_context:                                                  │
│       │   - run_id, agent_id, tenant_id                                 │
│       │   - started_at, completed_at                                    │
│       │   - termination_reason                                          │
│       ├─► policy_context:                                               │
│       │   - snapshot_id, policies, thresholds                           │
│       │   - violated_policy_id                                          │
│       ├─► trace_evidence:                                               │
│       │   - steps with is_inflection_point marker                       │
│       │   - content_hash for each step                                  │
│       ├─► incident_context (if applicable):                             │
│       │   - incident_id, severity, status                               │
│       │                                                                 │
│  If SOC2 Bundle:                                                        │
│       │                                                                 │
│       ├─► Add control_mappings:                                         │
│       │   - CC7.2: System Operations                                    │
│       │   - CC7.3: Change Management                                    │
│       │   - CC7.4: Incident Management                                  │
│       ├─► Add attestation_statement                                     │
│       │                                                                 │
│  If Executive Bundle:                                                   │
│       │                                                                 │
│       ├─► incident_summary (non-technical)                              │
│       ├─► business_impact                                               │
│       ├─► risk_level                                                    │
│       ├─► recommended_actions                                           │
│       │                                                                 │
│  Return bundle (or render to PDF)                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Cross-Domain Links

### 7.1 Inbound Links (→ Logs)

| Source Domain | Link Field | Purpose |
|---------------|------------|---------|
| Activity | `aos_traces.run_id` | Links trace to run |
| Incidents | `aos_traces.incident_id` | Links trace to incident |
| Policies | `aos_traces.violation_policy_id` | Links trace to violated policy |

### 7.2 Outbound Links (Logs →)

| Target Domain | Link Field | Purpose |
|---------------|------------|---------|
| Activity | Export provides run context | Evidence for run |
| Incidents | Export provides incident context | Evidence for incident |
| Policies | Audit logs reference policy actions | Governance trail |

### 7.3 Link Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     LOGS CROSS-DOMAIN LINKS                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────┐         ┌──────────┐         ┌──────────┐               │
│   │ Activity │         │ Incidents│         │ Policies │               │
│   │          │         │          │         │          │               │
│   │   Run    │         │ Incident │         │ PolicyRule│              │
│   └────┬─────┘         └────┬─────┘         └─────┬────┘               │
│        │                    │                     │                     │
│        │ run_id             │ incident_id         │ policy_id           │
│        │                    │                     │                     │
│        ▼                    ▼                     ▼                     │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │                           LOGS                                   │  │
│   │                                                                  │  │
│   │  ┌─────────────────────────────────────────────────────────┐    │  │
│   │  │                    aos_traces                            │    │  │
│   │  │  run_id ──────────────────────────────────────► Activity │    │  │
│   │  │  incident_id ─────────────────────────────────► Incidents│    │  │
│   │  │  violation_policy_id ─────────────────────────► Policies │    │  │
│   │  └─────────────────────────────────────────────────────────┘    │  │
│   │                                                                  │  │
│   │  ┌─────────────────────────────────────────────────────────┐    │  │
│   │  │                    audit_logs                            │    │  │
│   │  │  actor_id ────────────────────────────────────► Users    │    │  │
│   │  │  resource_id ─────────────────────────────────► Various  │    │  │
│   │  └─────────────────────────────────────────────────────────┘    │  │
│   │                                                                  │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Immutability & Integrity

### 8.1 Immutability Guarantees

| Table | Immutability Level | Enforcement |
|-------|-------------------|-------------|
| `aos_traces` | Full | DB trigger rejects UPDATE |
| `aos_trace_steps` | Full | DB trigger rejects UPDATE |
| `audit_logs` | Full | DB trigger rejects UPDATE/DELETE |
| `system_logs` | Append-only | Application enforced |

### 8.2 Database Triggers

```sql
-- aos_traces: immutable after creation
CREATE OR REPLACE FUNCTION raise_immutable_error()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Immutable record: modification not allowed';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_traces_immutable
BEFORE UPDATE ON aos_traces
FOR EACH ROW EXECUTE FUNCTION raise_immutable_error();

-- aos_trace_steps: immutable after creation
CREATE TRIGGER trigger_trace_steps_immutable
BEFORE UPDATE ON aos_trace_steps
FOR EACH ROW EXECUTE FUNCTION raise_immutable_error();

-- audit_logs: immutable after creation
CREATE TRIGGER trigger_audit_logs_immutable
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION raise_immutable_error();
```

### 8.3 Integrity Verification

**Hash Chain:**

Each trace step includes a `content_hash` computed from:
- `step_index`
- `step_type`
- `input_data`
- `output_data`
- `timestamp`

**Trace Hash:**

The `TraceSummary.content_hash` is computed from the ordered concatenation of all step hashes:

```python
def compute_trace_hash(steps: list[TraceStep]) -> str:
    sorted_steps = sorted(steps, key=lambda s: s.step_index)
    combined = "".join(s.content_hash for s in sorted_steps)
    return hashlib.sha256(combined.encode()).hexdigest()
```

**Verification:**

```python
def verify_trace_integrity(trace: TraceSummary, steps: list[TraceStep]) -> bool:
    computed_hash = compute_trace_hash(steps)
    return computed_hash == trace.content_hash
```

---

## 9. Replay Capability

### 9.1 Replay Engine

**Location:** `backend/app/traces/replay.py`
**Purpose:** Time-travel through execution history

```python
class TraceReplay:
    def replay(
        self,
        trace_id: str,
        emit_traces: bool = False,  # Default: no trace emission during replay
        speed: float = 1.0
    ) -> ReplayResult

    def get_state_at_step(self, trace_id: str, step_index: int) -> ExecutionState
```

### 9.2 Replay Modes

| Mode | Emit Traces | Use Case |
|------|-------------|----------|
| `AUDIT` | false | Compliance review |
| `DEBUG` | false | Investigation |
| `RERUN` | true | Re-execute with tracing |

### 9.3 Replay Invariant

> **Critical:** `emit_traces=False` is the default. Replaying a trace must not create new trace records unless explicitly requested. This preserves audit integrity.

---

## 10. Retention Policies

### 10.1 Default Retention

| Log Type | Retention | Notes |
|----------|-----------|-------|
| LLM Traces | 90 days | Configurable per tenant |
| System Logs | 30 days | Level-dependent |
| Audit Logs | 365 days | Compliance minimum |

### 10.2 Level-Based Retention (System Logs)

| Level | Retention |
|-------|-----------|
| DEBUG | 24 hours |
| INFO | 7 days |
| WARNING | 30 days |
| ERROR | 90 days |
| CRITICAL | Permanent |

### 10.3 Compliance Overrides

For compliance-critical tenants:

| Regulation | LLM Traces | Audit Logs |
|------------|------------|------------|
| SOC2 | 365 days | 7 years |
| HIPAA | 6 years | 6 years |
| GDPR | As needed | As needed |

---

## 11. Panel Data Shapes

### 11.1 LLM Runs Panel (O2 — List)

```typescript
interface LLMRunsListData {
  items: Array<{
    trace_id: string;
    run_id: string;
    agent_name: string;
    status: 'active' | 'completed' | 'failed' | 'aborted';
    step_count: number;
    total_tokens: number;
    total_cost_cents: number;
    has_violation: boolean;
    violation_policy_id?: string;
    started_at: string;
    completed_at?: string;
  }>;
  pagination: { total: number; page: number; page_size: number };
  filters_applied?: Record<string, string>;
}
```

### 11.2 Trace Detail Panel (O3 — Detail)

```typescript
interface TraceDetailData {
  trace: {
    trace_id: string;
    run_id: string;
    status: string;
    step_count: number;
    total_tokens: number;
    total_cost_cents: number;
    violation_step_index?: number;
    violation_policy_id?: string;
    violation_reason?: string;
  };
  steps: Array<{
    step_index: number;
    step_type: string;
    timestamp: string;
    tokens: number;
    cost_cents: number;
    is_inflection_point: boolean;
  }>;
  actions: Array<{ action: string; label: string; enabled: boolean }>;
}
```

### 11.3 Audit Log Panel (O2 — List)

```typescript
interface AuditLogListData {
  items: Array<{
    log_id: string;
    actor_name: string;
    action: string;
    resource_type: string;
    resource_id: string;
    timestamp: string;
    success: boolean;
  }>;
  pagination: { total: number; page: number; page_size: number };
}
```

### 11.4 Evidence Export Panel (O5 — Evidence)

```typescript
interface EvidenceExportData {
  source: { id: string; type: 'trace' | 'incident' };
  trace: {
    trace_id: string;
    steps: Array<{
      step_number: number;
      timestamp: string;
      type: string;
      is_inflection_point: boolean;
    }>;
  };
  exports: Array<{
    format: 'json' | 'csv' | 'pdf';
    bundle_type: 'evidence' | 'soc2' | 'executive';
    url: string;
  }>;
  integrity: {
    content_hash: string;
    verified: boolean;
  };
}
```

---

## 12. References

| Document | Purpose |
|----------|---------|
| `CROSS_DOMAIN_DATA_ARCHITECTURE.md` | Domain registry and data flow |
| `POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md` | Policy integration |
| `BACKEND_REMEDIATION_PLAN.md` | Gap remediation status |
| `CUSTOMER_CONSOLE_V2_CONSTITUTION.md` | Domain definitions |

---

**End of Document**
