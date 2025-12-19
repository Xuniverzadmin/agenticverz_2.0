/**
 * Global Overview - Operator Console
 *
 * System-wide health at a glance.
 * The operator's dashboard - shows everything that matters.
 *
 * Displays:
 * - System status (all tenants aggregated)
 * - Active incidents across all tenants
 * - Top consumers (by spend, by incidents)
 * - Model drift alerts
 * - Rate limit pressure
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card } from '../../../components/common/Card';
import { Badge } from '../../../components/common/Badge';
import { Spinner } from '../../../components/common/Spinner';
import { operatorApi } from '../../../api/operator';

interface SystemStatus {
  status: 'healthy' | 'degraded' | 'critical';
  total_tenants: number;
  active_tenants_24h: number;
  frozen_tenants: number;
  total_requests_24h: number;
  total_spend_24h_cents: number;
  active_incidents: number;
  model_drift_alerts: number;
}

interface TopTenant {
  tenant_id: string;
  tenant_name: string;
  metric_value: number;
  metric_label: string;
}

interface RecentIncident {
  id: string;
  tenant_id: string;
  tenant_name: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  started_at: string;
}

const STATUS_CONFIG = {
  healthy: { label: 'All Systems Operational', color: 'green', icon: '✓' },
  degraded: { label: 'Degraded Performance', color: 'yellow', icon: '⚠' },
  critical: { label: 'Critical Issues', color: 'red', icon: '✗' },
};

export function GlobalOverview() {
  // Fetch system status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['operator', 'status'],
    queryFn: operatorApi.getSystemStatus,
    refetchInterval: 5000,
  });

  // Fetch top tenants by spend
  const { data: topBySpend } = useQuery({
    queryKey: ['operator', 'top-tenants', 'spend'],
    queryFn: () => operatorApi.getTopTenants('spend', 5),
    refetchInterval: 30000,
  });

  // Fetch top tenants by incidents
  const { data: topByIncidents } = useQuery({
    queryKey: ['operator', 'top-tenants', 'incidents'],
    queryFn: () => operatorApi.getTopTenants('incidents', 5),
    refetchInterval: 30000,
  });

  // Fetch recent incidents
  const { data: recentIncidents } = useQuery({
    queryKey: ['operator', 'recent-incidents'],
    queryFn: () => operatorApi.getRecentIncidents(10),
    refetchInterval: 10000,
  });

  if (statusLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[status?.status ?? 'healthy'];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">System Overview</h1>
        <div className="text-sm text-gray-500">
          Auto-refresh: 5s
        </div>
      </div>

      {/* System Status Banner */}
      <div className={`p-4 rounded-lg flex items-center gap-4 ${
        statusConfig.color === 'green' ? 'bg-green-100' :
        statusConfig.color === 'yellow' ? 'bg-yellow-100' :
        'bg-red-100'
      }`}>
        <span className={`text-2xl ${
          statusConfig.color === 'green' ? 'text-green-600' :
          statusConfig.color === 'yellow' ? 'text-yellow-600' :
          'text-red-600'
        }`}>
          {statusConfig.icon}
        </span>
        <div>
          <h2 className={`font-bold ${
            statusConfig.color === 'green' ? 'text-green-800' :
            statusConfig.color === 'yellow' ? 'text-yellow-800' :
            'text-red-800'
          }`}>
            {statusConfig.label}
          </h2>
          <p className={`text-sm ${
            statusConfig.color === 'green' ? 'text-green-700' :
            statusConfig.color === 'yellow' ? 'text-yellow-700' :
            'text-red-700'
          }`}>
            {status?.active_incidents ?? 0} active incidents • {status?.frozen_tenants ?? 0} frozen tenants
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          label="Total Tenants"
          value={status?.total_tenants?.toLocaleString() ?? '0'}
          subValue={`${status?.active_tenants_24h ?? 0} active (24h)`}
        />
        <MetricCard
          label="Requests (24h)"
          value={formatNumber(status?.total_requests_24h ?? 0)}
          subValue={`${formatRate(status?.total_requests_24h ?? 0)} req/s avg`}
        />
        <MetricCard
          label="Spend (24h)"
          value={`$${((status?.total_spend_24h_cents ?? 0) / 100).toLocaleString()}`}
          subValue="Across all tenants"
        />
        <MetricCard
          label="Model Drift Alerts"
          value={status?.model_drift_alerts?.toString() ?? '0'}
          subValue="Requires review"
          highlight={status?.model_drift_alerts ?? 0 > 0}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Recent Incidents */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Recent Incidents</h3>
            <Link
              to="/operator/incidents"
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              View all →
            </Link>
          </div>
          <div className="space-y-3">
            {recentIncidents?.items?.slice(0, 5).map((incident: RecentIncident) => (
              <IncidentRow key={incident.id} incident={incident} />
            ))}
            {(!recentIncidents?.items || recentIncidents.items.length === 0) && (
              <p className="text-gray-500 text-center py-4">No active incidents</p>
            )}
          </div>
        </Card>

        {/* Top Tenants */}
        <div className="space-y-6">
          {/* By Spend */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Top by Spend (24h)</h3>
            </div>
            <div className="space-y-2">
              {topBySpend?.items?.map((tenant: TopTenant, index: number) => (
                <TenantRow
                  key={tenant.tenant_id}
                  tenant={tenant}
                  rank={index + 1}
                />
              ))}
            </div>
          </Card>

          {/* By Incidents */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Top by Incidents (24h)</h3>
            </div>
            <div className="space-y-2">
              {topByIncidents?.items?.map((tenant: TopTenant, index: number) => (
                <TenantRow
                  key={tenant.tenant_id}
                  tenant={tenant}
                  rank={index + 1}
                />
              ))}
              {(!topByIncidents?.items || topByIncidents.items.length === 0) && (
                <p className="text-gray-500 text-center py-4">No incidents in 24h</p>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <Card>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div className="flex gap-4">
          <Link
            to="/operator/incidents"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Live Incident Stream
          </Link>
          <Link
            to="/operator/audit"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Policy Audit Log
          </Link>
          <Link
            to="/operator/replay"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            Replay Lab
          </Link>
        </div>
      </Card>
    </div>
  );
}

// Metric Card
function MetricCard({
  label,
  value,
  subValue,
  highlight = false,
}: {
  label: string;
  value: string;
  subValue: string;
  highlight?: boolean;
}) {
  return (
    <Card className={highlight ? 'ring-2 ring-yellow-500' : ''}>
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${highlight ? 'text-yellow-600' : 'text-gray-900'}`}>
        {value}
      </p>
      <p className="text-xs text-gray-400 mt-1">{subValue}</p>
    </Card>
  );
}

// Incident Row
function IncidentRow({ incident }: { incident: RecentIncident }) {
  const severityColors = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-gray-100 text-gray-800',
  };

  return (
    <Link
      to={`/operator/incidents/${incident.id}`}
      className="flex items-center justify-between p-2 rounded hover:bg-gray-50"
    >
      <div className="flex items-center gap-3">
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColors[incident.severity]}`}>
          {incident.severity}
        </span>
        <div>
          <p className="text-sm font-medium text-gray-900">{incident.title}</p>
          <p className="text-xs text-gray-500">{incident.tenant_name}</p>
        </div>
      </div>
      <span className="text-xs text-gray-400">
        {formatTimeAgo(new Date(incident.started_at))}
      </span>
    </Link>
  );
}

// Tenant Row
function TenantRow({ tenant, rank }: { tenant: TopTenant; rank: number }) {
  return (
    <Link
      to={`/operator/tenants/${tenant.tenant_id}`}
      className="flex items-center justify-between p-2 rounded hover:bg-gray-50"
    >
      <div className="flex items-center gap-3">
        <span className="w-6 h-6 flex items-center justify-center bg-gray-200 text-gray-600 text-xs font-medium rounded-full">
          {rank}
        </span>
        <span className="text-sm font-medium text-gray-900">{tenant.tenant_name}</span>
      </div>
      <span className="text-sm text-gray-600">{tenant.metric_label}</span>
    </Link>
  );
}

// Helper functions
function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function formatRate(requests24h: number): string {
  const rps = requests24h / (24 * 60 * 60);
  if (rps >= 1000) return `${(rps / 1000).toFixed(1)}K`;
  return rps.toFixed(1);
}

function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  return `${Math.floor(diffHours / 24)}d ago`;
}

export default GlobalOverview;
