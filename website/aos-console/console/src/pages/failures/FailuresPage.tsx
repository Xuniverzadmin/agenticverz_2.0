import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, Search, RefreshCw, Shield, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardHeader, CardBody, Spinner, StatusBadge, Button, Input } from '@/components/common';
import { getFailures, getFailureStats, updateRecoveryStatus, type Failure } from '@/api/failures';
import { suggestRecovery } from '@/api/recovery';
import { truncateId } from '@/lib/utils';
import { cn } from '@/lib/utils';

export default function FailuresPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: failures, isLoading, refetch } = useQuery({
    queryKey: ['failures', statusFilter],
    queryFn: () => getFailures({ limit: 50, status: statusFilter || undefined }),
    refetchInterval: 30000,
  });

  const { data: stats } = useQuery({
    queryKey: ['failure-stats'],
    queryFn: getFailureStats,
    refetchInterval: 60000,
  });

  const suggestMutation = useMutation({
    mutationFn: (failureId: string) => suggestRecovery(failureId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['failures'] });
      queryClient.invalidateQueries({ queryKey: ['recovery-candidates'] });
    },
  });

  const dismissMutation = useMutation({
    mutationFn: (failureId: string) => updateRecoveryStatus(failureId, 'dismissed'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['failures'] });
    },
  });

  const failureList = failures?.items || [];
  const filteredFailures = failureList.filter((failure: Failure) =>
    !search ||
    failure.error_type.toLowerCase().includes(search.toLowerCase()) ||
    failure.error_message.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Failure Pattern Monitor
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Track and analyze execution failures for self-healing
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw size={16} />
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Total Failures</p>
            <p className="text-2xl font-semibold">{stats?.total || 0}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Recovery Rate</p>
            <p className="text-2xl font-semibold text-green-600">
              {stats?.recovery_rate || 0}%
            </p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">By Type</p>
            <div className="text-sm mt-1">
              {Object.entries(stats?.by_type || {}).slice(0, 3).map(([type, count]) => (
                <div key={type} className="flex justify-between">
                  <span className="text-gray-600">{type}</span>
                  <span className="font-medium">{count as number}</span>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">By Status</p>
            <div className="text-sm mt-1">
              {Object.entries(stats?.by_status || {}).slice(0, 3).map(([status, count]) => (
                <div key={status} className="flex justify-between">
                  <span className="text-gray-600">{status}</span>
                  <span className="font-medium">{count as number}</span>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardBody>
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px] relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search failures..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900"
              />
            </div>
            <select
              className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="suggested">Suggested</option>
              <option value="recovered">Recovered</option>
              <option value="dismissed">Dismissed</option>
            </select>
          </div>
        </CardBody>
      </Card>

      {/* Failures List */}
      <Card>
        <CardHeader title={`Failures (${filteredFailures.length})`} />
        <CardBody className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-8"><Spinner size="lg" /></div>
          ) : filteredFailures.length > 0 ? (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredFailures.map((failure: Failure) => (
                <div key={failure.id} className="p-4">
                  <div
                    className="flex items-center justify-between cursor-pointer"
                    onClick={() => setExpandedId(expandedId === failure.id ? null : failure.id)}
                  >
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="text-red-500" size={20} />
                      <div>
                        <span className="font-mono text-sm font-medium text-red-600">
                          {failure.error_type}
                        </span>
                        <p className="text-sm text-gray-600 dark:text-gray-400 truncate max-w-md">
                          {failure.error_message}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <StatusBadge status={failure.recovery_status || 'pending'} />
                      <span className="text-xs text-gray-400">
                        {new Date(failure.created_at).toLocaleString()}
                      </span>
                      {expandedId === failure.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </div>

                  {expandedId === failure.id && (
                    <div className="mt-4 pl-8 space-y-4">
                      <div>
                        <p className="text-xs font-medium text-gray-500 uppercase mb-1">Run ID</p>
                        <p className="font-mono text-sm">{failure.run_id}</p>
                      </div>
                      {failure.step_id && (
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase mb-1">Step ID</p>
                          <p className="font-mono text-sm">{failure.step_id}</p>
                        </div>
                      )}
                      {failure.stack_trace && (
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase mb-1">Stack Trace</p>
                          <pre className="bg-gray-50 dark:bg-gray-800 p-3 rounded text-xs overflow-auto max-h-40">
                            {failure.stack_trace}
                          </pre>
                        </div>
                      )}
                      {failure.context && (
                        <div>
                          <p className="text-xs font-medium text-gray-500 uppercase mb-1">Context</p>
                          <pre className="bg-gray-50 dark:bg-gray-800 p-3 rounded text-xs overflow-auto max-h-40">
                            {JSON.stringify(failure.context, null, 2)}
                          </pre>
                        </div>
                      )}
                      <div className="flex gap-2 pt-2">
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => suggestMutation.mutate(failure.id)}
                          disabled={suggestMutation.isPending || failure.recovery_status !== 'pending'}
                        >
                          Suggest Recovery
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => dismissMutation.mutate(failure.id)}
                          disabled={dismissMutation.isPending || failure.recovery_status === 'dismissed'}
                        >
                          Dismiss
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="px-4 py-8 text-center text-gray-500">
              <Shield className="mx-auto mb-2 text-green-500" size={32} />
              No failures found
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
