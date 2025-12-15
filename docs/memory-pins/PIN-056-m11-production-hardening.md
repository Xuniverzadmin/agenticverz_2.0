# PIN-056: M11 Production Hardening

**Date**: 2025-12-09
**Status**: COMPLETE
**Category**: Implementation / M11
**Author**: Claude Code Implementation

---

## Summary

Production hardening improvements for M11, including strict mode, safety limits, tenant billing, and health probes required for M12 Beta rollout.

---

## Changes Implemented

### 1. Strict Production Mode (ENV=prod)

**Files Modified:**
- `app/stores/__init__.py`
- `app/skills/adapters/__init__.py`

**Behavior:**
- When `ENV=prod` or `ENV=production`, silent fallbacks to memory stores or stub adapters are **blocked**
- Raises `StoreConfigurationError` or `AdapterConfigurationError` instead of silently degrading
- Explicit acknowledgment required (e.g., `BUDGET_STORE=memory`) to use in-memory in production

```python
# In production, this will raise StoreConfigurationError:
# ENV=prod, REDIS_URL not set → error instead of fallback

# To explicitly acknowledge in-memory mode:
ENV=prod
BUDGET_STORE=memory  # explicit acknowledgment
```

### 2. R2 Offload Safety

**File Modified:** `app/stores/checkpoint_offload.py`

**Safety Features:**
- **Upload → Verify → Delete** sequence (never delete before verify)
- **SHA256 integrity hash** stored in R2 metadata and verified before deletion
- **Exponential backoff with jitter** for retries
- **Retry limits** configurable via `CHECKPOINT_OFFLOAD_MAX_RETRIES`

```python
# Safe offload sequence:
# 1. Compress checkpoint with gzip
# 2. Compute SHA256 hash
# 3. Upload to R2 with hash in metadata
# 4. Verify upload by re-reading and comparing hash
# 5. Only delete from DB after verified upload
```

### 3. Tenant/Agent Labels for Metrics

**Files Modified:**
- `app/metrics.py` - Added `tenant_id` and `agent_id` labels to LLM metrics
- `app/skills/adapters/metrics.py` - Updated tracking functions

**New Metric Labels:**
```prometheus
nova_llm_tokens_total{provider, model, token_type, tenant_id, agent_id}
nova_llm_cost_cents_total{provider, model, tenant_id, agent_id}
nova_llm_duration_seconds{provider, model, tenant_id}
nova_llm_invocations_total{provider, model, status, tenant_id, agent_id}
nova_llm_tenant_rate_limit{tenant_id}
nova_llm_tenant_budget_remaining_cents{tenant_id}
```

**Usage:**
```python
# Pass tenant_id/agent_id via config
config = LLMConfig(max_tokens=1000, tenant_id="acme", agent_id="planner-1")
response = await adapter.invoke(prompt, config)
# Metrics automatically tracked with tenant/agent labels
```

### 4. OpenAI Adapter Safety Limits

**File Modified:** `app/skills/adapters/openai_adapter.py`

**Safety Limits:**
- **Rate limiting**: `OPENAI_REQUESTS_PER_MINUTE` (default: 60)
- **Max tokens**: `OPENAI_MAX_TOKENS_PER_REQUEST` (default: 16000)
- **Max cost**: `OPENAI_MAX_COST_CENTS_PER_REQUEST` (default: 50¢)
- **Model restrictions**: `OPENAI_ALLOWED_MODELS` (optional whitelist)

```bash
# Environment variables
OPENAI_REQUESTS_PER_MINUTE=60
OPENAI_MAX_TOKENS_PER_REQUEST=16000
OPENAI_MAX_COST_CENTS_PER_REQUEST=50
OPENAI_ALLOWED_MODELS=gpt-4o-mini,gpt-4o  # optional
```

### 5. Per-Tenant LLM Configuration

**New File:** `app/skills/adapters/tenant_config.py`

**Features:**
- Per-tenant model preferences
- Per-tenant rate limits and budgets
- Task-based model selection (planning → cheap model)
- Configuration from env vars or Vault

```python
from app.skills.adapters.tenant_config import get_model_for_tenant

# Get optimal model for tenant and task
model = await get_model_for_tenant(
    tenant_id="acme",
    task_type="planning"  # Uses cheap model
)

# Per-tenant env vars
TENANT_ACME_LLM_MODEL=gpt-4o-mini
TENANT_ACME_RATE_LIMIT=30
TENANT_ACME_BUDGET_CENTS=50000
```

### 6. DB + Redis Health Probes

**New File:** `app/stores/health.py`

**Endpoints:**
- `check_health()` - Overall system health
- `readiness_probe()` - Kubernetes readiness
- `liveness_probe()` - Kubernetes liveness
- Component-specific: `check_database_health()`, `check_redis_health()`, `check_r2_health()`

```python
from app.stores.health import check_health, readiness_probe

# Full health check
health = await check_health()
print(health.to_dict())
# {
#   "status": "healthy",
#   "components": {
#     "database": {"status": "healthy", "latency_ms": 5.2},
#     "redis": {"status": "healthy", "latency_ms": 2.1}
#   }
# }

# Kubernetes readiness
is_ready, details = await readiness_probe()
```

---

## Environment Variables Summary

```bash
# Strict Mode
ENV=prod  # Enables strict mode

# Store Configuration
BUDGET_STORE=redis|memory
CHECKPOINT_STORE=postgres|memory
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# R2 Offload
CHECKPOINT_OFFLOAD_MAX_RETRIES=3
CHECKPOINT_RETENTION_DAYS=7
CHECKPOINT_OFFLOAD_OLDER_THAN_DAYS=3

# OpenAI Safety Limits
OPENAI_REQUESTS_PER_MINUTE=60
OPENAI_MAX_TOKENS_PER_REQUEST=16000
OPENAI_MAX_COST_CENTS_PER_REQUEST=50
OPENAI_ALLOWED_MODELS=gpt-4o-mini,gpt-4o

# Per-Tenant Config
TENANT_LLM_CONFIG_SOURCE=env|vault|database
DEFAULT_LLM_MODEL=claude-sonnet-4-20250514
DEFAULT_TENANT_RATE_LIMIT=60
DEFAULT_TENANT_BUDGET_CENTS=100000

# Health Probes
HEALTH_CHECK_TIMEOUT_SECONDS=5
```

---

## Files Created/Modified

### New Files
| File | Purpose |
|------|---------|
| `app/skills/adapters/tenant_config.py` | Per-tenant LLM configuration |
| `app/stores/health.py` | DB/Redis health probes |

### Modified Files
| File | Changes |
|------|---------|
| `app/stores/__init__.py` | Strict mode, StoreConfigurationError |
| `app/stores/checkpoint_offload.py` | Safe upload→verify→delete, SHA256 hash, retries |
| `app/skills/adapters/__init__.py` | Strict mode, AdapterConfigurationError |
| `app/skills/adapters/metrics.py` | tenant_id/agent_id labels |
| `app/skills/adapters/openai_adapter.py` | Safety limits, rate limiter |
| `app/metrics.py` | New LLM metric labels |

---

## Testing

```bash
cd /root/agenticverz2.0/backend

# Test strict mode
ENV=prod PYTHONPATH=. python3 -c "
from app.stores import get_budget_store, StoreConfigurationError
try:
    store = get_budget_store()
except StoreConfigurationError as e:
    print(f'Strict mode working: {e}')
"

# Test health probes
PYTHONPATH=. python3 -c "
import asyncio
from app.stores.health import check_health
health = asyncio.run(check_health())
print(health.to_dict())
"

# Test tenant config
PYTHONPATH=. python3 -c "
import asyncio
from app.skills.adapters.tenant_config import get_model_for_tenant
model = asyncio.run(get_model_for_tenant('acme', task_type='planning'))
print(f'Model for planning: {model}')
"
```

---

## References

- PIN-055: M11 Store Factories & LLM Adapter Implementation
- PIN-054: Engineering Audit - Mock Wiring & FinOps
- M12 Beta Rollout Requirements
