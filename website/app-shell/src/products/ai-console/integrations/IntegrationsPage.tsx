/**
 * Customer Integrations Page - Connected Services & Webhooks
 *
 * Customer Console v1 Constitution: Connectivity Section
 * Purpose: Manage external service connections and webhooks
 *
 * Shows:
 * - Webhook endpoints (configured destinations)
 * - Connected services (OAuth integrations)
 * - Integration health status
 *
 * Design Principles:
 * - Clear status indicators for each integration
 * - Easy enable/disable controls
 * - Webhook delivery history
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { logger } from '@/lib/consoleLogger';

interface Webhook {
  id: string;
  name: string;
  url: string;
  events: string[];
  enabled: boolean;
  created_at: string;
  last_triggered?: string;
  success_rate: number;
  total_deliveries: number;
}

interface Integration {
  id: string;
  name: string;
  type: 'oauth' | 'api_key' | 'webhook';
  provider: string;
  status: 'connected' | 'disconnected' | 'error';
  connected_at?: string;
  last_sync?: string;
  icon: string;
}

interface IntegrationsResponse {
  webhooks: Webhook[];
  integrations: Integration[];
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  connected: { label: 'Connected', color: 'text-accent-success', bg: 'bg-accent-success/20' },
  disconnected: { label: 'Disconnected', color: 'text-slate-400', bg: 'bg-slate-500/20' },
  error: { label: 'Error', color: 'text-accent-danger', bg: 'bg-accent-danger/20' },
};

const EVENT_LABELS: Record<string, string> = {
  'run.started': 'Run Started',
  'run.completed': 'Run Completed',
  'run.failed': 'Run Failed',
  'incident.created': 'Incident Created',
  'incident.resolved': 'Incident Resolved',
  'policy.violated': 'Policy Violated',
  'budget.exceeded': 'Budget Exceeded',
};

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

export function IntegrationsPage() {
  const [activeTab, setActiveTab] = useState<'webhooks' | 'services'>('webhooks');
  const [selectedWebhook, setSelectedWebhook] = useState<Webhook | null>(null);

  useEffect(() => {
    logger.componentMount('CustomerIntegrationsPage');
    return () => logger.componentUnmount('CustomerIntegrationsPage');
  }, []);

  // Fetch integrations data
  const { data, isLoading, refetch } = useQuery<IntegrationsResponse>({
    queryKey: ['customer', 'integrations'],
    queryFn: async () => {
      // In production, this would call: GET /api/v1/integrations
      // For now, return demo data
      const now = Date.now();

      const demoWebhooks: Webhook[] = [
        {
          id: 'wh_001',
          name: 'Slack Alerts',
          url: 'https://hooks.slack.com/services/T00/B00/XXX',
          events: ['incident.created', 'policy.violated', 'budget.exceeded'],
          enabled: true,
          created_at: new Date(now - 30 * 86400000).toISOString(),
          last_triggered: new Date(now - 3600000).toISOString(),
          success_rate: 99.2,
          total_deliveries: 1247,
        },
        {
          id: 'wh_002',
          name: 'PagerDuty Incidents',
          url: 'https://events.pagerduty.com/integration/XXX/enqueue',
          events: ['incident.created', 'run.failed'],
          enabled: true,
          created_at: new Date(now - 14 * 86400000).toISOString(),
          last_triggered: new Date(now - 7200000).toISOString(),
          success_rate: 100,
          total_deliveries: 89,
        },
        {
          id: 'wh_003',
          name: 'Analytics Pipeline',
          url: 'https://analytics.example.com/ingest/aos',
          events: ['run.started', 'run.completed', 'run.failed'],
          enabled: false,
          created_at: new Date(now - 60 * 86400000).toISOString(),
          last_triggered: new Date(now - 7 * 86400000).toISOString(),
          success_rate: 94.5,
          total_deliveries: 5623,
        },
      ];

      const demoIntegrations: Integration[] = [
        {
          id: 'int_001',
          name: 'GitHub',
          type: 'oauth',
          provider: 'github',
          status: 'connected',
          connected_at: new Date(now - 45 * 86400000).toISOString(),
          last_sync: new Date(now - 1800000).toISOString(),
          icon: '🐙',
        },
        {
          id: 'int_002',
          name: 'Slack',
          type: 'oauth',
          provider: 'slack',
          status: 'connected',
          connected_at: new Date(now - 30 * 86400000).toISOString(),
          last_sync: new Date(now - 3600000).toISOString(),
          icon: '💬',
        },
        {
          id: 'int_003',
          name: 'Datadog',
          type: 'api_key',
          provider: 'datadog',
          status: 'connected',
          connected_at: new Date(now - 20 * 86400000).toISOString(),
          last_sync: new Date(now - 300000).toISOString(),
          icon: '📊',
        },
        {
          id: 'int_004',
          name: 'Jira',
          type: 'oauth',
          provider: 'jira',
          status: 'disconnected',
          icon: '📋',
        },
        {
          id: 'int_005',
          name: 'Linear',
          type: 'api_key',
          provider: 'linear',
          status: 'error',
          connected_at: new Date(now - 10 * 86400000).toISOString(),
          icon: '📐',
        },
      ];

      return {
        webhooks: demoWebhooks,
        integrations: demoIntegrations,
      };
    },
    refetchInterval: 60000,
    staleTime: 30000,
  });

  const webhooks = data?.webhooks ?? [];
  const integrations = data?.integrations ?? [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading integrations...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span>🔗</span> Integrations
          </h1>
          <p className="text-slate-400 mt-1">
            Manage webhooks and connected services
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 bg-navy-elevated border border-navy-border hover:bg-navy-subtle rounded-lg text-sm text-slate-300 flex items-center gap-2 transition-colors"
          >
            <span>🔄</span> Refresh
          </button>
          <button
            className="px-3 py-1.5 bg-accent-info/20 border border-accent-info/30 text-accent-info hover:bg-accent-info/30 rounded-lg text-sm flex items-center gap-2 transition-colors"
          >
            <span>➕</span> Add Integration
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex items-center gap-2 border-b border-navy-border">
        <button
          onClick={() => setActiveTab('webhooks')}
          className={`
            px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px
            ${activeTab === 'webhooks'
              ? 'border-accent-info text-accent-info'
              : 'border-transparent text-slate-400 hover:text-white'
            }
          `}
        >
          Webhooks ({webhooks.length})
        </button>
        <button
          onClick={() => setActiveTab('services')}
          className={`
            px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px
            ${activeTab === 'services'
              ? 'border-accent-info text-accent-info'
              : 'border-transparent text-slate-400 hover:text-white'
            }
          `}
        >
          Connected Services ({integrations.length})
        </button>
      </div>

      {/* Content */}
      {activeTab === 'webhooks' ? (
        <div className="flex gap-6">
          {/* Webhooks List */}
          <div className="flex-1">
            <div className="bg-navy-surface rounded-xl border border-navy-border overflow-hidden">
              {webhooks.length === 0 ? (
                <div className="p-8 text-center text-slate-400">
                  No webhooks configured
                </div>
              ) : (
                <div className="divide-y divide-navy-border">
                  {webhooks.map((webhook) => {
                    const isSelected = selectedWebhook?.id === webhook.id;

                    return (
                      <div
                        key={webhook.id}
                        onClick={() => setSelectedWebhook(webhook)}
                        className={`
                          p-4 cursor-pointer transition-colors
                          ${isSelected ? 'bg-navy-elevated' : 'hover:bg-navy-elevated/50'}
                        `}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">🪝</span>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-white">{webhook.name}</span>
                                {webhook.enabled ? (
                                  <span className="px-2 py-0.5 text-xs rounded bg-accent-success/20 text-accent-success">
                                    Active
                                  </span>
                                ) : (
                                  <span className="px-2 py-0.5 text-xs rounded bg-slate-500/20 text-slate-400">
                                    Disabled
                                  </span>
                                )}
                              </div>
                              <div className="text-sm text-slate-400 mt-1 font-mono truncate max-w-md">
                                {webhook.url.replace(/\/[A-Za-z0-9]{10,}.*$/, '/***')}
                              </div>
                            </div>
                          </div>
                          <div className="text-right text-sm">
                            <div className="text-slate-300">{webhook.success_rate}% success</div>
                            <div className="text-slate-500">{webhook.total_deliveries} deliveries</div>
                          </div>
                        </div>

                        {/* Events */}
                        <div className="mt-3 flex flex-wrap gap-2">
                          {webhook.events.map((event) => (
                            <span
                              key={event}
                              className="px-2 py-0.5 text-xs rounded bg-navy-inset text-slate-300"
                            >
                              {EVENT_LABELS[event] || event}
                            </span>
                          ))}
                        </div>

                        {/* Last triggered */}
                        {webhook.last_triggered && (
                          <div className="mt-2 text-xs text-slate-500">
                            Last triggered: {formatRelativeTime(webhook.last_triggered)}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Webhook Details Panel */}
          {selectedWebhook && (
            <div className="w-96">
              <WebhookDetailsPanel
                webhook={selectedWebhook}
                onClose={() => setSelectedWebhook(null)}
              />
            </div>
          )}
        </div>
      ) : (
        /* Connected Services Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {integrations.map((integration) => {
            const statusConfig = STATUS_CONFIG[integration.status];

            return (
              <div
                key={integration.id}
                className="bg-navy-surface rounded-xl border border-navy-border p-4 hover:border-navy-border/80 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{integration.icon}</span>
                    <div>
                      <div className="font-medium text-white">{integration.name}</div>
                      <div className="text-xs text-slate-400 capitalize">{integration.type.replace('_', ' ')}</div>
                    </div>
                  </div>
                  <span className={`
                    px-2 py-0.5 text-xs rounded font-medium
                    ${statusConfig.color} ${statusConfig.bg}
                  `}>
                    {statusConfig.label}
                  </span>
                </div>

                {integration.connected_at && (
                  <div className="mt-4 pt-4 border-t border-navy-border">
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <div className="text-slate-500">Connected</div>
                        <div className="text-slate-300">{formatDate(integration.connected_at)}</div>
                      </div>
                      {integration.last_sync && (
                        <div>
                          <div className="text-slate-500">Last Sync</div>
                          <div className="text-slate-300">{formatRelativeTime(integration.last_sync)}</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="mt-4 flex items-center gap-2">
                  {integration.status === 'connected' ? (
                    <>
                      <button className="flex-1 px-3 py-1.5 bg-navy-elevated border border-navy-border rounded-lg text-sm text-slate-300 hover:bg-navy-subtle transition-colors">
                        Configure
                      </button>
                      <button className="px-3 py-1.5 bg-navy-elevated border border-accent-danger/30 rounded-lg text-sm text-accent-danger hover:bg-navy-subtle transition-colors">
                        Disconnect
                      </button>
                    </>
                  ) : integration.status === 'error' ? (
                    <button className="flex-1 px-3 py-1.5 bg-accent-warning/20 border border-accent-warning/30 rounded-lg text-sm text-accent-warning hover:bg-accent-warning/30 transition-colors">
                      Reconnect
                    </button>
                  ) : (
                    <button className="flex-1 px-3 py-1.5 bg-accent-info/20 border border-accent-info/30 rounded-lg text-sm text-accent-info hover:bg-accent-info/30 transition-colors">
                      Connect
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {/* Add New Integration Card */}
          <div className="bg-navy-surface rounded-xl border border-dashed border-navy-border p-4 flex flex-col items-center justify-center min-h-[180px] hover:border-accent-info/30 transition-colors cursor-pointer">
            <span className="text-3xl mb-2">➕</span>
            <span className="text-slate-400">Add Integration</span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Webhook Details Panel
 */
function WebhookDetailsPanel({ webhook, onClose }: { webhook: Webhook; onClose: () => void }) {
  return (
    <div className="bg-navy-surface rounded-xl border border-navy-border p-4 sticky top-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-white">Webhook Details</h3>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>

      <div className="space-y-4">
        {/* Name & Status */}
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium text-white">{webhook.name}</span>
            {webhook.enabled ? (
              <span className="px-2 py-0.5 text-xs rounded bg-accent-success/20 text-accent-success">
                Active
              </span>
            ) : (
              <span className="px-2 py-0.5 text-xs rounded bg-slate-500/20 text-slate-400">
                Disabled
              </span>
            )}
          </div>
        </div>

        {/* URL */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Endpoint URL</div>
          <div className="font-mono text-sm text-slate-300 bg-navy-inset rounded px-3 py-2 break-all">
            {webhook.url}
          </div>
        </div>

        {/* Events */}
        <div>
          <div className="text-xs text-slate-500 mb-2">Subscribed Events</div>
          <div className="flex flex-wrap gap-2">
            {webhook.events.map((event) => (
              <span
                key={event}
                className="px-2 py-1 text-xs rounded bg-navy-inset text-slate-300"
              >
                {EVENT_LABELS[event] || event}
              </span>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="pt-4 border-t border-navy-border">
          <div className="text-xs text-slate-500 font-bold uppercase tracking-wide mb-3">
            Delivery Stats
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-navy-inset rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-white">{webhook.success_rate}%</div>
              <div className="text-xs text-slate-400">Success Rate</div>
            </div>
            <div className="bg-navy-inset rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-white">{webhook.total_deliveries}</div>
              <div className="text-xs text-slate-400">Total Deliveries</div>
            </div>
          </div>
        </div>

        {/* Timestamps */}
        <div className="pt-4 border-t border-navy-border">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Created</span>
              <span className="text-slate-300">{formatDate(webhook.created_at)}</span>
            </div>
            {webhook.last_triggered && (
              <div className="flex justify-between">
                <span className="text-slate-400">Last Triggered</span>
                <span className="text-slate-300">{formatRelativeTime(webhook.last_triggered)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="pt-4 border-t border-navy-border flex gap-2">
          <button className="flex-1 px-3 py-2 bg-navy-elevated border border-navy-border rounded-lg text-sm text-slate-300 hover:bg-navy-subtle transition-colors">
            Edit
          </button>
          <button className="flex-1 px-3 py-2 bg-navy-elevated border border-navy-border rounded-lg text-sm text-slate-300 hover:bg-navy-subtle transition-colors">
            Test
          </button>
          {webhook.enabled ? (
            <button className="px-3 py-2 bg-navy-elevated border border-accent-warning/30 rounded-lg text-sm text-accent-warning hover:bg-navy-subtle transition-colors">
              Disable
            </button>
          ) : (
            <button className="px-3 py-2 bg-accent-success/20 border border-accent-success/30 rounded-lg text-sm text-accent-success hover:bg-accent-success/30 transition-colors">
              Enable
            </button>
          )}
        </div>

        {/* Webhook ID */}
        <div className="pt-4 border-t border-navy-border">
          <div className="text-xs text-slate-500 mb-1">Webhook ID</div>
          <div className="font-mono text-xs text-slate-400 bg-navy-inset rounded px-2 py-1">
            {webhook.id}
          </div>
        </div>
      </div>
    </div>
  );
}

export default IntegrationsPage;
