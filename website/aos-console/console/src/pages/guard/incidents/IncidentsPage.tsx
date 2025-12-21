/**
 * Incidents Page - Customer Console (M23 Enhanced)
 *
 * Human narrative, not logs.
 *
 * M23 Enhancements:
 * - Search bar with debounced search
 * - Filters panel (user_id, severity, policy_status, model, date range)
 * - Decision timeline in detail view
 *
 * Component Map:
 * IncidentsPage
 * ├── IncidentSearchBar
 * ├── IncidentFilters
 * ├── IncidentList
 * │   └── IncidentRow
 * └── Decision Inspector Modal
 *     ├── DecisionSummary
 *     └── DecisionTimeline
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card } from '../../../components/common/Card';
import { Badge } from '../../../components/common/Badge';
import { Button } from '../../../components/common/Button';
import { Modal } from '../../../components/common/Modal';
import { Spinner } from '../../../components/common/Spinner';
import { guardApi, IncidentSearchRequest, IncidentSearchResult, DecisionTimelineResponse } from '../../../api/guard';
import { IncidentSearchBar } from './IncidentSearchBar';
import { IncidentFilters } from './IncidentFilters';
import { DecisionTimeline } from './DecisionTimeline';
import { logger } from '../../../lib/consoleLogger';

// Legacy incident type (for backwards compatibility with existing endpoints)
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

const SEVERITY_CONFIG = {
  critical: { label: 'Critical', bgColor: 'bg-red-100', textColor: 'text-red-800' },
  high: { label: 'High', bgColor: 'bg-orange-100', textColor: 'text-orange-800' },
  medium: { label: 'Medium', bgColor: 'bg-yellow-100', textColor: 'text-yellow-800' },
  low: { label: 'Low', bgColor: 'bg-gray-100', textColor: 'text-gray-800' },
};

const STATUS_CONFIG = {
  open: { label: 'Active', color: 'red' },
  acknowledged: { label: 'Acknowledged', color: 'yellow' },
  resolved: { label: 'Resolved', color: 'green' },
};

export function IncidentsPage() {
  // State
  const [selectedIncident, setSelectedIncident] = useState<string | null>(null);
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

  // Use search API when filters are active, otherwise use basic list
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

  // Decision timeline query
  const { data: timeline, isLoading: timelineLoading } = useQuery({
    queryKey: ['guard', 'incidents', selectedIncident, 'timeline'],
    queryFn: () => guardApi.getDecisionTimeline(selectedIncident!),
    enabled: !!selectedIncident,
  });

  // Demo seed mutation
  const seedDemoMutation = useMutation({
    mutationFn: () => guardApi.seedDemoIncident('contract_autorenew'),
    onSuccess: () => {
      logger.info('INCIDENTS', 'Demo incident seeded');
      refetchSearch();
    },
    onError: (error) => {
      logger.error('INCIDENTS', 'Failed to seed demo incident', error);
      alert(`Failed to seed demo: ${error instanceof Error ? error.message : 'Unknown error'}`);
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

  const handleInspect = useCallback((incidentId: string) => {
    logger.userEvent('click', 'incident_inspect', { incident_id: incidentId });
    setSelectedIncident(incidentId);
  }, []);

  // Determine which data to show
  const isLoading = hasActiveFilters ? searchLoading : basicLoading;
  const incidentItems = hasActiveFilters
    ? (searchResults?.items || []).map(mapSearchResultToIncident)
    : (basicIncidents?.items || []);
  const totalCount = hasActiveFilters
    ? (searchResults?.total || 0)
    : (basicIncidents?.total || 0);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Incidents</h1>
          <p className="text-sm text-gray-500">
            {totalCount} total | {incidentItems.filter(i => i.status === 'open').length} active
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => seedDemoMutation.mutate()}
            disabled={seedDemoMutation.isPending}
          >
            {seedDemoMutation.isPending ? 'Creating...' : 'Seed Demo'}
          </Button>
        </div>
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

      {/* Sticky Incident Summary Bar */}
      {!isLoading && incidentItems.length > 0 && (
        <div className="sticky top-0 z-10 bg-gray-50 border-b border-gray-200 px-4 py-2 mb-4 rounded-lg flex items-center gap-4 text-sm">
          <span className="font-medium text-gray-700">{totalCount} incidents</span>
          <span className="text-gray-400">|</span>
          <SeverityCount items={incidentItems} severity="critical" />
          <SeverityCount items={incidentItems} severity="high" />
          <SeverityCount items={incidentItems} severity="medium" />
          <SeverityCount items={incidentItems} severity="low" />
        </div>
      )}

      {/* Results Info */}
      {hasActiveFilters && searchResults && (
        <div className="mb-4 text-sm text-gray-500">
          Found {searchResults.total} incidents
          {searchQuery && ` matching "${searchQuery}"`}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-48">
          <Spinner size="lg" />
        </div>
      )}

      {/* Empty State - Educational */}
      {!isLoading && incidentItems.length === 0 && (
        <Card className="text-center py-12 px-8">
          <div className="text-gray-400 text-5xl mb-4">
            {hasActiveFilters ? '🔍' : '✨'}
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {hasActiveFilters ? 'No Matches' : 'All Clear'}
          </h3>
          <p className="text-gray-500 mb-4">
            {hasActiveFilters
              ? 'Try adjusting your search or filters.'
              : 'No incidents recorded. This means all your policies are passing.'}
          </p>
          {!hasActiveFilters && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg text-left max-w-md mx-auto">
              <p className="text-sm font-medium text-blue-800 mb-2">What does this mean?</p>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• All AI requests passed policy checks</li>
                <li>• No cost thresholds were exceeded</li>
                <li>• No content policy violations detected</li>
                <li>• Your guardrails are actively protecting</li>
              </ul>
              <p className="text-xs text-blue-600 mt-3">
                Incidents appear here when policies fail or anomalies are detected.
              </p>
            </div>
          )}
        </Card>
      )}

      {/* Incident List */}
      {!isLoading && incidentItems.length > 0 && (
        <div className="space-y-3">
          {incidentItems.map((incident) => (
            <IncidentRow
              key={incident.id}
              incident={incident}
              onClick={() => handleInspect(incident.id)}
            />
          ))}
        </div>
      )}

      {/* Decision Inspector Modal */}
      <Modal
        open={!!selectedIncident}
        onClose={() => setSelectedIncident(null)}
        title="Decision Inspector"
        size="xl"
      >
        {timelineLoading ? (
          <div className="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : timeline ? (
          <DecisionTimeline
            timeline={timeline}
            onReplay={() => {
              // Navigate to replay page with this call
              window.location.href = `/guard/replay?call_id=${timeline.call_id || timeline.incident_id}`;
            }}
            onExport={async () => {
              // Download PDF evidence report
              try {
                await guardApi.downloadEvidenceReport(timeline.incident_id, {
                  includeReplay: true,
                  includePrevention: true,
                  isDemo: true,
                });
              } catch (error) {
                console.error('Failed to download evidence report:', error);
                alert('Failed to download evidence report. Please try again.');
              }
            }}
          />
        ) : (
          <div className="text-center py-8 text-gray-500">
            Unable to load timeline
          </div>
        )}
      </Modal>
    </div>
  );
}

// Incident Row Component
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
    ? `$${(incident.cost_avoided_cents / 100).toFixed(2)} saved`
    : null;

  return (
    <Card
      className="cursor-pointer hover:shadow-md hover:border-blue-200 transition-all"
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Severity Badge */}
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${severity.bgColor} ${severity.textColor}`}>
            {severity.label}
          </div>

          {/* Title and Time */}
          <div>
            <h3 className="font-medium text-gray-900">{incident.title}</h3>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span>{timeAgo}</span>
              {incident.calls_affected > 0 && (
                <>
                  <span>•</span>
                  <span>{incident.calls_affected} calls</span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Action & Cost */}
          <div className="text-right">
            <p className="text-sm font-medium text-gray-700">{actionLabel}</p>
            {costAvoided && (
              <p className="text-sm text-green-600">{costAvoided}</p>
            )}
          </div>

          {/* Status & Inspect */}
          <Badge
            variant={status.color === 'green' ? 'success' : status.color === 'red' ? 'error' : 'warning'}
          >
            {status.label}
          </Badge>

          <button className="text-blue-600 hover:text-blue-800 font-medium text-sm">
            Inspect →
          </button>
        </div>
      </div>
    </Card>
  );
}

// Helper: Map search result to legacy incident format
function mapSearchResultToIncident(result: IncidentSearchResult): Incident {
  return {
    id: result.incident_id,
    title: result.output_preview || 'Incident',
    severity: (result.severity as Incident['severity']) || 'medium',
    status: 'open', // Search results don't include status
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

// Helper: Format time ago
function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

// Helper: Format action
function formatAction(action: string | null): string {
  if (!action) return 'Monitored';

  const actionMap: Record<string, string> = {
    'freeze': 'Traffic Stopped',
    'block': 'Request Blocked',
    'throttle': 'Rate Limited',
    'warn': 'Warning Issued',
    'aggregate': 'Events Grouped',
    'logged': 'Logged',
  };

  return actionMap[action] || action.replace(/_/g, ' ');
}

// Severity count pill for summary bar
function SeverityCount({ items, severity }: { items: Incident[]; severity: Incident['severity'] }) {
  const count = items.filter(i => i.severity === severity).length;
  if (count === 0) return null;

  const colors: Record<string, string> = {
    critical: 'bg-red-100 text-red-700',
    high: 'bg-orange-100 text-orange-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-gray-100 text-gray-600',
  };

  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[severity]}`}>
      {count} {severity}
    </span>
  );
}

export default IncidentsPage;
