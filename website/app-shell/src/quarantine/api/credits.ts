/**
 * @audience customer
 *
 * Credits API Client
 * Billing and credit balance management
 */
import apiClient from './client';
import type { CreditBalance, LedgerEntry, InvokeAudit, PaginatedResponse } from '@/types/credit';

export async function getCreditBalance(): Promise<CreditBalance> {
  try {
    // Get budget from capabilities endpoint
    const { data } = await apiClient.get('/api/v1/runtime/capabilities');
    const budget = data?.budget || {};
    return {
      balance: budget.total_cents || 0,
      reserved: (budget.total_cents || 0) - (budget.remaining_cents || 0),
      available: budget.remaining_cents || 0,
      last_updated: new Date().toISOString(),
    };
  } catch {
    return {
      balance: 0,
      reserved: 0,
      available: 0,
      last_updated: new Date().toISOString(),
    };
  }
}

export async function getLedger(params?: {
  type?: string;
  job_id?: string;
  page?: number;
  limit?: number;
  from?: string;
  to?: string;
}): Promise<PaginatedResponse<LedgerEntry>> {
  // No ledger endpoint yet - return empty
  console.log('getLedger called with params:', params);
  return { items: [], total: 0, page: 1, limit: 20 };
}

export async function getCreditUsage(params?: {
  range?: string;
  granularity?: string;
}) {
  console.log('getCreditUsage called with params:', params);
  return { data: [], labels: [] };
}

export async function getCreditBreakdown(params?: {
  by?: string;
  range?: string;
}) {
  console.log('getCreditBreakdown called with params:', params);
  return { data: [] };
}

export async function getInvokeAudit(params?: {
  caller?: string;
  target?: string;
  status?: string;
  page?: number;
  limit?: number;
}): Promise<PaginatedResponse<InvokeAudit>> {
  try {
    // Use traces endpoint as audit log
    const { data } = await apiClient.get('/api/v1/traces', { params: { limit: params?.limit || 20 } });
    const items = Array.isArray(data) ? data : (data?.items || []);
    return {
      items: items.map((t: Record<string, unknown>) => ({
        invoke_id: t.id || t.run_id,
        caller_agent: t.agent_id || 'system',
        target_agent: t.target || 'unknown',
        action: t.action || 'invoke',
        skill: t.skill || 'unknown',
        cost_cents: t.cost || 0,
        status: t.status || 'completed',
        started_at: t.started_at || t.created_at,
        completed_at: t.completed_at,
        latency_ms: t.latency_ms || 0,
        error_message: t.error,
      })),
      total: items.length,
      page: params?.page || 1,
      limit: params?.limit || 20,
    };
  } catch {
    return { items: [], total: 0, page: 1, limit: 20 };
  }
}

export async function getInvokeDetail(invokeId: string): Promise<InvokeAudit> {
  const { data } = await apiClient.get(`/api/v1/traces/${invokeId}`);
  return data;
}

export async function topupCredits(amount: number, note?: string): Promise<LedgerEntry> {
  console.log('topupCredits called:', amount, note);
  throw new Error('Credit topup not available');
}
