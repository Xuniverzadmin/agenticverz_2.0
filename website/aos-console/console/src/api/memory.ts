import apiClient from './client';

export interface MemoryPin {
  key: string;
  value: unknown;
  ttl_seconds?: number;
  created_at: string;
  expires_at?: string;
  metadata?: Record<string, unknown>;
}

// List Pins
export async function getPins(params?: {
  prefix?: string;
  limit?: number;
}) {
  try {
    const { data } = await apiClient.get('/api/v1/memory/pins', { params });
    return Array.isArray(data) ? data : data?.items || [];
  } catch {
    return [];
  }
}

// Get Pin
export async function getPin(key: string): Promise<MemoryPin | null> {
  try {
    const { data } = await apiClient.get(`/api/v1/memory/pins/${encodeURIComponent(key)}`);
    return data;
  } catch {
    return null;
  }
}

// Create/Upsert Pin
export async function setPin(key: string, value: unknown, ttlSeconds?: number) {
  const { data } = await apiClient.post('/api/v1/memory/pins', {
    key,
    value,
    ttl_seconds: ttlSeconds,
  });
  return data;
}

// Delete Pin
export async function deletePin(key: string) {
  await apiClient.delete(`/api/v1/memory/pins/${encodeURIComponent(key)}`);
}

// Cleanup Expired Pins
export async function cleanupPins() {
  const { data } = await apiClient.post('/api/v1/memory/pins/cleanup');
  return data;
}
