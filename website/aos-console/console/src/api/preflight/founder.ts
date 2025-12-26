/**
 * Founder Preflight API
 *
 * Runtime v1 Feature Freeze - PIN-183
 *
 * Domain: preflight-fops.agenticverz.com
 * Plane: Founder
 * Purpose: System truth verification before promoting to production
 *
 * HARD RULES:
 * - Founder-only auth
 * - Read-only
 * - Full system visibility
 * - Zero customer UI reuse
 * - No shared code with CustomerPreflightDTO
 */

// =============================================================================
// SCHEMA: FounderPreflightDTO
// =============================================================================

export interface FounderPreflightDTO {
  // Identity
  plane: 'founder';
  environment: 'preflight';
  timestamp: string;

  // Infra Health
  infra: {
    database: InfraStatus;
    redis: InfraStatus;
    worker: WorkerStatus;
    prometheus: InfraStatus;
  };

  // Cost Pipeline
  cost_pipeline: {
    last_aggregation: string;
    pending_records: number;
    total_tracked_cents: number;
  };

  // Incident State
  incidents: {
    open_count: number;
    last_24h_count: number;
    severity_breakdown: SeverityBreakdown;
  };

  // Recovery State
  recovery: {
    frozen_tenants: number;
    frozen_keys: number;
    active_guardrails: number;
  };

  // System Truth
  system: {
    version: string;
    deployed_at: string;
    feature_flags: Record<string, boolean>;
  };
}

export interface InfraStatus {
  status: 'ok' | 'degraded' | 'down';
  latency_ms: number;
}

export interface WorkerStatus {
  status: 'ok' | 'degraded' | 'down';
  active_count: number;
}

export interface SeverityBreakdown {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

// =============================================================================
// PROMOTION CHECKLIST
// =============================================================================

export interface FounderPromotionChecklist {
  infra_healthy: boolean;
  cost_pipeline_healthy: boolean;
  no_critical_incidents: boolean;
  recovery_state_understood: boolean;
  founder_auth_verified: boolean;

  // Derived
  ready_to_promote: boolean;
  blocking_reasons: string[];
}

// =============================================================================
// API CLIENT
// =============================================================================

const PREFLIGHT_FOPS_BASE = import.meta.env.VITE_PREFLIGHT_FOPS_BASE || 'https://preflight-fops.agenticverz.com';

/**
 * Fetch founder preflight status
 * Requires founder-level authentication
 */
export async function getFounderPreflight(): Promise<FounderPreflightDTO> {
  const response = await fetch(`${PREFLIGHT_FOPS_BASE}/api/v1/preflight`, {
    headers: {
      'Authorization': `Bearer ${getFounderToken()}`,
      'X-Plane': 'founder',
      'X-Environment': 'preflight',
    },
  });

  if (!response.ok) {
    throw new Error(`Founder preflight failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Get promotion checklist
 * Evaluates readiness to promote from preflight to production
 */
export async function getFounderPromotionChecklist(): Promise<FounderPromotionChecklist> {
  const preflight = await getFounderPreflight();

  const infra_healthy =
    preflight.infra.database.status === 'ok' &&
    preflight.infra.redis.status === 'ok' &&
    preflight.infra.worker.status === 'ok' &&
    preflight.infra.prometheus.status === 'ok';

  const cost_pipeline_healthy = preflight.cost_pipeline.pending_records < 1000;
  const no_critical_incidents = preflight.incidents.severity_breakdown.critical === 0;
  const recovery_state_understood = true; // Manual verification
  const founder_auth_verified = true; // Already authenticated if we got here

  const blocking_reasons: string[] = [];
  if (!infra_healthy) blocking_reasons.push('Infrastructure not healthy');
  if (!cost_pipeline_healthy) blocking_reasons.push('Cost pipeline backlog too high');
  if (!no_critical_incidents) blocking_reasons.push('Critical incidents open');

  return {
    infra_healthy,
    cost_pipeline_healthy,
    no_critical_incidents,
    recovery_state_understood,
    founder_auth_verified,
    ready_to_promote: blocking_reasons.length === 0,
    blocking_reasons,
  };
}

/**
 * Get founder auth token
 * This should be implemented based on your auth system
 */
function getFounderToken(): string {
  // In production, this would retrieve the founder's auth token
  // For now, use localStorage or auth store
  return localStorage.getItem('founder-auth-token') || '';
}

// =============================================================================
// TYPE GUARDS
// =============================================================================

export function isFounderPreflight(obj: unknown): obj is FounderPreflightDTO {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    (obj as FounderPreflightDTO).plane === 'founder' &&
    (obj as FounderPreflightDTO).environment === 'preflight'
  );
}
