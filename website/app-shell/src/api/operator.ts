/**
 * @audience founder
 *
 * Operator API Client
 *
 * Client for the Operator Console.
 * Handles all operator-level API calls for system administration.
 */

import { apiClient } from './client';

// ============== TYPES ==============

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'critical';
  total_tenants: number;
  active_tenants_24h: number;
  frozen_tenants: number;
  total_requests_24h: number;
  total_spend_24h_cents: number;
  active_incidents: number;
  model_drift_alerts: number;
}

export interface TopTenant {
  tenant_id: string;
  tenant_name: string;
  metric_value: number;
  metric_label: string;
}

export interface TenantProfile {
  tenant_id: string;
  tenant_name: string;
  email: string;
  plan: 'starter' | 'pro' | 'enterprise';
  created_at: string;
  status: 'active' | 'frozen' | 'suspended';
  frozen_at: string | null;
  frozen_by: string | null;
  frozen_reason: string | null;
}

export interface TenantMetrics {
  requests_24h: number;
  requests_7d: number;
  spend_24h_cents: number;
  spend_7d_cents: number;
  error_rate_24h: number;
  avg_latency_ms: number;
  incidents_24h: number;
  incidents_7d: number;
  cost_avoided_7d_cents: number;
}

export interface TenantGuardrail {
  id: string;
  name: string;
  enabled: boolean;
  threshold_value: number;
  threshold_unit: string;
  triggers_24h: number;
}

export interface Incident {
  id: string;
  tenant_id: string;
  tenant_name: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'acknowledged' | 'resolved';
  trigger_type: string;
  action_taken: string;
  calls_affected: number;
  cost_avoided_cents: number;
  started_at: string;
  ended_at: string | null;
}

export interface PolicyEnforcement {
  id: string;
  call_id: string;
  tenant_id: string;
  tenant_name: string;
  guardrail_id: string;
  guardrail_name: string;
  passed: boolean;
  action_taken: string | null;
  reason: string;
  confidence: number;
  latency_ms: number;
  created_at: string;
  request_context: {
    model: string;
    tokens_estimated: number;
    cost_estimated_cents: number;
  };
}

export interface ReplayResult {
  call_id: string;
  tenant_id: string;
  tenant_name: string;
  original: CallSnapshot;
  replay: CallSnapshot;
  match_level: 'exact' | 'logical' | 'semantic' | 'mismatch';
  policy_match: boolean;
  model_drift_detected: boolean;
  content_match: boolean;
  details: Record<string, any>;
}

export interface CallSnapshot {
  timestamp: string;
  model_id: string;
  model_version: string | null;
  temperature: number | null;
  policy_decisions: PolicyDecision[];
  response_hash: string;
  tokens_used: number;
  cost_cents: number;
  latency_ms: number;
}

export interface PolicyDecision {
  guardrail_id: string;
  guardrail_name: string;
  passed: boolean;
  action: string | null;
  reason: string;
  confidence: number;
}

export interface BatchReplayResult {
  total: number;
  completed: number;
  exact_matches: number;
  logical_matches: number;
  semantic_matches: number;
  mismatches: number;
  model_drift_count: number;
  policy_drift_count: number;
  failures: {
    call_id: string;
    error: string;
  }[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ============== API FUNCTIONS ==============

export const operatorApi = {
  // System Status
  getSystemStatus: async (): Promise<SystemStatus> => {
    const response = await apiClient.get('/operator/status');
    return response.data;
  },

  getTopTenants: async (metric: 'spend' | 'incidents', limit: number): Promise<PaginatedResponse<TopTenant>> => {
    const response = await apiClient.get('/operator/tenants/top', {
      params: { metric, limit },
    });
    return response.data;
  },

  getRecentIncidents: async (limit: number): Promise<PaginatedResponse<Incident>> => {
    const response = await apiClient.get('/operator/incidents/recent', {
      params: { limit },
    });
    return response.data;
  },

  // Incident Stream
  getIncidentStream: async (filters: {
    severity: string | null;
    status: string | null;
    tenant_id: string | null;
  }): Promise<PaginatedResponse<Incident>> => {
    const response = await apiClient.get('/operator/incidents/stream', {
      params: filters,
    });
    return response.data;
  },

  acknowledgeIncident: async (incidentId: string): Promise<void> => {
    await apiClient.post(`/operator/incidents/${incidentId}/acknowledge`);
  },

  resolveIncident: async (incidentId: string): Promise<void> => {
    await apiClient.post(`/operator/incidents/${incidentId}/resolve`);
  },

  // Tenant Management
  getTenantProfile: async (tenantId: string): Promise<TenantProfile> => {
    const response = await apiClient.get(`/operator/tenants/${tenantId}`);
    return response.data;
  },

  getTenantMetrics: async (tenantId: string): Promise<TenantMetrics> => {
    const response = await apiClient.get(`/operator/tenants/${tenantId}/metrics`);
    return response.data;
  },

  getTenantGuardrails: async (tenantId: string): Promise<PaginatedResponse<TenantGuardrail>> => {
    const response = await apiClient.get(`/operator/tenants/${tenantId}/guardrails`);
    return response.data;
  },

  getTenantIncidents: async (tenantId: string, limit: number): Promise<PaginatedResponse<Incident>> => {
    const response = await apiClient.get(`/operator/tenants/${tenantId}/incidents`, {
      params: { limit },
    });
    return response.data;
  },

  getTenantApiKeys: async (tenantId: string): Promise<PaginatedResponse<{ id: string; name: string; prefix: string; status: string; requests_24h: number }>> => {
    const response = await apiClient.get(`/operator/tenants/${tenantId}/keys`);
    return response.data;
  },

  freezeTenant: async (tenantId: string, reason: string): Promise<void> => {
    await apiClient.post(`/operator/tenants/${tenantId}/freeze`, { reason });
  },

  unfreezeTenant: async (tenantId: string): Promise<void> => {
    await apiClient.post(`/operator/tenants/${tenantId}/unfreeze`);
  },

  // Policy Audit
  getPolicyEnforcementLog: async (params: {
    guardrail_id: string | null;
    action: string | null;
    tenant_id: string | null;
    passed: boolean | null;
    date_from: string | null;
    date_to: string | null;
    page: number;
    page_size: number;
  }): Promise<PaginatedResponse<PolicyEnforcement>> => {
    const response = await apiClient.get('/operator/audit/policy', { params });
    return response.data;
  },

  getGuardrailTypes: async (): Promise<PaginatedResponse<{ id: string; name: string }>> => {
    const response = await apiClient.get('/operator/guardrails');
    return response.data;
  },

  exportAuditLog: async (filters: {
    guardrail_id: string | null;
    action: string | null;
    tenant_id: string | null;
    passed: boolean | null;
    date_from: string | null;
    date_to: string | null;
  }): Promise<Blob> => {
    const response = await apiClient.get('/operator/audit/policy/export', {
      params: filters,
      responseType: 'blob',
    });
    return response.data;
  },

  // Replay Lab
  replayCall: async (callId: string): Promise<ReplayResult> => {
    const response = await apiClient.post(`/operator/replay/${callId}`);
    return response.data;
  },

  batchReplay: async (config: {
    tenant_id: string;
    sample_size: number;
    time_range_hours: number;
  }): Promise<BatchReplayResult> => {
    const response = await apiClient.post('/operator/replay/batch', config);
    return response.data;
  },
};

export default operatorApi;
