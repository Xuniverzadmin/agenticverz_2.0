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

/**
 * Panel Content Registry - SDSR Data Binding
 *
 * RULE-AUTH-UI-001: Clerk is the auth store
 * - Use useUser() for user info (audit trails)
 *
 * Reference: PIN-407, docs/architecture/FRONTEND_AUTH_CONTRACT.md
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useUser } from '@clerk/clerk-react';
import { Activity, CheckCircle, AlertTriangle, AlertOctagon, History, FileCheck, Shield, FilePlus, Archive, DollarSign, Gauge, SlidersHorizontal, Clock, TrendingUp, Info } from 'lucide-react';
import { fetchActivityRuns, fetchActivitySummary, type RunSummary, type ActivitySummaryResponse } from '@/api/activity';
import {
  // Phase 3 Migration: Topic-scoped functions
  fetchActiveIncidents,
  fetchResolvedIncidents,
  // Legacy (kept for backward compatibility)
  fetchIncidents,
  fetchIncidentsMetrics,
  fetchIncidentsSummary,
  // Types
  type IncidentSummary,
  type IncidentsSummaryResponse,
  type TopicScopedIncidentsResponse,
} from '@/api/incidents';
import { fetchProposals, approveProposal, rejectProposal, type ProposalSummary } from '@/api/proposals';
import { getTraces, getTrace, type Trace, type TraceStep, type LogLevel } from '@/api/traces';
import {
  fetchHighlights,
  fetchDecisions,
  fetchCostIntelligence,
  type SystemPulse,
  type DomainCount,
  type DecisionItem,
  type LimitCostItem,
} from '@/api/overview';
import {
  fetchAuditEntries,
  fetchSystemRecords,
  type AuditLedgerItem,
  type SystemRecordItem,
} from '@/api/logs';
import type { NormalizedPanel } from '@/contracts/ui_projection_loader';

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
 * Live LLM Runs Navigation (O1) - Navigation-only panel for Live LLM runs
 *
 * PIN-411 O1 BINDING RULES:
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function LiveRunsNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewLiveRuns = () => {
    navigate('/precus/activity/runs?state=LIVE');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Monitor currently executing LLM runs in real-time.</p>
      </div>
      <button
        onClick={handleViewLiveRuns}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <Activity size={16} />
        View Live LLM Runs
      </button>
    </div>
  );
}

/**
 * Completed LLM Runs Navigation (O1) - Navigation-only panel for Completed LLM runs
 *
 * PIN-411 O1 BINDING RULES:
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function CompletedRunsNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewCompletedRuns = () => {
    navigate('/precus/activity/runs?state=COMPLETED');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Review finished LLM runs and their outcomes.</p>
      </div>
      <button
        onClick={handleViewCompletedRuns}
        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <CheckCircle size={16} />
        View Completed LLM Runs
      </button>
    </div>
  );
}

/**
 * Risk Signals Navigation (O1) - Navigation-only panel for Risk Signals
 *
 * PIN-411 O1 BINDING RULES:
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function RiskSignalsNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewRiskSignals = () => {
    navigate('/precus/activity/runs?risk=true');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">LLM runs with elevated risk levels, policy violations, or incidents.</p>
      </div>
      <button
        onClick={handleViewRiskSignals}
        className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <AlertTriangle size={16} />
        View Risk Signals
      </button>
    </div>
  );
}

/**
 * Active LLM Runs List (O2) - Shows list of running executions
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
 * Completed LLM Runs List (O2) - Shows list of completed executions
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
// Activity Domain - INTERPRETATION PANELS (HIL v1 - PIN-417)
// =============================================================================

/**
 * Activity Summary Briefing (O1) - HIL v1 Interpretation Panel
 *
 * PIN-417 HIL v1 RULES:
 * - This is an INTERPRETATION panel (panel_class: interpretation)
 * - Displays aggregated summary derived from execution data
 * - Read-only: No controls, no mutations
 * - Shows provenance: Where data came from (capability IDs)
 * - Attention reasons are registry-backed (no free strings)
 */
function ActivitySummaryBriefing({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['activity', 'summary', '24h'],
    queryFn: () => fetchActivitySummary({ window: '24h', include_synthetic: true }),
    refetchInterval: 30000,
    staleTime: 15000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading activity summary...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load activity summary</div>;
  }

  if (!data) {
    return <div className="text-slate-500 text-sm">No summary data available</div>;
  }

  const { runs, attention, provenance } = data;
  const hasAttention = attention.at_risk_count > 0;

  // Map reason codes to human-readable labels (registry-backed)
  const reasonLabels: Record<string, string> = {
    long_running: 'Long running',
    near_budget_threshold: 'Near budget threshold',
  };

  return (
    <div className="space-y-4">
      {/* Run Status Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
          <div className="text-xs text-slate-400 font-medium">Total</div>
          <div className="text-2xl font-bold text-white">{runs.total}</div>
          <div className="text-xs text-slate-500 mt-1">runs in {data.window}</div>
        </div>
        <div className="p-3 bg-gray-900/50 rounded-lg border border-blue-400/30">
          <div className="flex items-center gap-1.5">
            <Activity size={12} className="text-blue-400" />
            <span className="text-xs text-blue-400 font-medium">Running</span>
          </div>
          <div className="text-2xl font-bold text-blue-400">{runs.by_status.running}</div>
        </div>
        <div className="p-3 bg-gray-900/50 rounded-lg border border-green-400/30">
          <div className="flex items-center gap-1.5">
            <CheckCircle size={12} className="text-green-400" />
            <span className="text-xs text-green-400 font-medium">Completed</span>
          </div>
          <div className="text-2xl font-bold text-green-400">{runs.by_status.completed}</div>
          {runs.by_status.failed > 0 && (
            <div className="text-xs text-red-400 mt-1">
              {runs.by_status.failed} failed
            </div>
          )}
        </div>
      </div>

      {/* Attention Section */}
      {hasAttention && (
        <div className="p-3 bg-yellow-500/10 rounded-lg border border-yellow-400/30">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-yellow-400" />
            <span className="text-sm font-medium text-yellow-400">
              {attention.at_risk_count} run{attention.at_risk_count !== 1 ? 's' : ''} need attention
            </span>
          </div>
          {attention.reasons.length > 0 && (
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              {attention.reasons.map((reason) => (
                <span
                  key={reason}
                  className="px-2 py-0.5 rounded text-xs bg-yellow-500/20 text-yellow-300 border border-yellow-400/30"
                >
                  {reasonLabels[reason] || reason}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* No Attention - All Clear */}
      {!hasAttention && (
        <div className="p-3 bg-green-500/10 rounded-lg border border-green-400/30">
          <div className="flex items-center gap-2">
            <CheckCircle size={16} className="text-green-400" />
            <span className="text-sm font-medium text-green-400">
              All runs operating normally
            </span>
          </div>
        </div>
      )}

      {/* Provenance Section (HIL v1 requirement) */}
      <div className="pt-3 border-t border-gray-700/50">
        <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-2">
          <Info size={12} />
          <span>Derived from</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {provenance.derived_from.map((capabilityId) => (
            <span
              key={capabilityId}
              className="px-2 py-0.5 rounded text-xs bg-blue-500/10 text-blue-400 border border-blue-400/20 font-mono"
            >
              {capabilityId}
            </span>
          ))}
        </div>
        <div className="text-xs text-slate-600 mt-2">
          Aggregation: {provenance.aggregation} · Generated: {new Date(provenance.generated_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Overview Domain Content Renderers - PROJECTION-ONLY (PIN-413)
// =============================================================================

/**
 * System Status Summary (O1) - Shows system pulse and health status
 *
 * PIN-413 Overview is PROJECTION-ONLY:
 * - Aggregates from existing domain tables
 * - No owned state, read-only
 */
function SystemStatusSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['overview', 'highlights'],
    queryFn: fetchHighlights,
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading system status...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load system status</div>;
  }

  const pulse = data?.pulse;
  if (!pulse) {
    return <div className="text-slate-500 text-sm">No status data</div>;
  }

  const statusConfig: Record<string, { color: string; bg: string; label: string }> = {
    HEALTHY: { color: 'text-green-400', bg: 'bg-green-500/10 border-green-400/40', label: 'System Healthy' },
    ATTENTION_NEEDED: { color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-400/40', label: 'Attention Needed' },
    CRITICAL: { color: 'text-red-400', bg: 'bg-red-500/10 border-red-400/40', label: 'Critical Issues' },
  };

  const config = statusConfig[pulse.status] || statusConfig.HEALTHY;

  return (
    <div className="space-y-4">
      {/* Status hero */}
      <div className={`p-4 rounded-lg border ${config.bg}`}>
        <div className={`text-lg font-semibold ${config.color}`}>
          {config.label}
        </div>
        <div className="text-xs text-slate-400 mt-1">
          {pulse.status === 'HEALTHY'
            ? 'All systems operating normally'
            : pulse.status === 'ATTENTION_NEEDED'
            ? 'Some items require review'
            : 'Immediate action required'}
        </div>
      </div>

      {/* Quick stats */}
      <div className="flex items-center gap-4 text-sm">
        {pulse.active_incidents > 0 && (
          <div className="flex items-center gap-1.5">
            <AlertOctagon size={14} className="text-orange-400" />
            <span className="text-slate-300">{pulse.active_incidents} active incident{pulse.active_incidents !== 1 ? 's' : ''}</span>
          </div>
        )}
        {pulse.pending_decisions > 0 && (
          <div className="flex items-center gap-1.5">
            <FileCheck size={14} className="text-yellow-400" />
            <span className="text-slate-300">{pulse.pending_decisions} pending decision{pulse.pending_decisions !== 1 ? 's' : ''}</span>
          </div>
        )}
        {pulse.recent_breaches > 0 && (
          <div className="flex items-center gap-1.5">
            <AlertTriangle size={14} className="text-red-400" />
            <span className="text-slate-300">{pulse.recent_breaches} breach{pulse.recent_breaches !== 1 ? 'es' : ''} (24h)</span>
          </div>
        )}
        {pulse.active_incidents === 0 && pulse.pending_decisions === 0 && pulse.recent_breaches === 0 && (
          <div className="flex items-center gap-1.5">
            <CheckCircle size={14} className="text-green-400" />
            <span className="text-slate-300">No outstanding items</span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Health Metrics Summary (O1) - Shows domain counts and summary
 *
 * PIN-413 Overview is PROJECTION-ONLY
 */
function HealthMetricsSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['overview', 'highlights'],
    queryFn: fetchHighlights,
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading metrics...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load metrics</div>;
  }

  const domainCounts = data?.domain_counts ?? [];
  const lastActivity = data?.last_activity_at;

  if (domainCounts.length === 0) {
    return <div className="text-slate-500 text-sm">No domain metrics available</div>;
  }

  return (
    <div className="space-y-3">
      {/* Domain counts grid */}
      <div className="grid grid-cols-2 gap-3">
        {domainCounts.map((domain) => (
          <DomainCountCard key={domain.domain} domain={domain} />
        ))}
      </div>

      {/* Last activity */}
      {lastActivity && (
        <div className="text-xs text-slate-500 pt-2 border-t border-gray-700/50">
          Last activity: {new Date(lastActivity).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      )}
    </div>
  );
}

/**
 * Domain Count Card Component
 */
function DomainCountCard({ domain }: { domain: DomainCount }) {
  const hasAttention = domain.pending > 0 || domain.critical > 0;

  return (
    <div className={`p-3 rounded-lg border ${hasAttention ? 'bg-yellow-500/5 border-yellow-400/30' : 'bg-gray-900/50 border-gray-700/50'}`}>
      <div className="text-xs text-slate-400 font-medium">{domain.domain}</div>
      <div className="text-2xl font-bold text-white mt-1">{domain.total}</div>
      <div className="flex items-center gap-2 mt-1 text-xs">
        {domain.pending > 0 && (
          <span className="text-yellow-400">{domain.pending} pending</span>
        )}
        {domain.critical > 0 && (
          <span className="text-red-400">{domain.critical} critical</span>
        )}
        {domain.pending === 0 && domain.critical === 0 && (
          <span className="text-slate-500">No action needed</span>
        )}
      </div>
    </div>
  );
}

/**
 * Health Metrics List (O2) - Shows decisions queue and cost overview
 *
 * PIN-413 Overview is PROJECTION-ONLY
 */
function HealthMetricsList({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const { data: decisionsData, isLoading: decisionsLoading } = useQuery({
    queryKey: ['overview', 'decisions'],
    queryFn: () => fetchDecisions({ limit: 5 }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  const { data: costsData, isLoading: costsLoading } = useQuery({
    queryKey: ['overview', 'costs'],
    queryFn: () => fetchCostIntelligence(30),
    refetchInterval: 60000,
    staleTime: 30000,
  });

  const isLoading = decisionsLoading || costsLoading;

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading details...</div>;
  }

  const decisions = decisionsData?.items ?? [];
  const hasMoreDecisions = decisionsData?.has_more ?? false;
  const costData = costsData;

  return (
    <div className="space-y-6">
      {/* Pending Decisions */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="text-sm font-medium text-slate-300">Pending Decisions</div>
          {decisions.length > 0 && (
            <span className="px-2 py-0.5 rounded text-xs bg-yellow-500/10 text-yellow-400 border border-yellow-400/30">
              {decisionsData?.total ?? decisions.length} total
            </span>
          )}
        </div>
        {decisions.length === 0 ? (
          <div className="text-slate-500 text-sm">No pending decisions</div>
        ) : (
          <div className="space-y-2">
            {decisions.map((decision) => (
              <DecisionListItem key={decision.entity_id} decision={decision} />
            ))}
            {hasMoreDecisions && (
              <button
                onClick={() => navigate('/precus/overview/decisions')}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                View all decisions...
              </button>
            )}
          </div>
        )}
      </div>

      {/* Cost Overview */}
      {costData && (
        <div>
          <div className="text-sm font-medium text-slate-300 mb-3">Cost Overview (30 days)</div>
          <div className="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-400">LLM Spend</div>
                <div className="text-xl font-bold text-white">
                  ${costData.actuals.llm_run_cost.toFixed(2)}
                </div>
              </div>
              {costData.violations.breach_count > 0 && (
                <div className="text-right">
                  <div className="text-xs text-red-400">{costData.violations.breach_count} breach{costData.violations.breach_count !== 1 ? 'es' : ''}</div>
                  <div className="text-sm text-red-400">
                    +${costData.violations.total_overage.toFixed(2)} overage
                  </div>
                </div>
              )}
            </div>

            {/* Budget limits status */}
            {costData.limits.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-700/50 space-y-2">
                {costData.limits.slice(0, 3).map((limit) => (
                  <LimitStatusBar key={limit.limit_id} limit={limit} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Decision List Item Component
 */
function DecisionListItem({ decision }: { decision: DecisionItem }) {
  const priorityColors: Record<string, string> = {
    CRITICAL: 'text-red-400 border-red-400/40 bg-red-500/10',
    HIGH: 'text-orange-400 border-orange-400/40 bg-orange-500/10',
    MEDIUM: 'text-yellow-400 border-yellow-400/40 bg-yellow-500/10',
    LOW: 'text-blue-400 border-blue-400/40 bg-blue-500/10',
  };

  const domainColors: Record<string, string> = {
    INCIDENT: 'text-orange-400',
    POLICY: 'text-blue-400',
  };

  const priorityColor = priorityColors[decision.priority] || priorityColors.MEDIUM;
  const domainColor = domainColors[decision.source_domain] || 'text-slate-400';

  return (
    <div className="flex items-center justify-between p-2 bg-gray-800/50 rounded border border-gray-700/30">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-xs ${domainColor}`}>{decision.source_domain}</span>
          <span className={`px-1.5 py-0.5 rounded border text-xs font-medium ${priorityColor}`}>
            {decision.priority}
          </span>
          <span className="px-1.5 py-0.5 rounded text-xs bg-gray-700 text-slate-300">
            {decision.decision_type}
          </span>
        </div>
        <div className="text-sm text-white mt-1 truncate">{decision.summary}</div>
      </div>
      <div className="text-xs text-slate-500 ml-2">
        {new Date(decision.created_at).toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
        })}
      </div>
    </div>
  );
}

/**
 * Limit Status Bar Component
 */
function LimitStatusBar({ limit }: { limit: LimitCostItem }) {
  const percentage = limit.max_value > 0 ? (limit.used_value / limit.max_value) * 100 : 0;

  const statusColors: Record<string, string> = {
    OK: 'bg-green-500',
    NEAR_THRESHOLD: 'bg-yellow-500',
    BREACHED: 'bg-red-500',
  };

  const barColor = statusColors[limit.status] || statusColors.OK;

  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-slate-400">{limit.name}</span>
        <span className={limit.status === 'BREACHED' ? 'text-red-400' : 'text-slate-400'}>
          ${limit.used_value.toFixed(2)} / ${limit.max_value.toFixed(2)}
        </span>
      </div>
      <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} transition-all`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}

// =============================================================================
// Incidents Domain Content Renderers
// =============================================================================

// =============================================================================
// Incidents Domain - INTERPRETATION PANELS (HIL v1 - PIN-417)
// =============================================================================

/**
 * Incidents Summary Briefing (O1) - HIL v1 Interpretation Panel
 *
 * PIN-417 HIL v1 RULES:
 * - This is an INTERPRETATION panel (panel_class: interpretation)
 * - Displays aggregated summary derived from incident data
 * - Uses lifecycle_state (ACTIVE, ACKED, RESOLVED) not legacy status
 * - Read-only: No controls, no mutations
 * - Shows provenance: Where data came from (capability IDs)
 * - Attention reasons are registry-backed (no free strings)
 */
function IncidentsSummaryBriefing({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'summary', '24h'],
    queryFn: () => fetchIncidentsSummary({ window: '24h', include_synthetic: true }),
    refetchInterval: 30000,
    staleTime: 15000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading incidents summary...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load incidents summary</div>;
  }

  if (!data) {
    return <div className="text-slate-500 text-sm">No summary data available</div>;
  }

  const { incidents, attention, provenance } = data;
  const hasAttention = attention.count > 0;

  // Map reason codes to human-readable labels (registry-backed)
  const reasonLabels: Record<string, string> = {
    unresolved: 'Unresolved incidents',
    high_severity: 'High/Critical severity',
  };

  return (
    <div className="space-y-4">
      {/* Incident Status Summary */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
          <div className="text-xs text-slate-400 font-medium">Total</div>
          <div className="text-2xl font-bold text-white">{incidents.total}</div>
          <div className="text-xs text-slate-500 mt-1">in {data.window}</div>
        </div>
        <div className="p-3 bg-gray-900/50 rounded-lg border border-orange-400/30">
          <div className="flex items-center gap-1.5">
            <AlertOctagon size={12} className="text-orange-400" />
            <span className="text-xs text-orange-400 font-medium">Active</span>
          </div>
          <div className="text-2xl font-bold text-orange-400">{incidents.by_lifecycle_state.active}</div>
        </div>
        <div className="p-3 bg-gray-900/50 rounded-lg border border-green-400/30">
          <div className="flex items-center gap-1.5">
            <CheckCircle size={12} className="text-green-400" />
            <span className="text-xs text-green-400 font-medium">Resolved</span>
          </div>
          <div className="text-2xl font-bold text-green-400">{incidents.by_lifecycle_state.resolved}</div>
          {incidents.by_lifecycle_state.acked > 0 && (
            <div className="text-xs text-blue-400 mt-1">
              {incidents.by_lifecycle_state.acked} acknowledged
            </div>
          )}
        </div>
      </div>

      {/* Attention Section */}
      {hasAttention && (
        <div className="p-3 bg-orange-500/10 rounded-lg border border-orange-400/30">
          <div className="flex items-center gap-2">
            <AlertOctagon size={16} className="text-orange-400" />
            <span className="text-sm font-medium text-orange-400">
              {attention.count} incident{attention.count !== 1 ? 's' : ''} need attention
            </span>
          </div>
          {attention.reasons.length > 0 && (
            <div className="flex items-center gap-2 mt-2 flex-wrap">
              {attention.reasons.map((reason) => (
                <span
                  key={reason}
                  className="px-2 py-0.5 rounded text-xs bg-orange-500/20 text-orange-300 border border-orange-400/30"
                >
                  {reasonLabels[reason] || reason}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* No Attention - All Clear */}
      {!hasAttention && (
        <div className="p-3 bg-green-500/10 rounded-lg border border-green-400/30">
          <div className="flex items-center gap-2">
            <CheckCircle size={16} className="text-green-400" />
            <span className="text-sm font-medium text-green-400">
              No active incidents
            </span>
          </div>
        </div>
      )}

      {/* Provenance Section (HIL v1 requirement) */}
      <div className="pt-3 border-t border-gray-700/50">
        <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-2">
          <Info size={12} />
          <span>Derived from</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {provenance.derived_from.map((capabilityId) => (
            <span
              key={capabilityId}
              className="px-2 py-0.5 rounded text-xs bg-blue-500/10 text-blue-400 border border-blue-400/20 font-mono"
            >
              {capabilityId}
            </span>
          ))}
        </div>
        <div className="text-xs text-slate-600 mt-2">
          Aggregation: {provenance.aggregation} · Generated: {new Date(provenance.generated_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}

/**
 * Active Incidents Navigation (O1) - Navigation-only panel for Active Incidents
 *
 * PIN-412 O1 BINDING RULES (INV-DOMAIN-001):
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function ActiveIncidentsNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewActiveIncidents = () => {
    navigate('/precus/incidents?state=ACTIVE');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Unresolved incidents affecting LLM Runs that may require attention.</p>
      </div>
      <button
        onClick={handleViewActiveIncidents}
        className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <AlertOctagon size={16} />
        View Active Incidents
      </button>
    </div>
  );
}

/**
 * Historical Incidents Navigation (O1) - Navigation-only panel for Historical view
 *
 * PIN-412 O1 BINDING RULES (INV-DOMAIN-001):
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function HistoricalIncidentsNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewHistorical = () => {
    navigate('/precus/incidents?state=HISTORICAL');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Historical incident patterns and recurring issues for analysis.</p>
      </div>
      <button
        onClick={handleViewHistorical}
        className="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <History size={16} />
        View Historical Incidents
      </button>
    </div>
  );
}

/**
 * Resolved Incidents Navigation (O1) - Navigation-only panel for Resolved Incidents
 *
 * PIN-412 O1 BINDING RULES (INV-DOMAIN-001):
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function ResolvedIncidentsNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewResolvedIncidents = () => {
    navigate('/precus/incidents?state=RESOLVED');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Incidents that have been handled and closed.</p>
      </div>
      <button
        onClick={handleViewResolvedIncidents}
        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <FileCheck size={16} />
        View Resolved Incidents
      </button>
    </div>
  );
}

/**
 * Open Incidents List (O2) - Shows list of open incidents
 */
function OpenIncidentsList({ panel }: PanelContentProps) {
  // Phase 3.1 Migration: Rebind to topic-scoped /incidents/active endpoint
  // Topic enforced at endpoint boundary - no status param needed
  // Reference: INCIDENTS_DOMAIN_MIGRATION_PLAN.md Phase 3.1
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'active', 'list'],
    queryFn: () => fetchActiveIncidents({
      is_synthetic: true,
      limit: 10
    }),
    refetchInterval: 15000,
    staleTime: 5000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading active incidents...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load active incidents</div>;
  }

  // TopicScopedIncidentsResponse uses 'items' not 'incidents'
  const incidents = data?.items ?? [];

  if (incidents.length === 0) {
    return <div className="text-slate-500 text-sm">No active incidents</div>;
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
  // Phase 3.2 Migration: Rebind to topic-scoped /incidents/resolved endpoint
  // Topic enforced at endpoint boundary - no status param needed
  // Reference: INCIDENTS_DOMAIN_MIGRATION_PLAN.md Phase 3.2
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents', 'resolved', 'list'],
    queryFn: () => fetchResolvedIncidents({
      is_synthetic: true,
      limit: 10
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

  // TopicScopedIncidentsResponse uses 'items' not 'incidents'
  const incidents = data?.items ?? [];

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
// Logs Domain Content Renderers - AUDIT_LEDGER Subdomain (PIN-413)
// =============================================================================

/**
 * System Audit Summary (O1) - Shows system event counts
 *
 * PIN-413: System records are WRITE-ONCE (no UPDATE, no DELETE)
 */
function SystemAuditSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['logs', 'system', 'summary'],
    queryFn: () => fetchSystemRecords({ limit: 100 }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading system audit...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load system audit</div>;
  }

  const records = data?.items ?? [];
  const total = data?.total ?? 0;

  // Count by severity
  const criticalCount = records.filter(r => r.severity === 'CRITICAL').length;
  const warnCount = records.filter(r => r.severity === 'WARN').length;
  const infoCount = records.filter(r => r.severity === 'INFO').length;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-white">{total}</div>
        <div className="text-slate-400 text-sm">system records</div>
      </div>
      <div className="flex items-center gap-3 flex-wrap">
        {criticalCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-red-500/10 text-red-400 border-red-400/40">
            {criticalCount} critical
          </span>
        )}
        {warnCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-yellow-500/10 text-yellow-400 border-yellow-400/40">
            {warnCount} warning
          </span>
        )}
        {infoCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-blue-500/10 text-blue-400 border-blue-400/40">
            {infoCount} info
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * System Audit List (O2) - Shows list of system records
 *
 * PIN-413: System events like startup, shutdown, migrations
 */
function SystemAuditList({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['logs', 'system', 'list'],
    queryFn: () => fetchSystemRecords({ limit: 20 }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading system records...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load system records</div>;
  }

  const records = data?.items ?? [];

  if (records.length === 0) {
    return <div className="text-slate-500 text-sm">No system records found</div>;
  }

  return (
    <div className="space-y-2">
      {records.map((record) => (
        <SystemRecordListItem key={record.id} record={record} />
      ))}
      {data && data.total > records.length && (
        <div className="text-xs text-slate-500 pt-2">
          Showing {records.length} of {data.total} records
        </div>
      )}
    </div>
  );
}

/**
 * System Record List Item Component
 */
function SystemRecordListItem({ record }: { record: SystemRecordItem }) {
  const severityColors: Record<string, string> = {
    CRITICAL: 'text-red-400 border-red-400/40 bg-red-500/10',
    WARN: 'text-yellow-400 border-yellow-400/40 bg-yellow-500/10',
    INFO: 'text-blue-400 border-blue-400/40 bg-blue-500/10',
  };

  const componentColors: Record<string, string> = {
    worker: 'text-purple-400',
    api: 'text-green-400',
    scheduler: 'text-cyan-400',
    db: 'text-orange-400',
    auth: 'text-pink-400',
    migration: 'text-yellow-400',
  };

  const severityColor = severityColors[record.severity] || severityColors.INFO;
  const componentColor = componentColors[record.component] || 'text-slate-400';

  return (
    <div className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs font-mono ${componentColor}`}>{record.component}</span>
          <span className={`px-2 py-0.5 rounded border text-xs font-medium ${severityColor}`}>
            {record.severity}
          </span>
          <span className="px-2 py-0.5 rounded text-xs bg-gray-700 text-slate-300">
            {record.event_type}
          </span>
        </div>
        <div className="text-sm text-white mt-1 truncate">
          {record.summary}
        </div>
      </div>
      <div className="text-xs text-slate-500 ml-4">
        {new Date(record.created_at).toLocaleString('en-US', {
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
 * System Audit Detail (O3) - Shows system record with full details
 * Note: In full implementation, this would receive record_id from context
 */
function SystemAuditDetail({ panel }: PanelContentProps) {
  // For panel view, show most recent record
  const { data, isLoading, error } = useQuery({
    queryKey: ['logs', 'system', 'latest'],
    queryFn: () => fetchSystemRecords({ limit: 1 }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading record details...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load record details</div>;
  }

  const record = data?.items?.[0];
  if (!record) {
    return <div className="text-slate-500 text-sm">No record selected</div>;
  }

  const severityColors: Record<string, string> = {
    CRITICAL: 'text-red-400 border-red-400/40 bg-red-500/10',
    WARN: 'text-yellow-400 border-yellow-400/40 bg-yellow-500/10',
    INFO: 'text-blue-400 border-blue-400/40 bg-blue-500/10',
  };

  return (
    <div className="space-y-4">
      <div className="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-xs text-slate-400">{record.id.slice(0, 12)}...</span>
          <span className={`px-2 py-0.5 rounded border text-xs font-medium ${severityColors[record.severity]}`}>
            {record.severity}
          </span>
        </div>
        <div className="text-lg font-medium text-white mt-2">{record.summary}</div>
        <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
          <div>
            <span className="text-slate-500">Component:</span>
            <span className="text-white ml-2">{record.component}</span>
          </div>
          <div>
            <span className="text-slate-500">Event:</span>
            <span className="text-white ml-2">{record.event_type}</span>
          </div>
          {record.caused_by && (
            <div>
              <span className="text-slate-500">Caused by:</span>
              <span className="text-white ml-2">{record.caused_by}</span>
            </div>
          )}
          <div>
            <span className="text-slate-500">Created:</span>
            <span className="text-white ml-2">
              {new Date(record.created_at).toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * User Audit Summary (O1) - Shows audit ledger counts
 *
 * PIN-413: Audit ledger is WRITE-ONCE (no UPDATE, no DELETE)
 */
function UserAuditSummary({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['logs', 'audit', 'summary'],
    queryFn: () => fetchAuditEntries({ limit: 100 }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading user audit...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load user audit</div>;
  }

  const entries = data?.items ?? [];
  const total = data?.total ?? 0;

  // Count by actor type
  const humanCount = entries.filter(e => e.actor_type === 'HUMAN').length;
  const systemCount = entries.filter(e => e.actor_type === 'SYSTEM').length;
  const agentCount = entries.filter(e => e.actor_type === 'AGENT').length;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-white">{total}</div>
        <div className="text-slate-400 text-sm">audit entries</div>
      </div>
      <div className="flex items-center gap-3 flex-wrap">
        {humanCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-green-500/10 text-green-400 border-green-400/40">
            {humanCount} human
          </span>
        )}
        {systemCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-blue-500/10 text-blue-400 border-blue-400/40">
            {systemCount} system
          </span>
        )}
        {agentCount > 0 && (
          <span className="px-2 py-1 rounded border text-xs font-medium bg-purple-500/10 text-purple-400 border-purple-400/40">
            {agentCount} agent
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * User Audit List (O2) - Shows list of audit entries
 *
 * PIN-413: Governance actions by HUMAN, SYSTEM, AGENT actors
 */
function UserAuditList({ panel }: PanelContentProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['logs', 'audit', 'list'],
    queryFn: () => fetchAuditEntries({ limit: 20 }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading audit entries...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load audit entries</div>;
  }

  const entries = data?.items ?? [];

  if (entries.length === 0) {
    return <div className="text-slate-500 text-sm">No audit entries found</div>;
  }

  return (
    <div className="space-y-2">
      {entries.map((entry) => (
        <AuditEntryListItem key={entry.id} entry={entry} />
      ))}
      {data && data.total > entries.length && (
        <div className="text-xs text-slate-500 pt-2">
          Showing {entries.length} of {data.total} entries
        </div>
      )}
    </div>
  );
}

/**
 * Audit Entry List Item Component
 */
function AuditEntryListItem({ entry }: { entry: AuditLedgerItem }) {
  const actorColors: Record<string, string> = {
    HUMAN: 'text-green-400 border-green-400/40 bg-green-500/10',
    SYSTEM: 'text-blue-400 border-blue-400/40 bg-blue-500/10',
    AGENT: 'text-purple-400 border-purple-400/40 bg-purple-500/10',
  };

  const entityColors: Record<string, string> = {
    POLICY_RULE: 'text-blue-400',
    POLICY_PROPOSAL: 'text-yellow-400',
    LIMIT: 'text-orange-400',
    INCIDENT: 'text-red-400',
  };

  const actorColor = actorColors[entry.actor_type] || actorColors.SYSTEM;
  const entityColor = entityColors[entry.entity_type] || 'text-slate-400';

  return (
    <div className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`px-2 py-0.5 rounded border text-xs font-medium ${actorColor}`}>
            {entry.actor_type}
          </span>
          <span className={`text-xs ${entityColor}`}>{entry.entity_type}</span>
          <span className="px-2 py-0.5 rounded text-xs bg-gray-700 text-slate-300">
            {entry.event_type}
          </span>
        </div>
        <div className="text-sm text-white mt-1 truncate">
          {entry.action_reason || `${entry.event_type} on ${entry.entity_type}`}
        </div>
        <div className="text-xs text-slate-500 mt-1 font-mono">
          {entry.entity_id.slice(0, 16)}...
        </div>
      </div>
      <div className="text-xs text-slate-500 ml-4">
        {new Date(entry.created_at).toLocaleString('en-US', {
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
 * User Audit Detail (O3) - Shows audit entry with state snapshots
 * Note: In full implementation, this would receive entry_id from context
 */
function UserAuditDetail({ panel }: PanelContentProps) {
  // For panel view, show most recent entry
  const { data, isLoading, error } = useQuery({
    queryKey: ['logs', 'audit', 'latest'],
    queryFn: () => fetchAuditEntries({ limit: 1 }),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return <div className="text-slate-400 text-sm">Loading entry details...</div>;
  }

  if (error) {
    return <div className="text-red-400 text-sm">Failed to load entry details</div>;
  }

  const entry = data?.items?.[0];
  if (!entry) {
    return <div className="text-slate-500 text-sm">No entry selected</div>;
  }

  const actorColors: Record<string, string> = {
    HUMAN: 'text-green-400 border-green-400/40 bg-green-500/10',
    SYSTEM: 'text-blue-400 border-blue-400/40 bg-blue-500/10',
    AGENT: 'text-purple-400 border-purple-400/40 bg-purple-500/10',
  };

  return (
    <div className="space-y-4">
      <div className="p-3 bg-gray-900/50 rounded-lg border border-gray-700/50">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-xs text-slate-400">{entry.id.slice(0, 12)}...</span>
          <span className={`px-2 py-0.5 rounded border text-xs font-medium ${actorColors[entry.actor_type]}`}>
            {entry.actor_type}
          </span>
        </div>
        <div className="text-lg font-medium text-white mt-2">
          {entry.action_reason || `${entry.event_type} on ${entry.entity_type}`}
        </div>
        <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
          <div>
            <span className="text-slate-500">Entity Type:</span>
            <span className="text-white ml-2">{entry.entity_type}</span>
          </div>
          <div>
            <span className="text-slate-500">Event:</span>
            <span className="text-white ml-2">{entry.event_type}</span>
          </div>
          <div className="col-span-2">
            <span className="text-slate-500">Entity ID:</span>
            <span className="text-white ml-2 font-mono">{entry.entity_id}</span>
          </div>
          {entry.actor_id && (
            <div className="col-span-2">
              <span className="text-slate-500">Actor:</span>
              <span className="text-white ml-2 font-mono">{entry.actor_id}</span>
            </div>
          )}
          <div className="col-span-2">
            <span className="text-slate-500">Created:</span>
            <span className="text-white ml-2">
              {new Date(entry.created_at).toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Policies Domain Content Renderers - GOVERNANCE Subdomain (PIN-412)
// =============================================================================

/**
 * Active Rules Navigation (O1) - Navigation-only panel for Active Policy Rules
 *
 * PIN-412 O1 BINDING RULES (INV-DOMAIN-001):
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function ActiveRulesNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewActiveRules = () => {
    navigate('/precus/policies/rules?status=ACTIVE');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Policy Rules currently enforcing constraints on LLM Runs.</p>
      </div>
      <button
        onClick={handleViewActiveRules}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <Shield size={16} />
        View Active Rules
      </button>
    </div>
  );
}

/**
 * Proposals Navigation (O1) - Navigation-only panel for Policy Proposals
 *
 * PIN-412 O1 BINDING RULES (INV-DOMAIN-001):
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function ProposalsNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewProposals = () => {
    navigate('/precus/policies/proposals?status=PENDING');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Pending policy changes that require review and approval.</p>
      </div>
      <button
        onClick={handleViewProposals}
        className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <FilePlus size={16} />
        Review Proposals
      </button>
    </div>
  );
}

/**
 * Retired Rules Navigation (O1) - Navigation-only panel for Retired Policy Rules
 *
 * PIN-412 O1 BINDING RULES (INV-DOMAIN-001):
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function RetiredRulesNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewRetiredRules = () => {
    navigate('/precus/policies/rules?status=RETIRED');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Deprecated Policy Rules and their evolution history.</p>
      </div>
      <button
        onClick={handleViewRetiredRules}
        className="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <Archive size={16} />
        View Retired Rules
      </button>
    </div>
  );
}

// =============================================================================
// Policies Domain Content Renderers - LIMITS Subdomain (PIN-412)
// =============================================================================

/**
 * Budget Limits Navigation (O1) - Navigation-only panel for Budget Limits
 *
 * PIN-412 O1 BINDING RULES (INV-DOMAIN-001):
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function BudgetLimitsNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewBudgetLimits = () => {
    navigate('/precus/policies/limits?type=BUDGET');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Cost and token allocation constraints for LLM Runs.</p>
      </div>
      <button
        onClick={handleViewBudgetLimits}
        className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <DollarSign size={16} />
        View Budget Limits
      </button>
    </div>
  );
}

/**
 * Rate Limits Navigation (O1) - Navigation-only panel for Rate Limits
 *
 * PIN-412 O1 BINDING RULES (INV-DOMAIN-001):
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 */
function RateLimitsNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewRateLimits = () => {
    navigate('/precus/policies/limits?type=RATE');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Throughput constraints limiting requests per time window.</p>
      </div>
      <button
        onClick={handleViewRateLimits}
        className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <Gauge size={16} />
        View Rate Limits
      </button>
    </div>
  );
}

/**
 * Control Limits Navigation (O1) - Navigation-only panel for Control Limits
 *
 * PIN-412 O1 BINDING RULES (INV-DOMAIN-001):
 * - NO data fetching (instant render)
 * - NO counts rendered
 * - Navigation only with filters
 * - O2 loads data AFTER navigation
 *
 * Note: Renamed from ThresholdLimitsNavigation (2026-01-20)
 */
function ControlLimitsNavigation({ panel }: PanelContentProps) {
  const navigate = useNavigate();

  const handleViewControlLimits = () => {
    navigate('/precus/policies/limits/controls');
  };

  return (
    <div className="space-y-4">
      <div className="text-slate-300">
        <p className="text-sm">Quality and performance constraints for latency, duration, and retries.</p>
      </div>
      <button
        onClick={handleViewControlLimits}
        className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <SlidersHorizontal size={16} />
        View Controls
      </button>
    </div>
  );
}

/**
 * Proposals List (O2) - Shows list of proposals with approve/reject actions
 */
function ProposalsList({ panel }: PanelContentProps) {
  const queryClient = useQueryClient();
  const { user: clerkUser } = useUser();

  const { data, isLoading, error } = useQuery({
    queryKey: ['proposals', 'list'],
    queryFn: () => fetchProposals({ limit: 20 }),
    refetchInterval: 15000,
    staleTime: 5000,
  });

  // Use authenticated user's email for audit trail (Clerk user)
  const reviewedBy = clerkUser?.primaryEmailAddress?.emailAddress || clerkUser?.id || 'unknown';

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
  // Overview Domain - SYSTEM_HEALTH Subdomain (PIN-413)
  // Topic: CURRENT_STATUS
  'OVW-SH-CS-O1': SystemStatusSummary,
  // Topic: HEALTH_METRICS
  'OVW-SH-HM-O1': HealthMetricsSummary,
  'OVW-SH-HM-O2': HealthMetricsList,

  // Activity Domain - EXECUTIONS Subdomain
  // Topic: ACTIVE_RUNS (Live)
  // O1: Navigation-only (instant render, no data fetch) - PIN-411
  'ACT-EX-AR-O1': LiveRunsNavigation,
  'ACT-EX-AR-O2': ActiveRunsList,

  // Topic: COMPLETED_RUNS
  // O1: Navigation-only (instant render, no data fetch) - PIN-411
  'ACT-EX-CR-O1': CompletedRunsNavigation,
  'ACT-EX-CR-O2': CompletedRunsList,

  // Topic: RUN_DETAILS (Risk Signals)
  // O1: Navigation-only (instant render, no data fetch) - PIN-411
  'ACT-EX-RD-O1': RiskSignalsNavigation,

  // Activity Domain - INTERPRETATION PANELS (HIL v1 - PIN-417)
  // Topic: SUMMARY (Interpretation panel - derived from execution data)
  'ACT-EX-SUM-O1': ActivitySummaryBriefing,

  // Incidents Domain - INTERPRETATION PANELS (HIL v1 - PIN-417)
  // Topic: SUMMARY (Interpretation panel - derived from incident data)
  'INC-AI-SUM-O1': IncidentsSummaryBriefing,

  // Incidents Domain - EVENTS Subdomain (PIN-412)
  // Topic: ACTIVE (Unresolved, may require attention)
  // O1: Navigation-only (instant render, no data fetch) - INV-DOMAIN-001
  'INC-AI-OI-O1': ActiveIncidentsNavigation,
  'INC-AI-OI-O2': OpenIncidentsList,

  // Topic: HISTORICAL (Pattern recognition, not action)
  // O1: Navigation-only (instant render, no data fetch) - INV-DOMAIN-001
  'INC-AI-ID-O1': HistoricalIncidentsNavigation,

  // Topic: RESOLVED (Handled and closed)
  // O1: Navigation-only (instant render, no data fetch) - INV-DOMAIN-001
  'INC-HI-RI-O1': ResolvedIncidentsNavigation,
  'INC-HI-RI-O2': ResolvedIncidentsList,

  // Policies Domain - GOVERNANCE Subdomain (PIN-412)
  // Topic: ACTIVE_RULES
  // O1: Navigation-only (instant render, no data fetch) - INV-DOMAIN-001
  'POL-GOV-AR-O1': ActiveRulesNavigation,
  // Topic: PROPOSALS
  // O1: Navigation-only (instant render, no data fetch) - INV-DOMAIN-001
  'POL-PR-PP-O1': ProposalsNavigation,
  'POL-PR-PP-O2': ProposalsList,
  // Topic: RETIRED_RULES
  // O1: Navigation-only (instant render, no data fetch) - INV-DOMAIN-001
  'POL-GOV-RR-O1': RetiredRulesNavigation,

  // Policies Domain - LIMITS Subdomain (PIN-412)
  // Topic: BUDGET_LIMITS
  // O1: Navigation-only (instant render, no data fetch) - INV-DOMAIN-001
  'POL-LIM-BL-O1': BudgetLimitsNavigation,
  // Topic: RATE_LIMITS
  // O1: Navigation-only (instant render, no data fetch) - INV-DOMAIN-001
  'POL-LIM-RL-O1': RateLimitsNavigation,
  // Topic: CONTROLS (renamed from THRESHOLD_LIMITS 2026-01-20)
  // O1: Navigation-only (instant render, no data fetch) - INV-DOMAIN-001
  'POL-LIM-CTR-O1': ControlLimitsNavigation,

  // Logs Domain - EXECUTION_TRACES Subdomain (L2.1 intent: PIN-378)
  // Topic: TRACE_DETAILS
  'LOG-ET-TD-O1': TraceSummary,
  'LOG-ET-TD-O2': TraceList,
  'LOG-ET-TD-O3': TraceDetail,

  // Logs Domain - AUDIT_LEDGER Subdomain (PIN-413)
  // Topic: SYSTEM_AUDIT (System Records)
  'LOG-AL-SA-O1': SystemAuditSummary,
  'LOG-AL-SA-O2': SystemAuditList,
  'LOG-AL-SA-O3': SystemAuditDetail,
  // Topic: USER_AUDIT (Audit Ledger)
  'LOG-AL-UA-O1': UserAuditSummary,
  'LOG-AL-UA-O2': UserAuditList,
  'LOG-AL-UA-O3': UserAuditDetail,
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
