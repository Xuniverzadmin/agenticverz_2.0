// PermissionsPanel Component
// M16 Profile Tab - Shows what agent is allowed to do

import { useState } from 'react';
import { Shield, Globe, Wrench, Server, AlertTriangle, ChevronDown, ChevronRight } from 'lucide-react';
import { Card, CardBody } from '@/components/common';
import { cn } from '@/lib/utils';

interface Violation {
  type: 'domain' | 'tool' | 'connection' | 'limit';
  message: string;
}

interface Limits {
  memory?: string;
  timeout?: string;
  budget?: number;
}

interface PermissionsPanelProps {
  domains: string[];
  tools: string[];
  contexts?: string[];
  limits?: Limits;
  violations?: Violation[];
  className?: string;
}

export function PermissionsPanel({
  domains,
  tools,
  contexts = [],
  limits,
  violations = [],
  className,
}: PermissionsPanelProps) {
  const [expanded, setExpanded] = useState(false);
  const hasViolations = violations.length > 0;

  return (
    <Card className={cn(hasViolations && 'border-red-300 dark:border-red-700', className)}>
      <CardBody>
        <button
          className="w-full flex items-center justify-between"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center gap-3">
            <div className={cn(
              'p-2 rounded-lg',
              hasViolations
                ? 'bg-red-100 dark:bg-red-900/30'
                : 'bg-green-100 dark:bg-green-900/30'
            )}>
              <Shield className={cn(
                'size-5',
                hasViolations
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-green-600 dark:text-green-400'
              )} />
            </div>
            <div className="text-left">
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Permissions
              </h3>
              <p className="text-xs text-gray-500">
                {domains.length} domains, {tools.length} tools
                {hasViolations && (
                  <span className="text-red-600 ml-2">
                    {violations.length} violation{violations.length > 1 ? 's' : ''}
                  </span>
                )}
              </p>
            </div>
          </div>
          {expanded ? (
            <ChevronDown className="text-gray-400" size={20} />
          ) : (
            <ChevronRight className="text-gray-400" size={20} />
          )}
        </button>

        {expanded && (
          <div className="mt-4 space-y-4 pt-4 border-t dark:border-gray-700">
            {/* Violations */}
            {hasViolations && (
              <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <div className="flex items-center gap-2 text-red-700 dark:text-red-400 text-sm font-medium mb-2">
                  <AlertTriangle size={16} />
                  Permission Violations
                </div>
                <ul className="space-y-1">
                  {violations.map((v, i) => (
                    <li key={i} className="text-sm text-red-600 dark:text-red-300">
                      {v.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Domains */}
            <div>
              <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                <Globe size={14} />
                Allowed Domains
              </div>
              <div className="flex flex-wrap gap-1.5">
                {domains.length > 0 ? domains.map((domain) => (
                  <span
                    key={domain}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 rounded"
                  >
                    {domain}
                  </span>
                )) : (
                  <span className="text-xs text-gray-400">None specified</span>
                )}
              </div>
            </div>

            {/* Tools */}
            <div>
              <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                <Wrench size={14} />
                Allowed Tools
              </div>
              <div className="flex flex-wrap gap-1.5">
                {tools.length > 0 ? tools.map((tool) => (
                  <span
                    key={tool}
                    className="px-2 py-1 text-xs bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 rounded font-mono"
                  >
                    {tool}
                  </span>
                )) : (
                  <span className="text-xs text-gray-400">None specified</span>
                )}
              </div>
            </div>

            {/* Contexts */}
            {contexts.length > 0 && (
              <div>
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                  <Server size={14} />
                  Allowed Contexts
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {contexts.map((ctx) => (
                    <span
                      key={ctx}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded"
                    >
                      {ctx}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Limits */}
            {limits && (
              <div>
                <div className="text-sm text-gray-500 mb-2">Resource Limits</div>
                <div className="grid grid-cols-3 gap-2">
                  {limits.memory && (
                    <div className="px-2 py-1.5 bg-gray-100 dark:bg-gray-700 rounded text-center">
                      <div className="text-xs text-gray-500">Memory</div>
                      <div className="text-sm font-medium">{limits.memory}</div>
                    </div>
                  )}
                  {limits.timeout && (
                    <div className="px-2 py-1.5 bg-gray-100 dark:bg-gray-700 rounded text-center">
                      <div className="text-xs text-gray-500">Timeout</div>
                      <div className="text-sm font-medium">{limits.timeout}</div>
                    </div>
                  )}
                  {limits.budget !== undefined && (
                    <div className="px-2 py-1.5 bg-gray-100 dark:bg-gray-700 rounded text-center">
                      <div className="text-xs text-gray-500">Budget</div>
                      <div className="text-sm font-medium">{limits.budget.toLocaleString()} tokens</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
