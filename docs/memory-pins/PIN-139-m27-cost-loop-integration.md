# PIN-139: M27 Cost Loop Integration

**Status:** COMPLETE
**Category:** Milestone / M27 Cost Intelligence
**Created:** 2025-12-23
**Milestone:** M27 Cost Loop

---

## Summary

Complete implementation of M27 Cost Loop Integration, wiring M26 Cost Intelligence into the M25 Integration Loop through 5 specialized bridges (C1-C5).

---

## The Invariant

> Every cost anomaly enters the loop.
> Every loop completion reduces future cost risk.

---

## Implementation Details

### File Location

`backend/app/integrations/cost_bridges.py` (~970 lines)

### Data Flow

```
M26 Cost Intelligence
         │
         ▼
   CostAnomaly (input)
         │
         ▼
┌─────────────────────┐
│ C1: CostLoopBridge  │ → incident_id (HIGH/CRITICAL only)
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ C2: CostPatternMatcher │ → PatternMatchResult
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ C3: CostRecoveryGenerator │ → list[RecoverySuggestion]
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ C4: CostPolicyGenerator │ → PolicyRule (SHADOW mode)
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ C5: CostRoutingAdjuster │ → list[RoutingAdjustment]
└─────────────────────┘
```

---

## Components

### CostAnomaly Model

```python
@dataclass
class CostAnomaly:
    id: str
    tenant_id: str
    anomaly_type: AnomalyType  # USER_SPIKE, FEATURE_SPIKE, BUDGET_EXCEEDED, etc.
    severity: AnomalySeverity  # LOW, MEDIUM, HIGH, CRITICAL
    entity_type: str           # "user", "feature", "model", "tenant"
    entity_id: str
    current_value_cents: int
    expected_value_cents: int
    deviation_pct: float
    message: str
    detected_at: datetime
    metadata: dict[str, Any]
```

### Severity Classification

| Deviation | Severity |
|-----------|----------|
| 0-200% | LOW |
| 200-300% | MEDIUM |
| 300-500% | HIGH |
| 500%+ | CRITICAL |

### Bridge C1: CostLoopBridge

- **Input:** CostAnomaly
- **Output:** incident_id (optional)
- **Threshold:** Only HIGH and CRITICAL anomalies create incidents
- **Dispatches:** LoopEvent to M25 Integration Loop

### Bridge C2: CostPatternMatcher

Pre-defined cost patterns:

| Pattern | Entity | Anomaly Type | Min Deviation |
|---------|--------|--------------|---------------|
| `user_daily_spike` | user | user_spike | 200% |
| `user_hourly_spike` | user | user_spike | 500% |
| `feature_cost_explosion` | feature | feature_spike | 300% |
| `budget_breach` | tenant | budget_exceeded | 100% |
| `model_cost_anomaly` | model | unusual_model | 200% |

Confidence calculation based on deviation ratio above minimum.

### Bridge C3: CostRecoveryGenerator

Recovery strategies by anomaly type:

| Anomaly Type | Recovery Actions |
|--------------|------------------|
| `user_spike` | rate_limit_user, notify_user, review_usage |
| `feature_spike` | optimize_prompts, enable_caching, model_downgrade |
| `budget_exceeded` | enforce_hard_limit, escalate_to_admin, temporary_throttle |
| `budget_warning` | notify_admin |
| `unusual_model` | route_to_cheaper, review_routing_rules |
| `rate_anomaly` | temporary_rate_limit |

### Bridge C4: CostPolicyGenerator

Policy templates:

| Action | Category | Condition Template |
|--------|----------|-------------------|
| `rate_limit_user` | operational | `user.id == '{entity_id}' AND user.requests_today > {n}` |
| `model_downgrade` | routing | `request.estimated_cost_cents > {threshold}` |
| `enforce_hard_limit` | safety | `tenant.daily_spend_cents >= tenant.daily_budget_cents` |
| `temporary_throttle` | operational | `tenant.id == '{tenant_id}' AND NOW() < '{expires_at}'` |
| `optimize_prompts` | operational | `feature_tag == '{feature_tag}'` |

Confirmations required by category:
- Safety: 3
- Routing: 2
- Operational: 1

### Bridge C5: CostRoutingAdjuster

CARE routing adjustments by policy action:

| Policy Action | Adjustment Type | Magnitude | Decay |
|--------------|-----------------|-----------|-------|
| `route_to_model` | route_block | -0.3 | 14 days |
| `rate_limit` | confidence_penalty | -0.2 | 7 days |
| `block` | route_block | -1.0 | 0 (permanent) |
| `limit_tokens` | weight_shift | -0.15 | 7 days |
| `throttle` | confidence_penalty | -0.5 | 1 day |

### CostEstimationProbe (CARE Integration)

Pre-execution cost estimation:

```python
MODEL_COSTS = {
    "claude-opus-4-5-20251101": {"input": 1.5, "output": 7.5},
    "claude-sonnet-4-20250514": {"input": 0.3, "output": 1.5},
    "claude-3-5-haiku-20241022": {"input": 0.08, "output": 0.4},
    "gpt-4o": {"input": 0.5, "output": 1.5},
    "gpt-4o-mini": {"input": 0.015, "output": 0.06},
}
```

Returns: `allowed`, `reroute`, or `blocked` with suggested cheaper model.

### CostLoopOrchestrator

Single entry point for full loop:

```python
orchestrator = CostLoopOrchestrator(dispatcher, db_session)
result = await orchestrator.process_anomaly(anomaly)
# Returns: status, stages_completed, artifacts (pattern, recoveries, policy, adjustments)
```

---

## Usage Example

```python
from app.integrations.cost_bridges import (
    CostAnomaly, AnomalyType, CostLoopOrchestrator
)

# Create anomaly from M26 detection
anomaly = CostAnomaly.create(
    tenant_id="tenant_demo",
    anomaly_type=AnomalyType.USER_SPIKE,
    entity_type="user",
    entity_id="user_123",
    current_value_cents=5000,  # $50 actual
    expected_value_cents=1000,  # $10 expected (500% deviation → CRITICAL)
)

# Process through full loop
orchestrator = CostLoopOrchestrator(dispatcher, db_session)
result = await orchestrator.process_anomaly(anomaly)

# Result contains all loop artifacts
print(result["status"])  # "complete"
print(result["stages_completed"])  # ["incident_created", "pattern_matched", ...]
```

---

## Next Steps

1. **Migration 044**: Add `cost_routing_adjustments` table, `pattern_category` column
2. **Console UI**: Cost incident detail view, recovery action panel
3. **Integration Tests**: Wire C1-C5 with real M25 dispatcher
4. **M26 Integration**: Connect actual cost detection to `CostLoopOrchestrator`

---


---

## Updates

### Update (2025-12-23)

## 2025-12-23: M27 Safety Rails Implementation

### GPT Analysis Warning (Addressed)
> "Confidence >=90% can auto-apply, Zero confirmations required in some paths.
> Once customers are live, you'll need:
> - Per-tenant auto-apply caps
> - Blast-radius limits (per org/day)"

### New Module: cost_safety_rails.py

| Component | Purpose |
|-----------|---------|
| `SafetyConfig` | Per-tenant caps, blast-radius limits, severity gates |
| `CostSafetyRails` | Enforces M27 safety limits per tenant |
| `SafeCostLoopOrchestrator` | Production wrapper with safety rails |

### Safety Configuration

| Config | Default | Production |
|--------|---------|------------|
| max_auto_policies_per_tenant_per_day | 5 | 3 |
| max_auto_recoveries_per_tenant_per_day | 10 | 5 |
| max_routing_adjustments_per_tenant_per_day | 20 | 10 |
| max_users_affected_per_action | 100 | 50 |
| high_actions_require_confirmation | True | True |
| critical_actions_require_confirmation | True | True |
| action_cooldown_minutes | 15 | 30 |

### Test Results

| Category | Tests | Status |
|----------|-------|--------|
| CostAnomaly | 5 | ✅ PASS |
| CostPatternMatcher | 2 | ✅ PASS |
| CostRecoveryGenerator | 2 | ✅ PASS |
| CostEstimationProbe | 3 | ✅ PASS |
| CostSafetyRails | 5 | ✅ PASS |
| CostLoopOrchestrator | 3 | ✅ PASS |
| SafeCostLoopOrchestrator | 1 | ✅ PASS |
| **Total** | **21** | **✅ ALL PASS** |

### Files Created
- `backend/app/integrations/cost_safety_rails.py` - Safety rails module
- `backend/tests/test_m27_cost_loop.py` - M27 test suite (21 tests)

### THE INVARIANT (Enforced)
> No automatic cost action may exceed:
> - Per-tenant daily cap
> - Per-org daily cap
> - Blast-radius scope limits
> - Severity confirmation gates

## Related PINs

- PIN-131: M27 Cost Loop Integration Blueprint (design)
- PIN-130: M25 Graduation System Design (loop mechanics)
- PIN-135: M25 Integration Loop Wiring (events.py)
- PIN-138: M28 Console Structure Audit

---

## Changelog

- 2025-12-23: Implementation complete - all 5 bridges + orchestrator
