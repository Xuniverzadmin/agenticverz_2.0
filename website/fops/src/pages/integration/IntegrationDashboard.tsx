/**
 * M25 Integration Dashboard
 *
 * Overview of all integration loops and human checkpoints.
 * The operator's view into the self-improving feedback system.
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { logger } from '@/lib/consoleLogger';
import { Link } from 'react-router-dom';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { Spinner } from '@/components/common/Spinner';
import {
  integrationApi,
  IntegrationStats,
  HumanCheckpoint,
  ConfidenceBand,
  GraduationStatus,
} from '@/api/integration';

const CONFIDENCE_CONFIG: Record<ConfidenceBand, { label: string; color: string }> = {
  strong: { label: 'Strong', color: 'bg-green-500' },
  weak: { label: 'Weak', color: 'bg-yellow-500' },
  novel: { label: 'Novel', color: 'bg-purple-500' },
};

export function IntegrationDashboard() {
  const queryClient = useQueryClient();
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<HumanCheckpoint | null>(null);

  // Component logging
  useEffect(() => {
    logger.componentMount('IntegrationDashboard');
    return () => logger.componentUnmount('IntegrationDashboard');
  }, []);

  // Fetch stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['integration', 'stats'],
    queryFn: () => integrationApi.getStats(),
    refetchInterval: 10000,
  });

  // Fetch pending checkpoints
  const { data: checkpoints, isLoading: checkpointsLoading } = useQuery({
    queryKey: ['integration', 'checkpoints'],
    queryFn: () => integrationApi.getPendingCheckpoints(),
    refetchInterval: 5000,
  });

  // Fetch graduation status
  const { data: graduation, isLoading: graduationLoading } = useQuery({
    queryKey: ['integration', 'graduation'],
    queryFn: () => integrationApi.getGraduationStatus(),
    refetchInterval: 30000,
  });

  // Resolve checkpoint
  const resolveMutation = useMutation({
    mutationFn: ({ id, resolution }: { id: string; resolution: string }) =>
      integrationApi.resolveCheckpoint(id, resolution),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration'] });
      setSelectedCheckpoint(null);
    },
    onError: (error) => {
      logger.error('INTEGRATION', 'Failed to resolve checkpoint', error);
    },
  });

  const isLoading = statsLoading || checkpointsLoading || graduationLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Integration Loop Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Self-improving feedback system: Incident → Pattern → Recovery → Policy → Routing
          </p>
        </div>
        <Badge
          variant={graduation?.is_graduated ? 'success' : 'default'}
          className="text-lg px-4 py-2"
        >
          {graduation?.status ?? 'M25-ALPHA'}
        </Badge>
      </div>

      {/* M25 Graduation Status Widget */}
      {graduation && <GraduationWidget graduation={graduation} />}

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Loops Today"
          value={stats?.loops_today ?? 0}
          icon="🔄"
        />
        <StatCard
          label="Complete"
          value={stats?.loops_complete ?? 0}
          icon="✓"
          highlight
        />
        <StatCard
          label="Blocked"
          value={stats?.loops_blocked ?? 0}
          icon="⏸"
          alert={stats?.loops_blocked > 0}
        />
        <StatCard
          label="Avg Time"
          value={formatDuration(stats?.avg_completion_time_ms ?? 0)}
          icon="⏱"
        />
      </div>

      {/* Confidence Distribution */}
      {stats?.confidence_distribution && (
        <Card className="p-6 bg-slate-800/50 border-slate-700">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">Pattern Match Confidence</h2>
          <div className="flex items-center gap-8">
            {Object.entries(stats.confidence_distribution).map(([band, count]) => (
              <div key={band} className="flex items-center gap-3">
                <div className={`w-4 h-4 rounded ${CONFIDENCE_CONFIG[band as ConfidenceBand].color}`} />
                <div>
                  <p className="text-gray-100 font-medium">{count}</p>
                  <p className="text-sm text-gray-400">{CONFIDENCE_CONFIG[band as ConfidenceBand].label}</p>
                </div>
              </div>
            ))}
          </div>
          <ConfidenceBar distribution={stats.confidence_distribution} />
        </Card>
      )}

      {/* Pipeline Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          title="Patterns Matched"
          value={stats?.patterns_matched ?? 0}
          description="Incidents matched to known patterns"
          icon="🔍"
        />
        <MetricCard
          title="Recoveries Applied"
          value={stats?.recoveries_applied ?? 0}
          description="Recovery suggestions applied"
          icon="💡"
        />
        <MetricCard
          title="Policies Activated"
          value={stats?.policies_activated ?? 0}
          description="Policies promoted from shadow mode"
          icon="📋"
        />
      </div>

      {/* Pending Checkpoints */}
      <Card className="p-6 bg-slate-800/50 border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-100">
            Pending Human Decisions
            {checkpoints && checkpoints.length > 0 && (
              <Badge variant="warning" className="ml-3">
                {checkpoints.length}
              </Badge>
            )}
          </h2>
        </div>

        {!checkpoints || checkpoints.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-2">✓</div>
            <p className="text-gray-400">No pending decisions</p>
            <p className="text-sm text-gray-500">All loops are progressing automatically</p>
          </div>
        ) : (
          <div className="space-y-3">
            {checkpoints.map((checkpoint) => (
              <CheckpointRow
                key={checkpoint.id}
                checkpoint={checkpoint}
                onResolve={(resolution) => resolveMutation.mutate({ id: checkpoint.id, resolution })}
                isLoading={resolveMutation.isPending}
              />
            ))}
          </div>
        )}
      </Card>

      {/* Quick Actions */}
      <Card className="p-6 bg-slate-800/50 border-slate-700">
        <h2 className="text-lg font-semibold text-gray-100 mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-4">
          <Link to="/integration/loops">
            <Button variant="secondary">View All Loops</Button>
          </Link>
          <Link to="/failures">
            <Button variant="secondary">Pattern Catalog</Button>
          </Link>
          <Link to="/recovery">
            <Button variant="secondary">Recovery Queue</Button>
          </Link>
          <Link to="/operator/audit">
            <Button variant="secondary">Policy Audit Log</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

function GraduationWidget({ graduation }: { graduation: GraduationStatus }) {
  const gates = [
    {
      key: 'gate1_prevention',
      gate: graduation.gates.gate1_prevention,
      icon: graduation.gates.gate1_prevention.passed ? '✅' : '🔒',
      number: '1',
    },
    {
      key: 'gate2_rollback',
      gate: graduation.gates.gate2_rollback,
      icon: graduation.gates.gate2_rollback.passed ? '✅' : '🔒',
      number: '2',
    },
    {
      key: 'gate3_console',
      gate: graduation.gates.gate3_console,
      icon: graduation.gates.gate3_console.passed ? '✅' : '🔒',
      number: '3',
    },
  ];

  const passedCount = gates.filter((g) => g.gate.passed).length;

  return (
    <Card
      className={`p-6 border ${
        graduation.is_graduated
          ? 'bg-green-900/30 border-green-600'
          : 'bg-slate-800/50 border-slate-700'
      }`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">
            {graduation.is_graduated ? '🎓' : '📊'}
          </span>
          <div>
            <h2 className="text-lg font-semibold text-gray-100">M25 Graduation Status</h2>
            <p className="text-sm text-gray-400">
              {graduation.is_graduated
                ? 'Loop-Proven: System demonstrably learns from failures'
                : `Loop-Enabled: ${passedCount}/3 gates passed`}
            </p>
          </div>
        </div>
        {!graduation.is_graduated && (
          <Badge variant="warning">{graduation.next_action}</Badge>
        )}
      </div>

      {/* Gates Progress */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        {gates.map(({ key, gate, icon, number }) => (
          <div
            key={key}
            className={`p-4 rounded-lg border ${
              gate.passed
                ? 'bg-green-900/20 border-green-600/50'
                : 'bg-slate-700/30 border-slate-600'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{icon}</span>
              <span className="font-medium text-gray-100">
                Gate {number}: {gate.name}
              </span>
            </div>
            <p className="text-sm text-gray-400 mb-2">{gate.description}</p>
            {gate.passed && (
              <Badge variant="success" className="text-xs">Passed</Badge>
            )}
          </div>
        ))}
      </div>

      {/* Stats Row */}
      <div className="flex items-center gap-8 mt-4 pt-4 border-t border-slate-600/50">
        <div>
          <p className="text-xs text-gray-500 uppercase">Preventions</p>
          <p className="text-lg font-semibold text-gray-100">
            {graduation.prevention_stats.total}
            <span className="text-sm text-gray-400 ml-1">
              ({graduation.prevention_stats.rate})
            </span>
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase">Regret Events</p>
          <p className="text-lg font-semibold text-gray-100">
            {graduation.regret_stats.total_events}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase">Auto-Demotions</p>
          <p className="text-lg font-semibold text-gray-100">
            {graduation.regret_stats.auto_demotions}
          </p>
        </div>
      </div>
    </Card>
  );
}

function StatCard({
  label,
  value,
  icon,
  highlight,
  alert,
}: {
  label: string;
  value: number | string;
  icon: string;
  highlight?: boolean;
  alert?: boolean;
}) {
  return (
    <Card
      className={`p-4 text-center ${
        alert
          ? 'bg-red-900/30 border-red-600'
          : highlight
          ? 'bg-green-900/30 border-green-600'
          : 'bg-slate-800/50 border-slate-700'
      }`}
    >
      <div className="text-2xl mb-1">{icon}</div>
      <p
        className={`text-2xl font-bold ${
          alert ? 'text-red-400' : highlight ? 'text-green-400' : 'text-gray-100'
        }`}
      >
        {value}
      </p>
      <p className="text-sm text-gray-400">{label}</p>
    </Card>
  );
}

function MetricCard({
  title,
  value,
  description,
  icon,
}: {
  title: string;
  value: number;
  description: string;
  icon: string;
}) {
  return (
    <Card className="p-4 bg-slate-800/50 border-slate-700">
      <div className="flex items-center gap-3 mb-2">
        <span className="text-xl">{icon}</span>
        <span className="font-medium text-gray-100">{title}</span>
      </div>
      <p className="text-3xl font-bold text-gray-100">{value.toLocaleString()}</p>
      <p className="text-sm text-gray-400 mt-1">{description}</p>
    </Card>
  );
}

function ConfidenceBar({ distribution }: { distribution: Record<ConfidenceBand, number> }) {
  const total = Object.values(distribution).reduce((a, b) => a + b, 0);
  if (total === 0) return null;

  return (
    <div className="flex h-3 rounded-full overflow-hidden mt-4">
      {(['strong', 'weak', 'novel'] as ConfidenceBand[]).map((band) => {
        const count = distribution[band] ?? 0;
        const percent = (count / total) * 100;
        if (percent === 0) return null;
        return (
          <div
            key={band}
            className={CONFIDENCE_CONFIG[band].color}
            style={{ width: `${percent}%` }}
            title={`${band}: ${count} (${percent.toFixed(1)}%)`}
          />
        );
      })}
    </div>
  );
}

function CheckpointRow({
  checkpoint,
  onResolve,
  isLoading,
}: {
  checkpoint: HumanCheckpoint;
  onResolve: (resolution: string) => void;
  isLoading: boolean;
}) {
  const typeLabels: Record<string, string> = {
    approve_policy: '📋 Approve Policy',
    approve_recovery: '💡 Approve Recovery',
    simulate_routing: '🔀 Simulate Routing',
    revert_loop: '↩️ Revert Loop',
    override_guardrail: '⚠️ Override Guardrail',
  };

  return (
    <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-600 flex items-center justify-between">
      <div className="flex-1">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-amber-400">
            {typeLabels[checkpoint.checkpoint_type] ?? checkpoint.checkpoint_type}
          </span>
          <Link
            to={`/integration/loop/${checkpoint.incident_id}`}
            className="text-xs text-blue-400 hover:underline"
          >
            View Loop →
          </Link>
        </div>
        <p className="text-sm text-gray-300 mt-1">{checkpoint.description}</p>
        <p className="text-xs text-gray-500 mt-1">
          Created: {new Date(checkpoint.created_at).toLocaleString()}
        </p>
      </div>
      <div className="flex gap-2">
        {checkpoint.options.slice(0, 2).map((option) => (
          <Button
            key={option.action}
            size="sm"
            variant={option.is_destructive ? 'danger' : 'primary'}
            onClick={() => onResolve(option.action)}
            disabled={isLoading}
          >
            {option.label}
          </Button>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Helpers
// ============================================================================

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

export default IntegrationDashboard;
