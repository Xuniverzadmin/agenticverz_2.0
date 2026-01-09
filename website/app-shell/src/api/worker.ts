/**
 * @audience founder
 *
 * Worker API Client
 * Worker execution and management (founder-only)
 */
import apiClient from './client';

// Types
export interface WorkerRun {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  brand_request: BrandRequest;
  started_at: string;
  completed_at?: string;
  artifacts?: Record<string, unknown>;
  error?: string;
}

export interface BrandRequest {
  company_name: string;
  mission: string;
  value_proposition: string;
  tagline?: string;
  tone?: {
    primary: 'casual' | 'neutral' | 'professional' | 'formal' | 'luxury';
    secondary?: string;
  };
  target_audience?: 'b2c_consumer' | 'b2c_prosumer' | 'b2b_smb' | 'b2b_enterprise' | 'b2b_developer';
  industry?: string;
  competitors?: string[];
}

export interface WorkerHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  workers_available: number;
  last_check: string;
}

export interface RunEvent {
  event_id: string;
  run_id: string;
  event_type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

// Start a worker run
export async function startWorkerRun(
  workerId: string,
  brandRequest: BrandRequest
): Promise<{ run_id: string }> {
  const { data } = await apiClient.post(`/api/v1/workers/${workerId}/run`, brandRequest);
  return data;
}

// Validate brand schema
export async function validateBrand(
  workerId: string,
  brandRequest: BrandRequest
): Promise<{ valid: boolean; errors?: string[] }> {
  try {
    const { data } = await apiClient.post(`/api/v1/workers/${workerId}/validate-brand`, brandRequest);
    return data;
  } catch (error: unknown) {
    const err = error as { response?: { data?: { errors?: string[] } } };
    return { valid: false, errors: err.response?.data?.errors || ['Validation failed'] };
  }
}

// List worker runs
export async function listWorkerRuns(
  workerId?: string,
  params?: { limit?: number; offset?: number; status?: string }
): Promise<WorkerRun[]> {
  try {
    const endpoint = workerId
      ? `/api/v1/workers/${workerId}/runs`
      : '/api/v1/workers/business-builder/runs';
    const { data } = await apiClient.get(endpoint, { params });
    return Array.isArray(data) ? data : data?.items || [];
  } catch {
    return [];
  }
}

// Get run events
export async function getRunEvents(
  workerId: string,
  runId: string
): Promise<RunEvent[]> {
  try {
    const { data } = await apiClient.get(`/api/v1/workers/${workerId}/runs/${runId}/events`);
    return Array.isArray(data) ? data : data?.events || [];
  } catch {
    return [];
  }
}

// Replay a worker run
export async function replayWorkerRun(
  workerId: string,
  runId: string
): Promise<{ new_run_id: string }> {
  const { data } = await apiClient.post(`/api/v1/workers/${workerId}/replay`, { run_id: runId });
  return data;
}

// Get worker health
export async function getWorkerHealth(): Promise<WorkerHealth> {
  try {
    const { data } = await apiClient.get('/api/v1/workers/health');
    return data;
  } catch {
    return {
      status: 'unhealthy',
      workers_available: 0,
      last_check: new Date().toISOString(),
    };
  }
}

// Get run details
export async function getWorkerRun(
  workerId: string,
  runId: string
): Promise<WorkerRun | null> {
  try {
    const { data } = await apiClient.get(`/api/v1/workers/${workerId}/runs/${runId}`);
    return data;
  } catch {
    return null;
  }
}

// Get SSE stream URL for real-time updates
export function getWorkerStreamUrl(workerId: string, runId: string): string {
  return `/api/v1/workers/${workerId}/stream/${runId}`;
}

// ============================================================================
// Phase-2.5: Real Actions
// ============================================================================

export interface RetryRunResponse {
  id: string;
  parent_run_id: string;
  status: string;
}

/**
 * Retry a completed or failed run - Phase-2.5
 *
 * Creates a new run linked to the original via parent_run_id.
 * This is the first REAL action graduating from simulation.
 */
export async function retryRun(runId: string): Promise<RetryRunResponse> {
  const { data } = await apiClient.post<RetryRunResponse>(
    `/api/v1/workers/business-builder/runs/${runId}/retry`
  );
  return data;
}
