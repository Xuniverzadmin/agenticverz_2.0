# schema_parity.py

**Path:** `backend/app/hoc/hoc_spine/drivers/schema_parity.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            schema_parity.py
Lives in:        drivers/
Role:            Drivers
Inbound:         startup, SDK, API
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         M26 Prevention Mechanism #2: Startup Schema Parity Guard
Violations:      none
```

## Purpose

M26 Prevention Mechanism #2: Startup Schema Parity Guard
=========================================================

INVARIANT: SQLModel metadata must match live DB schema exactly.
If not → hard crash on boot.

Why hard-fail?
Because cost integrity errors are worse than downtime.

## Import Analysis

**External:**
- `sqlalchemy`
- `sqlalchemy.engine`
- `sqlmodel`
- `app.db`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `check_schema_parity(engine: Engine, models: Optional[List[type]], hard_fail: bool) -> Tuple[bool, List[str]]`

Check that SQLModel definitions match actual database schema.

Args:
    engine: SQLAlchemy engine
    models: List of SQLModel classes to check (default: all with __tablename__)
    hard_fail: If True, raise exception on mismatch

Returns:
    Tuple of (is_valid, list of errors)

### `check_m26_cost_tables(engine: Engine) -> Tuple[bool, List[str]]`

Specific check for M26 cost tables - the most critical.

These tables MUST match exactly:
- feature_tags
- cost_records
- cost_anomalies
- cost_budgets
- cost_daily_aggregates

### `run_startup_parity_check(engine: Engine) -> None`

Run full schema parity check on startup.
Call this from main.py before accepting requests.

## Classes

### `SchemaParityError(Exception)`

Raised when model schema doesn't match database schema.

## Domain Usage

**Callers:** startup, SDK, API

## Export Contract

```yaml
exports:
  functions:
    - name: check_schema_parity
      signature: "check_schema_parity(engine: Engine, models: Optional[List[type]], hard_fail: bool) -> Tuple[bool, List[str]]"
      consumers: ["orchestrator"]
    - name: check_m26_cost_tables
      signature: "check_m26_cost_tables(engine: Engine) -> Tuple[bool, List[str]]"
      consumers: ["orchestrator"]
    - name: run_startup_parity_check
      signature: "run_startup_parity_check(engine: Engine) -> None"
      consumers: ["orchestrator"]
  classes:
    - name: SchemaParityError
      methods: []
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.services.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['sqlalchemy', 'sqlalchemy.engine', 'sqlmodel', 'app.db']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

