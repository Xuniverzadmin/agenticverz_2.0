// Layer: L1 — Product Experience
// Product: ai-console
// Temporal:
//   Trigger: import-time
//   Execution: sync
// Role: Agent type definitions
// Callers: Agent-related components
// Allowed Imports: L2
// Forbidden Imports: L3, L4, L5, L6
// Reference: Frontend Types

export interface Agent {
  id: string;
  name?: string;
  type: 'orchestrator' | 'worker';
  status: 'active' | 'idle' | 'stale';
  capabilities?: string[];
  registered_at?: string;
  last_heartbeat?: string;
  heartbeat_age_seconds?: number;
  current_jobs?: string[];
  metadata?: Record<string, unknown>;
}

export interface AgentDetail extends Agent {
  jobs_completed: number;
  jobs_failed: number;
  messages_sent: number;
  messages_received: number;
  credits_consumed: number;
  uptime_seconds: number;
}

export interface AgentFilters {
  status?: 'active' | 'idle' | 'stale';
  type?: 'orchestrator' | 'worker';
  search?: string;
  page?: number;
  limit?: number;
}

export interface AgentStats {
  total: number;
  active: number;
  idle: number;
  stale: number;
  orchestrators?: number;
  workers?: number;
  by_type?: {
    orchestrator: number;
    worker: number;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit?: number;
  page_size?: number;
  has_more?: boolean;
}
