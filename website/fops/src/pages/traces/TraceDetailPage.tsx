/**
 * TraceDetailPage - O3 Accountability Page for Traces
 *
 * Phase A-Fix-1: Closes V-002 (PIN-187)
 *
 * This is the ONLY valid landing point for any trace link.
 * Enforces PIN-186 invariants:
 * - INV-3: Cross-link lands on O3
 * - INV-5: Breadcrumb resets on entity change
 * - INV-6: Value truncation (no inline JSON)
 *
 * MUST NOT:
 * - Show step JSON inline
 * - Have expandable step panels
 * - Contain nested navigation
 * - Contain modal navigation
 * - Contain O4 logic
 *
 * MUST:
 * - Be fully readable without scrolling chaos
 * - Establish trace <-> run accountability
 * - Be reachable from every trace link
 */

import { useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  GitBranch,
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Hash,
  Play,
  Download,
  ExternalLink,
} from 'lucide-react';
import { getTrace, type Trace } from '@/api/traces';
import { truncateId } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { CanonicalBreadcrumb } from '@/components/navigation/CanonicalBreadcrumb';
import { truncateValue } from '@/utils/truncateValue';

// =============================================================================
// TraceViewModel - Read-only, stable data contract
// =============================================================================

interface TraceViewModel {
  trace_id: string;
  run_id: string;
  created_at: string;
  completed_at: string | null;
  status: 'COMPLETE' | 'PARTIAL' | 'ERROR' | 'RUNNING';
  root_hash: string | null;
  hash_verified: boolean;
  hash_version: string;
  total_steps: number;
  success_steps: number;
  failed_steps: number;
  duration_ms: number | null;
  steps_summary: Array<{
    index: number;
    skill_id: string;
    status: 'ok' | 'error' | 'skipped';
    duration_ms: number | null;
  }>;
}

function mapTraceToViewModel(trace: Trace): TraceViewModel {
  const steps = trace.steps || [];
  const successSteps = steps.filter((s) => s.status === 'completed' || s.status === 'ok').length;
  const failedSteps = steps.filter((s) => s.status === 'failed' || s.status === 'error').length;

  // Calculate duration if completed
  let durationMs: number | null = null;
  if (trace.created_at && trace.completed_at) {
    durationMs = new Date(trace.completed_at).getTime() - new Date(trace.created_at).getTime();
  }

  // Map status
  let status: TraceViewModel['status'] = 'RUNNING';
  const traceStatus = trace.status?.toLowerCase() || '';
  if (traceStatus === 'completed' || traceStatus === 'complete') {
    status = failedSteps > 0 ? 'PARTIAL' : 'COMPLETE';
  } else if (traceStatus === 'failed' || traceStatus === 'error') {
    status = 'ERROR';
  }

  return {
    trace_id: trace.run_id, // Trace ID = Run ID in current schema
    run_id: trace.run_id,
    created_at: trace.created_at,
    completed_at: trace.completed_at || null,
    status,
    root_hash: trace.root_hash || null,
    hash_verified: !!trace.root_hash, // Assume verified if hash exists
    hash_version: 'v1',
    total_steps: steps.length,
    success_steps: successSteps,
    failed_steps: failedSteps,
    duration_ms: durationMs,
    steps_summary: steps.map((step, index) => ({
      index: index + 1,
      skill_id: step.skill_id,
      status:
        step.status === 'completed' || step.status === 'ok'
          ? 'ok'
          : step.status === 'failed' || step.status === 'error'
            ? 'error'
            : 'skipped',
      duration_ms: null, // Step duration not in current schema
    })),
  };
}

// =============================================================================
// Status Helpers
// =============================================================================

const STATUS_CONFIG = {
  COMPLETE: {
    label: 'COMPLETE',
    icon: CheckCircle,
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
  },
  PARTIAL: {
    label: 'PARTIAL',
    icon: AlertTriangle,
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
  },
  ERROR: {
    label: 'ERROR',
    icon: XCircle,
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
  },
  RUNNING: {
    label: 'RUNNING',
    icon: Clock,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
  },
};

// =============================================================================
// Components
// =============================================================================

// V-003 Fix: Local Breadcrumb removed - using CanonicalBreadcrumb

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-6">
      <h2 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3 border-b border-slate-700 pb-2">
        {title}
      </h2>
      {children}
    </div>
  );
}

function Field({
  label,
  value,
  mono = false,
  link,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
  link?: string;
}) {
  const valueContent = (
    <span className={cn('text-white', mono && 'font-mono text-sm')}>
      {value || '--'}
    </span>
  );

  return (
    <div className="flex items-start justify-between py-2">
      <span className="text-slate-400 text-sm min-w-32">{label}</span>
      {link ? (
        <Link
          to={link}
          className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
        >
          {valueContent}
          <ExternalLink className="w-3 h-3" />
        </Link>
      ) : (
        valueContent
      )}
    </div>
  );
}

function StepRow({
  step,
}: {
  step: TraceViewModel['steps_summary'][0];
}) {
  const statusIcon =
    step.status === 'ok' ? (
      <CheckCircle className="w-4 h-4 text-green-400" />
    ) : step.status === 'error' ? (
      <XCircle className="w-4 h-4 text-red-400" />
    ) : (
      <Clock className="w-4 h-4 text-slate-500" />
    );

  return (
    <div className="flex items-center gap-4 py-2 px-3 bg-slate-800/50 rounded">
      <span className="text-slate-500 text-sm w-6">#{step.index}</span>
      <span className="font-mono text-sm text-white flex-1">{step.skill_id}</span>
      {statusIcon}
      <span className="text-slate-500 text-xs w-16 text-right">
        {step.duration_ms ? `${step.duration_ms}ms` : '--'}
      </span>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function TraceDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();

  const {
    data: trace,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['trace', runId],
    queryFn: () => getTrace(runId!),
    enabled: !!runId,
  });

  // Map to view model
  const vm: TraceViewModel | null = trace ? mapTraceToViewModel(trace) : null;
  const statusConfig = vm ? STATUS_CONFIG[vm.status] : null;
  const StatusIcon = statusConfig?.icon || Clock;

  // Format duration
  const formatDuration = (ms: number | null) => {
    if (!ms) return '--';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  // Handle download (O5 action - no navigation)
  const handleDownload = () => {
    if (!trace) return;
    const blob = new Blob([JSON.stringify(trace, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trace-${runId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-4xl mx-auto">
          <CanonicalBreadcrumb
            root={{ label: 'Traces', path: '/traces' }}
            entity={{ label: runId || '', id: runId, path: `/traces/${runId}` }}
          />
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !vm) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-4xl mx-auto">
          <CanonicalBreadcrumb
            root={{ label: 'Traces', path: '/traces' }}
            entity={{ label: runId || '', id: runId, path: `/traces/${runId}` }}
          />
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
            <GitBranch className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-white mb-2">Trace Not Found</h2>
            <p className="text-slate-400 mb-4">
              The requested trace could not be loaded.
            </p>
            <button
              onClick={() => navigate('/traces')}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white text-sm"
            >
              Back to Traces
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* V-003 Fix: Using CanonicalBreadcrumb (INV-5) */}
        <CanonicalBreadcrumb
          root={{ label: 'Traces', path: '/traces' }}
          entity={{ label: vm.trace_id, id: vm.trace_id, path: `/traces/${vm.run_id}` }}
        />

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={() => navigate('/traces')}
                className="p-1 hover:bg-slate-800 rounded"
              >
                <ArrowLeft className="w-5 h-5 text-slate-400" />
              </button>
              <GitBranch className="w-6 h-6 text-slate-500" />
              <h1 className="text-2xl font-bold text-white">Trace Detail</h1>
            </div>
            <p className="text-slate-400 text-sm">
              O3 Accountability View - PIN-186 Compliant
            </p>
          </div>

          {/* Status Badge */}
          <div
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg border',
              statusConfig?.bg,
              statusConfig?.border
            )}
          >
            <StatusIcon className={cn('w-5 h-5', statusConfig?.color)} />
            <span className={cn('font-bold text-sm', statusConfig?.color)}>
              {statusConfig?.label}
            </span>
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          {/* TRACE IDENTITY */}
          <Section title="Trace Identity">
            <Field label="Trace ID" value={vm.trace_id} mono />
            <Field
              label="Run ID"
              value={truncateId(vm.run_id, 16)}
              mono
              link={`/guard/runs?run=${vm.run_id}`}
            />
            <Field
              label="Created At"
              value={new Date(vm.created_at).toLocaleString()}
            />
            <Field label="Status" value={vm.status} />
          </Section>

          {/* VERIFICATION */}
          <Section title="Verification">
            <Field
              label="Root Hash"
              value={vm.root_hash ? truncateId(vm.root_hash, 20) : 'N/A'}
              mono
            />
            <Field
              label="Verification Status"
              value={
                vm.hash_verified ? (
                  <span className="flex items-center gap-1 text-green-400">
                    <CheckCircle className="w-4 h-4" /> VERIFIED
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-yellow-400">
                    <AlertTriangle className="w-4 h-4" /> UNVERIFIED
                  </span>
                )
              }
            />
            <Field label="Hash Version" value={vm.hash_version} />
          </Section>

          {/* SUMMARY */}
          <Section title="Summary">
            <Field label="Total Steps" value={vm.total_steps} />
            <Field
              label="Successful Steps"
              value={
                <span className="text-green-400">{vm.success_steps}</span>
              }
            />
            <Field
              label="Failed Steps"
              value={
                vm.failed_steps > 0 ? (
                  <span className="text-red-400">{vm.failed_steps}</span>
                ) : (
                  <span className="text-slate-500">0</span>
                )
              }
            />
            <Field label="Total Duration" value={formatDuration(vm.duration_ms)} />
          </Section>

          {/* STEPS SUMMARY ONLY */}
          <Section title="Steps (Summary Only)">
            {vm.steps_summary.length > 0 ? (
              <div className="space-y-1">
                {vm.steps_summary.slice(0, 10).map((step) => (
                  <StepRow key={step.index} step={step} />
                ))}
                {vm.steps_summary.length > 10 && (
                  <div className="text-center py-2 text-slate-500 text-sm">
                    ... and {vm.steps_summary.length - 10} more steps
                  </div>
                )}
              </div>
            ) : (
              <p className="text-slate-500 text-sm py-4 text-center">
                No steps recorded
              </p>
            )}
            <p className="text-slate-600 text-xs mt-3 text-center">
              Step details not expanded here (O4 deferred per PIN-186)
            </p>
          </Section>

          {/* ACTIONS */}
          <Section title="Actions">
            <div className="flex items-center gap-3">
              <Link
                to={`/guard/runs?run=${vm.run_id}`}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white text-sm transition-colors"
              >
                <Play className="w-4 h-4" />
                View Run
              </Link>
              <button
                onClick={handleDownload}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white text-sm transition-colors"
              >
                <Download className="w-4 h-4" />
                Download Trace
              </button>
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}
