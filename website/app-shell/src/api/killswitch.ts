/**
 * @audience founder
 *
 * KillSwitch API Client
 *
 * Phase 5E-2: Kill-Switch UI Toggle
 *
 * Endpoints:
 * - GET /v1/killswitch/status - Get freeze status for a tenant
 * - POST /v1/killswitch/tenant - Freeze tenant
 * - POST /v1/killswitch/key - Freeze API key
 * - DELETE /v1/killswitch/tenant - Unfreeze tenant
 * - DELETE /v1/killswitch/key - Unfreeze API key
 * - GET /v1/policies/active - Get active guardrails
 * - GET /v1/incidents - List incidents
 *
 * RBAC:
 * - killswitch:read - View status (founder, operator, admin, customer)
 * - killswitch:activate - Freeze entities (founder, operator, infra, admin)
 * - killswitch:reset - Unfreeze entities (founder, infra only)
 *
 * Design Principles (per Phase 5E):
 * - Read-only display of current state
 * - Actions require explicit confirmation
 * - No smart summaries - verbatim values
 */

import { apiClient } from './client';

// =============================================================================
// Types (matching backend models verbatim)
// =============================================================================

export interface KillSwitchStatus {
  entity_type: 'tenant' | 'key';
  entity_id: string;
  is_frozen: boolean;
  frozen_at: string | null;
  frozen_by: string | null;
  freeze_reason: string | null;
  auto_triggered: boolean;
  trigger_type: string | null;
}

export interface KillSwitchAction {
  reason: string;
  actor?: string;
}

export interface TenantKillSwitchState {
  tenant_id: string;
  tenant: {
    is_frozen: boolean;
    frozen_at: string | null;
    frozen_by: string | null;
    freeze_reason: string | null;
    auto_triggered: boolean;
    trigger_type: string | null;
  };
  keys: Array<{
    key_id: string;
    is_frozen: boolean;
    frozen_at: string | null;
    frozen_by: string | null;
    freeze_reason: string | null;
  }>;
  effective_state: 'frozen' | 'active';
}

export interface GuardrailSummary {
  id: string;
  name: string;
  description: string | null;
  category: string;
  action: string;
  is_enabled: boolean;
  priority: number;
}

export interface IncidentSummary {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'acknowledged' | 'resolved';
  trigger_type: string;
  calls_affected: number;
  cost_delta_cents: number;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get kill-switch status for a tenant (includes all keys)
 */
export async function getKillSwitchStatus(tenantId: string): Promise<TenantKillSwitchState> {
  const response = await apiClient.get('/v1/killswitch/status', {
    params: { tenant_id: tenantId }
  });
  return response.data;
}

/**
 * Freeze a tenant (immediate, no in-flight retries)
 */
export async function freezeTenant(
  tenantId: string,
  action: KillSwitchAction
): Promise<KillSwitchStatus> {
  const response = await apiClient.post('/v1/killswitch/tenant', action, {
    params: { tenant_id: tenantId }
  });
  return response.data;
}

/**
 * Unfreeze a tenant
 */
export async function unfreezeTenant(
  tenantId: string,
  actor: string = 'founder'
): Promise<KillSwitchStatus> {
  const response = await apiClient.delete('/v1/killswitch/tenant', {
    params: { tenant_id: tenantId, actor }
  });
  return response.data;
}

/**
 * Freeze an API key
 */
export async function freezeKey(
  keyId: string,
  action: KillSwitchAction
): Promise<KillSwitchStatus> {
  const response = await apiClient.post('/v1/killswitch/key', action, {
    params: { key_id: keyId }
  });
  return response.data;
}

/**
 * Unfreeze an API key
 */
export async function unfreezeKey(
  keyId: string,
  actor: string = 'founder'
): Promise<KillSwitchStatus> {
  const response = await apiClient.delete('/v1/killswitch/key', {
    params: { key_id: keyId, actor }
  });
  return response.data;
}

/**
 * Get active guardrails (what's protecting right now)
 */
export async function getActiveGuardrails(): Promise<GuardrailSummary[]> {
  const response = await apiClient.get('/v1/policies/active');
  return response.data;
}

/**
 * List incidents for a tenant
 */
export async function listIncidents(params: {
  tenant_id: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<IncidentSummary[]> {
  const response = await apiClient.get('/v1/incidents', { params });
  return response.data;
}

/**
 * Get all tenants for kill-switch overview
 * Note: Uses /ops/customers which returns tenant list
 */
export async function getAllTenants(): Promise<Array<{
  tenant_id: string;
  tenant_name: string | null;
}>> {
  const response = await apiClient.get('/ops/customers', {
    params: { limit: 100 }
  });
  return response.data.map((c: { tenant_id: string; tenant_name: string | null }) => ({
    tenant_id: c.tenant_id,
    tenant_name: c.tenant_name
  }));
}
