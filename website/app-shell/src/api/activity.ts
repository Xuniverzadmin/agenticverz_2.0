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
