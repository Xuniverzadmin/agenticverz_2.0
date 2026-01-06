/**
 * Founder Explorer API Client
 *
 * H3 Founder Console - Cross-tenant exploratory access
 * FOUNDER ONLY - READ-ONLY diagnostics and patterns
 *
 * Reference: Phase H3 - Founder Console Exploratory Mode
 */

import apiClient from './client';

// =============================================================================
// Types
// =============================================================================

export interface TenantSummary {
  tenant_id: string;
  name: string;
  created_at: string;
  status: string;
  metrics: {
    total_runs: number;
    active_agents: number;
    budget_used_cents: number;
    budget_limit_cents: number;
    incidents_last_7d: number;
    policy_violations_last_7d: number;
  };
}

export interface SystemSummary {
  total_tenants: number;
  total_agents: number;
  total_runs_all_time: number;
  runs_last_24h: number;
  active_incidents: number;
  system_health: 'healthy' | 'degraded' | 'critical';
  top_tenants_by_activity: TenantSummary[];
  timestamp: string;
}

export interface TenantDiagnostics {
  tenant_id: string;
  diagnostics: {
    agents: {
      total: number;
      by_status: Record<string, number>;
      recent_failures: Array<{
        agent_id: string;
        name: string;
        failure_count: number;
        last_failure: string;
      }>;
    };
    runs: {
      total: number;
      by_status: Record<string, number>;
      avg_duration_ms: number;
      p95_duration_ms: number;
    };
    budget: {
      total_spent_cents: number;
      limit_cents: number;
      utilization_pct: number;
      trend: 'increasing' | 'stable' | 'decreasing';
    };
    incidents: {
      total: number;
      open: number;
      resolved_last_7d: number;
      by_severity: Record<string, number>;
    };
    policies: {
      total: number;
      active: number;
      violations_last_7d: number;
    };
  };
  collected_at: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'critical';
  checks: Array<{
    name: string;
    status: 'pass' | 'warn' | 'fail';
    message: string;
    last_check: string;
  }>;
  uptime_pct: number;
  last_incident: string | null;
  timestamp: string;
}

export interface UsagePattern {
  pattern_type: string;
  description: string;
  frequency: number;
  affected_tenants: number;
  trend: 'increasing' | 'stable' | 'decreasing';
  significance: 'low' | 'medium' | 'high';
}

export interface PatternsResponse {
  patterns: UsagePattern[];
  analysis_window: string;
  total_events_analyzed: number;
  generated_at: string;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get cross-tenant system summary
 * FOUNDER ONLY
 */
export async function getSystemSummary(): Promise<SystemSummary> {
  const response = await apiClient.get('/api/v1/explorer/summary');
  return response.data;
}

/**
 * List all tenants with metrics
 * FOUNDER ONLY
 */
export async function listTenants(options?: {
  limit?: number;
  offset?: number;
  sortBy?: 'activity' | 'budget' | 'incidents' | 'created';
  order?: 'asc' | 'desc';
}): Promise<TenantSummary[]> {
  const response = await apiClient.get('/api/v1/explorer/tenants', {
    params: options,
  });
  return response.data;
}

/**
 * Get deep diagnostics for a specific tenant
 * FOUNDER ONLY
 */
export async function getTenantDiagnostics(
  tenantId: string
): Promise<TenantDiagnostics> {
  const response = await apiClient.get(
    `/api/v1/explorer/tenant/${tenantId}/diagnostics`
  );
  return response.data;
}

/**
 * Get system health check
 * FOUNDER ONLY
 */
export async function getSystemHealth(): Promise<SystemHealth> {
  const response = await apiClient.get('/api/v1/explorer/system/health');
  return response.data;
}

/**
 * Get usage pattern analysis
 * FOUNDER ONLY
 */
export async function getUsagePatterns(): Promise<PatternsResponse> {
  const response = await apiClient.get('/api/v1/explorer/patterns');
  return response.data;
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get health status color
 */
export function getHealthStatusColor(
  status: 'healthy' | 'degraded' | 'critical'
): string {
  switch (status) {
    case 'healthy':
      return 'text-green-400';
    case 'degraded':
      return 'text-yellow-400';
    case 'critical':
      return 'text-red-400';
    default:
      return 'text-gray-400';
  }
}

/**
 * Get check status color
 */
export function getCheckStatusColor(status: 'pass' | 'warn' | 'fail'): string {
  switch (status) {
    case 'pass':
      return 'text-green-400 bg-green-900/30';
    case 'warn':
      return 'text-yellow-400 bg-yellow-900/30';
    case 'fail':
      return 'text-red-400 bg-red-900/30';
    default:
      return 'text-gray-400 bg-gray-900/30';
  }
}

/**
 * Get trend indicator
 */
export function getTrendIndicator(
  trend: 'increasing' | 'stable' | 'decreasing'
): { icon: string; color: string } {
  switch (trend) {
    case 'increasing':
      return { icon: '↑', color: 'text-green-400' };
    case 'decreasing':
      return { icon: '↓', color: 'text-red-400' };
    case 'stable':
    default:
      return { icon: '→', color: 'text-gray-400' };
  }
}

/**
 * Get significance color
 */
export function getSignificanceColor(
  significance: 'low' | 'medium' | 'high'
): string {
  switch (significance) {
    case 'high':
      return 'text-red-400 bg-red-900/30';
    case 'medium':
      return 'text-yellow-400 bg-yellow-900/30';
    case 'low':
      return 'text-blue-400 bg-blue-900/30';
    default:
      return 'text-gray-400 bg-gray-900/30';
  }
}

/**
 * Format budget utilization
 */
export function formatUtilization(pct: number): string {
  return `${pct.toFixed(1)}%`;
}

/**
 * Get utilization color
 */
export function getUtilizationColor(pct: number): string {
  if (pct >= 90) return 'text-red-400';
  if (pct >= 70) return 'text-yellow-400';
  return 'text-green-400';
}

export default {
  getSystemSummary,
  listTenants,
  getTenantDiagnostics,
  getSystemHealth,
  getUsagePatterns,
  getHealthStatusColor,
  getCheckStatusColor,
  getTrendIndicator,
  getSignificanceColor,
  formatUtilization,
  getUtilizationColor,
};
