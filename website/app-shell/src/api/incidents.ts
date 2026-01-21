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

// =============================================================================
// HIL v1: Incidents Summary Response (PIN-417)
// =============================================================================

export interface IncidentsByLifecycleState {
  active: number;
  acked: number;
  resolved: number;
}

export interface IncidentsCountData {
  total: number;
  by_lifecycle_state: IncidentsByLifecycleState;
}

export interface IncidentsAttentionSummary {
  count: number;
  reasons: string[];  // Registry-backed: 'unresolved', 'high_severity'
}

export interface IncidentsProvenance {
  derived_from: string[];  // Capability IDs
  aggregation: string;
  generated_at: string;
}

export interface IncidentsSummaryResponse {
  window: string;
  incidents: IncidentsCountData;
  attention: IncidentsAttentionSummary;
  provenance: IncidentsProvenance;
}

export interface IncidentsSummaryParams {
  window?: string;  // '24h' or '7d'
  include_synthetic?: boolean;
}

// =============================================================================
// Phase 3 Migration: Topic-Scoped Fetch Functions
// Reference: INCIDENTS_DOMAIN_MIGRATION_PLAN.md
// =============================================================================

export interface TopicScopedIncidentsParams {
  limit?: number;
  offset?: number;
  severity?: string;
  category?: string;
  cause_type?: string;
  is_synthetic?: boolean;
}

export interface TopicScopedIncidentsResponse {
  items: IncidentSummary[];
  total: number;
  has_more: boolean;
  filters_applied: Record<string, unknown>;
  pagination: {
    limit: number;
    offset: number;
    next_offset: number | null;
  };
}

/**
 * Fetch ACTIVE incidents (topic-scoped endpoint)
 * Topic enforced at endpoint boundary - no state/topic params needed
 * Reference: Phase 3.1 ACTIVE Topic Rebinding
 */
export async function fetchActiveIncidents(params: TopicScopedIncidentsParams = {}): Promise<TopicScopedIncidentsResponse> {
  const queryParams = new URLSearchParams();

  if (params.limit !== undefined) queryParams.set('limit', params.limit.toString());
  if (params.offset !== undefined) queryParams.set('offset', params.offset.toString());
  if (params.severity !== undefined) queryParams.set('severity', params.severity);
  if (params.category !== undefined) queryParams.set('category', params.category);
  if (params.cause_type !== undefined) queryParams.set('cause_type', params.cause_type);
  if (params.is_synthetic !== undefined) queryParams.set('is_synthetic', params.is_synthetic.toString());

  const url = `/api/v1/incidents/active${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<TopicScopedIncidentsResponse>(url);
  return response.data;
}

/**
 * Fetch RESOLVED incidents (topic-scoped endpoint)
 * Topic enforced at endpoint boundary - no state/topic params needed
 * Reference: Phase 3.2 RESOLVED Topic Rebinding
 */
export async function fetchResolvedIncidents(params: TopicScopedIncidentsParams = {}): Promise<TopicScopedIncidentsResponse> {
  const queryParams = new URLSearchParams();

  if (params.limit !== undefined) queryParams.set('limit', params.limit.toString());
  if (params.offset !== undefined) queryParams.set('offset', params.offset.toString());
  if (params.severity !== undefined) queryParams.set('severity', params.severity);
  if (params.category !== undefined) queryParams.set('category', params.category);
  if (params.cause_type !== undefined) queryParams.set('cause_type', params.cause_type);
  if (params.is_synthetic !== undefined) queryParams.set('is_synthetic', params.is_synthetic.toString());

  const url = `/api/v1/incidents/resolved${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<TopicScopedIncidentsResponse>(url);
  return response.data;
}

/**
 * Fetch HISTORICAL incidents (topic-scoped endpoint)
 * Topic enforced at endpoint boundary - RESOLVED beyond retention window
 * Reference: Phase 3.3 HISTORICAL Topic Rebinding
 */
export async function fetchHistoricalIncidents(params: TopicScopedIncidentsParams & { retention_days?: number } = {}): Promise<TopicScopedIncidentsResponse> {
  const queryParams = new URLSearchParams();

  if (params.limit !== undefined) queryParams.set('limit', params.limit.toString());
  if (params.offset !== undefined) queryParams.set('offset', params.offset.toString());
  if (params.severity !== undefined) queryParams.set('severity', params.severity);
  if (params.category !== undefined) queryParams.set('category', params.category);
  if (params.cause_type !== undefined) queryParams.set('cause_type', params.cause_type);
  if (params.retention_days !== undefined) queryParams.set('retention_days', params.retention_days.toString());

  const url = `/api/v1/incidents/historical${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<TopicScopedIncidentsResponse>(url);
  return response.data;
}

// =============================================================================
// Phase 3 Migration: Historical Analytics (Backend-Computed)
// =============================================================================

export interface HistoricalTrendDataPoint {
  period: string;
  incident_count: number;
  resolved_count: number;
  avg_resolution_time_ms: number | null;
}

export interface HistoricalTrendResponse {
  data_points: HistoricalTrendDataPoint[];
  granularity: string;
  window_days: number;
  total_incidents: number;
  generated_at: string;
}

export interface HistoricalDistributionEntry {
  dimension: string;
  value: string;
  count: number;
  percentage: number;
}

export interface HistoricalDistributionResponse {
  by_category: HistoricalDistributionEntry[];
  by_severity: HistoricalDistributionEntry[];
  by_cause_type: HistoricalDistributionEntry[];
  window_days: number;
  total_incidents: number;
  generated_at: string;
}

export interface CostTrendDataPoint {
  period: string;
  total_cost: number;
  incident_count: number;
  avg_cost_per_incident: number;
}

export interface CostTrendResponse {
  data_points: CostTrendDataPoint[];
  granularity: string;
  window_days: number;
  total_cost: number;
  total_incidents: number;
  generated_at: string;
}

/**
 * Fetch historical incident trend (backend-computed analytics)
 * Reference: Phase 3.3 HISTORICAL Topic Rebinding - HIST-O1
 */
export async function fetchHistoricalTrend(params: { window_days?: number; granularity?: string } = {}): Promise<HistoricalTrendResponse> {
  const queryParams = new URLSearchParams();
  if (params.window_days !== undefined) queryParams.set('window_days', params.window_days.toString());
  if (params.granularity !== undefined) queryParams.set('granularity', params.granularity);

  const url = `/api/v1/incidents/historical/trend${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<HistoricalTrendResponse>(url);
  return response.data;
}

/**
 * Fetch historical incident distribution (backend-computed analytics)
 * Reference: Phase 3.3 HISTORICAL Topic Rebinding - HIST-O2
 */
export async function fetchHistoricalDistribution(params: { window_days?: number } = {}): Promise<HistoricalDistributionResponse> {
  const queryParams = new URLSearchParams();
  if (params.window_days !== undefined) queryParams.set('window_days', params.window_days.toString());

  const url = `/api/v1/incidents/historical/distribution${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<HistoricalDistributionResponse>(url);
  return response.data;
}

/**
 * Fetch historical cost trend (backend-computed analytics)
 * Reference: Phase 3.3 HISTORICAL Topic Rebinding - HIST-O4
 */
export async function fetchHistoricalCostTrend(params: { window_days?: number; granularity?: string } = {}): Promise<CostTrendResponse> {
  const queryParams = new URLSearchParams();
  if (params.window_days !== undefined) queryParams.set('window_days', params.window_days.toString());
  if (params.granularity !== undefined) queryParams.set('granularity', params.granularity);

  const url = `/api/v1/incidents/historical/cost-trend${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<CostTrendResponse>(url);
  return response.data;
}

// =============================================================================
// Legacy Fetch Functions (Kept for backward compatibility during migration)
// These will be deprecated after Phase 5
// =============================================================================

/**
 * @deprecated Use fetchActiveIncidents() or fetchResolvedIncidents() instead
 * Fetch incidents from the backend using generic endpoint
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

// =============================================================================
// HIL v1: Incidents Summary (PIN-417)
// =============================================================================

/**
 * Fetch incidents summary for HIL v1 interpretation panel
 *
 * Returns aggregated incident counts by lifecycle_state (ACTIVE, ACKED, RESOLVED)
 * plus attention signals and provenance metadata.
 *
 * Reference: PIN-417 (HIL v1 Phase 4), incidents_summary.schema.json
 */
export async function fetchIncidentsSummary(params: IncidentsSummaryParams = {}): Promise<IncidentsSummaryResponse> {
  const queryParams = new URLSearchParams();

  if (params.window !== undefined) {
    queryParams.set('window', params.window);
  }
  if (params.include_synthetic !== undefined) {
    queryParams.set('include_synthetic', params.include_synthetic.toString());
  }

  const url = `/api/v1/incidents/summary${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<IncidentsSummaryResponse>(url);
  return response.data;
}
