/**
 * Replay Index Page
 *
 * H1 Replay UX - Lists incidents available for replay
 * READ-ONLY: No edit controls, no mutation buttons
 *
 * Reference: Phase H1 - Replay UX Enablement
 */

import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Play,
  AlertTriangle,
  Clock,
  Search,
  Loader2,
  Info,
  ChevronRight,
} from 'lucide-react';
import apiClient from '../../api/client';
import { getSeverityColor, getStatusColor } from '../../api/replay';

// Type for incident list response
interface IncidentListItem {
  id: string;
  title: string;
  severity: string;
  status: string;
  trigger_type: string;
  created_at: string;
  calls_affected: number;
}

interface IncidentsResponse {
  incidents: IncidentListItem[];
  total: number;
  page: number;
  page_size: number;
}

// Fetch incidents from backend
async function fetchIncidents(): Promise<IncidentsResponse> {
  const response = await apiClient.get('/api/v1/incidents', {
    params: { page: 1, page_size: 20, status: 'all' },
  });
  return response.data;
}

function IncidentCard({ incident }: { incident: IncidentListItem }) {
  return (
    <Link
      to={`/founder/replay/${incident.id}`}
      className="block bg-gray-900/50 hover:bg-gray-900/70 border border-navy-border hover:border-blue-600 rounded-lg p-4 transition-all"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(incident.severity)}`}>
              {incident.severity.toUpperCase()}
            </span>
            <span className={`text-sm ${getStatusColor(incident.status)}`}>
              {incident.status.charAt(0).toUpperCase() + incident.status.slice(1)}
            </span>
          </div>
          <h3 className="text-white font-medium mb-1">{incident.title}</h3>
          <div className="flex items-center gap-4 text-sm text-gray-400">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(incident.created_at).toLocaleString()}
            </span>
            <span className="flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              {incident.calls_affected} calls affected
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-blue-400">
          <Play className="w-5 h-5" />
          <span className="text-sm">Replay</span>
          <ChevronRight className="w-4 h-4" />
        </div>
      </div>
    </Link>
  );
}

export default function ReplayIndexPage() {
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery({
    queryKey: ['incidents-for-replay'],
    queryFn: fetchIncidents,
  });

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-2">Incident Replay</h1>
        <p className="text-gray-400">
          Select an incident to view its replay timeline. See what the agent saw, why it decided, and what it executed.
        </p>
      </div>

      {/* Immutability notice */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-3 mb-6 flex items-center gap-3">
        <Info className="w-5 h-5 text-blue-400 flex-shrink-0" />
        <div>
          <span className="text-blue-300 font-medium">Read-Only Replay</span>
          <span className="text-blue-400 ml-2 text-sm">
            All replay data is immutable. No modifications are possible.
          </span>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-500" />
            <p className="text-gray-400 mt-2">Loading incidents...</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-8 text-center">
          <AlertTriangle className="w-12 h-12 mx-auto text-red-500" />
          <h2 className="text-xl text-red-400 mt-4">Failed to Load Incidents</h2>
          <p className="text-gray-400 mt-2">
            {(error as Error)?.message || 'Unknown error occurred'}
          </p>
        </div>
      )}

      {/* Empty state */}
      {data && data.incidents.length === 0 && (
        <div className="bg-gray-900/30 border border-navy-border rounded-lg p-8 text-center">
          <Search className="w-12 h-12 mx-auto text-gray-500" />
          <h2 className="text-xl text-gray-400 mt-4">No Incidents Found</h2>
          <p className="text-gray-500 mt-2">
            When incidents occur, they will appear here for replay.
          </p>
        </div>
      )}

      {/* Incident list */}
      {data && data.incidents.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-white">
              Recent Incidents ({data.total} total)
            </h2>
          </div>
          <div className="space-y-3">
            {data.incidents.map((incident) => (
              <IncidentCard key={incident.id} incident={incident} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
