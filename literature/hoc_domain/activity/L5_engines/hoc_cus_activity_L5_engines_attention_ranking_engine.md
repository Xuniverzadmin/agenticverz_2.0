# hoc_cus_activity_L5_engines_attention_ranking_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/activity/L5_engines/attention_ranking_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | activity |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Attention ranking engine for activity signals

## Intent

**Role:** Attention ranking engine for activity signals
**Reference:** PIN-470, Activity Domain
**Callers:** activity_facade.py

## Purpose

Attention ranking engine for prioritizing signals.

---

## Classes

### `AttentionSignal`
- **Docstring:** A signal in the attention queue.
- **Class Variables:** signal_id: str, signal_type: str, dimension: str, title: str, description: str, severity: float, attention_score: float, attention_reason: str, created_at: datetime, source_run_id: Optional[str], acknowledged: bool, suppressed: bool

### `AttentionQueueResult`
- **Docstring:** Result of attention queue query.
- **Class Variables:** items: list[AttentionSignal], total: int, generated_at: datetime

### `AttentionRankingService`
- **Docstring:** Service for ranking and prioritizing activity signals.
- **Methods:** __init__, get_attention_queue, compute_attention_score

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.cus.hoc_spine.services.time` |

## Callers

activity_facade.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: AttentionSignal
      methods: []
    - name: AttentionQueueResult
      methods: []
    - name: AttentionRankingService
      methods: [get_attention_queue, compute_attention_score]
```

## PIN-520 Dead Code Rewiring Updates

- **Change Date:** 2026-02-03
- **Change Type:** Documentation — Dead Code Rewiring
- **Details:** Documented `min_score` parameter wiring during PIN-520 phase 3 dead code rewiring
- **Impact:** No code changes; enhanced documentation of existing parameter

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
