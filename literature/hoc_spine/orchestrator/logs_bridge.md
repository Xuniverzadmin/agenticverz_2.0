# logs_bridge.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/logs_bridge.py`
**Layer:** L4 — HOC Spine (Bridge)
**Component:** Orchestrator / Coordinator / Bridge
**Created:** 2026-02-03
**Reference:** PIN-510 (God Object Mitigation), PIN-519 (System Run Introspection), PIN-520 (L4 Uniformity Initiative)

---

## Placement Card

```
File:            logs_bridge.py
Lives in:        orchestrator/coordinators/bridges/
Role:            Logs domain capability factory
Inbound:         hoc_spine/orchestrator/handlers/logs_handler.py, coordinators
Outbound:        logs/L5_engines/*, logs/L6_drivers/* (lazy imports)
Transaction:     none (factory only)
Cross-domain:    no (single domain)
Purpose:         Bridge for logs L5/L6 access from L4
Violations:      none
```

## Purpose

Domain-specific capability factory for logs L5 engines and L6 drivers.
Implements the Switchboard Pattern (Law 4 - PIN-507):

- Never accepts session parameters (except audit_ledger_read_capability)
- Returns module references for lazy access
- Handler binds session (Law 4 responsibility)
- No retry logic, no decisions, no state

## Capabilities

| Method | Returns | L5/L6 Module | Purpose |
|--------|---------|--------------|---------|
| `logs_read_service()` | `LogsReadService` | logs/L5_engines/logs_read_engine | Read-only logs queries |
| `traces_store_capability()` | `SQLiteTraceStore` | logs/L6_drivers/traces_store | Run-scoped trace queries (PIN-519) |
| `audit_ledger_read_capability(session)` | `AuditLedgerReadDriver` | logs/L6_drivers/audit_ledger_read_driver | Signal feedback queries (PIN-519) |
| `capture_driver_capability()` | `capture_driver` module | logs/L6_drivers/capture_driver | Evidence capture (PIN-520) |

## Usage Pattern

```python
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge import (
    get_logs_bridge,
)

bridge = get_logs_bridge()

# Get logs read service
logs = bridge.logs_read_service()
records = await logs.list_records(session, tenant_id)

# Get traces store (PIN-519)
traces = bridge.traces_store_capability()
trace = traces.get_trace(run_id)

# Get audit ledger reader (PIN-519)
audit = bridge.audit_ledger_read_capability(session)
feedback = await audit.get_signal_feedback(signal_id)

# Get capture driver (PIN-520)
capture = bridge.capture_driver_capability()
capture.capture_environment_evidence(ctx, sdk_mode="api", ...)
```

## Capability Details

### logs_read_service()

Returns the LogsReadService singleton for read-only logs queries.

**Provides:**
- `list_records()`, `get_record()`, `get_trace()`, `get_envelope()`

### traces_store_capability() (PIN-519)

Returns SQLiteTraceStore for run-scoped trace queries. Used by `run_proof_coordinator.py`
for integrity verification via HASH_CHAIN model.

**Provides:**
- `get_trace()`, `list_traces()`, `get_trace_steps()`

### audit_ledger_read_capability(session) (PIN-519)

Returns AuditLedgerReadDriver for signal feedback queries. Used by `signal_feedback_coordinator.py`
for querying signal feedback from the audit ledger.

**Note:** This is the only capability that accepts a session parameter because the
audit ledger driver requires a database session for queries.

**Provides:**
- `get_signal_feedback()`, `list_signal_feedback()`

### capture_driver_capability() (PIN-520 Phase 1)

Returns the capture_driver module for evidence capture. Used by LogsCaptureHandler
to capture environment evidence at run creation time.

**Provides:**
- `capture_environment_evidence(ctx, sdk_mode, execution_environment, telemetry_delivery_status, capture_confidence_score)`

**Usage (via handler):**

```python
# LogsCaptureHandler uses this capability internally
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge import (
    get_logs_bridge,
)

bridge = get_logs_bridge()
capture = bridge.capture_driver_capability()

# Capture environment evidence
capture.capture_environment_evidence(
    execution_ctx,
    sdk_mode="api",
    execution_environment="prod",
    telemetry_delivery_status="connected",
    capture_confidence_score=1.0,
)
```

**Evidence Architecture v1.0 Integration:**

The capture_driver_capability supports the Evidence Architecture v1.0 model where
evidence is captured at key execution points:

1. **Run creation** (via LogsCaptureHandler): Environment evidence
2. **Tool invocation** (via MCP handlers): Tool-level evidence
3. **Run completion** (via workers.py): Outcome evidence

## Bridge Contract

| Rule | Enforcement |
|------|-------------|
| Max 5 methods | CI check 19 |
| Returns modules (not sessions) | Code review (exception: audit_ledger_read_capability) |
| Lazy imports only | No top-level L5/L6 imports |
| L4 handlers only | Forbidden import check |

## PIN-520 Phase 1

The `capture_driver_capability()` method was added as part of PIN-520 Phase 1
(workers.py migration). It enables:

1. Evidence capture at run creation time via L4 handler
2. Proper L4->L6 routing (no direct L2->L6 imports)
3. Evidence Architecture v1.0 compliance

This capability completes the logs_bridge coverage for evidence capture workflows,
complementing the existing trace and audit capabilities from PIN-519.

## Singleton Access

```python
_instance = None

def get_logs_bridge() -> LogsBridge:
    global _instance
    if _instance is None:
        _instance = LogsBridge()
    return _instance
```

---

*Generated: 2026-02-03*
