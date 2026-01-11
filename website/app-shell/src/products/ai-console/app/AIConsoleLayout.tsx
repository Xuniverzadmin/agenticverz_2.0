/**
 * AI Console Layout - Unified Navigation & Shell
 *
 * Customer Console v1 Constitution (v1.2.0):
 * - Core Lenses: Overview, Activity, Incidents, Policies, Logs (sidebar)
 * - Connectivity: Integrations, API Keys (sidebar)
 * - Account: Settings, Account (secondary nav - header dropdown)
 *
 * Phase 3: Account Separation
 * - Primary nav (sidebar): Core operational domains
 * - Secondary nav (header dropdown): Account & configuration
 *
 * Uses Navy-First Design System v1.0:
 * - Surfaces are neutral navy family
 * - Meaning conveyed via text, borders, icons (not colored backgrounds)
 */

import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { guardApi, GuardStatus, TodaySnapshot } from '@/api/guard';
import { HealthIndicator } from '@/components/HealthIndicator';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { healthMonitor } from '@/lib/healthCheck';
import { useAuthStore } from '@/stores/authStore';
import { ConsoleIsolationGuard } from '@/routing';

// ============== NAVIGATION STRUCTURE ==============
// Customer Console v1 Constitution (v1.2.0)
// Phase 3: Account Separation - Primary (sidebar) vs Secondary (header)

// PRIMARY NAV: Core Lenses + Connectivity (sidebar)
const PRIMARY_NAV_ITEMS = [
  // CORE LENSES (Primary Domains)
  { id: 'overview', label: 'Overview', icon: '📊', description: 'Is the system okay right now?' },
  { id: 'activity', label: 'Activity', icon: '⚡', description: 'What ran / is running?' },
  { id: 'incidents', label: 'Incidents', icon: '🔔', description: 'What went wrong?' },
  { id: 'policies', label: 'Policies', icon: '📜', description: 'How is behavior defined?' },
  { id: 'logs', label: 'Logs', icon: '📋', description: 'What is the raw truth?' },
  // CONNECTIVITY
  { id: 'integrations', label: 'Integrations', icon: '🔗', description: 'Connected services & webhooks' },
  { id: 'keys', label: 'API Keys', icon: '🔑', description: 'Manage access keys' },
] as const;

// ACCOUNT NAV: Secondary navigation (header dropdown)
// Account is NOT a domain - it manages who, what, and billing
const ACCOUNT_NAV_ITEMS = [
  { id: 'settings', label: 'Settings', icon: '⚙️', description: 'Configuration' },
  { id: 'account', label: 'Account', icon: '👤', description: 'Organization & team' },
] as const;

// Combined for type derivation (all valid navigation targets)
const ALL_NAV_ITEMS = [...PRIMARY_NAV_ITEMS, ...ACCOUNT_NAV_ITEMS] as const;

type NavItemId = typeof ALL_NAV_ITEMS[number]['id'];
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

interface AIConsoleLayoutProps {
  children: React.ReactNode;
  activeTab: NavItemId;
  onTabChange: (tab: NavItemId) => void;
  onLogout?: () => void;
  user?: User | null;
}

export function AIConsoleLayout({ children, activeTab, onTabChange, onLogout, user }: AIConsoleLayoutProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const tenantId = useAuthStore((state) => state.tenantId);

  // Account dropdown state
  const [isAccountDropdownOpen, setIsAccountDropdownOpen] = useState(false);
  const accountDropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (accountDropdownRef.current && !accountDropdownRef.current.contains(event.target as Node)) {
        setIsAccountDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Check if current tab is an account item
  const isAccountTabActive = ACCOUNT_NAV_ITEMS.some(item => item.id === activeTab);

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
      <ConsoleIsolationGuard>
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
                <h1 className="font-bold text-lg">AI Console</h1>
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

          {/* Navigation - Primary items only (Core Lenses + Connectivity) */}
          <nav className="flex-1 p-2 space-y-1">
            {PRIMARY_NAV_ITEMS.map((item) => (
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
                {ALL_NAV_ITEMS.find(i => i.id === activeTab)?.label}
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

              {/* Account Dropdown - Secondary Navigation */}
              <div className="relative" ref={accountDropdownRef}>
                <button
                  onClick={() => setIsAccountDropdownOpen(!isAccountDropdownOpen)}
                  className={`
                    px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors
                    ${isAccountTabActive
                      ? 'bg-navy-elevated text-accent-info border border-accent-info/30'
                      : 'text-slate-300 hover:text-white hover:bg-navy-elevated border border-transparent'
                    }
                  `}
                >
                  <span>👤</span>
                  <span>{user?.name || 'Account'}</span>
                  <span className={`transition-transform ${isAccountDropdownOpen ? 'rotate-180' : ''}`}>▾</span>
                </button>

                {/* Dropdown Menu */}
                {isAccountDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-navy-surface border border-navy-border rounded-xl shadow-lg z-50 overflow-hidden">
                    {/* User Info */}
                    {user && (
                      <div className="px-4 py-3 border-b border-navy-border">
                        <div className="font-medium text-white">{user.name}</div>
                        <div className="text-xs text-slate-400">{user.email}</div>
                      </div>
                    )}

                    {/* Account Navigation Items */}
                    <div className="py-2">
                      {ACCOUNT_NAV_ITEMS.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => {
                            onTabChange(item.id);
                            setIsAccountDropdownOpen(false);
                          }}
                          className={`
                            w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors
                            ${activeTab === item.id
                              ? 'bg-navy-elevated text-accent-info'
                              : 'text-slate-300 hover:bg-navy-elevated hover:text-white'
                            }
                          `}
                        >
                          <span>{item.icon}</span>
                          <div>
                            <span className="font-medium">{item.label}</span>
                            <span className="block text-xs text-slate-400">{item.description}</span>
                          </div>
                        </button>
                      ))}
                    </div>

                    {/* Logout */}
                    {onLogout && (
                      <div className="border-t border-navy-border py-2">
                        <button
                          onClick={() => {
                            setIsAccountDropdownOpen(false);
                            onLogout();
                          }}
                          className="w-full flex items-center gap-3 px-4 py-2.5 text-left text-slate-400 hover:bg-navy-elevated hover:text-white transition-colors"
                        >
                          <span>🚪</span>
                          <span className="font-medium">Logout</span>
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </header>

          {/* Content */}
          <main className="flex-1 overflow-auto bg-navy-app">
            {children}
          </main>
        </div>
      </div>
      </ConsoleIsolationGuard>
    </ErrorBoundary>
  );
}

export default AIConsoleLayout;
export type { NavItemId };
