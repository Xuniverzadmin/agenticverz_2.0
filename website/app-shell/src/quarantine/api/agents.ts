/**
 * @audience customer
 *
 * Agents API Client
 * Customer agent management
 */
import apiClient from './client';
import type { Agent, AgentFilters, PaginatedResponse } from '@/types/agent';

export async function getAgents(filters?: AgentFilters): Promise<PaginatedResponse<Agent>> {
  const params = new URLSearchParams();
  if (filters?.status) params.set('status', filters.status);
  if (filters?.type) params.set('type', filters.type);
  if (filters?.search) params.set('search', filters.search);
  if (filters?.page) params.set('page', String(filters.page));
  if (filters?.limit) params.set('limit', String(filters.limit));

  try {
    const { data } = await apiClient.get(`/agents?${params}`);
    // Normalize response - backend might return array or paginated object
    if (Array.isArray(data)) {
      return { items: data, total: data.length, page: 1, limit: 100 };
    }
    return data;
  } catch {
    return { items: [], total: 0, page: 1, limit: 100 };
  }
}

export async function getAgent(agentId: string): Promise<Agent> {
  const { data } = await apiClient.get(`/agents/${agentId}`);
  return data;
}

export async function getAgentStats() {
  try {
    // Get agents and compute stats
    const agents = await getAgents({ limit: 1000 });
    const items = agents.items || [];
    return {
      total: items.length,
      active: items.filter((a: Agent) => a.status === 'active').length,
      idle: items.filter((a: Agent) => a.status === 'idle').length,
      stale: items.filter((a: Agent) => a.status === 'stale').length,
      orchestrators: items.filter((a: Agent) => a.type === 'orchestrator').length,
      workers: items.filter((a: Agent) => a.type === 'worker').length,
    };
  } catch {
    return { total: 0, active: 0, idle: 0, stale: 0, orchestrators: 0, workers: 0 };
  }
}

export async function registerAgent(payload: {
  agent_name: string;
  agent_type: 'orchestrator' | 'worker';
  capabilities: string[];
}): Promise<Agent> {
  const { data } = await apiClient.post('/agents', payload);
  return data;
}

export async function deregisterAgent(agentId: string): Promise<void> {
  await apiClient.delete(`/agents/${agentId}`);
}

export async function sendHeartbeat(agentId: string): Promise<void> {
  await apiClient.post(`/agents/${agentId}/heartbeat`);
}

export async function getAgentRuns(agentId: string) {
  const { data } = await apiClient.get(`/agents/${agentId}/runs`);
  return data;
}
