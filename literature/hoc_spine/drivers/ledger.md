# ledger.py

**Path:** `backend/app/hoc/cus/hoc_spine/drivers/ledger.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            ledger.py
Lives in:        drivers/
Role:            Drivers
Inbound:         API routes, workers
Outbound:        none
Transaction:     OWNS COMMIT
Cross-domain:    none
Purpose:         Discovery Ledger - signal recording helpers.
Violations:      Driver calls commit (only transaction_coordinator allowed)
```

## Purpose

Discovery Ledger - signal recording helpers.

Core principle: Discovery Ledger records curiosity, not decisions.

This module provides:
- emit_signal(): Record a discovery signal (aggregating duplicates)
- DiscoverySignal: Pydantic model for signal data

Signals are aggregated: same (artifact, field, signal_type) updates seen_count.
Nothing in the system depends on this table - it's pure observation.

## Import Analysis

**External:**
- `pydantic`
- `sqlalchemy`
- `sqlalchemy.exc`
- `app.db`
- `app.db`

## Transaction Boundary

- **Commits:** YES
- **Flushes:** no
- **Rollbacks:** no

## Governance Violations

- Driver calls commit (only transaction_coordinator allowed)

## Functions

### `emit_signal(artifact: str, signal_type: str, evidence: dict[str, Any], detected_by: str, field: Optional[str], confidence: Optional[float], notes: Optional[str], phase: Optional[str], environment: Optional[str]) -> Optional[UUID]`

Record a discovery signal to the ledger.

Signals are aggregated: same (artifact, field, signal_type) updates seen_count.
This is non-blocking and safe to call frequently.

Args:
    artifact: Artifact name (e.g. "prediction_events")
    signal_type: Signal type (e.g. "high_operator_access")
    evidence: Evidence data as dict
    detected_by: Subsystem name that detected the signal
    field: Optional field name within the artifact
    confidence: Optional confidence score 0.0-1.0
    notes: Optional notes
    phase: Current phase (defaults to env var or "C")
    environment: Environment (defaults to env var or "local")

Returns:
    UUID of the signal record, or None if recording failed

Example:
    emit_signal(
        artifact="prediction_events",
        signal_type="high_operator_access",
        evidence={"count_7d": 21, "distinct_sessions": 5},
        detected_by="api_access_monitor",
        confidence=0.8
    )

### `get_signals(artifact: Optional[str], signal_type: Optional[str], status: Optional[str], limit: int) -> list[dict]`

Query discovery signals from the ledger.

Args:
    artifact: Filter by artifact name
    signal_type: Filter by signal type
    status: Filter by status (observed/ignored/promoted)
    limit: Max records to return

Returns:
    List of signal records as dicts

## Classes

### `DiscoverySignal(BaseModel)`

Discovery signal data model.

## Domain Usage

**Callers:** API routes, workers

## Export Contract

```yaml
exports:
  functions:
    - name: emit_signal
      signature: "emit_signal(artifact: str, signal_type: str, evidence: dict[str, Any], detected_by: str, field: Optional[str], confidence: Optional[float], notes: Optional[str], phase: Optional[str], environment: Optional[str]) -> Optional[UUID]"
      consumers: ["orchestrator"]
    - name: get_signals
      signature: "get_signals(artifact: Optional[str], signal_type: Optional[str], status: Optional[str], limit: int) -> list[dict]"
      consumers: ["orchestrator"]
  classes:
    - name: DiscoverySignal
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
    external: ['pydantic', 'sqlalchemy', 'sqlalchemy.exc', 'app.db', 'app.db']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

