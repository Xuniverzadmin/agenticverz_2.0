# LOGS Domain V2 Architecture

**Status:** LOCKED
**Version:** 2.0
**Effective:** 2026-01-19
**Contract:** `docs/contracts/LOGS_DOMAIN_V2_CONTRACT.md`
**Implementation Plan:** `docs/contracts/LOGS_DOMAIN_V2_IMPLEMENTATION_PLAN.md`

---

## Executive Summary

The LOGS domain provides audit-grade evidence for all system activity. Version 2 establishes a unified facade at `/api/v1/logs/*` with three topics (LLM_RUNS, SYSTEM_LOGS, AUDIT) and five O-levels per topic.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LOGS DOMAIN V2 FACADE                    │
│                      /api/v1/logs/*                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────┐      │
│  │  LLM_RUNS   │   │ SYSTEM_LOGS  │   │    AUDIT    │      │
│  │  (Topic 1)  │   │  (Topic 2)   │   │  (Topic 3)  │      │
│  └──────┬──────┘   └──────┬───────┘   └──────┬──────┘      │
│         │                 │                  │              │
│         ▼                 ▼                  ▼              │
│  ┌─────────────────────────────────────────────────┐       │
│  │              O-LEVEL STRUCTURE                   │       │
│  │  O1: Envelope/Snapshot (canonical record)       │       │
│  │  O2: Trace/Telemetry (step-by-step)            │       │
│  │  O3: Governance/Events (policy interaction)     │       │
│  │  O4: Replay/Window (60-second context)          │       │
│  │  O5: Export/Bundle (audit-grade evidence)       │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Endpoint Map

### LLM_RUNS (15 panels → 6 endpoints)

| O-Level | Endpoint | Purpose |
|---------|----------|---------|
| List | `GET /llm-runs` | List runs |
| O1 | `GET /llm-runs/{run_id}/envelope` | Canonical immutable record |
| O2 | `GET /llm-runs/{run_id}/trace` | Step-by-step execution |
| O3 | `GET /llm-runs/{run_id}/governance` | Policy interaction trace |
| O4 | `GET /llm-runs/{run_id}/replay` | 60-second replay window |
| O5 | `GET /llm-runs/{run_id}/export` | Audit-grade evidence bundle |

### SYSTEM_LOGS (15 panels → 6 endpoints)

| O-Level | Endpoint | Purpose |
|---------|----------|---------|
| List | `GET /system` | List system events |
| O1 | `GET /system/{run_id}/snapshot` | Environment baseline |
| O2 | `GET /system/{run_id}/telemetry` | Infrastructure telemetry (STUB) |
| O3 | `GET /system/{run_id}/events` | Infra events affecting run |
| O4 | `GET /system/{run_id}/replay` | Infrastructure replay window |
| O5 | `GET /system/audit` | Infrastructure attribution |

### AUDIT (15 panels → 6 endpoints)

| O-Level | Endpoint | Purpose |
|---------|----------|---------|
| List | `GET /audit` | List audit entries |
| O1 | `GET /audit/identity` | Identity lifecycle (login/logout) |
| O2 | `GET /audit/authorization` | Authorization decisions |
| O3 | `GET /audit/access` | Log access audit trail |
| O4 | `GET /audit/integrity` | Tamper detection records |
| O5 | `GET /audit/exports` | Compliance export records |

---

## Data Model

### Evidence Metadata Contract (INV-LOG-META-001)

All LOGS responses MUST include `EvidenceMetadata`:

```python
class EvidenceMetadata(BaseModel):
    # Identity
    tenant_id: str
    run_id: Optional[str]

    # Actor attribution (precedence: human > agent > system)
    human_actor_id: Optional[str]
    agent_id: Optional[str]
    system_id: Optional[str]

    # Time
    occurred_at: datetime
    recorded_at: datetime
    timezone: str = "UTC"

    # Correlation spine
    trace_id: Optional[str]
    policy_ids: List[str]
    incident_ids: List[str]
    export_id: Optional[str]
    correlation_id: Optional[str]

    # Source & provenance
    source_domain: Literal["ACTIVITY", "POLICY", "INCIDENTS", "LOGS", "SYSTEM"]
    source_component: str
    origin: Literal["SYSTEM", "HUMAN", "AGENT", "MIGRATION", "REPLAY"]

    # Integrity
    checksum: Optional[str]
    immutable: bool = True
```

### Database Tables

| Table | Purpose | Immutable |
|-------|---------|-----------|
| `llm_run_records` | LLM execution records | Yes (DB trigger) |
| `system_records` | System event records | Yes |
| `audit_ledger` | Audit trail entries | Yes (DB trigger) |
| `log_exports` | Export bundle metadata | Yes (DB trigger) |
| `aos_traces` | Execution traces | Yes |
| `aos_trace_steps` | Trace steps | Yes |

---

## Security Model

### RBAC Rules

| Environment | Access Tier | Permissions |
|-------------|-------------|-------------|
| Preflight | PUBLIC (temporary) | Read-only, expires 2026-03-01 |
| Production | SESSION | `logs.read` required |

### Security Constraints

1. **No Mutation Routes**: All 19 endpoints are GET-only
2. **Tenant Scoping**: All queries filtered by `tenant_id` from auth context
3. **Immutable Records**: DB triggers prevent UPDATE/DELETE on log tables
4. **Export URLs**: Metadata only; signed URL download to be implemented

### Gateway Configuration

```python
# Preflight SDSR validation
"/api/v1/logs/"  # Added to public_paths
```

---

## L4 Domain Facade

**File:** `backend/app/services/logs_facade.py`
**Getter:** `get_logs_facade()` (singleton)

The Logs Facade is the single entry point for all logs business logic. L2 API routes
must call facade methods rather than implementing inline SQL queries.

**Pattern:**
```python
from app.services.logs_facade import get_logs_facade

facade = get_logs_facade()
result = await facade.list_llm_runs(session, tenant_id, ...)
```

**Operations Provided:**
- `list_llm_runs()` - LLM runs list
- `get_llm_run_envelope()` - Run envelope (O1)
- `get_llm_run_trace()` - Run trace (O2)
- `get_llm_run_governance()` - Policy interaction (O3)
- `get_llm_run_replay()` - 60-second replay (O4)
- `get_llm_run_export()` - Audit export (O5)
- `list_system_records()` - System events list
- `get_system_snapshot()` - Environment baseline (O1)
- `list_audit_records()` - Audit entries list
- `get_audit_identity()` - Identity lifecycle (O1)
- `get_audit_authorization()` - Authorization decisions (O2)
- `get_audit_access()` - Access audit trail (O3)
- `get_audit_integrity()` - Tamper detection (O4)
- `get_audit_exports()` - Compliance exports (O5)

**Facade Rules:**
- L2 routes call facade methods, never direct SQL
- All responses include EvidenceMetadata (INV-LOG-META-001)
- Facade handles tenant isolation internally
- Read-only operations only (no mutations)

---

## File Inventory

### Canonical Files

| File | Layer | Role |
|------|-------|------|
| `backend/app/api/logs.py` | L2 | Unified LOGS API routes (19 endpoints) |
| `backend/app/services/logs_facade.py` | L4 | LOGS domain facade |
| `backend/app/models/log_exports.py` | L6 | LogExport model |
| `backend/app/models/logs_records.py` | L6 | LLMRunRecord, SystemRecord models |
| `backend/app/models/audit_ledger.py` | L6 | AuditLedger model |

### Deprecated/Auxiliary Files

| File | Layer | Role |
|------|-------|------|
| `backend/app/api/traces.py` | L2a | SDK/Internal API (NOT domain authority) |
| `backend/app/api/guard_logs.py` | L2a | Console adapter (DEPRECATED) |

### Migration

| File | Purpose |
|------|---------|
| `backend/alembic/versions/109_logs_domain_v2.py` | log_exports table, indexes, triggers |

---

## Capability Registry

| Capability ID | Status | Panels |
|---------------|--------|--------|
| `logs.llm_runs` | OBSERVED | LOG-REC-LLM-O1 through O5 |
| `logs.system_logs` | DECLARED | LOG-REC-SYS-O1 through O5 |
| `logs.audit` | OBSERVED | LOG-REC-AUD-O1 through O5 |

---

## Maintenance Rules

### DO NOT

- Add POST/PUT/DELETE endpoints to `/api/v1/logs/*`
- Bypass tenant scoping
- Remove immutability triggers
- Edit `traces.py` as if it were the LOGS facade
- Mix LOGS domain with other domains

### DO

- Use `/api/v1/logs/*` for all log viewing
- Use `traces.py` only for SDK trace ingestion
- Include `EvidenceMetadata` in all responses
- Maintain correlation_id for cross-system tracing
- Update capability registry after SDSR validation

---

## References

- Contract: `docs/contracts/LOGS_DOMAIN_V2_CONTRACT.md`
- Implementation Plan: `docs/contracts/LOGS_DOMAIN_V2_IMPLEMENTATION_PLAN.md`
- Intent Ledger: `design/l2_1/INTENT_LEDGER.md` (lines 4016-4322)
- PIN: PIN-449 (LOGS Domain V2 Implementation)
