/**
 * @audience shared
 *
 * Traces API Client
 * Execution trace viewing (used by both customer and founder)
 */
import apiClient from './client';

export interface Trace {
  run_id: string;
  root_hash?: string;
  status: string;
  created_at: string;
  completed_at?: string;
  steps?: Array<{
    step_id: string;
    skill_id: string;
    status: string;
    input_hash?: string;
    output_hash?: string;
  }>;
}

// List Traces
export async function getTraces(params?: {
  limit?: number;
  offset?: number;
  status?: string;
}) {
  try {
    const { data } = await apiClient.get('/api/v1/traces', { params });
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
