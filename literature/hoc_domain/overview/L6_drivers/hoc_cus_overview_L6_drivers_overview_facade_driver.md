# hoc_cus_overview_L6_drivers_overview_facade_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/overview/L6_drivers/overview_facade_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | overview |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Overview Facade Driver - Pure data access for overview aggregation

## Intent

**Role:** Overview Facade Driver - Pure data access for overview aggregation
**Reference:** PIN-470
**Callers:** overview_facade.py (L5)

## Purpose

Overview Facade Driver (L6 Data Access)

---

## Classes

### `IncidentCountSnapshot`
- **Docstring:** Raw incident count data from DB.
- **Class Variables:** total: int, active: int, critical: int

### `ProposalCountSnapshot`
- **Docstring:** Raw policy proposal count data from DB.
- **Class Variables:** total: int, pending: int

### `BreachCountSnapshot`
- **Docstring:** Raw limit breach count data from DB.
- **Class Variables:** recent: int

### `RunCountSnapshot`
- **Docstring:** Raw worker run count data from DB.
- **Class Variables:** total: int, running: int, queued: int

### `AuditCountSnapshot`
- **Docstring:** Raw audit count data from DB.
- **Class Variables:** last_activity_at: Optional[datetime]

### `IncidentSnapshot`
- **Docstring:** Snapshot of a single incident for decisions projection.
- **Class Variables:** id: str, title: Optional[str], severity: Optional[str], lifecycle_state: str, created_at: Optional[datetime]

### `ProposalSnapshot`
- **Docstring:** Snapshot of a single policy proposal for decisions projection.
- **Class Variables:** id: str, proposal_name: str, status: str, created_at: Optional[datetime]

### `LimitSnapshot`
- **Docstring:** Snapshot of a single limit for cost projection.
- **Class Variables:** id: str, name: str, limit_category: str, max_value: float, status: str

### `RunCostSnapshot`
- **Docstring:** Snapshot of run cost data from DB.
- **Class Variables:** total_cost_cents: int

### `BreachStatsSnapshot`
- **Docstring:** Snapshot of breach statistics from DB.
- **Class Variables:** breach_count: int, total_overage: float

### `IncidentDecisionCountSnapshot`
- **Docstring:** Snapshot of incident counts by severity for decisions count.
- **Class Variables:** total: int, critical: int, high: int, other: int

### `RecoverySnapshot`
- **Docstring:** Snapshot of incident recovery data from DB.
- **Class Variables:** total: int, recovered: int, pending: int, failed: int

### `OverviewFacadeDriver`
- **Docstring:** Overview Facade Driver - Pure data access layer.
- **Methods:** fetch_incident_counts, fetch_proposal_counts, fetch_breach_counts, fetch_run_counts, fetch_last_activity, fetch_pending_incidents, fetch_pending_proposals, fetch_run_cost, fetch_budget_limits, fetch_breach_stats, fetch_incident_decision_counts, fetch_proposal_count, fetch_recovery_stats

## Attributes

- `logger` (line 56)
- `__all__` (line 503)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.audit_ledger`, `app.models.killswitch`, `app.models.policy`, `app.models.policy_control_plane`, `app.models.tenant` |
| External | `app.hoc.cus.hoc_spine.services.time`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

overview_facade.py (L5)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: IncidentCountSnapshot
      methods: []
    - name: ProposalCountSnapshot
      methods: []
    - name: BreachCountSnapshot
      methods: []
    - name: RunCountSnapshot
      methods: []
    - name: AuditCountSnapshot
      methods: []
    - name: IncidentSnapshot
      methods: []
    - name: ProposalSnapshot
      methods: []
    - name: LimitSnapshot
      methods: []
    - name: RunCostSnapshot
      methods: []
    - name: BreachStatsSnapshot
      methods: []
    - name: IncidentDecisionCountSnapshot
      methods: []
    - name: RecoverySnapshot
      methods: []
    - name: OverviewFacadeDriver
      methods: [fetch_incident_counts, fetch_proposal_counts, fetch_breach_counts, fetch_run_counts, fetch_last_activity, fetch_pending_incidents, fetch_pending_proposals, fetch_run_cost, fetch_budget_limits, fetch_breach_stats, fetch_incident_decision_counts, fetch_proposal_count, fetch_recovery_stats]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
