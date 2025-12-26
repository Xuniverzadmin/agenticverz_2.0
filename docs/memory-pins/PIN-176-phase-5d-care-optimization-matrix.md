# PIN-176: Phase 5D - CARE Optimization Matrix

**Status:** COMPLETE
**Category:** Contracts / Behavioral Changes
**Created:** 2025-12-26
**Completed:** 2025-12-26
**Milestone:** Post-M28 Behavioral Changes (Final Optimization Phase)

---

## Scope Lock

> **This matrix is a DRAFT pending approval.**
> Phase 5D is the last phase before WRAP.
> Same discipline as 5A-5C applies.
>
> CARE can learn—but only within hard rails.

---

## Executive Summary

Phase 5D improves routing quality without compromising determinism, explainability, or reversibility. The CARE engine may optimize agent selection based on historical signals, but only within explicit bounds. Every optimization that changes a routing decision must emit a decision record. Silence is forbidden when optimization diverges from baseline.

---

## Prerequisites

| Prerequisite | Status |
|--------------|--------|
| Phase 5A complete (budget enforcement) | COMPLETE |
| Phase 5B complete (policy pre-check) | COMPLETE |
| Phase 5C complete (recovery automation) | COMPLETE |
| Contracts frozen (`contracts-stable-v1`) | COMPLETE |
| Decision emission infrastructure | COMPLETE |
| CARE routing engine functional | COMPLETE |

---

## Phase 5D Objective (Singular)

> **Improve CARE routing quality using historical signals, always with a decision record when optimization changes the choice.**

Nothing more. No other behavioral changes allowed.

---

## What CARE Optimization IS and IS NOT

### Optimization IS

- **Read-only learning** from historical execution data
- **Ranking/selection** within existing CARE agent options
- **Confidence scoring** to inform selection stability
- **Shadow evaluation** that logs but doesn't change behavior
- **Reversible** via kill-switch at any time
- **Explainable** in founder timeline

### Optimization is NOT

- A replacement for CARE logic
- An opaque ML model making routing decisions
- Permission to change policy/budget/recovery behavior
- Execution-time mutation of plans
- Learning from forbidden signals
- Anything that cannot be rolled back instantly

**If optimization is invisible, it is a bug.**

---

## Learning Signals (Frozen)

### Allowed Signals

| Signal | Source | Why Allowed |
|--------|--------|-------------|
| `latency_p50` | Execution history | Observable, no side effects |
| `latency_p95` | Execution history | Observable, no side effects |
| `cost_per_run` | Budget records | Already tracked, deterministic |
| `success_rate` | Outcome records | Binary execution success only (see note below) |
| `recovery_occurred` | Recovery decisions | Boolean only, not recovery details |
| `agent_availability` | Health checks | Real-time capability signal |
| `context_size_bucket` | Request metadata | Affects model fit, not content |

> **Note on `success_rate`:** This signal measures binary execution success only—whether the run completed without failure or halt. It is **not** a measure of subjective quality, content correctness, or user satisfaction. This prevents CARE from optimizing toward "easy but low-value" paths.

### Forbidden Signals (Hard Boundary)

| Signal | Why Forbidden |
|--------|---------------|
| `policy_outcome` | Would create feedback loop with policy |
| `budget_halt_reason` | Would optimize around budget limits |
| `recovery_class` | Would learn to avoid R3 scenarios |
| `customer_content` | Privacy, no content-based routing |
| `safety_events` | Would optimize around safety rails |
| `founder_overrides` | Would learn to predict/bypass human judgment |
| `failure_details` | Beyond boolean, could leak sensitive info |
| `user_feedback` | Proxy for content quality, introduces bias |

### Signal Isolation Rule

```
CARE optimization may ONLY read from:
  - contracts.execution_metrics (aggregated)
  - contracts.decision_records (type/outcome only, not inputs/details)

CARE optimization may NEVER read from:
  - policy evaluation results
  - budget enforcement decisions
  - recovery evaluation details
  - run content/payloads
  - safety event logs
```

---

## Decision Contract (CARE-Specific)

### New Decision Type

```python
class DecisionType(str, Enum):
    # ... existing ...
    CARE_ROUTING_OPTIMIZED = "care_routing_optimized"  # Phase 5D: Optimization changed routing
```

### New Decision Outcomes

```python
class DecisionOutcome(str, Enum):
    # ... existing ...
    BASELINE_SELECTED = "baseline_selected"      # Optimization agreed with baseline
    OPTIMIZED_SELECTED = "optimized_selected"    # Optimization changed selection
```

### Emission Rule (Frozen)

```
EMIT CARE_ROUTING_OPTIMIZED decision IF AND ONLY IF:
  - optimization_enabled = true
  - AND optimized_choice != baseline_choice

DO NOT EMIT decision IF:
  - optimization_disabled (baseline path)
  - optimized_choice == baseline_choice (no change)

Silence is allowed ONLY when baseline == optimized.
```

### Decision Record Structure

```python
DecisionRecord(
    decision_type=DecisionType.CARE_ROUTING_OPTIMIZED,
    decision_source=DecisionSource.SYSTEM,
    decision_trigger=DecisionTrigger.AUTONOMOUS,  # Learning-driven
    decision_inputs={
        "baseline_agent": "agent-a",
        "optimized_agent": "agent-b",
        "confidence_score": 0.85,
        "signals_used": ["latency_p50", "success_rate"],
    },
    decision_outcome=DecisionOutcome.OPTIMIZED_SELECTED,
    decision_reason="Optimization selected agent-b (higher success rate, lower latency)",
    run_id=None,  # Pre-run decision
    request_id="<request_id>",
    causal_role=CausalRole.PRE_RUN,  # Always pre-run
    details={
        "baseline_score": 0.72,
        "optimized_score": 0.85,
        "optimization_version": "v1.0",
    }
)
```

---

## Stability & Rollback Rules

### Feature Flag Control

```yaml
care_optimization:
  enabled: false           # Default OFF
  mode: "shadow"           # shadow | active
  version: "v1.0"          # For replay determinism
  kill_switch: true        # Always available
```

### Rollout Phases

| Phase | Mode | Behavior | Decision Emission |
|-------|------|----------|-------------------|
| 0 | Disabled | Baseline CARE only | None |
| 1 | Shadow | Log optimization choice, use baseline | Shadow log only |
| 2 | Active | Use optimization choice | Emit on divergence |
| 3 | Stable | Optimization is default | Emit on divergence |

### Shadow Mode Invariant (Mandatory)

> **Shadow mode MUST emit comparison metadata but MUST NOT emit CARE_ROUTING_OPTIMIZED decisions.**

Rationale:
- Shadow mode is *measurement*, not *decision*
- Decision emission implies causality
- Founder timelines must not be polluted with hypothetical choices
- Shadow logs go to observability, not to decision_records table

### Kill-Switch Behavior

```
IF kill_switch activated:
  - Immediately revert to baseline CARE
  - Log kill_switch_activated event
  - No optimization decisions emitted
  - Deterministic behavior restored

Kill-switch takes effect within 1 request cycle.
No gradual rollback. Instant revert.
```

### Deterministic Replay Requirement

```
GIVEN: Same request_id, same signals at decision time
WHEN: Replay executed
THEN: Same routing decision must be made

If replay diverges from original decision:
  - HALT optimization
  - Investigate signal drift
  - Do not re-enable until root cause resolved
```

---

## Founder Explainability

### Timeline Entry Format

When optimization changes routing, founder sees:

```
[CARE Routing Optimized]
Baseline would have selected: agent-a
Optimization selected: agent-b
Reason: Higher success rate (92% vs 78%), lower p50 latency (120ms vs 340ms)
Confidence: 0.85
Signals: latency_p50, success_rate
```

### Explainability Contract

Every optimized routing decision must answer:
1. What would baseline have chosen?
2. What did optimization choose?
3. Why? (which signals, what scores)
4. How confident?

If these cannot be answered from the decision record, optimization is broken.

---

## E2E Test Matrix (Design)

| Test ID | Scenario | Expected Outcome |
|---------|----------|------------------|
| G5D-01 | Optimization disabled | Baseline CARE only, no decision emitted |
| G5D-02 | Optimization enabled, same choice | No decision emitted (silence allowed) |
| G5D-03 | Optimization enabled, different choice | Decision emitted with optimized_selected |
| G5D-04 | Shadow mode, different choice | Shadow log only, baseline used |
| G5D-05 | Kill-switch activated | Instant revert to baseline |
| G5D-06 | Replay with same signals | Same decision reproduced |
| G5D-07 | Replay with different signals | Different decision (expected) |
| G5D-08 | Founder timeline shows optimization | Explainability fields present |
| G5D-09 | Forbidden signal access attempted | Hard error, not silent failure |
| G5D-10 | Policy/budget/recovery unchanged | No impact on other phases |
| G5D-11 | Confidence below threshold | Baseline selected (conservative) |
| G5D-12 | No historical data available | Baseline selected (cold start) |

### Invariant Tests

| Test ID | Invariant | Assertion |
|---------|-----------|-----------|
| G5D-INV-01 | No silent optimization | Every divergence emits decision |
| G5D-INV-02 | Forbidden signals blocked | Access attempt raises exception |
| G5D-INV-03 | Kill-switch works | Revert within 1 cycle |
| G5D-INV-04 | Replay deterministic | Same signal snapshot → same routing |
| G5D-INV-05 | No contract expansion | Only additive types/outcomes |
| G5D-INV-06 | Shadow mode no decisions | Shadow logs only, no decision_records |

---

## Stop Conditions (Automatic Halt)

Phase 5D implementation STOPS immediately if:

1. Routing changes without a decision record
2. Optimization affects policy/budget/recovery behavior
3. Replay diverges unexpectedly
4. Signals leak from forbidden sources
5. Kill-switch fails to revert instantly
6. Founder cannot explain a routing decision

If any condition occurs: **disable optimization, investigate, do not re-enable until resolved**.

---

## Behavioral Matrix (Frozen)

| ID | Behavior | Contract | Decision Outcome |
|----|----------|----------|------------------|
| 5D-01 | Optimization changes routing | DECISION | optimized_selected |
| 5D-02 | Optimization agrees with baseline | DECISION | (no emission) |
| 5D-03 | Shadow mode logs divergence | DECISION | (shadow log only) |
| 5D-04 | Kill-switch reverts to baseline | CONSTRAINT | (no emission, baseline) |
| 5D-05 | Forbidden signal access blocked | CONSTRAINT | (hard error) |
| 5D-06 | Replay reproduces decision | OUTCOME | (determinism verified) |
| 5D-07 | Founder sees explanation | OUTCOME | (visibility) |
| 5D-08 | Cold start uses baseline | DECISION | baseline_selected |

---

## Explicit Non-Goals (Forbidden in Phase 5D)

1. **No policy logic changes** - Policy is frozen (5B)
2. **No budget behavior changes** - Budget is frozen (5A)
3. **No recovery behavior changes** - Recovery is frozen (5C)
4. **No content-based routing** - Privacy boundary
5. **No opaque ML models** - Must be explainable
6. **No execution-time plan mutation** - Pre-run only
7. **No learning from forbidden signals** - Hard boundary
8. **No optimization without rollback** - Kill-switch mandatory

---

## Implementation Order

| Step | Task | Status |
|------|------|--------|
| 1 | Freeze PIN-176 matrix | COMPLETE |
| 2 | Add CARE_ROUTING_OPTIMIZED to DecisionType | COMPLETE |
| 3 | Add BASELINE_SELECTED, OPTIMIZED_SELECTED outcomes | COMPLETE |
| 4 | Implement signal isolation layer | COMPLETE |
| 5 | Implement emit_care_optimization_decision() | COMPLETE |
| 6 | Add feature flag + kill-switch | COMPLETE |
| 7 | Implement shadow mode | COMPLETE |
| 8 | Write E2E tests (red first) | COMPLETE |
| 9 | Implement until green | COMPLETE |
| 10 | Verify replay determinism | COMPLETE |

---

## Why This Is the Final Optimization

After Phase 5D:
- The system can route, fail, stop, block, recover, and optimize **honestly**
- Every decision is explainable and reversible
- Founders can delegate trust (optimization is bounded)
- Beta users experience predictable behavior
- WRAP criteria are met

This is where systems typically add magic. We are explicitly designing not to.

---

## Completion Note

Phase 5D implementation complete (2025-12-26).

Test results:
- 18/18 Phase 5D tests pass
- 18/18 Phase 5B tests pass (no regressions)
- 19/19 Phase 5C tests pass (no regressions)

Implementation summary:
- `CARE_ROUTING_OPTIMIZED` decision type added
- `BASELINE_SELECTED`, `OPTIMIZED_SELECTED` outcomes added
- Signal isolation: 7 allowed, 8 forbidden (hardcoded guards)
- Kill-switch: instant revert mechanism
- Confidence threshold: 0.50 (conservative baseline)
- Shadow mode: logs comparison, no decision emission

The system can now route, fail, stop, block, recover, and optimize **honestly**.
All trust-critical behavior is frozen and verified (5A-5D).
WRAP (Internal) criteria are met.
