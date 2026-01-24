# Logs Domain Lock — FINAL
# Status: LOCKED
# Effective: 2026-01-24
# Reference: Phase-2.5B Logs Extraction (LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md)

---

## Domain Status

**LOCKED** — No modifications permitted without explicit unlock command.

---

## Domain Nature

> **Logs is a FACT EMISSION domain, not a DECISION domain.**

Logs:
- **Records** — what happened
- **Verifies** — was it complete
- **Proves** — cryptographic evidence

Logs does NOT:
- Decide policy outcomes (→ Policies domain)
- Create incidents (→ Incidents domain)
- Orchestrate recovery (→ ROK/Orchestrator)
- Mutate historical records (→ NEVER)

---

## Locked Artifacts

### L4 Engines (31 files → 27 after quarantine)

| Layer | File | Status | Lock Date | Notes |
|-------|------|--------|-----------|-------|
| L4 | `engines/replay_determinism.py` | LOCKED | 2026-01-24 | Determinism definitions (INV-LOGS-003) |
| L4 | `engines/reconciler.py` | LOCKED | 2026-01-24 | Audit reconciliation |
| L4 | `engines/durability.py` | LOCKED | 2026-01-24 | Audit durability |
| L4 | `engines/completeness_checker.py` | LOCKED | 2026-01-24 | Compliance checking |
| L4 | `engines/certificate.py` | LOCKED | 2026-01-24 | Certificate generation |
| L4 | `engines/evidence_report.py` | LOCKED | 2026-01-24 | Evidence reporting |
| L4 | `engines/logs_read_service.py` | LOCKED | 2026-01-24 | Logs read operations |
| L4 | `engines/__init__.py` | LOCKED | 2026-01-24 | Engine exports |
| L4 | (remaining stubs) | LOCKED | 2026-01-24 | Various facades |

### L6 Database Drivers (16 files)

| Layer | File | Status | Lock Date | Notes |
|-------|------|--------|-----------|-------|
| L6 | `drivers/pg_store.py` | LOCKED | 2026-01-24 | PostgreSQL store |
| L6 | `drivers/traces_store.py` | LOCKED | 2026-01-24 | Trace storage |
| L6 | `drivers/audit_store.py` | LOCKED | 2026-01-24 | Audit storage |
| L6 | `drivers/integrity.py` | LOCKED | 2026-01-24 | Integrity checks |
| L6 | `drivers/idempotency.py` | LOCKED | 2026-01-24 | Idempotency handling |
| L6 | `drivers/alert_fatigue.py` | LOCKED | 2026-01-24 | Alert fatigue |
| L6 | `drivers/job_execution.py` | LOCKED | 2026-01-24 | Job execution tracking |
| L6 | `drivers/__init__.py` | LOCKED | 2026-01-24 | Driver exports |

### L4 Facades (3 files)

| Layer | File | Status | Lock Date | Notes |
|-------|------|--------|-----------|-------|
| L4 | `facades/trace_facade.py` | LOCKED | 2026-01-24 | Trace facade |
| L4 | `facades/evidence_facade.py` | LOCKED | 2026-01-24 | Evidence facade |
| L4 | `facades/logs_facade.py` | LOCKED | 2026-01-24 | Logs domain facade (LLM_RUNS, SYSTEM_LOGS, AUDIT) — RESTORED & SPLIT |
| L4 | `facades/__init__.py` | LOCKED | 2026-01-24 | Facade exports |

### L3 Adapters (1 file)

| Layer | File | Status | Lock Date | Notes |
|-------|------|--------|-----------|-------|
| L3 | `adapters/export_bundle_adapter.py` | LOCKED | 2026-01-24 | Export bundle adapter (SOC2, evidence) — RESTORED & SPLIT |
| L3 | `adapters/__init__.py` | LOCKED | 2026-01-24 | Adapter exports |

### L6 Drivers — New from Restoration (2 files)

| Layer | File | Status | Lock Date | Notes |
|-------|------|--------|-----------|-------|
| L6 | `drivers/logs_domain_store.py` | LOCKED | 2026-01-24 | Logs domain DB driver — extracted from logs_facade.py |
| L6 | `drivers/export_bundle_store.py` | LOCKED | 2026-01-24 | Export bundle DB driver — extracted from export_bundle_service.py |

### Quarantined Files (in customer/duplicates/)

| File | Original Location | Reason | Action |
|------|-------------------|--------|--------|
| `cost_anomaly_detector.py` | logs/engines/ | Decision logic ("Was this anomalous?") | Reassign to analytics |
| `pattern_detection.py` | logs/engines/ | Decision logic ("Is this a pattern?") | Reassign to analytics |
| `api.py` | logs/engines/ | DEPRECATED - L2 route misplaced | Archive |
| `M17_internal_worker.py` | logs/engines/ | DEPRECATED - L2 route misplaced | Archive |

### Restored Files (no longer quarantined)

| File | Restored As | Reason |
|------|-------------|--------|
| `logs_facade.py` | `facades/logs_facade.py` + `drivers/logs_domain_store.py` | CORE LOGS FUNCTION — LLM_RUNS, SYSTEM_LOGS, AUDIT operations |
| `export_bundle_service.py` | `adapters/export_bundle_adapter.py` + `drivers/export_bundle_store.py` | CORE LOGS FUNCTION — Evidence export, SOC2 compliance |

---

## Governance Invariants

| ID | Rule | Enforcement |
|----|------|-------------|
| **INV-LOGS-001** | Logs Never Decides Outcomes | LOCKED |
| **INV-LOGS-002** | Logs Is Append-Only in Spirit | LOCKED |
| **INV-LOGS-003** | Determinism Definitions Live Here Exclusively | LOCKED |
| **INV-LOGS-004** | Compliance Exports Must Be Reproducible | LOCKED |
| **INV-LOGS-005** | Facades Are Composition-Only | LOCKED |

---

## L4/L6 Contract Summary

### L4 Engines

L4 engines in logs domain:
- Define determinism semantics (hashing, ordering, replay)
- Compose evidence chains
- Validate completeness (fact check, not decision)
- Generate compliance reports

L4 engines do NOT:
- Import `sqlalchemy`, `sqlmodel`, `AsyncSession`
- Contain raw SQL queries
- Make decisions ("Was this anomalous?", "Is this a pattern?")

### L6 Drivers

L6 drivers in logs domain:
- Pure data access
- Return snapshots not ORM models
- No business logic

---

## Freeze Rules

### Prohibited Actions (Without Explicit Unlock)

1. **Refactors** — No structural changes to locked files
2. **Renames** — No file or method renames
3. **Extractions** — No additional driver/adapter extractions
4. **Cross-Domain Modifications** — No changes to bridge call sites
5. **Import Changes** — No new cross-domain imports
6. **Restore from Quarantine** — Cannot restore quarantined files without approval

### Permitted Actions

1. **Bug Fixes** — Critical fixes only, with change record
2. **CI Enforcement** — Layer segregation workflow remains authoritative
3. **Documentation** — Non-code updates to audit/lock files

### Unlock Procedure

To modify locked artifacts:
1. Issue explicit unlock command: `"Unlock Logs Domain for [reason]"`
2. Specify scope of modification
3. Re-run post-extraction audit after changes
4. Re-lock with updated artifacts

---

## Transitional Debt Registry

**Status:** NONE

All violating files were quarantined, not marked with transitional debt.
Zero transitional debt per founder guidance.

---

## Verification Summary

### BLCA Results

```
Layer Validator (PIN-240)
Scanning: backend
Files scanned: 2060
Violations found: 0

No layer violations found!
Layer architecture is clean.
```

### Quarantine Summary

| Category | Files | Status |
|----------|-------|--------|
| Decision Logic (wrong domain) | 2 | Quarantined |
| Deprecated (misplaced L2) | 2 | Quarantined |
| **Total Quarantined** | **4** | — |

### Restoration Summary

| Category | Files | Status |
|----------|-------|--------|
| Core Logs Function (L4/L6 split) | 2 | RESTORED |
| **Total Restored** | **2** | — |

**Restoration Rationale:** Files were incorrectly classified as "orphans" based on caller graph. Per HOC Migration Plan, the invariant for domain ownership is **core function**, not caller graph. Wiring happens in Phase 4.

---

## Audit Trail

| Phase | Scope | Status | Date |
|-------|-------|--------|------|
| 2.5B-P1 | Intent classification, headers | COMPLETE | 2026-01-24 |
| 2.5B-P2 | Quarantine decision-logic files | COMPLETE | 2026-01-24 |
| 2.5B-P3 | Quarantine orphan/deprecated files | COMPLETE | 2026-01-24 |
| POST-AUDIT | Full domain BLCA | PASS | 2026-01-24 |
| CLOSURE | Domain lock | FINAL | 2026-01-24 |
| 2.5B-RESTORE | Restore incorrectly quarantined files | COMPLETE | 2026-01-24 |
| 2.5B-SPLIT | L4/L6 layer separation for restored files | COMPLETE | 2026-01-24 |
| POST-RESTORE-AUDIT | Full domain BLCA | PASS (0 violations) | 2026-01-24 |
| HEADERS | Add AUDIENCE headers to 9 driver files | COMPLETE | 2026-01-24 |
| INTENT-FREEZE | Intent comments for 3 gray-zone files | COMPLETE | 2026-01-24 |
| FORMAL-LOCK | Domain formally locked | **LOCKED** | 2026-01-24 |

---

## Reviewed Gray-Zone Files

Three L6 driver files were identified during audit as containing patterns that MIGHT constitute
decision logic. After review, each was determined to be L6-compliant with INTENT FREEZE comments added.

### job_execution.py

| Aspect | Finding |
|--------|---------|
| **Pattern Found** | Retry strategies (exponential, fibonacci, linear) |
| **Assessment** | NOT a business decision |
| **Rationale** | Implements HOW retries are computed (timing math), not WHETHER to retry. The decision to retry is made by L5 engines via `RetryConfig` passed from callers. |
| **L6 Compliance** | Pure execution mechanics |

### redact.py

| Aspect | Finding |
|--------|---------|
| **Pattern Found** | PII regex patterns for passwords, cards, tokens |
| **Assessment** | NOT a business decision |
| **Rationale** | Implements SECURITY RULES based on industry-standard PII categories (GDPR/SOC2 compliance), not business policy. The patterns are fixed and deterministic. |
| **L6 Compliance** | Pure data transformation with fixed rules |

### pg_store.py

| Aspect | Finding |
|--------|---------|
| **Pattern Found** | `_status_to_level()` maps status → log level |
| **Assessment** | NOT a business decision |
| **Rationale** | Implements a FIXED MAPPING per PIN-378 (Canonical Logs System). The mapping (success→INFO, failure→ERROR, retry→WARN) is deterministic and policy-free. |
| **L6 Compliance** | Pure data access and fixed transformation |

### Verdict

All three files are **L6-compliant**. The patterns are:
- Execution mechanics (job_execution.py)
- Security standards (redact.py)
- Fixed mappings (pg_store.py)

None contain business decisions like "should this incident be critical?" or "should this policy apply?".

---

## Related Documents

| Document | Location |
|----------|----------|
| Implementation Plan | `docs/architecture/hoc/implementation/LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md` |
| HOC Layer Topology | `docs/architecture/HOC_LAYER_TOPOLOGY_V1.md` |
| HOC Index | `docs/architecture/hoc/INDEX.md` |
| Quarantine Directory | `backend/app/houseofcards/customer/duplicates/` |
| Logs Analysis | `docs/architecture/hoc/analysis/HOC_logs_analysis_v1.md` |

---

## Changelog

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-24 | 1.0.0 | Initial lock | Claude |
| 2026-01-24 | 1.1.0 | Restored logs_facade.py and export_bundle_service.py with L4/L6 split | Claude |
| 2026-01-24 | 1.2.0 | Added AUDIENCE headers (9 files), Intent Freeze (3 files), Gray-Zone review | Claude |
| 2026-01-24 | 1.3.0 | Phase 2.5D HEADER_CLAIM_MISMATCH fixes (6 files L6→L5) | Claude |
| 2026-01-24 | 1.4.0 | Phase 2.5E BLCA verification: 0 errors, 0 warnings across all 6 check types | Claude |

---

## BLCA Compliance Fixes (Phase 2.5D)

### HEADER_CLAIM_MISMATCH Fixes (2026-01-24)

Files claiming L6 (Driver) but containing no sqlalchemy/sqlmodel runtime imports were reclassified to L5 (Domain Engine) per HOC Layer Topology V1.

| File | Original Layer | New Layer | Rationale |
|------|----------------|-----------|-----------|
| `drivers/audit_evidence.py` | L6 | **L5** | Pure audit event emission, no DB ops |
| `drivers/traces_models.py` | L6 | **L5** | Pure dataclass definitions, no DB ops |
| `drivers/traces_metrics.py` | L6 | **L5** | Prometheus metrics utilities, no DB ops |
| `drivers/redact.py` | L6 | **L5** | Pure data transformation (PII redaction), no DB ops |
| `drivers/alert_fatigue.py` | L6 | **L5** | Redis infrastructure (not SQL), no DB ops |
| `drivers/pdf_renderer.py` | L6 | **L5** | Pure PDF rendering logic, no DB ops |

**NOTE:** Files remain in `drivers/` directory per "Layer ≠ Directory" principle.
Each file has `# NOTE: Reclassified L6→L5` header comment documenting the change.

**BLCA Status:** 0 CUSTOMER HEADER_CLAIM_MISMATCH errors for logs domain.

---

**END OF DOMAIN LOCK**
