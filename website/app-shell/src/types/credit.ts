// Layer: L1 — Product Experience
// Product: ai-console
// Temporal:
//   Trigger: import-time
//   Execution: sync
// Role: Credit type definitions
// Callers: Credit-related components
// Allowed Imports: L2
// Forbidden Imports: L3, L4, L5, L6
// Reference: Frontend Types

export interface CreditBalance {
  balance: number;
  reserved: number;
  available: number;
  last_updated: string;
}

export interface LedgerEntry {
  id: string;
  type: 'reserve' | 'charge' | 'refund' | 'topup' | 'adjustment' | string;
  amount: number;
  balance_after: number;
  job_id?: string | null;
  skill?: string | null;
  description?: string;
  created_at?: string;
  metadata?: Record<string, unknown>;
}

export interface InvokeAudit {
  invoke_id: string;
  caller_agent?: string;
  target_agent?: string;
  action?: string;
  skill?: string;
  status: 'success' | 'failed' | 'timeout' | 'completed' | string;
  cost_cents?: number;
  duration_ms?: number;
  latency_ms?: number;
  credits_charged?: number;
  job_id?: string | null;
  started_at?: string;
  completed_at?: string | null;
  error?: string;
  error_message?: string;
  error_code?: string;
}

export interface InvokeDetail extends InvokeAudit {
  request_payload?: unknown;
  response_payload?: unknown | null;
  retry_count?: number;
  correlation_id?: string;
  timeline?: Array<{
    event: string;
    timestamp: string;
    details?: unknown;
  }>;
}

export interface MonthlyUsage {
  month: string;
  total_spent: number;
  total_reserved: number;
  total_refunded: number;
  net_spend: number;
  budget: number | null;
  budget_percent: number | null;
}

export interface UsageTimeSeries {
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

export interface Breakdown {
  by: 'skill' | 'job_type' | 'agent';
  total: number;
  items: Array<{
    name: string;
    credits: number;
    percent: number;
    count: number;
  }>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit?: number;
  page_size?: number;
  has_more?: boolean;
}
