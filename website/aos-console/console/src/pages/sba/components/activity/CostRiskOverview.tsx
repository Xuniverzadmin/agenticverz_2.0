// CostRiskOverview Component
// M16 Activity Tab - Shows cost and risk levels per worker

import { DollarSign, AlertTriangle } from 'lucide-react';
import { Card, CardBody } from '@/components/common';
import { cn } from '@/lib/utils';

export interface WorkerMetrics {
  id: string;
  name?: string;
  cost: 'low' | 'medium' | 'high';
  risk: number; // 0-1
  budget_used: number; // percentage 0-100
}

interface CostRiskOverviewProps {
  workers: WorkerMetrics[];
  onClick?: (worker: WorkerMetrics) => void;
  className?: string;
}

export function CostRiskOverview({ workers, onClick, className }: CostRiskOverviewProps) {
  if (workers.length === 0) {
    return (
      <Card className={className}>
        <CardBody>
          <div className="text-center py-6 text-gray-500">
            <DollarSign className="mx-auto mb-2 text-gray-400" size={24} />
            No active workers
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardBody>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
            Cost & Risk Overview
          </h3>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500" /> Low
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-yellow-500" /> Medium
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500" /> High
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {workers.map((worker) => (
            <WorkerCard
              key={worker.id}
              worker={worker}
              onClick={() => onClick?.(worker)}
            />
          ))}
        </div>
      </CardBody>
    </Card>
  );
}

function WorkerCard({ worker, onClick }: { worker: WorkerMetrics; onClick?: () => void }) {
  const costColor = worker.cost === 'low' ? 'bg-green-500' :
    worker.cost === 'medium' ? 'bg-yellow-500' : 'bg-red-500';

  const riskColor = worker.risk < 0.3 ? 'text-green-600' :
    worker.risk < 0.6 ? 'text-yellow-600' : 'text-red-600';

  const budgetColor = worker.budget_used < 50 ? 'bg-green-500' :
    worker.budget_used < 80 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <button
      className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
          {worker.name || worker.id}
        </span>
        <span className={cn('w-2 h-2 rounded-full', costColor)} />
      </div>

      <div className="space-y-2">
        {/* Risk */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Risk</span>
          <span className={cn('text-xs font-medium', riskColor)}>
            {Math.round(worker.risk * 100)}%
          </span>
        </div>

        {/* Budget */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500">Budget</span>
            <span className="text-xs text-gray-600 dark:text-gray-400">
              {worker.budget_used}%
            </span>
          </div>
          <div className="h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={cn('h-full rounded-full transition-all', budgetColor)}
              style={{ width: `${worker.budget_used}%` }}
            />
          </div>
        </div>
      </div>

      {worker.risk >= 0.7 && (
        <div className="mt-2 flex items-center gap-1 text-xs text-red-600">
          <AlertTriangle size={12} />
          High risk
        </div>
      )}
    </button>
  );
}
