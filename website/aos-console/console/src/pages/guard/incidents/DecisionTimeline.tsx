/**
 * Decision Timeline - M23 Component Map
 *
 * The MOST IMPORTANT component. Shows step-by-step policy evaluation.
 *
 * Timeline Events (in order):
 * 1. INPUT_RECEIVED - What the user asked
 * 2. CONTEXT_RETRIEVED - What data was fetched
 * 3. POLICY_EVALUATED - Each policy check (PASS/FAIL/WARN)
 * 4. MODEL_CALLED - LLM invocation
 * 5. OUTPUT_GENERATED - Final response
 * 6. LOGGED - Audit trail
 *
 * Plus root cause identification.
 */

import React from 'react';
import { DecisionTimelineResponse, TimelineEvent, PolicyEvaluation } from '../../../api/guard';

interface DecisionTimelineProps {
  timeline: DecisionTimelineResponse;
  onReplay?: () => void;
  onExport?: () => void;
}

// Event type to icon/color mapping
const EVENT_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  INPUT_RECEIVED: { icon: '📥', color: 'text-blue-600', bg: 'bg-blue-100' },
  CONTEXT_RETRIEVED: { icon: '📋', color: 'text-purple-600', bg: 'bg-purple-100' },
  POLICY_EVALUATED: { icon: '🛡️', color: 'text-yellow-600', bg: 'bg-yellow-100' },
  MODEL_CALLED: { icon: '🤖', color: 'text-green-600', bg: 'bg-green-100' },
  OUTPUT_GENERATED: { icon: '📤', color: 'text-indigo-600', bg: 'bg-indigo-100' },
  LOGGED: { icon: '📝', color: 'text-gray-600', bg: 'bg-gray-100' },
};

const RESULT_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  PASS: { color: 'text-green-700', bg: 'bg-green-100', label: 'PASS' },
  FAIL: { color: 'text-red-700', bg: 'bg-red-100', label: 'FAIL' },
  WARN: { color: 'text-yellow-700', bg: 'bg-yellow-100', label: 'WARN' },
};

export function DecisionTimeline({ timeline, onReplay, onExport }: DecisionTimelineProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Decision Timeline</h2>
          <p className="text-sm text-gray-500 font-mono">{timeline.incident_id}</p>
        </div>
        <div className="flex gap-2">
          {onReplay && (
            <button
              onClick={onReplay}
              className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium
                         hover:bg-blue-700 transition-colors"
            >
              Replay
            </button>
          )}
          {onExport && (
            <button
              onClick={onExport}
              className="px-3 py-1.5 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium
                         hover:bg-gray-50 transition-colors"
            >
              Export PDF
            </button>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
        <StatItem label="Model" value={timeline.model} />
        <StatItem label="Latency" value={`${timeline.latency_ms}ms`} />
        <StatItem label="Cost" value={`$${(timeline.cost_cents / 100).toFixed(4)}`} />
        <StatItem
          label="Status"
          value={timeline.root_cause ? 'Policy Gap' : 'OK'}
          highlight={!!timeline.root_cause}
        />
      </div>

      {/* Root Cause Badge (if present) */}
      {timeline.root_cause_badge && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
          <div className="flex items-center gap-2">
            <span className="text-red-500 text-xl">🔴</span>
            <span className="font-bold text-red-800">{timeline.root_cause_badge}</span>
          </div>
          <p className="text-sm text-red-700 mt-1">{timeline.root_cause}</p>
        </div>
      )}

      {/* Policy Evaluations Summary */}
      <div className="space-y-2">
        <h3 className="font-medium text-gray-900">Policy Evaluations</h3>
        <div className="flex flex-wrap gap-2">
          {timeline.policy_evaluations.map((pe, idx) => (
            <PolicyBadge key={idx} evaluation={pe} />
          ))}
        </div>
      </div>

      {/* Visual Timeline */}
      <div className="relative">
        <h3 className="font-medium text-gray-900 mb-4">Execution Trace</h3>

        {/* Timeline line */}
        <div className="absolute left-5 top-12 bottom-4 w-0.5 bg-gray-200" />

        {/* Timeline events */}
        <div className="space-y-4">
          {timeline.events.map((event, idx) => (
            <TimelineEventCard key={idx} event={event} isLast={idx === timeline.events.length - 1} />
          ))}
        </div>
      </div>
    </div>
  );
}

// Timeline event card component
function TimelineEventCard({ event, isLast }: { event: TimelineEvent; isLast: boolean }) {
  const config = EVENT_CONFIG[event.event] || EVENT_CONFIG.LOGGED;
  const time = new Date(event.timestamp).toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  });

  // Check if this is a policy evaluation with failure
  const isPolicyFail = event.event === 'POLICY_EVALUATED' && event.data?.result === 'FAIL';

  return (
    <div className={`relative flex gap-4 ${isPolicyFail ? 'bg-red-50 -mx-2 px-2 py-2 rounded-lg' : ''}`}>
      {/* Timeline dot */}
      <div
        className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center
                    ${isPolicyFail ? 'bg-red-200' : config.bg}`}
      >
        <span className="text-lg">{config.icon}</span>
      </div>

      {/* Content */}
      <div className="flex-1 pb-4">
        <div className="flex items-center gap-2 mb-1">
          <span className={`font-medium ${isPolicyFail ? 'text-red-800' : 'text-gray-900'}`}>
            {formatEventName(event.event)}
          </span>
          {event.data?.result && (
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium
                          ${RESULT_CONFIG[event.data.result]?.bg || 'bg-gray-100'}
                          ${RESULT_CONFIG[event.data.result]?.color || 'text-gray-700'}`}
            >
              {event.data.result}
            </span>
          )}
          <span className="text-xs text-gray-400 font-mono">{time}</span>
          {event.duration_ms && event.duration_ms > 0 && (
            <span className="text-xs text-gray-400">({event.duration_ms}ms)</span>
          )}
        </div>

        {/* Event-specific content */}
        <EventContent event={event} />
      </div>
    </div>
  );
}

// Event-specific content renderer
function EventContent({ event }: { event: TimelineEvent }) {
  const { data } = event;

  switch (event.event) {
    case 'INPUT_RECEIVED':
      return (
        <div className="text-sm text-gray-600">
          <p className="font-medium">{data.role}: "{data.content}"</p>
          {data.model_requested && (
            <p className="text-xs text-gray-400 mt-1">Model: {data.model_requested}</p>
          )}
        </div>
      );

    case 'CONTEXT_RETRIEVED':
      return (
        <div className="text-sm text-gray-600">
          <p>Fields: {data.fields_retrieved?.join(', ') || 'None'}</p>
          {data.missing_fields?.length > 0 && (
            <p className="text-yellow-600">
              Missing: {data.missing_fields.join(', ')}
            </p>
          )}
        </div>
      );

    case 'POLICY_EVALUATED':
      return (
        <div className="text-sm">
          <p className="font-mono text-gray-700">{data.policy}</p>
          {data.reason && (
            <p className={`mt-1 ${data.result === 'FAIL' ? 'text-red-600' : 'text-gray-600'}`}>
              {data.reason}
            </p>
          )}
          {data.expected_behavior && (
            <div className="mt-2 p-2 bg-white rounded border border-gray-200 text-xs">
              <p><span className="font-medium text-green-700">Expected:</span> {data.expected_behavior}</p>
              <p><span className="font-medium text-red-700">Actual:</span> {data.actual_behavior}</p>
            </div>
          )}
        </div>
      );

    case 'MODEL_CALLED':
      return (
        <div className="text-sm text-gray-600">
          <p>Model: <span className="font-mono">{data.model}</span></p>
          <p>Tokens: {data.input_tokens} in / {data.output_tokens} out</p>
        </div>
      );

    case 'OUTPUT_GENERATED':
      return (
        <div className="text-sm text-gray-600">
          <p className="italic">"{data.content}"</p>
          <p className="text-xs text-gray-400 mt-1">
            {data.tokens} tokens | ${(data.cost_cents / 100).toFixed(4)}
          </p>
        </div>
      );

    case 'LOGGED':
      return (
        <div className="text-sm text-gray-500">
          Incident logged: {data.incident_id}
        </div>
      );

    default:
      return (
        <pre className="text-xs text-gray-500 bg-gray-50 p-2 rounded overflow-x-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      );
  }
}

// Policy badge component
function PolicyBadge({ evaluation }: { evaluation: PolicyEvaluation }) {
  const config = RESULT_CONFIG[evaluation.result] || RESULT_CONFIG.PASS;

  return (
    <div
      className={`px-3 py-1 rounded-full flex items-center gap-2 ${config.bg}`}
    >
      <span className="font-medium text-sm">{evaluation.policy}</span>
      <span className={`text-xs font-bold ${config.color}`}>{config.label}</span>
    </div>
  );
}

// Stat item component
function StatItem({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`font-medium ${highlight ? 'text-red-600' : 'text-gray-900'}`}>
        {value}
      </p>
    </div>
  );
}

// Format event name for display
function formatEventName(event: string): string {
  const names: Record<string, string> = {
    INPUT_RECEIVED: 'Input Received',
    CONTEXT_RETRIEVED: 'Context Retrieved',
    POLICY_EVALUATED: 'Policy Evaluated',
    MODEL_CALLED: 'Model Called',
    OUTPUT_GENERATED: 'Output Generated',
    LOGGED: 'Logged',
  };
  return names[event] || event;
}

export default DecisionTimeline;
