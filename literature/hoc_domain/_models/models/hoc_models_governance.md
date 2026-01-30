# hoc_models_governance

| Field | Value |
|-------|-------|
| Path | `backend/app/models/governance.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Governance signal data models (DB tables)

## Intent

**Role:** Governance signal data models (DB tables)
**Reference:** PIN-256 Phase E FIX-03
**Callers:** governance/*, L4 orchestrators, L5 executors

## Purpose

Governance Signal Models (Phase E FIX-03)

---

## Classes

### `GovernanceSignal(Base)`
- **Docstring:** Governance signal record - explicit persistence of L7 decisions.

### `GovernanceSignalCreate(BaseModel)`
- **Docstring:** Input model for creating governance signals.
- **Class Variables:** signal_type: str, scope: str, decision: str, reason: Optional[str], constraints: Optional[dict], recorded_by: str, expires_at: Optional[datetime]

### `GovernanceSignalResponse(BaseModel)`
- **Docstring:** Output model for governance signals.
- **Class Variables:** id: UUID, signal_type: str, scope: str, decision: str, reason: Optional[str], constraints: Optional[dict], recorded_by: str, recorded_at: datetime, expires_at: Optional[datetime], superseded_by: Optional[UUID], superseded_at: Optional[datetime]

### `GovernanceSignalQuery(BaseModel)`
- **Docstring:** Query model for checking governance status.
- **Class Variables:** scope: str, signal_type: Optional[str]

### `GovernanceCheckResult(BaseModel)`
- **Docstring:** Result of checking governance status for a scope.
- **Class Variables:** scope: str, is_blocked: bool, blocking_signals: list[GovernanceSignalResponse], warning_signals: list[GovernanceSignalResponse], last_checked: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.costsim_cb` |
| External | `pydantic`, `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlalchemy.sql` |

## Callers

governance/*, L4 orchestrators, L5 executors

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: GovernanceSignal
      methods: []
    - name: GovernanceSignalCreate
      methods: []
    - name: GovernanceSignalResponse
      methods: []
    - name: GovernanceSignalQuery
      methods: []
    - name: GovernanceCheckResult
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
