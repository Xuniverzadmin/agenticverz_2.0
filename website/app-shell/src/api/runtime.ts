/**
 * @audience shared
 *
 * Runtime API Client
 * Agent capabilities and runtime queries
 */
import apiClient from './client';

// Runtime Capabilities
export async function getCapabilities() {
  const { data } = await apiClient.get('/api/v1/runtime/capabilities');
  return data;
}

// Simulation
export async function simulate(plan: {
  plan: Array<{ skill: string; params?: Record<string, unknown> }>;
  budget_cents?: number;
}) {
  const { data } = await apiClient.post('/api/v1/runtime/simulate', plan);
  return data;
}

// Query Runtime State
export async function queryRuntime(query: {
  query_type: string;
  params?: Record<string, unknown>;
}) {
  const { data } = await apiClient.post('/api/v1/runtime/query', query);
  return data;
}

// Replay a Run
export async function replayRun(runId: string) {
  const { data } = await apiClient.post(`/api/v1/runtime/replay/${runId}`);
  return data;
}

// Skills
export async function getSkills() {
  const { data } = await apiClient.get('/api/v1/runtime/skills');
  return Array.isArray(data) ? data : data?.skills || [];
}

export async function getSkill(skillId: string) {
  const { data } = await apiClient.get(`/api/v1/runtime/skills/${skillId}`);
  return data;
}

// Resource Contracts
export async function getResourceContract(resourceId: string) {
  const { data } = await apiClient.get(`/api/v1/runtime/resource-contract/${resourceId}`);
  return data;
}
