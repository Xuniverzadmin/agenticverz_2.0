// FailuresRecoveryPanel Component - Right Bottom Pane
// Shows failures (M9), recoveries (M10), policies (M19), and drift events (M18)

import { AlertTriangle, RefreshCcw, Shield, TrendingDown, CheckCircle, XCircle } from 'lucide-react';
import type { PolicyEvent, DriftEvent, LogEvent } from '@/types/worker';
import clsx from 'clsx';

interface FailuresRecoveryPanelProps {
  policyEvents: PolicyEvent[];
  driftEvents: DriftEvent[];
  recoveries: Array<{ stage: string; recovery: string }>;
  logs: LogEvent[];
}

type EventEntry = {
  type: 'failure' | 'recovery' | 'policy' | 'drift';
  engine: string;
  description: string;
  status: 'success' | 'warning' | 'error' | 'info';
  stage?: string;
};

const ENGINE_ICONS: Record<string, React.ReactNode> = {
  M9: <AlertTriangle className="w-4 h-4 text-orange-500" />,
  M10: <RefreshCcw className="w-4 h-4 text-green-500" />,
  M19: <Shield className="w-4 h-4 text-purple-500" />,
  M18: <TrendingDown className="w-4 h-4 text-pink-500" />,
};

const TYPE_BADGES: Record<EventEntry['type'], { bg: string; text: string }> = {
  failure: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300' },
  recovery: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300' },
  policy: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-700 dark:text-purple-300' },
  drift: { bg: 'bg-pink-100 dark:bg-pink-900/30', text: 'text-pink-700 dark:text-pink-300' },
};

function StatusIcon({ status }: { status: EventEntry['status'] }) {
  switch (status) {
    case 'success':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'error':
      return <XCircle className="w-4 h-4 text-red-500" />;
    case 'warning':
      return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    default:
      return <div className="w-4 h-4 rounded-full bg-blue-500" />;
  }
}

export function FailuresRecoveryPanel({
  policyEvents,
  driftEvents,
  recoveries,
  logs,
}: FailuresRecoveryPanelProps) {
  // Build unified event list
  const events: EventEntry[] = [];

  // Extract failure events from logs (M9)
  logs
    .filter((log) => log.agent === 'M9' || log.message.includes('Failure pattern'))
    .forEach((log) => {
      events.push({
        type: 'failure',
        engine: 'M9',
        description: log.message,
        status: 'warning',
        stage: log.stage_id,
      });
    });

  // Recovery events (M10)
  recoveries.forEach((rec) => {
    events.push({
      type: 'recovery',
      engine: 'M10',
      description: `Recovery applied: ${rec.recovery}`,
      status: 'success',
      stage: rec.stage,
    });
  });

  // Policy events (M19)
  policyEvents.forEach((policy) => {
    events.push({
      type: 'policy',
      engine: 'M19',
      description: policy.passed
        ? `Policy passed: ${policy.policy}`
        : `Policy violation: ${policy.policy} - ${policy.reason || 'No reason provided'}`,
      status: policy.passed ? 'success' : 'error',
      stage: policy.stage_id,
    });
  });

  // Drift events (M18)
  driftEvents.forEach((drift) => {
    events.push({
      type: 'drift',
      engine: 'M18',
      description: `Drift ${drift.aligned ? 'within' : 'exceeded'} threshold: ${(drift.drift_score * 100).toFixed(0)}% (max ${(drift.threshold * 100).toFixed(0)}%)`,
      status: drift.aligned ? 'info' : 'warning',
      stage: drift.stage_id,
    });
  });

  // Count by type
  const counts = {
    failures: events.filter((e) => e.type === 'failure').length,
    recoveries: events.filter((e) => e.type === 'recovery').length,
    policies: events.filter((e) => e.type === 'policy').length,
    drifts: events.filter((e) => e.type === 'drift').length,
  };

  const policyPassed = policyEvents.filter((p) => p.passed).length;
  const policyFailed = policyEvents.filter((p) => !p.passed).length;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-purple-500" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            Failures, Policies & Recovery
          </h3>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          M9 Failures • M10 Recovery • M18 Drift • M19 Policy
        </p>
      </div>

      {/* Summary Cards */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-4 gap-2">
          <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded-lg text-center">
            <div className="text-lg font-bold text-red-600 dark:text-red-400">
              {counts.failures}
            </div>
            <div className="text-xs text-red-500 dark:text-red-400">Failures</div>
          </div>
          <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg text-center">
            <div className="text-lg font-bold text-green-600 dark:text-green-400">
              {counts.recoveries}
            </div>
            <div className="text-xs text-green-500 dark:text-green-400">Recovered</div>
          </div>
          <div className="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-center">
            <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
              {policyPassed}/{policyPassed + policyFailed}
            </div>
            <div className="text-xs text-purple-500 dark:text-purple-400">Policies</div>
          </div>
          <div className="p-2 bg-pink-50 dark:bg-pink-900/20 rounded-lg text-center">
            <div className="text-lg font-bold text-pink-600 dark:text-pink-400">
              {counts.drifts}
            </div>
            <div className="text-xs text-pink-500 dark:text-pink-400">Drift Checks</div>
          </div>
        </div>
      </div>

      {/* Event Table */}
      <div className="flex-1 overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-sm text-gray-400 text-center py-8">
            No events recorded yet
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Event
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Engine
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {events.map((event, index) => (
                <tr
                  key={index}
                  className={clsx(
                    'hover:bg-gray-50 dark:hover:bg-gray-800/50',
                    event.status === 'error' && 'bg-red-50/50 dark:bg-red-900/10'
                  )}
                >
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2">
                      <StatusIcon status={event.status} />
                      <span
                        className={clsx(
                          'px-2 py-0.5 text-xs font-medium rounded-full capitalize',
                          TYPE_BADGES[event.type].bg,
                          TYPE_BADGES[event.type].text
                        )}
                      >
                        {event.type}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2">
                      {ENGINE_ICONS[event.engine]}
                      <span className="text-sm font-mono text-gray-700 dark:text-gray-300">
                        {event.engine}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-2">
                    <div className="text-sm text-gray-600 dark:text-gray-300">
                      {event.description}
                    </div>
                    {event.stage && (
                      <div className="text-xs text-gray-400 mt-0.5">
                        Stage: {event.stage}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer Stats */}
      <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Total Events: {events.length}</span>
          {counts.failures > 0 && counts.recoveries > 0 && (
            <span className="text-green-600 dark:text-green-400">
              Recovery Rate: {((counts.recoveries / counts.failures) * 100).toFixed(0)}%
            </span>
          )}
          {policyFailed > 0 && (
            <span className="text-red-600 dark:text-red-400">
              {policyFailed} policy violation{policyFailed > 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
