// CompletionScore Component
// M16 Profile Tab - Shows overall completion with breakdown

import { Trophy, Star } from 'lucide-react';
import { Card, CardBody } from '@/components/common';
import { cn } from '@/lib/utils';

interface Breakdown {
  tasks: number;
  tests: number;
  criteria?: number;
  system?: number;
}

interface CompletionScoreProps {
  value: number; // 0-100
  breakdown?: Breakdown;
  threshold?: number; // Score needed to be "Ready to Publish"
  className?: string;
}

export function CompletionScore({ value, breakdown, threshold = 80, className }: CompletionScoreProps) {
  const isReady = value >= threshold;

  const scoreColor = value >= 80 ? 'text-green-600' :
    value >= 60 ? 'text-yellow-600' :
    value >= 40 ? 'text-orange-600' :
    'text-red-600';

  const ringColor = value >= 80 ? 'stroke-green-500' :
    value >= 60 ? 'stroke-yellow-500' :
    value >= 40 ? 'stroke-orange-500' :
    'stroke-red-500';

  // SVG circle progress
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const progress = ((100 - value) / 100) * circumference;

  return (
    <Card className={className}>
      <CardBody>
        <div className="flex items-center gap-6">
          {/* Circular Progress */}
          <div className="relative">
            <svg width="100" height="100" className="transform -rotate-90">
              {/* Background circle */}
              <circle
                cx="50"
                cy="50"
                r={radius}
                fill="none"
                stroke="currentColor"
                strokeWidth="8"
                className="text-gray-200 dark:text-gray-700"
              />
              {/* Progress circle */}
              <circle
                cx="50"
                cy="50"
                r={radius}
                fill="none"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={progress}
                className={cn('transition-all duration-500', ringColor)}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={cn('text-2xl font-bold', scoreColor)}>
                {value}%
              </span>
            </div>
          </div>

          {/* Details */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Trophy className={cn('size-5', isReady ? 'text-yellow-500' : 'text-gray-400')} />
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Completion Score
              </h3>
            </div>

            {isReady ? (
              <div className="flex items-center gap-1.5 px-2 py-1 bg-green-100 dark:bg-green-900/30 rounded-full w-fit mb-3">
                <Star className="size-3 text-yellow-500" />
                <span className="text-xs font-medium text-green-700 dark:text-green-400">
                  Ready to Publish
                </span>
              </div>
            ) : (
              <p className="text-xs text-gray-500 mb-3">
                Needs {threshold}% to be ready ({threshold - value}% more)
              </p>
            )}

            {/* Breakdown */}
            {breakdown && (
              <div className="space-y-1.5">
                <BreakdownBar label="Tasks" value={breakdown.tasks} />
                <BreakdownBar label="Tests" value={breakdown.tests} />
                {breakdown.criteria !== undefined && (
                  <BreakdownBar label="Criteria" value={breakdown.criteria} />
                )}
                {breakdown.system !== undefined && (
                  <BreakdownBar label="System" value={breakdown.system} />
                )}
              </div>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function BreakdownBar({ label, value }: { label: string; value: number }) {
  const barColor = value >= 80 ? 'bg-green-500' :
    value >= 60 ? 'bg-yellow-500' :
    value >= 40 ? 'bg-orange-500' :
    'bg-red-500';

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 w-14">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', barColor)}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-xs text-gray-600 dark:text-gray-400 w-8 text-right">
        {value}%
      </span>
    </div>
  );
}
