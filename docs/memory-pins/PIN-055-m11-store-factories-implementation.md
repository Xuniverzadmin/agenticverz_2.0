# PIN-055: M11 Store Factories & LLM Adapter Implementation

**Date**: 2025-12-09
**Status**: COMPLETE
**Category**: Implementation / M11
**Author**: Claude Code Implementation

---

## Summary

Implemented pluggable factory functions for all storage backends and LLM adapters, enabling environment-based switching between managed services (Neon, Upstash, Anthropic, OpenAI) and testing stubs.

---

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `backend/app/stores/__init__.py` | Factory functions for budget, checkpoint, idempotency stores |
| `backend/app/stores/checkpoint_offload.py` | R2 offload for old checkpoints |
| `backend/app/skills/adapters/openai_adapter.py` | OpenAI GPT-4o/mini adapter |
| `backend/app/skills/adapters/metrics.py` | Token metering decorator and cost estimation |

### Modified Files

| File | Changes |
|------|---------|
| `backend/app/skills/adapters/__init__.py` | Added `get_llm_adapter()` factory |
| `.env.example` | Added M11 configuration section |

---

## Factory Functions Implemented

### 1. Budget Store Factory

**Location**: `app/stores/__init__.py`

```python
from app.stores import get_budget_store

store = get_budget_store()  # Auto-detects from REDIS_URL
```

**Environment Variables**:
- `BUDGET_STORE`: `redis` or `memory` (auto-detects if not set)
- `REDIS_URL`: Redis/Upstash connection string

**Behavior**:
- Returns `RedisBudgetStore` if `REDIS_URL` is set
- Falls back to `InMemoryBudgetStore` for testing

### 2. Checkpoint Store Factory

**Location**: `app/stores/__init__.py`

```python
from app.stores import get_checkpoint_store

store = get_checkpoint_store()  # Auto-detects from DATABASE_URL
```

**Environment Variables**:
- `CHECKPOINT_STORE`: `postgres` or `memory` (auto-detects if not set)
- `DATABASE_URL`: PostgreSQL/Neon connection string

**Behavior**:
- Returns `CheckpointStore` (Postgres) if `DATABASE_URL` is set
- Falls back to `InMemoryCheckpointStore` for testing

### 3. LLM Adapter Factory

**Location**: `app/skills/adapters/__init__.py`

```python
from app.skills.adapters import get_llm_adapter

adapter = get_llm_adapter()  # Returns configured adapter
response = await adapter.invoke(prompt, config)
```

**Environment Variables**:
- `LLM_ADAPTER`: `claude`, `openai`, or `stub` (default: claude)
- `ANTHROPIC_API_KEY`: Required for Claude adapter
- `OPENAI_API_KEY`: Required for OpenAI adapter
- `OPENAI_DEFAULT_MODEL`: Default model for OpenAI (default: gpt-4o-mini)

**Behavior**:
- Returns `ClaudeAdapter` if `ANTHROPIC_API_KEY` is set
- Returns `OpenAIAdapter` if `LLM_ADAPTER=openai` and key is set
- Falls back to `StubAdapter` if no credentials

### 4. R2 Offload

**Location**: `app/stores/checkpoint_offload.py`

```python
from app.stores.checkpoint_offload import offload_old_checkpoints

# Run as scheduled job
result = await offload_old_checkpoints(older_than_days=3)
```

**Environment Variables**:
- `R2_ENDPOINT`: Cloudflare R2 endpoint
- `R2_BUCKET`: R2 bucket name
- `R2_ACCESS_KEY_ID`: R2 access key
- `R2_SECRET_ACCESS_KEY`: R2 secret key
- `CHECKPOINT_RETENTION_DAYS`: Days to keep in DB (default: 7)
- `CHECKPOINT_OFFLOAD_OLDER_THAN_DAYS`: When to offload (default: 3)

---

## OpenAI Adapter

**Location**: `app/skills/adapters/openai_adapter.py`

Features:
- Implements `LLMAdapter` interface
- Native seeding support (better determinism than Claude)
- Cost model for GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo
- Error mapping to contract error codes

**Cost Comparison** (per 1M tokens):

| Model | Input | Output |
|-------|-------|--------|
| claude-sonnet-4 | $3.00 | $15.00 |
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |

**Savings**: Switching to GPT-4o-mini saves ~70-80% vs Claude Sonnet for planning.

---

## Token Metrics Decorator

**Location**: `app/skills/adapters/metrics.py`

```python
from app.skills.adapters.metrics import track_llm_usage, track_llm_response

# Decorator usage
@track_llm_usage
async def invoke(self, prompt, config):
    ...

# Manual tracking
track_llm_response(response, adapter_id="claude", model="claude-sonnet-4")
```

**Metrics Tracked**:
- `nova_llm_tokens_total{provider, model, token_type}` - Token counts
- `nova_llm_cost_cents_total{provider, model}` - Cost tracking
- `nova_llm_duration_seconds{provider, model}` - Latency histogram
- `nova_llm_invocations_total{provider, model, status}` - Call counts

---

## Vault Secret Layout (Recommended)

As per user preferences, secrets should be stored under `secret/data/user/`:

```bash
# LLM Providers
vault kv put secret/user/anthropic ANTHROPIC_API_KEY=sk-ant-...
vault kv put secret/user/openai OPENAI_API_KEY=sk-...

# Managed Databases
vault kv put secret/user/neon DATABASE_URL=postgresql://user:pw@ep-xxx.neon.tech/db
vault kv put secret/user/upstash REDIS_URL=rediss://:token@xxx.upstash.io:6379

# R2 Storage
vault kv put secret/user/r2 \
  R2_ENDPOINT=https://account.r2.cloudflarestorage.com \
  R2_BUCKET=my-bucket \
  R2_ACCESS_KEY_ID=xxx \
  R2_SECRET_ACCESS_KEY=xxx
```

**Injection Script**:
```bash
export ANTHROPIC_API_KEY=$(vault kv get -field=ANTHROPIC_API_KEY secret/user/anthropic)
export DATABASE_URL=$(vault kv get -field=DATABASE_URL secret/user/neon)
export REDIS_URL=$(vault kv get -field=REDIS_URL secret/user/upstash)
```

---

## Testing

### Verify Store Factories

```bash
cd /root/agenticverz2.0/backend

# Test budget store factory
PYTHONPATH=. python3 -c "
from app.stores import get_budget_store
store = get_budget_store()
print(f'Budget store: {type(store).__name__}')
"

# Test checkpoint store factory
PYTHONPATH=. python3 -c "
from app.stores import get_checkpoint_store
store = get_checkpoint_store()
print(f'Checkpoint store: {type(store).__name__}')
"

# Test LLM adapter factory
PYTHONPATH=. python3 -c "
from app.skills.adapters import get_llm_adapter
adapter = get_llm_adapter()
print(f'LLM adapter: {adapter.adapter_id}')
"
```

### Verify OpenAI Adapter

```bash
OPENAI_API_KEY=sk-... LLM_ADAPTER=openai PYTHONPATH=. python3 -c "
import asyncio
from app.skills.adapters import get_llm_adapter
from app.skills.llm_invoke_v2 import LLMConfig

async def test():
    adapter = get_llm_adapter()
    print(f'Adapter: {adapter.adapter_id}')
    config = LLMConfig(max_tokens=50)
    response = await adapter.invoke('Say hello', config)
    print(f'Response: {response}')

asyncio.run(test())
"
```

---

## Deployment Checklist

1. **Configure Vault secrets** under `secret/data/user/*`
2. **Set environment variables** in deployment:
   - `LLM_ADAPTER=claude` (or `openai` for cost savings)
   - `BUDGET_STORE=redis`
   - `CHECKPOINT_STORE=postgres`
3. **Schedule checkpoint offload** job (daily cron):
   ```bash
   PYTHONPATH=/app python3 -m app.stores.checkpoint_offload --older-than 3
   ```
4. **Monitor token metrics** in Grafana:
   - Dashboard: LLM Cost Tracking
   - Alert: `nova_llm_cost_cents_total` > threshold

---

## References

- PIN-053: Mock Inventory & Real-World Plugins
- PIN-054: Engineering Audit - Mock Wiring & FinOps
- `app/workflow/policies.py` - RedisBudgetStore implementation
- `app/workflow/checkpoint.py` - CheckpointStore implementation
