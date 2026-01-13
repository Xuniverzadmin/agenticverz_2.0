/**
 * @audience customer
 *
 * Logs API Client - Immutable Record Access
 * Calls /api/v1/runtime/logs endpoints for audit and system records
 *
 * ARCHITECTURE:
 * - All records are APPEND-ONLY (enforced by DB trigger)
 * - All records are WRITE-ONCE (no UPDATE, no DELETE)
 * - These are trust anchors for verification
 *
 * Reference: PIN-413 (Logs Domain Design)
 */
import { apiClient } from './client';

// =============================================================================
// Types - Audit Ledger (User Audit)
// =============================================================================

export interface AuditLedgerItem {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor_type: 'HUMAN' | 'SYSTEM' | 'AGENT';
  actor_id: string | null;
  action_reason: string | null;
  created_at: string;
}

export interface AuditLedgerDetailItem extends AuditLedgerItem {
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
}

export interface AuditLedgerResponse {
  items: AuditLedgerItem[];
  total: number;
  has_more: boolean;
}

export interface AuditQueryParams {
  event_type?: string;
  entity_type?: 'POLICY_RULE' | 'POLICY_PROPOSAL' | 'LIMIT' | 'INCIDENT';
  actor_type?: 'HUMAN' | 'SYSTEM' | 'AGENT';
  created_after?: string;
  created_before?: string;
  limit?: number;
  offset?: number;
}

// =============================================================================
// Types - System Records
// =============================================================================

export interface SystemRecordItem {
  id: string;
  tenant_id: string | null;
  component: string;
  event_type: string;
  severity: 'INFO' | 'WARN' | 'CRITICAL';
  summary: string;
  caused_by: string | null;
  correlation_id: string | null;
  created_at: string;
}

export interface SystemRecordDetailItem extends SystemRecordItem {
  details: Record<string, unknown> | null;
}

export interface SystemRecordsResponse {
  items: SystemRecordItem[];
  total: number;
  has_more: boolean;
}

export interface SystemQueryParams {
  component?: 'worker' | 'api' | 'scheduler' | 'db' | 'auth' | 'migration';
  event_type?: string;
  severity?: 'INFO' | 'WARN' | 'CRITICAL';
  created_after?: string;
  created_before?: string;
  limit?: number;
  offset?: number;
}

// =============================================================================
// Types - LLM Run Records
// =============================================================================

export interface LLMRunRecordItem {
  id: string;
  run_id: string;
  trace_id: string | null;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  cost_cents: number;
  execution_status: 'SUCCEEDED' | 'FAILED' | 'ABORTED' | 'TIMEOUT';
  started_at: string;
  completed_at: string | null;
  source: string;
  is_synthetic: boolean;
  created_at: string;
}

export interface LLMRunRecordDetailItem extends LLMRunRecordItem {
  prompt_hash: string | null;
  response_hash: string | null;
  synthetic_scenario_id: string | null;
}

export interface LLMRunRecordsResponse {
  items: LLMRunRecordItem[];
  total: number;
  has_more: boolean;
}

export interface LLMRunQueryParams {
  run_id?: string;
  provider?: string;
  model?: string;
  execution_status?: 'SUCCEEDED' | 'FAILED' | 'ABORTED' | 'TIMEOUT';
  is_synthetic?: boolean;
  created_after?: string;
  created_before?: string;
  limit?: number;
  offset?: number;
}

// =============================================================================
// API Functions - Audit Ledger (User Audit)
// =============================================================================

/**
 * Fetch audit ledger entries (O2)
 * Shows governance actions by actors (HUMAN, SYSTEM, AGENT)
 */
export async function fetchAuditEntries(
  params: AuditQueryParams = {}
): Promise<AuditLedgerResponse> {
  const queryParams = new URLSearchParams();

  if (params.event_type) queryParams.set('event_type', params.event_type);
  if (params.entity_type) queryParams.set('entity_type', params.entity_type);
  if (params.actor_type) queryParams.set('actor_type', params.actor_type);
  if (params.created_after) queryParams.set('created_after', params.created_after);
  if (params.created_before) queryParams.set('created_before', params.created_before);
  if (params.limit !== undefined) queryParams.set('limit', params.limit.toString());
  if (params.offset !== undefined) queryParams.set('offset', params.offset.toString());

  const url = `/api/v1/runtime/logs/audit${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<AuditLedgerResponse>(url);
  return response.data;
}

/**
 * Fetch single audit entry detail (O3)
 */
export async function fetchAuditEntryDetail(entryId: string): Promise<AuditLedgerDetailItem> {
  const response = await apiClient.get<AuditLedgerDetailItem>(`/api/v1/runtime/logs/audit/${entryId}`);
  return response.data;
}

// =============================================================================
// API Functions - System Records
// =============================================================================

/**
 * Fetch system records (O2)
 * Shows system-level events: startup, shutdown, migrations, etc.
 */
export async function fetchSystemRecords(
  params: SystemQueryParams = {}
): Promise<SystemRecordsResponse> {
  const queryParams = new URLSearchParams();

  if (params.component) queryParams.set('component', params.component);
  if (params.event_type) queryParams.set('event_type', params.event_type);
  if (params.severity) queryParams.set('severity', params.severity);
  if (params.created_after) queryParams.set('created_after', params.created_after);
  if (params.created_before) queryParams.set('created_before', params.created_before);
  if (params.limit !== undefined) queryParams.set('limit', params.limit.toString());
  if (params.offset !== undefined) queryParams.set('offset', params.offset.toString());

  const url = `/api/v1/runtime/logs/system${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<SystemRecordsResponse>(url);
  return response.data;
}

/**
 * Fetch single system record detail (O3)
 */
export async function fetchSystemRecordDetail(recordId: string): Promise<SystemRecordDetailItem> {
  const response = await apiClient.get<SystemRecordDetailItem>(`/api/v1/runtime/logs/system/${recordId}`);
  return response.data;
}

// =============================================================================
// API Functions - LLM Run Records
// =============================================================================

/**
 * Fetch LLM run records (O2)
 * TRUST ANCHOR: Immutable execution records for every LLM run
 */
export async function fetchLLMRunRecords(
  params: LLMRunQueryParams = {}
): Promise<LLMRunRecordsResponse> {
  const queryParams = new URLSearchParams();

  if (params.run_id) queryParams.set('run_id', params.run_id);
  if (params.provider) queryParams.set('provider', params.provider);
  if (params.model) queryParams.set('model', params.model);
  if (params.execution_status) queryParams.set('execution_status', params.execution_status);
  if (params.is_synthetic !== undefined) queryParams.set('is_synthetic', params.is_synthetic.toString());
  if (params.created_after) queryParams.set('created_after', params.created_after);
  if (params.created_before) queryParams.set('created_before', params.created_before);
  if (params.limit !== undefined) queryParams.set('limit', params.limit.toString());
  if (params.offset !== undefined) queryParams.set('offset', params.offset.toString());

  const url = `/api/v1/runtime/logs/llm-runs${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  const response = await apiClient.get<LLMRunRecordsResponse>(url);
  return response.data;
}

/**
 * Fetch single LLM run record detail (O3)
 */
export async function fetchLLMRunRecordDetail(recordId: string): Promise<LLMRunRecordDetailItem> {
  const response = await apiClient.get<LLMRunRecordDetailItem>(`/api/v1/runtime/logs/llm-runs/${recordId}`);
  return response.data;
}
