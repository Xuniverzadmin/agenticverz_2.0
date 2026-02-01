# hoc_cus_activity_L5_engines_pattern_detection_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/activity/L5_engines/pattern_detection_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | activity |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Pattern detection engine for activity signals

## Intent

**Role:** Pattern detection engine for activity signals
**Reference:** PIN-470, Activity Domain
**Callers:** activity_facade.py

## Purpose

Pattern detection engine for identifying recurring patterns.

---

## Classes

### `DetectedPattern`
- **Docstring:** A detected activity pattern.
- **Class Variables:** pattern_id: str, pattern_type: str, dimension: str, title: str, description: str, confidence: float, occurrence_count: int, first_seen: datetime, last_seen: datetime, affected_run_ids: list[str], severity: float

### `PatternDetectionResult`
- **Docstring:** Result of pattern detection.
- **Class Variables:** patterns: list[DetectedPattern], runs_analyzed: int, window_hours: int, generated_at: datetime

### `PatternDetectionService`
- **Docstring:** Service for detecting patterns in activity data.
- **Methods:** __init__, detect_patterns, get_pattern_detail

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
    - name: DetectedPattern
      methods: []
    - name: PatternDetectionResult
      methods: []
    - name: PatternDetectionService
      methods: [detect_patterns, get_pattern_detail]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
