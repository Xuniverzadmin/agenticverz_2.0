# Logs Domain — Canonical Software Literature

**Domain:** logs
**Generated:** 2026-01-31
**Reference:** PIN-496
**Total Files:** 37 (18 L5_engines, 14 L6_drivers, 1 L5_support, 1 adapter, 3 __init__.py)
**PIN-519 Update:** +1 L6_driver (audit_ledger_read_driver.py)

---

## Reality Delta (2026-02-07)

- Execution topology: logs L2 routes dispatch via L4 `OperationRegistry` (no direct L2→L5 gaps).
- Clean-arch debt (mechanical audit): several L5 engines still import `app.models.*` (e.g. audit ledger + PDF rendering) and should be pushed behind L6 drivers to satisfy strict driver/engine purity.
- Verification: `python3 scripts/ops/hoc_l5_l6_purity_audit.py --domain logs`.

## Consolidation Actions (2026-01-31)

### Naming Violations Fixed (8 renames)

| # | Old Name | New Name | Layer |
|---|----------|----------|-------|
| N1 | audit_ledger_service.py | audit_ledger_engine.py | L5 |
| N2 | audit_ledger_service_async.py | audit_ledger_driver.py | L6 |
| N3 | capture.py | capture_driver.py | L6 |
| N4 | idempotency.py | idempotency_driver.py | L6 |
| N5 | integrity.py | integrity_driver.py | L6 |
| N6 | job_execution.py | job_execution_driver.py | L6 |
| N7 | panel_consistency_checker.py | panel_consistency_driver.py | L6 |
| N8 | replay.py | replay_driver.py | L6 |

### Header Corrections (2)

| File | Old Header | New Header |
|------|-----------|------------|
| logs/__init__.py | `# Layer: L4 — Domain Services` | `# Layer: L5 — Domain (Logs)` |
| logs/L5_schemas/__init__.py | `# Layer: L5 — Domain Services` | `# Layer: L5 — Domain Schemas` |

### Import Path Fix (1)

| File | Old Import | New Import |
|------|-----------|------------|
| panel_response_assembler.py | `from .panel_consistency_checker import` | `from app.hoc.cus.logs.L6_drivers.panel_consistency_driver import` |

### Legacy Connections

**None.** Domain is clean — no HOC→legacy or legacy→HOC imports.

### L2 Purity Update (2026-02-06)

L2 logs/tenants endpoints no longer import integrations L6 drivers directly.
They now use `IntegrationsDriverBridge` capabilities from hoc_spine (PIN-L2-PURITY).

### New L5_schemas File (PIN-504 Phase 6)

| File | Contents | Purpose |
|------|----------|---------|
| `L5_schemas/determinism_types.py` | `DeterminismLevel` enum | Type enum extracted from `replay_determinism.py` so L2 can import without L5_engines dependency |

### Cross-Domain Imports

**None.** Domain is clean.

### Duplicates

**None.** `audit_ledger_engine.py` (L5, sync) and `audit_ledger_driver.py` (L6, async) are a legitimate sync/async split.

---

## L5_engines (18 files)

### __init__.py
- **Role:** Package init, re-exports LogsDomainFacade, EvidenceFacade, TraceFacade
- **Classes:** None
- **Callers:** External importers

### audit_evidence.py
- **Role:** Audit evidence collection engine
- **Layer:** L5

### audit_ledger_engine.py *(renamed from audit_ledger_service.py)*
- **Role:** Sync audit ledger writer for governance events (incidents)
- **Classes:** `AuditLedgerService`
- **Factory:** `get_audit_ledger_service(session)`
- **Execution:** sync
- **Callers:** incident_write_engine (L5)

### audit_reconciler.py
- **Role:** Audit reconciliation engine
- **Layer:** L5

### certificate.py
- **Role:** Replay certificate generation (CertificateService)
- **Classes:** `CertificateService`
- **Execution:** sync
- **Callers:** L4 logs_handler (logs.certificate)

### completeness_checker.py
- **Role:** Evidence PDF completeness validation for SOC2 compliance
- **Classes:** `EvidenceCompletenessChecker`, `CompletenessCheckResult`, `CompletenessCheckResponse`, `EvidenceCompletenessError`
- **Functions:** `check_evidence_completeness()`, `ensure_evidence_completeness()`
- **Execution:** sync (pure validation, no DB)
- **Callers:** pdf_renderer, evidence_report, export APIs

### evidence_facade.py
- **Role:** Evidence domain facade
- **Classes:** `EvidenceFacade`
- **Factory:** `get_evidence_facade()`
- **Callers:** L4 logs_handler (logs.evidence)

### evidence_report.py
- **Role:** Legal-grade PDF evidence report generator
- **Classes:** `EvidenceReportGenerator`, `IncidentEvidence`, `CertificateEvidence`
- **Functions:** `generate_evidence_report()`
- **Execution:** sync
- **Callers:** L4 logs_handler (logs.evidence_report)
- **Dependencies:** reportlab

### logs_facade.py
- **Role:** Main logs domain facade (27 async endpoints)
- **Classes:** `LogsFacade`
- **Factory:** `get_logs_facade()`
- **Callers:** L4 logs_handler (logs.query)

### logs_read_engine.py
- **Role:** Logs read engine
- **Layer:** L5

### mapper.py
- **Role:** Data mapping utilities
- **Layer:** L5

### panel_response_assembler.py
- **Role:** Assemble final panel response envelope
- **Callers:** Panel adapters

### pdf_renderer.py
- **Role:** Render export bundles to PDF (evidence, SOC2, executive debrief)
- **Classes:** `PDFRenderer`
- **Factory:** `get_pdf_renderer()`
- **Methods:** `render_evidence_pdf()`, `render_soc2_pdf()`, `render_executive_debrief_pdf()`
- **Execution:** sync
- **Callers:** L4 logs_handler (logs.pdf), incidents L2 (cross-domain via L4)
- **Dependencies:** reportlab, app.models.export_bundles

### redact.py
- **Role:** Data redaction engine
- **Layer:** L5

### replay_determinism.py
- **Role:** Replay validation and context building
- **Classes:** `ReplayValidator`, `ReplayContextBuilder`
- **Callers:** L4 logs_handler (logs.replay)

### trace_facade.py
- **Role:** Trace domain facade
- **Classes:** `TraceFacade`
- **Factory:** `get_trace_facade()`

### traces_metrics.py
- **Role:** Trace metrics computation
- **Layer:** L5

### traces_models.py
- **Role:** Trace domain models/types
- **Layer:** L5

---

## L6_drivers (14 files)

### __init__.py
- **Role:** Package init, re-exports ExportBundleStore, LogsDomainStore + snapshots

### audit_ledger_driver.py *(renamed from audit_ledger_service_async.py)*
- **Role:** Async audit ledger writer for governance events
- **Classes:** `AuditLedgerServiceAsync`
- **Factory:** `get_audit_ledger_service_async(session)`
- **Execution:** async
- **Callers:** policy_limits_engine, policy_rules_engine, policy_proposal_engine (L5)
- **PIN-519:** Added signal feedback write methods (signal_acknowledged, signal_suppressed, signal_escalated)

### audit_ledger_read_driver.py *(NEW - PIN-519)*
- **Role:** Async audit ledger read operations for signal feedback queries
- **Classes:** `AuditLedgerReadDriver`
- **Factory:** `get_audit_ledger_read_driver(session)`
- **Execution:** async
- **Callers:** L4 signal_feedback_coordinator
- **Methods:** `get_signal_feedback()`, `get_audit_entries_for_entity()`, `get_signal_events_for_run()`

### bridges_driver.py
- **Role:** Bridge driver for cross-store operations
- **Layer:** L6

### capture_driver.py *(renamed from capture.py)*
- **Role:** Taxonomy evidence capture service (ctx-aware, NO COMMIT)
- **Classes:** `EvidenceContextError`, `CaptureFailureReason`, `FailureResolution`
- **Execution:** sync
- **Callers:** L5 engines

### export_bundle_store.py
- **Role:** Export bundle persistence
- **Classes:** `ExportBundleStore`
- **Factory:** `get_export_bundle_store()`

### idempotency_driver.py *(renamed from idempotency.py)*
- **Role:** Trace idempotency enforcement (Redis + Lua scripts)
- **Classes:** `IdempotencyResult`, `IdempotencyResponse`, `RedisIdempotencyStore`, `InMemoryIdempotencyStore`
- **Execution:** async

### integrity_driver.py *(renamed from integrity.py)*
- **Role:** Integrity computation with separated concerns
- **Classes:** `IntegrityState`, `IntegrityGrade`, `EvidenceClass`, `FailureResolution`, `CaptureFailure`, `IntegrityFacts`, `IntegrityAssembler`, `IntegrityEvaluation`, `IntegrityEvaluator`
- **Execution:** sync

### job_execution_driver.py *(renamed from job_execution.py)*
- **Role:** Job execution support services (retry, progress, audit)
- **Classes:** `RetryStrategy`, `RetryConfig`, `RetryAttempt`, `JobRetryManager`, `ProgressStage`, `ProgressUpdate`, `JobProgressTracker`, `JobAuditEventType`, `JobAuditEvent`, `JobAuditEmitter`
- **Factory:** `get_job_retry_manager()`, `get_job_progress_tracker()`, `get_job_audit_emitter()`
- **Execution:** async

### logs_domain_store.py
- **Role:** Main logs domain data store
- **Classes:** `LogsDomainStore`
- **Factory:** `get_logs_domain_store()`

### panel_consistency_driver.py *(renamed from panel_consistency_checker.py)*
- **Role:** Cross-slot consistency enforcement
- **Classes:** `ConsistencyViolation`, `ConsistencyCheckResult`, `PanelConsistencyChecker`
- **Execution:** sync (pure logic)

### pg_store.py
- **Role:** PostgreSQL store implementation
- **Layer:** L6

### replay_driver.py *(renamed from replay.py)*
- **Role:** Trace replay execution
- **Classes:** `ReplayBehavior`, `ReplayMismatchError`, `IdempotencyViolationError`, `ReplayResult`, `ReplayEnforcer`, `IdempotencyStore`, `InMemoryIdempotencyStore`, `RedisIdempotencyStore`
- **Factory:** `get_replay_enforcer()`
- **Execution:** sync (Redis-backed)

### traces_store.py
- **Role:** Trace data persistence store
- **Layer:** L6

---

## L5_support (1 file)

### CRM/engines/audit_engine.py
- **Role:** CRM audit engine (L8 support layer)
- **Layer:** L5_support

---

## Adapters (1 file)

### customer_logs_adapter.py
- **Role:** Customer logs adapter (L2 boundary)
- **Layer:** L2 adapter

---

## L5_schemas (1 file)

### __init__.py
- **Role:** Schemas package init

---

## L4 Handler

**File:** `hoc/cus/hoc_spine/orchestrator/handlers/logs_handler.py`
**Operations:** 6

| Operation | Handler Class | Target |
|-----------|--------------|--------|
| logs.query | LogsQueryHandler | LogsFacade |
| logs.evidence | LogsEvidenceHandler | EvidenceFacade |
| logs.certificate | LogsCertificateHandler | CertificateService |
| logs.replay | LogsReplayHandler | ReplayValidator, ReplayContextBuilder, ReplayCoordinator (PIN-520) |
| logs.evidence_report | LogsEvidenceReportHandler | generate_evidence_report() |
| logs.pdf | LogsPdfHandler | PDFRenderer |

### logs.replay Methods (PIN-520)

| Method | Type | Target | Purpose |
|--------|------|--------|---------|
| build_call_record | sync | ReplayContextBuilder (L5) | Build call record for replay |
| validate_replay | sync | ReplayValidator (L5) | Validate replay determinism |
| enforce_step | async | ReplayCoordinator (L4) | Enforce replay behavior for single step |
| enforce_trace | async | ReplayCoordinator (L4) | Enforce replay behavior for entire trace |

No L4 handler import updates required — none of the renamed files are referenced by the handler.

---

## Cleansing Cycle (2026-01-31) — PIN-503

### Cat B: Legacy Import Disconnected (1)

| File | Old Import | New Import |
|------|-----------|------------|
| `L5_engines/trace_facade.py` line 239 | `app.services.audit.models.AuditAction, AuditDomain, DomainAck` | `app.hoc.cus.hoc_spine.schemas.rac_models.AuditAction, AuditDomain, DomainAck` |

Active runtime import (lazy, function-scoped). All three classes exist in `hoc_spine/schemas/rac_models.py` (100% match per Phase 5 D738/D747).

### Cat B: Stale Docstring References Corrected (3)

| File | Old Docstring Reference | New Docstring Reference |
|------|------------------------|------------------------|
| `L5_engines/trace_facade.py` | `from app.services.observability.trace_facade import ...` | `from app.hoc.cus.logs.L5_engines.trace_facade import ...` |
| `L5_engines/evidence_facade.py` | `from app.services.evidence.facade import ...` | `from app.hoc.cus.logs.L5_engines.evidence_facade import ...` |
| `L5_engines/certificate.py` | `from app.services.certificate import ...` | `from app.hoc.cus.logs.L5_engines.certificate import ...` |

### Cat D: L2→L5 Bypass Violations (1 — DOCUMENT ONLY)

| L2 File | Line | Import | Domain Reached |
|---------|------|--------|----------------|
| `policies/guard.py` | 92 | `logs.L5_engines.replay_determinism.DeterminismLevel` | logs L5 |

**Deferred:** Requires Loop Model infrastructure (PIN-487 Part 2).

### Cat E: Cross-Domain L5→L5/L6 Violations (Inbound — 5)

| Source File | Source Domain | Import Target |
|------------|--------------|--------------|
| `incidents/L5_engines/incident_write_engine.py` | incidents | `logs.L5_engines.audit_ledger_service` |
| `policies/L5_engines/policy_limits_engine.py` | policies | `logs.L6_drivers.audit_ledger_service_async` |
| `policies/L5_engines/policy_proposal_engine.py` | policies | `logs.L6_drivers.audit_ledger_service_async` |
| `policies/L5_engines/policy_rules_engine.py` | policies | `logs.L6_drivers.audit_ledger_service_async` |
| `integrations/adapters/customer_logs_adapter.py` | integrations | `logs.L5_engines.logs_read_engine` |

**Deferred:** Requires L4 Coordinator to mediate cross-domain audit writes.

### Tally

38/38 checks PASS (34 consolidation + 4 cleansing).

---

## PIN-507 Law 5 Remediation (2026-02-01)

**L4 Handler Update:** All `getattr()`-based reflection dispatch in this domain's L4 handler replaced with explicit `dispatch = {}` maps. All `asyncio.iscoroutinefunction()` eliminated via explicit sync/async split. Zero `__import__()` calls remain. See PIN-507 for full audit trail.

## PIN-507 Law 0 Remediation (2026-02-01)

**`audit_ledger_engine.py` (L5):** Now imported by legacy `app/services/incident_write_engine.py` as a transitional `services→hoc` dependency. The previous import path `app.services.logs.audit_ledger_service` was abolished during HOC migration.

**`audit_ledger_driver.py` (L6):** Now imported by 3 legacy services (`policy_limits_service.py`, `policy_rules_service.py`, `policy_proposal.py`) as transitional `services→hoc` dependencies. The previous path `app.services.logs.audit_ledger_service_async` was abolished.

**`export_bundle_store.py` (L6):** `Incident` import corrected from `app.db` → `app.models.killswitch`. L6→L7 boundary comment added.

**`L5_engines/__init__.py`:** Fixed wrong re-export names (`LogsDomainFacade` → `LogsFacade`). Added eager-import warning docstring.

**`L6_drivers/__init__.py`:** Added eager-import warning docstring.

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-513 Phase 7 — Reverse Boundary Severing (HOC→services) (2026-02-01)

**`reactor_initializer.py` (L6 driver):** Import swapped from `app.services.governance.profile.get_governance_config` → `app.hoc.cus.hoc_spine.authority.profile_policy_mode.get_governance_config`. HOC equivalent already existed in hoc_spine authority layer. Fully severed.

## PIN-520 Wiring Audit (2026-02-03)

### ReplayCoordinator Wiring

**Problem:** ReplayCoordinator in `hoc_spine/orchestrator/coordinators/replay_coordinator.py` had zero callers.

**Solution:** Wired to logs domain via `logs.replay` operation.

| Method | Purpose | Input | Output |
|--------|---------|-------|--------|
| `enforce_step` | Single step enforcement with guard | step, execute_fn, tenant_id | StepEnforcementResult |
| `enforce_trace` | Full trace enforcement with guard | trace, step_executor, tenant_id | TraceEnforcementResult |

**Call Pattern:**
```
registry.execute("logs.replay", ctx) where ctx.params["method"] = "enforce_step" | "enforce_trace"
→ LogsReplayHandler.execute(ctx)
→ ReplayCoordinator.enforce_step() or enforce_trace()
→ Policy guard checks + step execution
```

**Export Path:** `from app.hoc.cus.hoc_spine.orchestrator.coordinators import ReplayCoordinator`

## PIN-519 System Run Introspection (2026-02-03)

### New L6 Driver: audit_ledger_read_driver.py

**Purpose:** Read-only async queries for signal feedback from audit ledger.

| Method | Purpose |
|--------|---------|
| `get_signal_feedback(tenant_id, signal_fingerprint)` | Query SIGNAL_ACKNOWLEDGED/SUPPRESSED/ESCALATED events |
| `get_audit_entries_for_entity(tenant_id, entity_type, entity_id, limit)` | Get audit entries for an entity |
| `get_signal_events_for_run(tenant_id, run_id, limit)` | Get signal events related to a run |

**Factory:** `get_audit_ledger_read_driver(session)`

### Updated L6 Driver: audit_ledger_driver.py

**New Signal Write Methods:**

| Method | Purpose |
|--------|---------|
| `signal_acknowledged(tenant_id, signal_id, actor_id, actor_type, reason, signal_state)` | Record signal acknowledgment |
| `signal_suppressed(tenant_id, signal_id, actor_id, actor_type, reason, suppressed_until)` | Record signal suppression |
| `signal_escalated(tenant_id, signal_id, actor_id, actor_type, reason, escalation_context)` | Record signal escalation |

### LogsBridge Extension

**New Capabilities:**

| Capability | Purpose | Consumer |
|------------|---------|----------|
| `traces_store_capability()` | Returns SQLiteTraceStore for run trace queries | RunProofCoordinator |
| `audit_ledger_read_capability(session)` | Returns AuditLedgerReadDriver for signal feedback | SignalFeedbackCoordinator |

**Usage:**
```python
logs_bridge = get_logs_bridge()
trace_store = logs_bridge.traces_store_capability()
audit_reader = logs_bridge.audit_ledger_read_capability(session)
```

## PIN-521 L5_schemas Extraction (2026-02-03)

### New L5_schemas File: traces_models.py

**Purpose:** Trace dataclasses extracted from L5_engines for L6 driver import compliance.

| Class/Function | Purpose |
|----------------|---------|
| `TraceStatus` | Enum: success, failure, retry, skipped |
| `TraceStep` | Single step in execution trace |
| `TraceSummary` | Summary for listing purposes |
| `TraceRecord` | Complete trace with all steps |
| `ParityResult` | Result of trace comparison |
| `compare_traces()` | Compare two traces for replay parity |

**Migration:**
```python
# OLD (violates L6→L5_engines ban)
from app.hoc.cus.logs.L5_engines.traces_models import TraceRecord

# NEW (compliant)
from app.hoc.cus.logs.L5_schemas.traces_models import TraceRecord
```

**Backward Compatibility:** `L5_engines/traces_models.py` re-exports from `L5_schemas` for existing callers.

### Updated: L6_drivers/traces_store.py

Import changed from `L5_engines.traces_models` to `L5_schemas.traces_models` per CI compliance.
