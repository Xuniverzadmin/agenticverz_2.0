// PurposeCard Component
// M16 Profile Tab - Shows agent purpose with alignment score

import { Target, TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardBody } from '@/components/common';
import { cn } from '@/lib/utils';

interface PurposeCardProps {
  description: string;
  alignment?: number; // 0-1, how well execution matches purpose
  className?: string;
}

export function PurposeCard({ description, alignment, className }: PurposeCardProps) {
  const alignmentPercent = alignment !== undefined ? Math.round(alignment * 100) : null;

  const alignmentColor = alignment === undefined ? 'text-gray-400' :
    alignment >= 0.8 ? 'text-green-600' :
    alignment >= 0.6 ? 'text-yellow-600' :
    'text-red-600';

  const alignmentBg = alignment === undefined ? 'bg-gray-100 dark:bg-gray-700' :
    alignment >= 0.8 ? 'bg-green-100 dark:bg-green-900/30' :
    alignment >= 0.6 ? 'bg-yellow-100 dark:bg-yellow-900/30' :
    'bg-red-100 dark:bg-red-900/30';

  return (
    <Card className={className}>
      <CardBody>
        <div className="flex items-start gap-4">
          <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
            <Target className="size-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2 mb-2">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                Purpose
              </h3>
              {alignmentPercent !== null && (
                <div className={cn('flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', alignmentBg, alignmentColor)}>
                  {alignment! >= 0.5 ? (
                    <TrendingUp size={12} />
                  ) : (
                    <TrendingDown size={12} />
                  )}
                  {alignmentPercent}% aligned
                </div>
              )}
            </div>
            <p className="text-gray-900 dark:text-gray-100">
              {description || 'No purpose defined'}
            </p>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
