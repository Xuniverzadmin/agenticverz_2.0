# PIN-087: Business Builder Worker API Hosting

**Serial:** PIN-087
**Created:** 2025-12-16
**Status:** Active
**Category:** Workers / API / Hosting
**Depends On:** PIN-086 (Business Builder Worker v0.2)

---

## Executive Summary

This PIN documents the API hosting layer for Business Builder Worker v0.2, making the worker accessible via hosted endpoints at `https://api.agenticverz.com`. This completes the transition from a local-only worker to a fully hostable, client-accessible service.

---

## What Was Built

### 1. API Router (`backend/app/api/workers.py`)

New API endpoints for the Business Builder Worker:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/workers/business-builder/run` | POST | Execute the worker |
| `/api/v1/workers/business-builder/replay` | POST | Replay execution (M4 Golden Replay) |
| `/api/v1/workers/business-builder/runs/{run_id}` | GET | Get run details |
| `/api/v1/workers/business-builder/runs` | GET | List recent runs |
| `/api/v1/workers/business-builder/validate-brand` | POST | Validate brand schema |
| `/api/v1/workers/business-builder/health` | GET | Worker health + moat status |
| `/api/v1/workers/business-builder/schema/brand` | GET | JSON schema for brand |
| `/api/v1/workers/business-builder/schema/run` | GET | JSON schema for run request |

### 2. CLI API Client Mode

The CLI now supports remote execution via hosted API:

```bash
# Local execution (existing)
python -m app.workers.business_builder.cli build-business "AI tool for podcasters"

# Remote execution via API (new)
python -m app.workers.business_builder.cli build-business "AI tool for podcasters" \
    --api https://api.agenticverz.com \
    --api-key AGZ_live_xxx

# Environment variables supported
export AGENTICVERZ_API_URL=https://api.agenticverz.com
export AGENTICVERZ_API_KEY=AGZ_live_xxx
python -m app.workers.business_builder.cli build-business "E-commerce platform"

# Async mode with polling
python -m app.workers.business_builder.cli build-business "SaaS idea" --async

# List runs
python -m app.workers.business_builder.cli list-runs --api ... --api-key ...

# Inspect run
python -m app.workers.business_builder.cli inspect <run_id> --failures --api ...
```

### 3. Request/Response Schemas

**WorkerRunRequest:**
```json
{
  "task": "AI tool for podcasters",
  "brand": {
    "company_name": "PodcastAI",
    "mission": "To revolutionize podcast production",
    "value_proposition": "AI-powered podcast editing in minutes",
    "tone": {"primary": "professional", "avoid": ["casual"]},
    "forbidden_claims": [
      {"pattern": "world's best", "reason": "Unverifiable", "severity": "error"}
    ]
  },
  "budget": 5000,
  "strict_mode": false,
  "depth": "auto",
  "async_mode": false
}
```

**WorkerRunResponse:**
```json
{
  "run_id": "uuid",
  "success": true,
  "status": "completed",
  "artifacts": {
    "market_report": {...},
    "landing_copy": {...},
    "landing_html": "...",
    "landing_css": "..."
  },
  "replay_token": {"plan_id": "...", "seed": 12345},
  "cost_report": {"total_tokens": 1000, "under_budget": true},
  "policy_violations": [],
  "recovery_log": [],
  "drift_metrics": {"research": 0.05, "copy": 0.12},
  "execution_trace": [...],
  "total_tokens_used": 1000,
  "total_latency_ms": 4500.0
}
```

---

## Moats Integration

The API exposes all 12+ moats from the worker:

| Moat | Integration Point |
|------|-------------------|
| M4 Golden Replay | `/replay` endpoint + `replay_token` in response |
| M9 Failure Catalog | `recovery_log` in response |
| M10 Recovery Engine | Auto-recovery during execution |
| M15 SBA | Brand schema triggers strategy binding |
| M17 CARE Routing | `routing_decisions` in response |
| M18 Drift Detection | `drift_metrics` in response |
| M19 Policy Layer | `policy_violations` in response |
| M20 Policy Compiler | PLang rules from brand constraints |

The `/health` endpoint reports moat availability:

```json
{
  "status": "healthy",
  "version": "0.2",
  "moats": {
    "m17_care": "available",
    "m20_policy": "available",
    "m9_failure_catalog": "available",
    "m10_recovery": "available"
  }
}
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENTS                                 │
├─────────────┬───────────────┬───────────────┬──────────────────┤
│   Web UI    │     CLI       │     SDK       │   Direct API     │
│ (Dashboard) │ (--api mode)  │   (Python)    │   (curl/httpx)   │
└──────┬──────┴───────┬───────┴───────┬───────┴────────┬─────────┘
       │              │               │                │
       └──────────────┴───────────────┴────────────────┘
                              │
                    HTTPS / Bearer Token
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 api.agenticverz.com                              │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              /api/v1/workers/business-builder            │   │
│   │                                                          │   │
│   │   POST /run        → BusinessBuilderWorker.run()         │   │
│   │   POST /replay     → replay()                            │   │
│   │   GET  /runs/{id}  → _get_run()                          │   │
│   │   GET  /runs       → _list_runs()                        │   │
│   │   POST /validate   → _brand_request_to_schema()          │   │
│   │   GET  /health     → moat status check                   │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │              BusinessBuilderWorker                        │   │
│   │                                                          │   │
│   │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │   │
│   │   │ Research │→ │ Strategy │→ │   Copy   │→ │   UX   │  │   │
│   │   └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘  │   │
│   │        │             │             │            │       │   │
│   │   ┌────▼─────────────▼─────────────▼────────────▼────┐  │   │
│   │   │                 M0-M20 Moat Stack                 │  │   │
│   │   │  M17 CARE → M19/M20 Policy → M9/M10 Recovery     │  │   │
│   │   │  M15 SBA → M18 Drift → M4 Replay                 │  │   │
│   │   └──────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Storage:                                                       │
│   ├─ PostgreSQL (Neon)     → Persistent run storage             │
│   ├─ Redis (Upstash)       → Job queue, caching                 │
│   └─ Cloudflare R2         → Artifact bundles                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Authentication

All endpoints require authentication:

```bash
# Bearer token
curl -X POST https://api.agenticverz.com/api/v1/workers/business-builder/run \
  -H "Authorization: Bearer AGZ_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{"task": "AI tool for podcasters"}'

# X-API-Key header (alternative)
curl -X POST https://api.agenticverz.com/api/v1/workers/business-builder/run \
  -H "X-API-Key: AGZ_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{"task": "AI tool for podcasters"}'
```

---

## Async Execution

For long-running tasks, use async mode:

```bash
# Start async run
curl -X POST .../run \
  -d '{"task": "Complex idea", "async_mode": true}'

# Response
{"run_id": "abc123", "status": "queued", ...}

# Poll for completion
curl .../runs/abc123

# Response when complete
{"run_id": "abc123", "status": "completed", "success": true, ...}
```

---

## Tests

**33 tests passing:**

| Test Category | Tests | Status |
|--------------|-------|--------|
| BrandSchema | 7 | PASS |
| AgentDefinitions | 6 | PASS |
| ExecutionPlan | 6 | PASS |
| WorkerExecution | 6 | PASS |
| PolicyValidation | 2 | PASS |
| StageImplementations | 4 | PASS |
| Integration | 2 | PASS |

---

## Files Modified/Created

| File | Change |
|------|--------|
| `backend/app/api/workers.py` | **NEW** - API router |
| `backend/app/main.py` | Added workers router |
| `backend/app/workers/business_builder/cli.py` | Added API client mode |

---

## Deployment Checklist

1. **API Gateway**: Route `/api/v1/workers/*` to backend
2. **Authentication**: Ensure API key validation is enabled
3. **Rate Limiting**: Apply per-tenant limits (100 req/min default)
4. **CORS**: Allow frontend domains
5. **Monitoring**: Add Prometheus metrics for worker runs
6. **Alerting**: Alert on high failure rates

---

## Usage Examples

### Python SDK

```python
import httpx

client = httpx.Client(
    base_url="https://api.agenticverz.com",
    headers={"Authorization": "Bearer AGZ_live_xxx"}
)

# Run worker
response = client.post("/api/v1/workers/business-builder/run", json={
    "task": "AI tool for podcasters",
    "budget": 5000,
})
result = response.json()
print(f"Run ID: {result['run_id']}")
print(f"Success: {result['success']}")

# Download artifacts
if result['success']:
    print(result['artifacts']['landing_html'])
```

### CLI

```bash
# One-liner with environment variables
AGENTICVERZ_API_URL=https://api.agenticverz.com \
AGENTICVERZ_API_KEY=AGZ_live_xxx \
python -m app.workers.business_builder.cli build-business "My SaaS idea"
```

### curl

```bash
curl -X POST https://api.agenticverz.com/api/v1/workers/business-builder/run \
  -H "Authorization: Bearer AGZ_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "AI tool for podcasters",
    "brand": {
      "company_name": "PodAI",
      "mission": "Revolutionize podcast production with AI",
      "value_proposition": "Create professional podcasts in minutes"
    },
    "budget": 5000
  }' | jq .
```

---

## Next Steps

1. **Persistent Storage**: Move from in-memory to PostgreSQL
2. **Billing Integration**: Track token usage per tenant
3. **Artifact Storage**: Upload bundles to R2
4. **Dashboard UI**: Build frontend for worker management
5. **Webhook Notifications**: Notify on run completion

---

## Related PINs

- [PIN-086](PIN-086-business-builder-worker-v02.md) - Business Builder Worker v0.2
- [PIN-084](PIN-084-m20-policy-compiler-runtime.md) - M20 Policy Compiler
- [PIN-078](PIN-078-m19-policy-layer.md) - M19 Policy Layer
- [PIN-075](PIN-075-m17-care-routing-engine.md) - M17 CARE Routing

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-16 | Initial creation - API hosting layer complete |
