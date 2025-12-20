# PIN-107: M24 Phase-2 - Friction Intelligence & Founder Actions

**Status:** ACTIVE
**Category:** Ops Console / Founder Intelligence
**Created:** 2025-12-20
**Author:** Claude Opus 4.5

---

## Summary

Phase-2 of the Ops Console (PIN-105) adds friction intelligence and founder intervention suggestions. This transforms the console from "measuring the past" to "predicting the future and suggesting action."

---

## Strategic Context

From founder feedback:
> "You are measuring the past. You need to predict the future."

Key insights:
- Event-first architecture is correct (ops_events as source of truth)
- Missing friction events (STARTED/ABORTED/VIEWED_NO_ACTION)
- Stickiness score needs recency decay (7d vs 30d)
- Need days_to_limit projections for infrastructure
- Need "Customers At Risk" with founder intervention suggestions
- Cache tables (ops_tenant_metrics) must be documented as non-authoritative

---

## Phase-2 Components

### 1. Friction Event Taxonomy

New event types added to `EventType` enum:

| Event Type | Signal | Description |
|------------|--------|-------------|
| `INCIDENT_VIEWED_NO_ACTION` | Hesitation | User viewed incident but took no action |
| `REPLAY_STARTED` | Intent | User initiated replay flow |
| `REPLAY_ABORTED` | Friction | User cancelled mid-flow |
| `REPLAY_FAILED` | System issue | Replay failed due to error |
| `EXPORT_STARTED` | Intent | User initiated export |
| `EXPORT_ABORTED` | Friction | User cancelled export |
| `EXPORT_FAILED` | System issue | Export failed |
| `POLICY_BLOCK_REPEAT` | Friction | Same policy blocking repeatedly |
| `SESSION_STARTED` | Engagement | User started session |
| `SESSION_ENDED` | Engagement | User ended session normally |
| `SESSION_IDLE_TIMEOUT` | Friction | User went idle/abandoned |

All friction events include `metadata.friction_signal` for classification.

### 2. Recency-Weighted Stickiness

**CustomerSegment model enhanced:**
```python
stickiness_7d: float      # Recent engagement (7 days)
stickiness_30d: float     # Historical baseline (30 days, normalized to weekly)
stickiness_delta: float   # Ratio: 7d/30d
                          # > 1 = accelerating
                          # < 1 = decelerating (churn risk)
```

**Calculation:**
- 7d: `(views * 0.2) + (replays * 0.3) + (exports * 0.5)`
- 30d: Same formula / 4.3 (normalize to weekly)
- Delta: `stickiness_7d / stickiness_30d`

### 3. Days-to-Limit Projections

**InfraLimits model enhanced:**
```python
db_storage_days_to_limit: Optional[int]    # Days until DB storage limit
redis_memory_days_to_limit: Optional[int]  # Days until Redis limit
db_growth_rate_gb_per_day: float           # Current growth rate
api_growth_rate_pct_per_week: float        # API traffic growth
```

Projections based on:
- Event volume (proxy for data growth)
- Week-over-week API request comparison

### 4. Customers At Risk Endpoint

**New endpoint:** `GET /ops/customers/at-risk`

Returns at-risk customers with:
- Risk score (0-100)
- Primary and secondary risk signals
- Stickiness decay metrics
- Friction event counts
- **Founder intervention suggestions**

### 5. Founder Interventions

Auto-generated action suggestions based on risk signals:

| Type | When | Action |
|------|------|--------|
| `call` | Critical risk | "Schedule 15-min call with customer" |
| `email` | Stickiness drop >50% | "Send personalized check-in email" |
| `feature_help` | No investigation >7d | "Send feature guide or walkthrough" |
| `technical` | Policy friction | "Review and adjust policy config" |

Priorities: `immediate` > `today` > `this_week`

### 6. Architecture Documentation

Added comprehensive docstring to `ops.py` documenting:
- ops_events as single source of truth
- Cache tables as non-authoritative
- Friction event semantics
- Stickiness decay formula
- Intervention generation logic

---

## Files Modified

| File | Change |
|------|--------|
| `backend/app/services/event_emitter.py` | Added 12 friction event types + convenience methods |
| `backend/app/api/ops.py` | Added Phase-2 models, at-risk endpoint, architecture docs |

---

## New Models

### CustomerAtRisk
```python
class CustomerAtRisk(BaseModel):
    tenant_id: str
    risk_level: str          # 'critical', 'high', 'medium'
    risk_score: float        # 0-100
    primary_risk_reason: str
    secondary_signals: List[str]
    stickiness_7d: float
    stickiness_30d: float
    stickiness_delta: float
    last_investigation: Optional[str]
    days_since_investigation: Optional[int]
    friction_events_7d: int
    top_friction_type: Optional[str]
    interventions: List[FounderIntervention]
```

### FounderIntervention
```python
class FounderIntervention(BaseModel):
    intervention_type: str   # 'call', 'email', 'feature_help', 'pricing', 'technical'
    priority: str            # 'immediate', 'today', 'this_week'
    suggested_action: str
    context: str
    expected_outcome: str
```

---

## API Changes

### Enhanced Endpoints

| Endpoint | Enhancement |
|----------|-------------|
| `GET /ops/customers` | Now includes stickiness_7d, stickiness_30d, stickiness_delta, friction_score |
| `GET /ops/infra` | Now includes days_to_limit projections, growth rates |

### New Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /ops/customers/at-risk` | "Who should I call today?" with interventions |

---

## Usage Example

```python
# Get customers at risk with interventions
response = await client.get("/ops/customers/at-risk?limit=10")

for customer in response.json():
    print(f"Tenant: {customer['tenant_id']}")
    print(f"Risk: {customer['risk_level']} ({customer['risk_score']}/100)")
    print(f"Stickiness: {customer['stickiness_7d']} (7d) vs {customer['stickiness_30d']} (30d)")
    print(f"Delta: {customer['stickiness_delta']} ({'accelerating' if customer['stickiness_delta'] > 1 else 'decelerating'})")

    for intervention in customer['interventions']:
        print(f"  [{intervention['priority']}] {intervention['suggested_action']}")
```

---

## Related PINs

- PIN-105: Ops Console - Founder Intelligence System (Phase-1)
- PIN-097: Prevention System v1.1

---

---

## Phase-2.1 Improvements (Epistemic Honesty & Playbooks)

From second round of strategic feedback:

### 1. Epistemic Honesty - Rename risk_score

**Before:** `risk_score: float  # 0-100`
**After:** `risk_signal_strength: float  # 0-100 (heuristic, NOT prediction)`

Rationale: Until validated with 10-20 real churn events, this is an attention ranking heuristic, not a prediction. Honest naming prevents blind trust.

### 2. Intervention Explainability

Every `FounderIntervention` now includes `triggering_signals`:

```python
class FounderIntervention(BaseModel):
    # ... existing fields ...
    triggering_signals: List[str]  # e.g., ["stickiness_delta < 0.3", "no REPLAY in 9 days"]
```

This enables:
- Founder can see "why" → builds trust
- Correlate actions with outcomes → learn what works
- Validate signal quality over time → improve heuristics

### 3. Friction Event Weighting

Not all friction is equal:

```python
FRICTION_WEIGHTS = {
    "REPLAY_ABORTED": 3.0,   # High - user gave up on core feature
    "EXPORT_ABORTED": 2.5,   # High - value extraction abandoned
    "REPLAY_FAILED": 2.0,    # System failure
    "EXPORT_FAILED": 2.0,
    "INCIDENT_VIEWED_NO_ACTION": 1.0,  # Low - hesitation
    "POLICY_BLOCK_REPEAT": 2.0,        # Systemic friction
    "SESSION_IDLE_TIMEOUT": 1.5,       # User went away
}

FRICTION_CAP_PER_SESSION = 5   # Prevent one bad path from dominating
FRICTION_CAP_PER_DAY = 10
```

### 4. "What Changed?" Correlation Layer

`CustomerAtRisk` now includes:

```python
recent_changes: List[str]      # e.g., ["policy_change 3 days ago"]
decay_correlation: Optional[str]  # Best guess at what triggered decay
```

Future: Query policy_changes, model_switches, rate_limit_changes to correlate with engagement decay.

### 5. Founder Playbooks v1

**New endpoint:** `GET /ops/playbooks`

Five playbooks with signal → action mappings:

| Playbook | Trigger | Risk Level |
|----------|---------|------------|
| `silent_churn` | API active, no investigation 7+ days | high |
| `policy_friction` | 3+ POLICY_BLOCK_REPEAT in 7 days | medium |
| `abandonment` | 3+ REPLAY_ABORTED/EXPORT_ABORTED | high |
| `engagement_decay` | stickiness_delta < 0.5 | critical |
| `legal_only` | Only certs, no investigation | medium |

Each playbook includes:
- `trigger_conditions`: When to apply
- `actions`: Step-by-step with timing and talk tracks
- `success_metric`: How to measure if it worked
- `notes`: Context for founders

**Philosophy:** Learn manually BEFORE automating. Track outcomes to validate playbooks.

---

## New Endpoints (Phase-2.1)

| Endpoint | Purpose |
|----------|---------|
| `GET /ops/playbooks` | List all founder playbooks |
| `GET /ops/playbooks/{id}` | Get specific playbook detail |

---

## Updated Models (Phase-2.1)

### CustomerAtRisk (updated)
```python
class CustomerAtRisk(BaseModel):
    # ... existing ...
    risk_signal_strength: float  # Renamed from risk_score
    friction_weighted_score: float  # Weighted, not raw count
    recent_changes: List[str]
    decay_correlation: Optional[str]
```

### FounderIntervention (updated)
```python
class FounderIntervention(BaseModel):
    # ... existing ...
    triggering_signals: List[str]  # NEW: Explicit triggers
```

### PlaybookDetail (new)
```python
class PlaybookDetail(BaseModel):
    id: str
    name: str
    trigger_conditions: List[str]
    risk_level: str
    actions: List[PlaybookAction]
    success_metric: str
    notes: str
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-20 | Initial Phase-2 implementation |
| 2025-12-20 | Phase-2.1: Epistemic honesty, explainability, friction weights, playbooks |
