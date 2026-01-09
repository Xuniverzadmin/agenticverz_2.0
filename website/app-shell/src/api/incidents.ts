/**
 * @audience customer
 *
 * Incidents API Client - SDSR Real Data
 * Calls /api/v1/incidents for real incident data from backend
 * Reference: PIN-370 (SDSR Pipeline)
 */
import { apiClient } from './client';

export interface IncidentSummary {
  id: string;
  source_run_id: string | null;
  source_type: string;
  category: string;
  severity: string;
  status: string;
  title: string;
  description: string | null;
  error_code: string | null;
  error_message: string | null;
  tenant_id: string;
  affected_agent_id: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  is_synthetic: boolean;
  synthetic_scenario_id: string | null;
}

export interface IncidentsResponse {
  incidents: IncidentSummary[];
  total: number;
  page: number;
  per_page: number;
}

export interface IncidentCountBySeverity {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface IncidentsMetricsResponse {
  total_open: number;
  total_resolved: number;
  by_severity: IncidentCountBySeverity;
}

export interface IncidentsQueryParams {
  page?: number;
  per_page?: number;
  status?: string;
  severity?: string;
  category?: string;
  include_synthetic?: boolean;
}

/**
 * Fetch incidents from the backend
 * This uses the real /api/v1/incidents endpoint
 */
export async function fetchIncidents(params: IncidentsQueryParams = {}): Promise<IncidentsResponse> {
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
  if (params.severity !== undefined) {
    queryParams.set('severity', params.severity);
  }
  if (params.category !== undefined) {
    queryParams.set('category', params.category);
  }
  if (params.include_synthetic !== undefined) {
    queryParams.set('include_synthetic', params.include_synthetic.toString());
  }

  const url = `/api/v1/incidents${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<IncidentsResponse>(url);
  return response.data;
}

/**
 * Fetch incidents metrics from the backend
 */
export async function fetchIncidentsMetrics(include_synthetic: boolean = true): Promise<IncidentsMetricsResponse> {
  const url = `/api/v1/incidents/metrics?include_synthetic=${include_synthetic}`;
  const response = await apiClient.get<IncidentsMetricsResponse>(url);
  return response.data;
}

/**
 * Fetch a single incident by ID
 */
export async function fetchIncidentDetail(incidentId: string): Promise<IncidentSummary> {
  const response = await apiClient.get<IncidentSummary>(`/api/v1/incidents/${incidentId}`);
  return response.data;
}

/**
 * Fetch incidents linked to a specific run
 */
export async function fetchIncidentsForRun(runId: string): Promise<{ run_id: string; incidents: IncidentSummary[]; total: number }> {
  const response = await apiClient.get<{ run_id: string; incidents: IncidentSummary[]; total: number }>(`/api/v1/incidents/by-run/${runId}`);
  return response.data;
}
