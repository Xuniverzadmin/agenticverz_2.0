/**
 * @audience customer
 *
 * Activity API Client - SDSR Real Data
 * Calls /api/v1/activity/runs for real run data from backend
 * Reference: PIN-370 (SDSR Pipeline)
 */
import { apiClient } from './client';

export interface RunSummary {
  run_id: string;
  status: string;
  goal: string;
  agent_id: string;
  tenant_id: string | null;
  parent_run_id: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  is_synthetic: boolean;
  synthetic_scenario_id: string | null;
}

export interface ActivityResponse {
  runs: RunSummary[];
  total: number;
  page: number;
  per_page: number;
}

export interface ActivityQueryParams {
  page?: number;
  per_page?: number;
  status?: string;
  include_synthetic?: boolean;
}

/**
 * Fetch activity runs from the backend
 * This uses the real /api/v1/activity/runs endpoint
 */
export async function fetchActivityRuns(params: ActivityQueryParams = {}): Promise<ActivityResponse> {
  const queryParams = new URLSearchParams();

  if (params.page !== undefined) {
    queryParams.set('page', params.page.toString());
  }
  if (params.per_page !== undefined) {
    queryParams.set('per_page', params.per_page.toString());
  }
  if (params.status !== undefined) {
    queryParams.set('status', params.status);
  }
  if (params.include_synthetic !== undefined) {
    queryParams.set('include_synthetic', params.include_synthetic.toString());
  }

  const url = `/api/v1/activity/runs${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<ActivityResponse>(url);
  return response.data;
}

/**
 * Fetch a single run by ID
 */
export async function fetchRunDetail(runId: string): Promise<RunSummary> {
  const response = await apiClient.get<RunSummary>(`/api/v1/activity/runs/${runId}`);
  return response.data;
}

// =============================================================================
// Activity Summary (HIL v1 Interpretation - PIN-417)
// =============================================================================

/**
 * Activity Summary Response - HIL v1 interpretation endpoint
 * Reference: backend/contracts/activity_summary.schema.json
 */
export interface RunsByStatus {
  running: number;
  completed: number;
  failed: number;
}

export interface AttentionSummary {
  at_risk_count: number;
  reasons: ('long_running' | 'near_budget_threshold')[];
}

export interface ActivityProvenance {
  derived_from: string[];
  aggregation: 'COUNT' | 'SUM' | 'TREND' | 'STATUS_BREAKDOWN' | 'TOP_N' | 'LATEST';
  generated_at: string;
}

export interface ActivitySummaryResponse {
  window: '24h' | '7d';
  runs: {
    total: number;
    by_status: RunsByStatus;
  };
  attention: AttentionSummary;
  provenance: ActivityProvenance;
}

export interface ActivitySummaryParams {
  window?: '24h' | '7d';
  include_synthetic?: boolean;
}

/**
 * Fetch activity summary from the backend (HIL v1 interpretation endpoint)
 * Reference: PIN-417 Phase 3
 */
export async function fetchActivitySummary(
  params: ActivitySummaryParams = {}
): Promise<ActivitySummaryResponse> {
  const queryParams = new URLSearchParams();

  if (params.window !== undefined) {
    queryParams.set('window', params.window);
  }
  if (params.include_synthetic !== undefined) {
    queryParams.set('include_synthetic', params.include_synthetic.toString());
  }

  const url = `/api/v1/activity/summary${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<ActivitySummaryResponse>(url);
  return response.data;
}
