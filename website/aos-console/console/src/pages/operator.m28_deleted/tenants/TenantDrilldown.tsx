/**
 * Tenant Drilldown - Operator Console
 *
 * Deep-dive into a specific tenant.
 * Everything the operator needs to understand and help a tenant.
 *
 * Displays:
 * - Tenant profile and status
 * - Usage metrics (requests, spend, errors)
 * - Active guardrails and thresholds
 * - Recent incidents
 * - API key status
 * - Quick actions (freeze/unfreeze, adjust limits)
 */

import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../../../components/common/Card';
import { Button } from '../../../components/common/Button';
import { Badge } from '../../../components/common/Badge';
import { Modal } from '../../../components/common/Modal';
import { Spinner } from '../../../components/common/Spinner';
import { operatorApi } from '../../../api/operator';

interface TenantProfile {
  tenant_id: string;
  tenant_name: string;
  email: string;
  plan: 'starter' | 'pro' | 'enterprise';
  created_at: string;
  status: 'active' | 'frozen' | 'suspended';
  frozen_at: string | null;
  frozen_by: string | null;
  frozen_reason: string | null;
}

interface TenantMetrics {
  requests_24h: number;
  requests_7d: number;
  spend_24h_cents: number;
  spend_7d_cents: number;
  error_rate_24h: number;
  avg_latency_ms: number;
  incidents_24h: number;
  incidents_7d: number;
  cost_avoided_7d_cents: number;
}

interface TenantGuardrail {
  id: string;
  name: string;
  enabled: boolean;
  threshold_value: number;
  threshold_unit: string;
  triggers_24h: number;
}

interface TenantIncident {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  status: string;
  started_at: string;
}

interface TenantApiKey {
  id: string;
  name: string;
  prefix: string;
  status: 'active' | 'frozen' | 'revoked';
  requests_24h: number;
}

const PLAN_COLORS = {
  starter: 'bg-gray-100 text-gray-800',
  pro: 'bg-blue-100 text-blue-800',
  enterprise: 'bg-purple-100 text-purple-800',
};

const STATUS_COLORS = {
  active: 'bg-green-100 text-green-800',
  frozen: 'bg-yellow-100 text-yellow-800',
  suspended: 'bg-red-100 text-red-800',
};

export function TenantDrilldown() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const queryClient = useQueryClient();
  const [showFreezeModal, setShowFreezeModal] = useState(false);
  const [freezeReason, setFreezeReason] = useState('');

  // Fetch tenant profile
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['operator', 'tenant', tenantId, 'profile'],
    queryFn: () => operatorApi.getTenantProfile(tenantId!),
    enabled: !!tenantId,
  });

  // Fetch tenant metrics
  const { data: metrics } = useQuery({
    queryKey: ['operator', 'tenant', tenantId, 'metrics'],
    queryFn: () => operatorApi.getTenantMetrics(tenantId!),
    enabled: !!tenantId,
    refetchInterval: 30000,
  });

  // Fetch tenant guardrails
  const { data: guardrails } = useQuery({
    queryKey: ['operator', 'tenant', tenantId, 'guardrails'],
    queryFn: () => operatorApi.getTenantGuardrails(tenantId!),
    enabled: !!tenantId,
  });

  // Fetch recent incidents
  const { data: incidents } = useQuery({
    queryKey: ['operator', 'tenant', tenantId, 'incidents'],
    queryFn: () => operatorApi.getTenantIncidents(tenantId!, 5),
    enabled: !!tenantId,
  });

  // Fetch API keys
  const { data: apiKeys } = useQuery({
    queryKey: ['operator', 'tenant', tenantId, 'keys'],
    queryFn: () => operatorApi.getTenantApiKeys(tenantId!),
    enabled: !!tenantId,
  });

  // Freeze tenant mutation
  const freezeMutation = useMutation({
    mutationFn: ({ tenantId, reason }: { tenantId: string; reason: string }) =>
      operatorApi.freezeTenant(tenantId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator', 'tenant', tenantId] });
      setShowFreezeModal(false);
      setFreezeReason('');
    },
  });

  // Unfreeze tenant mutation
  const unfreezeMutation = useMutation({
    mutationFn: (tenantId: string) => operatorApi.unfreezeTenant(tenantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator', 'tenant', tenantId] });
    },
  });

  if (profileLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-6">
        <Card className="text-center py-12">
          <div className="text-gray-400 text-5xl mb-4">🔍</div>
          <h3 className="text-lg font-medium text-gray-900">Tenant Not Found</h3>
          <p className="text-gray-500">No tenant with ID: {tenantId}</p>
          <Link to="/operator/tenants" className="mt-4 text-blue-600 hover:text-blue-800">
            ← Back to tenant list
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/operator"
            className="text-gray-400 hover:text-gray-600"
          >
            ←
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">{profile.tenant_name}</h1>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${PLAN_COLORS[profile.plan]}`}>
                {profile.plan}
              </span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[profile.status]}`}>
                {profile.status}
              </span>
            </div>
            <p className="text-gray-500 text-sm mt-1">{profile.email} • {profile.tenant_id}</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-3">
          {profile.status === 'active' ? (
            <Button
              variant="danger"
              onClick={() => setShowFreezeModal(true)}
            >
              Freeze Tenant
            </Button>
          ) : profile.status === 'frozen' ? (
            <Button
              variant="primary"
              onClick={() => unfreezeMutation.mutate(tenantId!)}
              disabled={unfreezeMutation.isPending}
              className="bg-green-600 hover:bg-green-700"
            >
              {unfreezeMutation.isPending ? 'Unfreezing...' : 'Unfreeze Tenant'}
            </Button>
          ) : null}
        </div>
      </div>

      {/* Frozen Banner */}
      {profile.status === 'frozen' && profile.frozen_at && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-yellow-500 text-xl">⚠️</span>
            <div>
              <h4 className="font-medium text-yellow-800">Tenant Frozen</h4>
              <p className="text-yellow-700 text-sm mt-1">
                Frozen at {new Date(profile.frozen_at).toLocaleString()}
                {profile.frozen_by && ` by ${profile.frozen_by}`}
              </p>
              {profile.frozen_reason && (
                <p className="text-yellow-700 text-sm mt-1">
                  Reason: {profile.frozen_reason}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          label="Requests (24h)"
          value={metrics?.requests_24h?.toLocaleString() ?? '0'}
          subValue={`${metrics?.requests_7d?.toLocaleString() ?? 0} (7d)`}
        />
        <MetricCard
          label="Spend (24h)"
          value={`$${((metrics?.spend_24h_cents ?? 0) / 100).toFixed(2)}`}
          subValue={`$${((metrics?.spend_7d_cents ?? 0) / 100).toFixed(2)} (7d)`}
        />
        <MetricCard
          label="Error Rate (24h)"
          value={`${((metrics?.error_rate_24h ?? 0) * 100).toFixed(2)}%`}
          subValue={`${metrics?.avg_latency_ms ?? 0}ms avg latency`}
          highlight={(metrics?.error_rate_24h ?? 0) > 0.05}
        />
        <MetricCard
          label="Incidents (7d)"
          value={metrics?.incidents_7d?.toString() ?? '0'}
          subValue={`$${((metrics?.cost_avoided_7d_cents ?? 0) / 100).toFixed(2)} avoided`}
          highlight={(metrics?.incidents_7d ?? 0) > 5}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Guardrails */}
        <Card>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Active Guardrails</h3>
          <div className="space-y-3">
            {guardrails?.items?.map((guardrail: TenantGuardrail) => (
              <div
                key={guardrail.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${guardrail.enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <span className="font-medium text-gray-900">{guardrail.name}</span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-gray-500">
                    {guardrail.threshold_value} {guardrail.threshold_unit}
                  </span>
                  {guardrail.triggers_24h > 0 && (
                    <Badge variant="warning">
                      {guardrail.triggers_24h} triggers
                    </Badge>
                  )}
                </div>
              </div>
            ))}
            {(!guardrails?.items || guardrails.items.length === 0) && (
              <p className="text-gray-500 text-center py-4">No guardrails configured</p>
            )}
          </div>
        </Card>

        {/* Recent Incidents */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Recent Incidents</h3>
            <Link
              to={`/operator/incidents?tenant=${tenantId}`}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              View all →
            </Link>
          </div>
          <div className="space-y-2">
            {incidents?.items?.map((incident: TenantIncident) => (
              <Link
                key={incident.id}
                to={`/operator/incidents/${incident.id}`}
                className="flex items-center justify-between p-2 rounded hover:bg-gray-50"
              >
                <div className="flex items-center gap-3">
                  <SeverityDot severity={incident.severity} />
                  <span className="text-sm text-gray-900">{incident.title}</span>
                </div>
                <span className="text-xs text-gray-400">
                  {formatTimeAgo(new Date(incident.started_at))}
                </span>
              </Link>
            ))}
            {(!incidents?.items || incidents.items.length === 0) && (
              <p className="text-gray-500 text-center py-4">No recent incidents</p>
            )}
          </div>
        </Card>

        {/* API Keys */}
        <Card className="col-span-2">
          <h3 className="text-lg font-medium text-gray-900 mb-4">API Keys</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2">Name</th>
                  <th className="pb-2">Key Prefix</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Requests (24h)</th>
                </tr>
              </thead>
              <tbody>
                {apiKeys?.items?.map((key: TenantApiKey) => (
                  <tr key={key.id} className="border-b last:border-0">
                    <td className="py-3 font-medium text-gray-900">{key.name}</td>
                    <td className="py-3 font-mono text-gray-500">{key.prefix}...</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        key.status === 'active' ? 'bg-green-100 text-green-800' :
                        key.status === 'frozen' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {key.status}
                      </span>
                    </td>
                    <td className="py-3 text-gray-600">{key.requests_24h.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(!apiKeys?.items || apiKeys.items.length === 0) && (
              <p className="text-gray-500 text-center py-4">No API keys</p>
            )}
          </div>
        </Card>
      </div>

      {/* Freeze Modal */}
      <Modal
        open={showFreezeModal}
        onClose={() => setShowFreezeModal(false)}
        title="Freeze Tenant"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            This will immediately stop all API traffic for this tenant.
            They will not be able to make any requests until you unfreeze them.
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason (required)
            </label>
            <textarea
              value={freezeReason}
              onChange={(e) => setFreezeReason(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              rows={3}
              placeholder="Enter reason for freezing this tenant..."
            />
          </div>

          <div className="flex gap-3 justify-end">
            <Button
              variant="secondary"
              onClick={() => setShowFreezeModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => freezeMutation.mutate({
                tenantId: tenantId!,
                reason: freezeReason,
              })}
              disabled={!freezeReason.trim() || freezeMutation.isPending}
            >
              {freezeMutation.isPending ? 'Freezing...' : 'Freeze Tenant'}
            </Button>
          </div>
        </div>
      </Modal>
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

// Severity Dot
function SeverityDot({ severity }: { severity: string }) {
  const colors = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-gray-400',
  };

  return (
    <span className={`w-2 h-2 rounded-full ${colors[severity as keyof typeof colors] ?? 'bg-gray-400'}`} />
  );
}

// Helper function
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

export default TenantDrilldown;
