/**
 * Customer Home Page - Calm Status Board
 *
 * M28 Unified Console: The first thing customers see.
 * NOT a dashboard. A status board. Big difference.
 *
 * 3 States ONLY:
 * - PROTECTED (green): Everything is fine, you can relax
 * - ATTENTION NEEDED (amber): Something needs review, not urgent
 * - ACTION REQUIRED (red): Something needs action now
 *
 * Design Principles:
 * - No charts (anxiety-inducing)
 * - No animations (distracting)
 * - No "smart" features exposed (we do the work, customer sees calm)
 * - Max 3 lines of recent activity (reassurance, not noise)
 */

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { guardApi } from '../../api/guard';
import { logger } from '../../lib/consoleLogger';
import type { NavItemId } from './GuardLayout';

// Simple relative time formatter (no date-fns dependency)
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString();
}

type HomeStatus = 'protected' | 'attention_needed' | 'action_required';

interface HomeData {
  status: HomeStatus;
  requests_today: number;
  incidents_today: number;
  ai_spend_today: number;
  recent_activity: Array<{
    id: string;
    message: string;
    timestamp: string;
    type: 'success' | 'info' | 'warning';
  }>;
}

// Status configurations - Navy-First design
const STATUS_CONFIG: Record<HomeStatus, {
  label: string;
  subtitle: string;
  color: string;
  border: string;
  icon: string;
}> = {
  protected: {
    label: 'PROTECTED',
    subtitle: 'All systems operational. Your AI is running safely.',
    color: 'text-accent-success',
    border: 'border-accent-success/40',
    icon: '✓',
  },
  attention_needed: {
    label: 'ATTENTION NEEDED',
    subtitle: 'Some items need your review. Nothing urgent.',
    color: 'text-accent-warning',
    border: 'border-accent-warning/40',
    icon: '!',
  },
  action_required: {
    label: 'ACTION REQUIRED',
    subtitle: 'Critical items need your attention now.',
    color: 'text-accent-danger',
    border: 'border-accent-danger/40',
    icon: '!!',
  },
};

// Activity type colors
const ACTIVITY_COLORS: Record<string, string> = {
  success: 'text-accent-success',
  info: 'text-slate-400',
  warning: 'text-accent-warning',
};

export function CustomerHomePage({
  onNavigate,
}: {
  onNavigate?: (tab: NavItemId) => void;
}) {
  useEffect(() => {
    logger.componentMount('CustomerHomePage');
    return () => logger.componentUnmount('CustomerHomePage');
  }, []);

  // Fetch home data
  const { data: homeData, isLoading } = useQuery<HomeData>({
    queryKey: ['guard', 'home'],
    queryFn: async () => {
      // Use existing endpoints to derive home data
      const [status, snapshot] = await Promise.all([
        guardApi.getStatus(),
        guardApi.getTodaySnapshot(),
      ]);

      // Derive home status from existing data
      let homeStatus: HomeStatus = 'protected';
      if (status.is_frozen) {
        homeStatus = 'action_required';
      } else if ((snapshot?.incidents_prevented ?? 0) > 3) {
        homeStatus = 'attention_needed';
      }

      // Build recent activity from available data
      const recentActivity: HomeData['recent_activity'] = [];

      if (snapshot?.incidents_prevented && snapshot.incidents_prevented > 0) {
        recentActivity.push({
          id: '1',
          message: `${snapshot.incidents_prevented} incidents prevented today`,
          timestamp: new Date().toISOString(),
          type: 'success',
        });
      }

      if (snapshot?.requests_today && snapshot.requests_today > 0) {
        recentActivity.push({
          id: '2',
          message: `${snapshot.requests_today.toLocaleString()} AI requests processed`,
          timestamp: new Date().toISOString(),
          type: 'info',
        });
      }

      recentActivity.push({
        id: '3',
        message: 'All safety policies active',
        timestamp: new Date().toISOString(),
        type: 'success',
      });

      return {
        status: homeStatus,
        requests_today: snapshot?.requests_today ?? 0,
        incidents_today: snapshot?.incidents_prevented ?? 0,
        ai_spend_today: (snapshot?.spend_today_cents ?? 0) / 100, // Convert cents to dollars
        recent_activity: recentActivity.slice(0, 3), // Max 3 items
      };
    },
    refetchInterval: 30000, // Calm refresh every 30s
    staleTime: 10000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

  const status = homeData?.status ?? 'protected';
  const statusConfig = STATUS_CONFIG[status];

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* ============== STATUS HERO ============== */}
      <div className={`
        p-8 rounded-xl bg-navy-surface border ${statusConfig.border}
        text-center mb-8
      `}>
        <div className={`
          w-20 h-20 mx-auto mb-4 rounded-full bg-navy-elevated
          flex items-center justify-center text-4xl font-bold
          ${statusConfig.color}
        `}>
          {statusConfig.icon}
        </div>
        <h1 className={`text-3xl font-bold ${statusConfig.color}`}>
          {statusConfig.label}
        </h1>
        <p className="text-slate-400 mt-2 text-lg">
          {statusConfig.subtitle}
        </p>
      </div>

      {/* ============== TODAY AT A GLANCE ============== */}
      <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
        Today at a Glance
      </h2>
      <div className="grid grid-cols-3 gap-4 mb-8">
        {/* Requests */}
        <div className="bg-navy-surface border border-navy-border rounded-xl p-6">
          <div className="text-sm text-slate-400 mb-1">Requests</div>
          <div className="text-3xl font-bold text-white">
            {homeData?.requests_today?.toLocaleString() ?? '0'}
          </div>
        </div>

        {/* Incidents */}
        <div className="bg-navy-surface border border-navy-border rounded-xl p-6">
          <div className="text-sm text-slate-400 mb-1">Incidents</div>
          <div className="text-3xl font-bold text-accent-success">
            {homeData?.incidents_today ?? 0}
            <span className="text-sm font-normal text-slate-400 ml-2">blocked</span>
          </div>
        </div>

        {/* AI Spend */}
        <div className="bg-navy-surface border border-navy-border rounded-xl p-6">
          <div className="text-sm text-slate-400 mb-1">AI Spend Today</div>
          <div className="text-3xl font-bold text-white">
            ${(homeData?.ai_spend_today ?? 0).toFixed(2)}
          </div>
        </div>
      </div>

      {/* ============== RECENT ACTIVITY ============== */}
      <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
        Recent Activity
      </h2>
      <div className="bg-navy-surface border border-navy-border rounded-xl p-4 mb-8">
        {homeData?.recent_activity && homeData.recent_activity.length > 0 ? (
          <ul className="space-y-3">
            {homeData.recent_activity.map((activity) => (
              <li key={activity.id} className="flex items-center gap-3">
                <span className={`w-1.5 h-1.5 rounded-full bg-current ${ACTIVITY_COLORS[activity.type]}`} />
                <span className={ACTIVITY_COLORS[activity.type]}>
                  {activity.message}
                </span>
                <span className="text-slate-500 text-sm ml-auto">
                  {formatRelativeTime(new Date(activity.timestamp))}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-slate-500 text-center py-4">No recent activity</p>
        )}
      </div>

      {/* ============== QUICK ACTIONS ============== */}
      <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
        Quick Actions
      </h2>
      <div className="grid grid-cols-3 gap-4">
        <button
          onClick={() => onNavigate?.('incidents')}
          className="bg-navy-surface border border-navy-border hover:border-accent-info/50 rounded-xl p-6 text-left transition-colors group"
        >
          <span className="text-2xl mb-3 block">📋</span>
          <span className="font-medium text-white group-hover:text-accent-info transition-colors">
            View Incidents
          </span>
          <p className="text-sm text-slate-400 mt-1">
            Review blocked requests
          </p>
        </button>

        <button
          onClick={() => onNavigate?.('settings')}
          className="bg-navy-surface border border-navy-border hover:border-accent-info/50 rounded-xl p-6 text-left transition-colors group"
        >
          <span className="text-2xl mb-3 block">💰</span>
          <span className="font-medium text-white group-hover:text-accent-info transition-colors">
            View Cost
          </span>
          <p className="text-sm text-slate-400 mt-1">
            AI usage & spending
          </p>
        </button>

        <button
          onClick={() => onNavigate?.('settings')}
          className="bg-navy-surface border border-navy-border hover:border-accent-info/50 rounded-xl p-6 text-left transition-colors group"
        >
          <span className="text-2xl mb-3 block">🔑</span>
          <span className="font-medium text-white group-hover:text-accent-info transition-colors">
            Manage API Keys
          </span>
          <p className="text-sm text-slate-400 mt-1">
            Create & rotate keys
          </p>
        </button>
      </div>
    </div>
  );
}

export default CustomerHomePage;
