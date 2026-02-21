# HOC_CUS_Observability_Standard_2026-02-21

**Created:** 2026-02-21
**Task:** T6 — Observability Design
**Status:** DONE

---

## 1. Objective

Define the required observability standard for all canonical HOC lanes. Establish required fields, correlation model, and dashboard minimums.

---

## 2. Required Logging Standard

### 2.1 Logger Hierarchy

Every HOC module MUST use a domain-scoped logger:

```python
# L2 API
logger = logging.getLogger("nova.hoc.api.cus.{domain}")

# L4 Orchestrator
logger = logging.getLogger("nova.hoc.spine.{handler_name}")

# L5 Engine
logger = logging.getLogger("nova.hoc.cus.{domain}.engine")

# L6 Driver
logger = logging.getLogger("nova.hoc.cus.{domain}.driver")
```

### 2.2 Required Structured Log Fields

Every log event MUST include these fields via `extra={}`:

| Field | Type | Required At | Description |
|-------|------|-------------|-------------|
| `correlation_id` | string | ALL layers | Request-scoped UUID, propagated L2→L4→L5→L6 |
| `tenant_id` | string | L4+ | Tenant scope |
| `operation` | string | L4 | Operation name (e.g., `traces.list`) |
| `layer` | string | ALL | Layer identifier (L2, L4, L5, L6) |
| `domain` | string | L5+ | Domain name (e.g., `policies`, `incidents`) |
| `duration_ms` | float | L4, L6 | Execution time in milliseconds |
| `status` | string | L4 | `success` or `error` |

### 2.3 Correlation ID Propagation

```python
# L2 (request entry point):
import contextvars
_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")

# Middleware sets:
_correlation_id.set(request.headers.get("X-Correlation-ID", str(uuid4())))

# All layers read:
cid = _correlation_id.get()
logger.info("operation_completed", extra={"correlation_id": cid, ...})
```

---

## 3. Required Metrics Standard

### 3.1 Per-Domain Metrics (Mandatory)

Every HOC domain MUST expose:

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `hoc_{domain}_operations_total` | Counter | operation, status, tenant_id | Operation count |
| `hoc_{domain}_operation_duration_seconds` | Histogram | operation, tenant_id | Latency distribution |
| `hoc_{domain}_errors_total` | Counter | operation, error_type, tenant_id | Error classification |

### 3.2 L6 Driver Metrics (Mandatory)

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `hoc_{domain}_db_duration_seconds` | Histogram | operation, tenant_id | DB query latency |
| `hoc_{domain}_db_errors_total` | Counter | operation, error_type | DB error count |

### 3.3 Auth Metrics (Already Implemented)

Existing `AUTH_SUCCESS_COUNTER` and `AUTH_FAILURE_COUNTER` in `gateway_audit.py` are sufficient. Add:

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `hoc_auth_token_refresh_total` | Counter | status | Refresh token usage |
| `hoc_auth_session_revocation_total` | Counter | reason | Session revocation tracking |

---

## 4. Required Health Checks

### 4.1 System Health (Existing — Needs Hardening)

| Check | Current | Required |
|-------|---------|----------|
| Database connectivity | "unknown" | Must verify actual `SELECT 1` |
| Redis connectivity | "unknown" | Must verify actual `PING` |
| Skills registry | Implemented | Keep |

### 4.2 Per-Domain Health (New)

Each domain SHOULD expose a health check via L4 operation:

```python
# L4 handler: {domain}.health
def health_check() -> dict:
    return {
        "domain": "policies",
        "status": "healthy",  # healthy | degraded | unhealthy
        "last_operation_at": "2026-02-21T19:00:00Z",
        "error_rate_1m": 0.0,
    }
```

---

## 5. Required Dashboard Coverage

### 5.1 Mandatory Dashboards

| Dashboard | Panels | Priority |
|-----------|--------|----------|
| HOC Domain Overview | Operations/sec, error rate, p99 latency per domain | P0 |
| Auth Gateway | Auth success/failure rate, token refresh rate, session revocation rate | P0 |
| L6 Driver Performance | DB query latency per domain, error rate | P1 |
| Domain Deep-Dive (per domain) | Top operations, slowest queries, error breakdown | P2 |

### 5.2 Required Alert Rules

| Alert | Condition | Severity |
|-------|-----------|----------|
| `HOCHighErrorRate` | Domain error rate > 5% for 5 min | WARNING |
| `HOCCriticalErrorRate` | Domain error rate > 20% for 5 min | CRITICAL |
| `HOCSlowOperation` | P99 latency > 5s for any domain | WARNING |
| `HOCAuthFailureSpike` | Auth failure rate > 10% for 5 min | CRITICAL |
| `HOCHealthDegraded` | Any domain health != "healthy" for 5 min | WARNING |

---

## 6. Event Observability

### 6.1 Event Persistence (Required for Wave A)

Domain events MUST be persisted to `domain_events` table:

| Column | Type | Description |
|--------|------|-------------|
| event_id | UUID | Unique event identifier |
| event_type | string | Domain.subtype format |
| tenant_id | string | Owning tenant |
| payload | JSONB | Event data |
| emitted_at | timestamp | Emission time |
| sequence_no | bigint | Per-tenant monotonic |

### 6.2 Event Emission Coverage Target

| Domain | Current | Wave A Target |
|--------|---------|---------------|
| Activity | 0% | 50% of write operations |
| Incidents | 0% | 80% of write operations |
| Policies | 0% | 80% of write operations |
| Account | 0% | 100% of write operations |
| All others | 0% | 30% of write operations |

---

## 7. Trace Correlation Model

### 7.1 Request Lifecycle Trace

```
[correlation_id: abc-123]
  L2 → log: "request_received" (path, method, auth_plane)
  L4 → log: "operation_dispatched" (operation, tenant_id)
    L5 → log: "engine_invoked" (domain, method)
      L6 → log: "driver_query" (table, duration_ms)
      L6 → log: "driver_query_complete" (rows_returned, duration_ms)
    L5 → log: "engine_complete" (status, duration_ms)
  L4 → log: "operation_complete" (status, duration_ms)
  L2 → log: "response_sent" (status_code, duration_ms)
```

### 7.2 Headers

| Header | Direction | Purpose |
|--------|-----------|---------|
| `X-Correlation-ID` | Request → Response | Request correlation |
| `X-Request-ID` | Response | Server-generated request ID |
| `X-Duration-Ms` | Response | Total request processing time |
