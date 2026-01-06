/**
 * @audience founder
 *
 * Recovery API Client
 * Handles recovery suggestions and failure remediation
 */
import apiClient from './client';

export interface RecoveryCandidate {
  id: string;
  failure_id: string;
  suggested_action: string;
  confidence: number;
  reasoning?: string;
  estimated_cost_cents?: number;
  created_at: string;
  status: 'pending' | 'approved' | 'rejected' | 'executed';
}

export interface RecoveryStats {
  total_candidates: number;
  approved: number;
  rejected: number;
  executed: number;
  success_rate: number;
}

// List Recovery Candidates
export async function getCandidates(params?: {
  limit?: number;
  status?: string;
}) {
  try {
    const { data } = await apiClient.get('/api/v1/recovery/candidates', { params });
    return Array.isArray(data) ? data : data?.items || [];
  } catch {
    return [];
  }
}

// Get Single Candidate
export async function getCandidate(candidateId: string): Promise<RecoveryCandidate | null> {
  try {
    const { data } = await apiClient.get(`/api/v1/recovery/candidates/${candidateId}`);
    return data;
  } catch {
    return null;
  }
}

// Delete Candidate
export async function deleteCandidate(candidateId: string) {
  await apiClient.delete(`/api/v1/recovery/candidates/${candidateId}`);
}

// Get Recovery Stats
export async function getRecoveryStats(): Promise<RecoveryStats> {
  try {
    const { data } = await apiClient.get('/api/v1/recovery/stats');
    return data;
  } catch {
    return { total_candidates: 0, approved: 0, rejected: 0, executed: 0, success_rate: 0 };
  }
}

// Suggest Recovery
export async function suggestRecovery(failureId: string, context?: Record<string, unknown>) {
  const { data } = await apiClient.post('/api/v1/recovery/suggest', {
    failure_id: failureId,
    context,
  });
  return data;
}

// Approve Candidate
export async function approveCandidate(candidateId: string) {
  const { data } = await apiClient.post('/api/v1/recovery/approve', {
    candidate_id: candidateId,
  });
  return data;
}
