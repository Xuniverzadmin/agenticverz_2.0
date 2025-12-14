// SBA (Strategy-Bound Agents) API Client
// M15.1.1 SBA Inspector UI

import apiClient from './client';
import type {
  SBAAgent,
  SBASchema,
  FulfillmentAggregated,
  SBAValidationResult,
  SpawnCheckResult,
  SBAFilters,
  SBAVersionInfo,
  VersionNegotiationResult,
  GroupByOption,
  FulfillmentHistoryEntry,
} from '@/types/sba';

// ============================================================================
// Agent Listing and Details
// ============================================================================

/**
 * List all agents with SBA status
 */
export async function getAgentsSBA(filters?: SBAFilters): Promise<{
  agents: SBAAgent[];
  count: number;
}> {
  try {
    const params = new URLSearchParams();
    if (filters?.agent_type) params.set('agent_type', filters.agent_type);
    if (filters?.sba_validated !== undefined && filters.sba_validated !== null) {
      params.set('sba_validated', String(filters.sba_validated));
    }

    const { data } = await apiClient.get(`/api/v1/sba?${params}`);
    return {
      agents: Array.isArray(data?.agents) ? data.agents : [],
      count: data?.count || 0,
    };
  } catch {
    return { agents: [], count: 0 };
  }
}

/**
 * Get single agent SBA details
 */
export async function getAgentSBA(agentId: string): Promise<SBAAgent | null> {
  try {
    const { data } = await apiClient.get(`/api/v1/sba/${encodeURIComponent(agentId)}`);
    return data;
  } catch {
    return null;
  }
}

// ============================================================================
// Fulfillment Data (for Heatmap)
// ============================================================================

/**
 * Get aggregated fulfillment data for heatmap visualization
 */
export async function getFulfillmentAggregated(
  groupBy: GroupByOption = 'domain',
  threshold?: number
): Promise<FulfillmentAggregated> {
  try {
    const params = new URLSearchParams({ group_by: groupBy });
    if (threshold !== undefined) params.set('threshold', String(threshold));

    const { data } = await apiClient.get(`/api/v1/sba/fulfillment/aggregated?${params}`);
    return {
      agents: Array.isArray(data?.agents) ? data.agents : [],
      groups: data?.groups || {},
      summary: data?.summary || {
        total_agents: 0,
        validated_count: 0,
        avg_fulfillment: 0,
        marketplace_ready_count: 0,
        by_fulfillment_range: {},
      },
    };
  } catch {
    return {
      agents: [],
      groups: {},
      summary: {
        total_agents: 0,
        validated_count: 0,
        avg_fulfillment: 0,
        marketplace_ready_count: 0,
        by_fulfillment_range: {},
      },
    };
  }
}

/**
 * Get fulfillment history for a single agent
 * (Extracted from agent SBA data)
 */
export async function getFulfillmentHistory(
  agentId: string,
  limit = 10
): Promise<FulfillmentHistoryEntry[]> {
  try {
    const agent = await getAgentSBA(agentId);
    if (!agent?.sba?.how_to_win?.fulfillment_history) {
      return [];
    }
    const history = agent.sba.how_to_win.fulfillment_history;
    return history.slice(-limit);
  } catch {
    return [];
  }
}

// ============================================================================
// Validation and Spawn Checks
// ============================================================================

/**
 * Validate SBA schema without registration
 */
export async function validateSBA(
  sba: Partial<SBASchema>,
  enforceGovernance = true
): Promise<SBAValidationResult> {
  try {
    const { data } = await apiClient.post('/api/v1/sba/validate', {
      sba,
      enforce_governance: enforceGovernance,
    });
    return data;
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } };
    return {
      valid: false,
      errors: [{ code: 'API_ERROR', field: 'sba', message: err.response?.data?.detail || 'Validation failed' }],
      warnings: [],
    };
  }
}

/**
 * Check if agent can spawn
 */
export async function checkSpawnEligibility(
  agentId: string,
  orchestrator?: string,
  autoGenerate = true
): Promise<SpawnCheckResult> {
  try {
    const params = new URLSearchParams({ agent_id: agentId });
    if (orchestrator) params.set('orchestrator', orchestrator);
    params.set('auto_generate', String(autoGenerate));

    const { data } = await apiClient.post(`/api/v1/sba/check-spawn?${params}`);
    return data;
  } catch (error: unknown) {
    const err = error as { response?: { data?: { detail?: string } } };
    return {
      agent_id: agentId,
      spawn_allowed: false,
      error: err.response?.data?.detail || 'Spawn check failed',
    };
  }
}

// ============================================================================
// Registration and Generation
// ============================================================================

/**
 * Register agent with SBA
 */
export async function registerAgentSBA(params: {
  agent_id: string;
  sba: SBASchema;
  agent_name?: string;
  description?: string;
  agent_type?: string;
  capabilities?: Record<string, unknown>;
  config?: Record<string, unknown>;
}): Promise<{ registered: boolean; agent_id: string; sba_version?: string; sba_validated?: boolean }> {
  const { data } = await apiClient.post('/api/v1/sba/register', params);
  return data;
}

/**
 * Auto-generate SBA for an agent
 */
export async function generateSBA(params: {
  agent_id: string;
  capabilities?: Record<string, unknown>;
  config?: Record<string, unknown>;
  orchestrator?: string;
}): Promise<SBASchema | null> {
  try {
    const { data } = await apiClient.post('/api/v1/sba/generate', params);
    return data?.sba || null;
  } catch {
    return null;
  }
}

// ============================================================================
// Version Negotiation
// ============================================================================

/**
 * Get SBA version info
 */
export async function getSBAVersionInfo(): Promise<SBAVersionInfo> {
  try {
    const { data } = await apiClient.get('/api/v1/sba/version');
    return data;
  } catch {
    return {
      current: '1.0',
      supported: ['1.0'],
      min_supported: '1.0',
      max_supported: '1.0',
      deprecated: [],
    };
  }
}

/**
 * Negotiate SBA version
 */
export async function negotiateSBAVersion(requestedVersion: string): Promise<VersionNegotiationResult> {
  try {
    const params = new URLSearchParams({ requested_version: requestedVersion });
    const { data } = await apiClient.post(`/api/v1/sba/version/negotiate?${params}`);
    return data;
  } catch {
    return {
      requested: requestedVersion,
      negotiated: null,
      supported: false,
      deprecated: false,
      message: 'Version negotiation failed',
    };
  }
}

// ============================================================================
// M16 Activity APIs
// ============================================================================

export interface WorkerMetrics {
  id: string;
  name?: string;
  cost: 'low' | 'medium' | 'high';
  risk: number;
  budget_used: number;
}

export interface ActivityCostsResponse {
  agent_id: string;
  workers: WorkerMetrics[];
  total_cost_level: string;
  total_risk: number;
  timestamp: string;
}

export interface SpendingDataResponse {
  agent_id: string;
  actual: number[];
  projected: number[];
  budget_limit: number;
  anomalies: Array<{ index: number; reason: string }>;
  period: string;
  timestamp: string;
}

export interface RetryEntry {
  time: string;
  reason: string;
  attempt: number;
  outcome: 'success' | 'failure' | 'pending';
  risk_change?: number;
}

export interface ActivityRetriesResponse {
  agent_id: string;
  retries: RetryEntry[];
  total_retries: number;
  success_rate: number;
  timestamp: string;
}

export interface BlockerEntry {
  type: 'dependency' | 'api' | 'tool' | 'circular' | 'budget';
  message: string;
  since: string;
  action?: string;
  details?: string;
}

export interface ActivityBlockersResponse {
  agent_id: string;
  blockers: BlockerEntry[];
  blocked: boolean;
  timestamp: string;
}

/**
 * Get worker cost and risk metrics for an agent
 */
export async function getActivityCosts(agentId: string): Promise<ActivityCostsResponse> {
  try {
    const { data } = await apiClient.get(`/api/v1/agents/${encodeURIComponent(agentId)}/activity/costs`);
    return data;
  } catch {
    return {
      agent_id: agentId,
      workers: [],
      total_cost_level: 'low',
      total_risk: 0,
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Get spending data for budget burn chart
 */
export async function getActivitySpending(
  agentId: string,
  period: '1h' | '6h' | '24h' | '7d' = '24h'
): Promise<SpendingDataResponse> {
  try {
    const params = new URLSearchParams({ period });
    const { data } = await apiClient.get(
      `/api/v1/agents/${encodeURIComponent(agentId)}/activity/spending?${params}`
    );
    return data;
  } catch {
    return {
      agent_id: agentId,
      actual: [],
      projected: [],
      budget_limit: 0,
      anomalies: [],
      period,
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Get retry log for an agent
 */
export async function getActivityRetries(
  agentId: string,
  limit = 50
): Promise<ActivityRetriesResponse> {
  try {
    const params = new URLSearchParams({ limit: String(limit) });
    const { data } = await apiClient.get(
      `/api/v1/agents/${encodeURIComponent(agentId)}/activity/retries?${params}`
    );
    return data;
  } catch {
    return {
      agent_id: agentId,
      retries: [],
      total_retries: 0,
      success_rate: 1,
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Get current blockers for an agent
 */
export async function getActivityBlockers(agentId: string): Promise<ActivityBlockersResponse> {
  try {
    const { data } = await apiClient.get(
      `/api/v1/agents/${encodeURIComponent(agentId)}/activity/blockers`
    );
    return data;
  } catch {
    return {
      agent_id: agentId,
      blockers: [],
      blocked: false,
      timestamp: new Date().toISOString(),
    };
  }
}

// ============================================================================
// M16 Health API
// ============================================================================

export interface HealthCheckItem {
  severity: 'error' | 'warning' | 'info';
  code: string;
  title: string;
  message: string;
  action?: string;
}

export interface HealthCheckResponse {
  agent_id: string;
  healthy: boolean;
  errors: HealthCheckItem[];
  warnings: HealthCheckItem[];
  suggestions: HealthCheckItem[];
  checked_at: string;
}

/**
 * Run comprehensive health check for an agent
 */
export async function checkAgentHealth(agentId: string): Promise<HealthCheckResponse> {
  try {
    const { data } = await apiClient.post(
      `/api/v1/agents/${encodeURIComponent(agentId)}/health/check`
    );
    return data;
  } catch {
    return {
      agent_id: agentId,
      healthy: false,
      errors: [{
        severity: 'error',
        code: 'API_ERROR',
        title: 'Health Check Failed',
        message: 'Could not reach health check endpoint',
        action: 'Try again',
      }],
      warnings: [],
      suggestions: [],
      checked_at: new Date().toISOString(),
    };
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get unique domains from agents list
 */
export function extractDomains(agents: Array<{ domain?: string }>): string[] {
  const domains = new Set<string>();
  agents.forEach((agent) => {
    if (agent.domain && agent.domain !== 'unknown') {
      domains.add(agent.domain);
    }
  });
  return Array.from(domains).sort();
}

/**
 * Get fulfillment color class based on value
 */
export function getFulfillmentColorClass(value: number): string {
  if (value < 0.2) return 'bg-red-600';
  if (value < 0.4) return 'bg-orange-500';
  if (value < 0.6) return 'bg-yellow-500';
  if (value < 0.8) return 'bg-lime-500';
  return 'bg-green-500';
}

/**
 * Get fulfillment text color class based on value
 */
export function getFulfillmentTextColorClass(value: number): string {
  if (value < 0.2) return 'text-red-600';
  if (value < 0.4) return 'text-orange-500';
  if (value < 0.6) return 'text-yellow-600';
  if (value < 0.8) return 'text-lime-600';
  return 'text-green-600';
}
