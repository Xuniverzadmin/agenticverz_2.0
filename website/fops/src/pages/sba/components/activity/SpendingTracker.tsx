// SpendingTracker Component
// M16 Activity Tab - Shows actual vs projected spending

import { TrendingUp, AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Area, ComposedChart } from 'recharts';
import { Card, CardBody } from '@/components/common';
import { cn } from '@/lib/utils';

interface Anomaly {
  index: number;
  reason: string;
}

interface SpendingTrackerProps {
  actual: number[];
  projected: number[];
  budget_limit: number;
  anomalies?: Anomaly[];
  className?: string;
}

export function SpendingTracker({
  actual,
  projected,
  budget_limit,
  anomalies = [],
  className,
}: SpendingTrackerProps) {
  // Build chart data
  const data = actual.map((value, index) => ({
    index: index + 1,
    actual: value,
    projected: projected[index] || 0,
    isAnomaly: anomalies.some(a => a.index === index),
  }));

  const currentSpend = actual[actual.length - 1] || 0;
  const projectedSpend = projected[projected.length - 1] || 0;
  const isOverBudget = currentSpend > budget_limit;
  const isOverProjected = currentSpend > projectedSpend * 1.1; // 10% tolerance

  return (
    <Card className={cn(isOverBudget && 'border-red-300 dark:border-red-700', className)}>
      <CardBody>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <TrendingUp className={cn(
              'size-5',
              isOverBudget ? 'text-red-500' : 'text-blue-500'
            )} />
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Spending Tracker
            </h3>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              Actual
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-gray-400" />
              Projected
            </span>
          </div>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-xs text-gray-500">Current</div>
            <div className={cn(
              'text-lg font-semibold',
              isOverBudget ? 'text-red-600' : 'text-gray-900 dark:text-gray-100'
            )}>
              {currentSpend.toLocaleString()}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">Projected</div>
            <div className="text-lg font-semibold text-gray-600 dark:text-gray-400">
              {projectedSpend.toLocaleString()}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">Budget</div>
            <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {budget_limit.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Warnings */}
        {(isOverBudget || isOverProjected || anomalies.length > 0) && (
          <div className="mb-4 space-y-2">
            {isOverBudget && (
              <div className="flex items-center gap-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 rounded-lg text-sm text-red-700 dark:text-red-400">
                <AlertTriangle size={16} />
                Over budget by {(currentSpend - budget_limit).toLocaleString()} tokens
              </div>
            )}
            {isOverProjected && !isOverBudget && (
              <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg text-sm text-yellow-700 dark:text-yellow-400">
                <AlertTriangle size={16} />
                Spending above projected (+{Math.round((currentSpend / projectedSpend - 1) * 100)}%)
              </div>
            )}
            {anomalies.length > 0 && (
              <div className="flex items-center gap-2 px-3 py-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg text-sm text-orange-700 dark:text-orange-400">
                <AlertTriangle size={16} />
                {anomalies.length} spending spike{anomalies.length > 1 ? 's' : ''} detected
              </div>
            )}
          </div>
        )}

        {/* Chart */}
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <XAxis
                dataKey="index"
                tick={{ fontSize: 10 }}
                tickLine={false}
                axisLine={{ stroke: '#e5e7eb' }}
              />
              <YAxis
                tick={{ fontSize: 10 }}
                tickLine={false}
                axisLine={{ stroke: '#e5e7eb' }}
                tickFormatter={(v) => v.toLocaleString()}
              />
              <Tooltip
                content={({ payload }) => {
                  if (!payload?.[0]) return null;
                  const item = payload[0].payload;
                  return (
                    <div className="bg-white dark:bg-gray-800 p-2 rounded shadow-lg border text-xs">
                      <div>Actual: {item.actual.toLocaleString()}</div>
                      <div className="text-gray-500">Projected: {item.projected.toLocaleString()}</div>
                      {item.isAnomaly && (
                        <div className="text-orange-600 mt-1">Spike detected</div>
                      )}
                    </div>
                  );
                }}
              />
              <ReferenceLine
                y={budget_limit}
                stroke="#ef4444"
                strokeDasharray="3 3"
                label={{ value: 'Budget', position: 'right', fontSize: 10, fill: '#ef4444' }}
              />
              <Area
                type="monotone"
                dataKey="projected"
                fill="#e5e7eb"
                stroke="#9ca3af"
                strokeDasharray="3 3"
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={(props) => {
                  const { cx, cy, payload } = props;
                  if (payload.isAnomaly) {
                    return (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={5}
                        fill="#f97316"
                        stroke="#fff"
                        strokeWidth={2}
                      />
                    );
                  }
                  return <circle cx={cx} cy={cy} r={3} fill="#3b82f6" />;
                }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardBody>
    </Card>
  );
}
