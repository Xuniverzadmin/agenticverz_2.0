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

interface ExecutionSummary {
  run_id: string;
  status: 'completed' | 'failed' | 'running' | 'cancelled';
  skill_name: string;
  started_at: string;
  ended_at: string | null;
  cost_cents: number;
  error_message: string | null;

  // Phase 5E-5: Contract Surfacing - PRE-RUN
  pre_run: {
    stages_planned: number;
    memory_injection: boolean;
    budget_mode: 'enforced' | 'advisory';
  };

  // Phase 5E-5: Contract Surfacing - CONSTRAINTS
  constraints: {
    budget_passed: boolean;
    rate_limit_passed: boolean;
    policy_passed: boolean;
  };

  // Phase 5E-5: Contract Surfacing - COST
  cost_estimated_cents: number;

  // Phase 5E-5: Contract Surfacing - OUTCOME
  outcome_reason: string | null;
}

interface ActivityResponse {
  runs: ExecutionSummary[];
  total: number;
  page: number;
  per_page: number;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; border: string }> = {
  completed: { label: 'Completed', color: 'text-green-400', border: 'border-green-400/40' },
  failed: { label: 'Failed', color: 'text-red-400', border: 'border-red-400/40' },
  running: { label: 'Running', color: 'text-blue-400', border: 'border-blue-400/40' },
  cancelled: { label: 'Cancelled', color: 'text-slate-400', border: 'border-slate-600' },
};

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

  // Fetch activity (executions)
  const { data, isLoading } = useQuery<ActivityResponse>({
    queryKey: ['customer', 'activity', page],
    queryFn: async () => {
      // In production, this would call: GET /api/v1/runs?page={page}
      // For now, return demo data
      return {
        runs: [
          {
            run_id: 'run_abc123',
            status: 'completed',
            skill_name: 'web_search',
            started_at: new Date(Date.now() - 300000).toISOString(),
            ended_at: new Date(Date.now() - 295000).toISOString(),
            cost_cents: 12,
            error_message: null,
            // Phase 5E-5: Contract Surfacing
            pre_run: { stages_planned: 3, memory_injection: true, budget_mode: 'enforced' },
            constraints: { budget_passed: true, rate_limit_passed: true, policy_passed: true },
            cost_estimated_cents: 10,
            outcome_reason: 'All stages completed successfully',
          },
          {
            run_id: 'run_def456',
            status: 'failed',
            skill_name: 'code_executor',
            started_at: new Date(Date.now() - 600000).toISOString(),
            ended_at: new Date(Date.now() - 590000).toISOString(),
            cost_cents: 8,
            error_message: 'Execution timeout: skill exceeded 30s limit',
            // Phase 5E-5: Contract Surfacing
            pre_run: { stages_planned: 5, memory_injection: false, budget_mode: 'advisory' },
            constraints: { budget_passed: true, rate_limit_passed: true, policy_passed: true },
            cost_estimated_cents: 25,
            outcome_reason: 'Skill timeout at stage 3/5',
          },
          {
            run_id: 'run_ghi789',
            status: 'completed',
            skill_name: 'data_analysis',
            started_at: new Date(Date.now() - 1200000).toISOString(),
            ended_at: new Date(Date.now() - 1180000).toISOString(),
            cost_cents: 45,
            error_message: null,
            // Phase 5E-5: Contract Surfacing - Demo budget exceeded in advisory mode
            pre_run: { stages_planned: 4, memory_injection: true, budget_mode: 'advisory' },
            constraints: { budget_passed: false, rate_limit_passed: true, policy_passed: true },
            cost_estimated_cents: 30,
            outcome_reason: 'Completed with budget overrun (advisory mode)',
          },
          {
            run_id: 'run_jkl012',
            status: 'completed',
            skill_name: 'web_search',
            started_at: new Date(Date.now() - 3600000).toISOString(),
            ended_at: new Date(Date.now() - 3595000).toISOString(),
            cost_cents: 10,
            error_message: null,
            // Phase 5E-5: Contract Surfacing
            pre_run: { stages_planned: 2, memory_injection: false, budget_mode: 'enforced' },
            constraints: { budget_passed: true, rate_limit_passed: true, policy_passed: true },
            cost_estimated_cents: 10,
            outcome_reason: 'Completed within budget',
          },
          {
            run_id: 'run_mno345',
            status: 'cancelled',
            skill_name: 'file_processor',
            started_at: new Date(Date.now() - 7200000).toISOString(),
            ended_at: new Date(Date.now() - 7190000).toISOString(),
            cost_cents: 3,
            error_message: 'Cancelled by user',
            // Phase 5E-5: Contract Surfacing
            pre_run: { stages_planned: 6, memory_injection: true, budget_mode: 'enforced' },
            constraints: { budget_passed: true, rate_limit_passed: false, policy_passed: true },
            cost_estimated_cents: 15,
            outcome_reason: 'User-initiated cancellation at stage 1/6',
          },
        ],
        total: 127,
        page: 1,
        per_page: 20,
      };
    },
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
          <div className="text-sm text-slate-400">Total Executions</div>
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
          <div className="text-sm text-slate-400">Total Cost</div>
          <div className="text-2xl font-bold text-white">
            ${(executions.reduce((sum, r) => sum + r.cost_cents, 0) / 100).toFixed(2)}
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
                  <th className="p-4">Execution ID</th>
                  <th className="p-4">Skill</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">Duration</th>
                  <th className="p-4">Cost</th>
                  <th className="p-4">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-border">
                {executions.map((execution) => {
                  const statusConfig = STATUS_CONFIG[execution.status];
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
                      <td className="p-4 text-white">{execution.skill_name}</td>
                      <td className="p-4">
                        <span className={`
                          px-2 py-1 rounded border text-xs font-medium bg-transparent
                          ${statusConfig.color} ${statusConfig.border}
                        `}>
                          {statusConfig.label}
                        </span>
                      </td>
                      <td className="p-4 text-sm text-slate-400">
                        {formatDuration(execution.started_at, execution.ended_at)}
                      </td>
                      <td className="p-4 text-sm text-slate-300">
                        ${(execution.cost_cents / 100).toFixed(2)}
                      </td>
                      <td className="p-4 text-sm text-slate-400">
                        {formatTime(execution.started_at)}
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
 * Execution Details Panel - Shows outcome with Phase 5E-5 Contract Surfacing
 *
 * Displays:
 * - PRE-RUN: Stages Planned, Memory Injection, Budget Mode
 * - CONSTRAINTS: Budget check, Rate Limit check, Policy check
 * - COST: Estimated vs Actual with delta
 * - OUTCOME: Final state with reason
 */
function ExecutionDetailsPanel({ execution, onClose }: { execution: ExecutionSummary; onClose: () => void }) {
  const statusConfig = STATUS_CONFIG[execution.status];
  const costDelta = execution.cost_cents - execution.cost_estimated_cents;
  const costDeltaPercent = execution.cost_estimated_cents > 0
    ? ((costDelta / execution.cost_estimated_cents) * 100).toFixed(0)
    : '0';

  return (
    <div className="bg-navy-surface rounded-xl border border-navy-border p-4 sticky top-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-white">Execution Details</h3>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>

      <div className="space-y-4">
        {/* Execution ID */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Execution ID</div>
          <div className="font-mono text-sm text-slate-300 bg-navy-inset rounded px-2 py-1">
            {execution.run_id}
          </div>
        </div>

        {/* Phase 5E-5: PRE-RUN SUMMARY */}
        <div className="pt-4 border-t border-navy-border">
          <div className="text-xs text-blue-400 font-bold uppercase tracking-wide mb-3">
            PRE-RUN SUMMARY
          </div>
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Stages Planned</span>
              <span className="text-white font-medium">{execution.pre_run.stages_planned}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Memory Injection</span>
              <span className={execution.pre_run.memory_injection ? 'text-green-400' : 'text-slate-500'}>
                {execution.pre_run.memory_injection ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Budget Mode</span>
              <span className={execution.pre_run.budget_mode === 'enforced' ? 'text-green-400' : 'text-amber-400'}>
                {execution.pre_run.budget_mode.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        {/* Phase 5E-5: CONSTRAINTS */}
        <div className="pt-4 border-t border-navy-border">
          <div className="text-xs text-yellow-400 font-bold uppercase tracking-wide mb-3">
            CONSTRAINTS
          </div>
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Budget</span>
              <span className={execution.constraints.budget_passed ? 'text-green-400' : 'text-red-400'}>
                {execution.constraints.budget_passed ? '✓ Passed' : '✗ Failed'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Rate Limit</span>
              <span className={execution.constraints.rate_limit_passed ? 'text-green-400' : 'text-red-400'}>
                {execution.constraints.rate_limit_passed ? '✓ Passed' : '✗ Failed'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Policy</span>
              <span className={execution.constraints.policy_passed ? 'text-green-400' : 'text-red-400'}>
                {execution.constraints.policy_passed ? '✓ Passed' : '✗ Failed'}
              </span>
            </div>
          </div>
        </div>

        {/* Phase 5E-5: COST */}
        <div className="pt-4 border-t border-navy-border">
          <div className="text-xs text-purple-400 font-bold uppercase tracking-wide mb-3">
            COST
          </div>
          <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Estimated</span>
              <span className="text-slate-300">${(execution.cost_estimated_cents / 100).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Actual</span>
              <span className="text-white font-bold">${(execution.cost_cents / 100).toFixed(2)}</span>
            </div>
            <div className="flex justify-between text-sm pt-2 border-t border-purple-500/20">
              <span className="text-slate-400">Difference</span>
              <span className={costDelta > 0 ? 'text-amber-400' : costDelta < 0 ? 'text-green-400' : 'text-slate-400'}>
                {costDelta > 0 ? '+' : ''}{costDelta}¢ ({costDelta > 0 ? '+' : ''}{costDeltaPercent}%)
              </span>
            </div>
          </div>
        </div>

        {/* Phase 5E-5: OUTCOME */}
        <div className="pt-4 border-t border-navy-border">
          <div className="text-xs text-green-400 font-bold uppercase tracking-wide mb-3">
            OUTCOME
          </div>
          <div className={`rounded-lg p-3 ${
            execution.status === 'completed' ? 'bg-green-500/10 border border-green-500/30' :
            execution.status === 'failed' ? 'bg-red-500/10 border border-red-500/30' :
            execution.status === 'cancelled' ? 'bg-slate-500/10 border border-slate-500/30' :
            'bg-blue-500/10 border border-blue-500/30'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              <span className={`
                inline-block px-2 py-1 rounded border text-xs font-medium bg-transparent
                ${statusConfig.color} ${statusConfig.border}
              `}>
                {statusConfig.label}
              </span>
            </div>
            {execution.outcome_reason && (
              <p className="text-sm text-slate-300">{execution.outcome_reason}</p>
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
              <span className="text-slate-400">Skill</span>
              <span className="text-white">{execution.skill_name}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Started</span>
              <span className="text-slate-300">{formatTime(execution.started_at)}</span>
            </div>
            {execution.ended_at && (
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Ended</span>
                <span className="text-slate-300">{formatTime(execution.ended_at)}</span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Duration</span>
              <span className="text-white font-medium">{formatDuration(execution.started_at, execution.ended_at)}</span>
            </div>
          </div>
        </div>

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
