/**
 * Guard API Client
 *
 * Client for the AI Budget & Incident Guard system.
 * Handles all guard-related API calls for the Customer Console.
 */

import { apiClient } from './client';

// ============== TYPES ==============

export interface GuardStatus {
  is_frozen: boolean;
  frozen_at: string | null;
  frozen_by: string | null;
  incidents_blocked_24h: number;
  active_guardrails: string[];
  last_incident_time: string | null;
}

export interface TodaySnapshot {
  requests_today: number;
  spend_today_cents: number;
  incidents_prevented: number;
  last_incident_time: string | null;
  cost_avoided_cents: number;
}

export interface Incident {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'acknowledged' | 'resolved';
  trigger_type: string;
  trigger_value: string;
  action_taken: string;
  cost_avoided_cents: number;
  calls_affected: number;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
}

export interface IncidentEvent {
  id: string;
  event_type: string;
  description: string;
  created_at: string;
  data?: Record<string, any>;
}

export interface IncidentDetail {
  incident: Incident;
  timeline: IncidentEvent[];
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  status: 'active' | 'frozen' | 'revoked';
  created_at: string;
  last_seen_at: string | null;
  requests_today: number;
  spend_today_cents: number;
}

export interface GuardrailConfig {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  threshold_type: 'cost' | 'rate' | 'count' | 'pattern';
  threshold_value: number;
  threshold_unit: string;
  action_on_trigger: string;
}

export interface TenantSettings {
  tenant_id: string;
  tenant_name: string;
  plan: 'starter' | 'pro' | 'enterprise';
  guardrails: GuardrailConfig[];
  budget_limit_cents: number;
  budget_period: 'daily' | 'weekly' | 'monthly';
  kill_switch_enabled: boolean;
  kill_switch_auto_trigger: boolean;
  auto_trigger_threshold_cents: number;
  notification_email: string;
  notification_slack_webhook: string | null;
}

export interface ReplayResult {
  call_id: string;
  original: {
    timestamp: string;
    model_id: string;
    policy_decisions: PolicyDecision[];
    response_hash: string;
    tokens_used: number;
    cost_cents: number;
  };
  replay: {
    timestamp: string;
    model_id: string;
    policy_decisions: PolicyDecision[];
    response_hash: string;
    tokens_used: number;
    cost_cents: number;
  };
  match_level: 'exact' | 'logical' | 'semantic' | 'mismatch';
  policy_match: boolean;
  model_drift_detected: boolean;
  details: Record<string, any>;
}

export interface PolicyDecision {
  guardrail_id: string;
  guardrail_name: string;
  passed: boolean;
  action: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ============== API FUNCTIONS ==============

export const guardApi = {
  // Status
  getStatus: async (): Promise<GuardStatus> => {
    const response = await apiClient.get('/guard/status');
    return response.data;
  },

  getTodaySnapshot: async (): Promise<TodaySnapshot> => {
    const response = await apiClient.get('/guard/snapshot/today');
    return response.data;
  },

  // Kill Switch
  activateKillSwitch: async (): Promise<void> => {
    await apiClient.post('/guard/killswitch/activate');
  },

  deactivateKillSwitch: async (): Promise<void> => {
    await apiClient.post('/guard/killswitch/deactivate');
  },

  // Incidents
  getIncidents: async (params?: {
    limit?: number;
    offset?: number;
    status?: string;
    severity?: string;
  }): Promise<PaginatedResponse<Incident>> => {
    const response = await apiClient.get('/guard/incidents', { params });
    return response.data;
  },

  getIncidentDetail: async (incidentId: string): Promise<IncidentDetail> => {
    const response = await apiClient.get(`/guard/incidents/${incidentId}`);
    return response.data;
  },

  acknowledgeIncident: async (incidentId: string): Promise<void> => {
    await apiClient.post(`/guard/incidents/${incidentId}/acknowledge`);
  },

  resolveIncident: async (incidentId: string): Promise<void> => {
    await apiClient.post(`/guard/incidents/${incidentId}/resolve`);
  },

  // Replay
  replayCall: async (callId: string): Promise<ReplayResult> => {
    const response = await apiClient.post(`/guard/replay/${callId}`);
    return response.data;
  },

  // API Keys
  getApiKeys: async (): Promise<PaginatedResponse<ApiKey>> => {
    const response = await apiClient.get('/guard/keys');
    return response.data;
  },

  freezeApiKey: async (keyId: string): Promise<void> => {
    await apiClient.post(`/guard/keys/${keyId}/freeze`);
  },

  unfreezeApiKey: async (keyId: string): Promise<void> => {
    await apiClient.post(`/guard/keys/${keyId}/unfreeze`);
  },

  // Settings (read-only for customers)
  getSettings: async (): Promise<TenantSettings> => {
    const response = await apiClient.get('/guard/settings');
    return response.data;
  },
};

export default guardApi;
