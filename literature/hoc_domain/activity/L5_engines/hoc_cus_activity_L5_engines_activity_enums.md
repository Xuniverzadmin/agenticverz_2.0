# hoc_cus_activity_L5_engines_activity_enums

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/activity/L5_engines/activity_enums.py` |
| Layer | L5 — Domain Engine |
| Domain | activity |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Canonical enums for activity domain - owned by engines

## Intent

**Role:** Canonical enums for activity domain - owned by engines
**Reference:** PIN-470, ACT-DUP-006, ACTIVITY_DTO_RULES.md
**Callers:** activity_facade.py, signal engines

## Purpose

Activity Domain Enums

---

## Classes

### `SignalType(str, Enum)`
- **Docstring:** Canonical signal types for activity domain.

### `SeverityLevel(str, Enum)`
- **Docstring:** Canonical severity levels for display/UI.
- **Methods:** from_score, from_risk_level

### `RunState(str, Enum)`
- **Docstring:** Run lifecycle state.

### `RiskType(str, Enum)`
- **Docstring:** Types of risk for threshold signals.

### `EvidenceHealth(str, Enum)`
- **Docstring:** Evidence health status.

## Attributes

- `__all__` (line 114)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

activity_facade.py, signal engines

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: SignalType
      methods: []
    - name: SeverityLevel
      methods: [from_score, from_risk_level]
    - name: RunState
      methods: []
    - name: RiskType
      methods: []
    - name: EvidenceHealth
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
