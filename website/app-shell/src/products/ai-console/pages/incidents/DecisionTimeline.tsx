/**
 * Decision Timeline - M23 Component Map (Redesigned v2)
 *
 * The MOST IMPORTANT component. Shows step-by-step policy evaluation.
 *
 * Design Principles (from GPT/Senior reviews):
 * 1. Reserve RED only for irreversible/blocking outcomes (kill switch, escaped incidents)
 * 2. Use AMBER for policy gaps, warnings, preventable failures
 * 3. De-emphasize passing policies (collapsed by default)
 * 4. Use shape+color for accessibility (not color alone)
 * 5. Root Cause is diagnostic: cause → consequence → action
 * 6. Header shows severity + copyable ID
 * 7. Verdict separated from telemetry
 * 8. Timeline emphasizes FAIL/OUTPUT events with accent bars
 *
 * Timeline Events (in order):
 * 1. INPUT_RECEIVED - What the user asked
 * 2. CONTEXT_RETRIEVED - What data was fetched
 * 3. POLICY_EVALUATED - Each policy check (PASS/FAIL/WARN)
 * 4. MODEL_CALLED - LLM invocation
 * 5. OUTPUT_GENERATED - Final response
 * 6. LOGGED - Audit trail
 */

import React, { useState, useEffect, useCallback } from 'react';
import { DecisionTimelineResponse, TimelineEvent, PolicyEvaluation } from '@/api/guard';
import { logger } from '@/lib/consoleLogger';
import { truncateValue } from '@/utils/truncateValue';

interface DecisionTimelineProps {
  timeline: DecisionTimelineResponse;
  // V-001 Fix: Actions removed from timeline (now on O3 page)
  // onReplay and onExport were violating INV-4 by putting actions in modal content
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

// Result config - Navy-First: text/border only, no filled backgrounds
// FAIL uses amber (warning), BLOCKED uses red (critical/irreversible)
const RESULT_CONFIG: Record<string, { color: string; darkColor: string; border: string; label: string; icon: string }> = {
  PASS: { color: 'text-emerald-600', darkColor: 'dark:text-emerald-400', border: 'border-emerald-500/40', label: 'PASS', icon: '✓' },
  FAIL: { color: 'text-amber-600', darkColor: 'dark:text-amber-400', border: 'border-amber-500/40', label: 'FAILED', icon: '⚠' },
  WARN: { color: 'text-yellow-600', darkColor: 'dark:text-yellow-400', border: 'border-yellow-500/40', label: 'WARN', icon: '⚠' },
  BLOCKED: { color: 'text-red-600', darkColor: 'dark:text-red-400', border: 'border-red-500/40', label: 'BLOCKED', icon: '⛔' },
};

export function DecisionTimeline({ timeline }: DecisionTimelineProps) {
  const [showAllPolicies, setShowAllPolicies] = useState(false);
  const [copiedId, setCopiedId] = useState(false);

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

  // Determine severity for header
  const severity = isCritical ? 'HIGH' : (failedPolicies.length > 0 ? 'MEDIUM' : 'LOW');
  const verdictLabel = isCritical ? 'BLOCKED' : (failedPolicies.length > 0 ? 'Policy Gap' : 'OK');

  // Copy incident ID to clipboard
  const copyIncidentId = useCallback(() => {
    navigator.clipboard.writeText(timeline.incident_id);
    setCopiedId(true);
    logger.userEvent('click', 'copy_incident_id', { incident_id: timeline.incident_id });
    setTimeout(() => setCopiedId(false), 2000);
  }, [timeline.incident_id]);

  return (
    <div className="space-y-6">
      {/* Enhanced Header - Severity + Copyable ID */}
      <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 pb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-[#e6eaf2]">Decision Inspector</h2>
          <span className="text-gray-400 dark:text-gray-500">/</span>
          <button
            onClick={copyIncidentId}
            className="group flex items-center gap-1.5 text-sm font-mono text-gray-600 dark:text-gray-400
                       hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
            title="Click to copy"
          >
            <span className="truncate max-w-[160px]">{timeline.incident_id}</span>
            <span className="opacity-0 group-hover:opacity-100 transition-opacity text-xs">
              {copiedId ? '✓' : '📋'}
            </span>
          </button>
          <span className="text-gray-400 dark:text-gray-500">·</span>
          <span className={`text-sm font-medium ${
            isCritical ? 'text-red-600 dark:text-red-400' :
            failedPolicies.length > 0 ? 'text-amber-600 dark:text-[#ffd18a]' :
            'text-emerald-600 dark:text-emerald-400'
          }`}>
            {verdictLabel}
          </span>
          <SeverityBadge severity={severity} />
        </div>
        {/* V-001 Fix: Actions removed - they now live on IncidentDetailPage (O3)
            O5 modals must be terminal (confirm-only), no navigation or actions */}
      </div>

      {/* Verdict Row - Navy-First: transparent + left border only */}
      <div className={`p-4 rounded-lg border-l-4 bg-transparent ${
        isCritical ? 'border-red-500' :
        failedPolicies.length > 0 ? 'border-amber-500' :
        'border-emerald-500'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <StatusBadge
              hasRootCause={!!timeline.root_cause}
              isCritical={isCritical}
            />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {failedPolicies.length} of {timeline.policy_evaluations.length} policies failed
            </span>
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-500 font-mono">
            {new Date(timeline.events[0]?.timestamp || Date.now()).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Telemetry Row - Navy-First: subtle border only */}
      <div className="grid grid-cols-3 gap-4 text-sm p-3 bg-transparent border border-slate-700/30 rounded-lg">
        <MetaItem label="Model" value={timeline.model} />
        <MetaItem label="Latency" value={`${timeline.latency_ms}ms`} />
        <MetaItem label="Cost" value={`$${(timeline.cost_cents / 100).toFixed(4)}`} />
      </div>

      {/* Root Cause - Navy-First: transparent + amber left border */}
      {timeline.root_cause_badge && (
        <div className="bg-transparent border-l-4 border-amber-500 pl-4 py-3">
          <div className="flex items-start gap-3">
            <span className="text-amber-500 text-lg flex-shrink-0">🔎</span>
            <div className="space-y-3 flex-1">
              {/* Cause */}
              <div>
                <p className="text-xs font-medium text-amber-500 uppercase tracking-wide mb-1">
                  What Happened
                </p>
                <p className="font-medium text-amber-400">
                  {timeline.root_cause_badge}
                </p>
                <p className="text-sm text-slate-400 mt-1">{timeline.root_cause}</p>
              </div>
              {/* Consequence */}
              <div className="pt-3 border-t border-slate-700/30">
                <p className="text-xs font-medium text-amber-500 uppercase tracking-wide mb-1">
                  Business Impact
                </p>
                <p className="text-sm text-slate-300">
                  {getImpactSummary(timeline.root_cause_badge, isCritical)}
                </p>
              </div>
              {/* Recommended Action */}
              <div className="pt-3 border-t border-slate-700/30">
                <p className="text-xs font-medium text-amber-500 uppercase tracking-wide mb-1">
                  Recommended Action
                </p>
                <p className="text-sm text-slate-400">
                  {getRecommendedAction(timeline.root_cause_badge, isCritical)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Policy Evaluations - Navy-First: left-border rows, no filled pills */}
      <div className="space-y-3">
        <h3 className="font-medium text-gray-700 dark:text-gray-300 text-sm">Policy Evaluations</h3>

        {/* Failed policies - always visible, left-border emphasis */}
        {failedPolicies.length > 0 && (
          <div className="space-y-1">
            {failedPolicies.map((pe, idx) => (
              <PolicyRow key={`fail-${idx}`} evaluation={pe} />
            ))}
          </div>
        )}

        {/* Passed policies - collapsed by default, muted when shown */}
        {passedPolicies.length > 0 && (
          <div className="mt-2">
            {showAllPolicies ? (
              <>
                <div className="space-y-1 opacity-60">
                  {passedPolicies.map((pe, idx) => (
                    <PolicyRow key={`pass-${idx}`} evaluation={pe} />
                  ))}
                </div>
                <button
                  onClick={() => setShowAllPolicies(false)}
                  className="mt-2 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700
                             dark:hover:text-gray-300 transition-colors"
                >
                  ▲ Hide passed policies
                </button>
              </>
            ) : (
              <button
                onClick={() => setShowAllPolicies(true)}
                className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400
                           hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
              >
                <span className="text-emerald-500">✓</span>
                Show all policy checks ({passedPolicies.length} passed)
                <span className="ml-1">▼</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Visual Timeline - With emphasis on key events */}
      <div className="relative">
        <h3 className="font-medium text-gray-700 dark:text-gray-300 text-sm mb-4">Execution Trace</h3>

        {/* Timeline line */}
        <div className="absolute left-5 top-10 bottom-4 w-0.5 bg-gray-200 dark:bg-gray-700" />

        {/* Timeline events */}
        <div className="space-y-3">
          {timeline.events.map((event, idx) => (
            <TimelineEventCard
              key={idx}
              event={event}
              isLast={idx === timeline.events.length - 1}
              isKeyEvent={event.event === 'OUTPUT_GENERATED' || event.data?.result === 'FAIL'}
            />
          ))}
        </div>
      </div>

      {/* Severity Legend - Collapsed by default */}
      <details className="text-xs text-slate-500">
        <summary className="cursor-pointer hover:text-slate-300">
          Severity Legend
        </summary>
        <div className="mt-2 p-3 bg-transparent border border-slate-700/30 rounded grid grid-cols-3 gap-2">
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

// Status badge - Navy-First: outline only, no filled background
function StatusBadge({ hasRootCause, isCritical }: { hasRootCause: boolean; isCritical: boolean }) {
  if (isCritical) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm font-medium
                       bg-transparent border border-red-500/40 text-red-600 dark:text-red-400">
        <span>⛔</span> Traffic Blocked
      </span>
    );
  }
  if (hasRootCause) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm font-medium
                       bg-transparent border border-amber-500/40 text-amber-600 dark:text-amber-400">
        <span>⚠</span> Policy Gap
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm font-medium
                     bg-transparent border border-emerald-500/40 text-emerald-600 dark:text-emerald-400">
      <span>✓</span> OK
    </span>
  );
}

// Metadata item
function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-gray-500 dark:text-gray-400 text-xs">{label}</p>
      <p className="font-medium text-gray-800 dark:text-[#e6eaf2]">{value}</p>
    </div>
  );
}

// Severity badge for header - Navy-First: outline only
function SeverityBadge({ severity }: { severity: 'HIGH' | 'MEDIUM' | 'LOW' }) {
  const config = {
    HIGH: { border: 'border-red-500/40', text: 'text-red-600 dark:text-red-400', label: 'HIGH' },
    MEDIUM: { border: 'border-amber-500/40', text: 'text-amber-600 dark:text-amber-400', label: 'MED' },
    LOW: { border: 'border-emerald-500/40', text: 'text-emerald-600 dark:text-emerald-400', label: 'LOW' },
  };
  const c = config[severity];

  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-bold bg-transparent border ${c.border} ${c.text}`}>
      {c.label}
    </span>
  );
}

// Timeline event card component - with emphasis on key events
function TimelineEventCard({ event, isLast, isKeyEvent }: { event: TimelineEvent; isLast: boolean; isKeyEvent?: boolean }) {
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
  const isOutput = event.event === 'OUTPUT_GENERATED';

  // Determine styling based on event importance - Navy-First: no backgrounds
  const cardClasses = isPolicyBlock
    ? 'border-l-4 border-red-500'
    : isPolicyFail
    ? 'border-l-4 border-amber-500'
    : isOutput
    ? 'border-l-4 border-blue-500'
    : isKeyEvent
    ? 'border-l-4 border-slate-600'
    : '';

  return (
    <div className={`relative flex gap-4 ${cardClasses} -mx-2 px-3 py-2 rounded-r`}>
      {/* Timeline dot - Navy-First: border only */}
      <div
        className={`relative z-10 w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0
                    bg-transparent border-2
                    ${isPolicyBlock ? 'border-red-500/50' :
                      isPolicyFail ? 'border-amber-500/50' :
                      isOutput ? 'border-blue-500/50' :
                      'border-slate-600'}`}
      >
        {isPolicyBlock ? (
          <span className="text-red-500 text-sm">⛔</span>
        ) : isPolicyFail ? (
          <span className="text-amber-500 text-sm">⚠</span>
        ) : isOutput ? (
          <span className="text-indigo-500 text-base">📤</span>
        ) : (
          <span className="text-base">{config.icon}</span>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          <span className={`font-medium text-sm ${
            isPolicyBlock ? 'text-red-700 dark:text-red-400' :
            isPolicyFail ? 'text-amber-700 dark:text-[#ffd18a]' :
            isOutput ? 'text-indigo-700 dark:text-indigo-400' :
            'text-gray-800 dark:text-gray-200'
          }`}>
            {formatEventName(event.event)}
          </span>
          {event.data?.result && (
            <ResultBadge result={event.data.result} action={event.data?.action} />
          )}
          <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">{time}</span>
          {event.duration_ms && event.duration_ms > 0 && (
            <span className="text-xs text-gray-400 dark:text-gray-500">({event.duration_ms}ms)</span>
          )}
        </div>

        {/* Event-specific content */}
        <EventContent event={event} />
      </div>
    </div>
  );
}

// Result badge - Navy-First: outline only, no filled background
function ResultBadge({ result, action }: { result: string; action?: string }) {
  // Use blocked styling only for actual blocks
  const effectiveResult = (action === 'block' || action === 'freeze') ? 'BLOCKED' : result;
  const config = RESULT_CONFIG[effectiveResult] || RESULT_CONFIG.PASS;

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium
                  bg-transparent ${config.color} ${config.darkColor} border ${config.border}`}
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
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <p className="truncate">{data.role}: "{data.content}"</p>
          {data.model_requested && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">Model: {data.model_requested}</p>
          )}
        </div>
      );

    case 'CONTEXT_RETRIEVED':
      return (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <p>Fields: {data.fields_retrieved?.join(', ') || 'None'}</p>
          {data.missing_fields?.length > 0 && (
            <p className="text-amber-600 dark:text-amber-400 text-xs mt-0.5">
              Missing: {data.missing_fields.join(', ')}
            </p>
          )}
        </div>
      );

    case 'POLICY_EVALUATED':
      return (
        <div className="text-sm">
          <p className="font-mono text-gray-700 dark:text-gray-300 text-xs">{data.policy}</p>
          {data.reason && (
            <p className={`mt-0.5 text-xs ${data.result === 'FAIL' ? 'text-amber-600 dark:text-amber-400' : 'text-gray-500 dark:text-gray-400'}`}>
              {data.reason}
            </p>
          )}
          {data.expected_behavior && (
            <div className="mt-1.5 p-2 bg-transparent rounded border border-slate-700/50 text-xs">
              <p><span className="font-medium text-emerald-400">Expected:</span> <span className="text-slate-400">{data.expected_behavior}</span></p>
              <p><span className="font-medium text-amber-400">Actual:</span> <span className="text-slate-400">{data.actual_behavior}</span></p>
            </div>
          )}
        </div>
      );

    case 'MODEL_CALLED':
      return (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <p className="text-xs">
            <span className="font-mono">{data.model}</span>
            {' · '}{data.input_tokens} in / {data.output_tokens} out
          </p>
        </div>
      );

    case 'OUTPUT_GENERATED':
      return (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <p className="italic text-xs truncate">"{data.content}"</p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
            {data.tokens} tokens | ${(data.cost_cents / 100).toFixed(4)}
          </p>
        </div>
      );

    case 'LOGGED':
      return (
        <div className="text-xs text-gray-400 dark:text-gray-500">
          Incident logged: {data.incident_id}
        </div>
      );

    default:
      // V-004 Fix: Use truncateValue instead of raw JSON.stringify
      return (
        <pre className="text-xs text-slate-400 bg-transparent border border-slate-700/30 p-2 rounded overflow-x-auto max-h-24">
          {truncateValue(data, { maxChars: 200, maxDepth: 2 })}
        </pre>
      );
  }
}

/**
 * PolicyRow - Navy-First policy evaluation display
 *
 * Design rules:
 * - NO filled backgrounds (backgrounds never encode meaning)
 * - Left border for FAIL status (amber)
 * - Text color carries the status signal
 * - Inline reason when available
 * - Transparent background only
 */
function PolicyRow({ evaluation }: { evaluation: PolicyEvaluation }) {
  const config = RESULT_CONFIG[evaluation.result] || RESULT_CONFIG.PASS;
  const isFail = evaluation.result === 'FAIL';

  return (
    <div
      className={`
        flex items-center gap-3 py-2 px-3
        bg-transparent
        ${isFail ? `border-l-3 ${config.border.replace('/40', '')}` : 'border-l-3 border-transparent'}
      `}
      style={{ borderLeftWidth: '3px' }}
    >
      {/* Policy name */}
      <span className={`font-mono text-sm ${isFail ? `${config.color} ${config.darkColor}` : 'text-slate-500 dark:text-slate-400'}`}>
        {evaluation.policy}
      </span>

      {/* Status label */}
      <span className={`text-xs font-medium ${config.color} ${config.darkColor}`}>
        {config.label}
      </span>

      {/* Inline reason - the key UX improvement */}
      {evaluation.reason && (
        <>
          <span className="text-slate-500 dark:text-slate-600">—</span>
          <span className="text-xs text-slate-500 dark:text-slate-400 truncate">
            {evaluation.reason}
          </span>
        </>
      )}
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

// Get recommended action for root cause
function getRecommendedAction(rootCauseBadge: string, isCritical: boolean): string {
  const badge = rootCauseBadge.toLowerCase();

  // Critical actions
  if (isCritical) {
    if (badge.includes('injection') || badge.includes('jailbreak')) {
      return 'Review attack pattern. Consider adding to blocklist. Notify security team if novel vector.';
    }
    if (badge.includes('cost') || badge.includes('budget')) {
      return 'Review cost thresholds. Consider per-request limits. Check for runaway loops.';
    }
    if (badge.includes('rate') || badge.includes('throttle')) {
      return 'Review rate limit configuration. Check if legitimate traffic spike or abuse pattern.';
    }
    return 'Review incident details. Determine if block should remain or traffic can resume.';
  }

  // Non-critical recommendations
  if (badge.includes('pii') || badge.includes('privacy')) {
    return 'Add PII scrubbing to output filter. Review what data is being passed to context.';
  }
  if (badge.includes('hallucination') || badge.includes('accuracy')) {
    return 'Add citation requirements to prompt. Consider fact-checking integration.';
  }
  if (badge.includes('tone') || badge.includes('sentiment')) {
    return 'Review system prompt for brand voice guidelines. Adjust temperature or model.';
  }
  if (badge.includes('contract') || badge.includes('legal')) {
    return 'Add contract/commitment detection to policy. Review output filter rules.';
  }
  if (badge.includes('off-topic') || badge.includes('scope')) {
    return 'Tighten scope constraints in system prompt. Add topic guardrails.';
  }

  // Default
  return 'Review policy configuration. Consider if gap requires rule adjustment or is acceptable.';
}

export default DecisionTimeline;
