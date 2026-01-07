/**
 * @audience founder
 *
 * AUTO_EXECUTE Review API Client - PIN-333
 *
 * Founder-only evidence dashboard for AUTO_EXECUTE decisions.
 * READ-ONLY - No control affordances, no approval/reject actions.
 *
 * Key Constraints:
 * - Evidence-only (execution envelopes + safety flags)
 * - No behavior changes to AUTO_EXECUTE
 * - Founder-scoped (FOPS token required)
 *
 * Reference: PIN-333 - Founder AUTO_EXECUTE Review Dashboard
 */

import apiClient from './client';

// =============================================================================
// Types - Mirror backend DTOs from ops.py
// =============================================================================

export interface AutoExecuteReviewItem {
  invocation_id: string;
  envelope_id: string;
  timestamp: string;
  tenant_id: string;
  capability_id: 'SUB-019';
  execution_vector: 'AUTO_EXEC';
  confidence_score: number;
  threshold: number;
  decision: 'EXECUTED' | 'SKIPPED';
  recovery_action: string | null;
  input_hash: string;
  plan_hash: string;
  safety_checked: boolean;
  safety_passed: boolean;
  safety_flags: string[];
  safety_warnings: string[];
  caller_id: string | null;
  impersonation_declared: boolean;
  impersonation_reason: string | null;
  agent_id: string | null;
  run_id: string | null;
  trace_hash: string | null;
  authority_path: string[];
  evidence_snapshot: Record<string, unknown>;
}

export interface AutoExecuteReviewList {
  items: AutoExecuteReviewItem[];
  total_count: number;
  page: number;
  page_size: number;
  executed_count: number;
  skipped_count: number;
  flagged_count: number;
}

export interface AutoExecuteReviewFilter {
  start_time?: string;
  end_time?: string;
  tenant_id?: string;
  decision?: 'EXECUTED' | 'SKIPPED';
  min_confidence?: number;
  max_confidence?: number;
  has_safety_flags?: boolean;
  page?: number;
  page_size?: number;
}

export interface AutoExecuteReviewStats {
  start_time: string;
  end_time: string;
  total_decisions: number;
  executed_count: number;
  skipped_count: number;
  confidence_distribution: Record<string, number>;
  flagged_count: number;
  flag_counts: Record<string, number>;
  daily_counts: Array<{
    date: string;
    executed: number;
    skipped: number;
    flagged: number;
  }>;
}

// =============================================================================
// API Functions - READ-ONLY
// =============================================================================

/**
 * List AUTO_EXECUTE decisions with filtering
 * FOUNDER ONLY - Evidence retrieval
 */
export async function listAutoExecuteDecisions(
  filter?: AutoExecuteReviewFilter
): Promise<AutoExecuteReviewList> {
  const response = await apiClient.get('/api/v1/founder/review/auto-execute', {
    params: filter,
  });
  return response.data;
}

/**
 * Get single AUTO_EXECUTE decision by invocation ID
 * FOUNDER ONLY - Evidence retrieval
 */
export async function getAutoExecuteDecision(
  invocationId: string
): Promise<AutoExecuteReviewItem> {
  const response = await apiClient.get(
    `/api/v1/founder/review/auto-execute/${invocationId}`
  );
  return response.data;
}

/**
 * Get AUTO_EXECUTE decision statistics
 * FOUNDER ONLY - Aggregate evidence
 */
export async function getAutoExecuteStats(options?: {
  start_time?: string;
  end_time?: string;
  tenant_id?: string;
}): Promise<AutoExecuteReviewStats> {
  const response = await apiClient.get('/api/v1/founder/review/auto-execute/stats', {
    params: options,
  });
  return response.data;
}

// =============================================================================
// Helper Functions - Display Formatting
// =============================================================================

/**
 * Get decision badge color
 */
export function getDecisionColor(decision: 'EXECUTED' | 'SKIPPED'): string {
  return decision === 'EXECUTED'
    ? 'text-green-400 bg-green-900/30'
    : 'text-yellow-400 bg-yellow-900/30';
}

/**
 * Get confidence score color based on threshold proximity
 */
export function getConfidenceColor(score: number, threshold: number): string {
  const margin = score - threshold;
  if (margin >= 0.2) return 'text-green-400';
  if (margin >= 0.1) return 'text-emerald-400';
  if (margin >= 0) return 'text-yellow-400';
  if (margin >= -0.1) return 'text-orange-400';
  return 'text-red-400';
}

/**
 * Get safety flag severity color
 */
export function getSafetyFlagColor(flag: string): string {
  // Blocking flags
  if (flag.includes('BLOCKED') || flag.includes('INJECTION')) {
    return 'text-red-400 bg-red-900/30';
  }
  // Violation flags
  if (flag.includes('VIOLATION') || flag.includes('MISMATCH')) {
    return 'text-orange-400 bg-orange-900/30';
  }
  // Warning flags
  if (flag.includes('MISSING') || flag.includes('UNRESOLVED')) {
    return 'text-yellow-400 bg-yellow-900/30';
  }
  // Info flags
  return 'text-blue-400 bg-blue-900/30';
}

/**
 * Format confidence score as percentage
 */
export function formatConfidence(score: number): string {
  return `${(score * 100).toFixed(1)}%`;
}

/**
 * Format timestamp for display
 */
export function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString();
}

/**
 * Get safety status indicator
 */
export function getSafetyStatus(
  checked: boolean,
  passed: boolean,
  flags: string[]
): { label: string; color: string } {
  if (!checked) {
    return { label: 'NOT CHECKED', color: 'text-gray-400 bg-gray-900/30' };
  }
  if (!passed) {
    return { label: 'FAILED', color: 'text-red-400 bg-red-900/30' };
  }
  if (flags.length > 0) {
    return { label: 'WARNINGS', color: 'text-yellow-400 bg-yellow-900/30' };
  }
  return { label: 'PASSED', color: 'text-green-400 bg-green-900/30' };
}

export default {
  listAutoExecuteDecisions,
  getAutoExecuteDecision,
  getAutoExecuteStats,
  getDecisionColor,
  getConfidenceColor,
  getSafetyFlagColor,
  formatConfidence,
  formatTimestamp,
  getSafetyStatus,
};
