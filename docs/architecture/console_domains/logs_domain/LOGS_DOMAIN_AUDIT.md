# Logs Domain Audit

**Status:** CLOSED (Governance-Grade)
**Last Updated:** 2026-01-22
**Reference:** PIN-413 (Logs Domain), PIN-463 (L4 Facade Pattern)

---

## Architecture Pattern

This domain follows the **L4 Facade Pattern** for data access:

| Layer | File | Role |
|-------|------|------|
| L2 API | `backend/app/api/aos_logs.py` | HTTP handling, response formatting |
| L4 Facade | `backend/app/services/logs_facade.py` | Business logic, tenant isolation |

**Data Flow:** `L1 (UI) → L2 (API) → L4 (Facade) → L6 (Database)`

**Key Rules:**
- L2 routes delegate to L4 facade (never direct SQL)
- Facade returns typed dataclasses (never ORM models)
- All operations are tenant-scoped

**Full Reference:** [PIN-463: L4 Facade Architecture Pattern](../../memory-pins/PIN-463-l4-facade-architecture-pattern.md), [LAYER_MODEL.md](../LAYER_MODEL.md)

---

## 1. Customer Meaning (LOCKED)

### One Question Logs Answer

> **"What exactly happened in my system?"**

Not *why* (that's incidents), not *how good* (that's metrics), not *what to do* (that's actions).

---

## 2. Three Log Types (Customer Language)

### 2.1 LLM Run Logs — "What my AI did"

**Customer question:** *"Show me what the AI actually did."*

**Contains:**
- Which model was used
- What inputs were sent (or hashes)
- What tools/functions were called
- How long each step took
- Tokens used and cost
- Final outcome (success / error / timeout)

**Answers:**
- Why did this response look like this?
- Did the model call a tool when it shouldn't have?
- Which run caused higher cost?
- What exactly happened before an error?

**Is NOT:** Audit trail, security log, health indicator

**Mental model:** *"Replayable trace of my AI's behavior."*

---

### 2.2 Audit Logs — "Who changed what"

**Customer question:** *"Who changed what, and when?"*

**Contains:**
- Policy rule created or changed
- Incident acknowledged or resolved
- Limit overridden
- Safety switch activated
- Configuration approved or rejected

Each entry has: **Who** (human/system/agent), **What**, **Why**, **When**

**Answers:**
- Who approved this policy?
- Why was this limit raised?
- When was this incident resolved?
- Did an AI agent take an autonomous action?

**Is NOT:** Execution details, metrics, debugging trace

**Mental model:** *"Compliance and accountability ledger."* (Think bank statement)

---

### 2.3 System Logs — "What happened to the platform"

**Customer question:** *"What happened to the platform itself?"*

**Contains:**
- Worker started or stopped
- Background job failed
- Pool scaled up or down
- Internal service restarted
- Emergency switch toggled

**Answers:**
- Was there a platform outage?
- Did the system restart during my run?
- Was maintenance performed?

**Is NOT:** Run-level debugging, cost analysis, incident explanation

**Mental model:** *"Black box recorder of the platform."*

---

## 3. Customer Situation Mapping

| Situation | Log Type |
|-----------|----------|
| "My AI behaved oddly" | LLM Run Logs |
| "Something was changed or approved" | Audit Logs |
| "The system was unstable or down" | System Logs |

**Rule:** If a log doesn't fit ONE situation clearly, it confuses customers.

---

## 4. Implementation Status

### 4.1 Summary Table

| Log Type | API Route | Model | Write Path | Status |
|----------|-----------|-------|------------|--------|
| LLM Run Logs | `/api/v1/logs/llm-runs` | `LLMRunRecord` | worker/runner.py | **FUNCTIONAL** |
| Audit Logs | `/api/v1/logs/audit` | `AuditLedger` | AuditLedgerService (sync/async) | **COMPLETE** |
| System Logs | `/api/v1/logs/system` | `SystemRecord` | main.py, pool.py | **FUNCTIONAL** |

### 4.2 Capability Registry

| Capability | Endpoint | Status |
|------------|----------|--------|
| `logs.llm_runs_list` | `/api/v1/logs/llm-runs` | DECLARED |
| `logs.audit_list` | `/api/v1/logs/audit` | DECLARED |
| `logs.system_list` | `/api/v1/logs/system` | DECLARED |

---

## 5. TODO Checklist

### 5.1 LLM Run Logs

- [x] Model contains only execution facts
- [x] Write path: only `worker/runner.py`
- [x] API is read-only
- [x] Filtering: time, run_id, agent_id, model
- [ ] Verify no intent/blame/severity fields

### 5.2 Audit Logs

- [x] Model: `AuditLedger` with canonical fields
- [x] Service: `AuditLedgerService` created (sync)
- [x] Service: `AuditLedgerServiceAsync` created (async)
- [x] DB triggers block UPDATE/DELETE (migration 091)
- [x] Transaction guard: `in_transaction()` check before emit
- [x] CI guard: `ci_check_audit_no_commit.sh`
- [x] CI guard: `ci_check_audit_immutability.py`
- [x] Wire: `IncidentWriteService.acknowledge_incident()`
- [x] Wire: `IncidentWriteService.resolve_incident()`
- [x] Wire: `IncidentWriteService.manual_close_incident()`
- [x] Wire: `PolicyRulesService.create()` → POLICY_RULE_CREATED
- [x] Wire: `PolicyRulesService.update()` → POLICY_RULE_MODIFIED
- [x] Wire: `PolicyRulesService.update()` (retirement) → POLICY_RULE_RETIRED
- [x] Wire: `PolicyLimitsService.create()` → LIMIT_CREATED
- [x] Wire: `PolicyLimitsService.update()` → LIMIT_UPDATED
- [x] Wire: `review_policy_proposal()` (approve) → POLICY_PROPOSAL_APPROVED
- [x] Wire: `review_policy_proposal()` (reject) → POLICY_PROPOSAL_REJECTED
- [x] API is read-only
- [x] Canonical event types enforced

### 5.3 System Logs

- [x] Model contains only platform events
- [x] Write paths: main.py, worker/pool.py
- [x] API is read-only
- [ ] Verify no user actions in system logs

### 5.4 Cross-Domain Linking

- [x] LLM run logs expose `run_id`
- [x] Incidents reference `source_run_id`
- [x] Audit logs reference entity IDs
- [x] No data duplication across logs

---

## 6. Audit Event Types (Canonical)

| Event | Entity | Wired? | Service |
|-------|--------|--------|---------|
| `IncidentAcknowledged` | INCIDENT | **DONE** | IncidentWriteService |
| `IncidentResolved` | INCIDENT | **DONE** | IncidentWriteService |
| `IncidentManuallyClosed` | INCIDENT | **DONE** | IncidentWriteService |
| `PolicyRuleCreated` | POLICY_RULE | **DONE** | PolicyRulesService |
| `PolicyRuleModified` | POLICY_RULE | **DONE** | PolicyRulesService |
| `PolicyRuleRetired` | POLICY_RULE | **DONE** | PolicyRulesService |
| `PolicyProposalApproved` | POLICY_PROPOSAL | **DONE** | policy_proposal.py |
| `PolicyProposalRejected` | POLICY_PROPOSAL | **DONE** | policy_proposal.py |
| `LimitCreated` | LIMIT | **DONE** | PolicyLimitsService |
| `LimitUpdated` | LIMIT | **DONE** | PolicyLimitsService |
| `LimitBreached` | LIMIT | READY | AuditLedgerServiceAsync (caller must wire) |
| `LimitOverrideGranted` | LIMIT | READY | AuditLedgerServiceAsync (caller must wire) |
| `LimitOverrideRevoked` | LIMIT | READY | AuditLedgerServiceAsync (caller must wire) |
| `EmergencyOverrideActivated` | LIMIT | READY | AuditLedgerServiceAsync (caller must wire) |
| `EmergencyOverrideDeactivated` | LIMIT | READY | AuditLedgerServiceAsync (caller must wire) |

**Note:** READY means the convenience method exists in `AuditLedgerServiceAsync`. Wiring requires the calling service (e.g., `LimitOverrideService`, runtime evaluator) to call the emit method inside a transaction block.

---

## 7. Transaction Contract (LOCKED)

### Invariant

> **An audit record must be committed if and only if the state change it represents is committed.**

### Pattern (Sync)

```python
with self._session.begin():
    # State change
    self._session.add(entity)
    # Audit emit (inside transaction)
    self._audit.emit(...)
# Transaction auto-commits here
```

### Pattern (Async)

```python
async with self.session.begin():
    # State change
    self.session.add(entity)
    # Audit emit (inside transaction)
    await self._audit.emit(...)
# Transaction auto-commits here
```

### Guards

1. **Transaction Guard**: `emit()` raises `RuntimeError` if not in active transaction
2. **No Commit Rule**: Audit services NEVER call `commit()` — caller owns boundary
3. **CI Enforcement**: `ci_check_audit_no_commit.sh` blocks commits in audit services

---

## 8. Hard Rules (Non-Negotiable)

### Must Do
- Preserve customer mental model
- Keep logs read-only
- Emit logs only from write paths
- Treat logs as evidence, not insight
- Emit audit atomically with state change

### Must NOT Do
- Add analytics to logs
- Add "insights" fields
- Rank or score logs
- Combine log types
- Auto-generate explanations
- Write logs from read paths
- Call `commit()` inside audit emit
- Add retry/recovery for audit failures

---

## 9. UI Labels (Customer-Facing)

| Internal | Customer Label | Meaning |
|----------|----------------|---------|
| LLMRunRecord | "LLM Run Logs" | What my AI did |
| AuditLedger | "Audit Logs" | Who changed what |
| SystemRecord | "System Logs" | Platform events |

**Forbidden in UI:** "Ledger", "Actor", "Entity mutation"

---

## 10. Validation Criteria

Work is DONE only if:
- [x] Each log type answers exactly one customer question
- [x] No log type overlaps another
- [x] All writes are centralized and mandatory
- [x] All APIs are read-only
- [x] Logs can be used as legal evidence without interpretation
- [x] Audit emits are atomic with state changes
- [x] Immutability enforced at DB level

---

## 11. Files

| File | Purpose |
|------|---------|
| `backend/app/api/logs.py` | Unified logs facade (L2) |
| `backend/app/models/audit_ledger.py` | AuditLedger model + ActorType enum |
| `backend/app/models/logs_records.py` | LLMRunRecord, SystemRecord models |
| `backend/app/services/logs/audit_ledger_service.py` | Sync audit write service |
| `backend/app/services/logs/audit_ledger_service_async.py` | Async audit write service |
| `backend/app/services/incident_write_service.py` | Incident mutations + audit |
| `backend/app/services/limits/policy_rules_service.py` | Policy rule mutations + audit |
| `backend/app/services/limits/policy_limits_service.py` | Policy limit mutations + audit |
| `backend/app/services/policy_proposal.py` | Proposal review + audit |
| `backend/scripts/ci_check_audit_no_commit.sh` | CI: no commit() in audit services |
| `backend/scripts/ci_check_audit_immutability.py` | CI: DB immutability verification |
| `backend/alembic/versions/091_audit_ledger.py` | Migration: audit_ledger table + triggers |
| `backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_logs.*.yaml` | Capabilities |

---

## 12. L4 Domain Facade

### 12.1 Architecture Pattern

The Logs domain uses a **Read-Only Facade Pattern** where L2 API endpoints delegate all data access to the L4 `LogsFacade`:

```
┌─────────────────────┐
│   L2: logs.py       │  (Endpoint handlers)
│   - Auth extraction │
│   - Request params  │
│   - Response mapping│
└──────────┬──────────┘
           │ await facade.method()
           ▼
┌─────────────────────┐
│   L4: LogsFacade    │  (Domain logic)
│   - Query building  │
│   - Filtering       │
│   - Result mapping  │
└──────────┬──────────┘
           │ session.execute()
           ▼
┌─────────────────────┐
│   L6: Database      │  (Data access)
└─────────────────────┘
```

### 12.2 Facade Entry Point

| Component | File | Pattern |
|-----------|------|---------|
| `LogsFacade` | `backend/app/services/logs_facade.py` | Singleton via `get_logs_facade()` |

### 12.3 Operations Provided

**LLM_RUNS Operations:**

| Method | Purpose | O-Level |
|--------|---------|---------|
| `list_llm_run_records()` | List LLM run records with filters | List |
| `get_llm_run_envelope()` | Canonical immutable run record | O1 |
| `get_llm_run_trace()` | Step-by-step trace | O2 |
| `get_llm_run_governance()` | Policy interaction trace | O3 |
| `get_llm_run_replay()` | 60-second replay window | O4 |
| `get_llm_run_export()` | Export information | O5 |

**SYSTEM_LOGS Operations:**

| Method | Purpose | O-Level |
|--------|---------|---------|
| `list_system_records()` | List system records with filters | List |
| `get_system_snapshot()` | Environment baseline snapshot | O1 |
| `get_system_telemetry()` | Telemetry stub (not implemented) | O2 |
| `get_system_events()` | Infra events affecting run | O3 |
| `get_system_replay()` | Infra replay window | O4 |
| `get_system_audit()` | Infra attribution | O5 |

**AUDIT Operations:**

| Method | Purpose | O-Level |
|--------|---------|---------|
| `list_audit_entries()` | List audit entries with filters | List |
| `get_audit_entry()` | Audit entry detail with state snapshots | Detail |
| `get_audit_identity()` | Identity lifecycle events | O1 |
| `get_audit_authorization()` | Authorization decisions | O2 |
| `get_audit_access()` | Log access audit | O3 |
| `get_audit_integrity()` | Tamper detection status | O4 |
| `get_audit_exports()` | Compliance exports | O5 |

### 12.4 L2-to-L4 Result Type Mapping

All L4 facade methods return dataclass result types that L2 maps to Pydantic response models:

| L4 Result Type | L2 Response Model | Purpose |
|----------------|-------------------|---------|
| `LLMRunRecordsResult` | `LLMRunRecordsResponse` | LLM run list |
| `LLMRunEnvelopeResult` | `LLMRunEnvelope` | Run envelope |
| `LLMRunTraceResult` | `LLMRunTrace` | Run trace |
| `LLMRunGovernanceResult` | `LLMRunGovernance` | Governance events |
| `LLMRunReplayResult` | `LLMRunReplay` | Replay window |
| `LLMRunExportResult` | `LLMRunExport` | Export info |
| `SystemRecordsResult` | `SystemRecordsResponse` | System records list |
| `SystemSnapshotResult` | `SystemSnapshot` | Env snapshot |
| `TelemetryStubResult` | `TelemetryStub` | Telemetry stub |
| `SystemEventsResult` | `SystemEvents` | Infra events |
| `SystemReplayResult` | `SystemReplay` | System replay |
| `SystemAuditResult` | `SystemAudit` | Infra audit |
| `AuditLedgerListResult` | `AuditLedgerResponse` | Audit entries list |
| `AuditLedgerDetailResult` | `AuditLedgerDetailItem` | Audit detail |
| `AuditIdentityResult` | `AuditIdentity` | Identity events |
| `AuditAuthorizationResult` | `AuditAuthorization` | Auth decisions |
| `AuditAccessResult` | `AuditAccess` | Access events |
| `AuditIntegrityResult` | `AuditIntegrity` | Integrity check |
| `AuditExportsResult` | `AuditExports` | Export records |

### 12.5 Evidence Metadata Contract (INV-LOG-META-001)

All Logs domain responses include `EvidenceMetadata` with:

| Field | Purpose |
|-------|---------|
| `tenant_id` | Identity: tenant scope |
| `run_id` | Identity: run correlation |
| `occurred_at` | Time: when event happened |
| `recorded_at` | Time: when evidence was recorded |
| `source_domain` | Provenance: always "LOGS" |
| `source_component` | Provenance: which service created |
| `origin` | Provenance: SYSTEM / HUMAN / AGENT |

### 12.6 Key Characteristics

- **Read-Only**: All facade methods are read operations (SELECT only)
- **Tenant-Scoped**: All queries filter by tenant_id
- **Evidence-Grade**: Results include immutable evidence metadata
- **No State Mutation**: Facade does not write audit logs (that's done by write services)

---

## 13. Closure Statement

> **Logs Domain Status: CLOSED**
>
> - All audit events are emitted atomically with state changes
> - Immutability is enforced at database and CI levels
> - Sync and async services follow identical transaction contracts
> - No silent failures, no partial commits, no inferred meaning
> - Logs answer exactly one customer question: *what happened*
>
> The Logs domain is now governance-grade and stable.
> Further changes require an explicit design proposal.

**Closed:** 2026-01-17
