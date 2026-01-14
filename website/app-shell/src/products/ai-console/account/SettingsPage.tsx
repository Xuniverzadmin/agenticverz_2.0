/**
 * AI Console Settings Page
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console
 * Role: View guardrails, notifications, and settings
 *
 * NO FAKE DATA. NO DEMO FALLBACKS.
 * If API fails, show error. If data missing, show empty state.
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { guardApi, TenantSettings, GuardrailConfig } from '@/api/guard';
import { apiClient } from '@/api/client';
import { logger } from '@/lib/consoleLogger';

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'guardrails' | 'notifications' | 'keys' | 'export'>('guardrails');

  useEffect(() => {
    logger.componentMount('AIConsoleSettingsPage');
    return () => logger.componentUnmount('AIConsoleSettingsPage');
  }, []);

  // Fetch settings - NO FALLBACK
  const { data: settings, isLoading, error } = useQuery({
    queryKey: ['guard', 'settings'],
    queryFn: guardApi.getSettings,
    retry: false,
  });

  const tabs = [
    { id: 'guardrails', label: 'Guardrails', icon: '🔒' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
    { id: 'keys', label: 'API Keys', icon: '🔑' },
    { id: 'export', label: 'Export', icon: '📤' },
  ] as const;

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="text-slate-400">Loading settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-red-500/10 border border-red-400/40 rounded-xl p-6">
          <h3 className="font-bold text-red-400">Failed to Load Settings</h3>
          <p className="text-sm text-slate-300 mt-1">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-amber-500/10 border border-amber-400/40 rounded-xl p-6">
          <h3 className="font-bold text-amber-400">No Settings Available</h3>
          <p className="text-sm text-slate-300 mt-1">
            Settings API returned empty response.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>⚙️</span> Settings
        </h1>
        <p className="text-slate-400 mt-1">
          View guardrails, notifications, and export options
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-navy-border pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              px-4 py-2 rounded-t-lg font-medium transition-colors
              ${activeTab === tab.id
                ? 'bg-navy-elevated text-accent-info border-b-2 border-accent-info'
                : 'text-slate-400 hover:text-white hover:bg-navy-elevated'
              }
            `}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'guardrails' && (
        <GuardrailsTab guardrails={settings.guardrails || []} />
      )}
      {activeTab === 'notifications' && (
        <NotificationsTab settings={settings} />
      )}
      {activeTab === 'keys' && (
        <KeysTab />
      )}
      {activeTab === 'export' && (
        <ExportTab />
      )}
    </div>
  );
}

// ============================================================================
// Guardrails Tab - READ-ONLY STATUS INDICATORS
// ============================================================================

function GuardrailsTab({ guardrails }: { guardrails: GuardrailConfig[] }) {
  if (guardrails.length === 0) {
    return (
      <div className="bg-navy-surface rounded-xl border border-navy-border p-8 text-center">
        <p className="text-slate-400">No guardrails configured.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white">Active Guardrails</h2>
          <p className="text-sm text-slate-400">Protection rules for your AI traffic</p>
        </div>
      </div>

      <div className="bg-navy-surface rounded-xl border border-navy-border overflow-hidden">
        {guardrails.map((guardrail, index) => (
          <div
            key={guardrail.id}
            className={`p-4 ${index > 0 ? 'border-t border-navy-border' : ''}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <GuardrailStatusIndicator enabled={guardrail.enabled} />
                <div>
                  <h3 className="font-medium text-white">{guardrail.name}</h3>
                  <p className="text-sm text-slate-400">{guardrail.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className="text-lg font-bold text-accent-info">{guardrail.threshold_value}</span>
                  <span className="text-sm text-slate-400 ml-1">{guardrail.threshold_unit}</span>
                </div>
                <ActionBadge action={guardrail.action_on_trigger} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function GuardrailStatusIndicator({ enabled }: { enabled: boolean }) {
  return (
    <div className={`
      flex items-center gap-2 px-3 py-1.5 rounded-lg
      border ${enabled ? 'border-green-500/30' : 'border-slate-600'}
      ${enabled ? 'text-green-400' : 'text-slate-500'}
    `}>
      <span className={`w-2 h-2 rounded-full ${enabled ? 'bg-green-400' : 'bg-slate-600'}`} />
      <span className="text-xs font-medium uppercase tracking-wide">
        {enabled ? 'Enabled' : 'Disabled'}
      </span>
    </div>
  );
}

function ActionBadge({ action }: { action: string }) {
  const config: Record<string, { text: string; border: string }> = {
    block: { text: 'text-red-400', border: 'border-red-400/40' },
    throttle: { text: 'text-amber-400', border: 'border-amber-400/40' },
    killswitch: { text: 'text-red-400', border: 'border-red-400/40' },
    warn: { text: 'text-blue-400', border: 'border-blue-400/40' },
  };
  const style = config[action] || { text: 'text-slate-400', border: 'border-slate-600' };

  return (
    <span className={`px-2 py-1 rounded border text-xs font-medium bg-transparent ${style.text} ${style.border}`}>
      {action}
    </span>
  );
}

// ============================================================================
// Notifications Tab
// ============================================================================

function NotificationsTab({ settings }: { settings: TenantSettings }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white">Notification Settings</h2>
        <p className="text-sm text-slate-400">View alert configuration</p>
      </div>

      <div className="bg-navy-surface rounded-xl border border-navy-border p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Alert Email</label>
          <div className="w-full bg-navy-inset border border-navy-border rounded-lg px-4 py-2 text-slate-400">
            {settings.notification_email || 'Not configured'}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Slack Webhook</label>
          <div className="w-full bg-navy-inset border border-navy-border rounded-lg px-4 py-2 text-slate-400 font-mono text-sm">
            {settings.notification_slack_webhook ? '••••••••••••••••' : 'Not configured'}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// API Keys Tab - Real API only
// ============================================================================

interface ApiKeyData {
  id: string;
  name: string;
  prefix: string;
  status: string;
  requests_today: number;
  spend_today_cents: number;
}

function KeysTab() {
  const { data: keys, isLoading, error } = useQuery({
    queryKey: ['guard', 'keys'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/keys');
      return response.data;
    },
    retry: false,
  });

  if (isLoading) {
    return <div className="text-slate-400">Loading keys...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-400/40 rounded-xl p-6">
        <h3 className="font-bold text-red-400">Keys API Not Available</h3>
        <p className="text-sm text-slate-300 mt-1">
          {error instanceof Error ? error.message : 'Unknown error'}
        </p>
        <p className="text-xs text-slate-500 mt-2 font-mono">
          Required: GET /api/v1/keys
        </p>
      </div>
    );
  }

  const keysList: ApiKeyData[] = keys?.items || keys || [];

  if (keysList.length === 0) {
    return (
      <div className="bg-navy-surface rounded-xl border border-navy-border p-8 text-center">
        <p className="text-slate-400">No API keys found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white">API Keys</h2>
        <p className="text-sm text-slate-400">View your API keys</p>
      </div>

      <div className="bg-navy-surface rounded-xl border border-navy-border overflow-hidden">
        <table className="w-full">
          <thead className="bg-navy-elevated">
            <tr className="text-left text-sm text-slate-400">
              <th className="p-4">Name</th>
              <th className="p-4">Key</th>
              <th className="p-4">Status</th>
              <th className="p-4">Today</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-navy-border">
            {keysList.map((key) => (
              <tr key={key.id}>
                <td className="p-4 font-medium text-white">{key.name}</td>
                <td className="p-4 font-mono text-sm text-slate-400">{key.prefix}</td>
                <td className="p-4">
                  <span className={`
                    px-2 py-1 rounded border text-xs font-medium bg-transparent
                    ${key.status === 'active' ? 'text-green-400 border-green-400/40' : 'text-red-400 border-red-400/40'}
                  `}>
                    {key.status}
                  </span>
                </td>
                <td className="p-4 text-sm text-slate-400">
                  {key.requests_today} req • ${(key.spend_today_cents / 100).toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================================
// Export Tab
// ============================================================================

function ExportTab() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white">Data Export</h2>
        <p className="text-sm text-slate-400">Export data for compliance or analysis</p>
      </div>

      <div className="bg-amber-500/10 border border-amber-400/30 rounded-lg p-4">
        <p className="text-sm text-amber-400">
          Export API not implemented.
        </p>
        <p className="text-xs text-slate-500 mt-1 font-mono">
          Required: POST /api/v1/export/*
        </p>
      </div>
    </div>
  );
}

export default SettingsPage;
