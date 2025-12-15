# Event Model Definitions

**Version:** 1.0.0
**Created:** 2025-12-13
**Purpose:** SSE/WebSocket event types for real-time UI updates

---

## Overview

This document defines all event types used for real-time streaming in the AOS Console. Events are delivered via:
- **SSE (Server-Sent Events)** - For one-way server-to-client updates
- **WebSocket** - For bidirectional communication

---

## Base Event Structure

All events follow this base structure:

```typescript
interface BaseEvent {
  id: string;                    // Unique event ID (UUID)
  type: string;                  // Event type (e.g., "job.started")
  timestamp: string;             // ISO 8601 timestamp
  tenant_id: string;             // Tenant context
  correlation_id?: string;       // For tracing related events
  sequence?: number;             // Monotonic sequence number
}
```

---

## Job Events

### Event Types

| Event Type | Trigger | Description |
|------------|---------|-------------|
| `job.created` | Job created | New job added to queue |
| `job.started` | Job begins | First item claimed |
| `job.progress` | Item status changes | Progress update |
| `job.completed` | All items done | Job finished successfully |
| `job.failed` | Job failed | Job terminated with errors |
| `job.cancelled` | Cancel requested | Job manually cancelled |

### Event Definitions

```typescript
// job.created
interface JobCreatedEvent extends BaseEvent {
  type: 'job.created';
  payload: {
    job_id: string;
    orchestrator_agent: string;
    worker_agent: string;
    task: string;
    total_items: number;
    parallelism: number;
    credits_reserved: number;
    created_at: string;
    created_by: string;          // User/agent who created
  };
}

// job.started
interface JobStartedEvent extends BaseEvent {
  type: 'job.started';
  payload: {
    job_id: string;
    started_at: string;
    first_worker: string;        // First worker to claim
  };
}

// job.progress
interface JobProgressEvent extends BaseEvent {
  type: 'job.progress';
  payload: {
    job_id: string;
    total_items: number;
    pending_items: number;
    claimed_items: number;
    completed_items: number;
    failed_items: number;
    progress_percent: number;
    estimated_remaining_seconds: number | null;
    credits_spent: number;
  };
}

// job.completed
interface JobCompletedEvent extends BaseEvent {
  type: 'job.completed';
  payload: {
    job_id: string;
    total_items: number;
    completed_items: number;
    failed_items: number;
    duration_seconds: number;
    credits_reserved: number;
    credits_spent: number;
    credits_refunded: number;
    completed_at: string;
    success_rate: number;        // Percentage
  };
}

// job.failed
interface JobFailedEvent extends BaseEvent {
  type: 'job.failed';
  payload: {
    job_id: string;
    reason: string;
    error_code: string;
    completed_items: number;
    failed_items: number;
    credits_spent: number;
    credits_refunded: number;
    failed_at: string;
  };
}

// job.cancelled
interface JobCancelledEvent extends BaseEvent {
  type: 'job.cancelled';
  payload: {
    job_id: string;
    cancelled_by: string;        // User who cancelled
    completed_items: number;
    cancelled_items: number;
    credits_refunded: number;
    cancelled_at: string;
    reason?: string;
  };
}
```

---

## Item Events

### Event Types

| Event Type | Trigger | Description |
|------------|---------|-------------|
| `item.pending` | Item added | Item waiting for worker |
| `item.claimed` | Worker claims | Worker picked up item |
| `item.completed` | Processing done | Item finished successfully |
| `item.failed` | Processing error | Item failed with error |
| `item.retry` | Retry scheduled | Item will be retried |
| `item.abandoned` | Worker died | Orphaned item released |

### Event Definitions

```typescript
// item.pending
interface ItemPendingEvent extends BaseEvent {
  type: 'item.pending';
  payload: {
    job_id: string;
    item_id: string;
    item_data: Record<string, any>;
    position: number;            // Position in queue
    created_at: string;
  };
}

// item.claimed
interface ItemClaimedEvent extends BaseEvent {
  type: 'item.claimed';
  payload: {
    job_id: string;
    item_id: string;
    worker_id: string;
    worker_name: string;
    claimed_at: string;
    wait_time_ms: number;        // Time in pending state
  };
}

// item.completed
interface ItemCompletedEvent extends BaseEvent {
  type: 'item.completed';
  payload: {
    job_id: string;
    item_id: string;
    worker_id: string;
    result: any;                 // Processing result
    duration_ms: number;
    credits_charged: number;
    completed_at: string;
  };
}

// item.failed
interface ItemFailedEvent extends BaseEvent {
  type: 'item.failed';
  payload: {
    job_id: string;
    item_id: string;
    worker_id: string;
    error: string;
    error_code: string;
    error_type: 'validation' | 'timeout' | 'exception' | 'resource';
    duration_ms: number;
    retry_count: number;
    max_retries: number;
    will_retry: boolean;
    failed_at: string;
    stack_trace?: string;        // Only in debug mode
  };
}

// item.retry
interface ItemRetryEvent extends BaseEvent {
  type: 'item.retry';
  payload: {
    job_id: string;
    item_id: string;
    retry_count: number;
    max_retries: number;
    previous_error: string;
    previous_worker: string;
    scheduled_at: string;
    backoff_ms: number;
  };
}

// item.abandoned
interface ItemAbandonedEvent extends BaseEvent {
  type: 'item.abandoned';
  payload: {
    job_id: string;
    item_id: string;
    previous_worker: string;
    reason: 'worker_died' | 'heartbeat_timeout' | 'deregistered';
    claimed_duration_ms: number;
    released_at: string;
    will_reclaim: boolean;
  };
}
```

---

## Agent Events

### Event Types

| Event Type | Trigger | Description |
|------------|---------|-------------|
| `agent.registered` | Agent joins | New agent registered |
| `agent.heartbeat` | Heartbeat sent | Agent still alive |
| `agent.stale` | Heartbeat missed | Agent may be dead |
| `agent.deregistered` | Agent leaves | Agent removed |
| `agent.status_changed` | Status update | Agent status changed |

### Event Definitions

```typescript
// agent.registered
interface AgentRegisteredEvent extends BaseEvent {
  type: 'agent.registered';
  payload: {
    agent_id: string;
    agent_name: string;
    agent_type: 'orchestrator' | 'worker';
    capabilities: string[];
    registered_at: string;
    metadata: Record<string, any>;
  };
}

// agent.heartbeat
interface AgentHeartbeatEvent extends BaseEvent {
  type: 'agent.heartbeat';
  payload: {
    agent_id: string;
    status: 'active' | 'idle';
    current_jobs: string[];
    items_processing: number;
    last_activity_at: string;
    heartbeat_at: string;
    uptime_seconds: number;
    resource_usage?: {
      cpu_percent: number;
      memory_mb: number;
    };
  };
}

// agent.stale
interface AgentStaleEvent extends BaseEvent {
  type: 'agent.stale';
  payload: {
    agent_id: string;
    agent_name: string;
    last_heartbeat_at: string;
    stale_duration_seconds: number;
    current_jobs: string[];
    items_at_risk: number;
  };
}

// agent.deregistered
interface AgentDeregisteredEvent extends BaseEvent {
  type: 'agent.deregistered';
  payload: {
    agent_id: string;
    agent_name: string;
    reason: 'requested' | 'timeout' | 'error' | 'admin';
    jobs_transferred: number;
    items_abandoned: number;
    deregistered_at: string;
    lifetime_seconds: number;
  };
}

// agent.status_changed
interface AgentStatusChangedEvent extends BaseEvent {
  type: 'agent.status_changed';
  payload: {
    agent_id: string;
    previous_status: 'active' | 'idle' | 'stale';
    new_status: 'active' | 'idle' | 'stale';
    reason: string;
    changed_at: string;
  };
}
```

---

## Message Events

### Event Types

| Event Type | Trigger | Description |
|------------|---------|-------------|
| `message.sent` | Message sent | New message dispatched |
| `message.delivered` | NOTIFY received | Message reached target |
| `message.read` | Agent reads | Message acknowledged |
| `message.failed` | Delivery failed | Message could not be delivered |
| `message.timeout` | No response | Invoke timed out |

### Event Definitions

```typescript
// message.sent
interface MessageSentEvent extends BaseEvent {
  type: 'message.sent';
  payload: {
    message_id: string;
    from_agent: string;
    to_agent: string;
    message_type: 'invoke' | 'response' | 'notification' | 'broadcast';
    payload_size_bytes: number;
    correlation_id?: string;
    invoke_id?: string;
    job_id?: string;
    sent_at: string;
  };
}

// message.delivered
interface MessageDeliveredEvent extends BaseEvent {
  type: 'message.delivered';
  payload: {
    message_id: string;
    from_agent: string;
    to_agent: string;
    delivered_at: string;
    latency_ms: number;
    delivery_method: 'notify' | 'poll';
  };
}

// message.read
interface MessageReadEvent extends BaseEvent {
  type: 'message.read';
  payload: {
    message_id: string;
    from_agent: string;
    to_agent: string;
    read_at: string;
    time_to_read_ms: number;     // From delivery to read
  };
}

// message.failed
interface MessageFailedEvent extends BaseEvent {
  type: 'message.failed';
  payload: {
    message_id: string;
    from_agent: string;
    to_agent: string;
    error: string;
    error_code: 'agent_not_found' | 'agent_stale' | 'queue_full' | 'internal';
    failed_at: string;
    retry_scheduled: boolean;
  };
}

// message.timeout
interface MessageTimeoutEvent extends BaseEvent {
  type: 'message.timeout';
  payload: {
    message_id: string;
    invoke_id: string;
    from_agent: string;
    to_agent: string;
    timeout_seconds: number;
    elapsed_seconds: number;
    timed_out_at: string;
  };
}
```

---

## Invoke Events

### Event Types

| Event Type | Trigger | Description |
|------------|---------|-------------|
| `invoke.started` | Invoke begins | Request-response initiated |
| `invoke.completed` | Response received | Invoke finished successfully |
| `invoke.failed` | Invoke error | Invoke terminated with error |
| `invoke.timeout` | No response | Invoke exceeded timeout |

### Event Definitions

```typescript
// invoke.started
interface InvokeStartedEvent extends BaseEvent {
  type: 'invoke.started';
  payload: {
    invoke_id: string;
    caller_agent: string;
    target_agent: string;
    action: string;
    job_id?: string;
    timeout_seconds: number;
    started_at: string;
  };
}

// invoke.completed
interface InvokeCompletedEvent extends BaseEvent {
  type: 'invoke.completed';
  payload: {
    invoke_id: string;
    caller_agent: string;
    target_agent: string;
    action: string;
    duration_ms: number;
    credits_charged: number;
    result_size_bytes: number;
    completed_at: string;
  };
}

// invoke.failed
interface InvokeFailedEvent extends BaseEvent {
  type: 'invoke.failed';
  payload: {
    invoke_id: string;
    caller_agent: string;
    target_agent: string;
    action: string;
    error: string;
    error_code: string;
    error_type: 'validation' | 'execution' | 'timeout' | 'agent_error';
    duration_ms: number;
    failed_at: string;
  };
}

// invoke.timeout
interface InvokeTimeoutEvent extends BaseEvent {
  type: 'invoke.timeout';
  payload: {
    invoke_id: string;
    caller_agent: string;
    target_agent: string;
    action: string;
    timeout_seconds: number;
    elapsed_seconds: number;
    timed_out_at: string;
  };
}
```

---

## Credit Events

### Event Types

| Event Type | Trigger | Description |
|------------|---------|-------------|
| `credit.reserved` | Job created | Credits held for job |
| `credit.charged` | Skill used | Credits deducted |
| `credit.refunded` | Job cancelled | Credits returned |
| `credit.low` | Balance warning | Below threshold |
| `credit.depleted` | Balance zero | No credits available |

### Event Definitions

```typescript
// credit.reserved
interface CreditReservedEvent extends BaseEvent {
  type: 'credit.reserved';
  payload: {
    ledger_id: string;
    job_id: string;
    amount: number;
    balance_after: number;
    reserved_at: string;
    estimated_items: number;
  };
}

// credit.charged
interface CreditChargedEvent extends BaseEvent {
  type: 'credit.charged';
  payload: {
    ledger_id: string;
    job_id?: string;
    skill: string;
    amount: number;
    balance_after: number;
    charged_at: string;
    item_id?: string;
    invoke_id?: string;
  };
}

// credit.refunded
interface CreditRefundedEvent extends BaseEvent {
  type: 'credit.refunded';
  payload: {
    ledger_id: string;
    job_id: string;
    amount: number;
    balance_after: number;
    reason: 'cancellation' | 'overestimate' | 'error_recovery';
    refunded_at: string;
    cancelled_items: number;
  };
}

// credit.low
interface CreditLowEvent extends BaseEvent {
  type: 'credit.low';
  payload: {
    current_balance: number;
    threshold: number;
    percent_remaining: number;
    estimated_runway_hours: number;
    triggered_at: string;
  };
}

// credit.depleted
interface CreditDepletedEvent extends BaseEvent {
  type: 'credit.depleted';
  payload: {
    last_balance: number;
    depleted_at: string;
    jobs_paused: string[];
    invokes_blocked: number;
  };
}
```

---

## Blackboard Events

### Event Types

| Event Type | Trigger | Description |
|------------|---------|-------------|
| `blackboard.set` | Key written | Value created/updated |
| `blackboard.delete` | Key deleted | Value removed |
| `blackboard.increment` | Counter changed | Atomic increment |
| `blackboard.lock.acquired` | Lock taken | Distributed lock acquired |
| `blackboard.lock.released` | Lock freed | Lock released |
| `blackboard.expired` | TTL reached | Key auto-removed |

### Event Definitions

```typescript
// blackboard.set
interface BlackboardSetEvent extends BaseEvent {
  type: 'blackboard.set';
  payload: {
    key: string;
    value_type: 'string' | 'integer' | 'json';
    value_size_bytes: number;
    ttl_seconds: number | null;
    is_update: boolean;          // false = new key
    set_by: string;              // Agent or user
    set_at: string;
  };
}

// blackboard.delete
interface BlackboardDeleteEvent extends BaseEvent {
  type: 'blackboard.delete';
  payload: {
    key: string;
    deleted_by: string;
    deleted_at: string;
    had_lock: boolean;
  };
}

// blackboard.increment
interface BlackboardIncrementEvent extends BaseEvent {
  type: 'blackboard.increment';
  payload: {
    key: string;
    amount: number;
    old_value: number;
    new_value: number;
    incremented_by: string;
    incremented_at: string;
  };
}

// blackboard.lock.acquired
interface BlackboardLockAcquiredEvent extends BaseEvent {
  type: 'blackboard.lock.acquired';
  payload: {
    key: string;
    lock_id: string;
    owner: string;
    ttl_seconds: number;
    waited_ms: number;
    acquired_at: string;
  };
}

// blackboard.lock.released
interface BlackboardLockReleasedEvent extends BaseEvent {
  type: 'blackboard.lock.released';
  payload: {
    key: string;
    lock_id: string;
    owner: string;
    held_ms: number;
    released_at: string;
    reason: 'explicit' | 'expired' | 'owner_deregistered';
  };
}

// blackboard.expired
interface BlackboardExpiredEvent extends BaseEvent {
  type: 'blackboard.expired';
  payload: {
    key: string;
    expired_at: string;
    original_ttl_seconds: number;
    created_at: string;
  };
}
```

---

## System Events

### Event Types

| Event Type | Trigger | Description |
|------------|---------|-------------|
| `system.health_changed` | Service status | Health state changed |
| `system.rate_limited` | Limit hit | Request throttled |
| `system.maintenance` | Planned work | Scheduled maintenance |
| `system.incident` | Issue detected | System problem |

### Event Definitions

```typescript
// system.health_changed
interface SystemHealthChangedEvent extends BaseEvent {
  type: 'system.health_changed';
  payload: {
    service: 'api' | 'database' | 'redis' | 'workers';
    previous_status: 'healthy' | 'degraded' | 'unhealthy';
    new_status: 'healthy' | 'degraded' | 'unhealthy';
    message: string;
    changed_at: string;
  };
}

// system.rate_limited
interface SystemRateLimitedEvent extends BaseEvent {
  type: 'system.rate_limited';
  payload: {
    endpoint: string;
    limit: number;
    window_seconds: number;
    retry_after_seconds: number;
    limited_at: string;
  };
}

// system.maintenance
interface SystemMaintenanceEvent extends BaseEvent {
  type: 'system.maintenance';
  payload: {
    maintenance_id: string;
    type: 'scheduled' | 'emergency';
    title: string;
    description: string;
    starts_at: string;
    ends_at: string;
    affected_services: string[];
  };
}
```

---

## SSE Implementation

### Connection

```typescript
// Client-side SSE connection
function connectJobStream(jobId: string, token: string): EventSource {
  const url = new URL(`https://agenticverz.com/api/v1/jobs/${jobId}/stream`);
  url.searchParams.set('token', token);

  const eventSource = new EventSource(url.toString());

  eventSource.onopen = () => {
    console.log('SSE connection opened');
  };

  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    // Implement reconnection with exponential backoff
  };

  // Generic message handler
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleEvent(data);
  };

  // Typed event handlers
  eventSource.addEventListener('job.progress', (event) => {
    const progress: JobProgressEvent = JSON.parse(event.data);
    updateJobProgress(progress);
  });

  eventSource.addEventListener('item.completed', (event) => {
    const item: ItemCompletedEvent = JSON.parse(event.data);
    updateItemStatus(item);
  });

  return eventSource;
}
```

### Server-Sent Event Format

```
id: evt_abc123
event: job.progress
data: {"type":"job.progress","timestamp":"2025-12-13T14:30:00Z","payload":{...}}

id: evt_abc124
event: item.completed
data: {"type":"item.completed","timestamp":"2025-12-13T14:30:01Z","payload":{...}}
```

### Reconnection Strategy

```typescript
class SSEConnection {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseDelay = 1000;

  connect(url: string) {
    this.eventSource = new EventSource(url);

    this.eventSource.onerror = () => {
      this.reconnect(url);
    };
  }

  private reconnect(url: string) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    const delay = Math.min(
      this.baseDelay * Math.pow(2, this.reconnectAttempts),
      30000 // Max 30 seconds
    );

    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(url);
    }, delay);
  }
}
```

---

## WebSocket Implementation

### Connection

```typescript
class AOSWebSocket {
  private ws: WebSocket | null = null;
  private subscriptions: Set<string> = new Set();

  connect(token: string) {
    const url = `wss://agenticverz.com/ws?token=${token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      // Resubscribe to previous subscriptions
      this.subscriptions.forEach(sub => this.subscribe(sub));
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = (event) => {
      if (!event.wasClean) {
        this.reconnect(token);
      }
    };
  }

  subscribe(channel: string) {
    this.subscriptions.add(channel);
    this.send({
      type: 'subscribe',
      channel: channel
    });
  }

  unsubscribe(channel: string) {
    this.subscriptions.delete(channel);
    this.send({
      type: 'unsubscribe',
      channel: channel
    });
  }

  private send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private handleMessage(message: any) {
    switch (message.type) {
      case 'event':
        this.dispatchEvent(message.event);
        break;
      case 'ack':
        // Subscription acknowledged
        break;
      case 'error':
        console.error('WebSocket error:', message.error);
        break;
    }
  }
}
```

### WebSocket Message Format

```typescript
// Client → Server
interface SubscribeMessage {
  type: 'subscribe';
  channel: string;           // e.g., 'jobs:job_abc123', 'agents:*'
}

interface UnsubscribeMessage {
  type: 'unsubscribe';
  channel: string;
}

// Server → Client
interface EventMessage {
  type: 'event';
  channel: string;
  event: BaseEvent;
}

interface AckMessage {
  type: 'ack';
  channel: string;
  subscribed: boolean;
}

interface ErrorMessage {
  type: 'error';
  code: string;
  message: string;
}
```

### Channel Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| `jobs:{job_id}` | Single job events | `jobs:job_abc123` |
| `jobs:*` | All job events | — |
| `agents:{agent_id}` | Single agent events | `agents:agent_xyz` |
| `agents:*` | All agent events | — |
| `messages:{agent_id}` | Messages for agent | `messages:agent_xyz` |
| `credits` | Credit events | — |
| `system` | System events | — |

---

## React Hooks for Events

### useJobEvents Hook

```typescript
function useJobEvents(jobId: string) {
  const [events, setEvents] = useState<JobEvent[]>([]);
  const [progress, setProgress] = useState<JobProgressEvent | null>(null);

  useEffect(() => {
    const eventSource = connectJobStream(jobId, getToken());

    eventSource.addEventListener('job.progress', (e) => {
      const event = JSON.parse(e.data);
      setProgress(event);
      setEvents(prev => [...prev, event]);
    });

    eventSource.addEventListener('item.completed', (e) => {
      const event = JSON.parse(e.data);
      setEvents(prev => [...prev, event]);
    });

    return () => {
      eventSource.close();
    };
  }, [jobId]);

  return { events, progress };
}
```

### useMessageStream Hook

```typescript
function useMessageStream(agentIds: string[]) {
  const [messages, setMessages] = useState<MessageEvent[]>([]);

  useEffect(() => {
    const ws = new AOSWebSocket();
    ws.connect(getToken());

    agentIds.forEach(id => {
      ws.subscribe(`messages:${id}`);
    });

    ws.onEvent((event) => {
      if (event.type.startsWith('message.')) {
        setMessages(prev => [event, ...prev].slice(0, 100));
      }
    });

    return () => {
      ws.disconnect();
    };
  }, [agentIds]);

  return messages;
}
```

---

## Event Processing Patterns

### Event Reducer

```typescript
type JobState = {
  job: Job | null;
  items: Map<string, JobItem>;
  loading: boolean;
  error: Error | null;
};

function jobReducer(state: JobState, event: BaseEvent): JobState {
  switch (event.type) {
    case 'job.started':
      return {
        ...state,
        job: { ...state.job!, status: 'running', started_at: event.payload.started_at }
      };

    case 'job.progress':
      return {
        ...state,
        job: {
          ...state.job!,
          completed_items: event.payload.completed_items,
          failed_items: event.payload.failed_items,
          progress_percent: event.payload.progress_percent
        }
      };

    case 'item.claimed':
      const claimedItem = state.items.get(event.payload.item_id);
      if (claimedItem) {
        const updated = new Map(state.items);
        updated.set(event.payload.item_id, {
          ...claimedItem,
          status: 'claimed',
          worker_id: event.payload.worker_id,
          claimed_at: event.payload.claimed_at
        });
        return { ...state, items: updated };
      }
      return state;

    case 'item.completed':
      const completedItem = state.items.get(event.payload.item_id);
      if (completedItem) {
        const updated = new Map(state.items);
        updated.set(event.payload.item_id, {
          ...completedItem,
          status: 'completed',
          result: event.payload.result,
          duration_ms: event.payload.duration_ms,
          completed_at: event.payload.completed_at
        });
        return { ...state, items: updated };
      }
      return state;

    case 'job.completed':
    case 'job.failed':
    case 'job.cancelled':
      return {
        ...state,
        job: {
          ...state.job!,
          status: event.type.split('.')[1] as any,
          completed_at: event.payload.completed_at || event.payload.failed_at || event.payload.cancelled_at
        }
      };

    default:
      return state;
  }
}
```

---

## Document Revision

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-13 | Initial event model definitions |
