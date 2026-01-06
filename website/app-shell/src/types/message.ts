// Layer: L1 — Product Experience
// Product: ai-console
// Temporal:
//   Trigger: import-time
//   Execution: sync
// Role: Message type definitions
// Callers: Message components
// Allowed Imports: L2
// Forbidden Imports: L3, L4, L5, L6
// Reference: Frontend Types

export interface Message {
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

export interface MessageDetail extends Message {
  payload: unknown;
  response: unknown | null;
  correlation_id: string | null;
  job_id: string | null;
  invoke_id: string | null;
  error: string | null;
  metadata: Record<string, unknown>;
}

export interface MessageStats {
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

export interface MessageFlow {
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

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}
