/**
 * @audience shared
 *
 * Metrics API Client
 * System metrics and health summaries
 */
import apiClient from './client';

export async function getMetricsSummary() {
  try {
    // Get health and capabilities to build a summary
    const [health, capabilities] = await Promise.all([
      getHealthStatus(),
      getCapabilities()
    ]);

    return {
      jobs: { total: 0, running: 0, completed: 0, failed: 0 },
      agents: { total: 0, active: 0 },
      credits: capabilities?.budget || { total_cents: 0, remaining_cents: 0 },
      health: health?.status || 'unknown',
    };
  } catch {
    return {
      jobs: { total: 0, running: 0, completed: 0, failed: 0 },
      agents: { total: 0, active: 0 },
      credits: { total_cents: 0, remaining_cents: 0 },
      health: 'unknown',
    };
  }
}

export async function getCapabilities() {
  const { data } = await apiClient.get('/api/v1/runtime/capabilities');
  return data;
}

export async function getSkills() {
  const { data } = await apiClient.get('/api/v1/runtime/skills');
  return data;
}

export async function getSkill(skillId: string) {
  const { data } = await apiClient.get(`/api/v1/runtime/skills/${skillId}`);
  return data;
}

export async function getThroughput() {
  // Return mock data - actual endpoint may not exist
  return {
    data: [],
    labels: [],
  };
}

export async function getInvokeLatency() {
  // Return mock data
  return {
    p50: 0,
    p90: 0,
    p99: 0,
  };
}

export async function getHealthStatus() {
  try {
    const { data } = await apiClient.get('/health');
    return data;
  } catch {
    return { status: 'unknown' };
  }
}

export async function getHealthAdapters() {
  try {
    const { data } = await apiClient.get('/health/adapters');
    return data;
  } catch {
    return {};
  }
}

export async function getHealthSkills() {
  try {
    const { data } = await apiClient.get('/health/skills');
    return data;
  } catch {
    return {};
  }
}

export async function getActivity(limit = 20) {
  try {
    // Use status history as activity feed
    const { data } = await apiClient.get('/api/v1/status_history', { params: { limit } });
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export async function getFailures() {
  try {
    const { data } = await apiClient.get('/api/v1/failures');
    return data;
  } catch {
    return { items: [], total: 0 };
  }
}

export async function getFailureStats() {
  try {
    const { data } = await apiClient.get('/api/v1/failures/stats');
    return data;
  } catch {
    return {};
  }
}

export async function getRecoveryCandidates() {
  try {
    const { data } = await apiClient.get('/api/v1/recovery/candidates');
    return data;
  } catch {
    return [];
  }
}

export async function getRecoveryStats() {
  try {
    const { data } = await apiClient.get('/api/v1/recovery/stats');
    return data;
  } catch {
    return {};
  }
}
