/**
 * Guard Console App - Alternative Entry Point
 *
 * Phase 5E-4: Customer Essentials
 *
 * Navigation structure (Customer-scoped):
 * - Home: Status overview
 * - Runs: Run history & outcomes
 * - Limits: Budget & rate limits
 * - Incidents: Search & investigate
 * - Keys: API key management
 * - Settings: Configuration
 * - Account: Organization & team
 * - Support: Help & feedback
 *
 * NOT exposed (Founder-only):
 * - Kill-switches, Decision timelines, Recovery classes, CARE internals
 */

import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '../../stores/authStore';
import { logger } from '../../lib/consoleLogger';
import { GuardLayout, NavItemId } from './GuardLayout';
import { CustomerHomePage } from './CustomerHomePage';
import { CustomerRunsPage } from './CustomerRunsPage';
import { CustomerLimitsPage } from './CustomerLimitsPage';
import { CustomerKeysPage } from './CustomerKeysPage';
import { IncidentsPage } from './incidents/IncidentsPage';
import { GuardSettingsPage } from './GuardSettingsPage';
import { AccountPage } from './AccountPage';
import { SupportPage } from './SupportPage';

// API key storage key
const API_KEY_STORAGE_KEY = 'guard-api-key';
const TENANT_STORAGE_KEY = 'guard-tenant-id';

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 2,
      refetchOnWindowFocus: true,
    },
  },
});

export function GuardConsoleApp() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<NavItemId>('home');

  useEffect(() => {
    logger.componentMount('GuardConsoleApp');
    return () => logger.componentUnmount('GuardConsoleApp');
  }, []);

  // Check for stored credentials on mount
  useEffect(() => {
    const storedKey = localStorage.getItem(API_KEY_STORAGE_KEY);
    const storedTenant = localStorage.getItem(TENANT_STORAGE_KEY);

    if (storedKey) {
      setApiKey(storedKey);
      setIsAuthenticated(true);

      // Set auth store
      useAuthStore.getState().setTokens(storedKey, '');
      useAuthStore.getState().setTenant(storedTenant || 'demo-tenant');
    }

    setIsLoading(false);
  }, []);

  const handleLogin = (key: string) => {
    // Store credentials
    localStorage.setItem(API_KEY_STORAGE_KEY, key);
    localStorage.setItem(TENANT_STORAGE_KEY, 'demo-tenant');

    // Set auth store
    useAuthStore.getState().setTokens(key, '');
    useAuthStore.getState().setTenant('demo-tenant');

    setApiKey(key);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem(API_KEY_STORAGE_KEY);
    localStorage.removeItem(TENANT_STORAGE_KEY);
    useAuthStore.getState().logout();
    setApiKey('');
    setIsAuthenticated(false);
    setActiveTab('home');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  // Render active page
  // Phase 5E-4: Customer Essentials - scoped to outcomes, limits, and keys
  const renderPage = () => {
    switch (activeTab) {
      case 'home':
        return <CustomerHomePage onNavigate={setActiveTab} />;
      case 'runs':
        return <CustomerRunsPage />;
      case 'limits':
        return <CustomerLimitsPage />;
      case 'incidents':
        return <IncidentsPage />;
      case 'keys':
        return <CustomerKeysPage />;
      case 'settings':
        return <GuardSettingsPage />;
      case 'account':
        return <AccountPage />;
      case 'support':
        return <SupportPage />;
      default:
        return <CustomerHomePage onNavigate={setActiveTab} />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <GuardLayout
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onLogout={handleLogout}
      >
        {renderPage()}
      </GuardLayout>
    </QueryClientProvider>
  );
}

// Login Page Component
function LoginPage({ onLogin }: { onLogin: (key: string) => void }) {
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }

    setIsLoading(true);

    // Simulate validation (in production, validate with backend)
    await new Promise(resolve => setTimeout(resolve, 500));

    onLogin(apiKey);
    setIsLoading(false);
  };

  const useDemoKey = () => {
    // Demo API key for testing
    onLogin('edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf');
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-4xl">🛡️</span>
          </div>
          <h1 className="text-3xl font-bold text-white">AI Guard Console</h1>
          <p className="text-slate-400 mt-2">Customer AI Safety Dashboard</p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6">
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your Guard API key"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
              {error && (
                <p className="text-red-400 text-sm mt-2">{error}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 rounded-lg font-medium transition-colors"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-700" />
            </div>
            <div className="relative flex justify-center">
              <span className="bg-slate-800 px-4 text-sm text-slate-400">or</span>
            </div>
          </div>

          <button
            onClick={useDemoKey}
            className="w-full py-3 bg-slate-700 hover:bg-slate-600 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            <span>🎮</span> Try Demo Mode
          </button>
        </div>

        {/* Help Text */}
        <div className="text-center mt-6">
          <p className="text-slate-400 text-sm">
            Need an API key?{' '}
            <a href="https://agenticverz.com" className="text-blue-400 hover:underline">
              Sign up for access
            </a>
          </p>
        </div>

        {/* Features */}
        <div className="mt-12 grid grid-cols-3 gap-4 text-center">
          {[
            { icon: '🔍', label: 'Investigate', desc: 'AI incidents' },
            { icon: '🔄', label: 'Replay', desc: 'Decisions' },
            { icon: '📊', label: 'Export', desc: 'Evidence' },
          ].map((feature, i) => (
            <div key={i} className="p-4">
              <span className="text-2xl">{feature.icon}</span>
              <p className="text-white font-medium mt-2">{feature.label}</p>
              <p className="text-slate-400 text-xs">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default GuardConsoleApp;
