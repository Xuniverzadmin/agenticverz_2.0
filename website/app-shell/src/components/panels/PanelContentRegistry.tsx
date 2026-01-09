/**
 * Panel Content Registry - SDSR Data Binding
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console
 * Temporal:
 *   Trigger: runtime (panel render)
 *   Execution: async (API fetch)
 * Role: Bind real API data to projection-driven panels
 * Reference: PIN-370 (SDSR Pipeline), L2.1 UI Projection
 *
 * ARCHITECTURE:
 * - DomainPage provides the structure (subdomain → topic tabs → panels)
 * - FullPanelSurface renders panels using this registry
 * - Each panel_id maps to a content renderer that fetches real data
 *
 * SDSR GATE: Panels with registered content show real data
 * Panels without registration show the placeholder
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchActivityRuns, type RunSummary } from '@/api/activity';
import { fetchIncidents, fetchIncidentsMetrics, type IncidentSummary } from '@/api/incidents';
import { fetchProposals, approveProposal, rejectProposal, type ProposalSummary } from '@/api/proposals';
import { getTraces, getTrace, type Trace, type TraceStep, type LogLevel } from '@/api/traces';
import type { NormalizedPanel } from '@/contracts/ui_projection_loader';
import { useAuthStore } from '@/stores/authStore';

// =============================================================================
// Content Renderer Interface
// =============================================================================

export interface PanelContentProps {
  panel: NormalizedPanel;
}

// =============================================================================
// Activity Domain Content Renderers
// =============================================================================

/**
 * Active Runs Summary (O1) - Shows count of running executions
 */
function ActiveRunsSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['activity', 'runs', 'running'],
    queryFn: () => fetchActivityRuns({ status: 'running', include_synthetic: true }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load active runs</div>;
  }

  const runningCount = data?.runs?.length ?? 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-blue-400">{runningCount}</div>
        <div className="text-slate-400 text-sm">
          {runningCount === 1 ? 'run' : 'runs'} currently active
        </div>
      </div>
      {runningCount > 0 && data?.runs && (
        <div className="text-xs text-slate-500">
          Latest: {data.runs[0]?.goal?.slice(0, 50)}...
        </div>
      )}
    </div>
  );
}

/**
 * Completed Runs Summary (O1) - Shows count of completed executions
 */
function CompletedRunsSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['activity', 'runs', 'completed'],
    queryFn: () => fetchActivityRuns({ status: 'completed', include_synthetic: true }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load completed runs</div>;
  }

  const completedCount = data?.total ?? 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-green-400">{completedCount}</div>
        <div className="text-slate-400 text-sm">
          {completedCount === 1 ? 'run' : 'runs'} completed
        </div>
      </div>
    </div>
  );
}

/**
 * Run Details Summary (O1) - Shows total run count
 */
function RunDetailsSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['activity', 'runs', 'all'],
    queryFn: () => fetchActivityRuns({ include_synthetic: true }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load run summary</div>;
  }

  const totalCount = data?.total ?? 0;
  const syntheticCount = data?.runs?.filter(r => r.is_synthetic).length ?? 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-white">{totalCount}</div>
        <div className="text-slate-400 text-sm">total runs</div>
      </div>
      {syntheticCount > 0 && (
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 rounded border text-xs font-medium bg-purple-500/10 text-purple-400 border-purple-400/40">
            SDSR
          </span>
          <span className="text-xs text-purple-300">{syntheticCount} synthetic</span>
        </div>
      )}
    </div>
  );
}

/**
 * Active Runs List (O2) - Shows list of running executions
 */
function ActiveRunsList({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['activity', 'runs', 'running', 'list'],
    queryFn: () => fetchActivityRuns({ status: 'running', include_synthetic: true, per_page: 10 }),
    refetchInterval: 15000,
    staleTime: 5000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading active runs...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load active runs</div>;
  }

  const runs = data?.runs ?? [];

  if (runs.length === 0) {
    return <div className="text-slate-500 text-sm">No active runs</div>;
  }

  return (
    <div className="space-y-2">
      {runs.map((run) => (
        <RunListItem key={run.run_id} run={run} />
      ))}
    </div>
  );
}

/**
 * Completed Runs List (O2) - Shows list of completed executions
 */
function CompletedRunsList({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['activity', 'runs', 'all', 'list'],
    queryFn: () => fetchActivityRuns({ include_synthetic: true, per_page: 10 }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading runs...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load runs</div>;
  }

  const runs = data?.runs ?? [];

  if (runs.length === 0) {
    return <div className="text-slate-500 text-sm">No runs found</div>;
  }

  return (
    <div className="space-y-2">
      {runs.map((run) => (
        <RunListItem key={run.run_id} run={run} />
      ))}
      {data && data.total > runs.length && (
        <div className="text-xs text-slate-500 pt-2">
          Showing {runs.length} of {data.total} runs
        </div>
      )}
    </div>
  );
}

/**
 * Shared Run List Item Component
 */
function RunListItem({ run }: { run: RunSummary }) {
  const statusColors: Record<string, string> = {
    completed: 'text-green-400 border-green-400/40',
    failed: 'text-red-400 border-red-400/40',
    running: 'text-blue-400 border-blue-400/40',
    queued: 'text-yellow-400 border-yellow-400/40',
    pending: 'text-orange-400 border-orange-400/40',
  };

  const statusColor = statusColors[run.status] || 'text-slate-400 border-slate-600';

  return (
    <div className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-slate-400">
            {run.run_id.slice(0, 8)}...
          </span>
          <span className={`px-2 py-0.5 rounded border text-xs font-medium bg-transparent ${statusColor}`}>
            {run.status}
          </span>
          {run.is_synthetic && (
            <span className="px-2 py-0.5 rounded border text-xs font-medium bg-purple-500/10 text-purple-400 border-purple-400/40">
              SDSR
            </span>
          )}
        </div>
        <div className="text-sm text-white mt-1 truncate">
          {run.goal.length > 60 ? `${run.goal.slice(0, 60)}...` : run.goal}
        </div>
      </div>
      <div className="text-xs text-slate-500 ml-4">
        {new Date(run.created_at).toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })}
      </div>
    </div>
  );
}

// =============================================================================
// Incidents Domain Content Renderers
// =============================================================================

/**
 * Open Incidents Summary (O1) - Shows count of open incidents
 */
function OpenIncidentsSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'metrics'],
    queryFn: () => fetchIncidentsMetrics(true),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load incident metrics</div>;
  }

  const openCount = data?.total_open ?? 0;
  const bySeverity = data?.by_severity;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-orange-400">{openCount}</div>
        <div className="text-slate-400 text-sm">
          open {openCount === 1 ? 'incident' : 'incidents'}
        </div>
      </div>
      {bySeverity && (bySeverity.critical > 0 || bySeverity.high > 0) && (
        <div className="flex items-center gap-2">
          {bySeverity.critical > 0 && (
            <span className="px-2 py-1 rounded border text-xs font-medium bg-red-500/10 text-red-400 border-red-400/40">
              {bySeverity.critical} CRITICAL
            </span>
          )}
          {bySeverity.high > 0 && (
            <span className="px-2 py-1 rounded border text-xs font-medium bg-orange-500/10 text-orange-400 border-orange-400/40">
              {bySeverity.high} HIGH
            </span>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Incident Summary (O1) - Shows incident counts by category
 */
function IncidentSummaryPanel({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'all'],
    queryFn: () => fetchIncidents({ include_synthetic: true }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load incidents</div>;
  }

  const totalCount = data?.total ?? 0;
  const syntheticCount = data?.incidents?.filter(i => i.is_synthetic).length ?? 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-white">{totalCount}</div>
        <div className="text-slate-400 text-sm">total incidents</div>
      </div>
      {syntheticCount > 0 && (
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 rounded border text-xs font-medium bg-purple-500/10 text-purple-400 border-purple-400/40">
            SDSR
          </span>
          <span className="text-xs text-purple-300">{syntheticCount} synthetic</span>
        </div>
      )}
    </div>
  );
}

/**
 * Resolved Incidents Summary (O1) - Shows count of resolved incidents
 */
function ResolvedIncidentsSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'metrics'],
    queryFn: () => fetchIncidentsMetrics(true),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load incident metrics</div>;
  }

  const resolvedCount = data?.total_resolved ?? 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-green-400">{resolvedCount}</div>
        <div className="text-slate-400 text-sm">
          resolved {resolvedCount === 1 ? 'incident' : 'incidents'}
        </div>
      </div>
    </div>
  );
}

/**
 * Open Incidents List (O2) - Shows list of open incidents
 */
function OpenIncidentsList({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'open', 'list'],
    queryFn: () => fetchIncidents({
      status: 'OPEN',
      include_synthetic: true,
      per_page: 10
    }),
    refetchInterval: 15000,
    staleTime: 5000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading open incidents...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load open incidents</div>;
  }

  const incidents = data?.incidents ?? [];

  if (incidents.length === 0) {
    return <div className="text-slate-500 text-sm">No open incidents</div>;
  }

  return (
    <div className="space-y-2">
      {incidents.map((incident) => (
        <IncidentListItem key={incident.id} incident={incident} />
      ))}
      {data && data.total > incidents.length && (
        <div className="text-xs text-slate-500 pt-2">
          Showing {incidents.length} of {data.total} incidents
        </div>
      )}
    </div>
  );
}

/**
 * Resolved Incidents List (O2) - Shows list of resolved incidents
 */
function ResolvedIncidentsList({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'resolved', 'list'],
    queryFn: () => fetchIncidents({
      status: 'RESOLVED',
      include_synthetic: true,
      per_page: 10
    }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading resolved incidents...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load resolved incidents</div>;
  }

  const incidents = data?.incidents ?? [];

  if (incidents.length === 0) {
    return <div className="text-slate-500 text-sm">No resolved incidents</div>;
  }

  return (
    <div className="space-y-2">
      {incidents.map((incident) => (
        <IncidentListItem key={incident.id} incident={incident} />
      ))}
      {data && data.total > incidents.length && (
        <div className="text-xs text-slate-500 pt-2">
          Showing {incidents.length} of {data.total} incidents
        </div>
      )}
    </div>
  );
}

/**
 * Shared Incident List Item Component
 */
function IncidentListItem({ incident }: { incident: IncidentSummary }) {
  const severityColors: Record<string, string> = {
    CRITICAL: 'text-red-400 border-red-400/40 bg-red-500/10',
    HIGH: 'text-orange-400 border-orange-400/40 bg-orange-500/10',
    MEDIUM: 'text-yellow-400 border-yellow-400/40 bg-yellow-500/10',
    LOW: 'text-blue-400 border-blue-400/40 bg-blue-500/10',
  };

  const statusColors: Record<string, string> = {
    OPEN: 'text-orange-400 border-orange-400/40',
    ACKNOWLEDGED: 'text-blue-400 border-blue-400/40',
    INVESTIGATING: 'text-purple-400 border-purple-400/40',
    RESOLVED: 'text-green-400 border-green-400/40',
    CLOSED: 'text-slate-400 border-slate-600',
  };

  const severityColor = severityColors[incident.severity] || 'text-slate-400 border-slate-600';
  const statusColor = statusColors[incident.status] || 'text-slate-400 border-slate-600';

  return (
    <div className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-xs text-slate-400">
            {incident.id.slice(0, 12)}...
          </span>
          <span className={`px-2 py-0.5 rounded border text-xs font-medium ${severityColor}`}>
            {incident.severity}
          </span>
          <span className={`px-2 py-0.5 rounded border text-xs font-medium bg-transparent ${statusColor}`}>
            {incident.status}
          </span>
          {incident.is_synthetic && (
            <span className="px-2 py-0.5 rounded border text-xs font-medium bg-purple-500/10 text-purple-400 border-purple-400/40">
              SDSR
            </span>
          )}
        </div>
        <div className="text-sm text-white mt-1 truncate">
          {incident.title}
        </div>
        {incident.error_code && (
          <div className="text-xs text-slate-500 mt-1 font-mono">
            {incident.error_code}
          </div>
        )}
      </div>
      <div className="text-xs text-slate-500 ml-4">
        {new Date(incident.created_at).toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })}
      </div>
    </div>
  );
}

// =============================================================================
// Logs Domain Content Renderers - EXECUTION_TRACES (L2.1 Intent: PIN-378)
// =============================================================================

/**
 * Trace Summary (O1) - Shows trace stats with SDSR filtering
 */
function TraceSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['traces', 'all'],
    queryFn: () => getTraces({ limit: 100 }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load trace summary</div>;
  }

  const traces = data ?? [];
  const totalCount = traces.length;
  const syntheticCount = traces.filter(t => t.is_synthetic).length;

  // Count by status
  const completedCount = traces.filter(t => t.status === 'completed').length;
  const runningCount = traces.filter(t => t.status === 'running').length;
  const failedCount = traces.filter(t => t.status === 'failed').length;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-white">{totalCount}</div>
        <div className="text-slate-400 text-sm">total traces</div>
      </div>
      <div className="flex items-center gap-3 flex-wrap">
        {runningCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-blue-500/10 text-blue-400 border-blue-400/40">
            {runningCount} running
          </span>
        )}
        {completedCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-green-500/10 text-green-400 border-green-400/40">
            {completedCount} completed
          </span>
        )}
        {failedCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-red-500/10 text-red-400 border-red-400/40">
            {failedCount} failed
          </span>
        )}
      </div>
      {syntheticCount > 0 && (
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 rounded border text-xs font-medium bg-purple-500/10 text-purple-400 border-purple-400/40">
            SDSR
          </span>
          <span className="text-xs text-purple-300">{syntheticCount} synthetic</span>
        </div>
      )}
    </div>
  );
}

/**
 * Trace List (O2) - Shows list of traces with SDSR markers
 */
function TraceList({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['traces', 'list'],
    queryFn: () => getTraces({ limit: 20 }),
    refetchInterval: 15000,
    staleTime: 5000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading traces...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load traces</div>;
  }

  const traces = data ?? [];

  if (traces.length === 0) {
    return <div className="text-slate-500 text-sm">No traces found</div>;
  }

  return (
    <div className="space-y-2">
      {traces.map((trace) => (
        <TraceListItem key={trace.trace_id || trace.run_id} trace={trace} />
      ))}
    </div>
  );
}

/**
 * Trace Detail (O3) - Shows trace with step timeline
 */
function TraceDetail({ panel }: PanelContentProps) {
  // In a real implementation, this would get the trace ID from context
  // For now, we show the most recent trace with steps
  const { data, isLoading, error } = useQuery({
    queryKey: ['traces', 'latest-detail'],
    queryFn: async () => {
      const traces = await getTraces({ limit: 1 });
      if (traces.length === 0) return null;
      return getTrace(traces[0].run_id);
    },
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading trace details...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load trace details</div>;
  }

  if (!data) {
    return <div className="text-slate-500 text-sm">No trace selected</div>;
  }

  const trace = data;
  const steps = trace.steps ?? [];

  return (
    <div className="space-y-4">
      {/* Trace header */}
      <div className="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-xs text-slate-400">
            {trace.run_id.slice(0, 12)}...
          </span>
          <TraceStatusBadge status={trace.status} />
          {trace.is_synthetic && (
            <span className="px-2 py-0.5 rounded border text-xs font-medium bg-purple-500/10 text-purple-400 border-purple-400/40">
              SDSR
            </span>
          )}
        </div>
        {trace.incident_id && (
          <div className="text-xs text-orange-400 mt-2 font-mono">
            Incident: {trace.incident_id.slice(0, 16)}...
          </div>
        )}
        <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
          <span>{trace.total_steps ?? steps.length} steps</span>
          {trace.total_duration_ms && (
            <span>{(trace.total_duration_ms / 1000).toFixed(2)}s</span>
          )}
          {trace.total_cost_cents !== undefined && (
            <span>${(trace.total_cost_cents / 100).toFixed(4)}</span>
          )}
        </div>
      </div>

      {/* Step timeline */}
      {steps.length > 0 && (
        <div className="space-y-1">
          <div className="text-xs text-slate-400 font-medium mb-2">Step Timeline</div>
          {steps.map((step, idx) => (
            <StepTimelineItem key={step.step_index ?? idx} step={step} />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Shared Trace List Item Component
 */
function TraceListItem({ trace }: { trace: Trace }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-xs text-slate-400">
            {trace.run_id.slice(0, 8)}...
          </span>
          <TraceStatusBadge status={trace.status} />
          {trace.is_synthetic && (
            <span className="px-2 py-0.5 rounded border text-xs font-medium bg-purple-500/10 text-purple-400 border-purple-400/40">
              SDSR
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
          <span>{trace.total_steps ?? 0} steps</span>
          {trace.total_duration_ms && (
            <span>{(trace.total_duration_ms / 1000).toFixed(2)}s</span>
          )}
          {trace.incident_id && (
            <span className="text-orange-400 font-mono">
              inc: {trace.incident_id.slice(0, 8)}
            </span>
          )}
        </div>
      </div>
      <div className="text-xs text-slate-500 ml-4">
        {new Date(trace.started_at || trace.created_at).toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })}
      </div>
    </div>
  );
}

/**
 * Trace Status Badge Component
 */
function TraceStatusBadge({ status }: { status: string }) {
  const statusColors: Record<string, string> = {
    completed: 'text-green-400 border-green-400/40',
    running: 'text-blue-400 border-blue-400/40',
    failed: 'text-red-400 border-red-400/40',
    pending: 'text-yellow-400 border-yellow-400/40',
  };

  const color = statusColors[status] || 'text-slate-400 border-slate-600';

  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-medium bg-transparent ${color}`}>
      {status}
    </span>
  );
}

/**
 * Step Timeline Item Component (PIN-378 SDSR extension)
 */
function StepTimelineItem({ step }: { step: TraceStep }) {
  const levelColors: Record<LogLevel, string> = {
    INFO: 'text-slate-400 border-slate-600',
    WARN: 'text-yellow-400 border-yellow-400/40',
    ERROR: 'text-red-400 border-red-400/40',
  };

  const levelColor = levelColors[step.level] || 'text-slate-400 border-slate-600';

  const sourceColors: Record<string, string> = {
    engine: 'text-blue-400',
    external: 'text-cyan-400',
    replay: 'text-purple-400',
  };

  const sourceColor = sourceColors[step.source] || 'text-slate-400';

  return (
    <div className="flex items-center gap-2 p-2 bg-gray-800/50 rounded border border-gray-700/30">
      <span className="text-xs font-mono text-slate-500 w-6">
        {String(step.step_index).padStart(2, '0')}
      </span>
      <span className={`px-1.5 py-0.5 rounded border text-xs font-medium bg-transparent ${levelColor}`}>
        {step.level}
      </span>
      <span className={`text-xs ${sourceColor}`}>
        {step.source}
      </span>
      <span className="text-xs text-white flex-1 truncate">
        {step.skill_name}
      </span>
      <span className="text-xs text-slate-500">
        {step.duration_ms}ms
      </span>
      {step.retry_count > 0 && (
        <span className="px-1.5 py-0.5 rounded text-xs bg-yellow-500/10 text-yellow-400">
          R{step.retry_count}
        </span>
      )}
    </div>
  );
}

// =============================================================================
// Policies Domain Content Renderers - PROPOSALS (L2.1 Intent: PIN-373)
// =============================================================================

/**
 * Pending Proposals Summary (O1) - Shows count of proposals by status
 */
function PendingProposalsSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['proposals', 'all'],
    queryFn: () => fetchProposals({ limit: 100 }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load proposals</div>;
  }

  const byStatus = data?.by_status ?? {};
  const draftCount = byStatus['draft'] ?? 0;
  const approvedCount = byStatus['approved'] ?? 0;
  const rejectedCount = byStatus['rejected'] ?? 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-yellow-400">{draftCount}</div>
        <div className="text-slate-400 text-sm">
          pending {draftCount === 1 ? 'proposal' : 'proposals'}
        </div>
      </div>
      <div className="flex items-center gap-3">
        {approvedCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-green-500/10 text-green-400 border-green-400/40">
            {approvedCount} approved
          </span>
        )}
        {rejectedCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-red-500/10 text-red-400 border-red-400/40">
            {rejectedCount} rejected
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Proposals List (O2) - Shows list of proposals with approve/reject actions
 */
function ProposalsList({ panel }: PanelContentProps) {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);

  const { data, isLoading, error } = useQuery({
    queryKey: ['proposals', 'list'],
    queryFn: () => fetchProposals({ limit: 20 }),
    refetchInterval: 15000,
    staleTime: 5000,
  });

  // Use authenticated user's email for audit trail
  const reviewedBy = user?.email || user?.id || 'unknown';

  const approveMutation = useMutation({
    mutationFn: (proposalId: string) => approveProposal(proposalId, { reviewed_by: reviewedBy }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
    },
    onError: (err) => {
      console.error('Failed to approve proposal:', err);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (proposalId: string) => rejectProposal(proposalId, { reviewed_by: reviewedBy }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
    },
    onError: (err) => {
      console.error('Failed to reject proposal:', err);
    },
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading proposals...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load proposals</div>;
  }

  const proposals = data?.items ?? [];

  if (proposals.length === 0) {
    return <div className="text-slate-500 text-sm">No proposals found</div>;
  }

  const isProcessing = approveMutation.isPending || rejectMutation.isPending;

  return (
    <div className="space-y-2">
      {proposals.map((proposal) => (
        <ProposalListItem
          key={proposal.id}
          proposal={proposal}
          onApprove={() => approveMutation.mutate(proposal.id)}
          onReject={() => rejectMutation.mutate(proposal.id)}
          isProcessing={isProcessing}
        />
      ))}
      {data && data.total > proposals.length && (
        <div className="text-xs text-slate-500 pt-2">
          Showing {proposals.length} of {data.total} proposals
        </div>
      )}
    </div>
  );
}

/**
 * Proposal List Item Component
 */
function ProposalListItem({
  proposal,
  onApprove,
  onReject,
  isProcessing,
}: {
  proposal: ProposalSummary;
  onApprove: () => void;
  onReject: () => void;
  isProcessing: boolean;
}) {
  const statusColors: Record<string, string> = {
    draft: 'text-yellow-400 border-yellow-400/40 bg-yellow-500/10',
    approved: 'text-green-400 border-green-400/40 bg-green-500/10',
    rejected: 'text-red-400 border-red-400/40 bg-red-500/10',
  };

  const typeColors: Record<string, string> = {
    timeout_policy: 'text-orange-400 border-orange-400/40',
    crash_recovery_policy: 'text-red-400 border-red-400/40',
    cost_cap_policy: 'text-blue-400 border-blue-400/40',
    rate_limit_policy: 'text-purple-400 border-purple-400/40',
    retry_policy: 'text-cyan-400 border-cyan-400/40',
    failure_pattern_policy: 'text-pink-400 border-pink-400/40',
  };

  const statusColor = statusColors[proposal.status] || 'text-slate-400 border-slate-600';
  const typeColor = typeColors[proposal.proposal_type] || 'text-slate-400 border-slate-600';

  const isDraft = proposal.status === 'draft';

  return (
    <div className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-xs text-slate-400">
            {proposal.id.slice(0, 8)}...
          </span>
          <span className={`px-2 py-0.5 rounded border text-xs font-medium ${statusColor}`}>
            {proposal.status}
          </span>
          <span className={`px-2 py-0.5 rounded border text-xs font-medium bg-transparent ${typeColor}`}>
            {proposal.proposal_type.replace(/_/g, ' ')}
          </span>
        </div>
        <div className="text-sm text-white mt-1 truncate">
          {proposal.proposal_name}
        </div>
        {proposal.rationale && (
          <div className="text-xs text-slate-500 mt-1 truncate">
            {proposal.rationale.slice(0, 80)}...
          </div>
        )}
      </div>
      <div className="flex items-center gap-2 ml-4">
        {isDraft && (
          <>
            <button
              onClick={onApprove}
              disabled={isProcessing}
              className="px-3 py-1 rounded text-xs font-medium bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-white"
            >
              Approve
            </button>
            <button
              onClick={onReject}
              disabled={isProcessing}
              className="px-3 py-1 rounded text-xs font-medium bg-red-600 hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed text-white"
            >
              Reject
            </button>
          </>
        )}
        <div className="text-xs text-slate-500">
          {proposal.created_at && new Date(proposal.created_at).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Panel Content Registry
// =============================================================================

type ContentRenderer = React.FC<PanelContentProps>;

/**
 * Registry mapping panel_ids to content renderers
 *
 * SDSR GATE CHECK:
 * - If panel_id is in this registry → render real data
 * - If panel_id is NOT in this registry → render placeholder
 */
const PANEL_CONTENT_REGISTRY: Record<string, ContentRenderer> = {
  // Activity Domain - EXECUTIONS Subdomain
  // Topic: ACTIVE_RUNS
  'ACT-EX-AR-O1': ActiveRunsSummary,
  'ACT-EX-AR-O2': ActiveRunsList,

  // Topic: COMPLETED_RUNS
  'ACT-EX-CR-O1': CompletedRunsSummary,
  'ACT-EX-CR-O2': CompletedRunsList,

  // Topic: RUN_DETAILS
  'ACT-EX-RD-O1': RunDetailsSummary,

  // Incidents Domain - ACTIVE_INCIDENTS Subdomain
  // Topic: OPEN_INCIDENTS
  'INC-AI-OI-O1': OpenIncidentsSummary,
  'INC-AI-OI-O2': OpenIncidentsList,

  // Topic: INCIDENT_DETAILS
  'INC-AI-ID-O1': IncidentSummaryPanel,

  // Incidents Domain - HISTORICAL_INCIDENTS Subdomain
  // Topic: RESOLVED_INCIDENTS
  'INC-HI-RI-O1': ResolvedIncidentsSummary,
  'INC-HI-RI-O2': ResolvedIncidentsList,

  // Policies Domain - PROPOSALS Subdomain (L2.1 intent: PIN-373)
  // Topic: PENDING_PROPOSALS
  'POL-PR-PP-O1': PendingProposalsSummary,
  'POL-PR-PP-O2': ProposalsList,

  // Logs Domain - EXECUTION_TRACES Subdomain (L2.1 intent: PIN-378)
  // Topic: TRACE_DETAILS
  'LOG-ET-TD-O1': TraceSummary,
  'LOG-ET-TD-O2': TraceList,
  'LOG-ET-TD-O3': TraceDetail,
};

/**
 * Get content renderer for a panel
 * Returns null if no renderer is registered (panel shows placeholder)
 */
export function getPanelContentRenderer(panelId: string): ContentRenderer | null {
  return PANEL_CONTENT_REGISTRY[panelId] ?? null;
}

/**
 * Check if a panel has registered content (SDSR data binding)
 */
export function hasPanelContent(panelId: string): boolean {
  return panelId in PANEL_CONTENT_REGISTRY;
}

/**
 * PanelContent Component
 * Renders the appropriate content for a panel based on registry
 */
export function PanelContent({ panel }: PanelContentProps) {
  const Renderer = getPanelContentRenderer(panel.panel_id);

  if (!Renderer) {
    // No registered content - show placeholder
    return (
      <div className="bg-gray-900/50 border border-dashed border-gray-600 rounded-lg p-8 text-center">
        <p className="text-gray-500 text-sm">
          Content surface — awaiting backend binding
        </p>
        <p className="text-gray-600 text-xs mt-2 font-mono">
          render_mode: {panel.render_mode} | controls: {panel.control_count}
        </p>
      </div>
    );
  }

  // Render registered content
  return <Renderer panel={panel} />;
}

export default PanelContent;
