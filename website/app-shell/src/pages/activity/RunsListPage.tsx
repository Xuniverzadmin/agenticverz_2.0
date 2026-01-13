/**
 * Runs List Page (O2) - Runtime Projection List View
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console
 * Temporal:
 *   Trigger: navigation from O1 panels
 *   Execution: async (API fetch)
 * Role: Display runs list with filters from URL query params
 * Callers: O1 navigation panels (Live, Completed, Risk Signals)
 * Reference: PIN-411 (O1 Activity Panel Binding)
 *
 * ROUTE MAPPING (PIN-411):
 * | Topic         | Route                              |
 * |---------------|-----------------------------------|
 * | Live          | /precus/activity/runs?state=LIVE      |
 * | Completed     | /precus/activity/runs?state=COMPLETED |
 * | Risk Signals  | /precus/activity/runs?risk=true       |
 *
 * INVARIANTS:
 * - O1 navigates here with filters (no data fetch in O1)
 * - O2 fetches data AFTER navigation based on query params
 * - Uses runtime projection API: GET /api/v1/runtime/activity/runs
 */

import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Activity,
  Loader2,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// =============================================================================
// Types (match backend schema)
// =============================================================================

interface RunSummary {
  run_id: string;
  tenant_id: string | null;
  project_id: string | null;
  is_synthetic: boolean;
  source: string;
  provider_type: string;
  state: string;
  status: string;
  started_at: string | null;
  last_seen_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  risk_level: string;
  latency_bucket: string;
  evidence_health: string;
  integrity_status: string;
  incident_count: number;
  policy_draft_count: number;
  policy_violation: boolean;
  input_tokens: number | null;
  output_tokens: number | null;
  estimated_cost_usd: number | null;
}

interface RunsListResponse {
  items: RunSummary[];
  total: number;
  has_more: boolean;
  filters_applied: Record<string, unknown>;
  pagination: {
    limit: number;
    offset: number;
    next_offset: number | null;
  };
}

// =============================================================================
// API Fetch Function
// =============================================================================

/**
 * Fetch runs from runtime projection API.
 *
 * INVARIANT (PIN-411):
 * - Frontend MUST NOT send tenant_id
 * - Backend derives tenant_id from auth_context
 * - This is a security invariant, not a convenience
 */
async function fetchRuns(params: {
  state?: string;
  risk?: boolean;
}): Promise<RunsListResponse> {
  const searchParams = new URLSearchParams();

  if (params.state) {
    searchParams.set('state', params.state);
  }

  if (params.risk) {
    searchParams.set('risk', 'true');
  }

  const response = await fetch(
    `/api/v1/runtime/activity/runs?${searchParams.toString()}`,
    {
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Send auth cookies
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch runs: ${response.status}`);
  }

  return response.json();
}

// =============================================================================
// Status Badge Component
// =============================================================================

function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { color: string; icon: React.ElementType }> = {
    running: { color: 'bg-blue-500/10 text-blue-400 border-blue-400/40', icon: Activity },
    succeeded: { color: 'bg-green-500/10 text-green-400 border-green-400/40', icon: CheckCircle },
    failed: { color: 'bg-red-500/10 text-red-400 border-red-400/40', icon: XCircle },
    aborted: { color: 'bg-gray-500/10 text-gray-400 border-gray-400/40', icon: XCircle },
    queued: { color: 'bg-yellow-500/10 text-yellow-400 border-yellow-400/40', icon: Clock },
    retry: { color: 'bg-orange-500/10 text-orange-400 border-orange-400/40', icon: RefreshCw },
  };

  const config = statusConfig[status.toLowerCase()] || statusConfig.queued;
  const Icon = config.icon;

  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium',
      config.color
    )}>
      <Icon size={12} />
      {status}
    </span>
  );
}

// =============================================================================
// Risk Level Badge Component
// =============================================================================

function RiskBadge({ level }: { level: string }) {
  const riskConfig: Record<string, string> = {
    NORMAL: 'bg-gray-500/10 text-gray-400 border-gray-400/40',
    NEAR_THRESHOLD: 'bg-yellow-500/10 text-yellow-400 border-yellow-400/40',
    AT_RISK: 'bg-orange-500/10 text-orange-400 border-orange-400/40',
    VIOLATED: 'bg-red-500/10 text-red-400 border-red-400/40',
  };

  const color = riskConfig[level] || riskConfig.NORMAL;

  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-medium',
      color
    )}>
      {level !== 'NORMAL' && <AlertTriangle size={12} />}
      {level}
    </span>
  );
}

// =============================================================================
// Health Badge Components (PIN-411 O2 Schema)
// =============================================================================

function LatencyBadge({ bucket }: { bucket: string }) {
  const config: Record<string, string> = {
    OK: 'bg-green-500/10 text-green-400 border-green-400/40',
    SLOW: 'bg-yellow-500/10 text-yellow-400 border-yellow-400/40',
    STALLED: 'bg-red-500/10 text-red-400 border-red-400/40',
  };
  return (
    <span className={cn(
      'inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium',
      config[bucket] || config.OK
    )}>
      {bucket}
    </span>
  );
}

function EvidenceHealthBadge({ health }: { health: string }) {
  const config: Record<string, string> = {
    FLOWING: 'bg-green-500/10 text-green-400 border-green-400/40',
    DEGRADED: 'bg-yellow-500/10 text-yellow-400 border-yellow-400/40',
    MISSING: 'bg-red-500/10 text-red-400 border-red-400/40',
  };
  return (
    <span className={cn(
      'inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium',
      config[health] || config.FLOWING
    )}>
      {health}
    </span>
  );
}

function IntegrityBadge({ status }: { status: string }) {
  const config: Record<string, string> = {
    UNKNOWN: 'bg-gray-500/10 text-gray-400 border-gray-400/40',
    VERIFIED: 'bg-green-500/10 text-green-400 border-green-400/40',
    DEGRADED: 'bg-yellow-500/10 text-yellow-400 border-yellow-400/40',
    FAILED: 'bg-red-500/10 text-red-400 border-red-400/40',
  };
  return (
    <span className={cn(
      'inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium',
      config[status] || config.UNKNOWN
    )}>
      {status}
    </span>
  );
}

// =============================================================================
// Run Row Component (PIN-411 O2 Pure Render)
// =============================================================================

/**
 * O2 Table Row - Pure render from API payload
 *
 * INVARIANTS (PIN-411):
 * - ❌ No client-side aggregation
 * - ❌ No totals
 * - ❌ No derived fields
 * - ❌ No joins
 * - All values come DIRECTLY from /runs response
 */
function RunRow({ run }: { run: RunSummary }) {
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <tr className="border-b border-gray-700/50 hover:bg-gray-800/50">
      {/* run_id (link → O3) */}
      <td className="px-4 py-3">
        <Link
          to={`/precus/activity/runs/${run.run_id}`}
          className="font-mono text-xs text-blue-400 hover:text-blue-300 hover:underline"
        >
          {run.run_id.slice(0, 8)}...
        </Link>
      </td>
      {/* status */}
      <td className="px-4 py-3">
        <StatusBadge status={run.status} />
      </td>
      {/* risk_level (badge) */}
      <td className="px-4 py-3">
        <RiskBadge level={run.risk_level} />
      </td>
      {/* latency_bucket (badge) */}
      <td className="px-4 py-3">
        <LatencyBadge bucket={run.latency_bucket} />
      </td>
      {/* evidence_health (badge) */}
      <td className="px-4 py-3">
        <EvidenceHealthBadge health={run.evidence_health} />
      </td>
      {/* integrity_status (badge) */}
      <td className="px-4 py-3">
        <IntegrityBadge status={run.integrity_status} />
      </td>
      {/* provider */}
      <td className="px-4 py-3 text-sm text-slate-400">
        {run.provider_type}
      </td>
      {/* started_at */}
      <td className="px-4 py-3 text-sm text-slate-400">
        {formatDate(run.started_at)}
      </td>
      {/* completed_at */}
      <td className="px-4 py-3 text-sm text-slate-400">
        {formatDate(run.completed_at)}
      </td>
    </tr>
  );
}

// =============================================================================
// Page Title Helper
// =============================================================================

function getPageTitle(state?: string, risk?: boolean): string {
  if (risk) return 'Risk Signals';
  if (state === 'LIVE') return 'Live LLM Runs';
  if (state === 'COMPLETED') return 'Completed LLM Runs';
  return 'All LLM Runs';
}

function getPageDescription(state?: string, risk?: boolean): string {
  if (risk) return 'LLM runs with elevated risk levels, policy violations, or incidents';
  if (state === 'LIVE') return 'Currently executing LLM runs';
  if (state === 'COMPLETED') return 'Finished LLM runs and their outcomes';
  return 'All LLM runs';
}

// =============================================================================
// Main Component
// =============================================================================

export default function RunsListPage() {
  const [searchParams] = useSearchParams();

  // Read filter params from URL
  const stateFilter = searchParams.get('state') || undefined;
  const riskFilter = searchParams.get('risk') === 'true';

  // INVARIANT (PIN-411): Frontend NEVER sends tenant_id
  // Backend derives tenant from auth_context - this is a security boundary

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['runs', 'list', stateFilter, riskFilter],
    queryFn: () => fetchRuns({
      state: stateFilter,
      risk: riskFilter,
    }),
    refetchInterval: stateFilter === 'LIVE' ? 10000 : 30000, // Faster refresh for live runs
    staleTime: 5000,
  });

  const title = getPageTitle(stateFilter, riskFilter);
  const description = getPageDescription(stateFilter, riskFilter);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/precus/activity"
            className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-gray-200 transition-colors"
          >
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-2xl font-semibold text-gray-100">{title}</h1>
            <p className="text-sm text-gray-400 mt-1">{description}</p>
          </div>
        </div>

        {/* Filters Applied Badge */}
        <div className="flex items-center gap-2">
          {stateFilter && (
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-300">
              state: {stateFilter}
            </span>
          )}
          {riskFilter && (
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-orange-900/30 text-orange-400">
              risk signals
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="animate-spin text-gray-500 mr-3" size={24} />
          <span className="text-gray-400">Loading runs...</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertCircle className="text-red-500 mb-3" size={32} />
          <h3 className="text-lg font-medium text-red-400 mb-2">Failed to load runs</h3>
          <p className="text-sm text-gray-400 mb-4">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-500"
          >
            Retry
          </button>
        </div>
      ) : data?.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Activity className="text-gray-500 mb-3" size={32} />
          <h3 className="text-lg font-medium text-gray-400 mb-2">No runs found</h3>
          <p className="text-sm text-gray-500">
            {riskFilter
              ? 'No runs with risk signals at this time.'
              : stateFilter === 'LIVE'
              ? 'No runs are currently executing.'
              : 'No completed runs match the filter criteria.'}
          </p>
        </div>
      ) : (
        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          {/* Summary */}
          <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
            <span className="text-sm text-gray-400">
              Showing {data?.items.length} of {data?.total} runs
            </span>
            {data?.has_more && (
              <span className="text-xs text-gray-500">
                More results available
              </span>
            )}
          </div>

          {/* Table - PIN-411 O2 Columns (Pure Render) */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900/50">
                <tr className="text-left text-xs text-gray-400 uppercase tracking-wider">
                  <th className="px-4 py-3 font-medium">Run ID</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Risk</th>
                  <th className="px-4 py-3 font-medium">Latency</th>
                  <th className="px-4 py-3 font-medium">Evidence</th>
                  <th className="px-4 py-3 font-medium">Integrity</th>
                  <th className="px-4 py-3 font-medium">Provider</th>
                  <th className="px-4 py-3 font-medium">Started</th>
                  <th className="px-4 py-3 font-medium">Completed</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((run) => (
                  <RunRow key={run.run_id} run={run} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
