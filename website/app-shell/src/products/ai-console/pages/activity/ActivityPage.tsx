/**
 * Customer Activity Page - Execution History & Outcomes
 *
 * Customer Console v1 Constitution: Activity Domain
 * Question: "What ran / is running?"
 *
 * Shows:
 * - Execution history (list view)
 * - Final state per execution
 * - Plain errors (no traces, no CARE internals)
 *
 * Does NOT show:
 * - Decision timelines
 * - Recovery classes
 * - Raw traces
 * - CARE internals
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { logger } from '@/lib/consoleLogger';
import { fetchActivityRuns, type RunSummary, type ActivityResponse } from '@/api/activity';

// Re-export for local use with extended display fields
interface ExecutionSummary extends RunSummary {
  // Display-friendly computed fields (optional)
}

const STATUS_CONFIG: Record<string, { label: string; color: string; border: string }> = {
  completed: { label: 'Completed', color: 'text-green-400', border: 'border-green-400/40' },
  failed: { label: 'Failed', color: 'text-red-400', border: 'border-red-400/40' },
  running: { label: 'Running', color: 'text-blue-400', border: 'border-blue-400/40' },
  cancelled: { label: 'Cancelled', color: 'text-slate-400', border: 'border-slate-600' },
  queued: { label: 'Queued', color: 'text-yellow-400', border: 'border-yellow-400/40' },
  pending: { label: 'Pending', color: 'text-orange-400', border: 'border-orange-400/40' },
};

// Default status config for unknown statuses
const DEFAULT_STATUS_CONFIG = { label: 'Unknown', color: 'text-slate-400', border: 'border-slate-600' };

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatDuration(startedAt: string, endedAt: string | null): string {
  if (!endedAt) return 'In progress';
  const start = new Date(startedAt).getTime();
  const end = new Date(endedAt).getTime();
  const durationMs = end - start;

  if (durationMs < 1000) return `${durationMs}ms`;
  if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
  return `${Math.floor(durationMs / 60000)}m ${Math.floor((durationMs % 60000) / 1000)}s`;
}

export function ActivityPage() {
  const [selectedExecution, setSelectedExecution] = useState<ExecutionSummary | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    logger.componentMount('CustomerActivityPage');
    return () => logger.componentUnmount('CustomerActivityPage');
  }, []);

  // Fetch activity (runs) from real backend API
  // SDSR Pipeline: Calls /api/v1/activity/runs (PIN-370)
  const { data, isLoading, error } = useQuery<ActivityResponse>({
    queryKey: ['customer', 'activity', page],
    queryFn: () => fetchActivityRuns({
      page,
      per_page: 20,
      include_synthetic: true, // Include synthetic SDSR data
    }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  const executions = data?.runs ?? [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading activity...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>⚡</span> Activity
        </h1>
        <p className="text-slate-400 mt-1">
          What ran / is running
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-navy-surface border border-navy-border rounded-lg p-4">
          <div className="text-sm text-slate-400">Total Runs</div>
          <div className="text-2xl font-bold text-white">{data?.total ?? 0}</div>
        </div>
        <div className="bg-navy-surface border border-navy-border rounded-lg p-4">
          <div className="text-sm text-slate-400">Completed</div>
          <div className="text-2xl font-bold text-green-400">
            {executions.filter(r => r.status === 'completed').length}
          </div>
        </div>
        <div className="bg-navy-surface border border-navy-border rounded-lg p-4">
          <div className="text-sm text-slate-400">Failed</div>
          <div className="text-2xl font-bold text-red-400">
            {executions.filter(r => r.status === 'failed').length}
          </div>
        </div>
        <div className="bg-navy-surface border border-navy-border rounded-lg p-4">
          <div className="text-sm text-slate-400">Synthetic (SDSR)</div>
          <div className="text-2xl font-bold text-purple-400">
            {executions.filter(r => r.is_synthetic).length}
          </div>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Executions List */}
        <div className="flex-1">
          <div className="bg-navy-surface rounded-xl border border-navy-border overflow-hidden">
            <table className="w-full">
              <thead className="bg-navy-elevated">
                <tr className="text-left text-sm text-slate-400">
                  <th className="p-4">Run ID</th>
                  <th className="p-4">Goal</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Agent</th>
                  <th className="p-4">Created</th>
                  <th className="p-4">Synthetic</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-border">
                {executions.map((execution) => {
                  const statusConfig = STATUS_CONFIG[execution.status] || DEFAULT_STATUS_CONFIG;
                  const isSelected = selectedExecution?.run_id === execution.run_id;

                  return (
                    <tr
                      key={execution.run_id}
                      onClick={() => setSelectedExecution(execution)}
                      className={`
                        cursor-pointer transition-colors
                        ${isSelected ? 'bg-navy-elevated' : 'hover:bg-navy-elevated/50'}
                      `}
                    >
                      <td className="p-4 font-mono text-sm text-slate-300">
                        {execution.run_id.slice(0, 12)}...
                      </td>
                      <td className="p-4 text-white max-w-xs truncate" title={execution.goal}>
                        {execution.goal.length > 40 ? `${execution.goal.slice(0, 40)}...` : execution.goal}
                      </td>
                      <td className="p-4">
                        <span className={`
                          px-2 py-1 rounded border text-xs font-medium bg-transparent
                          ${statusConfig.color} ${statusConfig.border}
                        `}>
                          {statusConfig.label}
                        </span>
                      </td>
                      <td className="p-4 font-mono text-xs text-slate-400">
                        {execution.agent_id.slice(0, 16)}...
                      </td>
                      <td className="p-4 text-sm text-slate-400">
                        {formatTime(execution.created_at)}
                      </td>
                      <td className="p-4">
                        {execution.is_synthetic ? (
                          <span className="px-2 py-1 rounded border text-xs font-medium bg-purple-500/10 text-purple-400 border-purple-400/40">
                            SDSR
                          </span>
                        ) : (
                          <span className="text-slate-500 text-xs">-</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex justify-between items-center mt-4 text-sm text-slate-400">
            <span>Showing {executions.length} of {data?.total ?? 0} executions</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 bg-navy-elevated border border-navy-border rounded hover:bg-navy-subtle disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={executions.length < (data?.per_page ?? 20)}
                className="px-3 py-1 bg-navy-elevated border border-navy-border rounded hover:bg-navy-subtle disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Execution Details Panel */}
        {selectedExecution && (
          <div className="w-80">
            <ExecutionDetailsPanel execution={selectedExecution} onClose={() => setSelectedExecution(null)} />
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Run Details Panel - Shows SDSR run details
 *
 * Displays:
 * - Run metadata (ID, goal, agent)
 * - Status with RETRY capability for failed runs
 * - Timing information
 * - SDSR synthetic data markers
 */
function ExecutionDetailsPanel({ execution, onClose }: { execution: ExecutionSummary; onClose: () => void }) {
  const statusConfig = STATUS_CONFIG[execution.status] || DEFAULT_STATUS_CONFIG;

  return (
    <div className="bg-navy-surface rounded-xl border border-navy-border p-4 sticky top-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-white">Run Details</h3>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>

      <div className="space-y-4">
        {/* Run ID */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Run ID</div>
          <div className="font-mono text-sm text-slate-300 bg-navy-inset rounded px-2 py-1 break-all">
            {execution.run_id}
          </div>
        </div>

        {/* Goal */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Goal</div>
          <div className="text-sm text-white bg-navy-inset rounded px-2 py-2">
            {execution.goal}
          </div>
        </div>

        {/* Status */}
        <div className="pt-4 border-t border-navy-border">
          <div className="text-xs text-slate-500 font-bold uppercase tracking-wide mb-3">
            STATUS
          </div>
          <div className={`rounded-lg p-3 ${
            execution.status === 'completed' ? 'bg-green-500/10 border border-green-500/30' :
            execution.status === 'failed' ? 'bg-red-500/10 border border-red-500/30' :
            execution.status === 'queued' ? 'bg-yellow-500/10 border border-yellow-500/30' :
            'bg-blue-500/10 border border-blue-500/30'
          }`}>
            <div className="flex items-center gap-2">
              <span className={`
                inline-block px-2 py-1 rounded border text-xs font-medium bg-transparent
                ${statusConfig.color} ${statusConfig.border}
              `}>
                {statusConfig.label}
              </span>
            </div>
          </div>
        </div>

        {/* Agent Info */}
        <div className="pt-4 border-t border-navy-border">
          <div className="text-xs text-slate-500 font-bold uppercase tracking-wide mb-3">
            AGENT
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Agent ID</span>
              <span className="font-mono text-xs text-slate-300">{execution.agent_id}</span>
            </div>
            {execution.tenant_id && (
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Tenant ID</span>
                <span className="font-mono text-xs text-slate-300">{execution.tenant_id}</span>
              </div>
            )}
          </div>
        </div>

        {/* Timing section */}
        <div className="pt-4 border-t border-navy-border">
          <div className="text-xs text-slate-500 font-bold uppercase tracking-wide mb-3">
            TIMING
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Created</span>
              <span className="text-slate-300">{formatTime(execution.created_at)}</span>
            </div>
            {execution.started_at && (
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Started</span>
                <span className="text-slate-300">{formatTime(execution.started_at)}</span>
              </div>
            )}
            {execution.completed_at && (
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Completed</span>
                <span className="text-slate-300">{formatTime(execution.completed_at)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Parent Run (for retries) */}
        {execution.parent_run_id && (
          <div className="pt-4 border-t border-navy-border">
            <div className="text-xs text-blue-400 font-bold uppercase tracking-wide mb-2">
              RETRY OF
            </div>
            <div className="font-mono text-xs text-blue-300 bg-blue-500/10 border border-blue-500/30 rounded px-2 py-1">
              {execution.parent_run_id}
            </div>
          </div>
        )}

        {/* SDSR Synthetic Marker */}
        {execution.is_synthetic && (
          <div className="pt-4 border-t border-navy-border">
            <div className="text-xs text-purple-400 font-bold uppercase tracking-wide mb-2">
              SDSR SYNTHETIC DATA
            </div>
            <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-1 rounded border text-xs font-medium bg-purple-500/20 text-purple-400 border-purple-400/40">
                  SYNTHETIC
                </span>
              </div>
              {execution.synthetic_scenario_id && (
                <p className="text-xs text-purple-300 font-mono">
                  Scenario: {execution.synthetic_scenario_id}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Error (if failed) */}
        {execution.error_message && (
          <div className="pt-4 border-t border-navy-border">
            <div className="text-xs text-red-400 font-bold uppercase tracking-wide mb-2">ERROR</div>
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
              <p className="text-red-300 text-sm">{execution.error_message}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ActivityPage;
