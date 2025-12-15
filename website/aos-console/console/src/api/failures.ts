import apiClient from './client';

export interface Failure {
  id: string;
  run_id: string;
  step_id?: string;
  error_type: string;
  error_message: string;
  stack_trace?: string;
  context?: Record<string, unknown>;
  recovery_status?: 'pending' | 'suggested' | 'approved' | 'recovered' | 'dismissed';
  created_at: string;
}

export interface FailureStats {
  total: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  recovery_rate: number;
}

// List Failures
export async function getFailures(params?: {
  limit?: number;
  offset?: number;
  status?: string;
  error_type?: string;
}) {
  try {
    const { data } = await apiClient.get('/api/v1/failures', { params });
    return Array.isArray(data) ? { items: data, total: data.length } : data;
  } catch {
    return { items: [], total: 0 };
  }
}

// Get Failure Stats
export async function getFailureStats(): Promise<FailureStats> {
  try {
    const { data } = await apiClient.get('/api/v1/failures/stats');
    return data;
  } catch {
    return { total: 0, by_type: {}, by_status: {}, recovery_rate: 0 };
  }
}

// List Unrecovered Failures
export async function getUnrecoveredFailures() {
  try {
    const { data } = await apiClient.get('/api/v1/failures/unrecovered');
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

// Get Single Failure
export async function getFailure(failureId: string): Promise<Failure | null> {
  try {
    const { data } = await apiClient.get(`/api/v1/failures/${failureId}`);
    return data;
  } catch {
    return null;
  }
}

// Update Recovery Status
export async function updateRecoveryStatus(failureId: string, status: string) {
  const { data } = await apiClient.patch(`/api/v1/failures/${failureId}/recovery`, { status });
  return data;
}
