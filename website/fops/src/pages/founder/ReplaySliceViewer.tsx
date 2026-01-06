/**
 * Replay Slice Viewer Page
 *
 * H1 Replay UX - Main page for incident replay visualization
 *
 * Features:
 * - Time-windowed incident replay
 * - Grouped view: inputs, decisions, actions, side-effects
 * - Play/pause timeline scrubbing
 * - Item explanation panel
 *
 * INVARIANTS:
 * - READ-ONLY: No edit controls, no mutation buttons, no annotations
 * - Uses existing RBAC enforcement (read:replay)
 * - Tenant isolation enforced by backend
 *
 * Reference: Phase H1 - Replay UX Enablement
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Info,
  AlertTriangle,
  Clock,
  DollarSign,
  ExternalLink,
  RefreshCw,
  Loader2,
  Eye,
  GitBranch,
  Play,
  Bell,
  ChevronRight,
} from 'lucide-react';
import {
  getIncidentSummary,
  getReplayTimeline,
  getReplayExplanation,
  ReplayItem,
  getSeverityColor,
  getStatusColor,
  getCategoryColor,
  formatCost,
} from '@/api/replay';
import ReplayTimeline from './components/ReplayTimeline';

// =============================================================================
// Incident Header Component
// =============================================================================

interface IncidentHeaderProps {
  title: string;
  severity: string;
  status: string;
  triggerType: string;
  startedAt: string;
  endedAt?: string;
  callsAffected: number;
  costDelta: number;
}

function IncidentHeader({
  title,
  severity,
  status,
  triggerType,
  startedAt,
  endedAt,
  callsAffected,
  costDelta,
}: IncidentHeaderProps) {
  return (
    <div className="bg-gray-900/50 rounded-lg p-4 mb-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white mb-2">{title}</h2>
          <div className="flex items-center gap-4 text-sm">
            <span className={`px-2 py-1 rounded ${getSeverityColor(severity)}`}>
              {severity.toUpperCase()}
            </span>
            <span className={`${getStatusColor(status)}`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
            <span className="text-gray-400">
              Trigger: {triggerType.replace(/_/g, ' ')}
            </span>
          </div>
        </div>

        <div className="text-right text-sm">
          <div className="text-gray-400">
            Started: {new Date(startedAt).toLocaleString()}
          </div>
          {endedAt && (
            <div className="text-gray-400">
              Ended: {new Date(endedAt).toLocaleString()}
            </div>
          )}
        </div>
      </div>

      {/* Impact metrics */}
      <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-navy-border">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-yellow-500" />
          <span className="text-gray-400">Calls Affected:</span>
          <span className="text-white font-medium">{callsAffected}</span>
        </div>
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-green-500" />
          <span className="text-gray-400">Cost Impact:</span>
          <span className="text-white font-medium">{formatCost(costDelta)}</span>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Explanation Panel Component
// =============================================================================

interface ExplanationPanelProps {
  incidentId: string;
  itemId: string | null;
  onClose: () => void;
}

function ExplanationPanel({ incidentId, itemId, onClose }: ExplanationPanelProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['replay-explanation', incidentId, itemId],
    queryFn: () => getReplayExplanation(incidentId, itemId!),
    enabled: !!itemId,
  });

  if (!itemId) {
    return (
      <div className="bg-gray-900/50 rounded-lg p-4 text-center text-gray-500">
        <Eye className="w-8 h-8 mx-auto mb-2" />
        <p>Select an item from the timeline to see details</p>
        <p className="text-xs mt-2">
          Learn what the agent saw, why it decided, and what it executed
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-gray-900/50 rounded-lg p-4 text-center">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-500" />
        <p className="text-gray-400 mt-2">Loading explanation...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-center">
        <AlertTriangle className="w-8 h-8 mx-auto text-red-500" />
        <p className="text-red-400 mt-2">Failed to load explanation</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900/50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-medium">Item Explanation</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white text-sm"
        >
          Clear
        </button>
      </div>

      {/* Item type and category */}
      <div className="flex items-center gap-2 mb-4">
        <span className={`px-2 py-1 rounded text-xs ${getCategoryColor(data.category as any)}`}>
          {data.category}
        </span>
        <span className="text-gray-400 text-sm">
          {data.item_type === 'proxy_call' ? 'API Call' : 'Incident Event'}
        </span>
        <span className="text-gray-500 text-xs">
          {new Date(data.timestamp).toLocaleTimeString()}
        </span>
      </div>

      {/* Explanation content */}
      <div className="space-y-4">
        {Object.entries(data.explanation).map(([key, value]) => (
          <div key={key}>
            <h4 className="text-gray-400 text-sm mb-1 capitalize">
              {key.replace(/_/g, ' ')}
            </h4>
            {typeof value === 'string' ? (
              <p className="text-gray-300 text-sm">{value}</p>
            ) : (
              <pre className="text-xs text-gray-300 bg-gray-800 p-2 rounded overflow-x-auto max-h-32">
                {JSON.stringify(value, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>

      {/* Immutability notice */}
      <div className="mt-4 pt-4 border-t border-navy-border text-xs text-gray-500 flex items-center gap-1">
        <Info className="w-3 h-3" />
        This data is immutable and cannot be modified
      </div>
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function ReplaySliceViewer() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const navigate = useNavigate();

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const playbackRef = useRef<number | null>(null);

  // Fetch incident summary
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useQuery({
    queryKey: ['incident-summary', incidentId],
    queryFn: () => getIncidentSummary(incidentId!),
    enabled: !!incidentId,
  });

  // Fetch timeline
  const {
    data: timeline,
    isLoading: timelineLoading,
    error: timelineError,
    refetch: refetchTimeline,
  } = useQuery({
    queryKey: ['replay-timeline', incidentId],
    queryFn: () => getReplayTimeline(incidentId!, 200),
    enabled: !!incidentId,
  });

  // Playback logic
  useEffect(() => {
    if (!isPlaying) {
      if (playbackRef.current) {
        cancelAnimationFrame(playbackRef.current);
        playbackRef.current = null;
      }
      return;
    }

    let startTime = performance.now();
    let startPosition = currentTime;
    const duration = 30000; // 30 second playback duration

    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = elapsed / duration;
      const newPosition = startPosition + progress;

      if (newPosition >= 1) {
        setCurrentTime(1);
        setIsPlaying(false);
        return;
      }

      setCurrentTime(newPosition);
      playbackRef.current = requestAnimationFrame(animate);
    };

    playbackRef.current = requestAnimationFrame(animate);

    return () => {
      if (playbackRef.current) {
        cancelAnimationFrame(playbackRef.current);
      }
    };
  }, [isPlaying, currentTime]);

  // Handlers
  const handlePlayPause = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  const handleSeek = useCallback((position: number) => {
    setCurrentTime(position);
    setIsPlaying(false);
  }, []);

  const handleItemClick = useCallback((item: ReplayItem) => {
    setSelectedItemId(item.id);
  }, []);

  const handleCloseExplanation = useCallback(() => {
    setSelectedItemId(null);
  }, []);

  // Loading state
  if (summaryLoading || timelineLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-blue-500" />
          <p className="text-gray-400 mt-2">Loading replay data...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (summaryError || timelineError || !summary || !timeline) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-8 text-center">
        <AlertTriangle className="w-12 h-12 mx-auto text-red-500" />
        <h2 className="text-xl text-red-400 mt-4">Failed to Load Replay</h2>
        <p className="text-gray-400 mt-2">
          {(summaryError as Error)?.message || 'Unknown error occurred'}
        </p>
        <button
          onClick={() => navigate(-1)}
          className="mt-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded"
        >
          Go Back
        </button>
      </div>
    );
  }

  // No replay data
  if (!summary.has_replay_data || timeline.items.length === 0) {
    return (
      <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg p-8 text-center">
        <Info className="w-12 h-12 mx-auto text-yellow-500" />
        <h2 className="text-xl text-yellow-400 mt-4">No Replay Data Available</h2>
        <p className="text-gray-400 mt-2">
          This incident does not have associated replay data.
        </p>
        <button
          onClick={() => navigate(-1)}
          className="mt-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded"
        >
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-800 rounded"
          >
            <ArrowLeft className="w-5 h-5 text-gray-400" />
          </button>
          <h1 className="text-2xl font-bold text-white">Incident Replay</h1>
          <span className="text-gray-500 text-sm">ID: {incidentId}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetchTimeline()}
            className="p-2 hover:bg-gray-800 rounded text-gray-400 hover:text-white"
            title="Refresh"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Immutability banner */}
      <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-3 mb-4 flex items-center gap-3">
        <Info className="w-5 h-5 text-blue-400 flex-shrink-0" />
        <div>
          <span className="text-blue-300 font-medium">Read-Only Replay</span>
          <span className="text-blue-400 ml-2 text-sm">
            This view shows immutable historical data. No modifications are possible.
          </span>
        </div>
      </div>

      {/* Incident header */}
      <IncidentHeader
        title={summary.title}
        severity={summary.severity}
        status={summary.status}
        triggerType={summary.trigger_type}
        startedAt={summary.started_at}
        endedAt={summary.ended_at}
        callsAffected={summary.calls_affected}
        costDelta={summary.cost_delta_cents}
      />

      {/* Main content grid */}
      <div className="grid grid-cols-3 gap-4 flex-1 min-h-0">
        {/* Timeline (2 columns) */}
        <div className="col-span-2 bg-gray-900/30 rounded-lg p-4 overflow-hidden flex flex-col">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Event Timeline
            <span className="text-gray-500 text-sm ml-2">
              ({timeline.total_items} events)
            </span>
          </h3>

          <ReplayTimeline
            items={timeline.items}
            timelineStart={timeline.timeline_start}
            timelineEnd={timeline.timeline_end}
            onItemClick={handleItemClick}
            selectedItemId={selectedItemId ?? undefined}
            isPlaying={isPlaying}
            onPlayPause={handlePlayPause}
            currentTime={currentTime}
            onSeek={handleSeek}
          />
        </div>

        {/* Explanation panel (1 column) */}
        <div className="col-span-1 overflow-y-auto">
          <h3 className="text-white font-medium mb-4 flex items-center gap-2">
            <Eye className="w-4 h-4" />
            Explanation
          </h3>

          <ExplanationPanel
            incidentId={incidentId!}
            itemId={selectedItemId}
            onClose={handleCloseExplanation}
          />

          {/* Legend */}
          <div className="mt-4 bg-gray-900/30 rounded-lg p-4">
            <h4 className="text-gray-400 text-sm mb-3">Understanding the Timeline</h4>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 rounded bg-blue-900/30 text-blue-400">
                  <Eye className="w-3 h-3 inline" />
                </span>
                <span className="text-gray-400">
                  <strong>Inputs:</strong> What the agent saw (requests, context)
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 rounded bg-yellow-900/30 text-yellow-400">
                  <GitBranch className="w-3 h-3 inline" />
                </span>
                <span className="text-gray-400">
                  <strong>Decisions:</strong> Why it decided (guardrails, policies)
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 rounded bg-green-900/30 text-green-400">
                  <Play className="w-3 h-3 inline" />
                </span>
                <span className="text-gray-400">
                  <strong>Actions:</strong> What it executed (API calls)
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 rounded bg-purple-900/30 text-purple-400">
                  <Bell className="w-3 h-3 inline" />
                </span>
                <span className="text-gray-400">
                  <strong>Side Effects:</strong> Notifications, logging
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
