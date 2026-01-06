/**
 * Founder Ops Console - AI Mission Control
 *
 * Single-page, read-only, signal-first dashboard for founders and ops.
 * Displays system health, at-risk customers, all customers, and founder playbooks.
 *
 * Layout:
 * - TOP STRIP: System Truth (always visible)
 * - TOP LEFT: Customers at Risk
 * - TOP RIGHT: All Customers
 * - BOTTOM LEFT: Founder Playbooks
 * - BOTTOM RIGHT: Timeline/Events (placeholder)
 */

import { useEffect, useState, useCallback } from 'react';
import {
  Activity,
  AlertTriangle,
  Clock,
  DollarSign,
  Database,
  HardDrive,
  Users,
  Play,
  BookOpen,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Phone,
  Mail,
  Slack,
  Settings,
  Shield,
  TrendingDown,
  TrendingUp,
  Minus,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  fetchOpsConsoleData,
  getCustomerSegments,
  type SystemPulse,
  type InfraMetrics,
  type CustomerAtRisk,
  type CustomerSegment,
  type FounderPlaybook,
  type FounderIntervention,
} from '@/api/ops';

// =============================================================================
// Constants
// =============================================================================

const POLL_INTERVAL_MS = 15000; // 15 seconds

// =============================================================================
// Utility Functions
// =============================================================================

function getStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'text-green-400';
    case 'degraded':
      return 'text-yellow-400';
    case 'critical':
      return 'text-red-400';
    default:
      return 'text-gray-400';
  }
}

function getRiskColor(risk: string): string {
  switch (risk) {
    case 'critical':
      return 'text-red-400 bg-red-900/30';
    case 'high':
      return 'text-yellow-400 bg-yellow-900/30';
    case 'medium':
      return 'text-orange-400 bg-orange-900/30';
    default:
      return 'text-gray-400 bg-gray-800';
  }
}

function getRiskBadgeColor(risk: string): string {
  switch (risk) {
    case 'critical':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'high':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    case 'medium':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    default:
      return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
}

function getTrendIcon(delta: number) {
  if (delta > 1.1) return <TrendingUp className="w-4 h-4 text-green-400" />;
  if (delta < 0.9) return <TrendingDown className="w-4 h-4 text-red-400" />;
  return <Minus className="w-4 h-4 text-gray-500" />;
}

function getInterventionIcon(type: string) {
  switch (type) {
    case 'call':
      return <Phone className="w-4 h-4" />;
    case 'email':
      return <Mail className="w-4 h-4" />;
    case 'slack':
      return <Slack className="w-4 h-4" />;
    case 'feature_flag':
      return <Settings className="w-4 h-4" />;
    case 'policy_adjust':
      return <Shield className="w-4 h-4" />;
    default:
      return <Activity className="w-4 h-4" />;
  }
}

function formatTenantId(id: string): string {
  return id.substring(0, 8) + '...';
}

// =============================================================================
// Components
// =============================================================================

// TOP STRIP - System Truth
function SystemTruthStrip({
  pulse,
  infra,
}: {
  pulse: SystemPulse | null;
  infra: InfraMetrics | null;
}) {
  const systemState = pulse?.system_state || 'unknown';
  const dbUsage = infra
    ? ((infra.db_storage_used_gb / infra.db_storage_limit_gb) * 100).toFixed(1)
    : '0';
  const redisUsage = infra
    ? ((infra.redis_memory_used_mb / infra.redis_memory_limit_mb) * 100).toFixed(1)
    : '0';

  return (
    <div className="bg-gray-900 border-b border-gray-800 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Left side - System status */}
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div
              className={cn(
                'w-3 h-3 rounded-full animate-pulse',
                systemState === 'healthy'
                  ? 'bg-green-500'
                  : systemState === 'degraded'
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              )}
            />
            <span className={cn('font-mono text-sm font-bold', getStatusColor(systemState))}>
              SYSTEM: {systemState.toUpperCase()}
            </span>
          </div>

          <div className="flex items-center gap-2 text-gray-400">
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
            <span className="font-mono text-sm">
              INCIDENTS: <span className="text-white">{pulse?.incidents_created_24h || 0}</span>
            </span>
          </div>

          <div className="flex items-center gap-2 text-gray-400">
            <DollarSign className="w-4 h-4 text-green-500" />
            <span className="font-mono text-sm">
              COST TODAY:{' '}
              <span className="text-white">${(pulse?.cost_today_usd || 0).toFixed(2)}</span>
            </span>
          </div>

          <div className="flex items-center gap-2 text-gray-400">
            <Clock className="w-4 h-4 text-blue-500" />
            <span className="font-mono text-sm">
              p95 LATENCY: <span className="text-white">{pulse?.latency_p95_ms || 0}ms</span>
            </span>
          </div>
        </div>

        {/* Right side - Infrastructure */}
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2 text-gray-400">
            <Database className="w-4 h-4 text-purple-500" />
            <span className="font-mono text-sm">
              DB:{' '}
              <span className="text-white">
                {infra?.db_storage_used_gb?.toFixed(2) || 0} / {infra?.db_storage_limit_gb || 0} GB
              </span>
              <span className="text-gray-500 ml-1">({dbUsage}%)</span>
            </span>
          </div>

          <div className="flex items-center gap-2 text-gray-400">
            <HardDrive className="w-4 h-4 text-cyan-500" />
            <span className="font-mono text-sm">
              REDIS:{' '}
              <span className="text-white">
                {infra?.redis_memory_used_mb?.toFixed(0) || 0} / {infra?.redis_memory_limit_mb || 0}{' '}
                MB
              </span>
              <span className="text-gray-500 ml-1">({redisUsage}%)</span>
            </span>
          </div>

          <div className="flex items-center gap-2 text-gray-400">
            <Users className="w-4 h-4 text-orange-500" />
            <span className="font-mono text-sm">
              ACTIVE (24h): <span className="text-white">{pulse?.active_tenants_24h || 0}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// LEFT PANEL - Customers at Risk
function AtRiskPanel({ customers }: { customers: CustomerAtRisk[] }) {
  const [expandedCustomer, setExpandedCustomer] = useState<string | null>(null);

  if (customers.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 h-full">
        <div className="flex items-center gap-2 mb-6">
          <AlertTriangle className="w-5 h-5 text-yellow-500" />
          <h2 className="text-lg font-bold text-white">AT-RISK CUSTOMERS</h2>
          <span className="ml-auto px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 text-xs font-mono">
            0
          </span>
        </div>
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <div className="w-16 h-16 rounded-full bg-green-900/30 flex items-center justify-center mb-4">
            <Activity className="w-8 h-8 text-green-500" />
          </div>
          <p className="text-gray-400 text-sm">No customers at risk (yet)</p>
          <p className="text-gray-600 text-xs mt-2">
            System is monitoring for friction patterns
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 h-full overflow-y-auto">
      <div className="flex items-center gap-2 mb-6">
        <AlertTriangle className="w-5 h-5 text-yellow-500" />
        <h2 className="text-lg font-bold text-white">AT-RISK CUSTOMERS</h2>
        <span
          className={cn(
            'ml-auto px-2 py-0.5 rounded-full text-xs font-mono',
            customers.length > 0 ? 'bg-yellow-900/50 text-yellow-400' : 'bg-gray-800 text-gray-400'
          )}
        >
          {customers.length}
        </span>
      </div>

      <div className="space-y-4">
        {customers.map((customer) => {
          const isExpanded = expandedCustomer === customer.tenant_id;
          return (
            <div
              key={customer.tenant_id}
              className={cn(
                'rounded-lg border transition-all cursor-pointer',
                getRiskColor(customer.risk_level),
                'hover:border-opacity-100 border-opacity-50'
              )}
            >
              <div
                className="p-4"
                onClick={() => setExpandedCustomer(isExpanded ? null : customer.tenant_id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          'px-2 py-0.5 rounded text-xs font-bold uppercase border',
                          getRiskBadgeColor(customer.risk_level)
                        )}
                      >
                        {customer.risk_level}
                      </span>
                      <span className="text-white font-mono text-sm">
                        {customer.tenant_name || formatTenantId(customer.tenant_id)}
                      </span>
                    </div>

                    <div className="mt-2 space-y-1">
                      <div className="flex items-center gap-2 text-sm">
                        {getTrendIcon(customer.stickiness_delta)}
                        <span className="text-gray-400">
                          Stickiness: {customer.stickiness_7d.toFixed(1)} (7d)
                        </span>
                        <span className="text-gray-600">
                          δ={customer.stickiness_delta.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-gray-300 text-sm">{customer.primary_risk_reason}</p>
                      {customer.top_friction_type && (
                        <p className="text-gray-500 text-xs">
                          Top friction: {customer.top_friction_type} ({customer.friction_count_14d}{' '}
                          in 14d)
                        </p>
                      )}
                    </div>
                  </div>
                  {isExpanded ? (
                    <ChevronDown className="w-5 h-5 text-gray-500" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-gray-500" />
                  )}
                </div>
              </div>

              {/* Interventions (expanded) */}
              {isExpanded && customer.interventions.length > 0 && (
                <div className="border-t border-gray-800 p-4 bg-gray-950/50">
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-3">
                    Suggested Interventions
                  </p>
                  <div className="space-y-3">
                    {customer.interventions.map((intervention, idx) => (
                      <InterventionCard key={idx} intervention={intervention} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function InterventionCard({ intervention }: { intervention: FounderIntervention }) {
  const priorityColors: Record<string, string> = {
    immediate: 'text-red-400 bg-red-900/30',
    today: 'text-yellow-400 bg-yellow-900/30',
    this_week: 'text-blue-400 bg-blue-900/30',
  };

  return (
    <div className="bg-gray-900 rounded p-3 border border-gray-800">
      <div className="flex items-center gap-2 mb-2">
        {getInterventionIcon(intervention.intervention_type)}
        <span className="text-white text-sm font-medium">{intervention.suggested_action}</span>
        <span
          className={cn(
            'ml-auto px-2 py-0.5 rounded text-xs font-bold uppercase',
            priorityColors[intervention.priority] || 'text-gray-400 bg-gray-800'
          )}
        >
          {intervention.priority.replace('_', ' ')}
        </span>
      </div>
      <p className="text-gray-400 text-xs mb-2">{intervention.context}</p>
      <div className="flex items-center gap-1 text-xs text-gray-600">
        <span>Signals:</span>
        {intervention.triggering_signals.map((signal, idx) => (
          <span key={idx} className="px-1.5 py-0.5 bg-gray-800 rounded text-gray-500">
            {signal.length > 30 ? signal.substring(0, 30) + '...' : signal}
          </span>
        ))}
      </div>
    </div>
  );
}

// TOP RIGHT - All Customers
function CustomersPanel({ customers }: { customers: CustomerSegment[] }) {
  const [sortBy, setSortBy] = useState<'stickiness' | 'friction' | 'recent'>('stickiness');

  const sortedCustomers = [...customers].sort((a, b) => {
    switch (sortBy) {
      case 'stickiness':
        return b.current_stickiness - a.current_stickiness;
      case 'friction':
        return b.friction_score - a.friction_score;
      case 'recent':
        return new Date(b.last_api_call || 0).getTime() - new Date(a.last_api_call || 0).getTime();
      default:
        return 0;
    }
  });

  if (customers.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 h-full">
        <div className="flex items-center gap-2 mb-6">
          <Users className="w-5 h-5 text-blue-500" />
          <h2 className="text-lg font-bold text-white">ALL CUSTOMERS</h2>
          <span className="ml-auto px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 text-xs font-mono">
            0
          </span>
        </div>
        <div className="flex flex-col items-center justify-center h-48 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mb-4">
            <Users className="w-8 h-8 text-gray-600" />
          </div>
          <p className="text-gray-400 text-sm">No customers yet</p>
          <p className="text-gray-600 text-xs mt-2">
            Customers will appear after API activity
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 h-full overflow-hidden flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <Users className="w-5 h-5 text-blue-500" />
        <h2 className="text-lg font-bold text-white">ALL CUSTOMERS</h2>
        <span className="ml-auto px-2 py-0.5 rounded-full bg-blue-900/50 text-blue-400 text-xs font-mono">
          {customers.length}
        </span>
      </div>

      {/* Sort Controls */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setSortBy('stickiness')}
          className={cn(
            'px-2 py-1 rounded text-xs font-medium transition-colors',
            sortBy === 'stickiness'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          )}
        >
          Stickiness
        </button>
        <button
          onClick={() => setSortBy('friction')}
          className={cn(
            'px-2 py-1 rounded text-xs font-medium transition-colors',
            sortBy === 'friction'
              ? 'bg-orange-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          )}
        >
          Friction
        </button>
        <button
          onClick={() => setSortBy('recent')}
          className={cn(
            'px-2 py-1 rounded text-xs font-medium transition-colors',
            sortBy === 'recent'
              ? 'bg-green-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          )}
        >
          Recent
        </button>
      </div>

      {/* Customer List */}
      <div className="flex-1 overflow-y-auto space-y-2">
        {sortedCustomers.map((customer) => (
          <div
            key={customer.tenant_id}
            className="p-3 rounded-lg bg-gray-950 border border-gray-800 hover:border-gray-700 transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-mono text-sm">
                {customer.tenant_name || formatTenantId(customer.tenant_id)}
              </span>
              <div className="flex items-center gap-2">
                {getTrendIcon(customer.stickiness_delta)}
                <span
                  className={cn(
                    'px-1.5 py-0.5 rounded text-xs font-bold',
                    customer.stickiness_trend === 'rising'
                      ? 'bg-green-900/30 text-green-400'
                      : customer.stickiness_trend === 'falling'
                      ? 'bg-red-900/30 text-red-400'
                      : 'bg-gray-800 text-gray-400'
                  )}
                >
                  {customer.stickiness_trend}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs">
              <div>
                <span className="text-gray-500">Stickiness</span>
                <div className="text-white font-mono">
                  {customer.stickiness_7d.toFixed(1)}
                  <span className="text-gray-600 ml-1">/ {customer.stickiness_30d.toFixed(1)}</span>
                </div>
              </div>
              <div>
                <span className="text-gray-500">Friction</span>
                <div
                  className={cn(
                    'font-mono',
                    customer.friction_score > 20
                      ? 'text-red-400'
                      : customer.friction_score > 10
                      ? 'text-yellow-400'
                      : 'text-green-400'
                  )}
                >
                  {customer.friction_score.toFixed(1)}
                </div>
              </div>
              <div>
                <span className="text-gray-500">Delta</span>
                <div
                  className={cn(
                    'font-mono',
                    customer.stickiness_delta > 1.1
                      ? 'text-green-400'
                      : customer.stickiness_delta < 0.9
                      ? 'text-red-400'
                      : 'text-gray-400'
                  )}
                >
                  {customer.stickiness_delta.toFixed(2)}x
                </div>
              </div>
            </div>

            {customer.last_api_call && (
              <div className="mt-2 text-xs text-gray-600">
                Last seen: {new Date(customer.last_api_call).toLocaleString()}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// BOTTOM LEFT - Founder Playbooks
function PlaybooksPanel({ playbooks }: { playbooks: FounderPlaybook[] }) {
  const [expandedPlaybook, setExpandedPlaybook] = useState<string | null>(null);

  if (playbooks.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 h-full">
        <div className="flex items-center gap-2 mb-6">
          <BookOpen className="w-5 h-5 text-blue-500" />
          <h2 className="text-lg font-bold text-white">FOUNDER PLAYBOOKS</h2>
        </div>
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <p className="text-gray-400 text-sm">No playbooks configured</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 h-full overflow-y-auto">
      <div className="flex items-center gap-2 mb-6">
        <BookOpen className="w-5 h-5 text-blue-500" />
        <h2 className="text-lg font-bold text-white">FOUNDER PLAYBOOKS</h2>
        <span className="ml-auto px-2 py-0.5 rounded-full bg-blue-900/50 text-blue-400 text-xs font-mono">
          {playbooks.length}
        </span>
      </div>

      <div className="space-y-3">
        {playbooks.map((playbook) => {
          const isExpanded = expandedPlaybook === playbook.id;
          return (
            <div
              key={playbook.id}
              className="rounded-lg border border-gray-800 bg-gray-950/50 overflow-hidden"
            >
              <div
                className="p-4 cursor-pointer hover:bg-gray-900/50 transition-colors"
                onClick={() => setExpandedPlaybook(isExpanded ? null : playbook.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded text-xs font-bold uppercase border',
                        getRiskBadgeColor(playbook.risk_level)
                      )}
                    >
                      {playbook.risk_level}
                    </span>
                    <span className="text-white font-medium">{playbook.name}</span>
                  </div>
                  {isExpanded ? (
                    <ChevronDown className="w-5 h-5 text-gray-500" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-gray-500" />
                  )}
                </div>
                <p className="text-gray-400 text-sm mt-2">{playbook.description}</p>
              </div>

              {isExpanded && (
                <div className="border-t border-gray-800 p-4 bg-gray-900/50">
                  {/* Trigger Conditions */}
                  <div className="mb-4">
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-2">
                      Trigger Conditions
                    </p>
                    <div className="space-y-1">
                      {playbook.trigger_conditions.map((condition, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm text-gray-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                          {condition}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Suggested Actions */}
                  <div className="mb-4">
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-2">
                      Suggested Actions
                    </p>
                    <div className="space-y-1">
                      {playbook.suggested_actions.map((action, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm text-gray-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                          {action}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Expected Outcomes */}
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase mb-2">
                      Expected Outcomes
                    </p>
                    <div className="space-y-1">
                      {playbook.expected_outcomes.map((outcome, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm text-green-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                          {outcome}
                        </div>
                      ))}
                    </div>
                  </div>

                  {playbook.requires_approval && (
                    <div className="mt-4 px-3 py-2 bg-yellow-900/20 rounded border border-yellow-500/30">
                      <p className="text-xs text-yellow-400">
                        Requires manual approval before execution
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// RIGHT PANEL - Timeline (Placeholder)
function TimelinePanel() {
  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-6 h-full">
      <div className="flex items-center gap-2 mb-6">
        <Play className="w-5 h-5 text-green-500" />
        <h2 className="text-lg font-bold text-white">TIMELINE</h2>
      </div>
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mb-4">
          <Clock className="w-8 h-8 text-gray-600" />
        </div>
        <p className="text-gray-400 text-sm">No ops_events yet.</p>
        <p className="text-gray-600 text-xs mt-2">System is waiting for real activity.</p>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function FounderOpsConsole() {
  const [pulse, setPulse] = useState<SystemPulse | null>(null);
  const [infra, setInfra] = useState<InfraMetrics | null>(null);
  const [atRiskCustomers, setAtRiskCustomers] = useState<CustomerAtRisk[]>([]);
  const [customers, setCustomers] = useState<CustomerSegment[]>([]);
  const [playbooks, setPlaybooks] = useState<FounderPlaybook[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [opsData, customerData] = await Promise.all([
        fetchOpsConsoleData(),
        getCustomerSegments(50).catch(() => []),
      ]);
      setPulse(opsData.pulse);
      setInfra(opsData.infra);
      setAtRiskCustomers(opsData.atRiskCustomers);
      setPlaybooks(opsData.playbooks);
      setCustomers(customerData);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Polling
  useEffect(() => {
    const interval = setInterval(fetchData, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Show skeleton layout while loading (faster perceived load)
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col">
        {/* Skeleton Top Strip */}
        <div className="bg-gray-900 border-b border-gray-800 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <div className="h-4 w-32 bg-gray-800 rounded animate-pulse" />
              <div className="h-4 w-24 bg-gray-800 rounded animate-pulse" />
              <div className="h-4 w-28 bg-gray-800 rounded animate-pulse" />
            </div>
            <div className="flex items-center gap-8">
              <div className="h-4 w-36 bg-gray-800 rounded animate-pulse" />
              <div className="h-4 w-32 bg-gray-800 rounded animate-pulse" />
            </div>
          </div>
        </div>

        {/* Skeleton Header */}
        <div className="px-6 py-4 flex items-center justify-between border-b border-gray-800">
          <div>
            <div className="h-7 w-48 bg-gray-800 rounded animate-pulse mb-2" />
            <div className="h-4 w-64 bg-gray-800 rounded animate-pulse" />
          </div>
          <div className="flex items-center gap-4">
            <div className="h-8 w-24 bg-gray-800 rounded animate-pulse" />
          </div>
        </div>

        {/* Skeleton 2x2 Grid */}
        <div className="flex-1 p-6 grid grid-cols-2 grid-rows-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-gray-900 rounded-lg border border-gray-800 p-6">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-5 h-5 bg-gray-800 rounded animate-pulse" />
                <div className="h-5 w-32 bg-gray-800 rounded animate-pulse" />
              </div>
              <div className="space-y-3">
                <div className="h-16 bg-gray-800 rounded animate-pulse" />
                <div className="h-16 bg-gray-800 rounded animate-pulse" />
                <div className="h-12 bg-gray-800 rounded animate-pulse" />
              </div>
            </div>
          ))}
        </div>

        {/* Skeleton Footer */}
        <div className="px-6 py-2 bg-gray-900 border-t border-gray-800 flex items-center justify-between">
          <div className="h-3 w-48 bg-gray-800 rounded animate-pulse" />
          <div className="h-3 w-64 bg-gray-800 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* TOP STRIP - System Truth */}
      <SystemTruthStrip pulse={pulse} infra={infra} />

      {/* Header */}
      <div className="px-6 py-4 flex items-center justify-between border-b border-gray-800">
        <div>
          <h1 className="text-2xl font-bold text-white">Founder Ops Console</h1>
          <p className="text-gray-500 text-sm">AI Mission Control • Signal-First Dashboard</p>
        </div>
        <div className="flex items-center gap-4">
          {error && (
            <span className="text-red-400 text-sm">{error}</span>
          )}
          <div className="flex items-center gap-2 text-gray-500 text-sm">
            <RefreshCw className="w-4 h-4" />
            <span>
              {lastUpdated
                ? `Updated ${lastUpdated.toLocaleTimeString()}`
                : 'Updating...'}
            </span>
          </div>
          <button
            onClick={fetchData}
            className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-sm text-white flex items-center gap-2 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Main Content - 2x2 Grid Layout */}
      <div className="flex-1 p-6 grid grid-cols-2 grid-rows-2 gap-4">
        {/* TOP LEFT - At Risk Customers */}
        <AtRiskPanel customers={atRiskCustomers} />

        {/* TOP RIGHT - All Customers */}
        <CustomersPanel customers={customers} />

        {/* BOTTOM LEFT - Founder Playbooks */}
        <PlaybooksPanel playbooks={playbooks} />

        {/* BOTTOM RIGHT - Timeline */}
        <TimelinePanel />
      </div>

      {/* Footer Status Bar */}
      <div className="px-6 py-2 bg-gray-900 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
        <span>
          Polling every {POLL_INTERVAL_MS / 1000}s • {customers.length} customers •{' '}
          {atRiskCustomers.length} at-risk • {playbooks.length} playbooks
        </span>
        <span>
          Replays (24h): {pulse?.replays_executed_24h || 0} • Error Rate:{' '}
          {((pulse?.error_rate_24h || 0) * 100).toFixed(2)}% • Uptime:{' '}
          {(pulse?.uptime_percent || 100).toFixed(2)}%
        </span>
      </div>
    </div>
  );
}
