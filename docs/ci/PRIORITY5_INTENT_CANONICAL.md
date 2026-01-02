# Priority-5 Canonical Intent Table

**Status:** FROZEN
**Effective:** 2026-01-01
**Reference:** PIN-265 (Phase-3 Intent-Driven Refactoring)
**CI Guard:** `priority5-intent-guard` in `.github/workflows/ci.yml`

---

## Purpose

This document defines the **canonical intent declarations** for all Priority-5 (CRITICAL blast radius) files.

These declarations are:
- **Frozen** - changes require founder ratification
- **CI-enforced** - `check_priority5_intent.py` blocks regressions
- **Semantically validated** - each intent reflects actual production behavior

---

## Why Priority-5?

Priority-5 files have the highest blast radius in the system:

| Category | Impact if Intent Wrong |
|----------|------------------------|
| Workers | Hung jobs, orphaned state, silent data loss |
| Circuit Breakers | Cascading failures, false positives, system instability |
| Recovery Services | Lost recovery opportunities, duplicate actions, infinite loops |

These are not "important files" - they are **system-critical control paths**.

---

## Canonical Intent Table

### Worker Layer (5 files)

| File | FeatureIntent | RetryPolicy | Rationale |
|------|---------------|-------------|-----------|
| `worker/runner.py` | RECOVERABLE_OPERATION | SAFE | Orchestrates run lifecycle with checkpointing; must resume on crash |
| `worker/outbox_processor.py` | RECOVERABLE_OPERATION | SAFE | Outbox pattern makes side effects effectively retriable via DB guarantee |
| `worker/pool.py` | STATE_MUTATION | SAFE | Manages worker pool state; atomic updates, no external calls |
| `worker/recovery_claim_worker.py` | RECOVERABLE_OPERATION | SAFE | Claims recovery candidates with FOR UPDATE SKIP LOCKED; released on shutdown |
| `worker/recovery_evaluator.py` | RECOVERABLE_OPERATION | SAFE | L5 executor for recovery actions; atomic UPDATE with exactly-once guarantee |

### Circuit Breaker (3 files)

| File | FeatureIntent | RetryPolicy | Rationale |
|------|---------------|-------------|-----------|
| `costsim/circuit_breaker.py` | STATE_MUTATION | SAFE | DB-backed state tracking with SELECT FOR UPDATE; atomic transitions |
| `costsim/circuit_breaker_async.py` | STATE_MUTATION | SAFE | Async variant; same atomic guarantees |
| `costsim/alert_worker.py` | EXTERNAL_SIDE_EFFECT | NEVER | Sends to Alertmanager; HTTP calls are non-deterministic |

### Recovery Services (4 files)

| File | FeatureIntent | RetryPolicy | Rationale |
|------|---------------|-------------|-----------|
| `services/orphan_recovery.py` | STATE_MUTATION | SAFE | Updates run status to "crashed"; factual state mutation, no external deps |
| `services/recovery_matcher.py` | EXTERNAL_SIDE_EFFECT | NEVER | Escalates to LLM; responses cannot be safely retried |
| `services/recovery_write_service.py` | STATE_MUTATION | SAFE | DB writes with ON CONFLICT DO UPDATE; explicit transaction boundaries |
| `tasks/recovery_queue_stream.py` | RECOVERABLE_OPERATION | SAFE | Redis Streams with XCLAIM for stalled message recovery |

---

## Intent Definitions (Reference)

| FeatureIntent | Meaning | Typical Use |
|---------------|---------|-------------|
| `PURE_QUERY` | Read-only, no side effects | Reports, lookups |
| `STATE_MUTATION` | DB writes, atomic, deterministic | CRUD, status updates |
| `EXTERNAL_SIDE_EFFECT` | Non-deterministic external calls | LLM, webhooks, alerts |
| `RECOVERABLE_OPERATION` | Designed for crash recovery | Workers, queues, orchestrators |

| RetryPolicy | Meaning | When Required |
|-------------|---------|---------------|
| `SAFE` | Can retry without semantic change | STATE_MUTATION, RECOVERABLE_OPERATION |
| `NEVER` | Retry may cause duplicate effects | EXTERNAL_SIDE_EFFECT |
| `DANGEROUS` | Retry is possible but risky | Rare, requires explicit justification |

---

## Change Protocol

**Changes to Priority-5 intent declarations require:**

1. **Founder ratification** - not team consensus
2. **Written justification** - why the original intent was wrong
3. **CI override** - `PRIORITY5_REOPEN` flag in commit message
4. **Re-freeze** - updated canonical table after change

**Allowed without ratification:**
- Adding new Priority-5 files (extends the table)
- Bug fixes that don't change intent semantics

---

## CI Enforcement

The `priority5-intent-guard` job in CI:

1. Checks all 12 files exist
2. Verifies FEATURE_INTENT matches canonical value
3. Verifies RETRY_POLICY matches canonical value
4. **Blocks merge** if any mismatch detected

Script: `backend/scripts/ci/check_priority5_intent.py`

---

## History

| Date | Action | Reference |
|------|--------|-----------|
| 2026-01-01 | Initial freeze (12 files) | PIN-265, Phase-3 Batch-1 |

---

## See Also

- PIN-264: Phase-2.3 Feature Intent System
- PIN-265: Phase-3 Intent-Driven Refactoring
- `backend/app/infra/feature_intent.py`: Intent enums and validation
- `backend/scripts/ci/check_feature_intent.py`: Full violation scanner
