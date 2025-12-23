import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ArrowRight, Activity, Cpu, Wallet, AlertTriangle, Shield, GitBranch, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardBody, Spinner, StatusBadge } from '@/components/common';
import { getHealth, getDeterminismStatus } from '@/api/health';
import { getCapabilities, getSkills } from '@/api/runtime';
import { getFailures, getFailureStats } from '@/api/failures';
import { getCandidates, getRecoveryStats } from '@/api/recovery';
import { getTraces } from '@/api/traces';
import { formatCredits, truncateId } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color?: string;
  subtitle?: string;
}

function MetricCard({ title, value, icon, color = 'blue', subtitle }: MetricCardProps) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
    green: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
    yellow: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400',
    red: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
    purple: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
  };

  return (
    <Card>
      <CardBody>
        <div className="flex items-center gap-4">
          <div className={cn('p-3 rounded-lg', colors[color])}>
            {icon}
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
            <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
              {value}
            </p>
            {subtitle && (
              <p className="text-xs text-gray-400 dark:text-gray-500">{subtitle}</p>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

export default function DashboardPage() {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 30000,
  });

  const { data: determinism } = useQuery({
    queryKey: ['determinism'],
    queryFn: getDeterminismStatus,
    refetchInterval: 60000,
  });

  const { data: capabilities } = useQuery({
    queryKey: ['capabilities'],
    queryFn: getCapabilities,
    refetchInterval: 60000,
  });

  const { data: skills } = useQuery({
    queryKey: ['skills'],
    queryFn: getSkills,
    refetchInterval: 60000,
  });

  const { data: failureStats } = useQuery({
    queryKey: ['failure-stats'],
    queryFn: getFailureStats,
    refetchInterval: 30000,
  });

  const { data: unrecoveredFailures } = useQuery({
    queryKey: ['failures-unrecovered'],
    queryFn: () => getFailures({ status: 'pending', limit: 10 }),
    refetchInterval: 30000,
  });

  const { data: recoveryCandidates } = useQuery({
    queryKey: ['recovery-candidates'],
    queryFn: () => getCandidates({ limit: 10 }),
    refetchInterval: 30000,
  });

  const { data: recoveryStats } = useQuery({
    queryKey: ['recovery-stats'],
    queryFn: getRecoveryStats,
    refetchInterval: 60000,
  });

  const { data: recentTraces } = useQuery({
    queryKey: ['recent-traces'],
    queryFn: () => getTraces({ limit: 10 }),
    refetchInterval: 30000,
  });

  if (healthLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  const skillList = Array.isArray(skills) ? skills : [];
  const failureList = unrecoveredFailures?.items || [];
  const candidateList = Array.isArray(recoveryCandidates) ? recoveryCandidates : [];
  const traceList = Array.isArray(recentTraces) ? recentTraces : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
          Dashboard
        </h1>
        <div className="flex items-center gap-2">
          <StatusBadge status={health?.status || 'unknown'} />
          {determinism?.deterministic === false && (
            <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
              Determinism Warning
            </span>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Available Skills"
          value={skillList.length || Object.keys(capabilities?.skills || {}).length}
          icon={<Cpu size={24} />}
          color="green"
        />
        <MetricCard
          title="Active Failures"
          value={failureStats?.total || failureList.length}
          icon={<AlertTriangle size={24} />}
          color={failureList.length > 0 ? 'red' : 'green'}
          subtitle={`${failureStats?.recovery_rate || 0}% recovery rate`}
        />
        <MetricCard
          title="Recovery Candidates"
          value={candidateList.length}
          icon={<RefreshCw size={24} />}
          color="purple"
          subtitle={`${recoveryStats?.success_rate || 0}% success rate`}
        />
        <MetricCard
          title="Credit Balance"
          value={formatCredits(capabilities?.budget?.remaining_cents || 0)}
          icon={<Wallet size={24} />}
          color="yellow"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skills Overview */}
        <Card>
          <CardHeader title="Runtime Skills">
            <Link
              to="/console/skills"
              className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              View all <ArrowRight size={14} />
            </Link>
          </CardHeader>
          <CardBody className="p-0">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Skill
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Cost
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Rate Limit
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {(skillList.length > 0 ? skillList : Object.entries(capabilities?.skills || {}).map(([id, s]) => ({ id, ...s as object }))).slice(0, 6).map((skill: { id?: string; skill_id?: string; cost_estimate_cents?: number; rate_limit_remaining?: number; available?: boolean }) => (
                  <tr key={skill.id || skill.skill_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          'w-2 h-2 rounded-full',
                          skill.available !== false ? 'bg-green-500' : 'bg-red-500'
                        )} />
                        <span className="font-mono text-sm">{skill.id || skill.skill_id}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {formatCredits(skill.cost_estimate_cents || 0)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {skill.rate_limit_remaining ?? '--'}/min
                    </td>
                  </tr>
                ))}
                {!skillList.length && !Object.keys(capabilities?.skills || {}).length && (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-gray-500">
                      No skills available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardBody>
        </Card>

        {/* Recent Traces */}
        <Card>
          <CardHeader title="Recent Executions">
            <Link
              to="/console/traces"
              className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              View all <ArrowRight size={14} />
            </Link>
          </CardHeader>
          <CardBody className="p-0">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Run ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Time
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {traceList.slice(0, 6).map((trace: { run_id: string; status: string; created_at: string }) => (
                  <tr key={trace.run_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      <Link to={`/console/traces/${trace.run_id}`} className="font-mono text-sm text-primary-600 hover:underline">
                        {truncateId(trace.run_id)}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={trace.status} />
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {new Date(trace.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
                {!traceList.length && (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-gray-500">
                      No recent executions
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardBody>
        </Card>
      </div>

      {/* Failure & Recovery Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Unrecovered Failures */}
        <Card>
          <CardHeader title="Failure Alerts">
            <Link
              to="/console/failures"
              className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              View all <ArrowRight size={14} />
            </Link>
          </CardHeader>
          <CardBody className="p-0">
            {failureList.length > 0 ? (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {failureList.slice(0, 4).map((failure: { id: string; error_type: string; error_message: string; created_at: string }) => (
                  <div key={failure.id} className="px-4 py-3">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-sm text-red-600">{failure.error_type}</span>
                      <span className="text-xs text-gray-400">
                        {new Date(failure.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 truncate mt-1">
                      {failure.error_message}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-4 py-8 text-center text-gray-500">
                <Shield className="mx-auto mb-2 text-green-500" size={32} />
                No active failures
              </div>
            )}
          </CardBody>
        </Card>

        {/* Recovery Candidates */}
        <Card>
          <CardHeader title="Recovery Candidates">
            <Link
              to="/console/recovery"
              className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              View all <ArrowRight size={14} />
            </Link>
          </CardHeader>
          <CardBody className="p-0">
            {candidateList.length > 0 ? (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {candidateList.slice(0, 4).map((candidate: { id: string; suggested_action: string; confidence: number; status: string }) => (
                  <div key={candidate.id} className="px-4 py-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{candidate.suggested_action}</span>
                      <span className={cn(
                        'text-xs px-2 py-0.5 rounded',
                        candidate.confidence > 0.8 ? 'bg-green-100 text-green-700' :
                        candidate.confidence > 0.5 ? 'bg-yellow-100 text-yellow-700' :
                        'bg-gray-100 text-gray-700'
                      )}>
                        {Math.round(candidate.confidence * 100)}% confidence
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">Status: {candidate.status}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-4 py-8 text-center text-gray-500">
                <Activity className="mx-auto mb-2 text-gray-400" size={32} />
                No pending recovery candidates
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Budget Info */}
      <Card>
        <CardHeader title="Budget & Rate Limits" />
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Budget</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                {formatCredits(capabilities?.budget?.total_cents || 0)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Remaining</p>
              <p className="text-xl font-semibold text-green-600">
                {formatCredits(capabilities?.budget?.remaining_cents || 0)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Per-Step Max</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                {formatCredits(capabilities?.budget?.per_step_max_cents || 0)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Determinism</p>
              <p className={cn(
                'text-xl font-semibold',
                determinism?.deterministic !== false ? 'text-green-600' : 'text-yellow-600'
              )}>
                {determinism?.deterministic !== false ? 'Verified' : 'Warning'}
              </p>
            </div>
          </div>
          <div className="mt-4">
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all"
                style={{
                  width: `${Math.min(100, ((capabilities?.budget?.remaining_cents || 0) / (capabilities?.budget?.total_cents || 1)) * 100)}%`
                }}
              />
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
