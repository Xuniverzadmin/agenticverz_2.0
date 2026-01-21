# LOGS DOMAIN V2 — Implementation Plan

**Status:** APPROVED
**Effective:** 2026-01-19
**Contract Reference:** `LOGS_DOMAIN_V2_CONTRACT.md`

---

## Executive Summary

This plan implements the ratified LOGS DOMAIN V2 design with all sustainability amendments including:
- Global Evidence Metadata Contract
- Actor Resolution Precedence
- Correlation Spine
- Data Lifecycle Rules
- Producer Declarations

**Scope Decision:** SYSTEM_LOGS is **scoped down** to existing producers (worker events, API health, migrations).

---

## Schema Inventory Analysis

### Existing Tables (Verified in Codebase)

| Table | Location | Status | Missing Columns |
|-------|----------|--------|-----------------|
| `audit_ledger` | `backend/app/models/audit_ledger.py` | ✅ Exists | `correlation_id` |
| `llm_run_records` | `backend/app/models/logs_records.py` | ✅ Exists | None |
| `system_records` | `backend/app/models/logs_records.py` | ✅ Exists | None |
| `aos_traces` | Migration 012 | ✅ Exists | None |
| `aos_trace_steps` | Migration 012 | ✅ Exists | None |
| `log_exports` | N/A | ❌ **MISSING** | All (new table) |

### Existing Indexes (Verified)

| Index | Table | Status |
|-------|-------|--------|
| `idx_llm_run_records_tenant_created` | `llm_run_records` | ❌ Missing |
| `idx_audit_ledger_tenant_created` | `audit_ledger` | ❌ Missing |
| `idx_system_records_tenant_created` | `system_records` | ❌ Missing |
| `idx_aos_trace_steps_trace_timestamp` | `aos_trace_steps` | ❌ Missing |
| `idx_aos_traces_run_id` | `aos_traces` | ✅ Exists |

### Existing Columns for Metadata

| Metadata Field | audit_ledger | llm_run_records | system_records |
|----------------|--------------|-----------------|----------------|
| `tenant_id` | ✅ | ✅ | ✅ (nullable) |
| `run_id` | ❌ | ✅ | ❌ |
| `actor_type` | ✅ | ❌ | ❌ |
| `actor_id` | ✅ | ❌ | ❌ |
| `created_at` | ✅ | ✅ | ✅ |
| `correlation_id` | ❌ | ❌ | ✅ |
| `source` | ❌ | ✅ | ❌ |
| `caused_by` | ❌ | ❌ | ✅ |

---

## Phase 0: Pre-Implementation Setup

### 0.1 Governance Artifacts

| Artifact | Location | Action | Status |
|----------|----------|--------|--------|
| LOGS_DOMAIN_V2_CONTRACT.md | `docs/contracts/` | ✅ Created | DONE |
| LOGS_DOMAIN_V2_IMPLEMENTATION_PLAN.md | `docs/contracts/` | ✅ Created | DONE |
| Intent YAML corrections (15 files) | `design/l2_1/intents/LOG-REC-*.yaml` | Update | TODO |
| Capability registry (3 files) | `backend/AURORA_L2_CAPABILITY_REGISTRY/` | Create | TODO |
| SDSR scenario stubs (4 files) | `backend/scripts/sdsr/scenarios/` | Create | TODO |

### 0.2 Database Migrations Required

**Migration 1: Create log_exports table**
```
File: backend/alembic/versions/XXX_create_log_exports.py
```

**Migration 2: Add missing indexes**
```
File: backend/alembic/versions/XXX_logs_domain_v2_indexes.py
```

**Migration 3: Add correlation_id to audit_ledger**
```
File: backend/alembic/versions/XXX_audit_ledger_correlation_id.py
```

### 0.3 Model Files to Create/Update

| File | Action | Content |
|------|--------|---------|
| `backend/app/models/log_exports.py` | CREATE | LogExports SQLModel |
| `backend/app/api/logs/models.py` | CREATE | EvidenceMetadata + Response models |
| `backend/app/models/audit_ledger.py` | UPDATE | Add correlation_id field |

---

## Phase 1: Facade Restructure

### 1.1 Directory Structure

```
backend/app/api/
├── logs.py                    # Unified facade (refactored)
├── logs/
│   ├── __init__.py
│   ├── models.py             # EvidenceMetadata + all response models
│   ├── llm_runs.py           # LLM_RUNS O1-O5 handlers
│   ├── system_logs.py        # SYSTEM_LOGS O1-O5 handlers
│   ├── audit.py              # AUDIT O1-O5 handlers
│   └── helpers.py            # Shared utilities
```

### 1.2 Response Models with Metadata

```python
# backend/app/api/logs/models.py

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel


class EvidenceMetadata(BaseModel):
    """Global metadata contract for all Logs responses (INV-LOG-META-001)."""

    # Identity
    tenant_id: str
    run_id: Optional[str] = None

    # Actor attribution (precedence: human > agent > system)
    human_actor_id: Optional[str] = None
    agent_id: Optional[str] = None
    system_id: Optional[str] = None

    # Time
    occurred_at: datetime
    recorded_at: datetime
    timezone: str = "UTC"

    # Correlation spine
    trace_id: Optional[str] = None
    policy_ids: List[str] = []
    incident_ids: List[str] = []
    export_id: Optional[str] = None
    correlation_id: Optional[str] = None

    # Source & provenance
    source_domain: Literal["ACTIVITY", "POLICY", "INCIDENTS", "LOGS", "SYSTEM"]
    source_component: str
    origin: Literal["SYSTEM", "HUMAN", "AGENT", "MIGRATION", "REPLAY"]

    # Integrity
    checksum: Optional[str] = None
    immutable: bool = True


class LLMRunEnvelope(BaseModel):
    """O1: Canonical immutable run record."""
    metadata: EvidenceMetadata
    run_id: str
    status: str
    executor_type: str  # LLM, agent, human
    outcome: str        # success, failure, near_threshold, terminated
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_cents: int
    started_at: datetime
    completed_at: Optional[datetime]


class LLMRunTrace(BaseModel):
    """O2: Step-by-step execution."""
    metadata: EvidenceMetadata
    run_id: str
    steps: List[dict]  # TraceStep objects
    total_steps: int
    total_duration_ms: float
    total_tokens: int


class LLMRunGovernance(BaseModel):
    """O3: Policy interaction trace."""
    metadata: EvidenceMetadata
    run_id: str
    threshold_checks: List[dict]
    policy_evaluations: List[dict]
    overrides: List[dict]


class ReplayWindow(BaseModel):
    """O4: 60-second replay window."""
    metadata: EvidenceMetadata
    run_id: str
    center_timestamp: datetime
    window_start: datetime
    window_end: datetime
    llm_events: List[dict]
    system_events: List[dict]
    policy_events: List[dict]


class EvidenceBundle(BaseModel):
    """O5: Audit-grade export package."""
    metadata: EvidenceMetadata
    run_id: str
    export_id: str
    format: str
    checksum: str
    retention_class: str
    compliance_tags: List[str]
    download_url: Optional[str]


# SYSTEM_LOGS Models
class SystemSnapshot(BaseModel):
    """O1: Environment baseline at run start."""
    metadata: EvidenceMetadata
    run_id: str
    environment_id: str
    component: str
    event_type: str
    severity: str
    summary: str


class SystemTelemetryStub(BaseModel):
    """O2: Telemetry stub (not yet collected)."""
    status: str = "telemetry_not_collected"
    reason: str = "infrastructure_telemetry_producer_not_implemented"
    run_id: str
    available_data: List[str] = ["events", "snapshot", "replay"]
    future_milestone: str = "M-TBD"


class SystemEvents(BaseModel):
    """O3: Infra events impacting run."""
    metadata: EvidenceMetadata
    run_id: str
    events: List[dict]
    total: int


# AUDIT Models
class AuditIdentity(BaseModel):
    """O1: Identity and auth lifecycle."""
    metadata: EvidenceMetadata
    entries: List[dict]
    total: int


class AuditAuthorization(BaseModel):
    """O2: Authorization decisions."""
    metadata: EvidenceMetadata
    decisions: List[dict]
    total: int


class AuditAccess(BaseModel):
    """O3: Log/trace access audit."""
    metadata: EvidenceMetadata
    access_events: List[dict]
    total: int


class AuditIntegrity(BaseModel):
    """O4: Integrity and tamper detection."""
    metadata: EvidenceMetadata
    integrity_status: str
    anomalies: List[dict]
    last_verified: datetime


class AuditExports(BaseModel):
    """O5: Compliance exports."""
    metadata: EvidenceMetadata
    exports: List[dict]
    total: int
```

### 1.3 Endpoint Routes

```python
# backend/app/api/logs.py (refactored facade)

from fastapi import APIRouter

from .logs import llm_runs, system_logs, audit

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

# Include sub-routers
router.include_router(llm_runs.router)
router.include_router(system_logs.router)
router.include_router(audit.router)
```

---

## Phase 2: O-Level Implementation

### 2.1 LLM_RUNS Endpoints

| O-Level | Endpoint | Data Source | Implementation |
|---------|----------|-------------|----------------|
| List | `GET /llm-runs` | `llm_run_records` | Rebind existing |
| O1 | `GET /llm-runs/{run_id}/envelope` | `llm_run_records` | NEW |
| O2 | `GET /llm-runs/{run_id}/trace` | `aos_traces` + steps | Rebind existing |
| O3 | `GET /llm-runs/{run_id}/governance` | `audit_ledger` filtered | NEW |
| O4 | `GET /llm-runs/{run_id}/replay` | Time-window join | NEW |
| O5 | `GET /llm-runs/{run_id}/export` | `log_exports` | NEW |

### 2.2 SYSTEM_LOGS Endpoints

| O-Level | Endpoint | Data Source | Implementation |
|---------|----------|-------------|----------------|
| List | `GET /system` | `system_records` | Rebind existing |
| O1 | `GET /system/{run_id}/snapshot` | `system_records` STARTUP | NEW |
| O2 | `GET /system/{run_id}/telemetry` | N/A | STUB |
| O3 | `GET /system/{run_id}/events` | `system_records` filtered | NEW |
| O4 | `GET /system/{run_id}/replay` | Time-window join | NEW |
| O5 | `GET /system/audit` | `system_records` attribution | NEW |

### 2.3 AUDIT Endpoints

| O-Level | Endpoint | Data Source | Implementation |
|---------|----------|-------------|----------------|
| List | `GET /audit` | `audit_ledger` | Rebind existing |
| O1 | `GET /audit/identity` | `audit_ledger` LOGIN/LOGOUT | NEW |
| O2 | `GET /audit/authorization` | `audit_ledger` ACCESS_DECISION | NEW |
| O3 | `GET /audit/access` | `audit_ledger` LOG_VIEW/EXPORT | NEW |
| O4 | `GET /audit/integrity` | `audit_ledger` + hash verify | NEW |
| O5 | `GET /audit/exports` | `log_exports` | NEW |

---

## Phase 3: Intent YAML & Capability Registry

### 3.1 Intent YAML Updates

**Files to update (15 total):**
```
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-LLM-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-LLM-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-LLM-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-LLM-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-LLM-O5.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-SYS-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-SYS-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-SYS-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-SYS-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-SYS-O5.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-AUD-O1.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-AUD-O2.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-AUD-O3.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-AUD-O4.yaml
design/l2_1/intents/AURORA_L2_INTENT_LOG-REC-AUD-O5.yaml
```

**Update Pattern:**
```yaml
# Before
capability:
  id: logs.llm_runs
  status: ASSUMED
  assumed_endpoint: /api/v1/runtime/traces  # WRONG

# After
capability:
  id: logs.llm_runs
  status: DECLARED
  endpoint: /api/v1/logs/llm-runs/{run_id}/envelope
  method: GET
```

### 3.2 Capability Registry Files

**Create 3 files:**
```
backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_logs.llm_runs.yaml
backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_logs.system_logs.yaml
backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_logs.audit.yaml
```

---

## Phase 4: SDSR Validation

### 4.1 Scenarios to Create

**Create 4 files:**
```
backend/scripts/sdsr/scenarios/SDSR-LOG-LLM-001.yaml
backend/scripts/sdsr/scenarios/SDSR-LOG-LLM-GOV-001.yaml
backend/scripts/sdsr/scenarios/SDSR-LOG-AUD-001.yaml
backend/scripts/sdsr/scenarios/SDSR-LOG-SYS-001.yaml
```

### 4.2 Post-SDSR Actions

1. Execute scenarios: `python inject_synthetic.py --scenario <yaml> --wait`
2. Apply observations: `python AURORA_L2_apply_sdsr_observations.py`
3. Re-run pipeline: `./scripts/tools/run_aurora_l2_pipeline.sh`
4. Verify capability status: DECLARED → OBSERVED

---

## Implementation Checklist

### Pre-Implementation (Phase 0)
- [x] Create `LOGS_DOMAIN_V2_CONTRACT.md`
- [x] Create `LOGS_DOMAIN_V2_IMPLEMENTATION_PLAN.md`
- [ ] Create migration for `log_exports` table
- [ ] Create migration for required indexes
- [ ] Create migration for `audit_ledger.correlation_id`
- [ ] Create `backend/app/models/log_exports.py`
- [ ] Update 15 Intent YAMLs with correct endpoints
- [ ] Create 3 capability registry files
- [ ] Create 4 SDSR scenario stubs

### Phase 1: Facade
- [ ] Create `backend/app/api/logs/` directory structure
- [ ] Create `models.py` with EvidenceMetadata + all response models
- [ ] Refactor `logs.py` to include sub-routers
- [ ] Create `llm_runs.py` handler
- [ ] Create `system_logs.py` handler
- [ ] Create `audit.py` handler
- [ ] Create `helpers.py` with metadata builder

### Phase 2: O-Levels
- [ ] Implement LLM_RUNS List (rebind)
- [ ] Implement LLM_RUNS O1 (envelope)
- [ ] Implement LLM_RUNS O2 (trace) - rebind
- [ ] Implement LLM_RUNS O3 (governance)
- [ ] Implement LLM_RUNS O4 (replay window)
- [ ] Implement LLM_RUNS O5 (export)
- [ ] Implement SYSTEM_LOGS List (rebind)
- [ ] Implement SYSTEM_LOGS O1 (snapshot)
- [ ] Implement SYSTEM_LOGS O2 (stub)
- [ ] Implement SYSTEM_LOGS O3 (events)
- [ ] Implement SYSTEM_LOGS O4 (replay)
- [ ] Implement SYSTEM_LOGS O5 (audit)
- [ ] Implement AUDIT List (rebind)
- [ ] Implement AUDIT O1-O5

### Phase 3: Registry
- [ ] Run `sync_from_intent_ledger.py` after YAML updates
- [ ] Verify projection updated
- [ ] Run AURORA L2 pipeline

### Phase 4: SDSR
- [ ] Execute SDSR-LOG-LLM-001
- [ ] Execute SDSR-LOG-LLM-GOV-001
- [ ] Execute SDSR-LOG-AUD-001
- [ ] Execute SDSR-LOG-SYS-001
- [ ] Apply observations
- [ ] Verify DECLARED → OBSERVED

### Post-Implementation
- [ ] Reclassify `traces.py` as SDK/Internal API
- [ ] Reclassify `guard_logs.py` as L2a Adapter
- [ ] Update `gateway_config.py` public_paths
- [ ] Update `RBAC_RULES.yaml` with new endpoints
- [ ] Update ENVIRONMENT_CONTRACT if needed

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| O4 replay query is slow | Medium | High | Pre-compute inflection_timestamp, add indexes |
| SYSTEM_LOGS O2 stays stub forever | Medium | Medium | Document as "future milestone", not "broken" |
| Export service complexity | Medium | Medium | Start with JSON-only, add PDF/ZIP later |
| Breaking existing list endpoints | Low | High | Keep `/logs/llm-runs` list alongside O-level routes |
| Metadata not populated consistently | Medium | High | Use helper function, enforce in code review |

---

## Success Criteria

1. ✅ All 15 panel endpoints return valid responses with `EvidenceMetadata`
2. ✅ All 3 capabilities move from DECLARED → OBSERVED
3. ✅ Intent YAMLs point to correct `/api/v1/logs/*` endpoints
4. ✅ `traces.py` and `guard_logs.py` reclassified (no domain authority)
5. ✅ `log_exports` table exists with append-only trigger
6. ✅ Lifecycle rules documented and acknowledged
7. ✅ All responses include correlation spine fields

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-19 | Initial creation | Claude + Human |
