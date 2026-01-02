# PIN-265: Phase-3 Intent-Driven Refactoring Plan

**Status:** IN_PROGRESS
**Date:** 2025-12-31
**Category:** Architecture / Debt Paydown
**Related PINs:** PIN-264 (Phase-2.3 Feature Intent System)

---

## Summary

Phase-3 systematically fixes the 128 FEATURE_INTENT violations discovered by the Phase-2.3 CI enforcement. Violations are clustered by feature group and prioritized by blast radius.

## Governing Principles

1. **Fix by feature group, not by file** — exposes design intent
2. **One group per commit** — atomic, reviewable changes
3. **Monotonic convergence** — violation count must decrease, never increase
4. **No regression** — once a group is fixed, it stays fixed (CI enforced)
5. **Education, not annotation** — each fix teaches correct patterns

## Violation Summary

**Total: 128 violations**

| Priority | Blast Radius | Files | Domain |
|----------|--------------|-------|--------|
| 5 | CRITICAL | 12 | Workers, Circuit Breakers, Recovery |
| 4 | HIGH | 8 | Jobs, Tasks, Optimization |
| 3 | MEDIUM | 37 | Policy, Workflow, Memory, Services |
| 2 | LOW | 27 | API routes |
| 1 | MINIMAL | 44 | Models, Utils, Auth, Skills |

---

## Priority 5 (CRITICAL) — Fix First

**Domain:** Production safety — workers, circuit breakers, recovery

### Files (12)

```
worker/
├── outbox_processor.py
├── pool.py
├── recovery_claim_worker.py
├── recovery_evaluator.py
└── runner.py

costsim/
├── circuit_breaker.py
├── circuit_breaker_async.py
└── alert_worker.py

services/
├── orphan_recovery.py
├── recovery_matcher.py
└── recovery_write_service.py

tasks/
└── recovery_queue_stream.py
```

### Expected Intent Patterns

| File Pattern | FeatureIntent | TransactionIntent | RetryPolicy |
|--------------|---------------|-------------------|-------------|
| `*_worker.py` | RECOVERABLE_OPERATION | LOCKED_MUTATION | SAFE |
| `circuit_breaker*.py` | STATE_MUTATION | LOCKED_MUTATION | SAFE |
| `recovery_*.py` | RECOVERABLE_OPERATION | LOCKED_MUTATION | SAFE |
| `outbox_processor.py` | EXTERNAL_SIDE_EFFECT | ATOMIC_WRITE | NEVER |

---

## Priority 4 (HIGH) — Background Processing

**Domain:** Jobs, tasks, optimization coordination

### Files (8)

```
jobs/
├── failure_aggregation.py
├── failure_classification_engine.py
├── graduation_evaluator.py
└── storage.py

tasks/
├── m10_metrics_collector.py
└── recovery_queue_stream.py

optimization/
├── audit_persistence.py
└── coordinator.py
```

### Expected Intent Patterns

| File Pattern | FeatureIntent | TransactionIntent | RetryPolicy |
|--------------|---------------|-------------------|-------------|
| `*_aggregation.py` | STATE_MUTATION | ATOMIC_WRITE | SAFE |
| `*_evaluator.py` | STATE_MUTATION | LOCKED_MUTATION | SAFE |
| `coordinator.py` | STATE_MUTATION | LOCKED_MUTATION | SAFE |

---

## Priority 3 (MEDIUM) — Domain Engines

**Domain:** Policy, workflow, memory, core services

### Files (37)

```
costsim/          (2 files: leader.py, provenance_async.py)
policy/           (4 files: engine.py, optimizer/*)
workflow/         (3 files: canonicalize.py, checkpoint.py, planner_sandbox.py)
memory/           (5 files: iaec.py, memory_service.py, retriever.py, store.py, vector_store.py)
integrations/     (5 files)
services/         (18 files)
```

### Expected Intent Patterns

| File Pattern | FeatureIntent | TransactionIntent | RetryPolicy |
|--------------|---------------|-------------------|-------------|
| `*_service.py` | STATE_MUTATION | ATOMIC_WRITE | SAFE |
| `engine.py` | STATE_MUTATION | ATOMIC_WRITE | — |
| `store.py` | STATE_MUTATION | ATOMIC_WRITE | SAFE |
| `retriever.py` | PURE_QUERY | READ_ONLY | — |

---

## Priority 2 (LOW) — API Layer

**Domain:** REST endpoints (thin layer over services)

### Files (27)

All files in `app/api/` plus `app/predictions/api.py`

### Expected Intent Patterns

| File Pattern | FeatureIntent | TransactionIntent | RetryPolicy |
|--------------|---------------|-------------------|-------------|
| `app/api/*.py` | STATE_MUTATION | ATOMIC_WRITE | — |
| Read-only endpoints | PURE_QUERY | READ_ONLY | — |

---

## Priority 1 (MINIMAL) — Declarations & Utilities

**Domain:** Models, utils, auth, skills

### Files (44)

```
models/           (7 files)
utils/            (6 files)
auth/             (3 files)
agents/           (12 files)
skills/           (3 files)
misc/             (13 files)
```

### Expected Intent Patterns

Most models may need reclassification — they declare tables but don't typically mutate.

---

## Fix Workflow

### Per-Batch Process

1. **Analyze** — Read each file, determine correct FeatureIntent
2. **Declare** — Add `FEATURE_INTENT` and `RETRY_POLICY` at module level
3. **Verify** — Run `check_feature_intent.py` on the group
4. **Commit** — `feat(intent): add FEATURE_INTENT to {group}`
5. **Lock** — Add group to "fixed" baseline (no regression)

### Commit Pattern

```
feat(intent): add FEATURE_INTENT to worker/*

- worker/outbox_processor.py: EXTERNAL_SIDE_EFFECT + NEVER
- worker/pool.py: STATE_MUTATION + SAFE
- worker/recovery_claim_worker.py: RECOVERABLE_OPERATION + SAFE
- worker/recovery_evaluator.py: RECOVERABLE_OPERATION + SAFE
- worker/runner.py: STATE_MUTATION + SAFE

Violation count: 128 → 123 (-5)
```

---

## Progress Tracking

| Batch | Priority | Files | Status | Violations After |
|-------|----------|-------|--------|------------------|
| 1 | 5 (CRITICAL) | 12 | FROZEN | 128 (baseline) |
| 2 | 4 (HIGH) | 7 | FROZEN | 121 |
| 3 | 3 (MEDIUM) | 37 | PENDING | — |
| 4 | 2 (LOW) | 27 | PENDING | — |
| 5 | 1 (MINIMAL) | 44 | PENDING | — |

### Batch-1 Completion (2026-01-01)

**Status:** FROZEN
**CI Guard:** `priority5-intent-guard`
**Canonical Table:** `docs/ci/PRIORITY5_INTENT_CANONICAL.md`

Files fixed:
- worker/runner.py → RECOVERABLE_OPERATION + SAFE
- worker/outbox_processor.py → RECOVERABLE_OPERATION + SAFE
- worker/pool.py → STATE_MUTATION + SAFE
- worker/recovery_claim_worker.py → RECOVERABLE_OPERATION + SAFE
- worker/recovery_evaluator.py → RECOVERABLE_OPERATION + SAFE
- costsim/circuit_breaker.py → STATE_MUTATION + SAFE
- costsim/circuit_breaker_async.py → STATE_MUTATION + SAFE
- costsim/alert_worker.py → EXTERNAL_SIDE_EFFECT + NEVER
- services/orphan_recovery.py → STATE_MUTATION + SAFE
- services/recovery_matcher.py → EXTERNAL_SIDE_EFFECT + NEVER
- services/recovery_write_service.py → STATE_MUTATION + SAFE
- tasks/recovery_queue_stream.py → RECOVERABLE_OPERATION + SAFE

### Batch-2 Completion (2026-01-01)

**Status:** FROZEN
**CI Guard:** `priority4-intent-guard`
**Violations:** 128 → 121 (−7)

Files fixed:
- jobs/failure_aggregation.py → EXTERNAL_SIDE_EFFECT + NEVER
- jobs/failure_classification_engine.py → PURE_QUERY
- jobs/graduation_evaluator.py → STATE_MUTATION + SAFE
- jobs/storage.py → EXTERNAL_SIDE_EFFECT + NEVER
- optimization/audit_persistence.py → STATE_MUTATION + SAFE
- optimization/coordinator.py → STATE_MUTATION + SAFE
- tasks/m10_metrics_collector.py → PURE_QUERY

---

## No-Regression Guard

Once a batch is complete, add to CI baseline:

```yaml
# .github/workflows/feature-intent.yml
feature_intent_baseline:
  fixed_groups:
    - worker/*
    - costsim/circuit_breaker*
  max_violations: 116  # Decreases with each batch
```

---

## References

- `scripts/ci/check_feature_intent.py` — CI enforcement
- `app/infra/feature_intent.py` — Intent definitions
- `app/infra/feature_intent_examples.py` — Golden examples
- PIN-264 — Phase-2.3 Feature Intent System
