/**
 * @audience shared
 *
 * Traces API Client
 * Execution trace viewing (used by both customer and founder)
 *
 * PIN-378: SDSR Extension - Added is_synthetic, synthetic_scenario_id, incident_id fields
 */
import apiClient from './client';

/**
 * Log level derived from step status:
 * - success → INFO
 * - skipped → INFO
 * - retry → WARN
 * - failure → ERROR
 */
export type LogLevel = 'INFO' | 'WARN' | 'ERROR';

/**
 * Source of the trace step
 */
export type StepSource = 'engine' | 'external' | 'replay';

export interface TraceStep {
  step_index: number;
  skill_id: string;
  skill_name: string;
  status: string;
  outcome_category: string;
  outcome_code?: string;
  outcome_data?: Record<string, unknown>;
  cost_cents: number;
  duration_ms: number;
  retry_count: number;
  timestamp: string;
  // SDSR fields (PIN-378)
  source: StepSource;
  level: LogLevel;
  // Hash fields
  input_hash?: string;
  output_hash?: string;
}

export interface Trace {
  run_id: string;
  trace_id: string;
  correlation_id: string;
  tenant_id: string;
  agent_id?: string;
  root_hash?: string;
  status: string;
  started_at: string;
  completed_at?: string;
  created_at: string;
  // SDSR fields (PIN-378)
  is_synthetic: boolean;
  synthetic_scenario_id?: string;
  incident_id?: string;
  // Stats
  total_steps?: number;
  success_count?: number;
  failure_count?: number;
  total_cost_cents?: number;
  total_duration_ms?: number;
  // Steps (only in detail view)
  steps?: TraceStep[];
}

/**
 * Trace list query parameters
 */
export interface TraceQueryParams {
  limit?: number;
  offset?: number;
  status?: string;
  // SDSR filters (PIN-378)
  is_synthetic?: boolean;
  level?: LogLevel;
  incident_id?: string;
  run_id?: string;
  from_date?: string;
  to_date?: string;
}

// List Traces with SDSR filtering (PIN-378)
export async function getTraces(params?: TraceQueryParams): Promise<Trace[]> {
  try {
    const { data } = await apiClient.get('/api/v1/traces', { params });
    return Array.isArray(data) ? data : data?.items || [];
  } catch {
    return [];
  }
}

// Get traces summary stats
export async function getTracesSummary(): Promise<{
  total: number;
  synthetic_count: number;
  by_status: Record<string, number>;
  by_level: Record<LogLevel, number>;
}> {
  const defaultByLevel: Record<LogLevel, number> = { INFO: 0, WARN: 0, ERROR: 0 };
  try {
    const { data } = await apiClient.get('/api/v1/traces/summary');
    return data || { total: 0, synthetic_count: 0, by_status: {}, by_level: defaultByLevel };
  } catch {
    return { total: 0, synthetic_count: 0, by_status: {}, by_level: defaultByLevel };
  }
}

// Get traces by incident (cross-domain correlation)
export async function getTracesByIncident(incidentId: string): Promise<Trace[]> {
  try {
    const { data } = await apiClient.get(`/api/v1/traces/by-incident/${incidentId}`);
    return Array.isArray(data) ? data : data?.items || [];
  } catch {
    return [];
  }
}

// Get Trace by Run ID
export async function getTrace(runId: string): Promise<Trace | null> {
  try {
    const { data } = await apiClient.get(`/api/v1/traces/${runId}`);
    return data;
  } catch {
    return null;
  }
}

// Get Trace by Hash
export async function getTraceByHash(rootHash: string): Promise<Trace | null> {
  try {
    const { data } = await apiClient.get(`/api/v1/traces/by-hash/${rootHash}`);
    return data;
  } catch {
    return null;
  }
}

// Compare Traces
export async function compareTraces(runId1: string, runId2: string) {
  try {
    const { data } = await apiClient.get(`/api/v1/traces/compare/${runId1}/${runId2}`);
    return data;
  } catch {
    return null;
  }
}

// Check Idempotency
export async function checkIdempotency(idempotencyKey: string) {
  try {
    const { data } = await apiClient.get(`/api/v1/traces/idempotency/${idempotencyKey}`);
    return data;
  } catch {
    return null;
  }
}

// Store Trace
export async function storeTrace(trace: Partial<Trace>) {
  const { data } = await apiClient.post('/api/v1/traces', trace);
  return data;
}

// Delete Trace
export async function deleteTrace(runId: string) {
  await apiClient.delete(`/api/v1/traces/${runId}`);
}

// Cleanup Old Traces
export async function cleanupTraces(olderThanDays?: number) {
  const { data } = await apiClient.post('/api/v1/traces/cleanup', { older_than_days: olderThanDays });
  return data;
}

// Mismatches
export async function reportMismatch(traceId: string, mismatch: {
  field: string;
  expected: unknown;
  actual: unknown;
}) {
  const { data } = await apiClient.post(`/api/v1/traces/${traceId}/mismatch`, mismatch);
  return data;
}

export async function getTraceMismatches(traceId: string) {
  try {
    const { data } = await apiClient.get(`/api/v1/traces/${traceId}/mismatches`);
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export async function resolveMismatch(traceId: string, mismatchId: string, resolution: string) {
  const { data } = await apiClient.post(
    `/api/v1/traces/${traceId}/mismatches/${mismatchId}/resolve`,
    { resolution }
  );
  return data;
}
