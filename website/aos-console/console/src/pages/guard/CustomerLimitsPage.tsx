/**
 * Customer Limits & Usage Page
 *
 * Phase 5E-4: Customer Essentials
 *
 * Shows:
 * - Budget: current spend vs limit
 * - Rate limits: current usage vs allowed
 * - Warnings: when approaching limits
 *
 * Does NOT show:
 * - Policy mechanics
 * - CARE internals
 * - Kill-switch controls
 */

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { logger } from '../../lib/consoleLogger';

interface UsageLimits {
  // Budget
  budget_limit_cents: number;
  budget_used_cents: number;
  budget_period: 'daily' | 'weekly' | 'monthly';
  budget_resets_at: string;

  // Rate limits
  rate_limit_per_minute: number;
  rate_current_per_minute: number;
  rate_limit_per_day: number;
  rate_current_per_day: number;

  // Cost per request
  max_cost_per_request_cents: number;
  avg_cost_per_request_cents: number;

  // Warnings
  warnings: Array<{
    id: string;
    type: 'budget' | 'rate' | 'cost';
    message: string;
    severity: 'info' | 'warning' | 'critical';
  }>;
}

const SEVERITY_CONFIG: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  info: { bg: 'bg-blue-500/10', border: 'border-blue-400/30', text: 'text-blue-400', icon: 'i' },
  warning: { bg: 'bg-amber-500/10', border: 'border-amber-400/30', text: 'text-amber-400', icon: '!' },
  critical: { bg: 'bg-red-500/10', border: 'border-red-400/30', text: 'text-red-400', icon: '!!' },
};

function formatTimeRemaining(isoString: string): string {
  const reset = new Date(isoString);
  const now = new Date();
  const diffMs = reset.getTime() - now.getTime();

  if (diffMs <= 0) return 'Now';

  const hours = Math.floor(diffMs / 3600000);
  const minutes = Math.floor((diffMs % 3600000) / 60000);

  if (hours > 24) {
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  }
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function ProgressBar({
  current,
  max,
  label,
  unit,
  warning = 80,
  critical = 95,
}: {
  current: number;
  max: number;
  label: string;
  unit: string;
  warning?: number;
  critical?: number;
}) {
  const percentage = max > 0 ? Math.min(100, (current / max) * 100) : 0;

  let barColor = 'bg-green-500';
  let textColor = 'text-green-400';

  if (percentage >= critical) {
    barColor = 'bg-red-500';
    textColor = 'text-red-400';
  } else if (percentage >= warning) {
    barColor = 'bg-amber-500';
    textColor = 'text-amber-400';
  }

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className={textColor}>
          {current.toLocaleString()} / {max.toLocaleString()} {unit}
        </span>
      </div>
      <div className="h-2 bg-navy-inset rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="text-xs text-slate-500 text-right">
        {percentage.toFixed(1)}% used
      </div>
    </div>
  );
}

export function CustomerLimitsPage() {
  useEffect(() => {
    logger.componentMount('CustomerLimitsPage');
    return () => logger.componentUnmount('CustomerLimitsPage');
  }, []);

  // Fetch usage limits
  const { data, isLoading } = useQuery<UsageLimits>({
    queryKey: ['customer', 'limits'],
    queryFn: async () => {
      // In production, this would call: GET /api/v1/customer/limits
      // For now, return demo data
      const now = new Date();
      const tomorrow = new Date(now);
      tomorrow.setHours(24, 0, 0, 0);

      return {
        budget_limit_cents: 5000, // $50/day
        budget_used_cents: 3750, // $37.50 used (75%)
        budget_period: 'daily',
        budget_resets_at: tomorrow.toISOString(),

        rate_limit_per_minute: 60,
        rate_current_per_minute: 12,
        rate_limit_per_day: 10000,
        rate_current_per_day: 4523,

        max_cost_per_request_cents: 50, // $0.50 max per request
        avg_cost_per_request_cents: 8, // $0.08 average

        warnings: [
          {
            id: 'w1',
            type: 'budget',
            message: 'Budget is at 75%. You will be notified at 80%.',
            severity: 'info',
          },
        ],
      };
    },
    refetchInterval: 30000,
    staleTime: 10000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading limits...</div>
      </div>
    );
  }

  const limits = data!;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <span>📊</span> Limits & Usage
        </h1>
        <p className="text-slate-400 mt-1">
          Monitor your budget, rate limits, and usage
        </p>
      </div>

      {/* Warnings */}
      {limits.warnings.length > 0 && (
        <div className="mb-6 space-y-2">
          {limits.warnings.map((warning) => {
            const config = SEVERITY_CONFIG[warning.severity];
            return (
              <div
                key={warning.id}
                className={`${config.bg} ${config.border} border rounded-lg px-4 py-3 flex items-center gap-3`}
              >
                <span className={`w-6 h-6 rounded-full ${config.bg} ${config.text} flex items-center justify-center text-sm font-bold`}>
                  {config.icon}
                </span>
                <span className={config.text}>{warning.message}</span>
              </div>
            );
          })}
        </div>
      )}

      <div className="grid grid-cols-2 gap-6">
        {/* Budget Card */}
        <div className="bg-navy-surface border border-navy-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>💰</span> Budget
            </h2>
            <div className="text-sm text-slate-400">
              Resets in {formatTimeRemaining(limits.budget_resets_at)}
            </div>
          </div>

          <div className="space-y-4">
            <div className="text-center mb-6">
              <div className="text-4xl font-bold text-white">
                ${(limits.budget_used_cents / 100).toFixed(2)}
              </div>
              <div className="text-slate-400 mt-1">
                of ${(limits.budget_limit_cents / 100).toFixed(2)} {limits.budget_period}
              </div>
            </div>

            <ProgressBar
              current={limits.budget_used_cents}
              max={limits.budget_limit_cents}
              label="Budget Used"
              unit="cents"
            />
          </div>

          <div className="mt-6 pt-4 border-t border-navy-border">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">Avg. cost per request</span>
              <span className="text-white">
                ${(limits.avg_cost_per_request_cents / 100).toFixed(3)}
              </span>
            </div>
            <div className="flex justify-between text-sm mt-2">
              <span className="text-slate-400">Max cost per request</span>
              <span className="text-white">
                ${(limits.max_cost_per_request_cents / 100).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Rate Limits Card */}
        <div className="bg-navy-surface border border-navy-border rounded-xl p-6">
          <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-6">
            <span>⚡</span> Rate Limits
          </h2>

          <div className="space-y-6">
            <ProgressBar
              current={limits.rate_current_per_minute}
              max={limits.rate_limit_per_minute}
              label="Requests / Minute"
              unit="req/min"
              warning={70}
              critical={90}
            />

            <ProgressBar
              current={limits.rate_current_per_day}
              max={limits.rate_limit_per_day}
              label="Requests / Day"
              unit="req"
            />
          </div>

          <div className="mt-6 pt-4 border-t border-navy-border bg-navy-elevated rounded-lg p-4">
            <h4 className="text-sm font-medium text-slate-300 mb-2">What happens when limits are reached?</h4>
            <ul className="text-sm text-slate-400 space-y-1">
              <li>• <span className="text-amber-400">Rate limit</span>: Requests are throttled</li>
              <li>• <span className="text-red-400">Budget limit</span>: Requests are blocked</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Usage Breakdown */}
      <div className="mt-6 bg-navy-surface border border-navy-border rounded-xl p-6">
        <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
          <span>📈</span> Usage Summary
        </h2>

        <div className="grid grid-cols-4 gap-4">
          <div className="bg-navy-elevated rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-white">
              {limits.rate_current_per_day.toLocaleString()}
            </div>
            <div className="text-sm text-slate-400 mt-1">Requests Today</div>
          </div>
          <div className="bg-navy-elevated rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-400">
              ${(limits.budget_used_cents / 100).toFixed(2)}
            </div>
            <div className="text-sm text-slate-400 mt-1">Spent Today</div>
          </div>
          <div className="bg-navy-elevated rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-white">
              ${(limits.avg_cost_per_request_cents / 100).toFixed(3)}
            </div>
            <div className="text-sm text-slate-400 mt-1">Avg per Request</div>
          </div>
          <div className="bg-navy-elevated rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-white">
              {Math.round(((limits.budget_limit_cents - limits.budget_used_cents) / limits.avg_cost_per_request_cents))}
            </div>
            <div className="text-sm text-slate-400 mt-1">Est. Remaining</div>
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="mt-6 bg-navy-elevated border border-accent-info/20 rounded-lg p-4">
        <h4 className="font-medium text-accent-info flex items-center gap-2">
          <span>💡</span> Need higher limits?
        </h4>
        <p className="text-sm text-slate-300 mt-2">
          Contact support to discuss increasing your budget or rate limits.
          Enterprise plans include custom limits and priority support.
        </p>
      </div>
    </div>
  );
}

export default CustomerLimitsPage;
