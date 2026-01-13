/**
 * @audience customer
 *
 * Overview API Client - Cross-Domain Projection
 * Calls /api/v1/runtime/overview endpoints for aggregated data
 *
 * ARCHITECTURE:
 * - Overview is PROJECTION-ONLY (does not own tables)
 * - Aggregates from existing domains: Incidents, Policies, Limits, Runs
 * - All endpoints are READ-ONLY
 *
 * Reference: PIN-413 (Overview Domain Design)
 */
import { apiClient } from './client';

// =============================================================================
// Types - Cross-Domain Highlights
// =============================================================================

export interface SystemPulse {
  status: 'HEALTHY' | 'ATTENTION_NEEDED' | 'CRITICAL';
  active_incidents: number;
  pending_decisions: number;
  recent_breaches: number;
}

export interface DomainCount {
  domain: string;
  total: number;
  pending: number;
  critical: number;
}

export interface CrossDomainHighlightsResponse {
  pulse: SystemPulse;
  domain_counts: DomainCount[];
  last_activity_at: string | null;
}

// =============================================================================
// Types - Decisions Queue
// =============================================================================

export interface DecisionItem {
  source_domain: 'INCIDENT' | 'POLICY';
  entity_type: string;
  entity_id: string;
  decision_type: 'ACK' | 'APPROVE' | 'OVERRIDE';
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  summary: string;
  created_at: string;
}

export interface DecisionsQueueResponse {
  items: DecisionItem[];
  total: number;
  has_more: boolean;
}

export interface DecisionsQueryParams {
  source_domain?: 'INCIDENT' | 'POLICY';
  priority?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  limit?: number;
  offset?: number;
}

// =============================================================================
// Types - Cost Intelligence
// =============================================================================

export interface CostPeriod {
  start: string;
  end: string;
}

export interface CostActuals {
  llm_run_cost: number;
}

export interface LimitCostItem {
  limit_id: string;
  name: string;
  category: string;
  max_value: number;
  used_value: number;
  remaining_value: number;
  status: 'OK' | 'NEAR_THRESHOLD' | 'BREACHED';
}

export interface CostViolations {
  breach_count: number;
  total_overage: number;
}

export interface CostIntelligenceResponse {
  currency: string;
  period: CostPeriod;
  actuals: CostActuals;
  limits: LimitCostItem[];
  violations: CostViolations;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Fetch cross-domain highlights (O1)
 * Returns system pulse and domain counts
 */
export async function fetchHighlights(): Promise<CrossDomainHighlightsResponse> {
  const response = await apiClient.get<CrossDomainHighlightsResponse>(
    '/api/v1/runtime/overview/highlights'
  );
  return response.data;
}

/**
 * Fetch decisions queue (O2)
 * Returns pending items requiring human action
 */
export async function fetchDecisions(
  params: DecisionsQueryParams = {}
): Promise<DecisionsQueueResponse> {
  const queryParams = new URLSearchParams();

  if (params.source_domain) {
    queryParams.set('source_domain', params.source_domain);
  }
  if (params.priority) {
    queryParams.set('priority', params.priority);
  }
  if (params.limit !== undefined) {
    queryParams.set('limit', params.limit.toString());
  }
  if (params.offset !== undefined) {
    queryParams.set('offset', params.offset.toString());
  }

  const url = `/api/v1/runtime/overview/decisions${
    queryParams.toString() ? '?' + queryParams.toString() : ''
  }`;
  const response = await apiClient.get<DecisionsQueueResponse>(url);
  return response.data;
}

/**
 * Fetch cost intelligence (O2)
 * Returns realized and constrained costs
 */
export async function fetchCostIntelligence(
  periodDays: number = 30
): Promise<CostIntelligenceResponse> {
  const response = await apiClient.get<CostIntelligenceResponse>(
    `/api/v1/runtime/overview/costs?period_days=${periodDays}`
  );
  return response.data;
}
