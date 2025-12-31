/**
 * AI Console Settings Page - Navy-First Design
 *
 * CRITICAL UX FIX:
 * - Toggles REMOVED - they were fake controls that lied to users
 * - Replaced with honest read-only status indicators
 * - Demo mode banner clearly explains locked state
 *
 * In a safety console, fake controls = loss of trust.
 * If a control doesn't work, don't render it as interactive.
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { guardApi, TenantSettings, GuardrailConfig } from '@/api/guard';
import { logger } from '@/lib/consoleLogger';

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'guardrails' | 'notifications' | 'keys' | 'export'>('guardrails');

  useEffect(() => {
    logger.componentMount('AIConsoleSettingsPage');
    return () => logger.componentUnmount('AIConsoleSettingsPage');
  }, []);

  // Fetch settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ['guard', 'settings'],
    queryFn: guardApi.getSettings,
  });

  // Demo settings if API fails
  const safeSettings: TenantSettings = settings || {
    tenant_id: 'demo-tenant',
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
      {/* Demo Mode Banner - Critical UX element */}
      <div className="bg-navy-elevated border border-amber-500/30 rounded-lg px-4 py-3 mb-6 flex items-center gap-3">
        <span className="text-amber-400">🔒</span>
        <div>
          <span className="text-amber-400 font-medium">Demo Mode</span>
          <span className="text-slate-400 ml-2">
            Settings are read-only. Changes available in production.
          </span>
        </div>
      </div>

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>⚙️</span> Settings
        </h1>
        <p className="text-slate-400 mt-1">
          View guardrails, notifications, and export options
        </p>
      </div>

      {/* Tab Navigation - Navy-First */}
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

// ============================================================================
// Guardrails Tab - READ-ONLY STATUS INDICATORS (no fake toggles)
// ============================================================================

function GuardrailsTab({ guardrails }: { guardrails: GuardrailConfig[] }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-white">Active Guardrails</h2>
          <p className="text-sm text-slate-400">Protection rules for your AI traffic</p>
        </div>
        <button
          disabled
          className="px-4 py-2 bg-navy-elevated border border-navy-border text-slate-500 rounded-lg text-sm font-medium cursor-not-allowed opacity-60"
        >
          + Add Guardrail
        </button>
      </div>

      <div className="bg-navy-surface rounded-xl border border-navy-border overflow-hidden">
        {guardrails.map((guardrail, index) => (
          <div
            key={guardrail.id}
            className={`p-4 ${index > 0 ? 'border-t border-navy-border' : ''}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* STATUS INDICATOR - Not a toggle! */}
                <GuardrailStatusIndicator enabled={guardrail.enabled} />

                <div>
                  <h3 className="font-medium text-white">{guardrail.name}</h3>
                  <p className="text-sm text-slate-400">{guardrail.description}</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                {/* Threshold */}
                <div className="text-right">
                  <span className="text-lg font-bold text-accent-info">{guardrail.threshold_value}</span>
                  <span className="text-sm text-slate-400 ml-1">{guardrail.threshold_unit}</span>
                </div>

                {/* Action badge - outline only */}
                <ActionBadge action={guardrail.action_on_trigger} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Understanding box */}
      <div className="bg-navy-elevated border border-accent-info/20 rounded-lg p-4 mt-6">
        <h4 className="font-medium text-accent-info flex items-center gap-2">
          <span>💡</span> Understanding Guardrails
        </h4>
        <p className="text-sm text-slate-300 mt-2">
          Guardrails protect your AI traffic by enforcing limits. Actions:
        </p>
        <ul className="text-sm text-slate-300 mt-2 space-y-1 ml-4">
          <li>• <span className="text-red-400">Block</span> — Stop request immediately</li>
          <li>• <span className="text-amber-400">Throttle</span> — Slow down request rate</li>
          <li>• <span className="text-red-400">Kill Switch</span> — Stop all traffic</li>
          <li>• <span className="text-blue-400">Warn</span> — Log but allow</li>
        </ul>
      </div>
    </div>
  );
}

/**
 * GuardrailStatusIndicator - READ-ONLY status display
 *
 * NOT a toggle. This is intentional.
 * A toggle that doesn't toggle is a UX lie.
 */
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

/**
 * ActionBadge - Shows action type with outline style
 */
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
        {/* Email */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Alert Email</label>
          <div className="w-full bg-navy-inset border border-navy-border rounded-lg px-4 py-2 text-slate-400">
            {settings.notification_email}
          </div>
          <p className="text-xs text-slate-500 mt-1">Receives alerts when guardrails trigger</p>
        </div>

        {/* Slack */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Slack Webhook</label>
          <div className="w-full bg-navy-inset border border-navy-border rounded-lg px-4 py-2 text-slate-400 font-mono text-sm">
            {settings.notification_slack_webhook ? '••••••••••••••••' : 'Not configured'}
          </div>
        </div>

        {/* Alert Preferences - Read-only checkmarks */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-3">Alert Preferences</label>
          <div className="space-y-3">
            {[
              { label: 'Guardrail triggered', enabled: true },
              { label: 'Kill switch activated', enabled: true },
              { label: 'Budget threshold (80%)', enabled: true },
              { label: 'Weekly summary', enabled: false },
            ].map((pref, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className={pref.enabled ? 'text-green-400' : 'text-slate-600'}>
                  {pref.enabled ? '✓' : '○'}
                </span>
                <span className={pref.enabled ? 'text-slate-300' : 'text-slate-500'}>
                  {pref.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// API Keys Tab
// ============================================================================

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
          <h2 className="text-lg font-bold text-white">API Keys</h2>
          <p className="text-sm text-slate-400">View your API keys</p>
        </div>
        <button
          disabled
          className="px-4 py-2 bg-navy-elevated border border-navy-border text-slate-500 rounded-lg text-sm font-medium cursor-not-allowed opacity-60"
        >
          + Create Key
        </button>
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
            {demoKeys.map((key: any) => (
              <tr key={key.id}>
                <td className="p-4 font-medium text-white">{key.name}</td>
                <td className="p-4 font-mono text-sm text-slate-400">{key.prefix}</td>
                <td className="p-4">
                  <span className={`
                    px-2 py-1 rounded border text-xs font-medium bg-transparent
                    ${key.status === 'active'
                      ? 'text-green-400 border-green-400/40'
                      : 'text-red-400 border-red-400/40'
                    }
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

      <div className="grid grid-cols-2 gap-4">
        {[
          { icon: '📊', title: 'Usage Report', description: 'API usage data for selected period', format: 'CSV' },
          { icon: '📋', title: 'Incidents Report', description: 'Incidents with decision timelines', format: 'PDF' },
          { icon: '🔐', title: 'Audit Log', description: 'Complete audit trail for compliance', format: 'JSON' },
          { icon: '📈', title: 'Analytics Export', description: 'Metrics and trends for analysis', format: 'CSV' },
        ].map((item, i) => (
          <div key={i} className="bg-navy-surface rounded-xl border border-navy-border p-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">{item.icon}</span>
              <div>
                <h3 className="font-medium text-white">{item.title}</h3>
                <span className="text-xs text-slate-500">{item.format}</span>
              </div>
            </div>
            <p className="text-sm text-slate-400 mb-4">{item.description}</p>
            <button className="w-full px-4 py-2 bg-navy-elevated hover:bg-navy-subtle border border-navy-border text-slate-300 rounded-lg text-sm transition-colors">
              📥 Export
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SettingsPage;
