// HealthTab Component
// M16 - Shows health checks: warnings, errors, and suggestions

import { useQuery } from '@tanstack/react-query';
import { RefreshCw } from 'lucide-react';
import { Spinner, Button } from '@/components/common';
import type { SBAAgent } from '@/types/sba';
import { HealthSummary } from '../health/HealthSummary';
import { HealthWarning, type HealthSeverity } from '../health/HealthWarning';

interface HealthCheck {
  severity: HealthSeverity;
  title: string;
  message: string;
  action?: string;
}

interface HealthCheckResult {
  healthy: boolean;
  errors: HealthCheck[];
  warnings: HealthCheck[];
  suggestions: HealthCheck[];
  checked_at: string;
}

interface HealthTabProps {
  agent: SBAAgent;
}

// Perform health checks based on agent SBA data
function performHealthChecks(agent: SBAAgent): HealthCheckResult {
  const errors: HealthCheck[] = [];
  const warnings: HealthCheck[] = [];
  const suggestions: HealthCheck[] = [];

  const sba = agent.sba;

  // Check 1: Missing purpose
  if (!sba?.winning_aspiration?.description) {
    errors.push({
      severity: 'error',
      title: 'No Purpose Defined',
      message: 'This agent has no purpose statement. Define what the agent is for.',
      action: 'Add Purpose',
    });
  }

  // Check 2: No tools defined
  if (!sba?.where_to_play?.allowed_tools?.length) {
    warnings.push({
      severity: 'warning',
      title: 'No Tools Specified',
      message: 'Agent has no allowed tools listed. It may not be able to perform any actions.',
      action: 'Configure Tools',
    });
  }

  // Check 3: No tasks defined
  if (!sba?.how_to_win?.tasks?.length) {
    warnings.push({
      severity: 'warning',
      title: 'No Tasks Defined',
      message: 'Agent has no tasks in its checklist. Define what it needs to accomplish.',
      action: 'Add Tasks',
    });
  }

  // Check 4: No governance
  if (sba?.enabling_management_systems?.governance !== 'BudgetLLM') {
    warnings.push({
      severity: 'warning',
      title: 'No Governance',
      message: 'Agent is not under governance control. Consider enabling BudgetLLM for cost management.',
      action: 'Enable Governance',
    });
  }

  // Check 5: Low fulfillment
  const fulfillment = sba?.how_to_win?.fulfillment_metric || 0;
  if (fulfillment < 0.5 && fulfillment > 0) {
    warnings.push({
      severity: 'warning',
      title: 'Low Completion Score',
      message: `Agent completion score is only ${Math.round(fulfillment * 100)}%. Review tasks and tests.`,
    });
  }

  // Check 6: No orchestrator
  if (!sba?.enabling_management_systems?.orchestrator) {
    errors.push({
      severity: 'error',
      title: 'No Workflow Defined',
      message: 'Agent has no orchestrator assigned. It cannot coordinate with other agents.',
      action: 'Assign Orchestrator',
    });
  }

  // Check 7: No dependencies declared but has tools
  if (sba?.where_to_play?.allowed_tools?.length && !sba?.capabilities_capacity?.dependencies?.length) {
    suggestions.push({
      severity: 'info',
      title: 'No Dependencies Listed',
      message: 'Agent uses tools but has no explicit dependencies. Consider declaring them for better tracking.',
    });
  }

  // Check 8: Not validated
  if (!agent.sba_validated) {
    errors.push({
      severity: 'error',
      title: 'Not Validated',
      message: 'Agent SBA schema has not passed validation. Fix validation errors before publishing.',
      action: 'Run Validation',
    });
  }

  return {
    healthy: errors.length === 0,
    errors,
    warnings,
    suggestions,
    checked_at: new Date().toLocaleTimeString(),
  };
}

export function HealthTab({ agent }: HealthTabProps) {
  const { data: healthResult, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['agent-health', agent.agent_id],
    queryFn: () => Promise.resolve(performHealthChecks(agent)),
    staleTime: 30000, // Cache for 30s
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  const result = healthResult || {
    healthy: true,
    errors: [],
    warnings: [],
    suggestions: [],
    checked_at: 'N/A',
  };

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center justify-between">
        <HealthSummary
          healthy={result.healthy}
          errorCount={result.errors.length}
          warningCount={result.warnings.length}
          lastChecked={result.checked_at}
          className="flex-1"
        />
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
          className="ml-4"
        >
          {isFetching ? <Spinner size="sm" /> : <RefreshCw size={16} />}
          Re-check
        </Button>
      </div>

      {/* Errors */}
      {result.errors.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-red-700 dark:text-red-400">
            Errors ({result.errors.length})
          </h3>
          {result.errors.map((error, i) => (
            <HealthWarning
              key={i}
              severity="error"
              title={error.title}
              message={error.message}
              action={error.action}
              onAction={() => console.log('Action:', error.action)}
            />
          ))}
        </div>
      )}

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
            Warnings ({result.warnings.length})
          </h3>
          {result.warnings.map((warning, i) => (
            <HealthWarning
              key={i}
              severity="warning"
              title={warning.title}
              message={warning.message}
              action={warning.action}
              onAction={() => console.log('Action:', warning.action)}
            />
          ))}
        </div>
      )}

      {/* Suggestions */}
      {result.suggestions.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-blue-700 dark:text-blue-400">
            Suggestions ({result.suggestions.length})
          </h3>
          {result.suggestions.map((suggestion, i) => (
            <HealthWarning
              key={i}
              severity="info"
              title={suggestion.title}
              message={suggestion.message}
            />
          ))}
        </div>
      )}

      {/* All clear message */}
      {result.healthy && result.errors.length === 0 && result.warnings.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p className="text-lg font-medium text-green-600 mb-1">Ready to Publish</p>
          <p className="text-sm">All health checks passed. This agent is properly configured.</p>
        </div>
      )}
    </div>
  );
}
