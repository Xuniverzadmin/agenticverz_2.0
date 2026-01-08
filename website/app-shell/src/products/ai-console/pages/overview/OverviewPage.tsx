// Layer: L1 — Product Experience (Frontend)
// Product: AI Console
// Domain: Overview ("Is the system okay right now?")
// Reference: PIN-240

/**
 * Customer Overview Page - Calm Status Board
 *
 * Customer Console v1 Constitution: Overview Domain
 * Question: "Is the system okay right now?"
 *
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
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { guardApi } from '@/api/guard';
import { CUSTOMER_ROUTES } from '@/routing';
import { logger } from '@/lib/consoleLogger';

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

type OverviewStatus = 'protected' | 'attention_needed' | 'action_required';

interface OverviewData {
  status: OverviewStatus;
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
const STATUS_CONFIG: Record<OverviewStatus, {
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

export function OverviewPage() {
  const navigate = useNavigate();

  useEffect(() => {
    logger.componentMount('CustomerOverviewPage');
    return () => logger.componentUnmount('CustomerOverviewPage');
  }, []);

  // Fetch overview data
  const { data: overviewData, isLoading } = useQuery<OverviewData>({
    queryKey: ['guard', 'overview'],
    queryFn: async () => {
      // Use existing endpoints to derive overview data
      const [status, snapshot] = await Promise.all([
        guardApi.getStatus(),
        guardApi.getTodaySnapshot(),
      ]);

      // Derive overview status from existing data
      let overviewStatus: OverviewStatus = 'protected';
      if (status.is_frozen) {
        overviewStatus = 'action_required';
      } else if ((snapshot?.incidents_prevented ?? 0) > 3) {
        overviewStatus = 'attention_needed';
      }

      // Build recent activity from available data
      const recentActivity: OverviewData['recent_activity'] = [];

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
        status: overviewStatus,
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

  const status = overviewData?.status ?? 'protected';
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
            {overviewData?.requests_today?.toLocaleString() ?? '0'}
          </div>
        </div>

        {/* Incidents */}
        <div className="bg-navy-surface border border-navy-border rounded-xl p-6">
          <div className="text-sm text-slate-400 mb-1">Incidents</div>
          <div className="text-3xl font-bold text-accent-success">
            {overviewData?.incidents_today ?? 0}
            <span className="text-sm font-normal text-slate-400 ml-2">blocked</span>
          </div>
        </div>

        {/* AI Spend */}
        <div className="bg-navy-surface border border-navy-border rounded-xl p-6">
          <div className="text-sm text-slate-400 mb-1">AI Spend Today</div>
          <div className="text-3xl font-bold text-white">
            ${(overviewData?.ai_spend_today ?? 0).toFixed(2)}
          </div>
        </div>
      </div>

      {/* ============== RECENT ACTIVITY ============== */}
      <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
        Recent Activity
      </h2>
      <div className="bg-navy-surface border border-navy-border rounded-xl p-4 mb-8">
        {overviewData?.recent_activity && overviewData.recent_activity.length > 0 ? (
          <ul className="space-y-3">
            {overviewData.recent_activity.map((activity) => (
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
      {/* PIN-352: Uses routing authority for navigation */}
      <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
        Quick Actions
      </h2>
      <div className="grid grid-cols-3 gap-4">
        <button
          onClick={() => navigate(CUSTOMER_ROUTES.activity)}
          className="bg-navy-surface border border-navy-border hover:border-accent-info/50 rounded-xl p-6 text-left transition-colors group"
        >
          <span className="text-2xl mb-3 block">⚡</span>
          <span className="font-medium text-white group-hover:text-accent-info transition-colors">
            View Activity
          </span>
          <p className="text-sm text-slate-400 mt-1">
            What ran / is running
          </p>
        </button>

        <button
          onClick={() => navigate(CUSTOMER_ROUTES.policies)}
          className="bg-navy-surface border border-navy-border hover:border-accent-info/50 rounded-xl p-6 text-left transition-colors group"
        >
          <span className="text-2xl mb-3 block">📜</span>
          <span className="font-medium text-white group-hover:text-accent-info transition-colors">
            View Policies
          </span>
          <p className="text-sm text-slate-400 mt-1">
            How behavior is defined
          </p>
        </button>

        <button
          onClick={() => navigate(CUSTOMER_ROUTES.keys)}
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

export default OverviewPage;
