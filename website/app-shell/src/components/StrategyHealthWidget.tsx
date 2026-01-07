/**
 * Strategy Health Widget
 * M16: Surface strategy bounds status in Guard Console
 *
 * Shows at-a-glance whether agents are operating within strategy bounds.
 * Clicking navigates to full SBA Inspector.
 */

import { useQuery } from '@tanstack/react-query';
import { guardApi, StrategyHealth } from '@/api/guard';
import { Shield, AlertTriangle, XCircle, Target } from 'lucide-react';

// Status configuration - maps status to visual treatment
const STATUS_CONFIG: Record<
  StrategyHealth['status'],
  {
    label: string;
    description: string;
    icon: typeof Shield;
    colorClass: string;
    borderClass: string;
  }
> = {
  healthy: {
    label: 'Within Bounds',
    description: 'All agents operating within strategy',
    icon: Shield,
    colorClass: 'text-accent-success',
    borderClass: 'border-accent-success/40',
  },
  approaching: {
    label: 'Approaching Bounds',
    description: 'Some agents need attention',
    icon: AlertTriangle,
    colorClass: 'text-accent-warning',
    borderClass: 'border-accent-warning/40',
  },
  exceeded: {
    label: 'Strategy Exceeded',
    description: 'Agents operating outside bounds',
    icon: XCircle,
    colorClass: 'text-accent-danger',
    borderClass: 'border-accent-danger/40',
  },
  no_agents: {
    label: 'No Agents',
    description: 'No strategy-bound agents configured',
    icon: Target,
    colorClass: 'text-slate-400',
    borderClass: 'border-slate-600',
  },
  unknown: {
    label: 'Unknown',
    description: 'Strategy status unavailable',
    icon: Target,
    colorClass: 'text-slate-400',
    borderClass: 'border-slate-600',
  },
  error: {
    label: 'Error',
    description: 'Could not check strategy health',
    icon: XCircle,
    colorClass: 'text-slate-400',
    borderClass: 'border-slate-600',
  },
};

export function StrategyHealthWidget() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['guard', 'strategy-health'],
    queryFn: guardApi.getStrategyHealth,
    refetchInterval: 30000, // Refresh every 30s
    staleTime: 15000,
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-navy-surface rounded-xl border border-navy-border p-4 animate-pulse">
        <div className="h-6 bg-navy-elevated rounded w-32 mb-2" />
        <div className="h-4 bg-navy-elevated rounded w-48" />
      </div>
    );
  }

  // Default to unknown if no data
  const status = health?.status || 'unknown';
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  // Navigate to SBA Inspector on click
  const handleClick = () => {
    window.location.href = '/sba';
  };

  return (
    <section
      onClick={handleClick}
      className={`
        bg-navy-surface rounded-xl border-2 ${config.borderClass} p-4
        cursor-pointer hover:bg-navy-elevated transition-colors
      `}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
    >
      <div className="flex items-center justify-between">
        {/* Left: Status info */}
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-full bg-navy-elevated ${config.colorClass}`}>
            <Icon size={20} />
          </div>
          <div>
            <h3 className={`font-semibold ${config.colorClass}`}>
              {config.label}
            </h3>
            <p className="text-sm text-slate-400">
              {config.description}
            </p>
          </div>
        </div>

        {/* Right: Counts (only show if we have agents) */}
        {health && health.total_agents > 0 && (
          <div className="flex items-center gap-4 text-sm">
            <div className="text-center">
              <div className="text-lg font-bold text-accent-success">
                {health.healthy_count}
              </div>
              <div className="text-xs text-slate-400">Healthy</div>
            </div>
            {health.approaching_bounds_count > 0 && (
              <div className="text-center">
                <div className="text-lg font-bold text-accent-warning">
                  {health.approaching_bounds_count}
                </div>
                <div className="text-xs text-slate-400">Approaching</div>
              </div>
            )}
            {health.exceeded_count > 0 && (
              <div className="text-center">
                <div className="text-lg font-bold text-accent-danger">
                  {health.exceeded_count}
                </div>
                <div className="text-xs text-slate-400">Exceeded</div>
              </div>
            )}
            <div className="text-slate-500">→</div>
          </div>
        )}

        {/* Arrow if no agents */}
        {(!health || health.total_agents === 0) && (
          <div className="text-slate-500">→</div>
        )}
      </div>
    </section>
  );
}

export default StrategyHealthWidget;
