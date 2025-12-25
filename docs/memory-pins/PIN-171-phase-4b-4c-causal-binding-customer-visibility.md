# PIN-171: Phase 4B/4C - Causal Binding & Customer Visibility

**Status:** COMPLETE
**Category:** Contracts / Implementation
**Created:** 2025-12-25
**Updated:** 2025-12-25
**Milestone:** Post-M28 Contract Governance

---

## Executive Summary

Completed Phase 4B extension (Causal Binding) and Phase 4C-2 (Customer Visibility) of the Contract Governance Framework. These changes address the visibility gaps identified in PIN-167 human testing.

---

## Phase 4B Extension: Causal Binding

### Problem

Pre-run decisions (routing, budget, policy) are emitted BEFORE run exists, creating a causality gap where decisions cannot be traced back to runs.

### Solution

1. **request_id** as first-class causal key (always present for pre-run decisions)
2. **causal_role** enum: `pre_run | in_run | post_run`
3. **backfill_run_id_for_request()** to bind pre-run decisions when run is created

### Implementation

| Component | File | Change |
|-----------|------|--------|
| CausalRole enum | `app/contracts/decisions.py` | Added enum |
| DecisionRecord model | `app/contracts/decisions.py` | Added request_id, causal_role |
| Backfill function | `app/contracts/decisions.py` | `backfill_run_id_for_request()` |
| Budget emission | `app/utils/budget_tracker.py` | Pass request_id |
| Goal endpoint | `app/main.py` | Generate request_id, call backfill |
| JSONB fix | `app/contracts/decisions.py` | json.dumps() for dict fields |

### Validation Results

```
request_id: 9a918b88-ca66-43
    routing (pre_run) → backfilled to run_id
    budget (pre_run)  → backfilled to run_id
    budget (in_run)   → direct with run_id
run_id: 1665d22f-18aa-4070-9b84-108038c501fc
```

- Pre-run decisions have request_id
- After run creation, pre-run decisions have run_id (via backfill)
- Founder can trace: run_id → request_id → all pre-run decisions

---

## Phase 4C-2: Customer Visibility

### Objective

Give customers predictability and accountability without exposing governance mechanics.

### Endpoints Created

| Endpoint | Purpose |
|----------|---------|
| `POST /customer/pre-run` | PRE-RUN declaration before execution |
| `POST /customer/acknowledge` | Customer acknowledgement gate |
| `GET /customer/outcome/{run_id}` | Outcome reconciliation after execution |
| `GET /customer/declaration/{id}` | Retrieve stored declaration |

### PRE-RUN Declaration

What customers see BEFORE execution:

```json
{
  "stages": [{"name": "analyze_request", "order": 1}, ...],
  "stage_count": 4,
  "cost": {
    "estimated_cents": 100,
    "minimum_cents": 50,
    "maximum_cents": 200,
    "budget_remaining_cents": 10000
  },
  "budget": {
    "mode": "soft",
    "description": "Budget limits are advisory..."
  },
  "policy": {
    "posture": "advisory",
    "active_policies": ["content-accuracy", "ftc-compliance", ...]
  },
  "memory": {
    "mode": "shared",
    "description": "Agent may use context from previous executions."
  },
  "requires_acknowledgement": true,
  "declaration_id": "uuid"
}
```

### Outcome Reconciliation

What customers see AFTER execution (decomposed, not single success flag):

```json
{
  "outcomes": [
    {"category": "task", "status": "success", "message": "Task completed."},
    {"category": "budget", "status": "warning", "message": "Budget exceeded."},
    {"category": "policy", "status": "success", "message": "No violations."},
    {"category": "recovery", "status": "success", "message": "No recovery needed."}
  ]
}
```

### What Customers DON'T See

- decision_source
- decision_trigger
- routing rejections
- recovery taxonomy
- request_id
- internal errors
- founder-only endpoints

### PIN-167 Predictability Validation

| Question | Answer |
|----------|--------|
| Can predict cost before running? | YES (estimated_cents, min/max range) |
| Warned about policy before running? | YES (posture: strict/advisory) |
| Understand result after running? | YES (decomposed outcomes) |
| Need to understand "decisions"? | NO (effects only, not mechanics) |

---

## Files Modified

| File | Change |
|------|--------|
| `app/contracts/decisions.py` | CausalRole, request_id, causal_role, backfill, JSON fix |
| `app/utils/budget_tracker.py` | request_id parameter |
| `app/main.py` | request_id generation, backfill call, router registration |
| `app/api/customer_visibility.py` | NEW - Customer endpoints |
| `app/api/founder_timeline.py` | request_id, causal_role in queries |
| `app/auth/rbac_middleware.py` | /customer/* route mappings |
| `alembic/versions/050_decision_records_causal_binding.py` | Migration |
| `docs/contracts/INDEX.md` | Phase documentation |

---

## Ledger Entries Addressed

| Visibility Gap | Scenario | Solution |
|----------------|----------|----------|
| CARE invisible | 2 | emit_routing_decision |
| Recovery siloed | 3 | emit_recovery_decision |
| Budget advisory | 1, 4 | emit_budget_decision |
| Memory opaque | 6 | emit_memory_decision |
| Pre-execution opaque | 1 | PRE-RUN declaration |
| Results opaque | 1-6 | Outcome reconciliation |

---

## Phase Status

| Phase | Status |
|-------|--------|
| Phase 4A: Contract Evolution | COMPLETE |
| Phase 4B: Record Emission | COMPLETE (+ causal binding) |
| Phase 4C-1: Founder Consumption | COMPLETE |
| Phase 4C-2: Customer Visibility | COMPLETE |

---

## Related PINs

- PIN-167: Final Review Tasks (human testing, visibility gaps)
- PIN-170: System Contract Governance Framework

---

## Next Steps

Phase 5 (behavioral changes) only after customer validation:
- Budget enforcement (hard limits)
- Policy pre-check blocking
- Recovery automation
- CARE tuning
