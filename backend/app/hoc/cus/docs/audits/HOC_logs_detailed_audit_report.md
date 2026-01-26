# HOC LOGS DOMAIN DEEP AUDIT REPORT

**Date:** 2026-01-23
**Scope:** `houseofcards/customer/logs/` (LOGS domain only)
**Auditor:** Claude
**Reference:** Policies domain audit methodology (POL-DUP-001 to POL-DUP-006)

---

## 1. EXECUTIVE SUMMARY

The Logs domain exhibits **significantly cleaner architecture** than the Policies domain. Unlike the policies audit which found 6 duplicate issues (4 quarantined), the logs domain shows:

- **0 Critical Duplications** (no 100% field overlap facade-engine DTOs)
- **2 Minor Issues** (utility drift, tolerated)
- **Strong Governance Markers** present (INV-LOGS-003, INV-LOGS-005)

**Verdict:** CLEAN — No quarantine action required.

---

## 2. DOMAIN STRUCTURE

### 2.1 Files Audited

| Folder | Files | LOC |
|--------|-------|-----|
| `facades/` | 3 | 2,443 |
| `engines/` | 11 | ~5,500 |
| `schemas/` | 1 | 381 |
| `drivers/` | 0 | — |
| **TOTAL** | **15** | **~8,324** |

### 2.2 Facades (L4 Boundary)

| File | Dataclasses | Enums | Classes | Singleton |
|------|-------------|-------|---------|-----------|
| `logs_facade.py` | 32 | 2 | 1 | `get_logs_facade()` |
| `trace_facade.py` | 0 | 0 | 1 | `get_trace_facade()` |
| `evidence_facade.py` | 4 | 3 | 1 | `get_evidence_facade()` |

### 2.3 Engines (L4 Domain Logic)

| File | Enums | Dataclasses | Classes | Singletons |
|------|-------|-------------|---------|------------|
| `audit_evidence.py` | 1 (`MCPAuditEventType`) | 1 (`MCPAuditEvent`) | 1 | `get_mcp_audit_emitter()` |
| `evidence_report.py` | 0 | 2 | 1 | — |
| `logs_read_service.py` | 0 | 0 | 1 | `get_logs_read_service()` |
| `reconciler.py` | 0 | 0 | 1 | `get_audit_reconciler()` |
| `completeness_checker.py` | 1 | 1 | 1 | — |
| `durability.py` | 1 | 1 | 1 | — |
| `replay_determinism.py` | 2 | 4 | 2 | — |
| `export_bundle_service.py` | 0 | 0 | 1 | `get_export_bundle_service()` |
| `pdf_renderer.py` | 0 | 0 | 1 | `get_pdf_renderer()` |
| `certificate.py` | 1 | 2 | 1 | — |

### 2.4 Schemas

| File | Enums | Dataclasses | Functions |
|------|-------|-------------|-----------|
| `models.py` | 4 | 3 | 2 |

---

## 3. CROSS-COMPARISON ANALYSIS

### 3.1 Facade Result Types vs Engine Types

**Unlike the Policies domain**, the Logs domain maintains clear separation:

| Pattern | Policies Domain | Logs Domain |
|---------|-----------------|-------------|
| Facade DTO duplicating Engine DTO | ✅ 4 cases (100% overlap) | ❌ None found |
| Facade-only result types | Mixed | ✅ Clear (32 result dataclasses) |
| Engine-only types | Mixed | ✅ Clear (`MCPAuditEvent`, `ReplayResult`, etc.) |

**Analysis:** `logs_facade.py` defines 32 result dataclasses with `*Result` suffix. These are API response envelopes, **not duplicates** of engine types. Engine types (`MCPAuditEvent`, `ReplayResult`, `CallRecord`) serve different purposes.

### 3.2 Enum Comparison

| Enum | Location | Values | Potential Overlap |
|------|----------|--------|-------------------|
| `SourceDomain` | `logs_facade.py:47` | ACTIVITY, POLICY, INCIDENTS, LOGS, SYSTEM | None |
| `Origin` | `logs_facade.py:57` | SYSTEM, HUMAN, AGENT, MIGRATION, REPLAY | None |
| `AuditDomain` | `schemas/models.py:44` | incidents, policies, logs, orchestrator | Different purpose |
| `AuditAction` | `schemas/models.py:53` | CREATE_INCIDENT, EVALUATE_POLICY, START_TRACE, etc. | Unique |
| `MCPAuditEventType` | `audit_evidence.py` | 10 event types | Unique (MCP-specific) |
| `DeterminismLevel` | `replay_determinism.py` | STRICT, LOGICAL, SEMANTIC | Unique |
| `ReplayMatch` | `replay_determinism.py` | EXACT, LOGICAL, SEMANTIC, MISMATCH | Unique |
| `CompletenessCheckResult` | `completeness_checker.py` | COMPLETE, INCOMPLETE, VALIDATION_DISABLED, PARTIAL | Unique |
| `DurabilityCheckResult` | `durability.py` | DURABLE, NOT_DURABLE, ENFORCEMENT_DISABLED, UNKNOWN | Unique |
| `EvidenceType` | `evidence_facade.py:57` | execution, retrieval, policy, cost, incident | Unique |
| `ExportFormat` | `evidence_facade.py:66` | json, csv, pdf | Unique |
| `ExportStatus` | `evidence_facade.py:73` | pending, processing, completed, failed | Unique |
| `CertificateType` | `certificate.py:50` | REPLAY_PROOF, POLICY_AUDIT, INCIDENT_EXPORT | Unique |

**Result:** No enum duplication detected.

---

## 4. ISSUES FOUND

### 4.1 LOGS-DUP-001: Utility Hash Functions Drift (DEFERRED)

**Severity:** LOW
**Status:** DEFERRED — Utility drift tolerated per architectural guidance

| File | Function | Purpose |
|------|----------|---------|
| `evidence_facade.py:424` | `_hash_data()` | SHA256 → 32-char truncated |
| `certificate.py:190` | `_sign()` | HMAC-SHA256 signature |
| `export_bundle_service.py:329` | `_compute_bundle_hash()` | SHA256 full |
| `audit_evidence.py` | `_hash_value()` | Integrity hash |

**Analysis:** These serve different cryptographic purposes:
- `_hash_data()` — Evidence chain linking
- `_sign()` — Certificate HMAC signing
- `_compute_bundle_hash()` — Bundle integrity
- `_hash_value()` — Audit event integrity

**Recommendation:** No action. Different algorithms/purposes. Consolidation would create inappropriate coupling.

### 4.2 LOGS-DUP-002: Similar Dataclass Patterns (NOT A DUPLICATION)

**Files Compared:**
- `evidence_facade.py::EvidenceLink` vs `certificate.py::CertificatePayload`
- `logs_facade.py::EvidenceMetadataResult` vs engine evidence types

**Analysis:** These types serve different domains:
- `EvidenceLink` — Chain-based evidence linking
- `CertificatePayload` — Cryptographic certificate content
- `EvidenceMetadataResult` — API response metadata envelope

**Verdict:** Not duplications. Different semantic purposes.

---

## 5. GOVERNANCE COMPLIANCE

### 5.1 Governance Markers Found

| File | Marker | Meaning |
|------|--------|---------|
| `logs_facade.py:13` | `INV-LOGS-005` | Facade is COMPOSITION-ONLY (no new logic) |
| `replay_determinism.py` | `INV-LOGS-003` | Determinism definitions live here exclusively |

### 5.2 Layer Compliance

All files have proper layer headers:
- Facades: L4 with `AUDIENCE: CUSTOMER`
- Engines: L4 Domain Engine
- Schemas: L4 Domain Engine (models.py)

---

## 6. COMPARISON TO POLICIES DOMAIN

| Metric | Policies Domain | Logs Domain |
|--------|-----------------|-------------|
| Files audited | 12 | 15 |
| Critical duplications | 4 (quarantined) | 0 |
| Deferred issues | 2 | 2 |
| Governance markers | 0 | 2 |
| Quarantine action | YES | NO |

---

## 7. VERDICT

**Status:** CLEAN

**Findings:**
- **0 duplications requiring quarantine**
- **2 deferred issues** (utility drift, tolerated)
- **Strong governance compliance** (INV-LOGS-003, INV-LOGS-005)

**Recommendation:** No quarantine folder needed for logs domain. The architecture correctly separates:
1. Facade result types (API responses)
2. Engine types (internal processing)
3. Schema types (RAC contract models)

---

## 8. DEFERRED ISSUES REGISTRY

| Issue ID | Type | Status |
|----------|------|--------|
| LOGS-DUP-001 | Utility hash function drift | DEFERRED — Utility drift tolerated |
| LOGS-DUP-002 | Similar dataclass patterns | NOT A DUPLICATION — Different semantic purposes |

---

## 9. ARTIFACT INVENTORY

### 9.1 Facades

#### logs_facade.py (1,592 lines)
- **Enums:** `SourceDomain`, `Origin`
- **Dataclasses (32):**
  - `EvidenceMetadataResult` — Global metadata contract
  - `LLMRunRecordResult`, `LLMRunRecordsResult` — LLM run records
  - `TraceStepResult` — Individual trace step
  - `LLMRunEnvelopeResult` — O1: Canonical immutable run record
  - `LLMRunTraceResult` — O2: Step-by-step trace
  - `GovernanceEventResult`, `LLMRunGovernanceResult` — O3: Policy interaction
  - `ReplayEventResult`, `LLMRunReplayResult` — O4: 60-second replay window
  - `LLMRunExportResult` — O5: Export metadata
  - `SystemRecordResult`, `SystemRecordsResult` — System records
  - `SystemSnapshotResult` — O1: Environment snapshot
  - `TelemetryStubResult` — O2: Telemetry stub
  - `SystemEventResult`, `SystemEventsResult` — O3: Infra events
  - `SystemReplayResult` — O4: Infra replay window
  - `SystemAuditResult` — O5: Infra attribution
  - `AuditLedgerItemResult`, `AuditLedgerDetailResult`, `AuditLedgerListResult` — Audit ledger
  - `IdentityEventResult`, `AuditIdentityResult` — O1: Identity lifecycle
  - `AuthorizationDecisionResult`, `AuditAuthorizationResult` — O2: Access decisions
  - `AccessEventResult`, `AuditAccessResult` — O3: Log access audit
  - `IntegrityCheckResult`, `AuditIntegrityResult` — O4: Tamper detection
  - `ExportRecordResult`, `AuditExportsResult` — O5: Compliance exports
- **Class:** `LogsFacade`
- **Singleton:** `get_logs_facade()`

#### trace_facade.py (289 lines)
- **Class:** `TraceFacade`
- **Singleton:** `get_trace_facade()`
- **RAC Integration:** Emits START_TRACE, COMPLETE_TRACE acks

#### evidence_facade.py (562 lines)
- **Enums:** `EvidenceType`, `ExportFormat`, `ExportStatus`
- **Dataclasses:** `EvidenceLink`, `EvidenceChain`, `VerificationResult`, `EvidenceExport`
- **Class:** `EvidenceFacade`
- **Singleton:** `get_evidence_facade()`

### 9.2 Engines

#### audit_evidence.py (664 lines)
- **Enum:** `MCPAuditEventType` (10 event types)
- **Dataclass:** `MCPAuditEvent` (tamper-evident audit event)
- **Class:** `MCPAuditEmitter`
- **Singleton:** `get_mcp_audit_emitter()`
- **Helpers:** `_hash_value()`, `_contains_sensitive()`, `_redact_sensitive()`

#### evidence_report.py (1,152 lines)
- **Dataclasses:** `CertificateEvidence`, `IncidentEvidence`
- **Class:** `EvidenceReportGenerator` (PDF generation with reportlab)
- **Function:** `generate_evidence_report()`

#### logs_read_service.py (207 lines)
- **Class:** `LogsReadService` (tenant-scoped reads)
- **Singleton:** `get_logs_read_service()`

#### reconciler.py (316 lines)
- **Class:** `AuditReconciler` (four-way validation)
- **Singleton:** `get_audit_reconciler()`

#### completeness_checker.py (513 lines)
- **Enum:** `CompletenessCheckResult`
- **Exception:** `EvidenceCompletenessError`
- **Dataclass:** `CompletenessCheckResponse`
- **Class:** `EvidenceCompletenessChecker`
- **Functions:** `check_evidence_completeness()`, `ensure_evidence_completeness()`

#### durability.py (320 lines)
- **Enum:** `DurabilityCheckResult`
- **Exception:** `RACDurabilityEnforcementError`
- **Dataclass:** `DurabilityCheckResponse`
- **Class:** `RACDurabilityChecker`
- **Functions:** `check_rac_durability()`, `ensure_rac_durability()`

#### replay_determinism.py (515 lines)
- **Governance:** INV-LOGS-003 — Determinism definitions live here exclusively
- **Enums:** `DeterminismLevel` (STRICT, LOGICAL, SEMANTIC), `ReplayMatch`
- **Dataclasses:** `ModelVersion`, `PolicyDecision`, `ReplayResult`, `CallRecord`
- **Classes:** `ReplayValidator`, `ReplayContextBuilder`

#### export_bundle_service.py (410 lines)
- **Class:** `ExportBundleService`
- **Singleton:** `get_export_bundle_service()`
- **Methods:** `create_evidence_bundle()`, `create_soc2_bundle()`, `create_executive_debrief()`

#### pdf_renderer.py (680 lines)
- **Class:** `PDFRenderer`
- **Singleton:** `get_pdf_renderer()`
- **Methods:** `render_evidence_pdf()`, `render_soc2_pdf()`, `render_executive_debrief_pdf()`

#### certificate.py (375 lines)
- **Enum:** `CertificateType` (REPLAY_PROOF, POLICY_AUDIT, INCIDENT_EXPORT)
- **Dataclasses:** `CertificatePayload`, `Certificate`
- **Class:** `CertificateService`

### 9.3 Schemas

#### models.py (381 lines)
- **Enums:** `AuditStatus`, `AuditDomain`, `AuditAction`, `AckStatus`
- **Dataclasses:** `AuditExpectation`, `DomainAck`, `ReconciliationResult`
- **Factory Functions:** `create_run_expectations()`, `create_domain_ack()`

---

## 10. AUDIT TRAIL

| Date | Action | Auditor |
|------|--------|---------|
| 2026-01-23 | Deep audit completed | Claude |
| 2026-01-23 | Report generated | Claude |

---

**End of Audit Report**
