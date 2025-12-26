/**
 * Founder Timeline API Client
 *
 * Phase 5E-1: Read-only, verbatim decision record consumption.
 *
 * Endpoints:
 * - GET /founder/timeline/run/{run_id} - Complete run timeline
 * - GET /founder/timeline/decisions - All decision records
 * - GET /founder/timeline/decisions/{decision_id} - Single record
 * - GET /founder/timeline/count - Count records
 *
 * Rules:
 * - Chronological order only
 * - No grouping
 * - No interpretation
 * - Verbatim display
 */

import { apiClient } from './client';

// =============================================================================
// Types (Matching Backend Models)
// =============================================================================

export interface DecisionRecordView {
  decision_id: string;
  decision_type: string;
  decision_source: string;
  decision_trigger: string;
  decision_inputs: Record<string, unknown>;
  decision_outcome: string;
  decision_reason: string | null;
  run_id: string | null;
  workflow_id: string | null;
  tenant_id: string;
  request_id: string | null;
  causal_role: string;
  decided_at: string;
  details: Record<string, unknown>;
}

export interface TimelineEntry {
  entry_type: 'pre_run' | 'decision' | 'outcome';
  timestamp: string;
  record: Record<string, unknown>;
}

export interface RunTimeline {
  run_id: string;
  entries: TimelineEntry[];
  entry_count: number;
}

export interface DecisionCount {
  count: number;
  error?: string;
}

// =============================================================================
// API Functions (Read-Only)
// =============================================================================

/**
 * Get complete timeline for a run.
 *
 * Returns: PRE-RUN -> DECISION RECORDS -> OUTCOME
 * Chronological. No interpretation.
 */
export async function getRunTimeline(runId: string): Promise<RunTimeline> {
  const response = await apiClient.get(`/founder/timeline/run/${runId}`);
  return response.data;
}

/**
 * List all decision records.
 *
 * For founder forensics across runs.
 * No aggregation, no scoring.
 */
export async function listDecisionRecords(params?: {
  limit?: number;
  offset?: number;
  decision_type?: string;
  tenant_id?: string;
}): Promise<DecisionRecordView[]> {
  const response = await apiClient.get('/founder/timeline/decisions', { params });
  return response.data;
}

/**
 * Get a single decision record by ID.
 *
 * All fields exposed. No interpretation.
 */
export async function getDecisionRecord(decisionId: string): Promise<DecisionRecordView> {
  const response = await apiClient.get(`/founder/timeline/decisions/${decisionId}`);
  return response.data;
}

/**
 * Count decision records.
 *
 * No aggregation beyond counting.
 */
export async function countDecisionRecords(params?: {
  decision_type?: string;
  tenant_id?: string;
}): Promise<DecisionCount> {
  const response = await apiClient.get('/founder/timeline/count', { params });
  return response.data;
}
