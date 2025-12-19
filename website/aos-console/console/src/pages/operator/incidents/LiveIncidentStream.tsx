/**
 * Live Incident Stream - Operator Console
 *
 * Real-time view of all tenant incidents.
 * The operator's war room - see everything as it happens.
 *
 * Features:
 * - Real-time streaming (SSE/WebSocket)
 * - Filter by severity, tenant, status
 * - Acknowledge/resolve incidents
 * - Quick tenant drilldown
 */

import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { Badge } from '../../../components/common/Badge';
import { Modal } from '../../../components/common/Modal';
import { Spinner } from '../../../components/common/Spinner';
import { operatorApi } from '../../../api/operator';

interface Incident {
  id: string;
  tenant_id: string;
  tenant_name: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'acknowledged' | 'resolved';
  trigger_type: string;
  action_taken: string;
  calls_affected: number;
  cost_avoided_cents: number;
  started_at: string;
  ended_at: string | null;
  is_overflow?: boolean;  // True if this is a rate-limit overflow incident
}

// Helper to detect overflow incidents
function isOverflowIncident(incident: Incident): boolean {
  return incident.is_overflow === true ||
         incident.trigger_type === 'rate_limit_overflow' ||
         incident.trigger_type === 'overflow' ||
         incident.title.toLowerCase().includes('overflow') ||
         incident.title.toLowerCase().includes('rate limit exceeded');
}

interface IncidentFilters {
  severity: string | null;
  status: string | null;
  tenant_id: string | null;
}

const SEVERITY_CONFIG = {
  critical: { label: 'Critical', bgColor: 'bg-red-500', textColor: 'text-white' },
  high: { label: 'High', bgColor: 'bg-orange-500', textColor: 'text-white' },
  medium: { label: 'Medium', bgColor: 'bg-yellow-500', textColor: 'text-black' },
  low: { label: 'Low', bgColor: 'bg-gray-400', textColor: 'text-white' },
};

const STATUS_CONFIG = {
  open: { label: 'Open', color: 'red' },
  acknowledged: { label: 'Ack', color: 'yellow' },
  resolved: { label: 'Resolved', color: 'green' },
};

export function LiveIncidentStream() {
  const queryClient = useQueryClient();
  const streamRef = useRef<HTMLDivElement>(null);
  const [filters, setFilters] = useState<IncidentFilters>({
    severity: null,
    status: 'open',
    tenant_id: null,
  });
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isLive, setIsLive] = useState(true);

  // Fetch incidents with filters
  const { data: incidents, isLoading, refetch } = useQuery({
    queryKey: ['operator', 'incidents', 'stream', filters],
    queryFn: () => operatorApi.getIncidentStream(filters),
    refetchInterval: isLive ? 3000 : false,
  });

  // Acknowledge mutation
  const acknowledgeMutation = useMutation({
    mutationFn: (incidentId: string) => operatorApi.acknowledgeIncident(incidentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator', 'incidents'] });
      setSelectedIncident(null);
    },
  });

  // Resolve mutation
  const resolveMutation = useMutation({
    mutationFn: (incidentId: string) => operatorApi.resolveIncident(incidentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator', 'incidents'] });
      setSelectedIncident(null);
    },
  });

  // Auto-scroll to new incidents
  useEffect(() => {
    if (isLive && streamRef.current) {
      streamRef.current.scrollTop = 0;
    }
  }, [incidents, isLive]);

  const incidentList = incidents?.items ?? [];

  // Group by severity for summary
  const severityCounts = {
    critical: incidentList.filter((i: Incident) => i.severity === 'critical').length,
    high: incidentList.filter((i: Incident) => i.severity === 'high').length,
    medium: incidentList.filter((i: Incident) => i.severity === 'medium').length,
    low: incidentList.filter((i: Incident) => i.severity === 'low').length,
  };

  return (
    <div className="p-6 h-[calc(100vh-64px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900">Live Incident Stream</h1>
          <button
            onClick={() => setIsLive(!isLive)}
            className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
              isLive
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
            {isLive ? 'LIVE' : 'PAUSED'}
          </button>
        </div>

        {/* Severity Summary */}
        <div className="flex items-center gap-2">
          {Object.entries(severityCounts).map(([severity, count]) => (
            <button
              key={severity}
              onClick={() => setFilters(f => ({
                ...f,
                severity: f.severity === severity ? null : severity
              }))}
              className={`px-3 py-1 rounded text-sm font-medium transition-all ${
                filters.severity === severity
                  ? SEVERITY_CONFIG[severity as keyof typeof SEVERITY_CONFIG].bgColor + ' ' +
                    SEVERITY_CONFIG[severity as keyof typeof SEVERITY_CONFIG].textColor
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {count} {severity}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-4 pb-4 border-b">
        <select
          value={filters.status ?? 'all'}
          onChange={(e) => setFilters(f => ({
            ...f,
            status: e.target.value === 'all' ? null : e.target.value
          }))}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          <option value="all">All Status</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>

        <input
          type="text"
          placeholder="Filter by tenant ID..."
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm w-64"
          onChange={(e) => setFilters(f => ({
            ...f,
            tenant_id: e.target.value || null
          }))}
        />

        <Button
          variant="secondary"
          size="sm"
          onClick={() => refetch()}
        >
          Refresh
        </Button>
      </div>

      {/* Incident Stream */}
      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : incidentList.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-gray-400 text-5xl mb-4">✓</div>
            <h3 className="text-lg font-medium text-gray-900">No Active Incidents</h3>
            <p className="text-gray-500">All systems operating normally</p>
          </div>
        </div>
      ) : (
        <div
          ref={streamRef}
          className="flex-1 overflow-y-auto space-y-2"
        >
          {incidentList.map((incident: Incident) => (
            <IncidentStreamCard
              key={incident.id}
              incident={incident}
              onClick={() => setSelectedIncident(incident)}
            />
          ))}
        </div>
      )}

      {/* Incident Action Modal */}
      <Modal
        open={!!selectedIncident}
        onClose={() => setSelectedIncident(null)}
        title="Incident Actions"
        size="lg"
      >
        {selectedIncident && (
          <div className="space-y-6">
            {/* Incident Summary */}
            <div className="border-b pb-4">
              <div className="flex items-center gap-3 mb-2">
                <span className={`px-3 py-1 rounded text-sm font-medium ${
                  SEVERITY_CONFIG[selectedIncident.severity].bgColor
                } ${SEVERITY_CONFIG[selectedIncident.severity].textColor}`}>
                  {selectedIncident.severity.toUpperCase()}
                </span>
                {/* Overflow Label in Modal - GA Lock Item */}
                {isOverflowIncident(selectedIncident) && (
                  <span className="px-3 py-1 rounded text-sm font-bold bg-purple-100 text-purple-800 border border-purple-300">
                    [OVERFLOW INCIDENT]
                  </span>
                )}
                <Badge
                  variant={
                    selectedIncident.status === 'resolved' ? 'success' :
                    selectedIncident.status === 'acknowledged' ? 'warning' :
                    'error'
                  }
                >
                  {STATUS_CONFIG[selectedIncident.status].label}
                </Badge>
              </div>
              <h2 className="text-xl font-bold text-gray-900">{selectedIncident.title}</h2>
              <p className="text-gray-500 mt-1">
                Tenant: {selectedIncident.tenant_name} ({selectedIncident.tenant_id})
              </p>
              {/* Overflow Explanation - GA Lock Item */}
              {isOverflowIncident(selectedIncident) && (
                <div className="mt-3 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                  <p className="text-sm text-purple-800">
                    <strong>Overflow Incident:</strong> This incident was created because the rate limit
                    for incident creation was exceeded. It represents multiple aggregated events that
                    occurred during a high-volume period.
                  </p>
                </div>
              )}
            </div>

            {/* Details */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Trigger</p>
                <p className="font-medium">{selectedIncident.trigger_type}</p>
              </div>
              <div>
                <p className="text-gray-500">Action Taken</p>
                <p className="font-medium">{selectedIncident.action_taken}</p>
              </div>
              <div>
                <p className="text-gray-500">Calls Affected</p>
                <p className="font-medium">{selectedIncident.calls_affected.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-gray-500">Cost Avoided</p>
                <p className="font-medium text-green-600">
                  ${(selectedIncident.cost_avoided_cents / 100).toFixed(2)}
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t">
              <Link
                to={`/operator/tenants/${selectedIncident.tenant_id}`}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
              >
                View Tenant
              </Link>

              {selectedIncident.status === 'open' && (
                <Button
                  variant="secondary"
                  onClick={() => acknowledgeMutation.mutate(selectedIncident.id)}
                  disabled={acknowledgeMutation.isPending}
                >
                  {acknowledgeMutation.isPending ? 'Acknowledging...' : 'Acknowledge'}
                </Button>
              )}

              {selectedIncident.status !== 'resolved' && (
                <Button
                  variant="primary"
                  onClick={() => resolveMutation.mutate(selectedIncident.id)}
                  disabled={resolveMutation.isPending}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {resolveMutation.isPending ? 'Resolving...' : 'Resolve'}
                </Button>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

// Incident Stream Card
function IncidentStreamCard({
  incident,
  onClick,
}: {
  incident: Incident;
  onClick: () => void;
}) {
  const severity = SEVERITY_CONFIG[incident.severity];
  const status = STATUS_CONFIG[incident.status];
  const timeAgo = formatTimeAgo(new Date(incident.started_at));

  const borderColorClass = incident.severity === 'critical' ? 'border-l-red-500' :
                          incident.severity === 'high' ? 'border-l-orange-500' :
                          incident.severity === 'medium' ? 'border-l-yellow-500' : 'border-l-gray-400';
  return (
    <Card
      className={`cursor-pointer hover:shadow-md transition-all border-l-4 ${borderColorClass}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Severity Badge */}
          <span className={`px-2 py-0.5 rounded text-xs font-bold ${severity.bgColor} ${severity.textColor}`}>
            {incident.severity.toUpperCase()}
          </span>

          {/* Info */}
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-gray-900">{incident.title}</h3>
              {/* Overflow Incident Label - GA Lock Item */}
              {isOverflowIncident(incident) && (
                <span className="px-2 py-0.5 rounded text-xs font-bold bg-purple-100 text-purple-800 border border-purple-300">
                  [OVERFLOW]
                </span>
              )}
              <Badge
                variant={
                  status.color === 'green' ? 'success' :
                  status.color === 'yellow' ? 'warning' : 'error'
                }
              >
                {status.label}
              </Badge>
            </div>
            <p className="text-sm text-gray-500">
              {incident.tenant_name} • {timeAgo}
              {isOverflowIncident(incident) && (
                <span className="ml-2 text-purple-600">• Rate-limited incident aggregation</span>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6 text-sm">
          <div className="text-right">
            <p className="text-gray-500">Affected</p>
            <p className="font-medium">{incident.calls_affected.toLocaleString()} calls</p>
          </div>
          <div className="text-right">
            <p className="text-gray-500">Avoided</p>
            <p className="font-medium text-green-600">
              ${(incident.cost_avoided_cents / 100).toFixed(2)}
            </p>
          </div>
          <span className="text-gray-400">→</span>
        </div>
      </div>
    </Card>
  );
}

// Helper function
function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);

  if (diffSecs < 60) return `${diffSecs}s ago`;

  const diffMins = Math.floor(diffSecs / 60);
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  return `${Math.floor(diffHours / 24)}d ago`;
}

export default LiveIncidentStream;
