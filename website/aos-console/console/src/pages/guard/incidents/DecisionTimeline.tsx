/**
 * Decision Timeline - M23 Component Map (Redesigned)
 *
 * The MOST IMPORTANT component. Shows step-by-step policy evaluation.
 *
 * Design Principles (from GPT review):
 * 1. Reserve RED only for irreversible/blocking outcomes (kill switch, escaped incidents)
 * 2. Use AMBER for policy gaps, warnings, preventable failures
 * 3. De-emphasize passing policies (they're expected)
 * 4. Use shape+color for accessibility (not color alone)
 * 5. Root Cause is diagnostic info, not an alarm
 *
 * Timeline Events (in order):
 * 1. INPUT_RECEIVED - What the user asked
 * 2. CONTEXT_RETRIEVED - What data was fetched
 * 3. POLICY_EVALUATED - Each policy check (PASS/FAIL/WARN)
 * 4. MODEL_CALLED - LLM invocation
 * 5. OUTPUT_GENERATED - Final response
 * 6. LOGGED - Audit trail
 */

import React, { useEffect } from 'react';
import { DecisionTimelineResponse, TimelineEvent, PolicyEvaluation } from '../../../api/guard';
import { logger } from '../../../lib/consoleLogger';

interface DecisionTimelineProps {
  timeline: DecisionTimelineResponse;
  onReplay?: () => void;
  onExport?: () => void;
}

// Event type to icon/color mapping - calmer colors
const EVENT_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  INPUT_RECEIVED: { icon: '📥', color: 'text-blue-500', bg: 'bg-blue-50' },
  CONTEXT_RETRIEVED: { icon: '📋', color: 'text-purple-500', bg: 'bg-purple-50' },
  POLICY_EVALUATED: { icon: '🛡️', color: 'text-slate-600', bg: 'bg-slate-100' },
  MODEL_CALLED: { icon: '🤖', color: 'text-emerald-500', bg: 'bg-emerald-50' },
  OUTPUT_GENERATED: { icon: '📤', color: 'text-indigo-500', bg: 'bg-indigo-50' },
  LOGGED: { icon: '📝', color: 'text-gray-400', bg: 'bg-gray-50' },
};

// Result config - FAIL is amber (warning), not red (critical)
const RESULT_CONFIG: Record<string, { color: string; bg: string; border: string; label: string; icon: string }> = {
  PASS: { color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200', label: 'PASS', icon: '✓' },
  FAIL: { color: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200', label: 'FAIL', icon: '⚠' },
  WARN: { color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200', label: 'WARN', icon: '⚠' },
  BLOCKED: { color: 'text-red-700', bg: 'bg-red-50', border: 'border-red-300', label: 'BLOCKED', icon: '⛔' },
};

export function DecisionTimeline({ timeline, onReplay, onExport }: DecisionTimelineProps) {
  // Log component mount
  useEffect(() => {
    logger.componentMount('DecisionTimeline');
    logger.info('DECISION_INSPECTOR', 'Timeline loaded', {
      incident_id: timeline.incident_id,
      events: timeline.events.length,
      has_root_cause: !!timeline.root_cause,
    });
    return () => logger.componentUnmount('DecisionTimeline');
  }, [timeline]);

  // Check if this is a critical (blocked) incident vs just a policy gap
  const isCritical = timeline.events.some(e =>
    e.data?.action === 'block' || e.data?.action === 'freeze'
  );

  // Count policy results
  const failedPolicies = timeline.policy_evaluations.filter(pe => pe.result === 'FAIL');
  const passedPolicies = timeline.policy_evaluations.filter(pe => pe.result === 'PASS');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 pb-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Decision Inspector</h2>
          <p className="text-sm text-gray-500 font-mono">{timeline.incident_id}</p>
        </div>
        <div className="flex gap-2">
          {onReplay && (
            <button
              onClick={() => {
                logger.userEvent('click', 'replay_button', { incident_id: timeline.incident_id });
                onReplay();
              }}
              className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium
                         hover:bg-blue-700 transition-colors"
            >
              Replay
            </button>
          )}
          {onExport && (
            <button
              onClick={() => {
                logger.userEvent('click', 'export_button', { incident_id: timeline.incident_id });
                onExport();
              }}
              className="px-3 py-1.5 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium
                         hover:bg-gray-50 transition-colors"
            >
              Export PDF
            </button>
          )}
        </div>
      </div>

      {/* Summary Stats - Status is prominent, others secondary */}
      <div className="p-4 bg-gray-50 rounded-lg">
        {/* Status Row - Most Important */}
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-gray-200">
          <span className="text-sm font-medium text-gray-600">Status</span>
          <StatusBadge
            hasRootCause={!!timeline.root_cause}
            isCritical={isCritical}
          />
        </div>
        {/* Metadata Row - Secondary */}
        <div className="grid grid-cols-3 gap-4 text-sm">
          <MetaItem label="Model" value={timeline.model} />
          <MetaItem label="Latency" value={`${timeline.latency_ms}ms`} />
          <MetaItem label="Cost" value={`$${(timeline.cost_cents / 100).toFixed(4)}`} />
        </div>
      </div>

      {/* Root Cause - Diagnostic Panel (not alert) */}
      {timeline.root_cause_badge && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-amber-500 text-lg">🔎</span>
            <div>
              <p className="font-medium text-amber-800">
                Root Cause: {timeline.root_cause_badge}
              </p>
              <p className="text-sm text-amber-700 mt-1">{timeline.root_cause}</p>
              {/* Impact Summary - Why This Matters */}
              <div className="mt-3 pt-3 border-t border-amber-200">
                <p className="text-xs font-medium text-amber-600 uppercase tracking-wide">Why This Matters</p>
                <p className="text-sm text-amber-800 mt-1">
                  {getImpactSummary(timeline.root_cause_badge, isCritical)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Policy Evaluations - Emphasize failures, dim passes */}
      <div className="space-y-2">
        <h3 className="font-medium text-gray-700 text-sm">Policy Evaluations</h3>
        <div className="flex flex-wrap gap-2">
          {/* Failed policies first - full prominence */}
          {failedPolicies.map((pe, idx) => (
            <PolicyBadge key={`fail-${idx}`} evaluation={pe} isPrimary={true} />
          ))}
          {/* Passed policies - secondary/muted */}
          {passedPolicies.map((pe, idx) => (
            <PolicyBadge key={`pass-${idx}`} evaluation={pe} isPrimary={false} />
          ))}
        </div>
      </div>

      {/* Visual Timeline - Calmer */}
      <div className="relative">
        <h3 className="font-medium text-gray-700 text-sm mb-4">Execution Trace</h3>

        {/* Timeline line */}
        <div className="absolute left-5 top-10 bottom-4 w-0.5 bg-gray-200" />

        {/* Timeline events */}
        <div className="space-y-3">
          {timeline.events.map((event, idx) => (
            <TimelineEventCard
              key={idx}
              event={event}
              isLast={idx === timeline.events.length - 1}
            />
          ))}
        </div>
      </div>

      {/* Severity Legend - Collapsed by default */}
      <details className="text-xs text-gray-500">
        <summary className="cursor-pointer hover:text-gray-700">
          Severity Legend
        </summary>
        <div className="mt-2 p-3 bg-gray-50 rounded grid grid-cols-3 gap-2">
          <div className="flex items-center gap-1">
            <span className="text-red-500">⛔</span> Blocked (critical)
          </div>
          <div className="flex items-center gap-1">
            <span className="text-amber-500">⚠</span> Policy gap (warn)
          </div>
          <div className="flex items-center gap-1">
            <span className="text-emerald-500">✓</span> Passed (ok)
          </div>
        </div>
      </details>
    </div>
  );
}

// Status badge - uses appropriate severity
function StatusBadge({ hasRootCause, isCritical }: { hasRootCause: boolean; isCritical: boolean }) {
  if (isCritical) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
        <span>⛔</span> Traffic Blocked
      </span>
    );
  }
  if (hasRootCause) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
        <span>⚠</span> Policy Gap
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm font-medium bg-emerald-100 text-emerald-700">
      <span>✓</span> OK
    </span>
  );
}

// Metadata item
function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-gray-500 text-xs">{label}</p>
      <p className="font-medium text-gray-800">{value}</p>
    </div>
  );
}

// Timeline event card component - calmer
function TimelineEventCard({ event, isLast }: { event: TimelineEvent; isLast: boolean }) {
  const config = EVENT_CONFIG[event.event] || EVENT_CONFIG.LOGGED;
  const time = new Date(event.timestamp).toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

  // Check if this is a policy evaluation with failure
  const isPolicyFail = event.event === 'POLICY_EVALUATED' && event.data?.result === 'FAIL';
  const isPolicyBlock = event.data?.action === 'block' || event.data?.action === 'freeze';

  // Determine background - only highlight blocked, not just failed
  const bgClass = isPolicyBlock
    ? 'bg-red-50 border-l-2 border-red-300'
    : isPolicyFail
    ? 'bg-amber-50/50'
    : '';

  return (
    <div className={`relative flex gap-4 ${bgClass} -mx-2 px-2 py-1.5 rounded`}>
      {/* Timeline dot with shape encoding */}
      <div
        className={`relative z-10 w-9 h-9 rounded-full flex items-center justify-center
                    ${isPolicyBlock ? 'bg-red-100' : isPolicyFail ? 'bg-amber-100' : config.bg}`}
      >
        {isPolicyBlock ? (
          <span className="text-red-500 text-sm">⛔</span>
        ) : isPolicyFail ? (
          <span className="text-amber-500 text-sm">⚠</span>
        ) : (
          <span className="text-base">{config.icon}</span>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`font-medium text-sm ${isPolicyBlock ? 'text-red-700' : isPolicyFail ? 'text-amber-700' : 'text-gray-800'}`}>
            {formatEventName(event.event)}
          </span>
          {event.data?.result && (
            <ResultBadge result={event.data.result} action={event.data?.action} />
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

// Result badge with shape encoding
function ResultBadge({ result, action }: { result: string; action?: string }) {
  // Use blocked styling only for actual blocks
  const effectiveResult = (action === 'block' || action === 'freeze') ? 'BLOCKED' : result;
  const config = RESULT_CONFIG[effectiveResult] || RESULT_CONFIG.PASS;

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium
                  ${config.bg} ${config.color} border ${config.border}`}
    >
      <span>{config.icon}</span>
      {config.label}
    </span>
  );
}

// Event-specific content renderer
function EventContent({ event }: { event: TimelineEvent }) {
  const { data } = event;

  switch (event.event) {
    case 'INPUT_RECEIVED':
      return (
        <div className="text-sm text-gray-600">
          <p className="truncate">{data.role}: "{data.content}"</p>
          {data.model_requested && (
            <p className="text-xs text-gray-400 mt-0.5">Model: {data.model_requested}</p>
          )}
        </div>
      );

    case 'CONTEXT_RETRIEVED':
      return (
        <div className="text-sm text-gray-600">
          <p>Fields: {data.fields_retrieved?.join(', ') || 'None'}</p>
          {data.missing_fields?.length > 0 && (
            <p className="text-amber-600 text-xs mt-0.5">
              Missing: {data.missing_fields.join(', ')}
            </p>
          )}
        </div>
      );

    case 'POLICY_EVALUATED':
      return (
        <div className="text-sm">
          <p className="font-mono text-gray-700 text-xs">{data.policy}</p>
          {data.reason && (
            <p className={`mt-0.5 text-xs ${data.result === 'FAIL' ? 'text-amber-600' : 'text-gray-500'}`}>
              {data.reason}
            </p>
          )}
          {data.expected_behavior && (
            <div className="mt-1.5 p-2 bg-white rounded border border-gray-200 text-xs">
              <p><span className="font-medium text-emerald-600">Expected:</span> {data.expected_behavior}</p>
              <p><span className="font-medium text-amber-600">Actual:</span> {data.actual_behavior}</p>
            </div>
          )}
        </div>
      );

    case 'MODEL_CALLED':
      return (
        <div className="text-sm text-gray-600">
          <p className="text-xs">
            <span className="font-mono">{data.model}</span>
            {' · '}{data.input_tokens} in / {data.output_tokens} out
          </p>
        </div>
      );

    case 'OUTPUT_GENERATED':
      return (
        <div className="text-sm text-gray-600">
          <p className="italic text-xs truncate">"{data.content}"</p>
          <p className="text-xs text-gray-400 mt-0.5">
            {data.tokens} tokens | ${(data.cost_cents / 100).toFixed(4)}
          </p>
        </div>
      );

    case 'LOGGED':
      return (
        <div className="text-xs text-gray-400">
          Incident logged: {data.incident_id}
        </div>
      );

    default:
      return (
        <pre className="text-xs text-gray-500 bg-gray-50 p-2 rounded overflow-x-auto max-h-24">
          {JSON.stringify(data, null, 2)}
        </pre>
      );
  }
}

// Policy badge component - with primary/secondary distinction
function PolicyBadge({ evaluation, isPrimary }: { evaluation: PolicyEvaluation; isPrimary: boolean }) {
  const config = RESULT_CONFIG[evaluation.result] || RESULT_CONFIG.PASS;

  if (isPrimary) {
    // Failed policies - full prominence
    return (
      <div
        className={`px-3 py-1.5 rounded-lg flex items-center gap-2 border ${config.bg} ${config.border}`}
      >
        <span>{config.icon}</span>
        <span className="font-medium text-sm">{evaluation.policy}</span>
        <span className={`text-xs font-bold ${config.color}`}>{config.label}</span>
      </div>
    );
  }

  // Passed policies - muted/secondary
  return (
    <div
      className="px-2 py-1 rounded flex items-center gap-1.5 bg-gray-100 opacity-60"
    >
      <span className="text-emerald-500 text-xs">✓</span>
      <span className="text-gray-600 text-xs">{evaluation.policy}</span>
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

// Get business impact summary for root cause
function getImpactSummary(rootCauseBadge: string, isCritical: boolean): string {
  const badge = rootCauseBadge.toLowerCase();

  // Critical impacts
  if (isCritical) {
    if (badge.includes('injection') || badge.includes('jailbreak')) {
      return 'Security breach prevented. Potential unauthorized data access or system manipulation blocked.';
    }
    if (badge.includes('cost') || badge.includes('budget')) {
      return 'Runaway spend prevented. Cost threshold would have been exceeded without intervention.';
    }
    if (badge.includes('rate') || badge.includes('throttle')) {
      return 'API abuse stopped. Rate limit prevented potential service degradation.';
    }
    return 'Traffic blocked to prevent potential damage. Review incident details before resuming.';
  }

  // Non-critical policy gaps
  if (badge.includes('pii') || badge.includes('privacy')) {
    return 'Customer data exposure risk. PII may have been included in model output.';
  }
  if (badge.includes('hallucination') || badge.includes('accuracy')) {
    return 'Information accuracy concern. Model output may contain unverified claims.';
  }
  if (badge.includes('tone') || badge.includes('sentiment')) {
    return 'Brand voice deviation. Response tone may not align with guidelines.';
  }
  if (badge.includes('contract') || badge.includes('legal')) {
    return 'Legal compliance risk. Output may contain unauthorized commitments.';
  }
  if (badge.includes('off-topic') || badge.includes('scope')) {
    return 'Scope creep detected. Model answered outside of intended use case.';
  }

  // Default
  return 'Policy gap identified. Review to determine if corrective action is needed.';
}

export default DecisionTimeline;
