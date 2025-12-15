# API to UI Mapping Table

**Version:** 1.0.0
**Created:** 2025-12-13
**Purpose:** Frontend developer reference for API integration

---

## Overview

This document maps every AOS Console screen to its required API endpoints, including:
- HTTP method and endpoint
- Request parameters
- Response shape
- Polling/SSE/WebSocket requirements
- Error conditions and handling

---

## Authentication

### Token Management

| Operation | Method | Endpoint | Request | Response |
|-----------|--------|----------|---------|----------|
| Login | POST | `/api/v1/auth/login` | `{ email, password, remember }` | `{ access_token, refresh_token, expires_in }` |
| Refresh | POST | `/api/v1/auth/refresh` | `{ refresh_token }` | `{ access_token, refresh_token, expires_in }` |
| Logout | POST | `/api/v1/auth/logout` | — | `{ success: true }` |
| SSO Redirect | GET | `/api/v1/auth/sso/redirect` | `?provider=enterprise` | Redirect |
| SSO Callback | GET | `/api/v1/auth/sso/callback` | `?code=...&state=...` | `{ access_token, refresh_token }` |

### Headers Required

```typescript
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json
```

---

## Page 1: Dashboard

**URL:** `/console/`

### API Calls on Mount

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| MetricsRow | `/api/v1/metrics/summary` | GET | `?range=24h` | `MetricsSummary` | 30s poll |
| ActiveJobsTable | `/api/v1/jobs` | GET | `?status=running&limit=5` | `PaginatedJobs` | 30s poll |
| SystemHealthPanel | `/health` | GET | — | `HealthStatus` | 30s poll |
| ActivityFeed | `/api/v1/activity` | GET | `?limit=10` | `ActivityEvent[]` | SSE |
| CreditUsageChart | `/api/v1/credits/usage` | GET | `?days=7` | `CreditUsageData` | 5min poll |
| WelcomeBanner | `/api/v1/users/me` | GET | — | `User` | Once |

### Response Types

```typescript
interface MetricsSummary {
  active_jobs: number;
  completed_today: number;
  failed_today: number;
  credits_balance: number;
  trends: {
    active_jobs_change: number;      // percentage
    completed_change: number;
    failed_change: number;
    credits_change: number;
  };
}

interface PaginatedJobs {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

interface Job {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  task: string;
  total_items: number;
  completed_items: number;
  failed_items: number;
  progress_percent: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    api: ServiceHealth;
    database: ServiceHealth;
    redis: ServiceHealth;
    workers: ServiceHealth;
  };
}

interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms: number;
  message?: string;
}

interface ActivityEvent {
  id: string;
  type: 'job.created' | 'job.completed' | 'job.failed' | 'agent.registered' | 'invoke.completed';
  message: string;
  timestamp: string;
  metadata: Record<string, any>;
}

interface CreditUsageData {
  days: Array<{
    date: string;
    credits_spent: number;
    credits_reserved: number;
    credits_refunded: number;
  }>;
  total_spent: number;
  total_reserved: number;
}
```

### Error Conditions

| Error Code | Condition | UI Handling |
|------------|-----------|-------------|
| 401 | Token expired | Redirect to /login |
| 403 | Insufficient permissions | Show permission error banner |
| 500 | Server error | Show retry button, fallback to cached data |
| Network | Connection failed | Show offline indicator, retry with backoff |

---

## Page 2: Agents Console

**URL:** `/console/agents`

### API Calls

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| AgentStats | `/api/v1/agents/stats` | GET | — | `AgentStats` | 30s poll |
| AgentsTable | `/api/v1/agents` | GET | `?status&type&search&page&limit` | `PaginatedAgents` | 30s poll |
| AgentDetailDrawer | `/api/v1/agents/{id}` | GET | — | `AgentDetail` | On open |
| RegisterAgentModal | `/api/v1/agents/register` | POST | `RegisterAgentRequest` | `Agent` | — |
| DeregisterAgent | `/api/v1/agents/{id}` | DELETE | — | `{ success: true }` | — |
| BulkDeregister | `/api/v1/agents/bulk/deregister` | POST | `{ agent_ids: string[] }` | `BulkResult` | — |

### Request/Response Types

```typescript
// Query Parameters
interface AgentFilters {
  status?: 'active' | 'idle' | 'stale';
  type?: 'orchestrator' | 'worker';
  search?: string;
  page?: number;
  limit?: number;
}

// Responses
interface AgentStats {
  total: number;
  active: number;
  idle: number;
  stale: number;
  by_type: {
    orchestrator: number;
    worker: number;
  };
}

interface PaginatedAgents {
  items: Agent[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

interface Agent {
  id: string;
  name: string;
  type: 'orchestrator' | 'worker';
  status: 'active' | 'idle' | 'stale';
  capabilities: string[];
  registered_at: string;
  last_heartbeat: string;
  heartbeat_age_seconds: number;
  current_jobs: string[];
  metadata: Record<string, any>;
}

interface AgentDetail extends Agent {
  jobs_completed: number;
  jobs_failed: number;
  messages_sent: number;
  messages_received: number;
  credits_consumed: number;
  uptime_seconds: number;
}

interface RegisterAgentRequest {
  agent_name: string;
  agent_type: 'orchestrator' | 'worker';
  capabilities: string[];
  metadata?: Record<string, any>;
}

interface BulkResult {
  success: number;
  failed: number;
  errors: Array<{ id: string; error: string }>;
}
```

### Error Conditions

| Error Code | Condition | UI Handling |
|------------|-----------|-------------|
| 404 | Agent not found | Remove from table, show toast |
| 409 | Agent already registered | Show conflict error in modal |
| 422 | Invalid agent name | Show validation error |

---

## Page 3: Job Simulator

**URL:** `/console/jobs/simulate`

### API Calls

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| AgentSelect (orch) | `/api/v1/agents` | GET | `?type=orchestrator&status=active` | `PaginatedAgents` | On focus |
| AgentSelect (work) | `/api/v1/agents` | GET | `?type=worker&status=active` | `PaginatedAgents` | On focus |
| SimulateButton | `/api/v1/jobs/simulate` | POST | `SimulateRequest` | `SimulationResult` | — |
| BudgetCheck | `/api/v1/credits/balance` | GET | — | `CreditBalance` | On simulate |

### Request/Response Types

```typescript
interface SimulateRequest {
  orchestrator_agent: string;
  worker_agent: string;
  task: string;
  items: Array<{ id: string; [key: string]: any }>;
  parallelism: number;
  max_retries?: number;
}

interface SimulationResult {
  feasible: boolean;
  estimated_credits: number;
  estimated_duration_seconds: number;

  credit_breakdown: {
    reserve_cost: number;
    item_cost: number;
    skill_cost: number;
    total: number;
  };

  budget_check: {
    sufficient: boolean;
    balance: number;
    required: number;
    shortfall: number;
  };

  time_estimate: {
    p50_seconds: number;
    p95_seconds: number;
    p99_seconds: number;
  };

  warnings: string[];
  risks: Array<{
    severity: 'low' | 'medium' | 'high';
    message: string;
  }>;

  resource_check: {
    agents_available: boolean;
    workers_available: number;
    workers_required: number;
  };
}

interface CreditBalance {
  balance: number;
  reserved: number;
  available: number;
  last_updated: string;
}
```

### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| orchestrator_agent | Required | "Select an orchestrator agent" |
| worker_agent | Required | "Select a worker agent" |
| task | Required, max 1000 chars | "Task description is required" |
| items | Required, min 1, max 10000 | "At least one item required" |
| items[].id | Required, unique | "Each item must have a unique id" |
| parallelism | 1-100 | "Parallelism must be between 1 and 100" |

### Error Conditions

| Error Code | Condition | UI Handling |
|------------|-----------|-------------|
| 400 | Invalid items JSON | Highlight JSON editor, show parse error |
| 402 | Insufficient credits | Show budget warning, disable "Run This Job" |
| 422 | Validation failed | Show field-level errors |
| 503 | Agents unavailable | Show warning, suggest waiting |

---

## Page 4: Job Runner

**URL:** `/console/jobs/run`

### API Calls - Create Tab

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| JobConfigForm | `/api/v1/jobs` | POST | `CreateJobRequest` | `Job` | — |

### API Calls - Active Jobs Tab

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| ActiveJobsList | `/api/v1/jobs` | GET | `?status=running,pending&limit=20` | `PaginatedJobs` | 10s poll |
| ActiveJobCard | `/api/v1/jobs/{id}` | GET | — | `JobDetail` | SSE stream |
| LiveFeed | — | SSE | — | `JobEvent` stream | Continuous |
| CancelButton | `/api/v1/jobs/{id}/cancel` | POST | — | `CancelResult` | — |

### API Calls - History Tab

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| JobHistoryTable | `/api/v1/jobs` | GET | `?status=completed,failed,cancelled&page&limit` | `PaginatedJobs` | On demand |
| ExportButton | `/api/v1/jobs/{id}/export` | GET | `?format=csv` | Binary download | — |

### Request/Response Types

```typescript
interface CreateJobRequest {
  orchestrator_agent: string;
  worker_agent: string;
  task: string;
  items: Array<{ id: string; [key: string]: any }>;
  parallelism: number;
  max_retries?: number;
  timeout_seconds?: number;
  metadata?: Record<string, any>;
}

interface JobDetail extends Job {
  orchestrator_agent: string;
  worker_agent: string;
  parallelism: number;
  credits_reserved: number;
  credits_spent: number;
  credits_refunded: number;

  item_counts: {
    pending: number;
    claimed: number;
    completed: number;
    failed: number;
  };

  items: JobItem[];  // Only first 100, use pagination for more

  timeline: Array<{
    event: string;
    timestamp: string;
    details?: Record<string, any>;
  }>;
}

interface JobItem {
  id: string;
  status: 'pending' | 'claimed' | 'completed' | 'failed';
  worker_id: string | null;
  result: any | null;
  error: string | null;
  duration_ms: number | null;
  retries: number;
  claimed_at: string | null;
  completed_at: string | null;
}

interface CancelResult {
  job_id: string;
  status: 'cancelled';
  completed_items: number;
  cancelled_items: number;
  credits_refunded: number;
  cancelled_at: string;
}
```

### SSE Stream - Job Events

**Endpoint:** `GET /api/v1/jobs/{id}/stream`

**Connection:**
```typescript
const eventSource = new EventSource(
  `https://agenticverz.com/api/v1/jobs/${jobId}/stream`,
  { headers: { Authorization: `Bearer ${token}` } }
);

eventSource.onmessage = (event) => {
  const jobEvent: JobEvent = JSON.parse(event.data);
  // Handle event
};
```

**Event Types:** See [Event Model Definitions](#event-models)

### Error Conditions

| Error Code | Condition | UI Handling |
|------------|-----------|-------------|
| 402 | Insufficient credits | Show balance warning, block creation |
| 404 | Job not found | Remove from list, show toast |
| 409 | Job already cancelled | Refresh job status |
| 423 | Job locked (being cancelled) | Disable cancel button, show status |

---

## Page 5: Blackboard Explorer

**URL:** `/console/blackboard`

### API Calls

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| KeyStats | `/api/v1/blackboard/stats` | GET | — | `BlackboardStats` | 30s poll |
| KeyValueTable | `/api/v1/blackboard` | GET | `?pattern&page&limit` | `PaginatedKeys` | 30s poll |
| KeyDetailPanel | `/api/v1/blackboard/{key}` | GET | — | `BlackboardEntry` | On select |
| AddKeyModal | `/api/v1/blackboard/{key}` | PUT | `SetKeyRequest` | `BlackboardEntry` | — |
| EditKeyModal | `/api/v1/blackboard/{key}` | PUT | `SetKeyRequest` | `BlackboardEntry` | — |
| IncrementButton | `/api/v1/blackboard/{key}/increment` | POST | `{ amount: number }` | `{ new_value: number }` | — |
| DeleteButton | `/api/v1/blackboard/{key}` | DELETE | — | `{ success: true }` | — |
| LockButton | `/api/v1/blackboard/{key}/lock` | POST | `LockRequest` | `LockResult` | — |
| UnlockButton | `/api/v1/blackboard/{key}/unlock` | POST | `{ lock_id: string }` | `{ success: true }` | — |

### Request/Response Types

```typescript
interface BlackboardStats {
  total_keys: number;
  locked_keys: number;
  expiring_soon: number;  // TTL < 1 hour
  by_pattern: Array<{
    pattern: string;
    count: number;
  }>;
}

interface PaginatedKeys {
  items: BlackboardEntry[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

interface BlackboardEntry {
  key: string;
  value: any;
  value_type: 'string' | 'integer' | 'json';
  ttl_seconds: number | null;      // null = no expiration
  expires_at: string | null;
  is_locked: boolean;
  lock_owner: string | null;
  lock_expires_at: string | null;
  created_at: string;
  updated_at: string;
}

interface SetKeyRequest {
  value: any;
  value_type?: 'string' | 'integer' | 'json';
  ttl_seconds?: number;
}

interface LockRequest {
  ttl_seconds: number;      // Lock duration
  wait_seconds?: number;    // How long to wait if already locked
}

interface LockResult {
  success: boolean;
  lock_id: string;
  expires_at: string;
  waited_ms?: number;
}
```

### Error Conditions

| Error Code | Condition | UI Handling |
|------------|-----------|-------------|
| 404 | Key not found | Remove from table, show toast |
| 409 | Key already locked | Show lock owner, offer wait option |
| 422 | Invalid value for type | Show validation error in modal |
| 423 | Lock acquisition failed | Show timeout error, offer retry |

---

## Page 6: Messaging Inspector

**URL:** `/console/messages`

### API Calls

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| LatencyStats | `/api/v1/messages/stats` | GET | `?range=1h` | `MessageStats` | 30s poll |
| MessageFlowGraph | `/api/v1/messages/flow` | GET | `?range=1h` | `MessageFlow` | 30s poll |
| MessagesTable | `/api/v1/messages` | GET | `?from&to&status&type&page&limit` | `PaginatedMessages` | SSE |
| MessageDetailDrawer | `/api/v1/messages/{id}` | GET | — | `MessageDetail` | On open |
| SendMessageModal | `/api/v1/agents/{id}/messages` | POST | `SendMessageRequest` | `Message` | — |

### Request/Response Types

```typescript
interface MessageStats {
  total_messages: number;
  by_status: {
    pending: number;
    delivered: number;
    read: number;
    failed: number;
  };
  latency: {
    p50_ms: number;
    p95_ms: number;
    p99_ms: number;
  };
  throughput: {
    messages_per_minute: number;
    peak_per_minute: number;
  };
}

interface MessageFlow {
  agents: Array<{
    id: string;
    name: string;
    type: 'orchestrator' | 'worker';
  }>;
  connections: Array<{
    from: string;
    to: string;
    message_count: number;
    avg_latency_ms: number;
  }>;
}

interface PaginatedMessages {
  items: Message[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

interface Message {
  id: string;
  from_agent: string;
  to_agent: string;
  type: 'invoke' | 'response' | 'notification' | 'broadcast';
  status: 'pending' | 'delivered' | 'read' | 'failed';
  sent_at: string;
  delivered_at: string | null;
  read_at: string | null;
  latency_ms: number | null;
  payload_size_bytes: number;
}

interface MessageDetail extends Message {
  payload: any;
  response: any | null;
  correlation_id: string | null;
  job_id: string | null;
  invoke_id: string | null;
  error: string | null;
  metadata: Record<string, any>;
}

interface SendMessageRequest {
  type: 'invoke' | 'notification';
  payload: any;
  timeout_seconds?: number;
}
```

### SSE Stream - Messages

**Endpoint:** `GET /api/v1/messages/stream`

**Query Params:** `?from={agent_id}&to={agent_id}&types=invoke,response`

### Error Conditions

| Error Code | Condition | UI Handling |
|------------|-----------|-------------|
| 404 | Agent not found | Show error in send modal |
| 408 | Message timeout | Show timeout indicator |
| 502 | Delivery failed | Show failed status, offer retry |

---

## Page 7: Credit & Audit Console

**URL:** `/console/credits`

### API Calls - Overview

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| BalanceCard | `/api/v1/credits/balance` | GET | — | `CreditBalance` | 30s poll |
| MonthlySpendCard | `/api/v1/credits/usage` | GET | `?range=month` | `MonthlyUsage` | 5min poll |

### API Calls - Ledger Tab

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| LedgerTable | `/api/v1/credits/ledger` | GET | `?type&job_id&page&limit&from&to` | `PaginatedLedger` | On demand |
| ExportLedger | `/api/v1/credits/ledger/export` | GET | `?format=csv&from&to` | Binary download | — |

### API Calls - Invoke Audit Tab

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| InvokeAuditTable | `/api/v1/invocations/audit` | GET | `?caller&target&status&page&limit` | `PaginatedAudit` | On demand |
| InvokeDetailModal | `/api/v1/invocations/{id}` | GET | — | `InvokeDetail` | On open |

### API Calls - Analytics Tab

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| UsageChart | `/api/v1/credits/usage` | GET | `?range=30d&granularity=day` | `UsageTimeSeries` | On mount |
| SkillBreakdownPie | `/api/v1/credits/breakdown` | GET | `?by=skill&range=30d` | `Breakdown` | On mount |
| JobTypeBreakdownPie | `/api/v1/credits/breakdown` | GET | `?by=job_type&range=30d` | `Breakdown` | On mount |

### Request/Response Types

```typescript
interface CreditBalance {
  balance: number;
  reserved: number;
  available: number;
  currency: 'credits';
  last_updated: string;
}

interface MonthlyUsage {
  month: string;           // "2025-12"
  total_spent: number;
  total_reserved: number;
  total_refunded: number;
  net_spend: number;
  budget: number | null;
  budget_percent: number | null;
}

interface PaginatedLedger {
  items: LedgerEntry[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

interface LedgerEntry {
  id: string;
  type: 'reserve' | 'charge' | 'refund' | 'topup' | 'adjustment';
  amount: number;           // Positive for credit, negative for debit
  balance_after: number;
  job_id: string | null;
  skill: string | null;
  description: string;
  created_at: string;
  metadata: Record<string, any>;
}

interface PaginatedAudit {
  items: InvokeAudit[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

interface InvokeAudit {
  invoke_id: string;
  caller_agent: string;
  target_agent: string;
  action: string;
  status: 'success' | 'failed' | 'timeout';
  duration_ms: number;
  credits_charged: number;
  job_id: string | null;
  started_at: string;
  completed_at: string | null;
}

interface InvokeDetail extends InvokeAudit {
  request_payload: any;
  response_payload: any | null;
  error: string | null;
  error_code: string | null;
  retry_count: number;
  correlation_id: string;
  timeline: Array<{
    event: string;
    timestamp: string;
    details?: any;
  }>;
}

interface UsageTimeSeries {
  range: string;
  granularity: 'hour' | 'day' | 'week';
  data: Array<{
    timestamp: string;
    credits_spent: number;
    credits_reserved: number;
    credits_refunded: number;
    job_count: number;
    invoke_count: number;
  }>;
}

interface Breakdown {
  by: 'skill' | 'job_type' | 'agent';
  total: number;
  items: Array<{
    name: string;
    credits: number;
    percent: number;
    count: number;
  }>;
}
```

### Error Conditions

| Error Code | Condition | UI Handling |
|------------|-----------|-------------|
| 400 | Invalid date range | Show date picker validation error |
| 403 | Not authorized for billing | Show permission error |

---

## Page 8: Metrics Overview

**URL:** `/console/metrics`

### API Calls

| Component | Endpoint | Method | Params | Response Shape | Refresh |
|-----------|----------|--------|--------|----------------|---------|
| HealthStatusRow | `/health` | GET | — | `HealthStatus` | 30s poll |
| JobsMetricsChart | `/api/v1/metrics/jobs` | GET | `?range&granularity` | `MetricTimeSeries` | 60s poll |
| ThroughputGauge | `/api/v1/metrics/throughput` | GET | `?range=1h` | `ThroughputData` | 30s poll |
| CreditFlowSummary | `/api/v1/credits/flow` | GET | `?range=24h` | `CreditFlow` | 5min poll |
| InvokeLatencyHistogram | `/api/v1/metrics/invoke-latency` | GET | `?range` | `LatencyHistogram` | 60s poll |
| MessageLatencyChart | `/api/v1/metrics/message-latency` | GET | `?range` | `LatencyTimeSeries` | 60s poll |

### Prometheus Proxy

For custom dashboards and advanced queries:

**Endpoint:** `GET /api/v1/metrics/query`

**Params:**
```typescript
{
  query: string;           // PromQL query
  start?: string;          // ISO timestamp
  end?: string;            // ISO timestamp
  step?: string;           // Duration (e.g., "1m", "5m")
}
```

**Example:**
```
GET /api/v1/metrics/query?query=m12_jobs_created_total&start=2025-12-13T00:00:00Z&end=2025-12-13T23:59:59Z&step=1h
```

### Response Types

```typescript
interface MetricTimeSeries {
  metric: string;
  range: string;
  granularity: string;
  data: Array<{
    timestamp: string;
    value: number;
  }>;
}

interface ThroughputData {
  current: number;           // items/hour
  average: number;
  peak: number;
  trend: 'up' | 'down' | 'stable';
  trend_percent: number;
}

interface CreditFlow {
  range: string;
  reserved: number;
  spent: number;
  refunded: number;
  net: number;
  by_hour: Array<{
    hour: string;
    reserved: number;
    spent: number;
    refunded: number;
  }>;
}

interface LatencyHistogram {
  metric: string;
  range: string;
  buckets: Array<{
    le: number;            // Less than or equal (ms)
    count: number;
  }>;
  percentiles: {
    p50: number;
    p75: number;
    p90: number;
    p95: number;
    p99: number;
  };
}
```

### Available Prometheus Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `m12_jobs_created_total` | Counter | Total jobs created |
| `m12_jobs_completed_total` | Counter | Total jobs completed |
| `m12_jobs_failed_total` | Counter | Total jobs failed |
| `m12_jobs_cancelled_total` | Counter | Total jobs cancelled |
| `m12_items_claimed_total` | Counter | Total items claimed |
| `m12_items_completed_total` | Counter | Total items completed |
| `m12_items_failed_total` | Counter | Total items failed |
| `m12_credits_reserved_total` | Counter | Total credits reserved |
| `m12_credits_spent_total` | Counter | Total credits spent |
| `m12_credits_refunded_total` | Counter | Total credits refunded |
| `m12_invoke_duration_seconds` | Histogram | Invoke latency distribution |
| `m12_message_latency_seconds` | Histogram | Message delivery latency |
| `m12_blackboard_op_duration_seconds` | Histogram | Blackboard operation latency |
| `m12_agents_active` | Gauge | Current active agents |
| `m12_jobs_running` | Gauge | Current running jobs |

---

## Global Components

### CreditBadge (Header)

| Endpoint | Method | Response | Refresh |
|----------|--------|----------|---------|
| `/api/v1/credits/balance` | GET | `{ balance, reserved, available }` | 60s poll |

### NotificationBell (Header)

| Endpoint | Method | Response | Refresh |
|----------|--------|----------|---------|
| `/api/v1/notifications` | GET | `{ unread_count, items[] }` | SSE stream |
| `/api/v1/notifications/{id}/read` | POST | `{ success }` | On click |

### TenantSelector (Sidebar)

| Endpoint | Method | Response | Refresh |
|----------|--------|----------|---------|
| `/api/v1/tenants` | GET | `{ tenants[] }` | On mount |
| `/api/v1/tenants/switch` | POST | `{ tenant_id }` | On change |

---

## WebSocket Connections

### Job Stream WebSocket

**URL:** `wss://agenticverz.com/ws/jobs/{job_id}`

**Auth:** Query param `?token={access_token}`

**Subscribe:**
```json
{ "type": "subscribe", "job_id": "job_xxx" }
```

**Events:** See Event Model Definitions

### Messages WebSocket

**URL:** `wss://agenticverz.com/ws/messages`

**Auth:** Query param `?token={access_token}`

**Subscribe:**
```json
{ "type": "subscribe", "agent_ids": ["agent_1", "agent_2"] }
```

---

## Rate Limiting

| Endpoint Pattern | Rate Limit | Scope |
|------------------|------------|-------|
| `POST /api/v1/jobs` | 10/minute | Per tenant |
| `POST /api/v1/jobs/simulate` | 30/minute | Per tenant |
| `GET /api/v1/*` | 100/minute | Per tenant |
| `POST /api/v1/agents/register` | 20/minute | Per tenant |
| WebSocket connections | 10 concurrent | Per tenant |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702468800
```

---

## Document Revision

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-13 | Initial API to UI mapping |
