# PIN-381: SDSR E2E Testing Protocol Implementation

**Status:** 📋 ACTIVE
**Created:** 2026-01-10
**Category:** SDSR / E2E Testing
**Milestone:** SDSR-E2E

---

## Summary

Complete chronology of SDSR E2E testing infrastructure implementation, from protocol design through scenario certification

---

## Details

## Overview

This PIN documents the implementation of the SDSR (Scenario-Driven System Realization) E2E Testing Protocol, establishing a production-grade testing infrastructure for backend-first causality validation.

## Chronology of Implementation

### Phase 1: Protocol Foundation

**Governance Document Created:**
- `docs/governance/SDSR_E2E_TESTING_PROTOCOL.md`
- Established 6 hard guardrails (GR-1 through GR-6)
- Defined Schema Reality Gates (SR-1, SR-2, SR-3)
- Specified verification checklist format

**Core Principles Locked:**
- UI is observational only
- Backend execution is source of truth
- Validate: Activity → Incident → Policy Proposal → Logs

### Phase 2: Schema Migrations

**Migration 079: SDSR Column Parity**
- Added `is_synthetic` and `synthetic_scenario_id` to all relevant tables
- Tables: runs, incidents, policy_proposals, aos_traces, aos_trace_steps

**Migration 080: Trace Archival Columns**
- Added `archived_at` to aos_traces and aos_trace_steps
- Created partial indexes for efficient exclusion queries
- Enabled soft-archive pattern for S6 immutability compliance

### Phase 3: Injection Infrastructure

**inject_synthetic.py Contract:**
- Rule 1: No intelligence (fail loudly on missing fields)
- Rule 2: No engine bypass (only inject causes)
- Rule 3: Every row traceable (is_synthetic=true, synthetic_scenario_id set)
- Rule 4: One scenario = one transaction
- Section 6: S6 immutability compliance (archive traces, don't delete)

**SDSR Identity Rule (PIN-379):**
- run_id must be execution-unique
- Format: `run-{scenario_id}-{UTC_YYYYMMDDTHHMMSSZ}`
- Prevents trace_id conflicts on re-execution

### Phase 4: Preflight Hardening

**SR-1: Migration Consistency Check**
- `backend/scripts/preflight/sr1_migration_check.py`
- Uses Alembic runtime APIs (no CLI parsing)
- Verifies single head, current revision matches

**SR-2: Required Columns Assertion**
- Validates all SDSR columns exist
- Hard failure if any missing

**SR-3: Worker Version Check**
- Capability-based validation (not path-specific)
- Checks TraceStore integration present

**RG-SDSR-01: Execution Identity Guard**
- `backend/scripts/preflight/rg_sdsr_execution_identity.py`
- Exit code 4 on run_id reuse
- LOCKED CONTRACT: No auto-fix, no bypass

### Phase 5: Observability

**Trace Metrics Added:**
- `aos_traces_active_total` (archived_at IS NULL)
- `aos_traces_archived_total` (archived_at IS NOT NULL)
- `aos_trace_steps_active_total`
- `aos_trace_steps_archived_total`

Read-only, zero side effects, updates immediately after cleanup.

### Phase 6: Baseline Freeze

**Tag: sdsr-e2e-stable-1**
- Frozen known-good contract
- Reference point for regression detection

### Phase 7: Scenario Certification

**SDSR-E2E-001: Failed Activity Propagation**
- Intent: Failed run → Incident → Policy Proposal → Logs
- Status: CERTIFIED
- Validates full backend-first causality

**SDSR-E2E-002: Success Path Negative Test**
- Intent: Successful run → NO Incident → NO Proposal
- Status: CERTIFIED
- Validates engine selectivity (only fire on failure)

## Key Files

| File | Purpose |
|------|---------|
| `docs/governance/SDSR_E2E_TESTING_PROTOCOL.md` | Protocol specification |
| `docs/governance/WHY_SDSR_EXECUTION_WORKS.md` | Design rationale |
| `backend/scripts/sdsr/inject_synthetic.py` | Scenario injection |
| `backend/scripts/preflight/sdsr_e2e_preflight.sh` | Full preflight suite |
| `backend/scripts/preflight/sr1_migration_check.py` | Migration consistency |
| `backend/scripts/preflight/rg_sdsr_execution_identity.py` | Identity guard |
| `backend/scripts/sdsr/scenarios/SDSR-E2E-001.yaml` | Failure scenario |
| `backend/scripts/sdsr/scenarios/SDSR-E2E-002.yaml` | Success scenario |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation error (SR-1 fail, missing columns) |
| 2 | Partial write detected |
| 3 | Guardrail violation |
| 4 | RG-SDSR-01: Identity reuse (HARD FAIL) |

## Invariants Established

1. **Identity Safety:** run_id reuse is impossible
2. **Immutability:** Traces are append-only; cleanup archives, never deletes
3. **Cleanup Truthfulness:** Fails loudly; no silent no-ops
4. **Preflight Determinism:** SR-1/2/3 are semantic, not CLI-based
5. **Observability:** Archived vs active counts available

## Next Scenarios (Candidates)

- SDSR-E2E-003: Incident severity thresholds
- SDSR-E2E-004: Policy proposal approval/rejection
- SDSR-E2E-005: Worker execution with trace generation


---

## Scenario Classification

### Update (2026-01-10)

## Scenario Classification (MANDATORY)

### Execution Modes

| Mode | Description |
|------|-------------|
| **WORKER_EXECUTION** | Run goes through worker, traces generated |
| **STATE_INJECTION** | State directly injected, bypasses worker |

### Coverage Matrix

| Scenario | Class | Worker Exec | Traces | Engine Validation |
|----------|-------|-------------|--------|-------------------|
| SDSR-E2E-001 | STATE_INJECTION | ❌ | ❌ (injected) | ✅ Failure propagation |
| SDSR-E2E-002 | STATE_INJECTION | ❌ | ❌ | ✅ Non-propagation |
| SDSR-E2E-005 | WORKER_EXECUTION | ✅ | ✅ | ✅ Success path |

### Correct Execution Order

1. ✅ SDSR-E2E-001 — Failure → Incident → Policy (STATE_INJECTION)
2. ✅ SDSR-E2E-002 — Success → No Incident/Policy (STATE_INJECTION)
3. 🔜 SDSR-E2E-005 — Success + Worker + Traces (WORKER_EXECUTION)
4. 🔜 SDSR-E2E-003 — Incident severity thresholds
5. 🔜 SDSR-E2E-004 — Policy approval/rejection

**Rule:** SDSR-E2E-005 MUST complete before SDSR-E2E-003/004.

### Gap Closed

SDSR-E2E-002 was previously ambiguous. It is now explicitly classified as:
- scenario_class: STATE_INJECTION
- execution_mode: non_executable
- coverage.trace_generation: false

This prevents future misinterpretation that "success path is trace-validated".

## Related PINs

- PIN-370: SDSR Architecture
- PIN-379: SDSR E2E Protocol
