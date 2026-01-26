# Threshold Params Contract

**Status:** ACTIVE
**Effective:** 2026-01-18
**Domain:** Policies → Limits → Controls
**Reference:** Migration 106, Panel POL-LIM-CTR-O3

---

## Purpose

This contract defines the **customer-controlled threshold parameters** for LLM run governance. These params drive the evaluation logic that enables:

- **ACT-LLM-LIVE-O2:** "Surface live runs exceeding expected execution time"
- **ACT-LLM-COMP-O3:** "Expose completed runs that ended in failure"

---

## Architecture Overview

```
Policies
 └── Limits
      └── Controls (limit_category = THRESHOLD)
           └── params (JSONB)
                ↓
        LLMRunThresholdResolver   ← Resolves effective params
                ↓
        LLMRunEvaluator           ← Evaluates runs
                ↓
        ActivitySignalEmitter     ← Emits signals
                ↓
        Activity Panels           ← Display signals
```

---

## Data Model

### Schema (limits.params)

```json
{
  "max_execution_time_ms": number,  // 1000-300000 (1s-5min)
  "max_tokens": number,             // 256-200000
  "max_cost_usd": number,           // 0.01-100.00
  "failure_signal": boolean         // default: true
}
```

### Safe Defaults

| Parameter | Default | Min | Max |
|-----------|---------|-----|-----|
| max_execution_time_ms | 60000 | 1000 | 300000 |
| max_tokens | 8192 | 256 | 200000 |
| max_cost_usd | 1.00 | 0.01 | 100.00 |
| failure_signal | true | - | - |

---

## API Contract

### GET /api/v1/policies/limits/{limit_id}/params

Returns current params and effective params (with defaults applied).

**Response:**
```json
{
  "limit_id": "string",
  "tenant_id": "string",
  "params": {},
  "effective_params": {
    "max_execution_time_ms": 60000,
    "max_tokens": 8192,
    "max_cost_usd": 1.00,
    "failure_signal": true
  },
  "updated_at": "datetime"
}
```

### PUT /api/v1/policies/limits/{limit_id}/params

Set threshold parameters. Only THRESHOLD category limits accepted.

**Request:**
```json
{
  "max_execution_time_ms": 45000,
  "max_tokens": 6000,
  "max_cost_usd": 0.75,
  "failure_signal": true
}
```

**Validation Rules:**
- All values within bounds
- No unknown keys (extra: forbid)
- Only for THRESHOLD category limits

---

## Resolution Precedence

When multiple limits exist, params are resolved in precedence order:

1. **Agent-scoped** (scope=AGENT, scope_id=agent_id) - highest
2. **Project-scoped** (scope=PROJECT, scope_id=project_id)
3. **Tenant-scoped** (scope=TENANT)
4. **Global defaults** - lowest

Later (higher precedence) values override earlier ones.

---

## Signal Types

| Signal | Trigger | Severity |
|--------|---------|----------|
| EXECUTION_TIME_EXCEEDED | elapsed > max_execution_time_ms | 2 |
| TOKEN_LIMIT_EXCEEDED | tokens > max_tokens | 2 |
| COST_LIMIT_EXCEEDED | cost > max_cost_usd | 2 |
| RUN_FAILED | status == failed && failure_signal | 3 |

---

## Panel: Set Execution Controls (POL-LIM-CTR-O3)

### UX Rules

- Show **effective defaults** even when params empty
- Grey text: "Inherited default"
- Yellow badge: "Overrides default"
- Red badge: "Invalid / rejected"
- Save = atomic write (immediate effect on next evaluation)

### Input Fields

| Field | Type | Required | Default |
|-------|------|----------|---------|
| Max Execution Time (ms) | Number | No | 60000 |
| Max Tokens | Number | No | 8192 |
| Max Cost (USD) | Decimal | No | 1.00 |
| Signal on Failure | Toggle | No | ON |

---

## Related Files

| File | Purpose |
|------|---------|
| `backend/alembic/versions/106_threshold_params.py` | Migration |
| `backend/app/services/llm_threshold_service.py` | Service layer |
| `backend/app/api/policy_limits_crud.py` | API endpoints |
| `backend/app/models/policy_control_plane.py` | Limit model |
| `design/l2_1/intents/AURORA_L2_INTENT_POL-LIM-THR-O3.yaml` | Panel intent |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial creation | Governance |
