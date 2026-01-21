# LOGS DOMAIN V2 CONTRACT

**Status:** RATIFIED
**Effective:** 2026-01-19
**PIN Reference:** PIN-XXX (to be assigned)

---

## 0. Design Positioning (LOCKED)

**Logs ≠ Activity ≠ Incident ≠ Policy**

| Domain | Role | Nature |
|--------|------|--------|
| **Activity** | Execution lifecycle | Stateful, transitions |
| **Incidents** | Failure manifestation | Event-driven |
| **Policy** | Governance & intent | Decisional |
| **Logs** | **Immutable evidence + replay substrate** | APPEND-ONLY |

> **Logs EXPLAIN runs, incidents, and policy decisions — they do not govern or decide.**

---

## 1. Domain Shape (Exactly 3 Topics)

| Topic | Meaning | Nature | Source Tables |
|-------|---------|--------|---------------|
| **LLM_RUNS** | Run-scoped execution evidence | Immutable | `llm_run_records`, `aos_traces`, `aos_trace_steps` |
| **SYSTEM_LOGS** | Infra + environment evidence | Time-series / snapshot | `system_records` |
| **AUDIT** | Access, integrity, compliance evidence | Append-only | `audit_ledger`, `log_exports` |

> **Rule:** Topics are evidence classes, not filters.

---

## 2. Single Facade (NON-NEGOTIABLE)

### Canonical Facade
```
/api/v1/logs/*
```

- Frontend panels talk **ONLY** to this
- No `/guard/logs` for domain authority
- No `/api/v1/traces` for logs authority

Everything else becomes **internal or adapter APIs**.

### Reclassifications

| API | New Classification | Notes |
|-----|-------------------|-------|
| `traces.py` | SDK/Internal Trace API | For replay verification, not logs authority |
| `guard_logs.py` | L2a Adapter (Console-scoped) | Must proxy to `/api/v1/logs/*` |

---

## 3. Global Evidence Metadata Contract (MANDATORY)

### INV-LOG-META-001: Metadata Invariant
> **Every Logs response MUST include `EvidenceMetadata`. Absence is a contract violation.**

### 3.1 Canonical Evidence Metadata Model

```python
class EvidenceMetadata(BaseModel):
    """Global metadata contract for all Logs responses."""

    # Identity
    tenant_id: str
    run_id: Optional[str] = None

    # Actor attribution (precedence: human > agent > system)
    human_actor_id: Optional[str] = None     # User / admin
    agent_id: Optional[str] = None           # Autonomous agent
    system_id: Optional[str] = None          # Scheduler, worker, infra component

    # Time
    occurred_at: datetime                     # When the event actually happened
    recorded_at: datetime                     # When it was persisted
    timezone: str = "UTC"

    # Correlation spine
    trace_id: Optional[str] = None
    policy_ids: List[str] = []
    incident_ids: List[str] = []
    export_id: Optional[str] = None
    correlation_id: Optional[str] = None     # Cross-system correlation

    # Source & provenance
    source_domain: Literal["ACTIVITY", "POLICY", "INCIDENTS", "LOGS", "SYSTEM"]
    source_component: str                     # e.g. TraceStore, AuditLedgerWriter
    origin: Literal["SYSTEM", "HUMAN", "AGENT", "MIGRATION", "REPLAY"]

    # Integrity
    checksum: Optional[str] = None            # For O5 / audit-grade objects
    immutable: bool = True
```

### 3.2 Actor Resolution Precedence

```yaml
actor_resolution_order:
  1: human_actor_id  # If present, human caused this
  2: agent_id        # If autonomous agent
  3: system_id       # If infrastructure / scheduler
```

### 3.3 Correlation Spine Definition

The correlation spine is the **join authority** for cross-domain queries:

| Field | Primary Key For | Join Direction |
|-------|-----------------|----------------|
| `run_id` | Activity → Logs | Primary binding |
| `trace_id` | Logs internal | LLM_RUNS detail |
| `policy_ids[]` | Policy → Logs | Governance trace |
| `incident_ids[]` | Incidents → Logs | Failure evidence |
| `export_id` | Logs internal | O5 exports |
| `correlation_id` | Cross-system | External tracing |

---

## 4. Topic-Scoped Endpoints (O-Level Preserved)

### 4.1 LLM_RUNS (Run-Scoped Evidence)

| O-Level | Question Answered | Endpoint |
|---------|-------------------|----------|
| **List** | What runs exist? | `GET /logs/llm-runs` |
| **O1** | What is the canonical immutable run record? | `GET /logs/llm-runs/{run_id}/envelope` |
| **O2** | How did the run execute step-by-step? | `GET /logs/llm-runs/{run_id}/trace` |
| **O3** | How did policy & thresholds interact? | `GET /logs/llm-runs/{run_id}/governance` |
| **O4** | What happened around the inflection point? | `GET /logs/llm-runs/{run_id}/replay` |
| **O5** | What is the audit-grade evidence bundle? | `GET /logs/llm-runs/{run_id}/export` |

### 4.2 SYSTEM_LOGS (Infra Evidence)

| O-Level | Question Answered | Endpoint | Availability |
|---------|-------------------|----------|--------------|
| **List** | What system events exist? | `GET /logs/system` | ✅ |
| **O1** | What was the environment baseline at run start? | `GET /logs/system/{run_id}/snapshot` | ✅ |
| **O2** | What was infra telemetry during execution? | `GET /logs/system/{run_id}/telemetry` | ⚠️ STUB |
| **O3** | What infra events impacted the run? | `GET /logs/system/{run_id}/events` | ✅ |
| **O4** | Infra replay around anomaly window | `GET /logs/system/{run_id}/replay` | ✅ |
| **O5** | Infra audit & responsibility attribution | `GET /logs/system/audit` | ✅ |

**O2 Stub Response:**
```json
{
  "status": "telemetry_not_collected",
  "reason": "infrastructure_telemetry_producer_not_implemented",
  "run_id": "{run_id}",
  "available_data": ["events", "snapshot", "replay"],
  "future_milestone": "M-TBD"
}
```

### 4.3 AUDIT (Access & Compliance)

| O-Level | Question Answered | Endpoint |
|---------|-------------------|----------|
| **List** | What audit entries exist? | `GET /logs/audit` |
| **O1** | Who accessed what, when, how? | `GET /logs/audit/identity` |
| **O2** | What authorization decisions occurred? | `GET /logs/audit/authorization` |
| **O3** | Who viewed/exported logs and traces? | `GET /logs/audit/access` |
| **O4** | Was integrity compromised? | `GET /logs/audit/integrity` |
| **O5** | What compliance exports exist? | `GET /logs/audit/exports` |

---

## 5. Capability Mapping (1:1:1 Enforced)

Each **O1 endpoint** is a **capability**. O2–O5 are **depth**, not new capabilities.

| Capability ID | Domain | Topic | Status |
|---------------|--------|-------|--------|
| `logs.llm_runs` | LOGS | LLM_RUNS | DECLARED |
| `logs.system_logs` | LOGS | SYSTEM_LOGS | DECLARED |
| `logs.audit` | LOGS | AUDIT | DECLARED |

---

## 6. Data Lifecycle Rules

### INV-LOG-LIFE-001: Retention Policy

```yaml
logs_lifecycle:
  llm_runs:
    hot_retention: 90 days
    archive_to: R2 (failure_patterns bucket)
    synthetic_purge: 7 days
    archive_format: gzip JSON

  system_logs:
    hot_retention: 30 days
    archive_to: optional

  audit:
    hot_retention: 7 years
    archive_to: never auto-purge
    compliance_tags: [SOC2, ISO27001]

  log_exports:
    hot_retention: 1 year
    archive_to: R2
```

### 6.1 Immutability Rules

| Table | UPDATE | DELETE | Enforcement |
|-------|--------|--------|-------------|
| `llm_run_records` | ❌ FORBIDDEN | ❌ FORBIDDEN | DB trigger |
| `system_records` | ❌ FORBIDDEN | ❌ FORBIDDEN | DB trigger |
| `audit_ledger` | ❌ FORBIDDEN | ❌ FORBIDDEN | DB trigger |
| `aos_traces` | ❌ FORBIDDEN | ❌ FORBIDDEN | DB trigger |
| `aos_trace_steps` | ❌ FORBIDDEN | ❌ FORBIDDEN | DB trigger |
| `log_exports` | ❌ FORBIDDEN | ❌ FORBIDDEN | DB trigger |

---

## 7. Producer Declarations

### INV-LOG-PROD-001: Every Record Has an Owner

```yaml
logs_producers:
  llm_runs:
    owner: TraceStore (backend/app/traces/)
    trigger: run_completed event
    tables: [llm_run_records, aos_traces, aos_trace_steps]
    metadata_responsibility:
      - tenant_id: REQUIRED
      - run_id: REQUIRED
      - trace_id: REQUIRED
      - agent_id: if autonomous
      - source_component: "TraceStore"
      - origin: "SYSTEM" | "AGENT"

  system_logs:
    owner: SystemRecordWriter (backend/app/engines/)
    trigger: [worker_heartbeat, api_health, migration_complete, auth_change]
    tables: [system_records]
    scope: |
      IN SCOPE:
      - Worker start/stop/restart
      - API health transitions
      - Migration execution
      - Auth config changes

      OUT OF SCOPE (future milestone):
      - Infrastructure telemetry (CPU, memory, network)
      - Cloud provider events
      - Container orchestration events
    metadata_responsibility:
      - tenant_id: optional (NULL for system-wide)
      - system_id: REQUIRED
      - correlation_id: if correlated to run
      - source_component: "SystemRecordWriter"
      - origin: "SYSTEM"

  audit:
    owner: AuditLedgerWriter (backend/app/engines/)
    trigger: governance_action event
    tables: [audit_ledger]
    metadata_responsibility:
      - tenant_id: REQUIRED
      - actor_type: REQUIRED
      - actor_id: REQUIRED if human/agent
      - source_component: "AuditLedgerWriter"
      - origin: from actor_type

  log_exports:
    owner: LogExportService (to be created)
    trigger: export_requested event
    tables: [log_exports]
    metadata_responsibility:
      - tenant_id: REQUIRED
      - requested_by: REQUIRED
      - export_id: REQUIRED
      - checksum: REQUIRED on completion
      - source_component: "LogExportService"
      - origin: "HUMAN" | "SYSTEM"
```

---

## 8. Replay Semantics

### INV-LOG-REPLAY-001: Replay is a Query, Not Storage

> **Replay window = time-window join, not a new dataset**

```sql
-- O4 Replay Query Contract
-- Returns T±30s around inflection point

WITH inflection AS (
    SELECT inflection_timestamp
    FROM runs
    WHERE id = :run_id
)
SELECT
    'llm' as source,
    step_index,
    timestamp,
    skill_name as action,
    outcome_category as outcome
FROM aos_trace_steps
WHERE trace_id = (
    SELECT trace_id FROM aos_traces WHERE run_id = :run_id
)
AND timestamp BETWEEN
    (SELECT inflection_timestamp - interval '30 seconds' FROM inflection)
    AND (SELECT inflection_timestamp + interval '30 seconds' FROM inflection)

UNION ALL

SELECT
    'system' as source,
    NULL as step_index,
    created_at as timestamp,
    event_type as action,
    severity as outcome
FROM system_records
WHERE (tenant_id = :tenant_id OR tenant_id IS NULL)
AND created_at BETWEEN
    (SELECT inflection_timestamp - interval '30 seconds' FROM inflection)
    AND (SELECT inflection_timestamp + interval '30 seconds' FROM inflection)

UNION ALL

SELECT
    'policy' as source,
    NULL as step_index,
    created_at as timestamp,
    event_type as action,
    entity_type as outcome
FROM audit_ledger
WHERE tenant_id = :tenant_id
AND entity_type IN ('POLICY_RULE', 'LIMIT')
AND created_at BETWEEN
    (SELECT inflection_timestamp - interval '30 seconds' FROM inflection)
    AND (SELECT inflection_timestamp + interval '30 seconds' FROM inflection)

ORDER BY timestamp;
```

---

## 9. Cross-Domain Binding

### Linkage Rules (Implicit, Clean)

| From Domain | Binding Key | To Logs Endpoint | Purpose |
|-------------|-------------|------------------|---------|
| Activity | `run_id` | `/logs/llm-runs/{run_id}/envelope` | Explain execution |
| Incidents | `run_id` | `/logs/llm-runs/{run_id}/replay` | Provide evidence |
| Policy | `run_id` | `/logs/llm-runs/{run_id}/governance` | Show enforcement |
| Overview | aggregate | `/logs/audit/exports` | Compliance proof |

> **No domain calls Logs to decide. Logs only explain.**

---

## 10. Database Schema Additions

### 10.1 New Table: `log_exports`

```sql
CREATE TABLE log_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    scope VARCHAR(32) NOT NULL CHECK (scope IN ('llm_run', 'system', 'audit', 'compliance')),
    run_id UUID,  -- nullable, for run-scoped exports

    -- Request metadata
    requested_by VARCHAR(128) NOT NULL,
    format VARCHAR(16) NOT NULL CHECK (format IN ('json', 'csv', 'pdf', 'zip')),

    -- Provenance (per GPT metadata contract)
    origin VARCHAR(32) NOT NULL CHECK (origin IN ('SYSTEM', 'HUMAN', 'AGENT')),
    source_component VARCHAR(64) NOT NULL DEFAULT 'LogExportService',
    correlation_id VARCHAR(64),

    -- Completion
    checksum VARCHAR(128),
    status VARCHAR(32) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
    delivered_at TIMESTAMPTZ,

    -- Immutable timestamp
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Append-only trigger (immutability)
CREATE TRIGGER log_exports_immutable
    BEFORE UPDATE OR DELETE ON log_exports
    FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- Index for queries
CREATE INDEX idx_log_exports_tenant_created
    ON log_exports(tenant_id, created_at DESC);
```

### 10.2 Required Indexes (Add if Missing)

```sql
-- LLM Run Records
CREATE INDEX IF NOT EXISTS idx_llm_run_records_tenant_created
    ON llm_run_records(tenant_id, created_at DESC);

-- Audit Ledger
CREATE INDEX IF NOT EXISTS idx_audit_ledger_tenant_created
    ON audit_ledger(tenant_id, created_at DESC);

-- System Records
CREATE INDEX IF NOT EXISTS idx_system_records_tenant_created
    ON system_records(tenant_id, created_at DESC);

-- Trace Steps (for replay window)
CREATE INDEX IF NOT EXISTS idx_aos_trace_steps_trace_timestamp
    ON aos_trace_steps(trace_id, timestamp);
```

### 10.3 Schema Extensions (Add Columns)

```sql
-- audit_ledger: Add correlation_id for correlation spine
ALTER TABLE audit_ledger
ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(64);

-- system_records: Ensure correlation_id exists (already present, verify)
-- No change needed based on existing schema
```

---

## 11. Intent YAML Corrections

### Mapping Table

| Topic | Old (Wrong) | New (Correct) |
|-------|-------------|---------------|
| LLM_RUNS | `/api/v1/runtime/traces` | `/api/v1/logs/llm-runs` |
| SYSTEM_LOGS | `/guard/logs` | `/api/v1/logs/system` |
| AUDIT | `/api/v1/traces` | `/api/v1/logs/audit` |

---

## 12. SDSR Requirements

### Scenarios to Create

| Scenario ID | Purpose | Validates |
|-------------|---------|-----------|
| SDSR-LOG-LLM-001 | Run exists → envelope retrievable | `logs.llm_runs` O1 |
| SDSR-LOG-LLM-GOV-001 | Threshold breach → governance trace present | `logs.llm_runs` O3 |
| SDSR-LOG-AUD-001 | Log export → audit entry recorded | `logs.audit` O5 |
| SDSR-LOG-SYS-001 | Infra event → system record exists | `logs.system_logs` O3 |

### Status Flow

```
DECLARED → (SDSR passes) → OBSERVED → (production stable) → TRUSTED
```

---

## 13. Explicit Non-Goals (FOUNDATION LOCK)

- ❌ No log mutation APIs
- ❌ No inline analytics
- ❌ No policy decisions in Logs
- ❌ No cross-domain writes
- ❌ No SYSTEM_LOGS telemetry until producer exists

---

## 14. Related Documents

| Document | Purpose |
|----------|---------|
| `LOGS_DOMAIN_V2_IMPLEMENTATION_PLAN.md` | Execution plan |
| `ENVIRONMENT_CONTRACT.md` | Environment modes |
| `SDSR_SYSTEM_CONTRACT.md` | SDSR validation rules |
| `AUTH_ARCHITECTURE_BASELINE.md` | Auth patterns |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-19 | Initial ratification | Claude + Human |
