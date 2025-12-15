import { useQuery } from '@tanstack/react-query';
import { RefreshCw } from 'lucide-react';
import { getHealthStatus, getCapabilities, getFailureStats, getRecoveryStats } from '@/api/metrics';
import { Card, CardHeader, CardBody, Button, StatusBadge } from '@/components/common';
import { formatCredits } from '@/lib/utils';
import { cn } from '@/lib/utils';

export default function MetricsPage() {
  const { data: health, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: getHealthStatus,
    refetchInterval: 30000,
  });

  const { data: capabilities } = useQuery({
    queryKey: ['capabilities'],
    queryFn: getCapabilities,
    refetchInterval: 60000,
  });

  const { data: failureStats } = useQuery({
    queryKey: ['failure-stats'],
    queryFn: getFailureStats,
    refetchInterval: 60000,
  });

  const { data: recoveryStats } = useQuery({
    queryKey: ['recovery-stats'],
    queryFn: getRecoveryStats,
    refetchInterval: 60000,
  });

  const skills = capabilities?.skills || {};
  const budget = capabilities?.budget || {};
  const rateLimits = capabilities?.rate_limits || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Metrics & Health
        </h1>
        <Button variant="outline" icon={<RefreshCw size={16} />} onClick={() => refetchHealth()}>
          Refresh
        </Button>
      </div>

      {/* System Health */}
      <Card>
        <CardHeader title="System Health">
          <StatusBadge status={health?.status || 'unknown'} />
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-sm text-gray-500">Service</div>
              <div className="text-lg font-semibold">{health?.service || 'aos-backend'}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Version</div>
              <div className="text-lg font-semibold">{health?.version || '1.0.0'}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Last Check</div>
              <div className="text-lg font-semibold">
                {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : '-'}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Uptime</div>
              <div className="text-lg font-semibold text-green-600">Online</div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Budget Overview */}
      <Card>
        <CardHeader title="Budget" />
        <CardBody>
          <div className="grid grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {formatCredits(budget?.total_cents || 0)}
              </div>
              <div className="text-sm text-gray-500 mt-1">Total Budget</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {formatCredits(budget?.remaining_cents || 0)}
              </div>
              <div className="text-sm text-gray-500 mt-1">Remaining</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600">
                {formatCredits(budget?.per_step_max_cents || 0)}
              </div>
              <div className="text-sm text-gray-500 mt-1">Per-Step Max</div>
            </div>
          </div>
          <div className="mt-6">
            <div className="flex justify-between text-sm text-gray-500 mb-1">
              <span>Budget Usage</span>
              <span>
                {Math.round(((budget?.total_cents || 0) - (budget?.remaining_cents || 0)) / (budget?.total_cents || 1) * 100)}%
              </span>
            </div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all"
                style={{
                  width: `${((budget?.remaining_cents || 0) / (budget?.total_cents || 1)) * 100}%`
                }}
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Skills */}
      <Card>
        <CardHeader title="Skills" />
        <CardBody className="p-0">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Skill
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Cost
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Latency
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Rate Limit
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {Object.entries(skills).map(([name, skill]) => {
                const s = skill as {
                  available: boolean;
                  cost_estimate_cents: number;
                  avg_latency_ms: number;
                  rate_limit_remaining: number;
                  known_failure_patterns: string[];
                };
                return (
                  <tr key={name} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3 font-mono text-sm">{name}</td>
                    <td className="px-4 py-3">
                      <span className={cn(
                        'inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium',
                        s.available
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      )}>
                        <span className={cn('w-1.5 h-1.5 rounded-full', s.available ? 'bg-green-500' : 'bg-red-500')} />
                        {s.available ? 'Available' : 'Unavailable'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{formatCredits(s.cost_estimate_cents || 0)}</td>
                    <td className="px-4 py-3 text-sm">{s.avg_latency_ms || 0}ms</td>
                    <td className="px-4 py-3 text-sm">{s.rate_limit_remaining || 0} remaining</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </CardBody>
      </Card>

      {/* Rate Limits */}
      <Card>
        <CardHeader title="Rate Limits" />
        <CardBody>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(rateLimits).map(([name, limit]) => {
              const l = limit as { remaining: number; resets_in_seconds: number };
              return (
                <div key={name} className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="font-mono text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {name}
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {l.remaining}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    resets in {l.resets_in_seconds}s
                  </div>
                </div>
              );
            })}
          </div>
        </CardBody>
      </Card>

      {/* Failure & Recovery Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Failure Stats" />
          <CardBody>
            <div className="space-y-3">
              {Object.entries(failureStats || {}).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400 capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="font-semibold">{String(value)}</span>
                </div>
              ))}
              {!Object.keys(failureStats || {}).length && (
                <div className="text-center text-gray-500 py-4">No failure data</div>
              )}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Recovery Stats" />
          <CardBody>
            <div className="space-y-3">
              {Object.entries(recoveryStats || {}).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400 capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="font-semibold">{String(value)}</span>
                </div>
              ))}
              {!Object.keys(recoveryStats || {}).length && (
                <div className="text-center text-gray-500 py-4">No recovery data</div>
              )}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
