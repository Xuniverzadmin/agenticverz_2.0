# PIN-071: M15 BudgetLLM A2A Integration

**Date:** 2025-12-14
**Status:** COMPLETE
**Version:** 1.0.0
**Category:** Feature / Integration

---

## Executive Summary

M15 integrates BudgetLLM's cost control and safety governance into the M12 multi-agent (A2A) system. This enables:

- **Per-job budget envelopes** - Set total LLM budget for a job
- **Per-worker budget allocation** - Automatically distribute budget across workers
- **Per-item risk tracking** - Record risk scores, blocked items, parameter clamping
- **Real-time budget enforcement** - Stop workers before overspend
- **Governance metrics** - Dashboard-ready aggregations

**Key Insight:** Agents without budget limits are a liability. M15 ensures every LLM call in the A2A system is governed.

---

## Architecture

### Integration Points

```
                    ┌─────────────────────┐
                    │   agent_spawn()     │
                    │   + llm_budget_cents │
                    └─────────┬───────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │     JobService      │
                    │  creates job with   │
                    │  llm_budget_cents,  │
                    │  llm_config         │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Worker 1 │   │ Worker 2 │   │ Worker N │
        │ claim()  │   │ claim()  │   │ claim()  │
        │ + budget │   │ + budget │   │ + budget │
        └────┬─────┘   └────┬─────┘   └────┬─────┘
             │              │              │
             ▼              ▼              ▼
        ┌──────────────────────────────────────┐
        │         BudgetLLM Client             │
        │  - Budget check before call          │
        │  - Risk scoring on response          │
        │  - Parameter clamping                │
        │  - Blocked item tracking             │
        └──────────────────────────────────────┘
                              │
                              ▼
        ┌──────────────────────────────────────┐
        │         GovernanceService            │
        │  - Record to job_items               │
        │  - Update job/instance totals        │
        │  - Aggregate for dashboard           │
        └──────────────────────────────────────┘
```

### Data Flow

1. **Job Creation**: `agent_spawn()` accepts `llm_budget_cents` parameter
2. **Budget Distribution**: Job budget distributed across items (`llm_budget_per_item`)
3. **Worker Claim**: Worker claims item, receives budget allocation
4. **LLM Call**: `governed_llm_invoke()` enforces budget and risk
5. **Completion**: `complete_item()` records governance data
6. **Aggregation**: `GovernanceService` provides metrics for dashboard

---

## Database Schema (Migration 027)

### jobs table additions

| Column | Type | Description |
|--------|------|-------------|
| `llm_budget_cents` | INTEGER | Total LLM budget for job |
| `llm_budget_used` | INTEGER | Consumed budget |
| `llm_risk_violations` | INTEGER | Count of blocked outputs |
| `llm_config` | JSONB | Risk threshold, max_temp, etc. |

### job_items table additions

| Column | Type | Description |
|--------|------|-------------|
| `risk_score` | FLOAT | 0.0-1.0 risk score |
| `risk_factors` | JSONB | Detailed risk breakdown |
| `blocked` | BOOLEAN | Whether output was blocked |
| `blocked_reason` | TEXT | Why blocked |
| `params_clamped` | JSONB | Parameters that were auto-corrected |
| `llm_cost_cents` | FLOAT | Cost of this item's LLM call |
| `llm_tokens_used` | INTEGER | Tokens consumed |

### instances table additions

| Column | Type | Description |
|--------|------|-------------|
| `llm_budget_cents` | INTEGER | Worker's budget allocation |
| `llm_budget_used` | INTEGER | Worker's consumed budget |
| `llm_risk_violations` | INTEGER | Worker's violation count |
| `llm_config` | JSONB | Worker's governance config |

### SQL Functions

```sql
-- Check if worker has budget for estimated call
SELECT * FROM agents.check_worker_budget(
    'worker-123',  -- instance_id
    50             -- estimated_cost_cents
);
-- Returns: (can_proceed: bool, budget_remaining: int, reason: text)

-- Record LLM usage for a job item
SELECT agents.record_llm_usage(
    'item-uuid',   -- item_id
    23.5,          -- cost_cents
    1500,          -- tokens
    0.42,          -- risk_score
    '{}',          -- risk_factors
    false,         -- blocked
    null,          -- blocked_reason
    '{}'           -- params_clamped
);
```

### Updated Views

- `agents.job_progress` - Now includes LLM governance metrics
- `agents.active_workers` - Now includes per-worker LLM stats

---

## New Modules

### 1. LLM Invoke Governed Skill

**File:** `backend/app/agents/skills/llm_invoke_governed.py`

```python
from app.agents.skills import governed_llm_invoke

result = await governed_llm_invoke(
    messages=[{"role": "user", "content": "Analyze this data"}],
    model="gpt-4o-mini",
    temperature=0.7,
    job_id=job.id,
    item_id=item.id,
    worker_instance_id=worker_id,
)

if result.blocked:
    # Output was blocked for safety
    log.warning(f"Blocked: {result.blocked_reason}")
else:
    # Use the response
    content = result.content
    print(f"Risk: {result.risk_score}")
    print(f"Cost: {result.cost_cents} cents")
```

**Key Classes:**
- `LLMInvokeGovernedSkill` - Main skill class
- `GovernedLLMClient` - BudgetLLM wrapper
- `GovernanceConfig` - Configuration dataclass

### 2. Governance Service

**File:** `backend/app/agents/services/governance_service.py`

```python
from app.agents.services import get_governance_service

service = get_governance_service()

# Get job budget status
status = service.get_job_budget_status(job_id)
print(f"Used: {status.used_cents}/{status.budget_cents}")
print(f"Exceeded: {status.is_exceeded}")

# Get risk metrics
risk = service.get_job_risk_metrics(job_id)
print(f"Avg risk: {risk.avg_risk_score}")
print(f"Blocked: {risk.blocked_items}")

# Check worker budget before call
check = service.check_worker_budget(
    instance_id="worker-123",
    estimated_cost_cents=50,
)
if not check.can_proceed:
    raise BudgetExceededError(check.reason)

# Get dashboard summary
summary = service.get_governance_summary(
    tenant_id="default",
    time_range_hours=24,
)
```

**Key Methods:**
- `get_job_budget_status()` - Budget utilization for job
- `get_job_risk_metrics()` - Risk aggregations for job
- `check_worker_budget()` - Pre-call budget check
- `allocate_worker_budget()` - Distribute budget to worker
- `get_governance_summary()` - Dashboard-ready aggregations
- `get_high_risk_items()` - Items above risk threshold

### 3. Updated Agent Spawn

**File:** `backend/app/agents/skills/agent_spawn.py`

```python
from app.agents.skills import AgentSpawnSkill, AgentSpawnInput

result = AgentSpawnSkill().execute(
    AgentSpawnInput(
        orchestrator_agent="data-processor",
        worker_agent="item-analyzer",
        task="Analyze 100 items",
        items=[...],
        parallelism=10,
        # M15: LLM Governance
        llm_budget_cents=1000,        # $10 total budget
        llm_risk_threshold=0.6,       # Block above 0.6
        llm_max_temperature=0.8,      # Clamp temp
        llm_enforce_safety=True,
    ),
    tenant_id="default",
)

print(f"Job: {result.job_id}")
print(f"Budget: {result.llm_budget_cents} cents")
print(f"Per item: {result.llm_budget_per_item} cents")
```

**New Input Fields:**
- `llm_budget_cents` - Total LLM budget
- `llm_budget_per_item` - Per-item budget (auto-calculated if not set)
- `llm_risk_threshold` - Risk score threshold
- `llm_max_temperature` - Max temperature allowed
- `llm_enforce_safety` - Enable/disable safety enforcement

### 4. Updated Worker Service

**File:** `backend/app/agents/services/worker_service.py`

```python
from app.agents.services import get_worker_service

worker = get_worker_service()

# Claim item with governance context
item = worker.claim_item(job_id, worker_instance_id)
# item.llm_budget_cents - Budget for this item
# item.llm_config - Governance settings

# Complete with governance data
worker.complete_item(
    item_id=item.id,
    output={"result": "..."},
    # M15: Governance data
    llm_cost_cents=23.5,
    llm_tokens_used=1500,
    risk_score=0.42,
    risk_factors={"hedging": 0.3, "unsupported_claims": 0.1},
    blocked=False,
    params_clamped={"temperature": {"original": 1.0, "clamped_to": 0.8}},
)
```

---

## Usage Examples

### Example 1: Basic Job with Budget

```python
# Create job with $10 LLM budget
result = AgentSpawnSkill().execute(
    AgentSpawnInput(
        orchestrator_agent="scraper",
        worker_agent="page-analyzer",
        task="Analyze 50 pages",
        items=urls,
        llm_budget_cents=1000,  # $10
    )
)

# Budget auto-distributed: 1000 / 50 = 20 cents per item
```

### Example 2: Strict Safety Mode

```python
# Strict safety: low threshold, enforce blocking
result = AgentSpawnSkill().execute(
    AgentSpawnInput(
        orchestrator_agent="research",
        worker_agent="fact-checker",
        task="Verify claims",
        items=claims,
        llm_budget_cents=500,
        llm_risk_threshold=0.4,      # Strict threshold
        llm_max_temperature=0.3,     # Low temperature for facts
        llm_enforce_safety=True,
    )
)
```

### Example 3: Creative Mode (Relaxed)

```python
# Creative task: high threshold, allow variation
result = AgentSpawnSkill().execute(
    AgentSpawnInput(
        orchestrator_agent="content",
        worker_agent="writer",
        task="Generate blog posts",
        items=topics,
        llm_budget_cents=2000,
        llm_risk_threshold=0.8,      # Relaxed threshold
        llm_max_temperature=1.2,     # Allow creativity
        llm_enforce_safety=False,    # Don't block
    )
)
```

### Example 4: Worker Loop with Governance

```python
async def worker_loop(job_id: UUID, worker_id: str):
    worker_service = get_worker_service()
    governance_service = get_governance_service()

    while True:
        # Claim next item
        item = worker_service.claim_item(job_id, worker_id)
        if not item:
            break

        # Check budget before LLM call
        check = governance_service.check_worker_budget(
            worker_id,
            estimated_cost_cents=item.llm_budget_cents or 50,
        )
        if not check.can_proceed:
            worker_service.fail_item(
                item.id,
                f"Budget exceeded: {check.reason}",
                retry=False,
            )
            continue

        # Make governed LLM call
        result = await governed_llm_invoke(
            messages=[{"role": "user", "content": f"Process: {item.input}"}],
            model="gpt-4o-mini",
            job_id=job_id,
            item_id=item.id,
            worker_instance_id=worker_id,
        )

        # Complete with governance data
        worker_service.complete_item(
            item.id,
            output={"content": result.content},
            llm_cost_cents=result.cost_cents,
            llm_tokens_used=result.input_tokens + result.output_tokens,
            risk_score=result.risk_score,
            risk_factors=result.risk_factors,
            blocked=result.blocked,
            blocked_reason=result.blocked_reason,
            params_clamped=result.params_clamped,
        )
```

---

## Dashboard Integration

### Governance Summary API

```python
# GET /api/v1/agents/governance/summary
summary = governance_service.get_governance_summary(
    tenant_id="default",
    time_range_hours=24,
)

# Response:
{
    "time_range_hours": 24,
    "jobs": {
        "total": 42,
        "total_budget_cents": 50000,
        "total_used_cents": 32450,
        "total_violations": 8
    },
    "items": {
        "total": 4200,
        "blocked": 8,
        "avg_risk_score": 0.34,
        "total_cost_cents": 32450,
        "total_tokens": 1250000
    },
    "utilization_pct": 64.9
}
```

### High-Risk Items API

```python
# GET /api/v1/agents/governance/high-risk
items = governance_service.get_high_risk_items(
    job_id=job_id,          # Optional: filter by job
    risk_threshold=0.6,
    limit=50,
)

# Response: List of items above threshold for review
```

### Job Governance View

The `agents.job_progress` view now includes:

```sql
SELECT
    id,
    task,
    status,
    -- Original fields
    total_items,
    completed_items,
    progress_pct,
    -- LLM governance fields
    llm_budget_cents,
    llm_budget_used,
    llm_budget_remaining,
    llm_risk_violations,
    blocked_items,
    avg_risk_score
FROM agents.job_progress
WHERE id = :job_id;
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BUDGET_CENTS` | None | Default budget (None = unlimited) |
| `LLM_DAILY_LIMIT_CENTS` | None | Daily limit |
| `LLM_MAX_TEMPERATURE` | 1.0 | Max allowed temperature |
| `LLM_MAX_COMPLETION_TOKENS` | 4096 | Max tokens |
| `LLM_ENFORCE_SAFETY` | true | Enable safety enforcement |
| `LLM_RISK_THRESHOLD` | 0.6 | Default risk threshold |
| `LLM_CACHE_ENABLED` | true | Enable prompt caching |
| `LLM_CACHE_TTL` | 3600 | Cache TTL seconds |
| `REDIS_URL` | None | Redis for distributed cache |

---

## File Structure

```
backend/app/agents/
├── skills/
│   ├── __init__.py                    # Updated: export governed skill
│   ├── agent_spawn.py                 # Updated: llm_budget params
│   ├── agent_invoke.py                # Unchanged
│   ├── blackboard_ops.py              # Unchanged
│   └── llm_invoke_governed.py         # NEW: BudgetLLM integration
├── services/
│   ├── __init__.py                    # Unchanged
│   ├── job_service.py                 # Updated: llm_budget in JobConfig
│   ├── worker_service.py              # Updated: governance data flow
│   ├── registry_service.py            # Unchanged
│   ├── credit_service.py              # Unchanged
│   └── governance_service.py          # NEW: Governance orchestration
└── alembic/versions/
    └── 027_m15_llm_governance.py      # NEW: Schema migration
```

---

## Migration Notes

### Running the Migration

```bash
# Apply M15 migration
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic upgrade head

# Verify columns exist
psql $DATABASE_URL -c "
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'agents'
      AND table_name = 'jobs'
      AND column_name LIKE 'llm_%';
"
```

### Backwards Compatibility

- All new columns have defaults (NULL or 0)
- Existing jobs/items work without governance data
- Migration adds columns without breaking existing queries
- Downgrade available: `alembic downgrade 026_m12_credit_tables_fix`

---

## Testing

### Verify Migration

```bash
# Run migration
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic upgrade head

# Check schema
psql $DATABASE_URL -c "\d agents.jobs"
psql $DATABASE_URL -c "\d agents.job_items"
psql $DATABASE_URL -c "\d agents.instances"
```

### Test Governance Flow

```python
# Test: Create job with budget, verify distribution
# Test: Claim item, verify budget allocation
# Test: Complete item, verify governance recording
# Test: Exceed budget, verify blocking
# Test: High risk output, verify blocking
```

---

## Related PINs

- **PIN-069:** BudgetLLM Go-To-Market Plan (Phase 0)
- **PIN-070:** BudgetLLM Safety Governance Layer (v0.2.0)
- **PIN-033:** M8-M14 Machine-Native Realignment Roadmap
- **PIN-025:** M12 Multi-Agent System Design

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-14 | Claude | Initial M15 implementation |
| 2025-12-14 | Claude | Migration 027, governance service, governed skill, worker integration |
