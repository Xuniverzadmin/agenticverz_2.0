// HealthSummary Component
// M16 Health Tab - Shows overall health status

import { Heart, CheckCircle, AlertTriangle, XCircle, Shield } from 'lucide-react';
import { Card, CardBody } from '@/components/common';
import { cn } from '@/lib/utils';

interface HealthSummaryProps {
  healthy: boolean;
  errorCount: number;
  warningCount: number;
  lastChecked?: string;
  className?: string;
}

export function HealthSummary({
  healthy,
  errorCount,
  warningCount,
  lastChecked,
  className,
}: HealthSummaryProps) {
  const status = errorCount > 0 ? 'error' :
    warningCount > 0 ? 'warning' : 'healthy';

  const statusConfig = {
    healthy: {
      icon: CheckCircle,
      color: 'text-green-500',
      bg: 'bg-green-100 dark:bg-green-900/30',
      label: 'All Systems Healthy',
      description: 'Agent is configured correctly and ready to run',
    },
    warning: {
      icon: AlertTriangle,
      color: 'text-yellow-500',
      bg: 'bg-yellow-100 dark:bg-yellow-900/30',
      label: 'Warnings Detected',
      description: `${warningCount} issue${warningCount > 1 ? 's' : ''} need attention`,
    },
    error: {
      icon: XCircle,
      color: 'text-red-500',
      bg: 'bg-red-100 dark:bg-red-900/30',
      label: 'Issues Found',
      description: `${errorCount} error${errorCount > 1 ? 's' : ''} must be fixed before publishing`,
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <Card className={className}>
      <CardBody>
        <div className="flex items-center gap-4">
          <div className={cn('p-3 rounded-full', config.bg)}>
            <Icon className={cn('size-8', config.color)} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {config.label}
              </h3>
              {healthy && (
                <Shield className="size-4 text-green-500" />
              )}
            </div>
            <p className="text-sm text-gray-500 mt-0.5">
              {config.description}
            </p>
            {lastChecked && (
              <p className="text-xs text-gray-400 mt-1">
                Last checked: {lastChecked}
              </p>
            )}
          </div>

          {/* Stats */}
          <div className="flex items-center gap-4">
            <div className="text-center">
              <div className={cn(
                'text-2xl font-bold',
                errorCount > 0 ? 'text-red-600' : 'text-gray-300'
              )}>
                {errorCount}
              </div>
              <div className="text-xs text-gray-500">Errors</div>
            </div>
            <div className="text-center">
              <div className={cn(
                'text-2xl font-bold',
                warningCount > 0 ? 'text-yellow-600' : 'text-gray-300'
              )}>
                {warningCount}
              </div>
              <div className="text-xs text-gray-500">Warnings</div>
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
