// RetryLog Component
// M16 Activity Tab - Shows retry attempts with reasons and outcomes

import { RotateCcw, CheckCircle, XCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card, CardBody } from '@/components/common';
import { cn } from '@/lib/utils';

export interface RetryEntry {
  time: string;
  reason: string;
  attempt: number;
  outcome: 'success' | 'failure' | 'pending';
  risk_change?: number; // -1 to 1, negative is good
}

interface RetryLogProps {
  retries: RetryEntry[];
  maxDisplay?: number;
  className?: string;
}

export function RetryLog({ retries, maxDisplay = 10, className }: RetryLogProps) {
  const displayRetries = retries.slice(-maxDisplay).reverse();
  const successCount = retries.filter(r => r.outcome === 'success').length;
  const failureCount = retries.filter(r => r.outcome === 'failure').length;

  return (
    <Card className={className}>
      <CardBody>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <RotateCcw className="size-5 text-orange-500" />
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Retry Log
            </h3>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="text-green-600">{successCount} recovered</span>
            <span className="text-red-600">{failureCount} failed</span>
          </div>
        </div>

        {displayRetries.length > 0 ? (
          <div className="space-y-2">
            {displayRetries.map((retry, i) => (
              <RetryItem key={i} retry={retry} />
            ))}
            {retries.length > maxDisplay && (
              <div className="text-center text-xs text-gray-400 pt-2">
                + {retries.length - maxDisplay} more retries
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500 text-sm">
            No retries recorded
          </div>
        )}
      </CardBody>
    </Card>
  );
}

function RetryItem({ retry }: { retry: RetryEntry }) {
  const outcomeIcon = retry.outcome === 'success' ? (
    <CheckCircle className="size-4 text-green-500" />
  ) : retry.outcome === 'failure' ? (
    <XCircle className="size-4 text-red-500" />
  ) : (
    <RotateCcw className="size-4 text-yellow-500 animate-spin" />
  );

  const riskIcon = retry.risk_change === undefined ? null :
    retry.risk_change < -0.1 ? (
      <TrendingDown className="size-3 text-green-500" />
    ) : retry.risk_change > 0.1 ? (
      <TrendingUp className="size-3 text-red-500" />
    ) : (
      <Minus className="size-3 text-gray-400" />
    );

  const riskText = retry.risk_change === undefined ? null :
    retry.risk_change < -0.1 ? 'Risk decreased' :
    retry.risk_change > 0.1 ? 'Risk increased' :
    'Risk unchanged';

  return (
    <div className="flex items-start gap-3 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div className="flex-shrink-0 mt-0.5">
        {outcomeIcon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
            {retry.reason}
          </span>
          <span className="text-xs text-gray-400 flex-shrink-0">
            {retry.time}
          </span>
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className="text-xs text-gray-500">
            Attempt #{retry.attempt}
          </span>
          {riskIcon && (
            <span className={cn(
              'flex items-center gap-1 text-xs',
              retry.risk_change! < -0.1 ? 'text-green-600' :
              retry.risk_change! > 0.1 ? 'text-red-600' :
              'text-gray-400'
            )}>
              {riskIcon}
              {riskText}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
