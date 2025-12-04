# CostSimulator V2 Specification

**Version:** 2.0
**Status:** DRAFT
**Created:** 2025-12-03
**Author:** M5 Prep Sprint

---

## 1. Executive Summary

CostSimulator V2 extends the current pre-execution cost validation with:
- Historical cost baselines per skill
- Simulated vs actual drift detection
- Trend analysis for budget forecasting
- Scenario replay for plan optimization

---

## 2. Current State (V1)

### What V1 Does
- Budget feasibility check before execution
- Permission validation
- Static cost estimates per skill
- Risk probability assessment

### V1 Limitations
- No historical baselines (uses static estimates)
- No drift detection (simulated vs actual)
- No trend analysis
- No scenario replay

---

## 3. V2 Architecture

### 3.1 Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    CostSimulator V2                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Baseline   │  │    Drift     │  │      Trend       │  │
│  │   Manager    │  │   Detector   │  │    Analyzer      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         │                 │                   │             │
│         └─────────────────┼───────────────────┘             │
│                           │                                 │
│                    ┌──────────────┐                         │
│                    │   Scenario   │                         │
│                    │   Replayer   │                         │
│                    └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Baseline Manager

Maintains rolling cost baselines per skill:

```python
@dataclass
class SkillCostBaseline:
    skill_id: str
    avg_cost_cents: float
    p50_cost_cents: float
    p95_cost_cents: float
    p99_cost_cents: float
    sample_count: int
    window_hours: int  # e.g., 24h, 7d
    last_updated: datetime
```

**Storage:** TimescaleDB or PostgreSQL with time partitioning

### 3.3 Drift Detector

Compares simulated vs actual cost per execution:

```python
@dataclass
class DriftMetric:
    skill_id: str
    simulated_cents: int
    actual_cents: int
    drift_cents: int  # actual - simulated
    drift_percentage: float
    timestamp: datetime
```

**Alerting Thresholds:**
- WARN: |drift| > 25%
- ERROR: |drift| > 50%
- CRITICAL: |drift| > 100% for 3+ consecutive executions

### 3.4 Trend Analyzer

Forecasts budget consumption:

```python
@dataclass
class CostTrend:
    skill_id: str
    trend_direction: str  # "increasing", "stable", "decreasing"
    daily_avg_change_cents: float
    weekly_forecast_cents: int
    confidence: float  # 0.0 - 1.0
```

**Algorithm:** Simple linear regression over 7-day window

### 3.5 Scenario Replayer

Evaluates alternative plans:

```python
@dataclass
class ScenarioResult:
    plan_id: str
    total_estimated_cost: int
    estimated_duration_ms: int
    risk_score: float  # 0.0 - 1.0
    alternatives: List[AlternativePlan]
```

---

## 4. API Design

### 4.1 Simulate Endpoint (Enhanced)

```
POST /v2/simulate
```

Request:
```json
{
  "plan": [
    {"skill_id": "http_call", "params": {...}},
    {"skill_id": "llm_invoke", "params": {...}}
  ],
  "budget_cents": 1000,
  "include_alternatives": true,
  "include_trends": true
}
```

Response:
```json
{
  "feasible": true,
  "estimated_cost_cents": 45,
  "estimated_duration_ms": 3500,
  "budget_sufficient": true,
  "cost_breakdown": [
    {"skill_id": "http_call", "estimated": 0, "baseline_p95": 0, "drift_warning": false},
    {"skill_id": "llm_invoke", "estimated": 45, "baseline_p95": 52, "drift_warning": false}
  ],
  "trend": {
    "llm_invoke": {"direction": "increasing", "daily_change": 2.3}
  },
  "alternatives": [
    {
      "plan": [...],
      "estimated_cost_cents": 12,
      "tradeoff": "uses cached data, may be stale"
    }
  ]
}
```

### 4.2 Record Actual Cost Endpoint

```
POST /v2/cost/record
```

Request:
```json
{
  "execution_id": "exec-123",
  "skill_id": "llm_invoke",
  "simulated_cents": 45,
  "actual_cents": 48
}
```

### 4.3 Get Baselines Endpoint

```
GET /v2/cost/baselines?skill_id=llm_invoke&window=24h
```

---

## 5. Database Schema

### 5.1 Cost Baselines Table

```sql
CREATE TABLE cost_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id VARCHAR(255) NOT NULL,
    window_type VARCHAR(50) NOT NULL,  -- '1h', '24h', '7d'
    avg_cost_cents DECIMAL(10,2),
    p50_cost_cents DECIMAL(10,2),
    p95_cost_cents DECIMAL(10,2),
    p99_cost_cents DECIMAL(10,2),
    sample_count INTEGER,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(skill_id, window_type)
);
```

### 5.2 Cost Records Table (for drift analysis)

```sql
CREATE TABLE cost_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id VARCHAR(255) NOT NULL,
    skill_id VARCHAR(255) NOT NULL,
    simulated_cents INTEGER NOT NULL,
    actual_cents INTEGER NOT NULL,
    drift_cents INTEGER GENERATED ALWAYS AS (actual_cents - simulated_cents) STORED,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_skill_recorded (skill_id, recorded_at)
);
```

---

## 6. Integration Points

### 6.1 Workflow Engine Integration

```python
# Before skill execution
simulation = cost_simulator_v2.simulate(plan, budget)
if not simulation.feasible:
    return StructuredOutcome.failure(
        code="BUDGET_INSUFFICIENT",
        recovery_mode="ABORT"
    )

# After skill execution
cost_simulator_v2.record_actual(
    execution_id=step.id,
    skill_id=step.skill_id,
    simulated=simulation.cost_breakdown[step.index].estimated,
    actual=step.actual_cost
)
```

### 6.2 Metrics Integration

```python
# Record drift to Prometheus
record_cost_simulation_drift(
    skill_id=step.skill_id,
    simulated_cents=simulated,
    actual_cents=actual
)
```

---

## 7. Migration Path

### Phase 1: Metrics (Week 1)
- Add drift recording to existing V1
- Start collecting actual costs
- Deploy Prometheus metrics

### Phase 2: Baselines (Week 2)
- Implement baseline computation
- Deploy cost_baselines table
- Backfill from existing data

### Phase 3: API (Week 3)
- Deploy V2 simulate endpoint
- Add trend analysis
- Add scenario replay

### Phase 4: Integration (Week 4)
- Wire to workflow engine
- Add Grafana dashboards
- Enable drift alerts

---

## 8. Success Criteria

| Metric | Target |
|--------|--------|
| Simulation accuracy | < 20% drift for 90% of executions |
| Baseline freshness | Updated every 1 hour |
| Trend prediction | < 30% error on weekly forecast |
| API latency | < 50ms p95 |

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Cold start (no baselines) | Fall back to V1 static estimates |
| Database growth | Time-based partitioning + retention policy |
| Accuracy degradation | Alerting on sustained high drift |

---

## 10. Open Questions

1. Should baselines be tenant-scoped or global?
2. What retention period for cost_records?
3. Should alternatives consider external API pricing changes?

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-03 | Initial V2 specification |
