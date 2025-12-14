// HealthWarning Component
// M16 Health Tab - Shows individual warning/error cards

import { AlertTriangle, XCircle, Info, ArrowRight } from 'lucide-react';
import { Card, CardBody, Button } from '@/components/common';
import { cn } from '@/lib/utils';

export type HealthSeverity = 'error' | 'warning' | 'info';

interface HealthWarningProps {
  severity: HealthSeverity;
  title: string;
  message: string;
  action?: string;
  onAction?: () => void;
  className?: string;
}

const SEVERITY_CONFIG = {
  error: {
    icon: XCircle,
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    iconColor: 'text-red-500',
    titleColor: 'text-red-800 dark:text-red-300',
    textColor: 'text-red-700 dark:text-red-400',
  },
  warning: {
    icon: AlertTriangle,
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    iconColor: 'text-yellow-500',
    titleColor: 'text-yellow-800 dark:text-yellow-300',
    textColor: 'text-yellow-700 dark:text-yellow-400',
  },
  info: {
    icon: Info,
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    iconColor: 'text-blue-500',
    titleColor: 'text-blue-800 dark:text-blue-300',
    textColor: 'text-blue-700 dark:text-blue-400',
  },
};

export function HealthWarning({
  severity,
  title,
  message,
  action,
  onAction,
  className,
}: HealthWarningProps) {
  const config = SEVERITY_CONFIG[severity];
  const Icon = config.icon;

  return (
    <div className={cn(
      'p-4 rounded-lg border',
      config.bg,
      config.border,
      className
    )}>
      <div className="flex items-start gap-3">
        <Icon className={cn('size-5 flex-shrink-0 mt-0.5', config.iconColor)} />
        <div className="flex-1 min-w-0">
          <h4 className={cn('font-medium', config.titleColor)}>
            {title}
          </h4>
          <p className={cn('text-sm mt-1', config.textColor)}>
            {message}
          </p>
          {action && onAction && (
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={onAction}
            >
              {action}
              <ArrowRight size={14} />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
