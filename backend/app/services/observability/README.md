# Observability Domain Module

**Layer:** L4 — Domain Engine
**Reference:** PIN-454 (Cross-Domain Orchestration Audit)
**Status:** IMPLEMENTED (Phase 2)

---

## Overview

The Observability module provides the facade layer for trace operations with RAC (Runtime Audit Contract) integration. It wraps the L6 TraceStore and emits audit acknowledgments.

## Problem Solved

Without the TraceFacade, trace operations:
- Go directly from L5 (runner) to L6 (TraceStore), bypassing L4
- Don't emit RAC acknowledgments
- Silent failures create "dark mode" runs

The TraceFacade provides:
1. **Layer-correct access** — L5 → L4 (facade) → L6 (store)
2. **RAC integration** — Emits acks after trace operations
3. **Consistent interface** — Matches other domain facades

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 L5: Execution & Workers                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ RunRunner / ObservabilityGuard                       │   │
│  │   Uses TraceFacade for trace operations              │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │ (via L4 facade)
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                 L4: Domain Engine                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ TraceFacade                                          │   │
│  │   ├─ start_trace()   → emits START_TRACE ack        │   │
│  │   ├─ complete_trace() → emits COMPLETE_TRACE ack    │   │
│  │   └─ add_step()       → best-effort, no ack         │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │ (wraps L6 store)
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                 L6: Platform Substrate                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ PostgresTraceStore                                   │   │
│  │   ├─ aos_traces table                               │   │
│  │   └─ aos_trace_steps table                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Components

### trace_facade.py

The TraceFacade wraps TraceStore operations and emits RAC acknowledgments:

- `start_trace(run_id, tenant_id, agent_id)` — Start a trace, emit START_TRACE ack
- `complete_trace(trace_id, run_id, status)` — Complete a trace, emit COMPLETE_TRACE ack
- `add_step(trace_id, step_type, data)` — Add a step (best-effort, no ack)

## Usage

### Basic Usage

```python
from app.services.observability import get_trace_facade

facade = get_trace_facade()

# Start a trace
trace_id = await facade.start_trace(
    run_id=run_id,
    tenant_id=tenant_id,
    agent_id=agent_id,
)

# Add steps during execution
await facade.add_step(
    trace_id=trace_id,
    step_type="skill_execution",
    data={"skill": "calculator", "input": "2+2"},
)

# Complete the trace
await facade.complete_trace(
    trace_id=trace_id,
    run_id=run_id,
    status="completed",
)
```

### With ObservabilityGuard (Phase 1)

The ObservabilityGuard at L5 can use the TraceFacade for trace operations:

```python
from app.worker.observability_guard import get_observability_guard
from app.services.observability import get_trace_facade

guard = get_observability_guard(mode="DEGRADED")
facade = get_trace_facade()

# Use facade for trace creation
trace_id = await facade.start_trace(run_id, tenant_id, agent_id)

# Guard handles failure modes
if trace_id is None and guard.mode == "STRICT":
    raise ObservabilityFailure("Trace creation failed")
```

## RAC Integration

The TraceFacade emits RAC acknowledgments after trace operations:

| Operation | Domain | Action | When |
|-----------|--------|--------|------|
| `start_trace()` | `logs` | `START_TRACE` | After trace creation attempt |
| `complete_trace()` | `logs` | `COMPLETE_TRACE` | After trace completion attempt |

The acks include:
- `run_id` — Correlation key
- `result_id` — The trace_id if successful
- `error` — Error message if failed

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `RAC_ENABLED` | `true` | Enable RAC ack emission |

## Files

| File | Role |
|------|------|
| `__init__.py` | Module exports |
| `trace_facade.py` | TraceFacade with RAC ack emission |

## Related Components

| Component | Location | Role |
|-----------|----------|------|
| ObservabilityGuard | `backend/app/worker/observability_guard.py` | L5 guard for trace failure modes |
| PostgresTraceStore | `backend/app/telemetry/trace_store.py` | L6 trace storage |
| AuditStore | `backend/app/services/audit/store.py` | RAC ack storage |

## Related Documents

- `docs/architecture/CROSS_DOMAIN_ORCHESTRATION_AUDIT.md` — Full audit and implementation plan
- `backend/app/services/audit/README.md` — RAC module documentation
- PIN-454 — Cross-Domain Orchestration Audit PIN
