/**
 * Run Detail Page (O3) - Runtime Projection Detail View
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console
 * Temporal:
 *   Trigger: navigation from O2 runs list
 *   Execution: async (API fetch)
 * Role: Display run detail with header, timeline, and CTA buttons
 * Callers: O2 RunsListPage via link
 * Reference: PIN-411 (O3 Detail Page)
 *
 * INVARIANTS (PIN-411):
 * - O3 fetches detail AFTER navigation based on run_id
 * - Uses runtime projection API: GET /api/v1/runtime/activity/runs/:id
 * - NO inline evidence (O4)
 * - NO inline traces (O5)
 * - CTA buttons for O4/O5 are preflight-only
 */

import { useParams, Link } from 'react-router-dom';
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
  FileText,
  Shield,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// =============================================================================
// Types (match backend O3 schema)
// =============================================================================

interface RunDetail {
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

// =============================================================================
// API Fetch Function
// =============================================================================

async function fetchRunDetail(runId: string): Promise<RunDetail> {
  const response = await fetch(
    `/api/v1/runtime/activity/runs/${runId}`,
    {
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch run: ${response.status}`);
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
      'inline-flex items-center gap-1.5 px-3 py-1 rounded border text-sm font-medium',
      config.color
    )}>
      <Icon size={16} />
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
      'inline-flex items-center gap-1.5 px-3 py-1 rounded border text-sm font-medium',
      color
    )}>
      {level !== 'NORMAL' && <AlertTriangle size={16} />}
      {level}
    </span>
  );
}

// =============================================================================
// Timeline Item Component
// =============================================================================

function TimelineItem({
  label,
  timestamp,
  isActive,
}: {
  label: string;
  timestamp: string | null;
  isActive?: boolean;
}) {
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className={cn(
      'flex items-center gap-4 p-3 rounded-lg',
      isActive ? 'bg-blue-500/10 border border-blue-500/30' : 'bg-gray-800/50'
    )}>
      <div className={cn(
        'w-3 h-3 rounded-full',
        timestamp ? 'bg-blue-400' : 'bg-gray-600'
      )} />
      <div className="flex-1">
        <div className="text-sm font-medium text-gray-300">{label}</div>
        <div className="text-xs text-gray-500">{formatDate(timestamp)}</div>
      </div>
    </div>
  );
}

// =============================================================================
// Execution Summary Component
// =============================================================================

function ExecutionSummary({ run }: { run: RunDetail }) {
  const formatDuration = (ms: number | null) => {
    if (ms === null) return '—';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const formatCost = (usd: number | null) => {
    if (usd === null) return '—';
    return `$${usd.toFixed(4)}`;
  };

  const formatTokens = (tokens: number | null) => {
    if (tokens === null) return '—';
    return tokens.toLocaleString();
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-gray-800/50 rounded-lg p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wide">Duration</div>
        <div className="text-lg font-medium text-gray-200 mt-1">
          {formatDuration(run.duration_ms)}
        </div>
      </div>
      <div className="bg-gray-800/50 rounded-lg p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wide">Input Tokens</div>
        <div className="text-lg font-medium text-gray-200 mt-1">
          {formatTokens(run.input_tokens)}
        </div>
      </div>
      <div className="bg-gray-800/50 rounded-lg p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wide">Output Tokens</div>
        <div className="text-lg font-medium text-gray-200 mt-1">
          {formatTokens(run.output_tokens)}
        </div>
      </div>
      <div className="bg-gray-800/50 rounded-lg p-4">
        <div className="text-xs text-gray-500 uppercase tracking-wide">Estimated Cost</div>
        <div className="text-lg font-medium text-gray-200 mt-1">
          {formatCost(run.estimated_cost_usd)}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Impact Signals Component
// =============================================================================

function ImpactSignals({ run }: { run: RunDetail }) {
  return (
    <div className="flex flex-wrap gap-4">
      {run.incident_count > 0 && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 rounded-lg border border-red-500/30">
          <AlertCircle size={16} className="text-red-400" />
          <span className="text-sm text-red-400">{run.incident_count} incident(s)</span>
        </div>
      )}
      {run.policy_draft_count > 0 && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-orange-500/10 rounded-lg border border-orange-500/30">
          <FileText size={16} className="text-orange-400" />
          <span className="text-sm text-orange-400">{run.policy_draft_count} policy draft(s)</span>
        </div>
      )}
      {run.policy_violation && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 rounded-lg border border-red-500/30">
          <Shield size={16} className="text-red-400" />
          <span className="text-sm text-red-400">Policy Violation</span>
        </div>
      )}
      {run.incident_count === 0 && run.policy_draft_count === 0 && !run.policy_violation && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-500/10 rounded-lg border border-gray-500/30">
          <CheckCircle size={16} className="text-gray-400" />
          <span className="text-sm text-gray-400">No impact signals</span>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function RunDetailPage() {
  const { id: runId } = useParams<{ id: string }>();

  const { data: run, isLoading, error, refetch } = useQuery({
    queryKey: ['run', 'detail', runId],
    queryFn: () => fetchRunDetail(runId!),
    enabled: !!runId,
    refetchInterval: 30000,
    staleTime: 5000,
  });

  if (!runId) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <AlertCircle className="text-red-500 mb-3" size={32} />
        <h3 className="text-lg font-medium text-red-400">Invalid Run ID</h3>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/precus/activity/runs"
            className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-gray-200 transition-colors"
          >
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-xl font-mono text-gray-100">{runId}</h1>
            <p className="text-sm text-gray-400 mt-1">Run Detail</p>
          </div>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="animate-spin text-gray-500 mr-3" size={24} />
          <span className="text-gray-400">Loading run details...</span>
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertCircle className="text-red-500 mb-3" size={32} />
          <h3 className="text-lg font-medium text-red-400 mb-2">Failed to load run</h3>
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
      ) : run ? (
        <div className="space-y-6">
          {/* Status Header Card */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <div className="flex flex-wrap items-center gap-4">
              <StatusBadge status={run.status} />
              <RiskBadge level={run.risk_level} />
              <span className="px-3 py-1 rounded bg-gray-700/50 text-sm text-gray-300">
                {run.provider_type}
              </span>
              <span className="px-3 py-1 rounded bg-gray-700/50 text-sm text-gray-300">
                {run.state}
              </span>
            </div>
          </div>

          {/* Timeline */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-200 mb-4">Timeline</h2>
            <div className="space-y-2">
              <TimelineItem
                label="Started"
                timestamp={run.started_at}
                isActive={run.state === 'LIVE' && run.status === 'running'}
              />
              <TimelineItem
                label="Last Seen"
                timestamp={run.last_seen_at}
                isActive={run.state === 'LIVE'}
              />
              <TimelineItem
                label="Completed"
                timestamp={run.completed_at}
                isActive={run.state === 'COMPLETED'}
              />
            </div>
          </div>

          {/* Execution Summary */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-200 mb-4">Execution Summary</h2>
            <ExecutionSummary run={run} />
          </div>

          {/* Impact Signals */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-200 mb-4">Impact Signals</h2>
            <ImpactSignals run={run} />
          </div>

          {/* CTA Buttons - Preflight Only */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-200 mb-4">Deeper Analysis</h2>
            <p className="text-sm text-gray-400 mb-4">
              Evidence and proof data are available in preflight console only.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
                disabled
                title="O4 Evidence - Preflight only"
              >
                <FileText size={16} />
                View Evidence (O4)
              </button>
              <button
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
                disabled
                title="O5 Proof - Preflight only"
              >
                <Shield size={16} />
                View Proof (O5)
              </button>
            </div>
          </div>

          {/* Metadata */}
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-4">
            <div className="flex flex-wrap gap-4 text-xs text-gray-500">
              <span>Source: {run.source}</span>
              <span>Latency: {run.latency_bucket}</span>
              <span>Evidence: {run.evidence_health}</span>
              <span>Integrity: {run.integrity_status}</span>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
