export interface Job {
  id: string;
  orchestrator_agent?: string;
  worker_agent?: string;
  task?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | string;
  parallelism?: number;
  total_items?: number;
  completed_items?: number;
  failed_items?: number;
  progress_percent?: number;
  credits_reserved?: number;
  credits_spent?: number;
  credits_refunded?: number;
  estimated_cost_cents?: number;
  actual_cost_cents?: number;
  created_at?: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface JobDetail extends Job {
  item_counts?: {
    pending: number;
    claimed: number;
    completed: number;
    failed: number;
  };
  timeline?: Array<{
    event: string;
    timestamp: string;
    details?: Record<string, unknown>;
  }>;
}

export interface JobItem {
  id: string;
  job_id?: string;
  status: 'pending' | 'claimed' | 'completed' | 'failed';
  worker_id?: string | null;
  skill?: string;
  params?: Record<string, unknown>;
  result?: unknown;
  error?: string | null;
  duration_ms?: number | null;
  retries?: number;
  created_at?: string;
  claimed_at?: string | null;
  completed_at?: string | null;
}

export interface CreateJobRequest {
  orchestrator_agent?: string;
  worker_agent?: string;
  task: string;
  items?: Array<{ id?: string; skill?: string; params?: Record<string, unknown>; [key: string]: unknown }>;
  parallelism?: number;
  max_retries?: number;
  timeout_seconds?: number;
}

export interface SimulationResult {
  feasible: boolean;
  estimated_cost_cents?: number;
  estimated_credits?: number;
  estimated_duration_ms?: number;
  estimated_duration_seconds?: number;
  skill_breakdown?: Array<{
    skill: string;
    cost_cents: number;
    duration_ms: number;
  }>;
  credit_breakdown?: {
    reserve_cost: number;
    item_cost: number;
    skill_cost: number;
    total: number;
  };
  budget_check?: {
    sufficient: boolean;
    available?: number;
    balance?: number;
    required: number;
    shortfall?: number;
  };
  time_estimate?: {
    p50_seconds: number;
    p95_seconds: number;
    p99_seconds: number;
  };
  warnings: string[];
  risks?: Array<{
    severity: 'low' | 'medium' | 'high';
    message: string;
  }>;
  resource_check?: {
    agents_available: boolean;
    workers_available: number;
    workers_required: number;
  };
}

export interface CancelResult {
  job_id: string;
  status: 'cancelled';
  completed_items: number;
  cancelled_items: number;
  credits_refunded: number;
  cancelled_at?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit?: number;
  page_size?: number;
  has_more?: boolean;
}
