/**
 * Incidents Page - Customer Console
 *
 * Human narrative, not logs.
 *
 * List view:
 * - Incident ID
 * - Time
 * - Severity
 * - Action taken (Frozen / Throttled / Blocked)
 * - Cost avoided (if applicable)
 *
 * Detail view:
 * - Timeline (chronological)
 * - Trigger
 * - What escalated
 * - What stopped it
 * - When it resolved
 *
 * No charts. No knobs. Just facts.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../../components/common/Card';
import { Badge } from '../../../components/common/Badge';
import { Button } from '../../../components/common/Button';
import { Modal } from '../../../components/common/Modal';
import { Spinner } from '../../../components/common/Spinner';
import { guardApi } from '../../../api/guard';

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

interface IncidentEvent {
  id: string;
  event_type: string;
  description: string;
  created_at: string;
  data?: Record<string, any>;
}

const SEVERITY_CONFIG = {
  critical: { label: 'Critical', color: 'red', bgColor: 'bg-red-100', textColor: 'text-red-800' },
  high: { label: 'High', color: 'orange', bgColor: 'bg-orange-100', textColor: 'text-orange-800' },
  medium: { label: 'Medium', color: 'yellow', bgColor: 'bg-yellow-100', textColor: 'text-yellow-800' },
  low: { label: 'Low', color: 'gray', bgColor: 'bg-gray-100', textColor: 'text-gray-800' },
};

const STATUS_CONFIG = {
  open: { label: 'Active', color: 'red' },
  acknowledged: { label: 'Acknowledged', color: 'yellow' },
  resolved: { label: 'Resolved', color: 'green' },
};

export function IncidentsPage() {
  const [selectedIncident, setSelectedIncident] = useState<string | null>(null);

  // Fetch incidents
  const { data: incidents, isLoading } = useQuery({
    queryKey: ['guard', 'incidents'],
    queryFn: () => guardApi.getIncidents({ limit: 50 }),
    refetchInterval: 30000,
  });

  // Fetch incident detail when selected
  const { data: incidentDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['guard', 'incidents', selectedIncident],
    queryFn: () => guardApi.getIncidentDetail(selectedIncident!),
    enabled: !!selectedIncident,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  const incidentList = incidents?.items ?? [];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Incidents</h1>
        <Badge variant="secondary">
          {incidentList.filter((i: Incident) => i.status === 'open').length} active
        </Badge>
      </div>

      {incidentList.length === 0 ? (
        <Card className="text-center py-12">
          <div className="text-gray-400 text-5xl mb-4">🛡️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Incidents</h3>
          <p className="text-gray-500">
            Your guardrails are working. No incidents have occurred.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {incidentList.map((incident: Incident) => (
            <IncidentCard
              key={incident.id}
              incident={incident}
              onClick={() => setSelectedIncident(incident.id)}
            />
          ))}
        </div>
      )}

      {/* Incident Detail Modal */}
      <Modal
        isOpen={!!selectedIncident}
        onClose={() => setSelectedIncident(null)}
        title="Incident Details"
        size="lg"
      >
        {detailLoading ? (
          <div className="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : incidentDetail ? (
          <IncidentDetailView incident={incidentDetail} />
        ) : null}
      </Modal>
    </div>
  );
}

// Incident Card Component
interface IncidentCardProps {
  incident: Incident;
  onClick: () => void;
}

function IncidentCard({ incident, onClick }: IncidentCardProps) {
  const severity = SEVERITY_CONFIG[incident.severity];
  const status = STATUS_CONFIG[incident.status];

  // Format time
  const timeAgo = formatTimeAgo(new Date(incident.started_at));

  // Format action
  const actionLabel = formatAction(incident.action_taken);

  // Format cost
  const costAvoided = incident.cost_avoided_cents > 0
    ? `$${(incident.cost_avoided_cents / 100).toFixed(2)} saved`
    : null;

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
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
            <p className="text-sm text-gray-500">{timeAgo}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Action Taken */}
          <div className="text-right">
            <p className="text-sm font-medium text-gray-700">{actionLabel}</p>
            {costAvoided && (
              <p className="text-sm text-green-600">{costAvoided}</p>
            )}
          </div>

          {/* Status */}
          <Badge
            variant={status.color === 'green' ? 'success' : status.color === 'red' ? 'danger' : 'warning'}
          >
            {status.label}
          </Badge>
        </div>
      </div>
    </Card>
  );
}

// Incident Detail View Component
interface IncidentDetailViewProps {
  incident: {
    incident: Incident;
    timeline: IncidentEvent[];
  };
}

function IncidentDetailView({ incident }: IncidentDetailViewProps) {
  const { incident: inc, timeline } = incident;
  const severity = SEVERITY_CONFIG[inc.severity];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <div className="flex items-center gap-3 mb-2">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${severity.bgColor} ${severity.textColor}`}>
            {severity.label}
          </span>
          <Badge variant={inc.status === 'resolved' ? 'success' : 'danger'}>
            {inc.status === 'resolved' ? 'Resolved' : 'Active'}
          </Badge>
        </div>
        <h2 className="text-xl font-bold text-gray-900">{inc.title}</h2>
      </div>

      {/* Key Facts */}
      <div className="grid grid-cols-2 gap-4">
        <FactItem label="Trigger" value={inc.trigger_type.replace(/_/g, ' ')} />
        <FactItem label="Action Taken" value={formatAction(inc.action_taken)} />
        <FactItem label="Calls Affected" value={inc.calls_affected.toString()} />
        <FactItem
          label="Duration"
          value={inc.duration_seconds ? `${Math.ceil(inc.duration_seconds / 60)} minutes` : 'Ongoing'}
        />
      </div>

      {/* Timeline */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Timeline</h3>
        <div className="space-y-4">
          {timeline.map((event, index) => (
            <TimelineEvent key={event.id} event={event} isLast={index === timeline.length - 1} />
          ))}
        </div>
      </div>
    </div>
  );
}

// Timeline Event Component
interface TimelineEventProps {
  event: IncidentEvent;
  isLast: boolean;
}

function TimelineEvent({ event, isLast }: TimelineEventProps) {
  const time = new Date(event.created_at).toLocaleTimeString();

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="w-3 h-3 bg-blue-500 rounded-full" />
        {!isLast && <div className="w-0.5 h-full bg-gray-200" />}
      </div>
      <div className="pb-4">
        <p className="text-sm text-gray-500">{time}</p>
        <p className="text-gray-900">{event.description}</p>
      </div>
    </div>
  );
}

// Fact Item Component
function FactItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="font-medium text-gray-900 capitalize">{value}</p>
    </div>
  );
}

// Helper functions
function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minutes ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hours ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} days ago`;
}

function formatAction(action: string | null): string {
  if (!action) return 'Monitored';

  const actionMap: Record<string, string> = {
    'freeze': 'Traffic Stopped',
    'block': 'Request Blocked',
    'throttle': 'Rate Limited',
    'warn': 'Warning Issued',
    'aggregate': 'Events Grouped',
  };

  return actionMap[action] || action.replace(/_/g, ' ');
}

export default IncidentsPage;
