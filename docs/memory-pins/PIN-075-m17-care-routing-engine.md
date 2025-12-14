# PIN-075: M17 Cascade-Aware Routing Engine (CARE)

**Status:** COMPLETE
**Created:** 2025-12-14
**Milestone:** M17

---

## Overview

M17 implements the **Cascade-Aware Routing Engine (CARE)** - a strategic router that routes tasks to agents based on their Strategy Cascade, not just workload.

This makes the system:
- **Intention-aligned** - Routes based on agent purpose
- **Risk-aware** - Considers risk policies in routing
- **Capability-constrained** - Hard gates on infrastructure availability

---

## Architecture

### 5-Stage Pipeline

```
Incoming Task
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: ASPIRATION → Success Metric                        │
│   Maps winning_aspiration to: COST | LATENCY | ACCURACY |   │
│   RISK_MIN | BALANCED                                       │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: DOMAIN_FILTER → Where-to-Play                      │
│   - Domain match                                            │
│   - Required tools available                                │
│   - Context allowed                                         │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: STRATEGY → How-to-Win                              │
│   - Difficulty threshold check                              │
│   - Risk policy compatibility                               │
│   - Fulfillment score threshold                             │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 4: CAPABILITY → Hard Gate                             │
│   Real-time infrastructure probes:                          │
│   - Database connectivity                                   │
│   - Redis availability                                      │
│   - API keys present                                        │
│   - Dependencies available                                  │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ Stage 5: ORCHESTRATOR → Mode Selection                      │
│   - PARALLEL: Independent tasks to swarm                    │
│   - HIERARCHICAL: Parent delegates to sub-agents            │
│   - BLACKBOARD: Shared memory, opportunistic                │
│   - SEQUENTIAL: One-by-one execution                        │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
Routing Decision → Best Agent Selected
```

---

## API Endpoints

### Routing Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/routing/cascade-evaluate` | POST | Evaluate agents through CARE pipeline (no routing) |
| `/api/v1/routing/dispatch` | POST | Execute full pipeline and route to best agent |
| `/api/v1/routing/stats` | GET | Get routing statistics |

### Strategy Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/agents/{id}/strategy` | GET | Get agent's Strategy Cascade |
| `/api/v1/agents/{id}/strategy/update` | POST | Hot-swap routing configuration |

---

## Implementation Files

### Backend (4 files)

| File | Purpose |
|------|---------|
| `app/routing/__init__.py` | Module exports |
| `app/routing/models.py` | Pydantic models for routing |
| `app/routing/probes.py` | Capability probes with Redis caching |
| `app/routing/care.py` | CARE engine with 5-stage pipeline |

### Migration

| File | Purpose |
|------|---------|
| `alembic/versions/030_m17_care_routing.py` | Schema for routing.routing_decisions, routing.capability_probes |

### Tests

| File | Purpose |
|------|---------|
| `tests/test_m17_care.py` | 25 scenario tests |

---

## Routing Models

### Success Metrics

```python
class SuccessMetric(str, Enum):
    COST = "cost"           # Minimize cost/resource usage
    LATENCY = "latency"     # Minimize response time
    ACCURACY = "accuracy"   # Maximize correctness
    RISK_MIN = "risk_min"   # Minimize risk exposure
    BALANCED = "balanced"   # Balance all factors
```

### Orchestrator Modes

```python
class OrchestratorMode(str, Enum):
    PARALLEL = "parallel"           # Independent tasks to workers
    HIERARCHICAL = "hierarchical"   # Parent delegates to sub-agents
    BLACKBOARD = "blackboard"       # Shared memory, opportunistic
    SEQUENTIAL = "sequential"       # One-by-one execution
```

### Risk Policies

```python
class RiskPolicy(str, Enum):
    STRICT = "strict"       # Extra validation, retry on failure
    BALANCED = "balanced"   # Standard validation
    FAST = "fast"           # Skip validation, no retry
```

---

## Capability Probes

Real-time infrastructure checks with Redis caching:

| Probe | Check | Cache TTL |
|-------|-------|-----------|
| DATABASE | SELECT 1 | 60s |
| REDIS | PING | 60s |
| API_KEY | Env var exists | 60s |
| HTTP | GET health endpoint | 60s |
| AGENT | Registry lookup | 60s |

All probes target **<150ms** per check.

---

## Usage Examples

### Evaluate Agents

```bash
curl -X POST /api/v1/routing/cascade-evaluate \
  -d '{
    "task_description": "Process batch data files",
    "task_domain": "data-processing",
    "difficulty": "medium",
    "risk_tolerance": "balanced"
  }'
```

Response:
```json
{
  "evaluated_count": 2,
  "eligible_count": 1,
  "agents": [
    {
      "agent_id": "data_worker",
      "eligible": true,
      "score": 0.85,
      "success_metric": "accuracy",
      "stages": [
        {"stage": "aspiration", "passed": true},
        {"stage": "domain_filter", "passed": true},
        {"stage": "strategy", "passed": true},
        {"stage": "capability", "passed": true},
        {"stage": "orchestrator", "passed": true}
      ]
    }
  ]
}
```

### Dispatch Task

```bash
curl -X POST /api/v1/routing/dispatch \
  -d '{
    "task_description": "Process batch data files",
    "difficulty": "medium"
  }'
```

Response:
```json
{
  "request_id": "abc123",
  "routed": true,
  "selected_agent_id": "data_worker",
  "success_metric": "accuracy",
  "orchestrator_mode": "parallel",
  "decision_reason": "Selected data_worker (score=0.85)"
}
```

### Hot-Swap Routing Config

```bash
curl -X POST /api/v1/agents/data_worker/strategy/update \
  -d '{
    "risk_policy": "strict",
    "difficulty_threshold": "high",
    "orchestrator_mode": "parallel"
  }'
```

---

## Aspiration → Metric Mapping

Keywords in `winning_aspiration.description` map to success metrics:

| Keywords | Metric |
|----------|--------|
| cost, budget, cheap, efficient | COST |
| fast, quick, speed, real-time | LATENCY |
| accurate, correct, precise, thorough | ACCURACY |
| safe, secure, risk, cautious | RISK_MIN |
| (no match) | BALANCED |

---

## Routing Config Extension

New fields added to SBA schema:

```json
{
  "routing_config": {
    "success_metric": "accuracy",
    "difficulty_threshold": "medium",
    "risk_policy": "balanced",
    "orchestrator_mode": "parallel",
    "max_parallel_tasks": 3,
    "escalation_enabled": true
  }
}
```

---

## Database Schema

### routing.routing_decisions

Audit log of all routing decisions:

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| request_id | VARCHAR(32) | Request identifier |
| task_description | TEXT | Task being routed |
| selected_agent_id | VARCHAR(100) | Chosen agent |
| success_metric | VARCHAR(20) | Derived metric |
| orchestrator_mode | VARCHAR(20) | Selected mode |
| routed | BOOLEAN | Success flag |
| error | TEXT | Error if failed |
| actionable_fix | TEXT | Fix instruction |
| total_latency_ms | FLOAT | Total routing time |
| decided_at | TIMESTAMP | Decision time |

### routing.capability_probes

Cached probe results (for persistence):

| Column | Type | Description |
|--------|------|-------------|
| probe_type | VARCHAR(20) | SMTP, DNS, API_KEY, etc. |
| probe_name | VARCHAR(200) | Target identifier |
| available | BOOLEAN | Probe result |
| latency_ms | FLOAT | Probe duration |
| expires_at | TIMESTAMP | Cache expiry |

---

## What Changes After M17

| Area | Before | After M17 |
|------|--------|-----------|
| Routing | Round-robin, skill-based | Strategic, risk-aware |
| Failures | Silent, cryptic | Actionable infra errors |
| Performance | Equal treatment | Task-specific optimization |
| Risk | Unbounded | Risk policy built-in |
| Capacity | Naive | Real-time resource gates |
| Orchestration | Fixed | Dynamic mode switching |

---

## Acceptance Criteria (DoD)

### Functional
- [x] Different cascades route to different paths
- [x] Missing capability blocks with remediation message
- [x] Success metric influences routing decisions
- [x] Orchestrator mode dynamically adjusts
- [x] Stage results include latency metrics

### Infrastructure
- [x] Hard gate checks target <150ms
- [x] All decisions logged as structured JSON
- [x] Capability probe caching (Redis, 60s TTL)

### Testing
- [x] Test file: `tests/test_m17_care.py`
- [x] Aspiration → metric inference tests
- [x] Orchestrator mode inference tests
- [x] Stage evaluation tests
- [x] Error handling tests

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-072 | M15.1 SBA Foundations (schema) |
| PIN-073 | M15.1.1 SBA Inspector UI |
| PIN-074 | M16 Governance Console |

---

## Next Steps (M18+)

1. **Persist routing decisions** to database for analytics
2. **WebSocket streaming** for live routing updates
3. **Fulfillment feedback loop** - adjust routing based on outcomes
4. **Multi-tenant routing policies**
5. **A/B testing** for routing strategies
