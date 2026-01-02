# L2 API Contract

**Version:** 1.0.0
**Generated:** 2026-01-02
**Status:** FROZEN
**Total Routes:** 336

---

## Overview

This document defines the **frontend-facing API contracts** for AOS.
These are the APIs that L1 (Product Experience) may consume.

### What This Document Is
- A **product-facing contract summary**
- The **truth** about what each endpoint guarantees
- A guide for **frontend developers**

### What This Document Is NOT
- OpenAPI/Swagger (see `/docs` for that)
- Implementation documentation
- Internal API reference

---

## Route Categories

| Category | Routes | Frontend Role |
|----------|-------:|---------------|
| **core** | 45 | Essential operations (auth, execution) |
| **monitoring** | 39 | Status, dashboards, observability |
| **governance** | 120 | Agents, policies, recovery |
| **operations** | 36 | Founder/ops actions |
| **supporting** | 30 | Traces, memory, embedding |
| **internal** | 35 | Not for customer frontend |

---

## 1. CORE APIs (Essential)

These endpoints are required for basic application functionality.

### 1.1 Authentication

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `POST /api/v1/onboarding/login/{provider}` | OAuth login (Google, Azure) | Returns JWT tokens |
| `POST /api/v1/onboarding/refresh` | Refresh access token | Silent refresh supported |
| `GET /api/v1/onboarding/me` | Get current user profile | Returns tenant context |
| `POST /api/v1/onboarding/logout` | Logout and invalidate tokens | Clears session |
| `POST /api/v1/onboarding/signup/email` | Email signup | Requires verification |
| `POST /api/v1/onboarding/verify/email` | Verify email | Activates account |

**Auth Requirement:** Public for login/signup, protected for others

**What Frontend Should Know:**
- Tokens expire after 1 hour
- Refresh tokens expire after 7 days
- Use silent refresh before token expiry
- `me` endpoint returns tenant_id for data scoping

### 1.2 Worker Execution

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `POST /api/v1/workers/run` | Submit execution request | Returns run_id immediately |
| `GET /api/v1/workers/runs/{run_id}` | Get run status | Eventual consistency (< 1s) |
| `GET /api/v1/workers/stream/{run_id}` | SSE stream for real-time updates | Keep-alive every 15s |
| `DELETE /api/v1/workers/runs/{run_id}` | Cancel running execution | Best-effort cancellation |
| `GET /api/v1/workers/events/{run_id}` | Get run events | Paginated, ordered |

**Auth Requirement:** Required (tenant-scoped)

**What Frontend Should Know:**
- `run` returns 202 Accepted, not final result
- Poll `runs/{id}` or use SSE stream for completion
- Stream reconnection: use `Last-Event-ID` header
- Cancellation may not stop in-flight LLM calls

### 1.3 Tenant Management

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `GET /api/v1/tenants/tenant` | Get current tenant info | Current tenant only |
| `GET /api/v1/tenants/api-keys` | List API keys | Masked secrets |
| `POST /api/v1/tenants/api-keys` | Create new API key | Returns full key once |
| `DELETE /api/v1/tenants/api-keys/{key_id}` | Revoke API key | Immediate effect |
| `GET /api/v1/tenants/tenant/quota/*` | Get quota (runs, tokens) | Current usage |

**Auth Requirement:** Required (owner only for mutations)

---

## 2. MONITORING APIs

Endpoints for observability and status.

### 2.1 Incidents

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `GET /api/v1/guard/incidents` | List incidents | Paginated, filterable |
| `GET /api/v1/guard/incidents/{id}` | Get incident detail | Full context |
| `POST /api/v1/guard/incidents/{id}/acknowledge` | Acknowledge incident | Audit logged |
| `GET /api/v1/guard/incidents/{id}/timeline` | Get incident timeline | Ordered events |
| `GET /api/v1/guard/status` | Guard system status | Health summary |

**What Frontend Should Know:**
- Incidents are tenant-scoped
- Use `search` endpoint for complex queries
- Timeline includes all related events

### 2.2 Cost Intelligence

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `GET /api/v1/cost-intelligence/dashboard` | Cost dashboard data | Aggregated metrics |
| `GET /api/v1/cost-intelligence/summary` | Cost summary | Rolling window |
| `GET /api/v1/cost-intelligence/by-model` | Breakdown by LLM model | Per-model costs |
| `GET /api/v1/cost-intelligence/by-feature` | Breakdown by feature | Per-feature costs |
| `GET /api/v1/cost-intelligence/anomalies` | Cost anomalies | Detected spikes |

**What Frontend Should Know:**
- Cost data updates every minute
- Anomaly detection runs on 15-minute windows
- Currency is always USD

### 2.3 Status History

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `GET /api/v1/status-history/stats` | Historical status summary | Last 30 days |
| `GET /api/v1/status-history/entity/{type}/{id}` | Entity status history | Paginated |
| `POST /api/v1/status-history/export` | Export to PDF/CSV | Returns export_id |
| `GET /api/v1/status-history/download/{id}` | Download export | S3 presigned URL |

---

## 3. GOVERNANCE APIs

Endpoints for policy, agents, and recovery management.

### 3.1 Agents

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `GET /api/v1/agents/agents` | List agents | All registered agents |
| `GET /api/v1/agents/agents/{id}/strategy` | Get agent strategy | SBA cascade |
| `GET /api/v1/agents/agents/{id}/reputation` | Get agent reputation | Scoring metrics |
| `GET /api/v1/agents/{id}/evolution` | Get SBA evolution | Historical changes |
| `POST /api/v1/agents/spawn-check` | Pre-spawn eligibility | Validation only |

**What Frontend Should Know:**
- Agents are immutable once registered
- Reputation updates every execution
- Evolution tracks strategy drift

### 3.2 Policy Layer

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `GET /api/v1/policy-layer/templates` | List policy templates | System templates |
| `GET /api/v1/policy-layer/active` | Get active policies | Currently enforced |
| `POST /api/v1/policy-layer/simulate` | Simulate policy effect | Dry-run only |
| `GET /api/v1/policy-layer/conflicts` | Detect policy conflicts | Real-time |

### 3.3 Recovery (M10)

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `GET /api/v1/recovery/candidates` | List recovery candidates | Suggested actions |
| `GET /api/v1/recovery/candidates/{id}` | Get candidate detail | Full context |
| `POST /api/v1/recovery/approve` | Approve recovery action | Executes recovery |
| `GET /api/v1/recovery/scopes/{incident_id}` | Get scoped candidates | Incident-specific |

**What Frontend Should Know:**
- Candidates are auto-generated from failure patterns
- Approval is a mutation (requires confirmation)
- Scopes limit recovery blast radius

---

## 4. OPERATIONS APIs (Founder/Ops Only)

These endpoints require elevated permissions.

### 4.1 Founder Actions

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `POST /api/v1/founder-actions/freeze-tenant` | Emergency freeze | Immediate |
| `POST /api/v1/founder-actions/unfreeze-tenant` | Remove freeze | Audit logged |
| `POST /api/v1/founder-actions/freeze-api-key` | Freeze specific key | Key-level |
| `POST /api/v1/founder-actions/override-incident` | Override incident state | Manual resolution |
| `GET /api/v1/founder-actions/audit` | Audit trail | All actions |

### 4.2 Kill-Switch

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `POST /api/v1/v1-killswitch/killswitch/tenant` | Emergency tenant disable | Blocks all calls |
| `GET /api/v1/v1-killswitch/killswitch/status` | Kill-switch status | Current state |
| `POST /api/v1/v1-killswitch/replay/{call_id}` | Replay blocked call | After resolution |

---

## 5. SUPPORTING APIs

Additional functionality endpoints.

### 5.1 Traces

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `GET /api/v1/traces/{run_id}` | Get execution trace | Full detail |
| `GET /api/v1/traces/by-hash/{hash}` | Get by root hash | Deterministic lookup |
| `GET /api/v1/traces/compare/{id1}/{id2}` | Compare two traces | Diff output |
| `POST /api/v1/traces/{id}/mismatch` | Report mismatch | Creates investigation |

### 5.2 Memory Pins

| Endpoint | Purpose | Guarantees |
|----------|---------|------------|
| `GET /api/v1/memory-pins/pins` | List memory pins | Agent-scoped |
| `POST /api/v1/memory-pins/pins` | Create pin | Persisted |
| `GET /api/v1/memory-pins/pins/{key}` | Get pin by key | TTL-aware |
| `DELETE /api/v1/memory-pins/pins/{key}` | Delete pin | Soft delete |

---

## 6. Error Semantics

All endpoints follow consistent error handling.

### HTTP Status Codes

| Code | Meaning | Frontend Action |
|------|---------|-----------------|
| 200 | Success | Process response |
| 201 | Created | Process response |
| 202 | Accepted (async) | Poll for result |
| 400 | Bad request | Show validation error |
| 401 | Unauthorized | Redirect to login |
| 403 | Forbidden | Show permission error |
| 404 | Not found | Show not found |
| 409 | Conflict | Show conflict message |
| 429 | Rate limited | Retry with backoff |
| 500 | Server error | Show generic error |

### Error Response Format

```json
{
  "error": {
    "code": "ERR_BUDGET_EXCEEDED",
    "message": "Token budget exhausted",
    "details": {
      "budget_remaining": 0,
      "budget_used": 10000
    }
  }
}
```

---

## 7. What Frontend Should NOT Assume

### Do NOT Assume

| Assumption | Reality |
|------------|---------|
| Retries are automatic | Frontend must implement retry logic |
| Order is guaranteed | Only where explicitly documented |
| Sync = instant | Many operations are eventually consistent |
| Delete = gone | Soft deletes are common |
| Errors are recoverable | Some errors are permanent |

### Do Assume

| Assumption | Guarantee |
|------------|-----------|
| Auth is consistent | Same token works across all endpoints |
| Tenant isolation | Data is always scoped |
| Idempotency | POST with idempotency key is safe to retry |
| Timestamps are UTC | All timestamps are ISO 8601 UTC |

---

## 8. Versioning

- Current version: `v1`
- Version in path: `/api/v1/...`
- Breaking changes require `v2`
- Non-breaking additions allowed in `v1`

---

## 9. Rate Limits

| Tier | Requests/min | Concurrent |
|------|-------------:|-----------:|
| Free | 60 | 5 |
| Pro | 600 | 20 |
| Enterprise | 6000 | 100 |

Rate limit headers:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

---

## Version History

| Date | Version | Change |
|------|---------|--------|
| 2026-01-02 | 1.0.0 | Initial contract from extraction |
