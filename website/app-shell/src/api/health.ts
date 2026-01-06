/**
 * @audience shared
 *
 * Health API Client
 * System health and status checks
 */
import apiClient from './client';

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  timestamp: string;
  service: string;
  version: string;
  details?: Record<string, unknown>;
}

export interface AdapterStatus {
  [adapter: string]: {
    status: string;
    latency_ms?: number;
    last_check?: string;
  };
}

// Main Health Check
export async function getHealth(): Promise<HealthStatus> {
  try {
    const { data } = await apiClient.get('/health');
    return data;
  } catch {
    return { status: 'unknown', timestamp: new Date().toISOString(), service: 'aos-backend', version: 'unknown' };
  }
}

// Readiness Check
export async function getReadiness() {
  try {
    const { data } = await apiClient.get('/health/ready');
    return data;
  } catch {
    return { ready: false };
  }
}

// Adapter Status
export async function getAdapterStatus(): Promise<AdapterStatus> {
  try {
    const { data } = await apiClient.get('/health/adapters');
    return data;
  } catch {
    return {};
  }
}

// Skills Status
export async function getSkillsStatus() {
  try {
    const { data } = await apiClient.get('/health/skills');
    return data;
  } catch {
    return {};
  }
}

// Determinism Status
export async function getDeterminismStatus() {
  try {
    const { data } = await apiClient.get('/health/determinism');
    return data;
  } catch {
    return { deterministic: true, last_check: null, violations: [] };
  }
}

// Worker Pool Health
export async function getWorkerPoolHealth() {
  try {
    const { data } = await apiClient.get('/healthz/worker_pool');
    return data;
  } catch {
    return { healthy: false, workers: 0 };
  }
}

// Version Info
export async function getVersion() {
  try {
    const { data } = await apiClient.get('/version');
    return data;
  } catch {
    return { service: 'unknown', version: 'unknown' };
  }
}
