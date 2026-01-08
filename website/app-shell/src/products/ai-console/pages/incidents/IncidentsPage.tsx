/**
 * Incidents Page - Customer Console (Navy-First Design)
 *
 * PIN-186 Classification: O2 (List/Overview)
 * V-001 Fix: Modal removed, navigation to O3 detail page
 *
 * Navy-First Design Rules Applied:
 * 1. All surfaces use navy family ONLY (no white, no gray, no colored backgrounds)
 * 2. Meaning conveyed via text color, borders, icons - never backgrounds
 * 3. Max 3 accent colors: amber (severity), green (savings), blue (actions)
 * 4. Severity = left border, not colored pill
 * 5. Status = outline pill, not filled
 *
 * Component Map:
 * IncidentsPage (O2)
 * ├── IncidentSearchBar
 * ├── IncidentFilters
 * └── IncidentList
 *     └── IncidentRow → navigates to IncidentDetailPage (O3)
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { guardApi, IncidentSearchRequest, IncidentSearchResult } from '@/api/guard';
import { CUSTOMER_ROUTES } from '@/routing';
import { IncidentSearchBar } from './IncidentSearchBar';
import { IncidentFilters } from './IncidentFilters';
import { logger } from '@/lib/consoleLogger';
// V-001 Fix: DecisionTimeline and ReplayResultsModal removed from this page
// They now live on IncidentDetailPage (O3) - modals must be terminal (INV-4)

// Legacy incident type (for backwards compatibility)
interface Incident {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'acknowledged' | 'resolved';
  trigger_type: string;
  trigger_value: string;
  action_taken: string;
  cost_avoided_cents: number;
  calls_affected: number;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
}

// Navy-First: Severity uses border color only (no background)
const SEVERITY_CONFIG = {
  critical: { label: 'Critical', borderColor: 'border-l-red-500', textColor: 'text-red-400' },
  high: { label: 'High', borderColor: 'border-l-amber-500', textColor: 'text-amber-400' },
  medium: { label: 'Medium', borderColor: 'border-l-yellow-500', textColor: 'text-yellow-400' },
  low: { label: 'Low', borderColor: 'border-l-slate-500', textColor: 'text-slate-400' },
};

// Navy-First: Status uses outline only
const STATUS_CONFIG = {
  open: { label: 'Active', textColor: 'text-amber-400', borderColor: 'border-amber-400/40' },
  acknowledged: { label: 'Ack', textColor: 'text-blue-400', borderColor: 'border-blue-400/40' },
  resolved: { label: 'Resolved', textColor: 'text-green-400', borderColor: 'border-green-400/40' },
};

export function IncidentsPage() {
  // V-001 Fix: Navigation replaces modal - incidents drill to O3 detail page
  const navigate = useNavigate();

  // State
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<IncidentSearchRequest>({
    limit: 50,
    offset: 0,
  });
  const [searchQuery, setSearchQuery] = useState('');

  // Log page mount
  useEffect(() => {
    logger.componentMount('IncidentsPage');
    logger.info('INCIDENTS', 'Page loaded');
    return () => logger.componentUnmount('IncidentsPage');
  }, []);

  // Use search API when filters are active
  const hasActiveFilters = Boolean(
    filters.user_id || filters.severity || filters.policy_status ||
    filters.model || filters.time_from || filters.time_to || searchQuery
  );

  // Search query
  const { data: searchResults, isLoading: searchLoading, refetch: refetchSearch } = useQuery({
    queryKey: ['guard', 'incidents', 'search', { ...filters, query: searchQuery }],
    queryFn: () => guardApi.searchIncidents({ ...filters, query: searchQuery }),
    enabled: hasActiveFilters,
    refetchInterval: 30000,
  });

  // Basic list query (when no filters)
  const { data: basicIncidents, isLoading: basicLoading } = useQuery({
    queryKey: ['guard', 'incidents', 'list'],
    queryFn: () => guardApi.getIncidents({ limit: 50 }),
    enabled: !hasActiveFilters,
    refetchInterval: 30000,
  });

  // V-001 Fix: Timeline and replay queries moved to IncidentDetailPage (O3)
  // This page is O2 (list) - drilling navigates to O3 (detail)

  // Demo seed mutation
  const seedDemoMutation = useMutation({
    mutationFn: () => guardApi.seedDemoIncident('contract_autorenew'),
    onSuccess: () => {
      logger.info('INCIDENTS', 'Demo incident seeded');
      refetchSearch();
    },
    onError: (error) => {
      logger.error('INCIDENTS', 'Failed to seed demo incident', error);
    },
  });

  // Handlers
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    setFilters(prev => ({ ...prev, offset: 0 }));
  }, []);

  const handleFilterChange = useCallback((newFilters: IncidentSearchRequest) => {
    setFilters(newFilters);
  }, []);

  // V-001 Fix: Navigate to O3 detail page instead of opening modal
  // PIN-352: Uses routing authority for navigation
  const handleInspect = useCallback((incidentId: string) => {
    logger.userEvent('click', 'incident_inspect', { incident_id: incidentId });
    navigate(CUSTOMER_ROUTES.incidentDetail(incidentId));
  }, [navigate]);

  // Determine which data to show
  const isLoading = hasActiveFilters ? searchLoading : basicLoading;
  const incidentItems = hasActiveFilters
    ? (searchResults?.items || []).map(mapSearchResultToIncident)
    : (basicIncidents?.items || []);
  const totalCount = hasActiveFilters
    ? (searchResults?.total || 0)
    : (basicIncidents?.total || 0);

  // Count by severity
  const severityCounts = {
    critical: incidentItems.filter(i => i.severity === 'critical').length,
    high: incidentItems.filter(i => i.severity === 'high').length,
    medium: incidentItems.filter(i => i.severity === 'medium').length,
    low: incidentItems.filter(i => i.severity === 'low').length,
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header - Navy-First */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span>📋</span> Incidents
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            AI safety events requiring attention
          </p>
        </div>
        <button
          onClick={() => seedDemoMutation.mutate()}
          disabled={seedDemoMutation.isPending}
          className="px-4 py-2 bg-navy-elevated hover:bg-navy-subtle border border-navy-border text-slate-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          {seedDemoMutation.isPending ? 'Creating...' : '+ Seed Demo'}
        </button>
      </div>

      {/* Search Bar */}
      <IncidentSearchBar
        onSearch={handleSearch}
        onFilterToggle={() => setShowFilters(!showFilters)}
        isLoading={isLoading}
      />

      {/* Filters Panel */}
      <IncidentFilters
        filters={filters}
        onChange={handleFilterChange}
        onClose={() => setShowFilters(false)}
        open={showFilters}
      />

      {/* Summary Bar - Navy surface, text-only counts */}
      {!isLoading && incidentItems.length > 0 && (
        <div className="bg-navy-surface border border-navy-border rounded-lg px-4 py-3 mb-4 flex items-center gap-6 text-sm">
          <span className="text-slate-300">
            <span className="font-semibold text-white">{totalCount}</span> incidents
          </span>
          <span className="text-navy-border">|</span>
          {severityCounts.critical > 0 && (
            <span className="text-red-400">{severityCounts.critical} critical</span>
          )}
          {severityCounts.high > 0 && (
            <span className="text-amber-400">{severityCounts.high} high</span>
          )}
          {severityCounts.medium > 0 && (
            <span className="text-yellow-400">{severityCounts.medium} medium</span>
          )}
          {severityCounts.low > 0 && (
            <span className="text-slate-400">{severityCounts.low} low</span>
          )}
        </div>
      )}

      {/* Results Info */}
      {hasActiveFilters && searchResults && (
        <div className="mb-4 text-sm text-slate-400">
          Found {searchResults.total} incidents
          {searchQuery && ` matching "${searchQuery}"`}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-48">
          <div className="w-8 h-8 border-2 border-accent-info border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Empty State - Navy surface */}
      {!isLoading && incidentItems.length === 0 && (
        <div className="bg-navy-surface border border-navy-border rounded-xl text-center py-12 px-8">
          <div className="text-4xl mb-4">
            {hasActiveFilters ? '🔍' : '✨'}
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">
            {hasActiveFilters ? 'No Matches' : 'All Clear'}
          </h3>
          <p className="text-slate-400 mb-4 max-w-md mx-auto">
            {hasActiveFilters
              ? 'Try adjusting your search or filters.'
              : 'No incidents recorded. Your guardrails are working.'}
          </p>
          {!hasActiveFilters && (
            <div className="mt-6 p-4 bg-navy-elevated border border-accent-info/20 rounded-lg text-left max-w-md mx-auto">
              <p className="text-sm font-medium text-accent-info mb-2">What this means:</p>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• All AI requests passed policy checks</li>
                <li>• No cost thresholds exceeded</li>
                <li>• No content violations detected</li>
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Incident List - Navy rows with left-border severity */}
      {/* V-001 Fix: Row click navigates to O3 detail page (no modal) */}
      {!isLoading && incidentItems.length > 0 && (
        <div className="space-y-2">
          {incidentItems.map((incident) => (
            <IncidentRow
              key={incident.id}
              incident={incident}
              onClick={() => handleInspect(incident.id)}
            />
          ))}
        </div>
      )}

      {/* V-001 Fix: Modal removed - replaced by IncidentDetailPage (O3)
          O5 modals must be terminal (confirm-only) per INV-4
          Decision inspection now happens on dedicated O3 page */}
    </div>
  );
}

// ============================================================================
// IncidentRow - Navy-First with left-border severity
// ============================================================================

interface IncidentRowProps {
  incident: Incident;
  onClick: () => void;
}

function IncidentRow({ incident, onClick }: IncidentRowProps) {
  const severity = SEVERITY_CONFIG[incident.severity] || SEVERITY_CONFIG.medium;
  const status = STATUS_CONFIG[incident.status] || STATUS_CONFIG.open;
  const timeAgo = formatTimeAgo(new Date(incident.started_at));
  const actionLabel = formatAction(incident.action_taken);
  const costAvoided = incident.cost_avoided_cents > 0
    ? `$${(incident.cost_avoided_cents / 100).toFixed(2)}`
    : null;

  return (
    <div
      onClick={onClick}
      className={`
        bg-navy-surface border border-navy-border rounded-lg
        border-l-4 ${severity.borderColor}
        hover:bg-navy-elevated hover:-translate-y-0.5
        transition-all cursor-pointer
        p-4
      `}
    >
      <div className="flex items-center justify-between gap-4">
        {/* Left: Severity + Title + Meta */}
        <div className="flex-1 min-w-0">
          {/* Severity label (text only) */}
          <span className={`text-xs font-medium uppercase tracking-wide ${severity.textColor}`}>
            {severity.label}
          </span>

          {/* Title */}
          <h3 className="font-medium text-white mt-1 truncate">
            {incident.title}
          </h3>

          {/* Metadata - muted */}
          <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
            <span>{incident.trigger_type || 'Policy check'}</span>
            <span>•</span>
            <span>{timeAgo}</span>
            {incident.calls_affected > 0 && (
              <>
                <span>•</span>
                <span>{incident.calls_affected} call{incident.calls_affected > 1 ? 's' : ''}</span>
              </>
            )}
          </div>
        </div>

        {/* Right: Savings + Status + Action */}
        <div className="flex items-center gap-4 flex-shrink-0">
          {/* Cost saved - green text only */}
          {costAvoided && (
            <div className="text-right">
              <span className="text-green-400 text-sm">{costAvoided}</span>
              <span className="block text-xs text-slate-500">saved</span>
            </div>
          )}

          {/* Action taken */}
          <div className="text-right">
            <span className="text-slate-300 text-sm">{actionLabel}</span>
          </div>

          {/* Status - outline pill only */}
          <span className={`
            px-2 py-1 rounded border text-xs font-medium
            bg-transparent ${status.textColor} ${status.borderColor}
          `}>
            {status.label}
          </span>

          {/* Inspect link */}
          <span className="text-accent-info text-sm font-medium hover:underline">
            Inspect →
          </span>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Helpers
// ============================================================================

function mapSearchResultToIncident(result: IncidentSearchResult): Incident {
  return {
    id: result.incident_id,
    title: result.output_preview || 'Incident',
    severity: (result.severity as Incident['severity']) || 'medium',
    status: 'open',
    trigger_type: result.policy_status.replace('_FAILED', ''),
    trigger_value: '',
    action_taken: 'logged',
    cost_avoided_cents: result.cost_cents,
    calls_affected: 1,
    started_at: result.timestamp,
    ended_at: null,
    duration_seconds: null,
  };
}

function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

function formatAction(action: string | null): string {
  if (!action) return 'Monitored';

  const actionMap: Record<string, string> = {
    'freeze': 'Stopped',
    'block': 'Blocked',
    'throttle': 'Throttled',
    'warn': 'Warning',
    'aggregate': 'Grouped',
    'logged': 'Logged',
  };

  return actionMap[action] || action.replace(/_/g, ' ');
}

export default IncidentsPage;
