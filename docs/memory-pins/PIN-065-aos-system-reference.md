# PIN-065: AOS System Reference (M12 + M12.1)

**Created:** 2025-12-13
**Status:** REFERENCE
**Category:** Architecture / System Reference
**Milestone:** M12.1
**Parent PINs:** PIN-062 (M12), PIN-063 (M12.1), PIN-005 (Machine-Native)
**Author:** Claude Code + Human Review

---

## Purpose

Complete end-to-end reference for the Agentic Operating System (AOS) as it exists after M12 + M12.1. Designed to enable UI Console development with full coverage of every AOS capability.

---

## 1. Core Concepts

### 1.1 Agent Instances

An **agent instance** is a running execution context with a unique identity.

```
┌─────────────────────────────────────────────────────────┐
│                    agents.instances                      │
├─────────────────────────────────────────────────────────┤
│ id: UUID                    # DB primary key            │
│ agent_id: TEXT              # Agent type (e.g. "scraper_worker") │
│ instance_id: TEXT           # Unique runtime ID         │
│ job_id: UUID (nullable)     # Associated job            │
│ status: TEXT                # starting|running|idle|stopped|failed │
│ capabilities: JSONB         # What this agent can do    │
│ heartbeat_at: TIMESTAMPTZ   # Last heartbeat            │
│ created_at: TIMESTAMPTZ     # When registered           │
│ completed_at: TIMESTAMPTZ   # When deregistered         │
└─────────────────────────────────────────────────────────┘
```

**Lifecycle:**
```
register() → status='starting'
    ↓
heartbeat() → status='running' or 'idle'
    ↓
[30s no heartbeat] → mark_instance_stale() → status='stale'
    ↓
deregister() → status='stopped', completed_at=now()
```

**Key Behaviors:**
- Instance ID format: `{agent_id}_{uuid_hex[:8]}` (e.g., `scraper_worker_a1b2c3d4`)
- Heartbeat interval: 10-30 seconds recommended
- Stale threshold: Configurable, default 60 seconds
- Stale instances have their claimed job_items reclaimed

---

### 1.2 Jobs and Job Items

A **job** is a batch of work items to be processed in parallel.

```
┌─────────────────────────────────────────────────────────┐
│                      agents.jobs                         │
├─────────────────────────────────────────────────────────┤
│ id: UUID                                                │
│ orchestrator_instance_id: TEXT  # Who created this job  │
│ task: TEXT                      # Human-readable name   │
│ config: JSONB                   # Full job config       │
│ status: TEXT                    # pending|running|completed|failed|cancelled │
│ total_items: INT                                        │
│ completed_items: INT                                    │
│ failed_items: INT                                       │
│ credits_reserved: DECIMAL(12,2)                         │
│ credits_spent: DECIMAL(12,2)                            │
│ credits_refunded: DECIMAL(12,2)                         │
│ tenant_id: TEXT                 # For multi-tenancy     │
│ created_at, started_at, completed_at: TIMESTAMPTZ       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    agents.job_items                      │
├─────────────────────────────────────────────────────────┤
│ id: UUID                                                │
│ job_id: UUID (FK → jobs)                                │
│ item_index: INT                 # Order in batch        │
│ input: JSONB                    # Work payload          │
│ output: JSONB                   # Result (after complete) │
│ worker_instance_id: TEXT        # Who claimed it        │
│ status: TEXT                    # pending|claimed|completed|failed|cancelled │
│ claimed_at, completed_at: TIMESTAMPTZ                   │
│ error_message: TEXT             # If failed             │
│ retry_count: INT                # Retry attempts        │
│ max_retries: INT                # Max allowed retries   │
└─────────────────────────────────────────────────────────┘
```

**Job Item Lifecycle:**
```
pending → claimed → completed
              ↓
           failed → (if retry_count < max_retries) → pending
              ↓
           failed (permanent)
```

**Concurrency Safety (FOR UPDATE SKIP LOCKED):**
```sql
WITH next_item AS (
    SELECT id FROM agents.job_items
    WHERE job_id = :job_id AND status = 'pending'
    ORDER BY item_index
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
UPDATE agents.job_items
SET status = 'claimed', worker_instance_id = :worker_id, claimed_at = now()
FROM next_item
WHERE agents.job_items.id = next_item.id
RETURNING *;
```

---

### 1.3 Worker Lifecycle

```
┌────────────────────────────────────────────────────────────────┐
│                      WORKER LIFECYCLE                           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. REGISTER                                                   │
│     POST /api/v1/agents/register                               │
│     → instance_id assigned                                     │
│     → status = 'starting'                                      │
│                                                                │
│  2. CLAIM LOOP                                                 │
│     while true:                                                │
│         POST /api/v1/jobs/{job_id}/claim                       │
│         if item:                                               │
│             process(item.input)                                │
│             POST /api/v1/jobs/{job_id}/items/{item_id}/complete│
│         else:                                                  │
│             break  # No more items                             │
│         POST /api/v1/agents/{instance_id}/heartbeat            │
│                                                                │
│  3. DEREGISTER                                                 │
│     DELETE /api/v1/agents/{instance_id}                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

### 1.4 Orchestrator Workflow

```
┌────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR WORKFLOW                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. REGISTER as orchestrator                                   │
│     POST /api/v1/agents/register                               │
│                                                                │
│  2. SIMULATE job (optional)                                    │
│     POST /api/v1/jobs/simulate                                 │
│     → Check feasibility before committing                      │
│                                                                │
│  3. CREATE JOB                                                 │
│     POST /api/v1/jobs                                          │
│     → job_id returned, credits reserved, items created         │
│                                                                │
│  4. SPAWN WORKERS                                              │
│     Workers register and start claiming                        │
│                                                                │
│  5. MONITOR PROGRESS                                           │
│     GET /api/v1/jobs/{job_id}                                  │
│                                                                │
│  6. AGGREGATE RESULTS (optional)                               │
│     GET /api/v1/blackboard/results:*                           │
│                                                                │
│  7. FINALIZE                                                   │
│     Job auto-completes or POST /api/v1/jobs/{job_id}/cancel    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

### 1.5 Credit Model

**Cost Table:**

| Skill | Cost (credits) |
|-------|----------------|
| agent_spawn | 5 |
| agent_invoke | 10 |
| blackboard_read | 1 |
| blackboard_write | 1 |
| blackboard_lock | 1 |
| job_item (processing) | 2 |

**Credit Flow:**
```
1. JOB CREATION
   credits_reserved = job_overhead + (item_count × item_cost)
   → INSERT INTO credit_ledger (operation='reserve')

2. ITEM COMPLETION
   → UPDATE jobs SET credits_spent += item_cost
   → INSERT INTO credit_ledger (operation='charge')

3. JOB CANCELLATION
   refund = (pending_items × item_cost)
   → INSERT INTO credit_ledger (operation='refund')
```

---

### 1.6 Cancellation & Refunds

```http
POST /api/v1/jobs/{job_id}/cancel

Response:
{
  "job_id": "...",
  "status": "cancelled",
  "completed_items": 50,
  "cancelled_items": 50,
  "credits_refunded": 100.0
}
```

**What Happens:**
1. Job status → 'cancelled'
2. All 'pending' items → 'cancelled'
3. Credits refunded for cancelled items
4. Entry in `agents.job_cancellations` table
5. Entry in `agents.credit_ledger` with operation='refund'

---

### 1.7 Pre-Execution Simulation

```http
POST /api/v1/jobs/simulate

Response:
{
  "feasible": true,
  "estimated_credits": 205.0,
  "credits_per_item": 2.0,
  "item_count": 100,
  "estimated_duration_seconds": 600,
  "budget_check": {"sufficient": true, "required": 205.0},
  "risks": [],
  "warnings": ["Consider increasing parallelism"],
  "cost_breakdown": {"job_overhead": 5.0, "item_processing": 200.0, "total": 205.0}
}
```

**Key Points:**
- Does NOT create job or reserve credits
- Checks credit availability
- Estimates duration based on parallelism
- Identifies risks and warnings

---

## 2. Skills Available

### 2.1 agent_spawn (5 credits)

**Purpose:** Create a parallel job with worker items

```python
# Input
AgentSpawnInput(
    orchestrator_instance_id: str,
    worker_agent: str,
    task: str,
    items: List[Any],
    parallelism: int = 10,
    timeout_per_item: int = 60,
    max_retries: int = 3
)

# Output
AgentSpawnOutput(
    success: bool,
    job_id: Optional[str],
    items_created: int,
    credits_reserved: float,
    error: Optional[str]
)
```

---

### 2.2 agent_invoke (10 credits)

**Purpose:** Request-response between agents with correlation ID

```python
# Input
AgentInvokeInput(
    caller_instance_id: str,
    target_instance_id: str,
    request_payload: Dict[str, Any],
    timeout_seconds: int = 30,
    job_id: Optional[str] = None
)

# Output
AgentInvokeOutput(
    success: bool,
    invoke_id: Optional[str],
    response_payload: Optional[Dict[str, Any]],
    error: Optional[str],
    timeout: bool = False,
    latency_ms: Optional[int]
)
```

**Flow:**
```
CALLER                          TARGET
  │  1. start_invoke (audit)      │
  │  2. create invocation row     │
  │  3. send message ─────────────►
  │     (invoke_request)          │ 4. process request
  │  5. LISTEN invoke_{id}        │ 5. respond_to_invoke()
  │  ◄───────────────────────────── 6. pg_notify
  │  7. read response             │
  │  8. complete_invoke (audit)   │
  │  9. charge credits            │
```

---

### 2.3 Blackboard Skills (1 credit each)

**blackboard_read:**
```python
BlackboardReadInput(job_id, key, pattern=False)
BlackboardReadOutput(success, value, keys_found)
```

**blackboard_write:**
```python
BlackboardWriteInput(job_id, key, value, ttl=None)
BlackboardWriteOutput(success)
```

**blackboard_lock:**
```python
BlackboardLockInput(job_id, key, holder, action="acquire", ttl=30)
BlackboardLockOutput(success, acquired, current_holder)
```

---

## 3. Messaging Infrastructure

### 3.1 P2P Messaging Table

```sql
CREATE TABLE agents.messages (
    id UUID PRIMARY KEY,
    from_instance_id TEXT NOT NULL,
    to_instance_id TEXT NOT NULL,
    job_id UUID,
    message_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending|delivered|read
    reply_to_id UUID,               -- For request/response correlation
    created_at TIMESTAMPTZ DEFAULT now(),
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ
);
```

### 3.2 LISTEN/NOTIFY Behavior

**On Message Send:**
```python
session.execute(
    text("SELECT pg_notify(:channel, :payload)"),
    {"channel": f"msg_{to_instance_id}", "payload": json.dumps({...})}
)
```

**On Invoke Response:**
```python
session.execute(
    text("SELECT pg_notify(:channel, :payload)"),
    {"channel": f"invoke_{invoke_id}", "payload": json.dumps({"status": "completed"})}
)
```

**Latency:** Sub-second with LISTEN/NOTIFY vs 0.5-1s polling

### 3.3 Invoke Audit Trail

```sql
CREATE TABLE agents.invoke_audit (
    id UUID PRIMARY KEY,
    invoke_id TEXT UNIQUE NOT NULL,
    caller_instance_id TEXT NOT NULL,
    target_instance_id TEXT NOT NULL,
    job_id UUID,
    request_payload JSONB NOT NULL,
    response_payload JSONB,
    status TEXT NOT NULL,  -- pending|completed|timeout|failed
    credits_charged DECIMAL(12,2),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    error_message TEXT
);
```

---

## 4. Blackboard Infrastructure

**Backend:** Redis

**Key Format:** `bb:{job_id}:{key}` or `bb:global:{key}`

| Operation | Redis Command | Use Case |
|-----------|---------------|----------|
| Read | `GET bb:job:{key}` | Fetch single value |
| Write | `SET bb:job:{key}` | Store result |
| Write+TTL | `SETEX bb:job:{key} ttl` | Temporary data |
| Increment | `INCRBY bb:job:{key} amt` | Aggregate counts |
| Pattern Scan | `SCAN MATCH bb:job:results:*` | Collect all worker results |
| Lock Acquire | `SET bb:job:lock:{key} holder NX EX ttl` | Exclusive access |
| Lock Release | `DEL bb:job:lock:{key}` (if holder matches) | Release lock |

---

## 5. Billing & Resource Contracts

### Credit Ledger Schema

```sql
CREATE TABLE agents.credit_ledger (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    job_id UUID,
    skill TEXT,
    operation TEXT,  -- reserve, charge, refund
    amount DECIMAL(12,2) NOT NULL,
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE agents.credit_balances (
    id UUID PRIMARY KEY,
    tenant_id TEXT UNIQUE NOT NULL,
    balance DECIMAL(12,2) DEFAULT 0,
    reserved DECIMAL(12,2) DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### Ledger Entry Examples

```sql
-- Reserve on job creation
('tenant_001', 'job_123', NULL, 'reserve', 205.00)

-- Charge on item completion
('tenant_001', 'job_123', 'job_item', 'charge', 2.00)

-- Refund on cancellation
('tenant_001', 'job_123', NULL, 'refund', 100.00)
```

---

## 6. Observability & Metrics

### M12 Metrics (m12_*)

| Metric | Type | Description |
|--------|------|-------------|
| `m12_jobs_created_total` | Counter | Jobs created |
| `m12_jobs_completed_total` | Counter | Jobs finished |
| `m12_items_claimed_total` | Counter | Items claimed |
| `m12_items_completed_total` | Counter | Items completed |
| `m12_items_failed_total` | Counter | Items failed |
| `m12_spawn_duration_seconds` | Histogram | Job creation latency |
| `m12_claim_duration_seconds` | Histogram | Item claim latency |
| `m12_complete_duration_seconds` | Histogram | Item completion latency |
| `m12_invoke_duration_seconds` | Histogram | agent_invoke round-trip |
| `m12_invoke_success_total` | Counter | Successful invokes |
| `m12_invoke_failure_total` | Counter | Failed invokes |
| `m12_invoke_timeout_total` | Counter | Timed out invokes |
| `m12_credits_reserved_total` | Counter | Credits reserved |
| `m12_credits_spent_total` | Counter | Credits spent |
| `m12_credits_refunded_total` | Counter | Credits refunded |
| `m12_blackboard_ops_total` | Counter | Blackboard operations |
| `m12_message_latency_seconds` | Histogram | P2P message delivery time |

### Audit Tables

| Table | Purpose |
|-------|---------|
| `agents.invoke_audit` | All agent_invoke calls |
| `agents.job_cancellations` | Job cancellation history |
| `agents.credit_ledger` | All credit transactions |

---

## 7. APIs Required for UI Console

### Agent Management

| Action | Method | Endpoint |
|--------|--------|----------|
| List all agents | GET | `/api/v1/agents` |
| Get agent details | GET | `/api/v1/agents/{instance_id}` |
| Filter by status | GET | `/api/v1/agents?status=running` |
| Filter by job | GET | `/api/v1/agents?job_id={job_id}` |
| Register agent | POST | `/api/v1/agents/register` |
| Send heartbeat | POST | `/api/v1/agents/{id}/heartbeat` |
| Deregister | DELETE | `/api/v1/agents/{id}` |

### Skill Discovery

| Action | Method | Endpoint |
|--------|--------|----------|
| List all skills | GET | `/api/v1/runtime/skills` |
| Get skill details | GET | `/api/v1/runtime/skills/{skill_id}` |
| Get capabilities | GET | `/api/v1/runtime/capabilities` |

### Job Operations

| Action | Method | Endpoint |
|--------|--------|----------|
| Simulate job | POST | `/api/v1/jobs/simulate` |
| Create job | POST | `/api/v1/jobs` |
| Get job status | GET | `/api/v1/jobs/{job_id}` |
| Cancel job | POST | `/api/v1/jobs/{job_id}/cancel` |
| Claim item | POST | `/api/v1/jobs/{job_id}/claim` |
| Complete item | POST | `/api/v1/jobs/{job_id}/items/{item_id}/complete` |
| Fail item | POST | `/api/v1/jobs/{job_id}/items/{item_id}/fail` |

### Blackboard Operations

| Action | Method | Endpoint |
|--------|--------|----------|
| Read key | GET | `/api/v1/blackboard/{key}` |
| Write key | PUT | `/api/v1/blackboard/{key}` |
| Increment | POST | `/api/v1/blackboard/{key}/increment` |
| Lock operations | POST | `/api/v1/blackboard/{key}/lock` |

### Messaging

| Action | Method | Endpoint |
|--------|--------|----------|
| Send message | POST | `/api/v1/agents/{to_id}/messages` |
| Get inbox | GET | `/api/v1/agents/{id}/messages` |
| Mark as read | POST | `/api/v1/agents/{id}/messages/{msg_id}/read` |

### Invocations

| Action | Method | Endpoint |
|--------|--------|----------|
| Respond to invoke | POST | `/api/v1/invocations/respond` |

---

## 8. End-to-End Example: Parallel URL Scraper

### Flow Diagram

```
USER
  │
  │ 1. POST /jobs/simulate
  │    → feasible: true, estimated_credits: 205
  │
  │ 2. POST /jobs
  │    → job_id: "job_abc123"
  │    → LEDGER: reserve 205 credits
  │    → METRIC: m12_jobs_created_total++
  ▼

ORCHESTRATOR
  │
  │ 3. Spawn 10 workers
  ▼

WORKER_001...WORKER_010 (each):
  │
  │ 4. POST /agents/register
  │
  │ 5. LOOP:
  │    a. POST /jobs/{job_id}/claim
  │       → METRIC: m12_claim_duration_seconds
  │
  │    b. Process URL (scrape)
  │
  │    c. PUT /blackboard/results:{worker_id}
  │       → METRIC: m12_blackboard_ops_total++
  │
  │    d. POST /jobs/{job_id}/items/{item_id}/complete
  │       → METRIC: m12_items_completed_total++
  │       → LEDGER: charge 2 credits
  │
  │    e. POST /agents/{id}/heartbeat
  │
  │ 6. DELETE /agents/{id}
  ▼

AGGREGATOR
  │
  │ 7. GET /blackboard?pattern=results:*
  │ 8. Combine results
  │ 9. PUT /blackboard/final_result
  ▼

JOB COMPLETION
  │
  │ 10. All 100 items completed
  │     → status = 'completed'
  │     → METRIC: m12_jobs_completed_total++
  ▼

USER
  │
  │ 11. GET /jobs/{job_id}
  │     → status: "completed", progress: 100%
  │
  │ 12. GET /blackboard/final_result
  │     → Combined scraped data
```

### Metrics Timeline

```
T+0.0s  m12_jobs_created_total         +1
T+0.0s  m12_credits_reserved_total     +205
T+0.5s  m12_items_claimed_total        +10
T+2.1s  m12_items_completed_total      +10
T+2.1s  m12_credits_spent_total        +20
...
T+60s   m12_jobs_completed_total       +1
```

### Ledger Entries

```sql
T+0:   (tenant, job, 'reserve', 205.00)
T+2.1: (tenant, job, 'charge', 2.00) × 10
...
T+60:  Total charged: 200.00
```

---

## 9. UI Console Requirements Summary

### Dashboard Views
1. **Agent Overview** - Live instances, status, heartbeat age
2. **Job Monitor** - Active/completed jobs, progress bars
3. **Credit Summary** - Balance, reserved, spent, refunded
4. **Metrics Dashboard** - Grafana-style graphs for m12_*

### Interactive Features
1. **Job Simulator** - Test configs before creating
2. **Job Creator** - Form to spawn parallel jobs
3. **Job Cancellation** - One-click cancel with refund preview
4. **Blackboard Explorer** - Browse/edit keys, pattern search
5. **Message Viewer** - Inbox per agent, message timeline
6. **Audit Timeline** - Full invoke history for any job

### Real-Time Updates
1. WebSocket for job progress
2. Live agent status (heartbeats)
3. Message notifications

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-062 | M12 Multi-Agent System (implementation) |
| PIN-063 | M12.1 Stabilization (fixes) |
| PIN-064 | M13 Boundary Checklist (next steps) |
| PIN-005 | Machine-Native Architecture (vision) |
| PIN-033 | M8-M14 Roadmap (plan) |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-13 | Initial creation - complete system reference |
