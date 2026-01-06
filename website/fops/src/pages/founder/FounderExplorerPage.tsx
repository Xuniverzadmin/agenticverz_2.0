/**
 * FounderExplorerPage
 *
 * H3 Founder Console - Exploratory Mode
 * Cross-tenant visibility for business learning and diagnostics
 *
 * FOUNDER ONLY - READ-ONLY (no mutation flows)
 *
 * Reference: Phase H3 - Founder Console Exploratory Mode
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Compass,
  Building2,
  Activity,
  AlertTriangle,
  Heart,
  TrendingUp,
  ChevronRight,
  RefreshCw,
  Search,
  Users,
  DollarSign,
  Shield,
} from 'lucide-react';
import {
  getSystemSummary,
  listTenants,
  getTenantDiagnostics,
  getSystemHealth,
  getUsagePatterns,
  getHealthStatusColor,
  getCheckStatusColor,
  getTrendIndicator,
  getSignificanceColor,
  formatUtilization,
  getUtilizationColor,
  type TenantSummary,
  type TenantDiagnostics,
} from '@/api/explorer';

// =============================================================================
// Sub-components
// =============================================================================

function SystemOverviewCard() {
  const { data: summary, isLoading, refetch } = useQuery({
    queryKey: ['explorer', 'summary'],
    queryFn: getSystemSummary,
    staleTime: 30000,
  });

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4" />
        <div className="h-20 bg-gray-700 rounded" />
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary-400" />
          <h2 className="text-lg font-semibold text-white">System Overview</h2>
        </div>
        <button
          onClick={() => refetch()}
          className="p-2 text-gray-400 hover:text-white transition-colors"
          title="Refresh"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-900/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">
            {summary.total_tenants}
          </div>
          <div className="text-sm text-gray-400">Total Tenants</div>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">
            {summary.total_agents}
          </div>
          <div className="text-sm text-gray-400">Total Agents</div>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">
            {summary.runs_last_24h.toLocaleString()}
          </div>
          <div className="text-sm text-gray-400">Runs (24h)</div>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <div
              className={`text-2xl font-bold ${getHealthStatusColor(summary.system_health)}`}
            >
              {summary.system_health.toUpperCase()}
            </div>
          </div>
          <div className="text-sm text-gray-400">System Health</div>
        </div>
      </div>

      {summary.active_incidents > 0 && (
        <div className="mt-4 p-3 bg-red-900/20 border border-red-800 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-400" />
          <span className="text-red-400">
            {summary.active_incidents} active incident
            {summary.active_incidents > 1 ? 's' : ''} across tenants
          </span>
        </div>
      )}
    </div>
  );
}

function HealthChecksCard() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['explorer', 'health'],
    queryFn: getSystemHealth,
    staleTime: 30000,
  });

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-8 bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (!health) return null;

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <Heart className="h-5 w-5 text-primary-400" />
        <h2 className="text-lg font-semibold text-white">Health Checks</h2>
      </div>

      <div className="space-y-2">
        {health.checks.map((check) => (
          <div
            key={check.name}
            className="flex items-center justify-between p-2 bg-gray-900/50 rounded"
          >
            <span className="text-gray-300">{check.name}</span>
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${getCheckStatusColor(check.status)}`}
            >
              {check.status.toUpperCase()}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 text-sm text-gray-500">
        Uptime: {health.uptime_pct.toFixed(2)}%
      </div>
    </div>
  );
}

function UsagePatternsCard() {
  const { data: patternsData, isLoading } = useQuery({
    queryKey: ['explorer', 'patterns'],
    queryFn: getUsagePatterns,
    staleTime: 60000,
  });

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (!patternsData) return null;

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-5 w-5 text-primary-400" />
        <h2 className="text-lg font-semibold text-white">Usage Patterns</h2>
      </div>

      <div className="space-y-3">
        {patternsData.patterns.slice(0, 5).map((pattern, idx) => {
          const trend = getTrendIndicator(pattern.trend);
          return (
            <div
              key={idx}
              className="p-3 bg-gray-900/50 rounded-lg"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-white font-medium">
                  {pattern.pattern_type}
                </span>
                <span
                  className={`px-2 py-0.5 rounded text-xs ${getSignificanceColor(pattern.significance)}`}
                >
                  {pattern.significance}
                </span>
              </div>
              <p className="text-sm text-gray-400 mb-2">
                {pattern.description}
              </p>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span>Frequency: {pattern.frequency}</span>
                <span>Tenants: {pattern.affected_tenants}</span>
                <span className={trend.color}>
                  {trend.icon} {pattern.trend}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 text-xs text-gray-500">
        Analyzed {patternsData.total_events_analyzed.toLocaleString()} events
      </div>
    </div>
  );
}

function TenantListCard({
  onSelectTenant,
}: {
  onSelectTenant: (tenantId: string) => void;
}) {
  const [search, setSearch] = useState('');
  const { data: tenants, isLoading } = useQuery({
    queryKey: ['explorer', 'tenants'],
    queryFn: () => listTenants({ sortBy: 'activity', order: 'desc' }),
    staleTime: 30000,
  });

  const filteredTenants = tenants?.filter(
    (t) =>
      t.tenant_id.toLowerCase().includes(search.toLowerCase()) ||
      t.name.toLowerCase().includes(search.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4" />
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <Building2 className="h-5 w-5 text-primary-400" />
        <h2 className="text-lg font-semibold text-white">Tenants</h2>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
        <input
          type="text"
          placeholder="Search tenants..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredTenants?.map((tenant) => (
          <button
            key={tenant.tenant_id}
            onClick={() => onSelectTenant(tenant.tenant_id)}
            className="w-full p-3 bg-gray-900/50 rounded-lg hover:bg-gray-900 transition-colors text-left group"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">{tenant.name}</div>
                <div className="text-xs text-gray-500 font-mono">
                  {tenant.tenant_id.slice(0, 8)}...
                </div>
              </div>
              <ChevronRight className="h-4 w-4 text-gray-600 group-hover:text-primary-400 transition-colors" />
            </div>
            <div className="flex gap-4 mt-2 text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <Users className="h-3 w-3" />
                {tenant.metrics.active_agents} agents
              </span>
              <span className="flex items-center gap-1">
                <Activity className="h-3 w-3" />
                {tenant.metrics.total_runs} runs
              </span>
              {tenant.metrics.incidents_last_7d > 0 && (
                <span className="flex items-center gap-1 text-yellow-400">
                  <AlertTriangle className="h-3 w-3" />
                  {tenant.metrics.incidents_last_7d} incidents
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function TenantDiagnosticsPanel({
  tenantId,
  onClose,
}: {
  tenantId: string;
  onClose: () => void;
}) {
  const { data: diagnostics, isLoading } = useQuery({
    queryKey: ['explorer', 'diagnostics', tenantId],
    queryFn: () => getTenantDiagnostics(tenantId),
    staleTime: 30000,
  });

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 animate-pulse">
        <div className="h-6 bg-gray-700 rounded w-1/2 mb-4" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gray-700 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (!diagnostics) return null;

  const { diagnostics: d } = diagnostics;

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Compass className="h-5 w-5 text-primary-400" />
          <h2 className="text-lg font-semibold text-white">
            Tenant Diagnostics
          </h2>
        </div>
        <button
          onClick={onClose}
          className="text-sm text-gray-400 hover:text-white"
        >
          Close
        </button>
      </div>

      <div className="text-sm text-gray-400 mb-4 font-mono">
        {tenantId}
      </div>

      {/* Agents Section */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
          <Users className="h-4 w-4" />
          Agents
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xl font-bold text-white">{d.agents.total}</div>
            <div className="text-xs text-gray-500">Total Agents</div>
          </div>
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xl font-bold text-white">
              {d.agents.by_status.active || 0}
            </div>
            <div className="text-xs text-gray-500">Active</div>
          </div>
        </div>
        {d.agents.recent_failures.length > 0 && (
          <div className="mt-3 p-3 bg-red-900/20 border border-red-800 rounded">
            <div className="text-xs text-red-400 mb-2">Recent Failures</div>
            {d.agents.recent_failures.slice(0, 3).map((f) => (
              <div key={f.agent_id} className="text-sm text-gray-300">
                {f.name} - {f.failure_count} failures
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Runs Section */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Runs
        </h3>
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xl font-bold text-white">
              {d.runs.total.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">Total Runs</div>
          </div>
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xl font-bold text-white">
              {d.runs.avg_duration_ms.toFixed(0)}ms
            </div>
            <div className="text-xs text-gray-500">Avg Duration</div>
          </div>
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xl font-bold text-white">
              {d.runs.p95_duration_ms.toFixed(0)}ms
            </div>
            <div className="text-xs text-gray-500">P95 Duration</div>
          </div>
        </div>
      </div>

      {/* Budget Section */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
          <DollarSign className="h-4 w-4" />
          Budget
        </h3>
        <div className="bg-gray-900/50 rounded p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400">Utilization</span>
            <span
              className={`font-bold ${getUtilizationColor(d.budget.utilization_pct)}`}
            >
              {formatUtilization(d.budget.utilization_pct)}
            </span>
          </div>
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                d.budget.utilization_pct >= 90
                  ? 'bg-red-500'
                  : d.budget.utilization_pct >= 70
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(d.budget.utilization_pct, 100)}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-500">
            <span>
              ${(d.budget.total_spent_cents / 100).toFixed(2)} spent
            </span>
            <span>${(d.budget.limit_cents / 100).toFixed(2)} limit</span>
          </div>
        </div>
      </div>

      {/* Incidents Section */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          Incidents
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-900/50 rounded p-3">
            <div
              className={`text-xl font-bold ${d.incidents.open > 0 ? 'text-red-400' : 'text-white'}`}
            >
              {d.incidents.open}
            </div>
            <div className="text-xs text-gray-500">Open</div>
          </div>
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xl font-bold text-green-400">
              {d.incidents.resolved_last_7d}
            </div>
            <div className="text-xs text-gray-500">Resolved (7d)</div>
          </div>
        </div>
      </div>

      {/* Policies Section */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
          <Shield className="h-4 w-4" />
          Policies
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-900/50 rounded p-3">
            <div className="text-xl font-bold text-white">
              {d.policies.active}
            </div>
            <div className="text-xs text-gray-500">Active Policies</div>
          </div>
          <div className="bg-gray-900/50 rounded p-3">
            <div
              className={`text-xl font-bold ${d.policies.violations_last_7d > 0 ? 'text-yellow-400' : 'text-white'}`}
            >
              {d.policies.violations_last_7d}
            </div>
            <div className="text-xs text-gray-500">Violations (7d)</div>
          </div>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-gray-700 text-xs text-gray-500">
        Collected at: {new Date(diagnostics.collected_at).toLocaleString()}
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function FounderExplorerPage() {
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Compass className="h-8 w-8 text-emerald-400" />
          <h1 className="text-2xl font-bold text-white">Founder Explorer</h1>
        </div>
        <p className="text-gray-400">
          Cross-tenant visibility for business learning and diagnostics
        </p>

        {/* Advisory Notice */}
        <div className="mt-4 p-3 bg-emerald-900/20 border border-emerald-800 rounded-lg text-sm text-emerald-400">
          <strong>READ-ONLY:</strong> This console provides visibility into all
          tenants for diagnostic purposes. No mutation operations are available.
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Overview & Health */}
        <div className="lg:col-span-2 space-y-6">
          <SystemOverviewCard />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <HealthChecksCard />
            <UsagePatternsCard />
          </div>
        </div>

        {/* Right Column - Tenant List or Diagnostics */}
        <div>
          {selectedTenantId ? (
            <TenantDiagnosticsPanel
              tenantId={selectedTenantId}
              onClose={() => setSelectedTenantId(null)}
            />
          ) : (
            <TenantListCard onSelectTenant={setSelectedTenantId} />
          )}
        </div>
      </div>
    </div>
  );
}
