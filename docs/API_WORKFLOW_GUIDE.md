# AOS API Workflow Guide

> Sequential workflows for using the NOVA AOS API

**Base URL:** `http://109.123.252.1:8000`
**OpenAPI Spec:** [openapi.yaml](./openapi.yaml)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Basic Agent Run Workflow](#basic-agent-run-workflow)
3. [Machine-Native Workflow (Recommended)](#machine-native-workflow)
4. [Policy & Approval Workflow](#policy--approval-workflow)
5. [Cost Simulation Workflow](#cost-simulation-workflow)
6. [Memory Pins Workflow](#memory-pins-workflow)

---

## Authentication

All protected endpoints require one of:

| Header | Use Case |
|--------|----------|
| `X-API-Key: <api_key>` | Standard API access |
| `X-Machine-Token: <token>` | Machine/service accounts (RBAC) |

```bash
# Example: Check health (no auth required)
curl http://109.123.252.1:8000/health

# Example: Protected endpoint
curl -H "X-API-Key: YOUR_API_KEY" http://109.123.252.1:8000/api/v1/runs
```

---

## Basic Agent Run Workflow

Simple workflow to execute an agent task.

```
┌─────────────────────────────────────────────────────────────┐
│  1. Create Run  →  2. Poll Status  →  3. Get Results        │
└─────────────────────────────────────────────────────────────┘
```

### Step 1: Create a Run

```bash
curl -X POST http://109.123.252.1:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "agent_id": "agent-001",
    "goal": "Fetch the current Bitcoin price and format it as JSON",
    "budget_cents": 100
  }'
```

**Response:**
```json
{
  "run_id": "run-abc123",
  "status": "queued",
  "created_at": "2025-12-05T10:00:00Z"
}
```

### Step 2: Poll Run Status

```bash
curl http://109.123.252.1:8000/api/v1/runs/run-abc123 \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response (running):**
```json
{
  "run_id": "run-abc123",
  "status": "running",
  "current_step": 2,
  "total_steps": 3
}
```

**Response (completed):**
```json
{
  "run_id": "run-abc123",
  "status": "completed",
  "result": { "price": 43521.50, "currency": "USD" },
  "cost_cents": 12,
  "duration_ms": 2340
}
```

### Step 3: Get Run Details

```bash
curl http://109.123.252.1:8000/api/v1/runs/run-abc123/details \
  -H "X-API-Key: YOUR_API_KEY"
```

---

## Machine-Native Workflow (Recommended)

The machine-native workflow allows agents to make informed decisions before execution.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  1. Get Capabilities  →  2. Simulate Plan  →  3. Execute  →  4. Query   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Step 1: Get Available Capabilities

Check what skills are available and their costs.

```bash
curl http://109.123.252.1:8000/api/v1/runtime/capabilities \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "agent_id": null,
  "skills": {
    "http_call": {
      "available": true,
      "cost_estimate_cents": 0,
      "rate_limit_remaining": 95
    },
    "llm_invoke": {
      "available": true,
      "cost_estimate_cents": 5,
      "rate_limit_remaining": 50
    }
  },
  "budget": {
    "total_cents": 1000,
    "remaining_cents": 988
  },
  "rate_limits": {},
  "permissions": ["read", "write", "execute"]
}
```

### Step 2: Get Skill Details

```bash
curl http://109.123.252.1:8000/api/v1/runtime/skills/http_call \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "skill_id": "http_call",
  "name": "HTTP Call",
  "version": "0.2.0",
  "description": "Make HTTP requests",
  "cost_model": { "base_cents": 0 },
  "failure_modes": [
    { "code": "TIMEOUT", "category": "TRANSIENT", "recovery_hint": "Retry with backoff" },
    { "code": "HTTP_4XX", "category": "PERMANENT", "recovery_hint": "Check request params" }
  ],
  "constraints": { "timeout_ms": 30000, "max_response_bytes": 10485760 }
}
```

### Step 3: Simulate Plan Before Execution

Test feasibility without spending budget.

```bash
curl -X POST http://109.123.252.1:8000/api/v1/runtime/simulate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "plan": [
      { "skill": "http_call", "params": { "url": "https://api.coinbase.com/v2/prices/BTC-USD/spot" } },
      { "skill": "llm_invoke", "params": { "prompt": "Format this price data" } }
    ],
    "budget_cents": 100
  }'
```

**Response:**
```json
{
  "feasible": true,
  "status": "ok",
  "estimated_cost_cents": 5,
  "estimated_duration_ms": 1500,
  "budget_remaining_cents": 95,
  "budget_sufficient": true,
  "permission_gaps": [],
  "risks": [
    { "step": 0, "risk": "External API may timeout", "probability": 0.1 }
  ],
  "step_estimates": [
    { "skill": "http_call", "cost_cents": 0, "latency_ms": 500 },
    { "skill": "llm_invoke", "cost_cents": 5, "latency_ms": 1000 }
  ],
  "alternatives": [],
  "warnings": []
}
```

### Step 4: Execute the Run

If simulation passes, execute the plan.

```bash
curl -X POST http://109.123.252.1:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "agent_id": "agent-001",
    "goal": "Fetch BTC price and format as JSON",
    "budget_cents": 100
  }'
```

### Step 5: Query Runtime State

Check execution history and budget.

```bash
curl -X POST http://109.123.252.1:8000/api/v1/runtime/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "query_type": "remaining_budget_cents",
    "params": {}
  }'
```

**Supported query types:**
- `remaining_budget_cents` - Budget status
- `what_did_i_try_already` - Execution history
- `allowed_skills` - Available skills
- `last_step_outcome` - Most recent result

---

## Policy & Approval Workflow

For operations requiring human approval.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. Eval Policy  →  2. Create Request  →  3. Wait/Approve  →  4. Execute   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 1: Evaluate Policy (Sandbox)

Check if action requires approval.

```bash
curl -X POST http://109.123.252.1:8000/api/v1/policy/eval \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "skill_name": "postgres_query",
    "action": "DELETE FROM users WHERE id = 123",
    "context": { "tenant_id": "tenant-001" }
  }'
```

**Response:**
```json
{
  "allowed": false,
  "requires_approval": true,
  "approval_level": 2,
  "reason": "Destructive database operation requires L2 approval"
}
```

### Step 2: Create Approval Request

```bash
curl -X POST http://109.123.252.1:8000/api/v1/policy/requests \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "skill_name": "postgres_query",
    "action": "DELETE FROM users WHERE id = 123",
    "tenant_id": "tenant-001",
    "requester": "agent-001",
    "justification": "User requested account deletion"
  }'
```

**Response:**
```json
{
  "request_id": "apr-xyz789",
  "status": "pending",
  "approval_level": 2,
  "expires_at": "2025-12-05T12:00:00Z"
}
```

### Step 3: Check Request Status

```bash
curl http://109.123.252.1:8000/api/v1/policy/requests/apr-xyz789 \
  -H "X-API-Key: YOUR_API_KEY"
```

### Step 4: Approve Request (Admin)

```bash
curl -X POST http://109.123.252.1:8000/api/v1/policy/requests/apr-xyz789/approve \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ADMIN_API_KEY" \
  -d '{
    "approver": "admin@example.com",
    "comment": "Verified user consent"
  }'
```

### Step 5: List Pending Requests

```bash
curl "http://109.123.252.1:8000/api/v1/policy/requests?status=pending" \
  -H "X-API-Key: YOUR_API_KEY"
```

---

## Cost Simulation Workflow

Compare V1 and V2 cost models.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. Check Status  →  2. Run Simulation  →  3. Get Divergence Report     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Step 1: Check Sandbox Status

```bash
curl http://109.123.252.1:8000/costsim/v2/status \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "sandbox_enabled": true,
  "circuit_breaker_open": false,
  "model_version": "v2.1.0",
  "drift_threshold": 0.2
}
```

### Step 2: Run V2 Simulation

```bash
curl -X POST http://109.123.252.1:8000/costsim/v2/simulate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "plan": [
      { "skill": "http_call", "params": {} },
      { "skill": "llm_invoke", "params": { "model": "claude-sonnet-4-20250514" } }
    ]
  }'
```

### Step 3: Get Divergence Report

```bash
curl "http://109.123.252.1:8000/costsim/divergence?days=7" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Response:**
```json
{
  "delta_p50": 0.02,
  "delta_p90": 0.08,
  "kl_divergence": 0.015,
  "outlier_count": 3,
  "fail_ratio": 0.01,
  "matching_rate": 0.95
}
```

---

## Memory Pins Workflow

Store and retrieve structured key-value data.

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. Create Pin  →  2. Get Pin  →  3. List Pins  →  4. Delete Pin    │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 1: Create/Update Memory Pin

```bash
curl -X POST http://109.123.252.1:8000/api/v1/memory/pins \
  -H "Content-Type: application/json" \
  -H "X-Machine-Token: YOUR_MACHINE_TOKEN" \
  -d '{
    "namespace": "agent-001",
    "key": "last_btc_price",
    "value": { "price": 43521.50, "timestamp": "2025-12-05T10:00:00Z" },
    "ttl_seconds": 3600
  }'
```

**Response:**
```json
{
  "id": "pin-abc123",
  "namespace": "agent-001",
  "key": "last_btc_price",
  "created_at": "2025-12-05T10:00:00Z",
  "expires_at": "2025-12-05T11:00:00Z"
}
```

### Step 2: Get Memory Pin

```bash
curl http://109.123.252.1:8000/api/v1/memory/pins/agent-001/last_btc_price \
  -H "X-Machine-Token: YOUR_MACHINE_TOKEN"
```

### Step 3: List Memory Pins

```bash
curl "http://109.123.252.1:8000/api/v1/memory/pins?namespace=agent-001" \
  -H "X-Machine-Token: YOUR_MACHINE_TOKEN"
```

### Step 4: Delete Memory Pin

```bash
curl -X DELETE http://109.123.252.1:8000/api/v1/memory/pins/agent-001/last_btc_price \
  -H "X-Machine-Token: YOUR_MACHINE_TOKEN"
```

---

## Status History & Audit

Query audit trail for compliance.

```bash
# Get status history for an entity
curl "http://109.123.252.1:8000/status_history/entity/run/run-abc123" \
  -H "X-API-Key: YOUR_API_KEY"

# Export to CSV
curl -X POST http://109.123.252.1:8000/status_history/export \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "format": "csv",
    "entity_type": "run",
    "start_time": "2025-12-01T00:00:00Z"
  }'
```

---

## Error Handling

All errors return structured responses:

```json
{
  "error": {
    "code": "ERR_BUDGET_EXCEEDED",
    "message": "Run budget exhausted",
    "category": "RESOURCE",
    "retryable": false,
    "details": { "budget_cents": 100, "spent_cents": 102 }
  }
}
```

**Error Categories:**
| Category | Action |
|----------|--------|
| `TRANSIENT` | Retry with backoff |
| `PERMANENT` | Don't retry, fix request |
| `RESOURCE` | Wait for quota reset |
| `PERMISSION` | Check credentials |
| `VALIDATION` | Fix input data |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| All endpoints | 100 req/min per IP |
| `/api/v1/runs` | 10 req/min per tenant |
| `/api/v1/runtime/simulate` | 30 req/min per tenant |

Rate limit headers in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701777600
```

---

## SDK Examples

### Python SDK

```python
from aos_sdk import AOSClient

client = AOSClient(
    base_url="http://109.123.252.1:8000",
    api_key="YOUR_API_KEY"
)

# Simulate before executing
sim = client.runtime.simulate([
    {"skill": "http_call", "params": {"url": "https://api.example.com"}},
    {"skill": "llm_invoke", "params": {"prompt": "Summarize"}}
])

if sim.feasible:
    run = client.runs.create(
        agent_id="agent-001",
        goal="Fetch and summarize data",
        budget_cents=100
    )
    result = client.runs.wait(run.run_id)
    print(result)
```

### cURL Cheat Sheet

```bash
# Health check
curl http://109.123.252.1:8000/health

# List skills
curl http://109.123.252.1:8000/api/v1/runtime/skills -H "X-API-Key: KEY"

# Simulate plan
curl -X POST http://109.123.252.1:8000/api/v1/runtime/simulate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: KEY" \
  -d '{"plan":[{"skill":"http_call","params":{}}],"budget_cents":100}'

# Create run
curl -X POST http://109.123.252.1:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -H "X-API-Key: KEY" \
  -d '{"agent_id":"agent-001","goal":"Do something","budget_cents":100}'
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-05 | Initial workflow guide created |
