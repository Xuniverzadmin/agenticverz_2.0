// RoutingDashboard Component - Left Bottom Pane
// Shows CARE routing decisions, agent selection, and strategy graph

import { useEffect } from 'react';
import { Network, Zap, TrendingUp, Shield } from 'lucide-react';
import type { RoutingDecisionEvent, DriftEvent } from '@/types/worker';
import { logger } from '../../../lib/consoleLogger';
import clsx from 'clsx';

interface RoutingDashboardProps {
  routingDecisions: RoutingDecisionEvent[];
  driftEvents: DriftEvent[];
  artifacts: Array<{ artifact_name: string; artifact_type: string }>;
}

function ComplexityBar({ value }: { value: number }) {
  const percentage = Math.min(100, Math.max(0, value * 100));
  const color =
    value < 0.4
      ? 'bg-green-500'
      : value < 0.7
      ? 'bg-yellow-500'
      : 'bg-red-500';

  return (
    <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
      <div
        className={clsx('h-full transition-all duration-500', color)}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

function ConfidenceBadge({ value }: { value: number }) {
  const color =
    value >= 0.8
      ? 'text-green-600 bg-green-100 dark:bg-green-900/30'
      : value >= 0.6
      ? 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30'
      : 'text-red-600 bg-red-100 dark:bg-red-900/30';

  return (
    <span className={clsx('px-2 py-0.5 text-xs font-medium rounded', color)}>
      {(value * 100).toFixed(0)}% conf
    </span>
  );
}

export function RoutingDashboard({
  routingDecisions,
  driftEvents,
  artifacts,
}: RoutingDashboardProps) {
  useEffect(() => {
    logger.componentMount('RoutingDashboard');
    return () => logger.componentUnmount('RoutingDashboard');
  }, []);

  const latestDecisions = routingDecisions.slice(-4);
  const avgComplexity =
    routingDecisions.length > 0
      ? routingDecisions.reduce((sum, d) => sum + d.complexity, 0) /
        routingDecisions.length
      : 0;
  const avgDrift =
    driftEvents.length > 0
      ? driftEvents.reduce((sum, d) => sum + d.drift_score, 0) / driftEvents.length
      : 0;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-purple-500" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
            CARE Routing Dashboard
          </h3>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          M17 Complexity-Aware Routing Engine
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-3.5 h-3.5 text-yellow-500" />
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Avg Complexity
              </span>
            </div>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {(avgComplexity * 100).toFixed(0)}%
            </div>
            <ComplexityBar value={avgComplexity} />
          </div>

          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-3.5 h-3.5 text-blue-500" />
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Avg Drift
              </span>
            </div>
            <div
              className={clsx(
                'text-lg font-semibold',
                avgDrift < 0.2
                  ? 'text-green-600'
                  : avgDrift < 0.35
                  ? 'text-yellow-600'
                  : 'text-red-600'
              )}
            >
              {(avgDrift * 100).toFixed(0)}%
            </div>
          </div>

          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Shield className="w-3.5 h-3.5 text-green-500" />
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Artifacts
              </span>
            </div>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {artifacts.length}
            </div>
          </div>
        </div>

        {/* Routing Decisions */}
        <div>
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
            Recent Routing Decisions
          </h4>

          {latestDecisions.length === 0 ? (
            <div className="text-sm text-gray-400 text-center py-4">
              No routing decisions yet
            </div>
          ) : (
            <div className="space-y-2">
              {latestDecisions.map((decision, index) => (
                <div
                  key={index}
                  className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                      {decision.stage_id.replace('_', ' ')}
                    </span>
                    <ConfidenceBadge value={decision.confidence} />
                  </div>

                  <div className="text-xs text-gray-600 dark:text-gray-300 mb-2">
                    Selected:{' '}
                    <span className="font-mono text-purple-600 dark:text-purple-400">
                      {decision.selected_agent}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">Complexity:</span>
                    <div className="flex-1">
                      <ComplexityBar value={decision.complexity} />
                    </div>
                    <span className="text-xs text-gray-500">
                      {(decision.complexity * 100).toFixed(0)}%
                    </span>
                  </div>

                  {decision.alternatives && decision.alternatives.length > 0 && (
                    <div className="mt-2 text-xs text-gray-400">
                      Alternatives: {decision.alternatives.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Drift Events */}
        {driftEvents.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
              Drift Detection (M18)
            </h4>
            <div className="space-y-2">
              {driftEvents.map((drift, index) => (
                <div
                  key={index}
                  className={clsx(
                    'p-2 rounded-lg text-xs flex items-center justify-between',
                    drift.aligned
                      ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                      : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                  )}
                >
                  <span className="capitalize">{drift.stage_id}</span>
                  <span>
                    {(drift.drift_score * 100).toFixed(0)}% (threshold:{' '}
                    {(drift.threshold * 100).toFixed(0)}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Artifacts */}
        {artifacts.length > 0 && (
          <div>
            <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
              Generated Artifacts
            </h4>
            <div className="flex flex-wrap gap-2">
              {artifacts.map((artifact, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded-full"
                >
                  {artifact.artifact_name}.{artifact.artifact_type}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
