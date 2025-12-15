import apiClient from './client';
import type { BlackboardEntry, PaginatedResponse } from '@/types/blackboard';

export async function getBlackboardKeys(params?: {
  pattern?: string;
  page?: number;
  limit?: number;
}): Promise<PaginatedResponse<BlackboardEntry>> {
  const { data } = await apiClient.get('/api/v1/blackboard', { params });
  return data;
}

export async function getBlackboardStats() {
  const { data } = await apiClient.get('/api/v1/blackboard/stats');
  return data;
}

export async function getBlackboardKey(key: string): Promise<BlackboardEntry> {
  const { data } = await apiClient.get(`/api/v1/blackboard/${encodeURIComponent(key)}`);
  return data;
}

export async function setBlackboardKey(
  key: string,
  value: unknown,
  ttl_seconds?: number
): Promise<BlackboardEntry> {
  const { data } = await apiClient.put(`/api/v1/blackboard/${encodeURIComponent(key)}`, {
    value,
    ttl_seconds,
  });
  return data;
}

export async function incrementBlackboardKey(
  key: string,
  amount: number
): Promise<{ new_value: number }> {
  const { data } = await apiClient.post(`/api/v1/blackboard/${encodeURIComponent(key)}/increment`, {
    amount,
  });
  return data;
}

export async function deleteBlackboardKey(key: string): Promise<void> {
  await apiClient.delete(`/api/v1/blackboard/${encodeURIComponent(key)}`);
}

export async function lockBlackboardKey(
  key: string,
  ttl_seconds: number,
  wait_seconds?: number
): Promise<{ success: boolean; lock_id: string; expires_at: string }> {
  const { data } = await apiClient.post(`/api/v1/blackboard/${encodeURIComponent(key)}/lock`, {
    ttl_seconds,
    wait_seconds,
  });
  return data;
}

export async function unlockBlackboardKey(key: string, lock_id: string): Promise<void> {
  await apiClient.post(`/api/v1/blackboard/${encodeURIComponent(key)}/unlock`, { lock_id });
}
