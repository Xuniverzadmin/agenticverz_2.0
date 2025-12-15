# PIN-078: M19 Policy Layer - Constitutional Governance

**Status:** COMPLETE
**Created:** 2025-12-15
**Milestone:** M19

---

## Overview

M19 introduces the **Policy Layer** - a Constitutional Governance system that every agent and subsystem must consult before deciding, routing, executing, escalating, or self-modifying.

The Policy Engine acts as the "Constitution" of the multi-agent ecosystem, ensuring:
- Compliance with jurisdictional and data handling rules
- Ethical constraints (no coercion, no fabrication, transparency)
- Risk ceilings (cost, retry, cascade limits)
- Safety rules (hard stops, escalations, cooldowns)
- Business rules (budgets, tier access, feature gates)

---

## Architecture Position

```
                        ┌─────────────────────┐
                        │     M19 POLICY      │  ← "Constitution"
                        │   LAYER (NEW)       │
                        └──────────┬──────────┘
                                   │
                                   ▼
            ┌──────────────────────┴──────────────────────┐
            │                                             │
            ▼                                             ▼
    ┌───────────────┐                           ┌─────────────────┐
    │   M18 CARE-L  │                           │   M18 SBA       │
    │   (Routing)   │                           │   (Strategy)    │
    └───────────────┘                           └─────────────────┘
            │                                             │
            └──────────────────────┬──────────────────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   M18 Governor      │
                        │   (Stabilization)   │
                        └─────────────────────┘
```

---

## Core Components

### 1. Policy Engine (`app/policy/engine.py`)

The central evaluation engine. Every action request flows through `evaluate()`:

```python
from app.policy import get_policy_engine, PolicyEvaluationRequest, ActionType

engine = get_policy_engine()
result = await engine.evaluate(PolicyEvaluationRequest(
    action_type=ActionType.EXECUTE,
    agent_id="agent-123",
    tenant_id="tenant-456",
    proposed_action="send_email",
    estimated_cost=0.05,
))

if result.decision == PolicyDecision.BLOCK:
    # Handle blocked action
    print(f"Blocked: {result.decision_reason}")
elif result.decision == PolicyDecision.MODIFY:
    # Apply modifications
    for mod in result.modifications:
        apply_modification(mod)
else:
    # Proceed with action
    execute_action()
```

### 2. Policy Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **Compliance** | Jurisdictional, data handling | GDPR, PII restrictions |
| **Ethical** | Non-negotiables | No coercion, no fabrication |
| **Risk** | Dynamic limits | Cost/hour, retry/minute |
| **Safety** | Hard stops | Command blocks, cooldowns |
| **Business** | Commercial rules | Budgets, tier gates |

### 3. Action Types

All agent actions requiring policy evaluation:

- `ROUTE` - Routing decisions (CARE)
- `EXECUTE` - Skill/task execution
- `ADAPT` - Strategy adaptation (SBA)
- `ESCALATE` - Escalation to human
- `SELF_MODIFY` - Agent self-modification
- `SPAWN` - Agent spawning
- `INVOKE` - Agent invocation
- `DATA_ACCESS` - Data access request
- `EXTERNAL_CALL` - External API call

### 4. Policy Decisions

- `ALLOW` - Action permitted
- `BLOCK` - Action denied (with violations)
- `MODIFY` - Action permitted with modifications

---

## Database Schema

Created in `policy` schema:

| Table | Purpose |
|-------|---------|
| `policies` | Policy definitions with versioning |
| `evaluations` | Audit log of all evaluations |
| `violations` | Violation records |
| `risk_ceilings` | Dynamic risk limits |
| `safety_rules` | Hard stop rules |
| `ethical_constraints` | Non-negotiable constraints |
| `business_rules` | Commercial rules |

Migration: `backend/alembic/versions/032_m19_policy_layer.py`

---

## API Endpoints

Prefix: `/api/v1/policy-layer`

### Core Evaluation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/evaluate` | Evaluate action against policies |
| POST | `/simulate` | Dry-run evaluation (no side effects) |
| POST | `/evaluate/batch` | Batch evaluation (max 50) |

### State & Reload

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/state` | Current policy layer state |
| POST | `/reload` | Hot-reload policies from DB |

### Violations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/violations` | List violations |
| GET | `/violations/{id}` | Get specific violation |
| POST | `/violations/{id}/acknowledge` | Mark reviewed |

### Risk Ceilings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/risk-ceilings` | List ceilings |
| GET | `/risk-ceilings/{id}` | Get ceiling |
| PATCH | `/risk-ceilings/{id}` | Update ceiling |
| POST | `/risk-ceilings/{id}/reset` | Reset value |

### Safety & Ethical

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/safety-rules` | List safety rules |
| PATCH | `/safety-rules/{id}` | Update rule |
| GET | `/ethical-constraints` | List constraints |

### Cooldowns

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cooldowns` | List active cooldowns |
| DELETE | `/cooldowns/{agent_id}` | Clear cooldowns |

---

## Default Policies (Seeded)

### Ethical Constraints

1. **no_coercion** - Blocks coercive language
2. **no_fabrication** - Blocks data fabrication
3. **no_manipulation** - Blocks manipulation attempts
4. **transparency** - Requires explainability

### Risk Ceilings

1. **hourly_cost_ceiling** - $100/hour (throttle)
2. **retry_rate_ceiling** - 30/minute (block)
3. **cascade_depth_ceiling** - 5 levels (block)
4. **concurrent_agents_ceiling** - 50 agents (throttle)

### Safety Rules

1. **block_system_commands** - Blocks rm -rf, shutdown, etc.
2. **escalate_high_cost** - Requires approval for $50+
3. **cooldown_on_failure_spike** - 5 failures → cooldown
4. **block_external_pii** - Blocks PII to external services

---

## M18 Governor Integration

Severe violations (severity >= 0.9) automatically trigger M18 Governor:

```python
# In PolicyEngine._route_to_governor()
if violation.severity >= 0.9:
    await self._governor.force_freeze(
        duration_seconds=300,
        reason=f"Policy violation: {violation.description}"
    )
    violation.governor_action = "freeze"
```

The Policy Engine singleton automatically wires to the Governor:

```python
def get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
        from app.routing import get_governor
        _policy_engine.set_governor(get_governor())
    return _policy_engine
```

---

## Files Added/Modified

### New Files

| File | Description |
|------|-------------|
| `backend/app/policy/__init__.py` | Module exports |
| `backend/app/policy/engine.py` | Policy Engine core |
| `backend/app/policy/models.py` | Policy models |
| `backend/app/api/policy_layer.py` | API endpoints |
| `backend/alembic/versions/032_m19_policy_layer.py` | DB migration |
| `backend/tests/test_m19_policy.py` | Comprehensive tests |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/main.py` | Added policy_layer_router |

---

## Testing

Run M19 tests:

```bash
cd backend
PYTHONPATH=. python -m pytest tests/test_m19_policy.py -v
```

Test coverage:
- Policy evaluation (all action types)
- Ethical constraints (coercion, fabrication, transparency)
- Safety rules (blocks, cooldowns, escalations)
- Risk ceilings (cost, retry, cascade)
- Business rules (budgets, tiers, gates)
- Governor integration (freeze on violations)
- State and metrics
- Edge cases

---

## Acceptance Criteria Status

| AC | Description | Status |
|----|-------------|--------|
| AC1 | Runtime policy evaluation | ✅ PASS |
| AC2 | Block/Allow/Modify decisions | ✅ PASS |
| AC3 | Violations routed to Governor | ✅ PASS |
| AC4 | Policy versioning & hot-reload | ✅ PASS |
| AC5 | Test harness | ✅ PASS |

---

## Usage Examples

### 1. Evaluate Before Execution

```python
from app.policy import get_policy_engine, PolicyEvaluationRequest, ActionType

async def execute_skill(skill_id: str, agent_id: str, params: dict):
    engine = get_policy_engine()

    result = await engine.evaluate(PolicyEvaluationRequest(
        action_type=ActionType.EXECUTE,
        agent_id=agent_id,
        proposed_action=skill_id,
        context=params,
    ))

    if result.decision == PolicyDecision.BLOCK:
        raise PolicyBlockedError(result.decision_reason, result.violations)

    # Apply any modifications
    for mod in result.modifications:
        params[mod.parameter] = mod.modified_value

    # Proceed with execution
    return await run_skill(skill_id, params)
```

### 2. Check Risk Ceilings

```python
from app.policy import get_policy_engine

engine = get_policy_engine()
ceilings = await engine.get_risk_ceilings()

for ceiling in ceilings:
    utilization = ceiling.current_value / ceiling.max_value
    if utilization > 0.8:
        alert(f"Risk ceiling {ceiling.name} at {utilization:.0%}")
```

### 3. Simulate Before Commit

```python
# Dry run to preview what would happen
result = await engine.evaluate(request, dry_run=True)

if result.decision == PolicyDecision.BLOCK:
    # Show user what would be blocked
    return {
        "would_block": True,
        "violations": [v.description for v in result.violations]
    }
```

---

## M19.1 Gap Fixes (Critical Enhancements)

The following critical gaps were identified and addressed:

### GAP 1: Policy Versioning & Provenance

**Problem**: No version IDs, signed policies, history of changes, or rollback support.

**Solution**:
- Added `policy_versions` table for snapshots
- Added `policy_provenance` table for audit trail
- Semantic versioning (1.0.0 format)
- SHA256 policy hash for tamper detection
- Rollback support with provenance tracking

**API Endpoints**:
- `GET /versions` - List version history
- `GET /versions/current` - Get active version
- `POST /versions` - Create version snapshot
- `POST /versions/rollback` - Rollback to previous version
- `GET /versions/{id}/provenance` - Get change history

### GAP 2: Policy Dependency Graph & Conflict Resolution

**Problem**: Policies can conflict, but no way to track dependencies or resolve conflicts.

**Solution**:
- Added `policy_dependencies` table
- Added `policy_conflicts` table
- Dependency types: requires, conflicts_with, overrides, modifies
- Resolution strategies: source_wins, target_wins, merge, escalate

**Default Dependencies**:
- `ethical.no_manipulation` conflicts_with `business.personalization` (source_wins)
- `risk.cascade_depth` modifies `routing.parallelization`
- `safety.block_system_commands` overrides `business.automation`
- `compliance.gdpr` conflicts_with `business.data_sharing`

**API Endpoints**:
- `GET /dependencies` - Get dependency graph
- `GET /conflicts` - List conflicts
- `POST /conflicts/{id}/resolve` - Resolve a conflict

### GAP 3: Temporal Policies (Sliding Windows)

**Problem**: Policies only checked instantaneous state, not cumulative effects over time.

**Solution**:
- Added `temporal_policies` table
- Added `temporal_metric_windows` for window tracking
- Added `temporal_metric_events` for event logging
- Types: sliding_window, cumulative_daily, cumulative_weekly, rate_decay, burst_limit

**Default Temporal Policies**:
| Policy | Metric | Max | Window | Action |
|--------|--------|-----|--------|--------|
| retry_total_per_24h | retries | 300 | 24h | block |
| adaptations_per_agent_per_day | adaptations | 10 | 24h | throttle |
| escalations_per_hour | escalations | 20 | 1h | throttle |
| cost_burst_5min | cost | $10 | 5m | block |
| external_calls_per_minute | external_calls | 60 | 1m | throttle |

**API Endpoints**:
- `GET /temporal-policies` - List temporal policies
- `POST /temporal-policies` - Create temporal policy
- `GET /temporal-policies/{id}/utilization` - Get current utilization

### GAP 4: Policy Context Object

**Problem**: No comprehensive context passed through the decision cycle.

**Solution**:
- Added `PolicyContext` model with:
  - Agent identity (id, type, capabilities)
  - Tenant context (id, tier)
  - Risk state (current metrics, utilization)
  - Historical context (violation count, last violation)
  - Action chain context (depth, chain IDs, origin trigger)
  - Cost tracking (1h, 24h cumulative)
  - Temporal metrics (current window values)
  - Policy versioning (governing version, hash)

**API Endpoint**:
- `POST /evaluate/context-aware` - Evaluate with full context

### GAP 5: Enhanced Violation Classifications

**Problem**: Only minor/major/severe classification, not enough granularity.

**Solution**:
- Added `ViolationSeverity` enum:
  - ETHICAL_CRITICAL, COMPLIANCE_CRITICAL, OPERATIONAL_CRITICAL
  - ETHICAL_HIGH, COMPLIANCE_HIGH, OPERATIONAL_HIGH
  - RECOVERABLE_MEDIUM, RECOVERABLE_LOW, AUDIT_ONLY

- Added `RecoverabilityType` enum:
  - NON_RECOVERABLE - Immediate freeze required
  - RECOVERABLE_MANUAL - Needs human intervention
  - RECOVERABLE_AUTO - System can auto-recover
  - AUDIT_ONLY - Log only

**Classification Logic**:
- Ethical violations (severity >= 0.9) → ETHICAL_CRITICAL, NON_RECOVERABLE
- Compliance breaches (severity >= 0.9) → COMPLIANCE_CRITICAL, NON_RECOVERABLE
- High severity operational → RECOVERABLE_MANUAL
- Medium severity → RECOVERABLE_AUTO

---

## Files Added in M19.1

| File | Description |
|------|-------------|
| `backend/alembic/versions/033_m19_1_policy_gaps.py` | Gap fix migration |

## Files Modified in M19.1

| File | Changes |
|------|---------|
| `backend/app/policy/models.py` | Added GAP 1-5 models |
| `backend/app/policy/engine.py` | Added GAP 1-4 methods |
| `backend/app/policy/__init__.py` | Export new models |
| `backend/app/api/policy_layer.py` | Added GAP 1-4 endpoints |

---

## M19.1 Migration

New database tables (in `policy` schema):
- `policy_versions` - Version snapshots
- `policy_provenance` - Change audit trail
- `policy_dependencies` - Dependency relationships
- `policy_conflicts` - Detected conflicts
- `temporal_policies` - Sliding window policies
- `temporal_metric_windows` - Window aggregates
- `temporal_metric_events` - Event log

New columns added to existing tables:
- `violations`: severity_class, recoverability, action_chain_depth, is_temporal_violation, temporal_window_seconds, temporal_metric_value, recommended_action
- `evaluations`: policy_version, policy_hash, temporal_policies_checked, dependencies_checked, conflicts_detected

---

## M19.2 Critical Fixes (Pre-M20 Requirements)

The following critical issues were identified and fixed before M20:

### ISSUE 1: DAG Enforcement on Policy Dependencies

**Problem**: No cycle detection on policy dependencies. Cycles cause:
- Infinite recursion in override resolution
- Dependency evaluation oscillation
- Rule folding failures in policy compiler
- MODIFY rules looping indefinitely

**Solution**:
- Added `validate_dependency_dag()` method with DFS cycle detection
- Added `add_dependency_with_dag_check()` that blocks cyclic additions
- Added `get_topological_evaluation_order()` for policy ordering
- API endpoints: `/dependencies/dag/validate`, `/dependencies/add`, `/dependencies/evaluation-order`

**Algorithm**: Three-color DFS marking (WHITE/GRAY/BLACK) with cycle extraction.

### ISSUE 2: Temporal Metric Retention & Compaction

**Problem**: `temporal_metric_events` table will grow unbounded, causing:
- Storage explosion
- Query slowdown
- No historical aggregation

**Solution**:
- Added `prune_temporal_metrics()` method with:
  1. Delete events older than retention period (default: 7 days)
  2. Downsample older events to hourly aggregates (default: 24h+)
  3. Cap maximum events per policy (default: 10,000)
- Added `get_temporal_storage_stats()` for monitoring
- API endpoints: `/temporal-metrics/prune`, `/temporal-metrics/storage-stats`
- Added unique constraint on `window_key` for upsert operations

**Recommendation**: Run pruning daily via cron job.

### ISSUE 3: Version Activation with Pre-Activation Integrity Checks

**Problem**: No cohesion checks when switching policy versions. Without checks:
- Missing dependency references
- Unresolved critical conflicts
- Cycles in dependency graph
- Invalid temporal configurations
- Broken escalation paths

**Solution**:
- Added `activate_policy_version()` with 6 pre-activation checks:
  1. **Dependency closure** - all referenced policies exist
  2. **Conflict scan** - no unresolved critical conflicts (severity >= 0.7)
  3. **DAG validation** - no cycles in dependency graph
  4. **Temporal integrity** - valid window configurations
  5. **Severity compatibility** - escalation paths exist for strict enforcement
  6. **Simulation** - dry-run against test cases

- API endpoints: `/versions/activate`, `/versions/{version_id}/check`
- Supports `dry_run=True` for validation without activation

---

## API Endpoints Added in M19.2

### DAG Enforcement (ISSUE 1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dependencies/dag/validate` | Validate DAG structure |
| POST | `/dependencies/add` | Add dependency with cycle check |
| GET | `/dependencies/evaluation-order` | Get topological order |

### Temporal Metrics (ISSUE 2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/temporal-metrics/prune` | Prune & compact events |
| GET | `/temporal-metrics/storage-stats` | Get storage statistics |

### Version Activation (ISSUE 3)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/versions/activate` | Activate with integrity checks |
| POST | `/versions/{id}/check` | Dry-run integrity check |

---

## Files Modified in M19.2

| File | Changes |
|------|---------|
| `backend/app/policy/engine.py` | Added ISSUE 1-3 methods |
| `backend/app/api/policy_layer.py` | Added ISSUE 1-3 endpoints |
| `backend/alembic/versions/033_m19_1_policy_gaps.py` | Added unique constraint on window_key |

---

## Next Steps

1. **M20**: Policy Compiler that uses dependency graph
2. **Integration**: Wire all agent execution paths through Policy Engine
3. **Dashboard**: Add policy metrics to Grafana dashboard
4. **Audit**: Enable policy evaluation audit trail in production
5. **Cron Setup**: Schedule daily temporal metric pruning

---

## Related PINs

- PIN-076: M18 CARE-L + SBA Evolution
- PIN-075: M17 CARE Routing Engine
- PIN-033: M8-M14 Machine-Native Realignment
