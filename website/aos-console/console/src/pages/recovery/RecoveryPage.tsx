import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { RefreshCw, Check, X, Zap, Activity } from 'lucide-react';
import { Card, CardHeader, CardBody, Spinner, StatusBadge, Button } from '@/components/common';
import { getCandidates, getRecoveryStats, approveCandidate, deleteCandidate, type RecoveryCandidate } from '@/api/recovery';
import { cn } from '@/lib/utils';

export default function RecoveryPage() {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const queryClient = useQueryClient();

  const { data: candidates, isLoading, refetch } = useQuery({
    queryKey: ['recovery-candidates', statusFilter],
    queryFn: () => getCandidates({ limit: 50, status: statusFilter || undefined }),
    refetchInterval: 30000,
  });

  const { data: stats } = useQuery({
    queryKey: ['recovery-stats'],
    queryFn: getRecoveryStats,
    refetchInterval: 60000,
  });

  const approveMutation = useMutation({
    mutationFn: (candidateId: string) => approveCandidate(candidateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recovery-candidates'] });
      queryClient.invalidateQueries({ queryKey: ['recovery-stats'] });
      queryClient.invalidateQueries({ queryKey: ['failures'] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (candidateId: string) => deleteCandidate(candidateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recovery-candidates'] });
      queryClient.invalidateQueries({ queryKey: ['recovery-stats'] });
    },
  });

  const candidateList = Array.isArray(candidates) ? candidates : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
            Self-Healing Engine
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            AI-suggested recovery actions for failed executions
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
            <p className="text-sm text-gray-500">Total Candidates</p>
            <p className="text-2xl font-semibold">{stats?.total_candidates || 0}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Approved</p>
            <p className="text-2xl font-semibold text-green-600">{stats?.approved || 0}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Executed</p>
            <p className="text-2xl font-semibold text-blue-600">{stats?.executed || 0}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-500">Success Rate</p>
            <p className="text-2xl font-semibold text-purple-600">{stats?.success_rate || 0}%</p>
          </CardBody>
        </Card>
      </div>

      {/* Filter */}
      <Card>
        <CardBody>
          <div className="flex gap-4">
            <select
              className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="executed">Executed</option>
            </select>
          </div>
        </CardBody>
      </Card>

      {/* Candidates */}
      <Card>
        <CardHeader title={`Recovery Candidates (${candidateList.length})`} />
        <CardBody className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-8"><Spinner size="lg" /></div>
          ) : candidateList.length > 0 ? (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {candidateList.map((candidate: RecoveryCandidate) => (
                <div key={candidate.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Zap className={cn(
                          'size-5',
                          candidate.confidence > 0.8 ? 'text-green-500' :
                          candidate.confidence > 0.5 ? 'text-yellow-500' : 'text-gray-400'
                        )} />
                        <span className="font-medium">{candidate.suggested_action}</span>
                        <span className={cn(
                          'text-xs px-2 py-0.5 rounded-full',
                          candidate.confidence > 0.8 ? 'bg-green-100 text-green-700' :
                          candidate.confidence > 0.5 ? 'bg-yellow-100 text-yellow-700' :
                          'bg-gray-100 text-gray-700'
                        )}>
                          {Math.round(candidate.confidence * 100)}% confidence
                        </span>
                        <StatusBadge status={candidate.status} />
                      </div>
                      {candidate.reasoning && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 ml-8">
                          {candidate.reasoning}
                        </p>
                      )}
                      <div className="mt-2 ml-8 flex gap-4 text-xs text-gray-500">
                        <span>Failure: {candidate.failure_id}</span>
                        {candidate.estimated_cost_cents && (
                          <span>Est. Cost: ${(candidate.estimated_cost_cents / 100).toFixed(2)}</span>
                        )}
                        <span>{new Date(candidate.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                    {candidate.status === 'pending' && (
                      <div className="flex gap-2 ml-4">
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => approveMutation.mutate(candidate.id)}
                          disabled={approveMutation.isPending}
                        >
                          <Check size={14} className="mr-1" />
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => rejectMutation.mutate(candidate.id)}
                          disabled={rejectMutation.isPending}
                        >
                          <X size={14} className="mr-1" />
                          Reject
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="px-4 py-8 text-center text-gray-500">
              <Activity className="mx-auto mb-2 text-gray-400" size={32} />
              No recovery candidates
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
