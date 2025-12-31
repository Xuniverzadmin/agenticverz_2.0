// Layer: L1 — Product Experience
// Product: ai-console
// Temporal:
//   Trigger: import-time
//   Execution: sync
// Role: Frontend constants and configuration
// Callers: All frontend components
// Allowed Imports: L2
// Forbidden Imports: L3, L4, L5, L6
// Reference: Frontend Utilities

export const API_BASE = import.meta.env.VITE_API_BASE;
export const WS_URL = import.meta.env.VITE_WS_URL;

export const REFRESH_INTERVALS = {
  FAST: 5000,    // 5 seconds
  NORMAL: 30000, // 30 seconds
  SLOW: 60000,   // 1 minute
} as const;

export const SKILL_COSTS: Record<string, number> = {
  agent_spawn: 5,
  agent_invoke: 10,
  blackboard_read: 1,
  blackboard_write: 1,
  blackboard_lock: 1,
  job_item: 2,
};

export const STATUS_COLORS = {
  active: 'text-green-500',
  idle: 'text-gray-500',
  stale: 'text-yellow-500',
  running: 'text-blue-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
  cancelled: 'text-gray-500',
  pending: 'text-yellow-500',
  claimed: 'text-blue-500',
  delivered: 'text-green-500',
  read: 'text-green-600',
} as const;

export const STATUS_VARIANTS = {
  active: 'success',
  idle: 'default',
  stale: 'warning',
  running: 'info',
  completed: 'success',
  failed: 'error',
  cancelled: 'default',
  pending: 'warning',
  claimed: 'info',
  delivered: 'success',
  read: 'success',
} as const;

export const PAGE_SIZES = [10, 25, 50, 100] as const;
export const DEFAULT_PAGE_SIZE = 25;
