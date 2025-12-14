// IssuesBlockers Component
// M16 Activity Tab - Shows current problems blocking the agent

import { AlertOctagon, Clock, Server, Wrench, GitBranch, Wallet, RotateCcw, ArrowRight } from 'lucide-react';
import { Card, CardBody, Button } from '@/components/common';
import { cn } from '@/lib/utils';

export type IssueType = 'dependency' | 'api' | 'tool' | 'circular' | 'budget';

export interface Issue {
  type: IssueType;
  message: string;
  since: string;
  action?: string;
  details?: string;
}

interface IssuesBlockersProps {
  issues: Issue[];
  onAction?: (issue: Issue, action: string) => void;
  className?: string;
}

const ISSUE_CONFIG: Record<IssueType, { icon: typeof AlertOctagon; color: string; label: string }> = {
  dependency: { icon: Clock, color: 'text-blue-500', label: 'Waiting' },
  api: { icon: Server, color: 'text-red-500', label: 'API Error' },
  tool: { icon: Wrench, color: 'text-orange-500', label: 'Missing Tool' },
  circular: { icon: GitBranch, color: 'text-purple-500', label: 'Circular Dep' },
  budget: { icon: Wallet, color: 'text-yellow-500', label: 'Budget' },
};

export function IssuesBlockers({ issues, onAction, className }: IssuesBlockersProps) {
  const criticalCount = issues.filter(i => i.type === 'api' || i.type === 'tool').length;

  return (
    <Card className={cn(criticalCount > 0 && 'border-red-300 dark:border-red-700', className)}>
      <CardBody>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertOctagon className={cn(
              'size-5',
              criticalCount > 0 ? 'text-red-500' : 'text-gray-400'
            )} />
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Issues & Blockers
            </h3>
          </div>
          {issues.length > 0 && (
            <span className={cn(
              'px-2 py-0.5 rounded-full text-xs font-medium',
              criticalCount > 0
                ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
            )}>
              {issues.length} issue{issues.length > 1 ? 's' : ''}
            </span>
          )}
        </div>

        {issues.length > 0 ? (
          <div className="space-y-3">
            {issues.map((issue, i) => (
              <IssueItem
                key={i}
                issue={issue}
                onAction={onAction}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500 text-sm">
            No issues - agent running smoothly
          </div>
        )}
      </CardBody>
    </Card>
  );
}

function IssueItem({ issue, onAction }: { issue: Issue; onAction?: (issue: Issue, action: string) => void }) {
  const config = ISSUE_CONFIG[issue.type];
  const Icon = config.icon;

  return (
    <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div className="flex items-start gap-3">
        <div className={cn('p-1.5 rounded-lg bg-white dark:bg-gray-700', config.color)}>
          <Icon size={16} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={cn('text-xs font-medium px-1.5 py-0.5 rounded', config.color, 'bg-opacity-10')}>
              {config.label}
            </span>
            <span className="text-xs text-gray-400">
              {issue.since}
            </span>
          </div>
          <p className="text-sm text-gray-900 dark:text-gray-100">
            {issue.message}
          </p>
          {issue.details && (
            <p className="text-xs text-gray-500 mt-1">
              {issue.details}
            </p>
          )}
        </div>
      </div>

      {issue.action && (
        <div className="mt-3 flex justify-end">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onAction?.(issue, issue.action!)}
          >
            {issue.action === 'Retry' && <RotateCcw size={14} />}
            {issue.action}
            <ArrowRight size={14} />
          </Button>
        </div>
      )}
    </div>
  );
}
