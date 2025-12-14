# PIN-076: M18 CARE-L + SBA Evolution (Autonomous Strategic Agents)

**Status:** COMPLETE
**Created:** 2025-12-14
**Milestone:** M18

---

## Overview

M18 is the first milestone where **the platform optimizes itself** across two learning layers:

1. **CARE-L (Learning Router)** - Decides who should act, learns from outcomes
2. **SBA-L1 (Agent Evolution)** - Improves agents that act, detects drift

Both layers reinforce each other in a **sealed bidirectional feedback loop**.

### M18.2 Additions

The production-grade M18 includes:
- **Governor/Stabilization Layer** - Prevents oscillation and overcorrection
- **Bidirectional Feedback Loop** - CARE-L ↔ SBA sealed loop
- **SLA-aware Scoring** - Task criticality and complexity weighting
- **Explainability Interface** - Explain routing decisions
- **Inter-Agent Coordination** - Capability redistribution on failure
- **Offline Batch Learning** - Retrospective parameter tuning

---

## Architecture

### Two Learning Engines

```
                    ┌─────────────────────────────────────────┐
                    │           INCOMING TASK                  │
                    └─────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CARE-L (Learning Router)                             │
│                                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────────┐    │
│  │ Reputation  │   │ Hysteresis  │   │ Quarantine  │   │  Prediction  │    │
│  │   Score     │──▶│   Filter    │──▶│   Check     │──▶│    Model     │    │
│  └─────────────┘   └─────────────┘   └─────────────┘   └──────────────┘    │
│         ▲                                                      │            │
│         │                 LEARNS FROM                          ▼            │
│         │          ◄──────────────────────         ┌──────────────────┐    │
│         │                                          │  Route Decision  │    │
│         │                                          └──────────────────┘    │
└─────────┼──────────────────────────────────────────────────┼────────────────┘
          │                                                  │
          │              FEEDBACK LOOP                       ▼
          │                                    ┌─────────────────────────────┐
          │                                    │      SELECTED AGENT         │
          │                                    └─────────────────────────────┘
          │                                                  │
          │                                                  ▼
┌─────────┼─────────────────────────────────────────────────────────────────────┐
│         │                    SBA-L1 (Agent Evolution)                          │
│         │                                                                      │
│  ┌──────┴──────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────────┐      │
│  │  Outcome    │   │  Boundary   │   │   Drift     │   │  Strategy    │      │
│  │  Recording  │──▶│  Detector   │──▶│   Engine    │──▶│  Adjuster    │      │
│  └─────────────┘   └─────────────┘   └─────────────┘   └──────────────┘      │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## CARE-L (Learning Router Layer)

### 1. Agent Reputation System

Reputation is a computed score (0.0-1.0) based on historical performance:

```python
class AgentReputation:
    agent_id: str
    success_rate: float        # Rolling success rate
    latency_percentile: float  # Latency ranking (lower = better)
    violation_count: int       # Boundary/risk violations
    quarantine_count: int      # Times quarantined
    reputation_score: float    # Computed 0.0-1.0
    last_updated: datetime
```

**Reputation Formula:**

```
reputation = (
    success_rate * 0.40 +
    (1 - latency_percentile) * 0.20 +
    (1 - violation_rate) * 0.25 +
    consistency_bonus * 0.15
)
```

### 2. Predictive Routing

Routes tasks based on probability-of-success, not just static rules:

```python
def predict_success_probability(
    agent_id: str,
    task: RoutingRequest,
) -> float:
    """
    Predict probability of success for agent on task.

    Factors:
    - Historical success rate for similar tasks
    - Agent reputation score
    - Current load factor
    - Time of day patterns (optional)
    """
```

### 3. Quarantine System

Agents with high failure rates are isolated:

| State | Entry Condition | Exit Condition |
|-------|-----------------|----------------|
| ACTIVE | Default | - |
| PROBATION | 3+ failures in 5min | 5 successes in row |
| QUARANTINED | 5+ failures OR violation | Manual review OR 30min cool-off |

```python
class QuarantineState(str, Enum):
    ACTIVE = "active"           # Normal operation
    PROBATION = "probation"     # Warning state, monitored
    QUARANTINED = "quarantined" # Blocked from routing
```

### 4. Hysteresis-Stable Routing

Prevents oscillation between agents during performance swings:

```python
HYSTERESIS_THRESHOLD = 0.15  # 15% score difference required to switch
HYSTERESIS_WINDOW = 300      # 5 minute stability window
```

If Agent A is currently selected and Agent B scores higher:
- Only switch if `score_B - score_A > HYSTERESIS_THRESHOLD`
- AND Agent B has been consistently better for `HYSTERESIS_WINDOW`

### 5. Self-Tuning Parameters

Router thresholds and weights adjust automatically:

```python
class LearningParameters:
    # Adjustable thresholds
    confidence_block: float = 0.35      # Auto-adjusted
    confidence_fallback: float = 0.55   # Auto-adjusted
    quarantine_threshold: int = 5       # Auto-adjusted

    # Learning rate
    adaptation_rate: float = 0.01       # How fast to adjust

    def tune_from_outcomes(self, outcomes: List[RoutingOutcome]):
        """Adjust parameters based on routing outcomes."""
```

---

## SBA-L1 (Agent Evolution Layer)

### 1. Boundary Awareness

Agents track and refine their "Where-to-Play" limits:

```python
class BoundaryViolation:
    agent_id: str
    violation_type: str       # "domain", "tool", "context", "risk"
    description: str
    task_description: str
    detected_at: datetime
    auto_reported: bool       # Agent self-reported vs system detected
```

Violations feed back into:
- CARE-L reputation (lowers score)
- SBA boundary refinement (tightens constraints)

### 2. Capability Awareness

Real capability tracking via probes:

```python
class CapabilityProbeHistory:
    agent_id: str
    capability: str           # Tool/API name
    probe_results: List[ProbeResult]
    availability_rate: float  # % of time available
    last_verified: datetime
```

### 3. Dynamic How-to-Win

Agents adjust strategy when success rate drops:

```python
class StrategyAdjustment:
    agent_id: str
    trigger: str              # "low_success", "high_latency", "drift"
    old_strategy: Dict
    new_strategy: Dict
    adjustment_type: str      # "task_split", "step_refinement", "fallback_add"
    adjusted_at: datetime
```

### 4. Drift Detection Engine

Detects when agent strategies no longer match environment:

```python
class DriftType(str, Enum):
    DATA_DRIFT = "data_drift"         # Input distribution changed
    DOMAIN_DRIFT = "domain_drift"     # Task domain shifted
    BEHAVIOR_DRIFT = "behavior_drift" # Agent outputs changed
    BOUNDARY_DRIFT = "boundary_drift" # Boundaries too tight/loose

class DriftSignal:
    agent_id: str
    drift_type: DriftType
    severity: float           # 0.0-1.0
    evidence: Dict            # Supporting data
    recommendation: str       # "expand_boundary", "update_strategy", etc.
    detected_at: datetime
```

**Drift Detection Methods:**

| Method | Detects |
|--------|---------|
| Success Rate Degradation | Tasks agent used to complete now failing |
| Boundary Violation Spike | Frequent out-of-scope attempts |
| Latency Increase | Agent taking longer than historical baseline |
| Tool Failure Pattern | Dependencies becoming unreliable |

---

## Database Schema

### New Tables

```sql
-- Agent reputation tracking
CREATE TABLE routing.agent_reputation (
    agent_id VARCHAR(128) PRIMARY KEY,
    reputation_score FLOAT NOT NULL DEFAULT 1.0,
    success_rate FLOAT NOT NULL DEFAULT 1.0,
    latency_percentile FLOAT NOT NULL DEFAULT 0.5,
    violation_count INT NOT NULL DEFAULT 0,
    quarantine_count INT NOT NULL DEFAULT 0,
    quarantine_state VARCHAR(20) NOT NULL DEFAULT 'active',
    quarantine_until TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_failure_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Boundary violations
CREATE TABLE agents.boundary_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(128) NOT NULL,
    violation_type VARCHAR(50) NOT NULL,
    description TEXT,
    task_description TEXT,
    task_domain VARCHAR(100),
    severity FLOAT NOT NULL DEFAULT 0.5,
    auto_reported BOOLEAN NOT NULL DEFAULT false,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Drift signals
CREATE TABLE agents.drift_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(128) NOT NULL,
    drift_type VARCHAR(50) NOT NULL,
    severity FLOAT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}',
    recommendation TEXT,
    acknowledged BOOLEAN NOT NULL DEFAULT false,
    auto_adjusted BOOLEAN NOT NULL DEFAULT false,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Strategy adjustments audit
CREATE TABLE agents.strategy_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(128) NOT NULL,
    trigger VARCHAR(50) NOT NULL,
    adjustment_type VARCHAR(50) NOT NULL,
    old_strategy JSONB NOT NULL,
    new_strategy JSONB NOT NULL,
    success_rate_before FLOAT,
    success_rate_after FLOAT,
    adjusted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Learning parameters (router self-tuning)
CREATE TABLE routing.learning_parameters (
    id SERIAL PRIMARY KEY,
    parameter_name VARCHAR(100) NOT NULL UNIQUE,
    current_value FLOAT NOT NULL,
    min_value FLOAT NOT NULL,
    max_value FLOAT NOT NULL,
    adaptation_rate FLOAT NOT NULL DEFAULT 0.01,
    last_adjusted_at TIMESTAMPTZ,
    adjustment_reason TEXT
);
```

---

## M18.2: Governor/Stabilization Layer

The Governor prevents the learning system from destabilizing:

```python
class Governor:
    """Prevents oscillation and overcorrection."""

    # Limits
    MAX_ADJUSTMENTS_PER_HOUR = 5      # Per agent
    MAX_ADJUSTMENT_MAGNITUDE = 0.10   # 10% max change
    GLOBAL_FREEZE_THRESHOLD = 10      # System-wide freeze
    FREEZE_DURATION = 900             # 15 min freeze window

    # Rollback
    ROLLBACK_WINDOW = 1800            # 30 min to evaluate
    MIN_IMPROVEMENT_REQUIRED = 0.05   # 5% improvement needed
    AUTO_ROLLBACK_ENABLED = True      # Auto-rollback bad adjustments
```

**Governor States:**
- `STABLE` - Normal operation
- `CAUTIOUS` - Reduced adjustment rate
- `FROZEN` - No adjustments allowed

---

## M18.2: Bidirectional Feedback Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ROUTING OUTCOME                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│      FeedbackLoop           │──▶│    SBA Evolution            │
│                             │   │                             │
│  - Record outcome           │   │  - Record violation         │
│  - Update SLA score         │   │  - Detect drift             │
│  - Compute reputation       │   │  - Suggest adjustment       │
│                             │◀──│  - Update fulfillment       │
│  - reputation_delta         │   │                             │
└─────────────────────────────┘   └─────────────────────────────┘
```

The `FeedbackLoop` class manages:
- Routing outcomes → SBA drift signals
- SBA adjustments → CARE-L reputation updates
- Inter-agent capability redistribution

---

## M18.2: SLA-aware Scoring

Tasks are weighted by priority and complexity:

```python
class TaskPriority(str, Enum):
    CRITICAL = "critical"  # 2x weight
    HIGH = "high"          # 1.5x weight
    NORMAL = "normal"      # 1x weight
    LOW = "low"            # 0.8x weight

class TaskComplexity(str, Enum):
    SIMPLE = "simple"      # 0.8x difficulty
    MODERATE = "moderate"  # 1x difficulty
    COMPLEX = "complex"    # 1.3x difficulty
```

SLA-adjusted reputation:
```python
def compute_sla_adjusted_reputation(agent_id, base_reputation):
    sla_score = get_sla_score(agent_id)
    adjustment = 1.0 - (sla_score.sla_gap * 0.5)
    return base_reputation * max(0.5, min(1.5, adjustment))
```

---

## M18.2: Explainability Interface

Endpoints for understanding routing decisions:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/routing/explain/{request_id}` | POST | Explain routing decision |
| `/api/v1/agents/{agent_id}/evolution` | GET | Get agent evolution report |
| `/api/v1/routing/stability` | GET | Get system stability metrics |
| `/api/v1/routing/stability/freeze` | POST | Manually freeze system |
| `/api/v1/routing/stability/unfreeze` | POST | Manually unfreeze system |
| `/api/v1/routing/batch-learning` | POST | Trigger batch learning |
| `/api/v1/agents/{agent_id}/reputation` | GET | Get agent reputation |
| `/api/v1/agents/{agent_id}/sla` | GET | Get agent SLA score |
| `/api/v1/agents/{agent_id}/successors` | GET | Get successor mapping |

---

## M18.2: Inter-Agent Coordination

When an agent struggles with a capability, the system recommends successors:

```python
async def recommend_capability_redistribution(
    weak_agent_id: str,
    capability: str,
) -> Optional[str]:
    """Find agents that handle similar tasks well."""

async def get_successor_mapping(agent_id: str) -> Dict[str, str]:
    """Get mapping of capabilities → recommended successor agents."""
```

---

## API Endpoints

### CARE-L (Router Learning)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/agents/{agent_id}/reputation` | GET | Get agent reputation |
| `/api/v1/agents/{agent_id}/sla` | GET | Get agent SLA score |
| `/api/v1/agents/{agent_id}/successors` | GET | Get successor mapping |
| `/api/v1/routing/stability` | GET | Get system stability metrics |
| `/api/v1/routing/stability/freeze` | POST | Manually freeze system |
| `/api/v1/routing/stability/unfreeze` | POST | Manually unfreeze |
| `/api/v1/routing/batch-learning` | POST | Trigger batch learning |
| `/api/v1/routing/explain/{request_id}` | POST | Explain routing decision |

### SBA Evolution

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/agents/{agent_id}/evolution` | GET | Get evolution report |
| `/api/v1/sba/{agent_id}/violations` | GET | Get boundary violations |
| `/api/v1/sba/{agent_id}/violations` | POST | Report violation |
| `/api/v1/sba/{agent_id}/drift` | GET | Get drift signals |
| `/api/v1/sba/{agent_id}/drift/acknowledge` | POST | Acknowledge drift |
| `/api/v1/sba/{agent_id}/strategy/adjust` | POST | Trigger strategy adjustment |
| `/api/v1/sba/{agent_id}/strategy/history` | GET | Get adjustment history |

---

## Implementation Files

### New Files

| File | Purpose |
|------|---------|
| `app/routing/learning.py` | CARE-L learning engine (reputation, quarantine, hysteresis) |
| `app/routing/governor.py` | Stabilization layer (rate limits, freeze, rollback) |
| `app/routing/feedback.py` | Bidirectional feedback loop (SLA, batch learning) |
| `app/agents/sba/evolution.py` | SBA evolution engine (drift, violations, adjustments) |
| `alembic/versions/031_m18_care_l_sba_evolution.py` | Database migration |
| `tests/test_m18_care_l.py` | Core M18 tests (35 tests) |
| `tests/test_m18_advanced.py` | Advanced M18 tests (27 tests) |

### Modified Files

| File | Changes |
|------|---------|
| `app/routing/__init__.py` | Export Governor, FeedbackLoop, new models |
| `app/agents/sba/__init__.py` | Export evolution engine |
| `app/api/agents.py` | Add M18 explainability endpoints |

---

## Feedback Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ROUTING DECISION                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TASK EXECUTION                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌──────────┐   ┌──────────┐   ┌──────────┐
              │ SUCCESS  │   │ FAILURE  │   │ VIOLATION│
              └──────────┘   └──────────┘   └──────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OUTCOME RECORDING                                     │
│                                                                              │
│  RoutingOutcome {                                                            │
│    request_id, agent_id, success, latency_ms,                               │
│    risk_violated, boundary_violated, violation_type                          │
│  }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│        CARE-L Update        │   │      SBA-L1 Update          │
│                             │   │                             │
│  - Update reputation        │   │  - Check boundaries         │
│  - Adjust quarantine state  │   │  - Detect drift             │
│  - Tune parameters          │   │  - Adjust strategy          │
│  - Update performance vec   │   │  - Update fulfillment       │
└─────────────────────────────┘   └─────────────────────────────┘
```

---

## Acceptance Criteria (DoD)

### CARE-L

- [x] Agent reputation computed and persisted
- [x] Quarantine system with ACTIVE/PROBATION/QUARANTINED states
- [x] Hysteresis prevents routing oscillation
- [x] Learning parameters auto-tune from outcomes
- [x] Predictive routing uses reputation in scoring

### SBA Evolution

- [x] Boundary violations tracked and surfaced
- [x] Drift detection for data/domain/behavior/boundary
- [x] Strategy adjustments logged with audit trail
- [x] Agents can self-report violations

### M18.2 Additions

- [x] Governor prevents oscillation with rate limits
- [x] Auto-rollback on performance degradation
- [x] SLA-aware scoring with task priority/complexity
- [x] Bidirectional feedback loop (CARE-L ↔ SBA)
- [x] Inter-agent coordination (successor mapping)
- [x] Offline batch learning
- [x] Explainability endpoints

### Integration

- [x] Feedback loop connects outcome → reputation → routing
- [x] Drift signals lower agent reputation
- [x] Quarantined agents excluded from routing
- [x] SLA gap affects routing decisions

### Testing

- [x] 62 tests covering:
  - Reputation calculation (5 tests)
  - Quarantine state machine (5 tests)
  - Hysteresis stability (5 tests)
  - Drift detection (5 tests)
  - Boundary violations (5 tests)
  - End-to-end feedback loop (10 tests)
  - System convergence (4 tests)
  - Oscillation stress (4 tests)
  - Boundary cascade (3 tests)
  - Hysteresis vs drift (3 tests)
  - Self-tuning instability (5 tests)
  - Integration stress (3 tests)
  - Edge cases (5 tests)

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-072 | M15.1 SBA Foundations (schema) |
| PIN-075 | M17 CARE Routing Engine |
| PIN-074 | M16 Governance Console |

---

## Next Steps (M19+)

1. **Multi-tenant routing policies**
2. **A/B testing** for routing strategies
3. **WebSocket streaming** for live updates
4. **ML-based prediction** (replace heuristics)
5. **Agent skill discovery** (proactive capability detection)
