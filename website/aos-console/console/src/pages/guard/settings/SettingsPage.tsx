/**
 * Settings Page - Customer Console (Read-Only)
 *
 * Shows what's configured, but no knobs to turn.
 *
 * Displays:
 * - Active guardrails (view only)
 * - Default thresholds
 * - Kill switch semantics (plain English)
 *
 * Why read-only?
 * - Changes require understanding
 * - Wrong changes can be catastrophic
 * - Contact support to modify
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../../../components/common/Card';
import { Badge } from '../../../components/common/Badge';
import { Spinner } from '../../../components/common/Spinner';
import { guardApi } from '../../../api/guard';

interface GuardrailConfig {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  threshold_type: 'cost' | 'rate' | 'count' | 'pattern';
  threshold_value: number;
  threshold_unit: string;
  action_on_trigger: string;
}

interface TenantSettings {
  tenant_id: string;
  tenant_name: string;
  plan: 'starter' | 'pro' | 'enterprise';
  guardrails: GuardrailConfig[];
  budget_limit_cents: number;
  budget_period: 'daily' | 'weekly' | 'monthly';
  kill_switch_enabled: boolean;
  kill_switch_auto_trigger: boolean;
  auto_trigger_threshold_cents: number;
  notification_email: string;
  notification_slack_webhook: string | null;
}

const PLAN_CONFIG = {
  starter: { label: 'Starter', color: 'gray' },
  pro: { label: 'Pro', color: 'blue' },
  enterprise: { label: 'Enterprise', color: 'purple' },
};

export function SettingsPage() {
  const { data: settings, isLoading } = useQuery({
    queryKey: ['guard', 'settings'],
    queryFn: guardApi.getSettings,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!settings) {
    return (
      <Card className="m-6 text-center py-12">
        <div className="text-gray-400 text-5xl mb-4">⚙️</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Settings Unavailable</h3>
        <p className="text-gray-500">Unable to load your settings. Please try again.</p>
      </Card>
    );
  }

  const plan = PLAN_CONFIG[settings.plan];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Guard Settings</h1>
          <p className="text-gray-600 mt-1">
            Your protection configuration. Contact support to make changes.
          </p>
        </div>
        <Badge
          variant={settings.plan === 'enterprise' ? 'default' : 'primary'}
          className={`${
            settings.plan === 'enterprise' ? 'bg-purple-100 text-purple-800' :
            settings.plan === 'pro' ? 'bg-blue-100 text-blue-800' :
            'bg-gray-100 text-gray-800'
          }`}
        >
          {plan.label} Plan
        </Badge>
      </div>

      <div className="space-y-6">
        {/* Budget Settings */}
        <Card>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Budget Protection</h2>
          <div className="grid grid-cols-2 gap-6">
            <SettingItem
              label="Budget Limit"
              value={`$${(settings.budget_limit_cents / 100).toLocaleString()}`}
              detail={`Per ${settings.budget_period}`}
            />
            <SettingItem
              label="Current Period"
              value={settings.budget_period.charAt(0).toUpperCase() + settings.budget_period.slice(1)}
              detail="Billing cycle"
            />
          </div>
        </Card>

        {/* Kill Switch Settings */}
        <Card>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Kill Switch</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-6">
              <SettingItem
                label="Manual Kill Switch"
                value={settings.kill_switch_enabled ? 'Available' : 'Disabled'}
                detail="You can stop all traffic instantly"
              />
              <SettingItem
                label="Auto-Trigger"
                value={settings.kill_switch_auto_trigger ? 'Enabled' : 'Disabled'}
                detail={settings.kill_switch_auto_trigger
                  ? `Triggers at $${(settings.auto_trigger_threshold_cents / 100).toLocaleString()}`
                  : 'Manual only'
                }
              />
            </div>

            {/* Plain English Explanation */}
            <div className="bg-gray-50 rounded-lg p-4 mt-4">
              <h4 className="font-medium text-gray-900 mb-2">What happens when kill switch activates?</h4>
              <ul className="space-y-2 text-sm text-gray-700">
                <li className="flex items-start gap-2">
                  <span className="text-red-500">•</span>
                  All API requests are immediately blocked
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-500">•</span>
                  Active requests are terminated mid-flight
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-500">•</span>
                  No new charges will be incurred
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-500">•</span>
                  You can resume traffic at any time from the Overview page
                </li>
              </ul>
            </div>
          </div>
        </Card>

        {/* Active Guardrails */}
        <Card>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Active Guardrails</h2>
          <div className="space-y-3">
            {settings.guardrails.filter((g: GuardrailConfig) => g.enabled).map((guardrail: GuardrailConfig) => (
              <GuardrailItem key={guardrail.id} guardrail={guardrail} />
            ))}

            {settings.guardrails.filter((g: GuardrailConfig) => g.enabled).length === 0 && (
              <p className="text-gray-500 text-center py-4">
                No guardrails configured. Contact support to enable protection.
              </p>
            )}
          </div>
        </Card>

        {/* Disabled Guardrails */}
        {settings.guardrails.filter((g: GuardrailConfig) => !g.enabled).length > 0 && (
          <Card>
            <h2 className="text-lg font-medium text-gray-500 mb-4">Available Guardrails (Not Enabled)</h2>
            <div className="space-y-3 opacity-60">
              {settings.guardrails.filter((g: GuardrailConfig) => !g.enabled).map((guardrail: GuardrailConfig) => (
                <GuardrailItem key={guardrail.id} guardrail={guardrail} />
              ))}
            </div>
          </Card>
        )}

        {/* Notifications */}
        <Card>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Notifications</h2>
          <div className="grid grid-cols-2 gap-6">
            <SettingItem
              label="Email Alerts"
              value={settings.notification_email || 'Not configured'}
              detail="Incident notifications"
            />
            <SettingItem
              label="Slack Alerts"
              value={settings.notification_slack_webhook ? 'Configured' : 'Not configured'}
              detail="Real-time alerts"
            />
          </div>
        </Card>

        {/* Contact Support */}
        <Card className="bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-blue-900">Need to change settings?</h3>
              <p className="text-blue-700 text-sm mt-1">
                Contact our support team to modify your protection configuration.
              </p>
            </div>
            <a
              href="mailto:support@agenticverz.com"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Contact Support
            </a>
          </div>
        </Card>
      </div>
    </div>
  );
}

// Setting Item Component
function SettingItem({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-lg font-medium text-gray-900">{value}</p>
      <p className="text-xs text-gray-400 mt-0.5">{detail}</p>
    </div>
  );
}

// Guardrail Item Component
function GuardrailItem({ guardrail }: { guardrail: GuardrailConfig }) {
  const thresholdDisplay = formatThreshold(guardrail);

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${guardrail.enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
          <h4 className="font-medium text-gray-900">{guardrail.name}</h4>
        </div>
        <p className="text-sm text-gray-500 mt-1">{guardrail.description}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-medium text-gray-700">{thresholdDisplay}</p>
        <p className="text-xs text-gray-400">{formatAction(guardrail.action_on_trigger)}</p>
      </div>
    </div>
  );
}

// Helper functions
function formatThreshold(guardrail: GuardrailConfig): string {
  switch (guardrail.threshold_type) {
    case 'cost':
      return `$${guardrail.threshold_value} ${guardrail.threshold_unit}`;
    case 'rate':
      return `${guardrail.threshold_value} req/${guardrail.threshold_unit}`;
    case 'count':
      return `${guardrail.threshold_value} ${guardrail.threshold_unit}`;
    case 'pattern':
      return 'Pattern match';
    default:
      return `${guardrail.threshold_value} ${guardrail.threshold_unit}`;
  }
}

function formatAction(action: string): string {
  const actionMap: Record<string, string> = {
    'block': 'Block request',
    'throttle': 'Rate limit',
    'freeze': 'Stop traffic',
    'warn': 'Log warning',
    'alert': 'Send alert',
  };

  return actionMap[action] || action;
}

export default SettingsPage;
