/**
 * Guard Console Entry Point
 *
 * ⚠️ IMPORTANT: This is the PRODUCTION entry point loaded via lazy loading.
 * When adding new pages:
 * 1. Add import here (NOT just in GuardConsoleApp.tsx)
 * 2. Add case in renderPage() switch
 * 3. Update NAV_ITEMS in GuardLayout.tsx
 *
 * Standalone entry for the AI Incident Console (Guard Console).
 * Implements full 8-phase customer console with unified navigation.
 *
 * Access: https://agenticverz.com/console/guard
 *
 * Authentication (Hybrid - M24):
 * - Primary: OAuth tokens from main auth store (after onboarding)
 * - Fallback: API key via URL query param or login form
 * - Stored in localStorage for session persistence
 *
 * Navigation (must match GuardLayout.tsx NAV_ITEMS):
 * - Overview: Control plane & status (Phase 1)
 * - Live Activity: Real-time event stream (Phase 4)
 * - Incidents: Search & investigate (Phase 2-3)
 * - Kill Switch: Emergency controls + blast radius (Phase 5)
 * - Logs: Event history (Phase 4)
 * - Settings: Configuration (Phase 8)
 * - Account: Organization & team
 * - Support: Help & feedback
 */

import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/authStore';
import { GuardLayout, type NavItemId } from './GuardLayout';
import { GuardDashboard } from './GuardDashboard';
import { LiveActivityPage } from './LiveActivityPage';
import { IncidentsPage } from './incidents/IncidentsPage';
import { KillSwitchPage } from './KillSwitchPage';
import { LogsPage } from './LogsPage';
import { GuardSettingsPage } from './GuardSettingsPage';
import { AccountPage } from './AccountPage';
import { SupportPage } from './SupportPage';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://agenticverz.com';
const STORAGE_KEY = 'guard-console-api-key';
const TENANT_STORAGE_KEY = 'guard-console-tenant-id';

// Create query client with optimized settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 2,
      refetchOnWindowFocus: true,
    },
  },
});

export default function GuardConsoleEntry() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Get OAuth state from main auth store
  const {
    isAuthenticated: oauthAuthenticated,
    token: oauthToken,
    tenantId: oauthTenantId,
    user,
    logout: oauthLogout
  } = useAuthStore();

  const [apiKey, setApiKey] = useState('');
  const [inputKey, setInputKey] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState('');
  const [isApiKeyAuthenticated, setIsApiKeyAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState<NavItemId>('overview');
  const [authMode, setAuthMode] = useState<'oauth' | 'apikey' | null>(null);

  // Check authentication on mount
  useEffect(() => {
    // Priority 1: OAuth from main auth store (after onboarding)
    if (oauthAuthenticated && oauthToken) {
      setAuthMode('oauth');
      return;
    }

    // Priority 2: API key from URL param
    const urlKey = searchParams.get('key');
    if (urlKey) {
      validateAndSetKey(urlKey);
      return;
    }

    // Priority 3: Stored API key
    const storedKey = localStorage.getItem(STORAGE_KEY);
    if (storedKey) {
      validateAndSetKey(storedKey);
    }
  }, [oauthAuthenticated, oauthToken, searchParams]);

  const validateAndSetKey = async (key: string) => {
    if (!key.trim()) return;

    setIsValidating(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/v1/runtime/capabilities`, {
        headers: { 'X-API-Key': key },
      });

      if (response.ok) {
        setApiKey(key);
        setIsApiKeyAuthenticated(true);
        setAuthMode('apikey');
        localStorage.setItem(STORAGE_KEY, key);

        // Set auth store for guard API calls
        const tenantId = localStorage.getItem(TENANT_STORAGE_KEY) || 'demo-tenant';
        useAuthStore.getState().setTokens(key, '');
        useAuthStore.getState().setTenant(tenantId);

        // Remove key from URL for security
        if (searchParams.get('key')) {
          window.history.replaceState({}, '', window.location.pathname);
        }
      } else {
        setError('Invalid API key');
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (err) {
      // Allow demo mode even if validation fails
      setApiKey(key);
      setIsApiKeyAuthenticated(true);
      setAuthMode('apikey');
      localStorage.setItem(STORAGE_KEY, key);
      const tenantId = localStorage.getItem(TENANT_STORAGE_KEY) || 'demo-tenant';
      useAuthStore.getState().setTokens(key, '');
      useAuthStore.getState().setTenant(tenantId);
    } finally {
      setIsValidating(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    validateAndSetKey(inputKey);
  };

  const handleLogout = () => {
    if (authMode === 'oauth') {
      // OAuth logout - go back to login
      oauthLogout();
      navigate('/login', { replace: true });
    } else {
      // API key logout - stay on guard login
      setApiKey('');
      setIsApiKeyAuthenticated(false);
      setAuthMode(null);
      setActiveTab('overview');
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const handleDemoLogin = () => {
    validateAndSetKey('edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf');
  };

  const handleOAuthLogin = () => {
    navigate('/login', { replace: true });
  };

  // Check if authenticated (either OAuth or API key)
  const isAuthenticated = authMode === 'oauth' || (authMode === 'apikey' && isApiKeyAuthenticated);

  // Show login form if not authenticated - Navy-First design
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-navy-app p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="w-20 h-20 bg-gradient-to-br from-accent-info to-accent-primary rounded-2xl flex items-center justify-center">
                <span className="text-4xl">🛡️</span>
              </div>
            </div>
            <h1 className="text-3xl font-bold text-white">
              AI Guard Console
            </h1>
            <p className="text-slate-400 mt-2">
              Customer AI Safety Dashboard
            </p>
          </div>

          <div className="bg-navy-surface rounded-xl p-6 border border-navy-border">
            {/* OAuth Login Button */}
            <button
              onClick={handleOAuthLogin}
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2 mb-4"
            >
              Sign in with Google or Microsoft
            </button>

            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-navy-border" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-navy-surface px-4 text-sm text-slate-400">or use API key</span>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  API Key
                </label>
                <input
                  type="password"
                  value={inputKey}
                  onChange={(e) => setInputKey(e.target.value)}
                  placeholder="Enter your Guard API key"
                  className="w-full px-4 py-3 bg-navy-inset border border-navy-border rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent-info focus:border-transparent"
                  disabled={isValidating}
                />
              </div>

              {error && (
                <div className="p-3 bg-navy-elevated border border-accent-danger/40 rounded-lg text-accent-danger text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isValidating || !inputKey.trim()}
                className="w-full py-3 bg-navy-elevated hover:bg-navy-subtle border border-accent-info text-accent-info disabled:border-navy-border disabled:text-slate-500 disabled:cursor-not-allowed font-medium rounded-lg transition-colors"
              >
                {isValidating ? 'Connecting...' : 'Sign In with API Key'}
              </button>
            </form>

            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-navy-border" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-navy-surface px-4 text-sm text-slate-400">or</span>
              </div>
            </div>

            <button
              onClick={handleDemoLogin}
              disabled={isValidating}
              className="w-full py-3 bg-navy-elevated hover:bg-navy-subtle border border-navy-border text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              <span>🎮</span> Try Demo Mode
            </button>

            <div className="mt-6 pt-6 border-t border-navy-border">
              <p className="text-xs text-slate-500 text-center">
                New customer?{' '}
                <a href="/login" className="text-accent-info hover:underline">
                  Sign up for access
                </a>
              </p>
            </div>
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

  // Render active page
  const renderPage = () => {
    switch (activeTab) {
      case 'overview':
        return <GuardDashboard onLogout={handleLogout} />;
      case 'live':
        return <LiveActivityPage />;
      case 'incidents':
        return <IncidentsPage />;
      case 'killswitch':
        return <KillSwitchPage />;
      case 'logs':
        return <LogsPage />;
      case 'settings':
        return <GuardSettingsPage />;
      case 'account':
        return <AccountPage />;
      case 'support':
        return <SupportPage />;
      default:
        return <GuardDashboard onLogout={handleLogout} />;
    }
  };

  // Render the Guard Console with unified layout
  return (
    <QueryClientProvider client={queryClient}>
      <GuardLayout
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onLogout={handleLogout}
        user={authMode === 'oauth' ? user : undefined}
      >
        {renderPage()}
      </GuardLayout>
    </QueryClientProvider>
  );
}
