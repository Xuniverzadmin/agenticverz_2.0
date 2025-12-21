/**
 * Guard Console Layout - Unified Navigation & Shell
 *
 * Implements the 8-phase plan navigation:
 * - Overview (Control Plane)
 * - Live Activity (Phase 4)
 * - Incidents (Phase 2-3)
 * - Kill Switch (Phase 5)
 * - Logs (Phase 4)
 * - Settings
 *
 * Uses Navy-First Design System v1.0:
 * - Surfaces are neutral navy family
 * - Meaning conveyed via text, borders, icons (not colored backgrounds)
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { guardApi, GuardStatus, TodaySnapshot } from '../../api/guard';
import { HealthIndicator } from '../../components/HealthIndicator';
import { ErrorBoundary } from '../../components/ErrorBoundary';
import { healthMonitor } from '../../lib/healthCheck';
import { useAuthStore } from '../../stores/authStore';

// Navigation items matching target IA (with Account & Support)
const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: '🛡️', description: 'Control plane & status' },
  { id: 'live', label: 'Live Activity', icon: '📡', description: 'Real-time event stream' },
  { id: 'incidents', label: 'Incidents', icon: '📋', description: 'Search & investigate' },
  { id: 'killswitch', label: 'Kill Switch', icon: '🚨', description: 'Emergency controls' },
  { id: 'logs', label: 'Logs', icon: '📜', description: 'Event history' },
  { id: 'settings', label: 'Settings', icon: '⚙️', description: 'Configuration' },
  { id: 'account', label: 'Account', icon: '👤', description: 'Organization & team' },
  { id: 'support', label: 'Support', icon: '💬', description: 'Help & feedback' },
] as const;

type NavItemId = typeof NAV_ITEMS[number]['id'];
type ConsoleMode = 'live' | 'demo' | 'staging';
type ProtectionStatus = 'protected' | 'at_risk' | 'stopped';

const MODE_CONFIG: Record<ConsoleMode, { label: string; color: string; pulse: boolean }> = {
  live: { label: 'LIVE', color: 'text-green-400', pulse: true },
  demo: { label: 'DEMO', color: 'text-amber-400', pulse: false },
  staging: { label: 'STAGING', color: 'text-blue-400', pulse: false },
};

// Navy-First: minimal backgrounds, status via text/border only
const STATUS_CONFIG: Record<ProtectionStatus, { label: string; color: string; bg: string; border: string }> = {
  protected: { label: 'Protected', color: 'text-accent-success', bg: 'bg-navy-elevated', border: 'border-accent-success/30' },
  at_risk: { label: 'At Risk', color: 'text-accent-warning', bg: 'bg-navy-elevated', border: 'border-accent-warning/30' },
  stopped: { label: 'Stopped', color: 'text-accent-danger', bg: 'bg-navy-elevated', border: 'border-accent-danger/30' },
};

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface GuardLayoutProps {
  children: React.ReactNode;
  activeTab: NavItemId;
  onTabChange: (tab: NavItemId) => void;
  onLogout?: () => void;
  user?: User | null;
}

export function GuardLayout({ children, activeTab, onTabChange, onLogout, user }: GuardLayoutProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const tenantId = useAuthStore((state) => state.tenantId);

  // Initialize health monitoring only after authentication
  useEffect(() => {
    if (!isAuthenticated) return;

    // Small delay to ensure auth headers are ready
    const timer = setTimeout(() => {
      healthMonitor.startPeriodicCheck(30000, tenantId || 'demo-tenant');
    }, 500);

    return () => {
      clearTimeout(timer);
      healthMonitor.stopPeriodicCheck();
    };
  }, [isAuthenticated, tenantId]);

  // Fetch status for header display
  // staleTime prevents duplicate fetches when data is still fresh
  const { data: status } = useQuery({
    queryKey: ['guard', 'status'],
    queryFn: guardApi.getStatus,
    refetchInterval: 5000,
    staleTime: 4000, // Fresh for 4s (< 5s backend cache TTL)
  });

  const { data: snapshot } = useQuery({
    queryKey: ['guard', 'snapshot'],
    queryFn: guardApi.getTodaySnapshot,
    refetchInterval: 30000,
    staleTime: 10000, // Fresh for 10s (matches backend cache)
  });

  // Derive protection status
  const protectionStatus: ProtectionStatus = status?.is_frozen
    ? 'stopped'
    : (snapshot?.incidents_prevented ?? 0) > 0
      ? 'at_risk'
      : 'protected';

  const statusConfig = STATUS_CONFIG[protectionStatus];
  const mode: ConsoleMode = (status as any)?.mode || 'demo';
  const modeConfig = MODE_CONFIG[mode];

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-navy-app text-slate-100 flex">
        {/* ============== SIDEBAR ============== */}
        <aside className="w-64 bg-navy-surface border-r border-navy-border flex flex-col">
          {/* Logo */}
          <div className="p-4 border-b border-navy-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-accent-info to-accent-primary rounded-lg flex items-center justify-center">
                <span className="text-xl">🛡️</span>
              </div>
              <div>
                <h1 className="font-bold text-lg">AI Guard</h1>
                <p className="text-xs text-slate-400">Customer Console</p>
              </div>
            </div>
          </div>

          {/* Status Summary */}
          <div className="p-4 border-b border-navy-border">
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${statusConfig.bg} ${statusConfig.border} border`}>
              <span className={`w-2 h-2 rounded-full bg-current ${statusConfig.color} animate-pulse`} />
              <span className={`font-medium ${statusConfig.color}`}>{statusConfig.label}</span>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div className="bg-navy-subtle rounded p-2">
                <span className="text-slate-400">Today</span>
                <span className="block font-bold">{snapshot?.requests_today?.toLocaleString() ?? '0'}</span>
              </div>
              <div className="bg-navy-subtle rounded p-2">
                <span className="text-slate-400">Blocked</span>
                <span className="block font-bold text-accent-success">{snapshot?.incidents_prevented ?? 0}</span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-2 space-y-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors
                  ${activeTab === item.id
                    ? 'bg-navy-elevated text-accent-info border border-accent-info/30'
                    : 'hover:bg-navy-elevated text-slate-300'
                  }
                `}
              >
                <span className="text-lg">{item.icon}</span>
                <div>
                  <span className="font-medium">{item.label}</span>
                  {activeTab === item.id && (
                    <span className="block text-xs text-slate-400">{item.description}</span>
                  )}
                </div>
              </button>
            ))}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-navy-border">
            <HealthIndicator showDetails={true} position="inline" />
          </div>
        </aside>

        {/* ============== MAIN CONTENT ============== */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="h-14 bg-navy-surface border-b border-navy-border px-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h2 className="text-lg font-semibold">
                {NAV_ITEMS.find(i => i.id === activeTab)?.label}
              </h2>
            </div>

            <div className="flex items-center gap-4">
              {/* Mode Badge */}
              <div className={`flex items-center gap-2 px-3 py-1 rounded-full border border-current/30 ${modeConfig.color}`}>
                {modeConfig.pulse && (
                  <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
                )}
                <span className="text-sm font-medium">{modeConfig.label}</span>
              </div>

              {/* Quick Actions - text-only buttons with accent borders */}
              {status?.is_frozen ? (
                <button className="px-3 py-1.5 border border-accent-success/50 text-accent-success hover:bg-navy-elevated rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
                  <span>▶</span> Resume
                </button>
              ) : (
                <button className="px-3 py-1.5 border border-accent-danger/50 text-accent-danger hover:bg-navy-elevated rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
                  <span>⏹</span> Stop
                </button>
              )}

              {onLogout && (
                <button
                  onClick={onLogout}
                  className="px-3 py-1.5 text-slate-400 hover:text-white hover:bg-navy-elevated rounded-lg text-sm transition-colors"
                >
                  Logout
                </button>
              )}
            </div>
          </header>

          {/* Content */}
          <main className="flex-1 overflow-auto bg-navy-app">
            {children}
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default GuardLayout;
export type { NavItemId };
