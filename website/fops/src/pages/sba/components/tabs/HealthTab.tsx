// HealthTab Component
// M16 - Shows health checks: warnings, errors, and suggestions

import { useQuery } from '@tanstack/react-query';
import { RefreshCw } from 'lucide-react';
import { Spinner, Button } from '@/components/common';
import type { SBAAgent } from '@/types/sba';
import { checkAgentHealth, type HealthCheckResponse, type HealthCheckItem } from '@/api/sba';
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

// Transform API response to UI format
function transformHealthResponse(response: HealthCheckResponse): HealthCheckResult {
  const mapItem = (item: HealthCheckItem): HealthCheck => ({
    severity: item.severity as HealthSeverity,
    title: item.title,
    message: item.message,
    action: item.action,
  });

  return {
    healthy: response.healthy,
    errors: response.errors.map(mapItem),
    warnings: response.warnings.map(mapItem),
    suggestions: response.suggestions.map(mapItem),
    checked_at: new Date(response.checked_at).toLocaleTimeString(),
  };
}

export function HealthTab({ agent }: HealthTabProps) {
  const { data: healthResult, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['agent-health', agent.agent_id],
    queryFn: async () => {
      const response = await checkAgentHealth(agent.agent_id);
      return transformHealthResponse(response);
    },
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
