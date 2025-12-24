/**
 * Live Activity Page - Phase 4 Implementation
 *
 * Real-time streaming visibility:
 * - Live event feed (INPUT, POLICY, RESPONSE, KILLSWITCH)
 * - Filters by severity, component
 * - Pause/resume functionality
 * - Click to expand details
 *
 * "What is happening right now?"
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { guardApi } from '../../api/guard';
import { logger } from '../../lib/consoleLogger';

// Event types matching backend
type EventType =
  | 'INPUT_RECEIVED'
  | 'CONTEXT_RETRIEVED'
  | 'POLICY_EVALUATED'
  | 'POLICY_BLOCKED'
  | 'MODEL_CALLED'
  | 'OUTPUT_GENERATED'
  | 'KILLSWITCH_TRIGGERED'
  | 'RATE_LIMITED'
  | 'ERROR';

interface LiveEvent {
  id: string;
  type: EventType;
  timestamp: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  message: string;
  user_id?: string;
  model?: string;
  latency_ms?: number;
  cost_cents?: number;
  policy?: string;
  data?: Record<string, any>;
}

const EVENT_CONFIG: Record<EventType, { icon: string; color: string; label: string }> = {
  INPUT_RECEIVED: { icon: '📥', color: 'text-blue-400', label: 'Input' },
  CONTEXT_RETRIEVED: { icon: '📚', color: 'text-slate-400', label: 'Context' },
  POLICY_EVALUATED: { icon: '🔍', color: 'text-slate-400', label: 'Policy Check' },
  POLICY_BLOCKED: { icon: '🚫', color: 'text-red-400', label: 'Blocked' },
  MODEL_CALLED: { icon: '🤖', color: 'text-purple-400', label: 'Model Call' },
  OUTPUT_GENERATED: { icon: '📤', color: 'text-green-400', label: 'Output' },
  KILLSWITCH_TRIGGERED: { icon: '🚨', color: 'text-red-500', label: 'Kill Switch' },
  RATE_LIMITED: { icon: '⏳', color: 'text-amber-400', label: 'Rate Limited' },
  ERROR: { icon: '❌', color: 'text-red-400', label: 'Error' },
};

const SEVERITY_COLORS = {
  info: 'bg-slate-500/20 border-slate-500/30',
  warning: 'bg-amber-500/20 border-amber-500/30',
  error: 'bg-red-500/20 border-red-500/30',
  success: 'bg-green-500/20 border-green-500/30',
};

export function LiveActivityPage() {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<LiveEvent | null>(null);
  const [filter, setFilter] = useState<{
    type: EventType | 'all';
    severity: 'all' | 'warning' | 'error';
  }>({ type: 'all', severity: 'all' });

  const eventListRef = useRef<HTMLDivElement>(null);
  const eventIdCounter = useRef(0);

  useEffect(() => {
    logger.componentMount('LiveActivityPage');
    return () => logger.componentUnmount('LiveActivityPage');
  }, []);

  // Simulate live events for demo (in production, use SSE/WebSocket)
  const { data: snapshot } = useQuery({
    queryKey: ['guard', 'snapshot'],
    queryFn: guardApi.getTodaySnapshot,
    refetchInterval: 5000,
  });

  // Generate simulated events for demo mode
  const generateDemoEvent = useCallback((): LiveEvent => {
    const types: EventType[] = ['INPUT_RECEIVED', 'POLICY_EVALUATED', 'MODEL_CALLED', 'OUTPUT_GENERATED'];
    const type = types[Math.floor(Math.random() * types.length)];
    const config = EVENT_CONFIG[type];

    eventIdCounter.current += 1;

    const severities: Array<'info' | 'warning' | 'error' | 'success'> = ['info', 'info', 'info', 'success', 'warning'];

    return {
      id: `evt_${eventIdCounter.current}`,
      type,
      timestamp: new Date().toISOString(),
      severity: type === 'POLICY_BLOCKED' ? 'error' : severities[Math.floor(Math.random() * severities.length)],
      message: getDemoMessage(type),
      user_id: `user_${Math.floor(Math.random() * 1000)}`,
      model: 'gpt-4o-mini',
      latency_ms: Math.floor(Math.random() * 500) + 100,
      cost_cents: Math.floor(Math.random() * 10) + 1,
    };
  }, []);

  // Add demo events periodically
  useEffect(() => {
    if (isPaused) return;

    const interval = setInterval(() => {
      const newEvent = generateDemoEvent();
      setEvents(prev => [newEvent, ...prev.slice(0, 99)]); // Keep last 100 events
    }, 2000 + Math.random() * 3000);

    return () => clearInterval(interval);
  }, [isPaused, generateDemoEvent]);

  // Scroll to top on new event
  useEffect(() => {
    if (!isPaused && eventListRef.current) {
      eventListRef.current.scrollTop = 0;
    }
  }, [events.length, isPaused]);

  // Filter events
  const filteredEvents = events.filter(event => {
    if (filter.type !== 'all' && event.type !== filter.type) return false;
    if (filter.severity !== 'all' && event.severity !== filter.severity) return false;
    return true;
  });

  // Stats
  const stats = {
    total: events.length,
    blocked: events.filter(e => e.type === 'POLICY_BLOCKED').length,
    errors: events.filter(e => e.severity === 'error').length,
    eventsPerMinute: Math.round(events.length / 2), // Approximate
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <span className="text-2xl">📡</span>
              Live Activity
              {!isPaused && (
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              )}
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Real-time event stream • {stats.eventsPerMinute} events/min
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Filters */}
            <select
              value={filter.type}
              onChange={(e) => setFilter(f => ({ ...f, type: e.target.value as any }))}
              className="bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm"
            >
              <option value="all">All Events</option>
              {Object.entries(EVENT_CONFIG).map(([type, config]) => (
                <option key={type} value={type}>{config.label}</option>
              ))}
            </select>

            <select
              value={filter.severity}
              onChange={(e) => setFilter(f => ({ ...f, severity: e.target.value as any }))}
              className="bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm"
            >
              <option value="all">All Severity</option>
              <option value="warning">⚠️ Warnings</option>
              <option value="error">🔴 Errors</option>
            </select>

            {/* Pause/Resume */}
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`px-4 py-1.5 rounded-lg font-medium flex items-center gap-2 ${
                isPaused
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-slate-700 hover:bg-slate-600'
              }`}
            >
              {isPaused ? (
                <>▶ Resume</>
              ) : (
                <>⏸ Pause</>
              )}
            </button>

            {/* Clear */}
            <button
              onClick={() => setEvents([])}
              className="px-4 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="flex gap-4 mt-4">
          <StatBadge label="Events" value={stats.total} />
          <StatBadge label="Blocked" value={stats.blocked} color="red" />
          <StatBadge label="Errors" value={stats.errors} color="amber" />
          <StatBadge label="Requests Today" value={snapshot?.requests_today?.toLocaleString() ?? '0'} color="blue" />
        </div>
      </div>

      {/* Event Stream */}
      <div
        ref={eventListRef}
        className="flex-1 overflow-auto p-4 space-y-2"
      >
        {isPaused && (
          <div className="bg-amber-500/20 border border-amber-500/50 rounded-lg p-3 mb-4 flex items-center gap-2">
            <span>⏸</span>
            <span className="text-amber-300">Stream paused. New events will appear when resumed.</span>
          </div>
        )}

        {filteredEvents.length === 0 ? (
          <div className="text-center py-16 text-slate-400">
            <span className="text-4xl block mb-2">📡</span>
            {filter.type !== 'all' || filter.severity !== 'all'
              ? 'No events match the current filters'
              : 'Waiting for events...'}
          </div>
        ) : (
          filteredEvents.map((event) => (
            <EventRow
              key={event.id}
              event={event}
              isSelected={selectedEvent?.id === event.id}
              onClick={() => setSelectedEvent(event.id === selectedEvent?.id ? null : event)}
            />
          ))
        )}
      </div>

      {/* Event Detail Panel */}
      {selectedEvent && (
        <div className="h-64 bg-slate-800 border-t border-slate-700 p-4 overflow-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold flex items-center gap-2">
              <span>{EVENT_CONFIG[selectedEvent.type].icon}</span>
              {EVENT_CONFIG[selectedEvent.type].label}
            </h3>
            <button
              onClick={() => setSelectedEvent(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-slate-400">Event ID:</span>
              <span className="ml-2 font-mono">{selectedEvent.id}</span>
            </div>
            <div>
              <span className="text-slate-400">Timestamp:</span>
              <span className="ml-2">{new Date(selectedEvent.timestamp).toLocaleTimeString()}</span>
            </div>
            <div>
              <span className="text-slate-400">User:</span>
              <span className="ml-2">{selectedEvent.user_id || 'N/A'}</span>
            </div>
            <div>
              <span className="text-slate-400">Model:</span>
              <span className="ml-2">{selectedEvent.model || 'N/A'}</span>
            </div>
            <div>
              <span className="text-slate-400">Latency:</span>
              <span className="ml-2">{selectedEvent.latency_ms}ms</span>
            </div>
            <div>
              <span className="text-slate-400">Cost:</span>
              <span className="ml-2">${((selectedEvent.cost_cents || 0) / 100).toFixed(4)}</span>
            </div>
          </div>

          {selectedEvent.data && (
            <div className="mt-4">
              <span className="text-slate-400 text-sm">Raw Data:</span>
              <pre className="mt-2 bg-slate-900 rounded p-3 text-xs overflow-auto">
                {JSON.stringify(selectedEvent.data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Sub-components
function EventRow({ event, isSelected, onClick }: {
  event: LiveEvent;
  isSelected: boolean;
  onClick: () => void;
}) {
  const config = EVENT_CONFIG[event.type];
  const time = new Date(event.timestamp).toLocaleTimeString();

  return (
    <div
      onClick={onClick}
      className={`
        flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all
        ${SEVERITY_COLORS[event.severity]}
        ${isSelected ? 'ring-2 ring-blue-500' : 'hover:bg-slate-700/50'}
      `}
    >
      <span className="text-lg">{config.icon}</span>
      <span className={`font-mono text-xs ${config.color}`}>{config.label}</span>
      <span className="flex-1 text-sm truncate">{event.message}</span>
      {event.latency_ms && (
        <span className="text-xs text-slate-400">{event.latency_ms}ms</span>
      )}
      {event.cost_cents && (
        <span className="text-xs text-green-400">${(event.cost_cents / 100).toFixed(3)}</span>
      )}
      <span className="text-xs text-slate-500">{time}</span>
    </div>
  );
}

function StatBadge({ label, value, color = 'slate' }: {
  label: string;
  value: string | number;
  color?: 'slate' | 'red' | 'amber' | 'green' | 'blue';
}) {
  const colors = {
    slate: 'bg-slate-700/50 text-slate-300',
    red: 'bg-red-500/20 text-red-300',
    amber: 'bg-amber-500/20 text-amber-300',
    green: 'bg-green-500/20 text-green-300',
    blue: 'bg-blue-500/20 text-blue-300',
  };

  return (
    <div className={`px-3 py-1 rounded-lg ${colors[color]}`}>
      <span className="text-xs opacity-70">{label}: </span>
      <span className="font-bold">{value}</span>
    </div>
  );
}

// Demo message generator
function getDemoMessage(type: EventType): string {
  const messages: Record<EventType, string[]> = {
    INPUT_RECEIVED: [
      'Chat completion request received',
      'Embedding request queued',
      'Completion with function calls',
    ],
    CONTEXT_RETRIEVED: [
      'Retrieved 3 conversation turns',
      'Loaded user preferences',
    ],
    POLICY_EVALUATED: [
      'Content safety: PASS',
      'Rate limit check: PASS',
      'Budget check: PASS',
    ],
    POLICY_BLOCKED: [
      'Prompt injection detected',
      'Rate limit exceeded',
      'Budget exceeded',
    ],
    MODEL_CALLED: [
      'gpt-4o-mini response received',
      'Embedding generated',
    ],
    OUTPUT_GENERATED: [
      'Response sent to client',
      'Stream completed',
    ],
    KILLSWITCH_TRIGGERED: [
      'Emergency stop activated',
    ],
    RATE_LIMITED: [
      'Request queued - rate limit',
    ],
    ERROR: [
      'API timeout',
      'Model unavailable',
    ],
  };

  const options = messages[type] || ['Event processed'];
  return options[Math.floor(Math.random() * options.length)];
}

export default LiveActivityPage;
