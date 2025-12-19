// ExecutionTimeline Component - Left Top Pane
// Shows vertical timeline of execution stages with status indicators

import { CheckCircle, XCircle, Loader2, Clock, RefreshCcw } from 'lucide-react';
import type { StageState, StageStatus } from '@/types/worker';
import clsx from 'clsx';

interface ExecutionTimelineProps {
  stages: StageState[];
  currentStageIndex: number;
}

const StatusIcon = ({ status }: { status: StageStatus }) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    case 'failed':
      return <XCircle className="w-5 h-5 text-red-500" />;
    case 'running':
      return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    case 'recovered':
      return <RefreshCcw className="w-5 h-5 text-yellow-500" />;
    case 'pending':
    default:
      return <Clock className="w-5 h-5 text-gray-400" />;
  }
};

const StatusBadge = ({ status }: { status: StageStatus }) => {
  const colors: Record<StageStatus, string> = {
    pending: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
    running: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    completed: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    recovered: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
  };

  return (
    <span className={clsx('px-2 py-0.5 text-xs font-medium rounded-full', colors[status])}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

export function ExecutionTimeline({ stages, currentStageIndex }: ExecutionTimelineProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
          Execution Timeline
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {currentStageIndex < stages.length
            ? `Stage ${currentStageIndex + 1} of ${stages.length}`
            : 'All stages completed'}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-1">
          {stages.map((stage, index) => (
            <div
              key={stage.id}
              className={clsx(
                'relative flex items-start gap-3 p-3 rounded-lg transition-colors',
                stage.status === 'running' && 'bg-blue-50 dark:bg-blue-900/20',
                stage.status === 'failed' && 'bg-red-50 dark:bg-red-900/20',
                stage.status === 'recovered' && 'bg-yellow-50 dark:bg-yellow-900/20'
              )}
            >
              {/* Timeline connector */}
              {index < stages.length - 1 && (
                <div
                  className={clsx(
                    'absolute left-[22px] top-10 w-0.5 h-[calc(100%-16px)]',
                    stage.status === 'completed' || stage.status === 'recovered'
                      ? 'bg-green-300 dark:bg-green-700'
                      : 'bg-gray-200 dark:bg-gray-700'
                  )}
                />
              )}

              {/* Status icon */}
              <div className="flex-shrink-0 z-10">
                <StatusIcon status={stage.status} />
              </div>

              {/* Stage content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-sm text-gray-900 dark:text-white">
                    {stage.name}
                  </span>
                  <StatusBadge status={stage.status} />
                </div>

                {/* Agent info */}
                {stage.agent && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Agent: <span className="font-mono">{stage.agent}</span>
                  </p>
                )}

                {/* Metrics */}
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                  {stage.duration_ms !== undefined && (
                    <span>{stage.duration_ms.toFixed(0)}ms</span>
                  )}
                  {stage.tokens !== undefined && (
                    <span>{stage.tokens} tokens</span>
                  )}
                  {stage.drift_score !== undefined && (
                    <span
                      className={clsx(
                        stage.drift_score < 0.2
                          ? 'text-green-600'
                          : stage.drift_score < 0.35
                          ? 'text-yellow-600'
                          : 'text-red-600'
                      )}
                    >
                      Drift: {(stage.drift_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                {/* Error message */}
                {stage.error && (
                  <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                    {stage.error}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
