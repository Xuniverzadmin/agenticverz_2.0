# PIN-244: L3 Adapter Contract

**Status:** DESIGNED (Paper Only)
**Created:** 2025-12-30
**Category:** Architecture / Layer Governance
**Related:** PIN-240 (Seven-Layer Model), PIN-242 (Baseline Freeze)

---

## Purpose

The 17 L2→L5 violations exist because **L3 is underdeveloped**. L2 APIs bypass the translation layer and reach directly into worker internals.

This PIN defines what L3 adapters **should** provide — without writing code yet.

---

## The Missing Layer

```
L2 — Product APIs
        │
        ╳ ← BYPASS (17 violations)
        │
        ▼
L3 — Boundary Adapters (THIN, MISSING)
        │
        ▼ (should go here)
L4 — Domain Engines
        │
        ▼
L5 — Execution & Workers
```

L3 should **translate product intent into domain operations** without exposing worker internals.

---

## Violation Analysis

### Category 1: Metrics Recording (9 violations)

**Current:**
```python
# L2 (policy.py) imports L5 (workflow.metrics)
from app.workflow.metrics import record_policy_decision
```

**Problem:** Metrics is in `workflow/` (L5) but should be L6 (cross-cutting).

**Fix:** Move `record_*` functions to `app/metrics.py` (L6f Observability).

---

### Category 2: Cost Simulation (2 violations)

**Current:**
```python
# L2 (runtime.py, policy.py) imports L5 (worker.simulate)
from app.worker.simulate import CostSimulator
```

**Problem:** L2 needs to simulate costs before execution.

**Fix:** Create L3 adapter:
```python
# app/services/cost_simulation_adapter.py (L3)
class CostSimulationAdapter:
    """Translates product cost queries into simulation results."""

    def simulate_run_cost(self, plan: dict, budget: int) -> SimulationResult:
        """Returns estimated cost without accessing worker internals."""
        pass
```

---

### Category 3: Runtime Query (1 violation)

**Current:**
```python
# L2 (runtime.py) imports L5 (worker.runtime.core)
from app.worker.runtime.core import Runtime
```

**Problem:** L2 needs to query runtime capabilities.

**Fix:** Create L3 adapter:
```python
# app/services/runtime_query_adapter.py (L3)
class RuntimeQueryAdapter:
    """Translates capability queries without runtime internals."""

    def get_capabilities(self) -> CapabilityManifest:
        """Returns what the runtime can do, not how it does it."""
        pass
```

---

### Category 4: Worker Invocation (4 violations)

**Current:**
```python
# L2 (workers.py) imports L5 (workers.business_builder.worker)
from app.workers.business_builder.worker import BusinessBuilderWorker
```

**Problem:** L2 API directly instantiates and invokes workers.

**Fix:** Create L3 adapter:
```python
# app/services/worker_invocation_adapter.py (L3)
class WorkerInvocationAdapter:
    """Translates product requests into worker invocations."""

    def invoke_worker(self, worker_id: str, params: dict) -> InvocationResult:
        """Queue worker execution, return tracking handle."""
        pass

    def get_worker_status(self, invocation_id: str) -> WorkerStatus:
        """Query status without accessing worker internals."""
        pass
```

---

### Category 5: Cost Calculation (1 violation)

**Current:**
```python
# L2 (workers.py) imports L5 (worker.runner)
from app.worker.runner import calculate_llm_cost_cents
```

**Problem:** Cost calculation is in runner (L5) but needed by L2.

**Fix:** Move to L6 (Platform) or create L3 adapter:
```python
# Option A: Move to L6
# app/utils/cost_calculator.py (L6g Utils)
def calculate_llm_cost_cents(model: str, tokens: int) -> int:
    pass

# Option B: L3 adapter if product-specific formatting needed
# app/services/cost_format_adapter.py (L3)
class CostFormatAdapter:
    def format_cost_for_display(self, cents: int) -> CostDisplay:
        pass
```

---

## L3 Adapter Responsibilities

### What L3 Adapters DO

| Responsibility | Example |
|----------------|---------|
| Translate intent | "simulate cost" → CostSimulator call |
| Format output | Internal data → Product-friendly DTOs |
| Hide internals | Worker state → Simple status enum |
| Enforce boundaries | Reject invalid product requests |

### What L3 Adapters DON'T DO

| Anti-Pattern | Why Wrong |
|--------------|-----------|
| Business logic | That's L4's job |
| State mutation | That's L5's job |
| Authentication | That's L6a's job |
| Scheduling | That's L5's job |

---

## L3 Adapter Constraints (From PIN-240)

```
L3 Adapter Constraints:
- Maximum 200 lines of code
- No business logic (only translation)
- No state mutation (read-only or ephemeral)
- No independent execution (always called by L2)

If violated → promote to L4 or split into L3 + L4
```

---

## Proposed L3 Adapter Files

| File | Purpose | Fixes Violations |
|------|---------|------------------|
| `app/services/cost_simulation_adapter.py` | Simulate costs | runtime.py:148, policy.py:373 |
| `app/services/runtime_query_adapter.py` | Query capabilities | runtime.py:159 |
| `app/services/worker_invocation_adapter.py` | Invoke workers | workers.py:753, 1020, 1078, 1420 |
| `app/services/cost_format_adapter.py` | Format costs | workers.py:39 |

Plus L6 move:
- Move `app/workflow/metrics.py` → `app/metrics.py` (fixes 9 violations)

---

## Time & Control Flow Consideration

Before refactoring, each violation should answer:

| Question | Implications |
|----------|-------------|
| Is this sync or async? | Sync → adapter returns value; Async → adapter returns handle |
| Is this read or write? | Read → L3 can call L4/L5; Write → must go through L4 |
| Is this control-plane or data-plane? | Control → queuing; Data → direct call |

### Violation Classification

| Violation | Sync/Async | Read/Write | Plane |
|-----------|------------|------------|-------|
| CostSimulator import | Sync | Read | Data |
| Runtime import | Sync | Read | Control |
| BusinessBuilderWorker | Async | Write | Control |
| calculate_llm_cost_cents | Sync | Read | Data |
| record_* metrics | Sync | Write | Data |

---

## Resolution Order

1. **First: Move metrics to L6** (9 violations)
   - Lowest risk: no behavioral change
   - Highest ROI: most violations fixed

2. **Second: Create CostSimulationAdapter** (2 violations)
   - Simple read-only adapter
   - No async complexity

3. **Third: Create RuntimeQueryAdapter** (1 violation)
   - Simple read-only adapter

4. **Fourth: Create WorkerInvocationAdapter** (4 violations)
   - More complex: async invocation
   - Needs careful design

5. **Fifth: Move cost calculation to L6** (1 violation)
   - Simple function move

---

## Non-Goals

This PIN does NOT:
- Move any files
- Write adapter code
- Change runtime behavior
- Fix violations

It ONLY:
- Defines what L3 should do
- Classifies violations by fix type
- Prescribes resolution order

---

## Success Criteria

When L3 is properly designed:
1. L2 APIs never import from `app/worker/` or `app/workflow/`
2. All L5 access goes through L3 or L4
3. Layer validator reports 0 violations
4. Each adapter file is < 200 lines

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial design. Paper only — no code changes. |
