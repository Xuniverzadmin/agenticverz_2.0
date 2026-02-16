# Canary & Shadow Rollout Contract V1

**Created:** 2026-02-16
**Status:** ACTIVE
**Purpose:** Defines the canary and shadow execution model for risky operation changes.

---

## Shadow Mode

Shadow mode runs BOTH the current and candidate decision paths for an operation, compares the results, and logs differences — but only the current path's result is used.

### Activation

Shadow mode is activated per-operation via configuration:
- `shadow_enabled: true` in operation config
- Operations eligible: any L4-dispatched operation with deterministic decision logic

### Comparison Contract

| Field | Current | Candidate | Comparison |
|-------|---------|-----------|-----------|
| outcome | ALLOW/DENY/DEFERRED | ALLOW/DENY/DEFERRED | Must match |
| reason | string | string | Should match |
| invariants_checked | list[str] | list[str] | Must match |

### Severity Classification

| Mismatch | Severity | Action |
|----------|----------|--------|
| Outcome differs | CRITICAL | Block candidate rollout, alert |
| Invariants differ | HIGH | Review before rollout |
| Reason differs | LOW | Informational only |
| Full match | NONE | Safe to promote candidate |

---

## Canary Mode

Canary mode routes a percentage of requests to the candidate path and uses its result for those requests.

### Configuration

```yaml
canary:
  enabled: true
  percentage: 5        # Start at 5%
  auto_promote: false  # Require manual promotion
  auto_rollback: true  # Rollback on CRITICAL severity
  rollback_threshold: 1  # Number of CRITICAL diffs before rollback
  observation_window: "1h"  # Minimum observation before promotion
```

### Staged Rollout

| Stage | Percentage | Duration | Auto-Rollback Trigger |
|-------|-----------|----------|----------------------|
| 1 | 5% | 1 hour | Any CRITICAL diff |
| 2 | 25% | 4 hours | >= 2 CRITICAL diffs |
| 3 | 50% | 8 hours | >= 3 CRITICAL diffs |
| 4 | 100% | N/A | Full rollout |

### Rollback Contract

Auto-rollback occurs when:
1. Number of CRITICAL severity comparisons exceeds `rollback_threshold`
2. Any unhandled exception in candidate path
3. Candidate latency exceeds 2x current path latency

Rollback action:
- Immediately route 100% to current path
- Log rollback event with reason
- Create incident-guardrail artifact (per BA-26)

---

## Evidence Requirements

- Shadow comparison logs must be persisted for 30 days
- Canary metrics must include: latency p50/p95/p99, error rate, decision drift rate
- Promotion decisions must be recorded as governance events

---

## Integration Points

- `shadow_compare.py` — decision comparison logic
- `operation_registry.py` — dispatch routing (current vs candidate)
- `business_invariants.py` — invariant evaluation for both paths
