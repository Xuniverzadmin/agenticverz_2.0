/**
 * @audience founder
 *
 * Ops Console API Client
 *
 * Endpoints for Founder/Ops Console:
 * - GET /ops/pulse - System health and activity metrics
 * - GET /ops/infra - Infrastructure metrics (DB, Redis, connections)
 * - GET /ops/customers - All customer segments with stickiness
 * - GET /ops/customers/at-risk - Customers requiring attention
 * - GET /ops/playbooks - Founder playbooks configuration
 */

import { apiClient } from './client';

// =============================================================================
// Types
// =============================================================================

export interface SystemPulse {
  system_state: 'healthy' | 'degraded' | 'critical';
  active_tenants_24h: number;
  incidents_created_24h: number;
  replays_executed_24h: number;
  alerts_triggered_24h: number;
  cost_today_usd: number;
  latency_p95_ms: number;
  error_rate_24h: number;
  last_incident_at: string | null;
  uptime_percent: number;
}

export interface InfraMetrics {
  db_storage_used_gb: number;
  db_storage_limit_gb: number;
  db_connections_current: number;
  db_connections_max: number;
  redis_memory_used_mb: number;
  redis_memory_limit_mb: number;
  redis_connected_clients: number;
  cpu_percent: number;
  memory_percent: number;
}

export interface CustomerSegment {
  tenant_id: string;
  tenant_name: string | null;
  first_action: string | null;
  first_action_at: string | null;
  inferred_buyer_type: string | null;
  current_stickiness: number;
  stickiness_7d: number;
  stickiness_30d: number;
  stickiness_delta: number;
  peak_stickiness: number;
  stickiness_trend: 'rising' | 'stable' | 'falling' | 'unknown';
  last_api_call: string | null;
  last_investigation: string | null;
  is_silent_churn: boolean;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_reason: string | null;
  friction_score: number;
  last_friction_event: string | null;
}

export interface FounderIntervention {
  intervention_type: 'call' | 'email' | 'slack' | 'feature_flag' | 'policy_adjust';
  priority: 'immediate' | 'today' | 'this_week';
  suggested_action: string;
  context: string;
  expected_outcome: string;
  triggering_signals: string[];
}

export interface CustomerAtRisk {
  tenant_id: string;
  tenant_name: string | null;
  risk_level: 'medium' | 'high' | 'critical';
  risk_signal_strength: number;
  primary_risk_reason: string;
  days_since_last_investigation: number | null;
  stickiness_7d: number;
  stickiness_30d: number;
  stickiness_delta: number;
  friction_weighted_score: number;
  top_friction_type: string | null;
  friction_count_14d: number;
  recent_changes: string[];
  decay_correlation: string | null;
  interventions: FounderIntervention[];
}

export interface FounderPlaybook {
  id: string;
  name: string;
  description: string;
  risk_level: 'medium' | 'high' | 'critical';
  trigger_conditions: string[];
  suggested_actions: string[];
  expected_outcomes: string[];
  auto_actions: string[];
  requires_approval: boolean;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get system health and activity metrics
 */
export async function getSystemPulse(): Promise<SystemPulse> {
  const response = await apiClient.get('/ops/pulse');
  return response.data;
}

/**
 * Get infrastructure metrics
 */
export async function getInfraMetrics(): Promise<InfraMetrics> {
  const response = await apiClient.get('/ops/infra');
  return response.data;
}

/**
 * Get all customer segments
 */
export async function getCustomerSegments(limit = 50): Promise<CustomerSegment[]> {
  const response = await apiClient.get('/ops/customers', { params: { limit } });
  return response.data;
}

/**
 * Get customers at risk
 */
export async function getCustomersAtRisk(): Promise<CustomerAtRisk[]> {
  const response = await apiClient.get('/ops/customers/at-risk');
  return response.data;
}

/**
 * Get founder playbooks
 */
export async function getFounderPlaybooks(): Promise<FounderPlaybook[]> {
  const response = await apiClient.get('/ops/playbooks');
  return response.data;
}

/**
 * Trigger background job to refresh customer segments
 */
export async function refreshCustomerSegments(): Promise<{ status: string; message: string }> {
  const response = await apiClient.post('/ops/jobs/compute-stickiness');
  return response.data;
}

// =============================================================================
// Hooks (polling)
// =============================================================================

export interface OpsConsoleData {
  pulse: SystemPulse | null;
  infra: InfraMetrics | null;
  atRiskCustomers: CustomerAtRisk[];
  playbooks: FounderPlaybook[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

/**
 * Fetch all ops console data in parallel
 */
export async function fetchOpsConsoleData(): Promise<Omit<OpsConsoleData, 'isLoading' | 'error' | 'lastUpdated'>> {
  const [pulse, infra, atRiskCustomers, playbooks] = await Promise.all([
    getSystemPulse().catch(() => null),
    getInfraMetrics().catch(() => null),
    getCustomersAtRisk().catch(() => []),
    getFounderPlaybooks().catch(() => []),
  ]);

  return { pulse, infra, atRiskCustomers, playbooks };
}
