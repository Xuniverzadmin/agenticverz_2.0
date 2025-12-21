/**
 * Guard Settings Page - Phase 8 Polish
 *
 * Configuration and settings:
 * - Guardrail configuration
 * - Notification settings
 * - API key management
 * - Export settings
 *
 * Operator confidence polish with clear labels and tooltips.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { guardApi, TenantSettings, GuardrailConfig } from '../../api/guard';

export function GuardSettingsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'guardrails' | 'notifications' | 'keys' | 'export'>('guardrails');

  // Fetch settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ['guard', 'settings'],
    queryFn: guardApi.getSettings,
  });

  // Demo settings if API fails
  const safeSettings: TenantSettings = settings || {
    tenant_id: 'tenant_demo',
    tenant_name: 'Demo Company',
    plan: 'pro',
    guardrails: [
      {
        id: 'gr_1',
        name: 'Max Cost Per Request',
        description: 'Block requests that would exceed this cost',
        enabled: true,
        threshold_type: 'cost',
        threshold_value: 10,
        threshold_unit: 'cents',
        action_on_trigger: 'block',
      },
      {
        id: 'gr_2',
        name: 'Rate Limit',
        description: 'Limit requests per minute per user',
        enabled: true,
        threshold_type: 'rate',
        threshold_value: 60,
        threshold_unit: 'requests/min',
        action_on_trigger: 'throttle',
      },
      {
        id: 'gr_3',
        name: 'Prompt Injection Block',
        description: 'Detect and block prompt injection attempts',
        enabled: true,
        threshold_type: 'pattern',
        threshold_value: 0.8,
        threshold_unit: 'confidence',
        action_on_trigger: 'block',
      },
      {
        id: 'gr_4',
        name: 'Daily Budget',
        description: 'Stop traffic when daily budget is exceeded',
        enabled: true,
        threshold_type: 'cost',
        threshold_value: 5000,
        threshold_unit: 'cents',
        action_on_trigger: 'killswitch',
      },
    ],
    budget_limit_cents: 5000,
    budget_period: 'daily',
    kill_switch_enabled: true,
    kill_switch_auto_trigger: true,
    auto_trigger_threshold_cents: 5000,
    notification_email: 'alerts@company.com',
    notification_slack_webhook: 'https://hooks.slack.com/...',
  };

  const tabs = [
    { id: 'guardrails', label: 'Guardrails', icon: '🔒' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
    { id: 'keys', label: 'API Keys', icon: '🔑' },
    { id: 'export', label: 'Export', icon: '📤' },
  ] as const;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <span>⚙️</span> Settings
        </h1>
        <p className="text-slate-400 mt-1">
          Configure guardrails, notifications, and export options
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-slate-700 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              px-4 py-2 rounded-t-lg font-medium transition-colors
              ${activeTab === tab.id
                ? 'bg-blue-600/20 text-blue-400 border-b-2 border-blue-500'
                : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
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
        <GuardrailsTab guardrails={safeSettings.guardrails} />
      )}
      {activeTab === 'notifications' && (
        <NotificationsTab settings={safeSettings} />
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

// Guardrails Tab
function GuardrailsTab({ guardrails }: { guardrails: GuardrailConfig[] }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold">Active Guardrails</h2>
          <p className="text-sm text-slate-400">Configure protection rules for your AI traffic</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium">
          + Add Guardrail
        </button>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        {guardrails.map((guardrail, index) => (
          <div
            key={guardrail.id}
            className={`p-4 ${index > 0 ? 'border-t border-slate-700' : ''}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={guardrail.enabled}
                    onChange={() => {}}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-green-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all" />
                </label>
                <div>
                  <h3 className="font-medium">{guardrail.name}</h3>
                  <p className="text-sm text-slate-400">{guardrail.description}</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className="text-lg font-bold text-blue-400">{guardrail.threshold_value}</span>
                  <span className="text-sm text-slate-400 ml-1">{guardrail.threshold_unit}</span>
                </div>
                <span className={`
                  px-2 py-1 rounded text-xs font-medium
                  ${guardrail.action_on_trigger === 'block' ? 'bg-red-500/20 text-red-400' : ''}
                  ${guardrail.action_on_trigger === 'throttle' ? 'bg-amber-500/20 text-amber-400' : ''}
                  ${guardrail.action_on_trigger === 'killswitch' ? 'bg-red-500/20 text-red-400' : ''}
                  ${guardrail.action_on_trigger === 'warn' ? 'bg-blue-500/20 text-blue-400' : ''}
                `}>
                  {guardrail.action_on_trigger}
                </span>
                <button className="text-slate-400 hover:text-white">
                  ⋮
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Help Box */}
      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mt-6">
        <h4 className="font-medium text-blue-400 flex items-center gap-2">
          <span>💡</span> Understanding Guardrails
        </h4>
        <p className="text-sm text-slate-300 mt-2">
          Guardrails protect your AI traffic by enforcing limits and policies. When triggered, they can:
        </p>
        <ul className="text-sm text-slate-300 mt-2 space-y-1 ml-4">
          <li>• <strong>Block</strong> - Stop the request immediately</li>
          <li>• <strong>Throttle</strong> - Slow down the request rate</li>
          <li>• <strong>Kill Switch</strong> - Stop all traffic until manually resumed</li>
          <li>• <strong>Warn</strong> - Log the event but allow the request</li>
        </ul>
      </div>
    </div>
  );
}

// Notifications Tab
function NotificationsTab({ settings }: { settings: TenantSettings }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold">Notification Settings</h2>
        <p className="text-sm text-slate-400">Configure how you receive alerts</p>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 space-y-6">
        {/* Email */}
        <div>
          <label className="block text-sm font-medium mb-2">Alert Email</label>
          <input
            type="email"
            value={settings.notification_email}
            onChange={() => {}}
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2"
          />
          <p className="text-xs text-slate-400 mt-1">Receive alerts when guardrails are triggered</p>
        </div>

        {/* Slack */}
        <div>
          <label className="block text-sm font-medium mb-2">Slack Webhook URL</label>
          <input
            type="url"
            value={settings.notification_slack_webhook || ''}
            onChange={() => {}}
            placeholder="https://hooks.slack.com/..."
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2"
          />
          <p className="text-xs text-slate-400 mt-1">Optional: Send alerts to a Slack channel</p>
        </div>

        {/* Alert Preferences */}
        <div>
          <label className="block text-sm font-medium mb-3">Alert Preferences</label>
          <div className="space-y-3">
            {[
              { label: 'Guardrail triggered', description: 'When any guardrail blocks or throttles', default: true },
              { label: 'Kill switch activated', description: 'When traffic is stopped', default: true },
              { label: 'Budget threshold (80%)', description: 'When approaching daily budget', default: true },
              { label: 'Weekly summary', description: 'Weekly digest of all activity', default: false },
            ].map((pref, i) => (
              <label key={i} className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  defaultChecked={pref.default}
                  className="mt-1"
                />
                <div>
                  <span className="font-medium">{pref.label}</span>
                  <span className="block text-xs text-slate-400">{pref.description}</span>
                </div>
              </label>
            ))}
          </div>
        </div>
      </div>

      <button className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium">
        Save Changes
      </button>
    </div>
  );
}

// API Keys Tab
function KeysTab() {
  const { data: keys } = useQuery({
    queryKey: ['guard', 'keys'],
    queryFn: guardApi.getApiKeys,
  });

  const demoKeys = keys?.items || [
    { id: 'key_1', name: 'Production', prefix: 'sk-prod-****', status: 'active', requests_today: 1234, spend_today_cents: 234 },
    { id: 'key_2', name: 'Development', prefix: 'sk-dev-****', status: 'active', requests_today: 56, spend_today_cents: 12 },
    { id: 'key_3', name: 'Testing', prefix: 'sk-test-****', status: 'frozen', requests_today: 0, spend_today_cents: 0 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">API Keys</h2>
          <p className="text-sm text-slate-400">Manage your API keys</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium">
          + Create Key
        </button>
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-700/50">
            <tr className="text-left text-sm text-slate-400">
              <th className="p-4">Name</th>
              <th className="p-4">Key</th>
              <th className="p-4">Status</th>
              <th className="p-4">Today</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {demoKeys.map((key: any) => (
              <tr key={key.id}>
                <td className="p-4 font-medium">{key.name}</td>
                <td className="p-4 font-mono text-sm text-slate-400">{key.prefix}</td>
                <td className="p-4">
                  <span className={`
                    px-2 py-1 rounded text-xs font-medium
                    ${key.status === 'active' ? 'bg-green-500/20 text-green-400' : ''}
                    ${key.status === 'frozen' ? 'bg-red-500/20 text-red-400' : ''}
                  `}>
                    {key.status}
                  </span>
                </td>
                <td className="p-4 text-sm">
                  {key.requests_today} req • ${(key.spend_today_cents / 100).toFixed(2)}
                </td>
                <td className="p-4">
                  <div className="flex gap-2">
                    <button className="text-xs text-blue-400 hover:text-blue-300">Copy</button>
                    <button className="text-xs text-amber-400 hover:text-amber-300">
                      {key.status === 'frozen' ? 'Unfreeze' : 'Freeze'}
                    </button>
                    <button className="text-xs text-red-400 hover:text-red-300">Revoke</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Export Tab
function ExportTab() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold">Data Export</h2>
        <p className="text-sm text-slate-400">Export your data for compliance or analysis</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {[
          {
            icon: '📊',
            title: 'Usage Report',
            description: 'Export all API usage data for the selected period',
            format: 'CSV',
          },
          {
            icon: '📋',
            title: 'Incidents Report',
            description: 'All incidents with decision timelines',
            format: 'PDF',
          },
          {
            icon: '🔐',
            title: 'Audit Log',
            description: 'Complete audit trail for compliance',
            format: 'JSON',
          },
          {
            icon: '📈',
            title: 'Analytics Export',
            description: 'Metrics and trends for analysis',
            format: 'CSV',
          },
        ].map((item, i) => (
          <div key={i} className="bg-slate-800 rounded-xl border border-slate-700 p-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">{item.icon}</span>
              <div>
                <h3 className="font-medium">{item.title}</h3>
                <span className="text-xs text-slate-400">{item.format}</span>
              </div>
            </div>
            <p className="text-sm text-slate-400 mb-4">{item.description}</p>
            <button className="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm">
              📥 Export
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default GuardSettingsPage;
