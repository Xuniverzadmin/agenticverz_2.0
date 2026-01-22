# HOC Logs Domain Analysis v1.0

**Domain:** `customer/logs`
**Date:** 2026-01-22
**Total Files:** 20 Python files
**Status:** CLEAN (0 AUDIENCE violations)
**Topics:** audit, llm_runs, system

---

## EXECUTIVE JUDGMENT

| Aspect | Assessment |
|--------|------------|
| **Domain Health** | Strong and internally consistent |
| **Design Intent** | Clear — Logs is not "logging", it is **evidence, audit, and determinism** |
| **Primary Risk** | Scale and gravity, not correctness |
| **Primary Opportunity** | Clarify what must never leak out of Logs |

> This is one of the few domains that already behaves like a **compliance subsystem**, not an application feature.

---

## 1. FILE STRUCTURE

```
logs/
├── __init__.py                          # Domain root (12 LOC)
│   # Layer: L4 — Domain Services
│   # AUDIENCE: CUSTOMER
│   # Purpose: Logs domain - Evidence and audit
│
├── facades/
│   ├── __init__.py                      # Facade exports (11 LOC)
│   ├── logs_facade.py                   # Main unified facade (1587 LOC) — L4 Domain Engine
│   ├── evidence_facade.py               # Evidence chain facade (562 LOC) — L4 Domain Engine
│   └── trace_facade.py                  # Trace domain facade (289 LOC) — L4 Domain Engine
│
├── engines/
│   ├── __init__.py                      # Engine exports (11 LOC)
│   ├── store.py                         # AuditStore for RAC (447 LOC) — L4 Domain Engine
│   ├── durability.py                    # RAC durability enforcement (320 LOC) — L4 Domain Engine
│   ├── reconciler.py                    # Audit reconciler (316 LOC) — L4 Domain Engine
│   ├── certificate.py                   # Cryptographic certificates (375 LOC) — L3 Boundary Adapter
│   ├── evidence_report.py               # Legal-grade PDF evidence (1152 LOC) — L3 Boundary Adapter
│   ├── export_bundle_service.py         # Export bundle generation (410 LOC) — L3 Boundary Adapter
│   ├── logs_read_service.py             # Log read operations (207 LOC) — L4 Domain Engine
│   ├── pdf_renderer.py                  # PDF renderer service (680 LOC) — L3 Boundary Adapter
│   ├── replay_determinism.py            # Replay determinism (502 LOC) — (no header, implicit L4)
│   ├── audit_evidence.py                # MCP audit events (664 LOC) — L4 Domain Engines
│   └── completeness_checker.py          # Evidence completeness (513 LOC) — L4 Domain Engines
│
├── schemas/
│   └── models.py                        # RAC models (381 LOC) — L4 Domain Engine
│
└── drivers/
    └── __init__.py                      # Empty (reserved for L3 adapters)
```

---

## 2. FACADES ANALYSIS

### 2.1 logs_facade.py (1587 LOC) — MAIN UNIFIED FACADE

**Header:**
- Layer: L4 — Domain Engine
- AUDIENCE: CUSTOMER
- Product: ai-console

**Purpose:** Unified facade for all Logs domain operations (LLM_RUNS, SYSTEM_LOGS, AUDIT).

**Imports:**
```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
```

**Key Classes:**

| Class | Purpose |
|-------|---------|
| `LogsFacade` | Main facade class with all log operations |
| `EvidenceMetadataResult` | INV-LOG-META-001 compliant metadata wrapper |

**35+ Result Dataclasses:**
```python
# LLM Runs Topic
LLMRunSummaryResult, LLMRunListResult, LLMRunEnvelopeResult
LLMRunTraceResult, LLMRunGovernanceResult, LLMRunReplayResult
LLMRunExportResult

# System Logs Topic
SystemRecordResult, SystemRecordListResult, SystemSnapshotResult
SystemEventsResult, SystemReplayResult, SystemAuditResult

# Audit Topic
AuditEntrySummaryResult, AuditEntryListResult, AuditEntryDetailResult
AuditIdentityResult, AuditAuthorizationResult, AuditAccessResult
AuditIntegrityResult, AuditExportsResult

# Error
LogsErrorResult
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `list_llm_run_records()` | List LLM run summaries with pagination |
| `get_llm_run_envelope()` | Get complete envelope for a run |
| `get_llm_run_trace()` | Get trace details for a run |
| `get_llm_run_governance()` | Get governance/policy decisions for a run |
| `get_llm_run_replay()` | Get replay status and determinism info |
| `get_llm_run_export()` | Export run data with evidence bundle |
| `list_system_records()` | List system log records |
| `get_system_snapshot()` | Get system state snapshot |
| `get_system_events()` | Get system events for time range |
| `get_system_replay()` | Replay system state at point-in-time |
| `get_system_audit()` | Get system-level audit entries |
| `list_audit_entries()` | List audit trail entries |
| `get_audit_entry()` | Get specific audit entry |
| `get_audit_identity()` | Get identity audit (who did what) |
| `get_audit_authorization()` | Get authorization audit |
| `get_audit_access()` | Get access patterns audit |
| `get_audit_integrity()` | Get data integrity audit |
| `get_audit_exports()` | List audit exports |

**Exports:**
```python
__all__ = ["LogsFacade", "get_logs_facade", "EvidenceMetadataResult", ...]
```

---

### 2.2 evidence_facade.py (562 LOC)

**Header:**
- Layer: L4 — Domain Engine
- Product: system-wide

**Purpose:** Evidence chain operations for compliance exports.

**Key Classes:**

| Class | Purpose |
|-------|---------|
| `EvidenceLink` | Single piece of evidence in a chain |
| `EvidenceChain` | Collection of linked evidence |
| `VerificationResult` | Result of chain integrity verification |
| `EvidenceExport` | Exported evidence bundle |
| `EvidenceFacade` | Main facade for evidence operations |

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `list_chains()` | List evidence chains for tenant |
| `get_chain()` | Get specific chain with all links |
| `create_chain()` | Create new evidence chain |
| `add_evidence()` | Add evidence link to chain |
| `verify_chain()` | Verify chain integrity (hash chain) |
| `create_export()` | Create compliance export from chain |
| `get_export()` | Retrieve existing export |
| `list_exports()` | List tenant exports |

---

### 2.3 trace_facade.py (289 LOC)

**Header:**
- Layer: L4 — Domain Engine
- Product: system-wide

**Purpose:** Trace operations with Runtime Audit Contract (RAC) acknowledgment emission.

**Key Class:** `TraceFacade`

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `start_trace()` | Start a new trace, emit RAC ack |
| `complete_trace()` | Complete a trace, emit RAC ack |
| `add_step()` | Add step to trace |
| `_emit_ack()` | Internal RAC acknowledgment emission |

**Environment Flag:** `RAC_ENABLED` controls ack emission.

---

## 3. ENGINES ANALYSIS

### 3.1 store.py (447 LOC) — AUDIT STORE

**Header:**
- Layer: L4 — Domain Engine
- Product: system-wide
- Reference: PIN-454 (Cross-Domain Orchestration Audit)

**Purpose:** Audit store for expectations and acknowledgments (RAC backend).

**Key Enum:**
```python
class StoreDurabilityMode(str, Enum):
    MEMORY = "MEMORY"    # In-memory only (loses data on restart)
    REDIS = "REDIS"      # Redis-backed (durable)
```

**Key Class:** `AuditStore`

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `add_expectations()` | Add expectations for a run |
| `get_expectations()` | Get expectations for a run |
| `update_expectation_status()` | Update expectation status |
| `add_ack()` | Add acknowledgment |
| `get_acks()` | Get acks for a run |
| `clear_run()` | Clear all data for a run |
| `get_pending_run_ids()` | Get runs with pending expectations |

**Exports:**
```python
__all__ = ["AuditStore", "StoreDurabilityMode", "get_audit_store"]
```

---

### 3.2 durability.py (320 LOC) — RAC DURABILITY

**Header:**
- Layer: L4 — Domain Engine
- Reference: GAP-050 (RAC Durability Enforcement)

**Purpose:** Enforce RAC durability before acknowledgment. When enabled, acks must be persisted to durable storage (Redis) before being accepted.

**Key Enum:**
```python
class DurabilityCheckResult(str, Enum):
    DURABLE = "durable"
    NOT_DURABLE = "not_durable"
    ENFORCEMENT_DISABLED = "enforcement_disabled"
    UNKNOWN = "unknown"
```

**Key Classes:**

| Class | Purpose |
|-------|---------|
| `RACDurabilityEnforcementError` | Raised when durability fails |
| `DurabilityCheckResponse` | Response from durability check |
| `RACDurabilityChecker` | Main checker class |

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `check()` | Check durability status |
| `ensure_durable()` | Ensure durable or raise error |
| `should_allow_operation()` | Check if operation should proceed |

**Exports:**
```python
__all__ = [
    "RACDurabilityEnforcementError", "RACDurabilityChecker",
    "check_rac_durability", "ensure_rac_durability"
]
```

---

### 3.3 reconciler.py (316 LOC) — AUDIT RECONCILER

**Header:**
- Layer: L4 — Domain Engine
- Reference: PIN-454 (Cross-Domain Orchestration Audit)

**Purpose:** Four-way validation of expectations vs acknowledgments:
1. `expected − acked` → missing (audit alert)
2. `acked − expected` → drift (unexpected action)
3. Missing finalization → stale run (liveness violation)
4. Expectations without deadline → invalid contract

**Key Class:** `AuditReconciler`

**Prometheus Metrics:**
```python
RECONCILIATION_TOTAL = Counter("rac_reconciliation_total", ...)
MISSING_ACTIONS_TOTAL = Counter("rac_missing_actions_total", ...)
DRIFT_ACTIONS_TOTAL = Counter("rac_drift_actions_total", ...)
STALE_RUNS_TOTAL = Counter("rac_stale_runs_total", ...)
RECONCILIATION_DURATION = Histogram("rac_reconciliation_duration_seconds", ...)
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `reconcile()` | Reconcile expectations vs acks for a run |
| `check_deadline_violations()` | Find expectations past deadline |
| `get_run_audit_summary()` | Get audit state summary for debugging |

**Exports:**
```python
__all__ = ["AuditReconciler", "get_audit_reconciler"]
```

---

### 3.4 certificate.py (375 LOC) — CRYPTOGRAPHIC CERTIFICATES

**Header:**
- Layer: L3 — Boundary Adapter (Console → Platform)
- Product: AI Console
- Reference: PIN-240

**Purpose:** Create HMAC-signed certificates proving deterministic replay and policy evaluation.

**Key Enums:**
```python
class CertificateType(str, Enum):
    REPLAY_PROOF = "replay_proof"
    POLICY_AUDIT = "policy_audit"
    INCIDENT_EXPORT = "incident_export"
```

**Key Classes:**

| Class | Purpose |
|-------|---------|
| `CertificatePayload` | Signed payload content |
| `Certificate` | Complete signed certificate |
| `CertificateService` | Create/verify certificates |

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `create_replay_certificate()` | Create certificate for replay validation |
| `create_policy_audit_certificate()` | Create certificate for policy audit |
| `verify_certificate()` | Verify signature and expiry |
| `export_certificate()` | Export in json/pem/compact format |

**Exports:**
```python
__all__ = ["CertificateService", "Certificate", "CertificatePayload", "CertificateType"]
```

---

### 3.5 evidence_report.py (1152 LOC) — LEGAL-GRADE PDF EXPORT

**Header:**
- Layer: L3 — Boundary Adapter (Console → Platform)
- Product: AI Console
- Reference: PIN-240

**Purpose:** Generate deterministic, verifiable PDF evidence reports for AI incidents. Designed to survive legal review, audit, and hostile questioning.

**Key Dataclasses:**

| Class | Purpose |
|-------|---------|
| `CertificateEvidence` | M23 certificate data for crypto proof |
| `IncidentEvidence` | All evidence data for an incident |

**Key Class:** `EvidenceReportGenerator`

**PDF Sections Generated:**
1. Incident Snapshot (1-page executive summary)
2. Cover Page
3. Executive Summary
4. Factual Reconstruction (Evidence)
5. Policy Evaluation Record
6. Decision Timeline (Deterministic Trace)
7. Deterministic Replay Verification
8. Cryptographic Certificate (M23)
9. Counterfactual Prevention Proof
10. Remediation & Controls
11. Legal Attestation

**Key Function:**
```python
def generate_evidence_report(...) -> bytes:
    """Convenience function to generate an evidence report PDF."""
```

---

### 3.6 export_bundle_service.py (410 LOC)

**Header:**
- Layer: L3 — Boundary Adapter (Console → Platform)
- Reference: GAP-004, GAP-005, GAP-008

**Purpose:** Generate structured export bundles from incidents, runs, and traces for evidence export, SOC2 compliance, and executive debriefs.

**Key Class:** `ExportBundleService`

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `create_evidence_bundle()` | Create evidence bundle from incident |
| `create_soc2_bundle()` | Create SOC2-compliant bundle with controls |
| `create_executive_debrief()` | Create non-technical executive summary |

**Exports:**
```python
__all__ = ["ExportBundleService", "get_export_bundle_service"]
```

---

### 3.7 logs_read_service.py (207 LOC)

**Header:**
- Layer: L4 — Domain Engine
- Reference: PIN-281 (L3 Adapter Closure - PHASE 1)

**Purpose:** L4 service for logs/trace READ operations. Sits between L3 (CustomerLogsAdapter) and L6 (PostgresTraceStore).

**Key Class:** `LogsReadService`

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `search_traces()` | Search traces with filters |
| `get_trace()` | Get single trace with tenant isolation |
| `get_trace_count()` | Get total trace count |
| `get_trace_by_root_hash()` | Get trace by deterministic hash |
| `list_traces()` | List traces with pagination |

**Exports:**
```python
__all__ = ["LogsReadService", "get_logs_read_service"]
```

---

### 3.8 pdf_renderer.py (680 LOC)

**Header:**
- Layer: L3 — Boundary Adapter (Console → Platform)
- Reference: GAP-004, GAP-005

**Purpose:** Render export bundles to PDF format for compliance exports.

**Key Class:** `PDFRenderer`

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `render_evidence_pdf()` | Render EvidenceBundle to PDF |
| `render_soc2_pdf()` | Render SOC2Bundle with attestations |
| `render_executive_debrief_pdf()` | Render ExecutiveDebriefBundle |

**Exports:**
```python
__all__ = ["PDFRenderer", "get_pdf_renderer"]
```

---

### 3.9 replay_determinism.py (502 LOC)

**Header:** (No explicit layer header)
- Product: system-wide (implicit)

**Purpose:** Define and enforce determinism semantics for replay validation.

**Determinism Levels:**
```python
class DeterminismLevel(str, Enum):
    STRICT = "strict"    # Byte-for-byte match
    LOGICAL = "logical"  # Policy decision equivalence
    SEMANTIC = "semantic" # Meaning-equivalent match
```

**Key Classes:**

| Class | Purpose |
|-------|---------|
| `ModelVersion` | Track model version for a call |
| `PolicyDecision` | Record of policy enforcement decision |
| `ReplayMatch` | Enum for match results |
| `ReplayResult` | Complete replay validation result |
| `CallRecord` | Call record for replay validation |
| `ReplayValidator` | Main validator class |
| `ReplayContextBuilder` | Build replay context from API calls |

**Exports:**
```python
__all__ = [
    "DeterminismLevel", "ModelVersion", "PolicyDecision", "ReplayMatch",
    "ReplayResult", "CallRecord", "ReplayValidator", "ReplayContextBuilder"
]
```

---

### 3.10 audit_evidence.py (664 LOC) — MCP AUDIT EVENTS

**Header:**
- Layer: L4 — Domain Engines
- Reference: GAP-143

**Purpose:** Emit compliance-grade audit events for MCP tool calls with tamper-evident integrity hashes.

**Key Enum:**
```python
class MCPAuditEventType(str, Enum):
    TOOL_INVOCATION_REQUESTED = "tool_invocation_requested"
    TOOL_INVOCATION_ALLOWED = "tool_invocation_allowed"
    TOOL_INVOCATION_DENIED = "tool_invocation_denied"
    TOOL_INVOCATION_STARTED = "tool_invocation_started"
    TOOL_INVOCATION_COMPLETED = "tool_invocation_completed"
    TOOL_INVOCATION_FAILED = "tool_invocation_failed"
    SERVER_REGISTERED = "server_registered"
    SERVER_UNREGISTERED = "server_unregistered"
    SERVER_HEALTH_CHANGED = "server_health_changed"
    POLICY_UPDATED = "policy_updated"
```

**Key Classes:**

| Class | Purpose |
|-------|---------|
| `MCPAuditEvent` | Compliance-grade audit event |
| `MCPAuditEmitter` | Emit audit events to event bus |

**Key Methods (MCPAuditEmitter):**

| Method | Purpose |
|--------|---------|
| `emit_tool_requested()` | Emit when tool invocation requested |
| `emit_tool_allowed()` | Emit when tool invocation allowed |
| `emit_tool_denied()` | Emit when tool invocation denied |
| `emit_tool_started()` | Emit when tool execution starts |
| `emit_tool_completed()` | Emit when tool execution completes |
| `emit_tool_failed()` | Emit when tool execution fails |
| `emit_server_registered()` | Emit when MCP server registered |
| `emit_server_unregistered()` | Emit when MCP server removed |

**Exports:**
```python
__all__ = [
    "MCPAuditEventType", "MCPAuditEvent", "MCPAuditEmitter",
    "get_mcp_audit_emitter", "configure_mcp_audit_emitter"
]
```

---

### 3.11 completeness_checker.py (513 LOC)

**Header:**
- Layer: L4 — Domain Engines
- Reference: GAP-027 (Evidence PDF Completeness)

**Purpose:** Validate evidence bundle completeness before PDF generation for SOC2 compliance.

**Required Fields (Standard):**
```python
REQUIRED_EVIDENCE_FIELDS = frozenset({
    "bundle_id", "incident_id", "run_id", "trace_id", "tenant_id",
    "policy_snapshot_id", "termination_reason", "total_steps",
    "total_tokens", "total_cost_cents", "created_at", "exported_by"
})
```

**SOC2 Required Fields:**
```python
SOC2_REQUIRED_FIELDS = frozenset({
    "control_mappings", "attestation_statement",
    "compliance_period_start", "compliance_period_end"
})
```

**Key Classes:**

| Class | Purpose |
|-------|---------|
| `EvidenceCompletenessError` | Raised when incomplete |
| `CompletenessCheckResponse` | Validation result |
| `EvidenceCompletenessChecker` | Main checker class |

**Exports:**
```python
__all__ = [
    "EvidenceCompletenessError", "CompletenessCheckResult",
    "EvidenceCompletenessChecker", "check_evidence_completeness",
    "ensure_evidence_completeness"
]
```

---

## 4. SCHEMAS ANALYSIS

### 4.1 models.py (381 LOC) — RAC MODELS

**Header:**
- Layer: L4 — Domain Engine
- Reference: PIN-454 (Cross-Domain Orchestration Audit)

**Purpose:** Runtime Audit Contract (RAC) data structures.

**Key Enums:**
```python
class AuditStatus(str, Enum):
    PENDING = "PENDING"
    ACKED = "ACKED"
    MISSING = "MISSING"
    FAILED = "FAILED"

class AuditDomain(str, Enum):
    INCIDENTS = "incidents"
    POLICIES = "policies"
    LOGS = "logs"
    ORCHESTRATOR = "orchestrator"

class AuditAction(str, Enum):
    CREATE_INCIDENT = "create_incident"
    EVALUATE_POLICY = "evaluate_policy"
    START_TRACE = "start_trace"
    COMPLETE_TRACE = "complete_trace"
    FINALIZE_RUN = "finalize_run"

class AckStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
```

**Key Dataclasses:**

| Class | Purpose |
|-------|---------|
| `AuditExpectation` | Declares what action MUST happen for a run |
| `DomainAck` | Reports that an action has completed |
| `ReconciliationResult` | Result of comparing expectations vs acks |

**Factory Functions:**
```python
def create_run_expectations(run_id, run_timeout_ms, grace_period_ms) -> List[AuditExpectation]
def create_domain_ack(run_id, domain, action, result_id, error, **metadata) -> DomainAck
```

---

## 5. LAYER DISTRIBUTION

| Layer | Files | Description |
|-------|-------|-------------|
| **L3** | 4 | Boundary Adapters (certificate, evidence_report, export_bundle_service, pdf_renderer) |
| **L4** | 14 | Domain Engines (facades, store, reconciler, durability, etc.) |
| **Empty** | 2 | Reserved (__init__.py stubs) |

---

## 6. CROSS-DOMAIN DEPENDENCIES

### Imports FROM Logs Domain:

| Caller | What They Import |
|--------|------------------|
| `app.services.audit.store` | `AuditStore`, `get_audit_store` (deprecated path) |
| `app.services.audit.models` | `AuditExpectation`, `DomainAck`, etc. |
| `ROK (L5)` | Reconciler, expectations |

### Imports INTO Logs Domain:

| File | External Imports |
|------|------------------|
| `reconciler.py` | `prometheus_client`, `app.services.audit.models`, `app.services.audit.store` |
| `export_bundle_service.py` | `app.db.Incident`, `app.db.Run`, `app.traces.store.TraceStore` |
| `logs_read_service.py` | `app.traces.models`, `app.traces.pg_store` |

---

## 7. VIOLATIONS

**Status:** CLEAN (0 violations detected)

All files in the Logs domain have appropriate `AUDIENCE: CUSTOMER` or are implicit customer-facing engines.

---

## 8. SUMMARY STATISTICS

| Metric | Value |
|--------|-------|
| **Total Files** | 20 |
| **Total LOC** | ~8,000 |
| **Facades** | 3 (logs_facade, evidence_facade, trace_facade) |
| **Engines** | 11 |
| **Schemas** | 1 (models.py) |
| **Empty Dirs** | 1 (drivers/) |
| **AUDIENCE Violations** | 0 |
| **Layer Violations** | 0 |

---

## 9. KEY ARCHITECTURAL PATTERNS

1. **Runtime Audit Contract (RAC)**: Expectations created at run start, acks emitted by domain facades, reconciler validates completeness.

2. **Evidence Chain**: Cryptographically linked evidence for compliance exports.

3. **Determinism Levels**: STRICT (byte-exact) → LOGICAL (policy-equivalent) → SEMANTIC (meaning-equivalent).

4. **Tamper-Evident Audit**: All audit events include integrity hashes and chain to previous events.

5. **Singleton Pattern**: `get_*_facade()` and `get_*_service()` factory functions throughout.

---

## 10. GOVERNANCE DECLARATIONS (NON-NEGOTIABLE)

These principles are **hard rules** that govern all future changes to the Logs domain.

### 10.1 INV-LOGS-001: Logs Never Decides Outcomes

Logs **records, verifies, and proves**. It does NOT:
- Decide policy (that's Policies domain)
- Create incidents (that's Incidents domain)
- Orchestrate recovery (that's ROK/Orchestrator)

**Violation:** Any code in Logs that makes enforcement decisions.

### 10.2 INV-LOGS-002: Logs Is Append-Only in Spirit

Corrections are **new evidence**, not mutations.

- No `UPDATE` or `DELETE` on audit tables without rollback trace
- Evidence chains are immutable once created
- Reprocessing creates new records, never overwrites

**Violation:** Any direct mutation of historical audit data.

### 10.3 INV-LOGS-003: Determinism Definitions Live Here Exclusively

Other domains **consume** these definitions:
- `DeterminismLevel` (STRICT, LOGICAL, SEMANTIC)
- `ReplayMatch` (EXACT, LOGICAL, SEMANTIC, MISMATCH)
- `PolicyDecision`, `CallRecord`, `ReplayResult`

Other domains **MUST NOT** redefine or fork these semantics.

**Violation:** Creating parallel determinism enums in another domain.

### 10.4 INV-LOGS-004: Compliance Exports Must Be Reproducible

Same inputs → same PDF bytes.

- Hash verification must pass on regeneration
- No non-deterministic elements (random IDs, floating timestamps)
- All content is derived from immutable audit records

**Violation:** Evidence PDF that produces different hash on regeneration.

### 10.5 INV-LOGS-005: logs_facade.py Is Composition-Only

The main facade (~1,600 LOC) is a **gravity well by design**.

Rules:
- No new computation logic inside the facade
- All logic must live in engines or sub-facades
- Facade methods are orchestration, not implementation

**Violation:** Adding business logic directly to `logs_facade.py` instead of creating/using an engine.

---

## 11. GOVERNANCE DECISIONS

### 11.1 PRESERVE (Do Not Touch)

| Component | Rationale |
|-----------|-----------|
| **RAC centralized in Logs** | Infrastructure-grade. Fragmenting it later breaks audit trail. |
| **L3/L4 split as-is** | certificate, PDF, export_bundle are correctly L3. They encode legal intent. |
| **evidence_report.py "heavy" (1152 LOC)** | Not a smell — it's a legal artifact. Premature splitting creates jurisdiction risk. |
| **drivers/ empty** | Logs is pull-heavy and emission-based. Empty directory is valid state. |
| **Domain scope boundaries** | Logs does NOT decide policy, create incidents, or orchestrate recovery. |

### 11.2 ACT (Required Changes)

| Action | Priority | Reason |
|--------|----------|--------|
| Add header to `replay_determinism.py` | HIGH | Other domains depend on determinism definitions. Implicit layer = accidental coupling. |
| Fix legacy import paths | HIGH | `app.services.audit.*` paths create shadow dependencies. Breakage compounds if deferred to Phase 6. |
| Declare logs_facade.py as composition-only | MEDIUM | Add governance comment at top to prevent logic creep. |

### 11.3 DO NOT DO

| Avoided Action | Reason |
|----------------|--------|
| Split `logs_facade.py` into 3 files | It's a gravity well by design. Splitting creates coordination overhead without benefit. |
| Rename `schemas/models.py` to `rac_models.py` | Only rename if non-RAC schemas appear. Churn for naming aesthetics is negative value. |
| Move PDF/export engines to a separate domain | Legal artifacts must stay with their audit chain. Separation breaks provenance. |
| "Simplify" L3 adapters | They are correctly heavy. Compliance code should be explicit, not clever. |
| Collapse L3 into L4 | L3/L4 split is the right layering for legal/compliance artifacts. |

---

## 12. CROSS-DOMAIN CONTRACTS

### 12.1 Logs ↔ Incidents

| Direction | What Flows |
|-----------|------------|
| Logs → Incidents | `EvidenceChain`, evidence links for incident export |
| Incidents → Logs | `AuditExpectation` (CREATE_INCIDENT), `DomainAck` emissions |

### 12.2 Logs ↔ Policies

| Direction | What Flows |
|-----------|------------|
| Logs → Policies | `PolicyDecision` audit records, determinism validation |
| Policies → Logs | `AuditExpectation` (EVALUATE_POLICY), `DomainAck` emissions |

### 12.3 Logs ↔ Orchestrator (ROK)

| Direction | What Flows |
|-----------|------------|
| Logs → ROK | `ReconciliationResult`, `AuditStore` queries |
| ROK → Logs | Expectations at T0, `DomainAck` (FINALIZE_RUN) at Tn |

---

## 13. SILENT RISKS (Monitor)

### 13.1 logs_facade.py as Gravity Well

At ~1,600 LOC, this file is not "too big" — it is **too central**.

If anything new touches Logs, it will be tempted to land here.

**Mitigation:** Governance rule INV-LOGS-005 (composition-only).

### 13.2 Legacy Import Paths

Imports like `app.services.audit.store` and `app.services.audit.models` still exist.

This is the **biggest real risk** in the domain.

**Mitigation:** Prioritize import path updates in Phase 5. Treat Logs as foundational dependency. Other domains should import Logs, not shadow it.

### 13.3 Missing Header on replay_determinism.py

The file defines **core determinism semantics** with no explicit layer declaration.

**Mitigation:** Add header immediately (see Section 14.1).

---

## 14. REQUIRED ACTIONS

### 14.1 Add Missing Header to replay_determinism.py

The file `replay_determinism.py` lacks the standard layer header. **Required** addition:

```python
# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Replay determinism validation for LLM calls — CANONICAL DEFINITIONS
# Callers: logs_facade.py, evidence services, other domains (read-only)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Governance: INV-LOGS-003 — Determinism definitions live here exclusively
```

### 14.2 Add Governance Comment to logs_facade.py

Add at top of file after existing header:

```python
# GOVERNANCE: INV-LOGS-005
# This facade is COMPOSITION-ONLY. No new computation logic inside.
# All logic must live in engines or sub-facades.
# This file orchestrates; it does not implement.
```

### 14.3 Update __init__.py Exports

The `facades/__init__.py` and `engines/__init__.py` files contain placeholder text. Add explicit exports once the migration is complete.

---

## 15. RELATED DOCUMENTS

- `HOC_account_analysis_v1.md` - Account domain analysis
- `HOC_policies_analysis_v1.md` - Policies domain analysis
- `HOC_remaining_domains_analysis_v1.md` - Summary of other domains
- `DIRECTORY_REORGANIZATION_PLAN.md` - Overall HOC reorganization plan
