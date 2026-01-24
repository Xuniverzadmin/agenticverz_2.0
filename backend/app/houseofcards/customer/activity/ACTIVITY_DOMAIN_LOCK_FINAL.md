# Activity Domain Lock — FINAL
# Status: LOCKED
# Effective: 2026-01-24
# Reference: Phase-2.5A Activity Extraction (ACTIVITY_PHASE2.5_IMPLEMENTATION_PLAN.md)

---

## Domain Status

**LOCKED** — No modifications permitted without explicit unlock command.

---

## Locked Artifacts

### L4 Decision Engines

| Layer | File | Status | Lock Date | Notes |
|-------|------|--------|-----------|-------|
| L4 | `engines/threshold_engine.py` | LOCKED | 2026-01-24 | Threshold resolution & evaluation logic |
| L4 | `engines/signal_feedback_service.py` | LOCKED | 2026-01-24 | Stub - no DB dependency |
| L4 | `engines/attention_ranking_service.py` | LOCKED | 2026-01-24 | Stub - no DB dependency |
| L4 | `engines/pattern_detection_service.py` | LOCKED | 2026-01-24 | Stub - no DB dependency |
| L4 | `engines/cost_analysis_service.py` | LOCKED | 2026-01-24 | Stub - no DB dependency |
| L4 | `engines/signal_identity.py` | LOCKED | 2026-01-24 | Signal identity utilities |
| L4 | `engines/__init__.py` | LOCKED | 2026-01-24 | Engine exports |

### L6 Database Drivers

| Layer | File | Status | Lock Date | Notes |
|-------|------|--------|-----------|-------|
| L6 | `drivers/threshold_driver.py` | LOCKED | 2026-01-24 | Threshold limit DB operations |
| L6 | `drivers/activity_enums.py` | LOCKED | 2026-01-24 | Activity domain enumerations |
| L6 | `drivers/__init__.py` | LOCKED | 2026-01-24 | Driver exports |

### Deprecated Files

| File | Status | Notes |
|------|--------|-------|
| `drivers/llm_threshold_service.py.deprecated` | DEPRECATED | Original mixed L4/L6 file, replaced by engine+driver split |

---

## L4/L6 Contract Summary

### Threshold Engine (L4)

The threshold engine owns:
- `ThresholdParams`, `ThresholdParamsUpdate` — Decision contracts
- `ThresholdSignal` — Signal enum
- `LLMRunThresholdResolver` — Precedence resolution logic
- `LLMRunEvaluator` — Threshold evaluation logic
- Signal record helpers

The engine does NOT import:
- `sqlalchemy`, `sqlmodel`, `AsyncSession`

### Threshold Driver (L6)

The threshold driver owns:
- `LimitSnapshot` — Return type for driver queries
- `ThresholdDriver` — Async DB operations
- `ThresholdDriverSync` — Sync DB operations
- Signal emission functions

The driver does NOT contain:
- Precedence logic (`if scope == "AGENT"` patterns)
- Evaluation logic (threshold comparison)

---

## Freeze Rules

### Prohibited Actions (Without Explicit Unlock)

1. **Refactors** — No structural changes to locked files
2. **Renames** — No file or method renames
3. **Extractions** — No additional driver/adapter extractions
4. **Cross-Domain Modifications** — No changes to bridge call sites
5. **Import Changes** — No new cross-domain imports

### Permitted Actions

1. **Bug Fixes** — Critical fixes only, with change record
2. **CI Enforcement** — Layer segregation workflow remains authoritative
3. **Documentation** — Non-code updates to audit/lock files

### Unlock Procedure

To modify locked artifacts:
1. Issue explicit unlock command: `"Unlock Activity Domain for [reason]"`
2. Specify scope of modification
3. Re-run post-extraction audit after changes
4. Re-lock with updated artifacts

---

## Transitional Debt Registry

**Status:** NONE

All extractions completed with zero transitional debt per user approval.

---

## Verification Summary

### Phase 1: Engine Stub Cleanup

| Task | File | Fix | Status |
|------|------|-----|--------|
| ACT-001 | `signal_feedback_service.py` | Removed unused AsyncSession | COMPLETE |
| ACT-002 | `attention_ranking_service.py` | Removed unused AsyncSession | COMPLETE |
| ACT-003 | `pattern_detection_service.py` | Removed unused AsyncSession | COMPLETE |
| ACT-004 | `cost_analysis_service.py` | Removed unused AsyncSession | COMPLETE |
| ACT-005 | BLCA verification | 0 violations | PASS |

### Phase 2: Driver/Engine Split

| Task | Description | Status |
|------|-------------|--------|
| ACT-006 | Create `threshold_engine.py` (L4) | COMPLETE |
| ACT-007 | Create `threshold_driver.py` (L6) | COMPLETE |
| ACT-008 | Update imports in callers | COMPLETE |
| ACT-009 | BLCA verification | PASS (0 violations) |
| ACT-010 | Create domain lock | THIS DOCUMENT |

### BLCA Results

```
Layer Validator (PIN-240)
Scanning: backend/app/houseofcards/customer/activity
Files scanned: 15
Violations found: 0

No layer violations found!
Layer architecture is clean.
```

---

## Callers Updated

The following files were updated to use the new module paths:

| File | Imports From |
|------|--------------|
| `app/worker/runner.py` | `threshold_engine` (L4), `threshold_driver` (L6) |
| `app/houseofcards/internal/analytics/engines/runner.py` | `threshold_engine` (L4), `threshold_driver` (L6) |
| `app/api/policy_limits_crud.py` | `threshold_engine` (L4) |
| `app/houseofcards/api/customer/policies/policy_limits_crud.py` | `threshold_engine` (L4) |

---

## Audit Trail

| Phase | Scope | Status | Date |
|-------|-------|--------|------|
| 2.5A-P1 | Engine stub cleanup (4 files) | COMPLETE | 2026-01-24 |
| 2.5A-P2 | Driver/Engine split | COMPLETE | 2026-01-24 |
| 2.5A-P3 | Caller updates | COMPLETE | 2026-01-24 |
| POST-AUDIT | Full domain BLCA | PASS | 2026-01-24 |
| CLOSURE | Domain lock | FINAL | 2026-01-24 |

---

## Related Documents

| Document | Location |
|----------|----------|
| Implementation Plan | `docs/architecture/hoc/implementation/ACTIVITY_PHASE2.5_IMPLEMENTATION_PLAN.md` |
| HOC Layer Topology | `docs/architecture/HOC_LAYER_TOPOLOGY_V1.md` |
| Driver-Engine Contract | `backend/app/houseofcards/DRIVER_ENGINE_CONTRACT.md` |
| Activity Audit Report | `backend/app/houseofcards/customer/activity/HOC_activity_deep_audit_report.md` |

---

## Changelog

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-24 | 1.0.0 | Initial lock | Claude |

---

**END OF DOMAIN LOCK**
