// Layer: L1 — Product Experience
// Product: ai-console
// Temporal:
//   Trigger: import-time
//   Execution: sync
// Role: Event type definitions
// Callers: Event-related components
// Allowed Imports: L2
// Forbidden Imports: L3, L4, L5, L6
// Reference: Frontend Types

// Base event structure
export interface BaseEvent {
  id: string;
  type: string;
  timestamp: string;
  tenant_id: string;
  correlation_id?: string;
  sequence?: number;
}

// Job Events
export interface JobCreatedEvent extends BaseEvent {
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
  };
}

export interface JobProgressEvent extends BaseEvent {
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

export interface JobCompletedEvent extends BaseEvent {
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
    success_rate: number;
  };
}

// Item Events
export interface ItemClaimedEvent extends BaseEvent {
  type: 'item.claimed';
  payload: {
    job_id: string;
    item_id: string;
    worker_id: string;
    worker_name: string;
    claimed_at: string;
    wait_time_ms: number;
  };
}

export interface ItemCompletedEvent extends BaseEvent {
  type: 'item.completed';
  payload: {
    job_id: string;
    item_id: string;
    worker_id: string;
    result: unknown;
    duration_ms: number;
    credits_charged: number;
    completed_at: string;
  };
}

export interface ItemFailedEvent extends BaseEvent {
  type: 'item.failed';
  payload: {
    job_id: string;
    item_id: string;
    worker_id: string;
    error: string;
    error_code: string;
    duration_ms: number;
    retry_count: number;
    max_retries: number;
    will_retry: boolean;
    failed_at: string;
  };
}

// Agent Events
export interface AgentRegisteredEvent extends BaseEvent {
  type: 'agent.registered';
  payload: {
    agent_id: string;
    agent_name: string;
    agent_type: 'orchestrator' | 'worker';
    capabilities: string[];
    registered_at: string;
  };
}

export interface AgentHeartbeatEvent extends BaseEvent {
  type: 'agent.heartbeat';
  payload: {
    agent_id: string;
    status: 'active' | 'idle';
    current_jobs: string[];
    items_processing: number;
    heartbeat_at: string;
  };
}

// Message Events
export interface MessageSentEvent extends BaseEvent {
  type: 'message.sent';
  payload: {
    message_id: string;
    from_agent: string;
    to_agent: string;
    message_type: string;
    sent_at: string;
  };
}

export interface MessageDeliveredEvent extends BaseEvent {
  type: 'message.delivered';
  payload: {
    message_id: string;
    from_agent: string;
    to_agent: string;
    delivered_at: string;
    latency_ms: number;
  };
}

// Credit Events
export interface CreditChargedEvent extends BaseEvent {
  type: 'credit.charged';
  payload: {
    ledger_id: string;
    job_id?: string;
    skill: string;
    amount: number;
    balance_after: number;
    charged_at: string;
  };
}

// Union type for all events
export type JobEvent =
  | JobCreatedEvent
  | JobProgressEvent
  | JobCompletedEvent
  | ItemClaimedEvent
  | ItemCompletedEvent
  | ItemFailedEvent;

export type AgentEvent = AgentRegisteredEvent | AgentHeartbeatEvent;

export type MessageEvent = MessageSentEvent | MessageDeliveredEvent;

export type CreditEvent = CreditChargedEvent;

export type AnyEvent = JobEvent | AgentEvent | MessageEvent | CreditEvent;
