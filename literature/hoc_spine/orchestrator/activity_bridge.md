# activity_bridge.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/activity_bridge.py`
**Layer:** L4 — HOC Spine (Bridge)
**Component:** Orchestrator / Coordinator / Bridge
**Created:** 2026-02-06
**Reference:** PIN-520 Iter3.1 (L4 Uniformity Initiative)

---

## Placement Card

```
File:            activity_bridge.py
Lives in:        orchestrator/coordinators/bridges/
Role:            Activity domain capability factory
Inbound:         hoc_spine/orchestrator/handlers/activity_*.py
Outbound:        activity/L5_engines/* (lazy imports)
Transaction:     none (factory only)
Cross-domain:    no (single domain)
Purpose:         Bridge for activity L5 engine access from L4
Violations:      none
```

## Purpose

Domain-specific capability factory for activity L5 engines.
Implements the Switchboard Pattern (Law 4 - PIN-507):

- Never accepts session parameters
- Returns module references for lazy access
- Handler binds session (Law 4 responsibility)
- No retry logic, no decisions, no state

## Capabilities

| Method | Returns | L5 Module |
|--------|---------|-----------|
| `activity_query_capability()` | Activity query factory | L5 ActivityQueryEngine - PIN-520 Iter3.1 (2026-02-06) |
| `run_evidence_coordinator_capability()` | Run evidence coordinator factory | L5 EvidenceEngine - PIN-520 Iter3.1 (2026-02-06) |
| `run_proof_coordinator_capability()` | Run proof coordinator factory | L5 ProofEngine - PIN-520 Iter3.1 (2026-02-06) |
| `signal_feedback_coordinator_capability()` | Signal feedback coordinator factory | L5 SignalFeedbackEngine - PIN-520 Iter3.1 (2026-02-06) |

## Usage Pattern

```python
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.activity_bridge import (
    get_activity_bridge,
)

bridge = get_activity_bridge()

# Get activity query capability
query = bridge.activity_query_capability()
result = await query.get_activities(session, params)

# Get run evidence coordinator capability
evidence = bridge.run_evidence_coordinator_capability()
result = await evidence.record_evidence(session, run_id, evidence_data)

# Get run proof coordinator capability
proof = bridge.run_proof_coordinator_capability()
result = await proof.verify_proof(session, proof_id)

# Get signal feedback coordinator capability
feedback = bridge.signal_feedback_coordinator_capability()
result = await feedback.process_feedback(session, signal_id, feedback_data)
```

## Bridge Contract

| Rule | Enforcement |
|------|-------------|
| Max 5 methods | CI check 19 |
| Returns modules (not sessions) | Code review |
| Lazy imports only | No top-level L5 imports |
| L4 handlers only | Forbidden import check |

## PIN-520 Iter3.1 (L4 Uniformity Initiative)

This bridge was created as part of PIN-520 Iter3.1 (Bridge Completion).
Provides L4 bridge access for activity domain capabilities including:

- Activity query operations
- Run evidence coordination
- Run proof verification
- Signal feedback processing

## Singleton Access

```python
_bridge_instance: ActivityBridge | None = None

def get_activity_bridge() -> ActivityBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ActivityBridge()
    return _bridge_instance
```

---

*Generated: 2026-02-06*
