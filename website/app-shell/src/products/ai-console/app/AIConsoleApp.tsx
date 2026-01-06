// Layer: L1 — Product Experience (Frontend)
// Product: AI Console
// Type: Product Root (routing, providers, layout)
// Reference: PIN-240
// NOTE: If this file disappeared, only screens disappear. No logic here.

/**
 * AI Console - Product Application Root
 *
 * Role: Product boundary (routing, providers, layout)
 *
 * This is the product root for AI Console. It can be:
 * - Lazy-loaded by the main console shell (current: /guard/*)
 * - Mounted standalone via main.tsx (future: console.agenticverz.com)
 *
 * Architecture (3-layer separation):
 * - main.tsx        = Browser entry (DOM mounting, environment)
 * - AIConsoleApp    = Product root (providers, routing, layout) ← YOU ARE HERE
 * - pages/*         = Features (UI, business logic)
 *
 * URL Routes:
 * - /guard                 → Redirects to /guard/overview
 * - /guard/overview        → Is the system okay right now?
 * - /guard/activity        → What ran / is running?
 * - /guard/incidents       → What went wrong?
 * - /guard/incidents/:id   → Incident detail (O3)
 * - /guard/policies        → How is behavior defined?
 * - /guard/logs            → What is the raw truth?
 * - /guard/integrations    → Connected services & webhooks
 * - /guard/keys            → API key management
 * - /guard/settings        → Configuration
 * - /guard/account         → Organization & team
 *
 * Authentication (Hybrid - M24):
 * - Primary: OAuth tokens from main auth store (after onboarding)
 * - Fallback: API key via URL query param or login form
 *
 * NOT exposed to customers (Founder-only):
 * - Kill-switches, Decision timelines, Recovery classes, CARE internals
 */

import { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate, useLocation, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/authStore';
import { BetaBanner } from '@/components/BetaBanner';

// App-level components (local)
import { AIConsoleLayout, type NavItemId } from './AIConsoleLayout';

// Pages - domain-first structure
import { OverviewPage } from '@ai-console/pages/overview/OverviewPage';
import { ActivityPage } from '@ai-console/pages/activity/ActivityPage';
import { PoliciesPage } from '@ai-console/pages/policies/PoliciesPage';
import { LogsPage } from '@ai-console/pages/logs/LogsPage';
import { IncidentsPage } from '@ai-console/pages/incidents/IncidentsPage';
import IncidentDetailPage from '@ai-console/pages/incidents/IncidentDetailPage';
// Integrations
import { IntegrationsPage } from '@ai-console/integrations/IntegrationsPage';
import { KeysPage } from '@ai-console/integrations/KeysPage';

// Account
import { SettingsPage } from '@ai-console/account/SettingsPage';
import { AccountPage } from '@ai-console/account/AccountPage';
// QUARANTINE (PIN-317): SupportPage moved to quarantine - no route defined

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

/**
 * AIConsoleApp - Product Root Component
 *
 * Named export for direct imports (main.tsx, tests)
 * Default export for lazy loading (routes/index.tsx)
 */
export function AIConsoleApp() {
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
  const [authMode, setAuthMode] = useState<'oauth' | 'apikey' | null>(null);
  const location = useLocation();

  // Derive activeTab from URL path
  const activeTab = useMemo((): NavItemId => {
    const path = location.pathname;
    // Match /guard/{tab} pattern
    const match = path.match(/^\/guard\/([a-z]+)/);
    if (match) {
      const tab = match[1] as NavItemId;
      // Validate it's a known tab
      const validTabs: NavItemId[] = ['overview', 'activity', 'incidents', 'policies', 'logs', 'integrations', 'keys', 'settings', 'account'];
      if (validTabs.includes(tab)) {
        return tab;
      }
    }
    return 'overview';
  }, [location.pathname]);

  // Navigation handler - navigates to URL instead of setting state
  const handleTabChange = (tab: NavItemId) => {
    navigate(`/guard/${tab}`);
  };

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
      localStorage.removeItem(STORAGE_KEY);
      navigate('/guard/overview', { replace: true });
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
              AI Console
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
                  placeholder="Enter your API key"
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

  // Phase 5: URL-based routing - all pages are routes
  const renderRoutes = () => {
    return (
      <Routes>
        {/* Default redirect to overview */}
        <Route path="/" element={<Navigate to="/guard/overview" replace />} />

        {/* Core Lenses */}
        <Route path="overview" element={<OverviewPage />} />
        <Route path="activity" element={<ActivityPage />} />
        <Route path="incidents" element={<IncidentsPage />} />
        <Route path="incidents/:incidentId" element={<IncidentDetailPage />} />
        <Route path="policies" element={<PoliciesPage />} />
        <Route path="logs" element={<LogsPage />} />

        {/* Connectivity */}
        <Route path="integrations" element={<IntegrationsPage />} />
        <Route path="keys" element={<KeysPage />} />

        {/* Account (secondary nav) */}
        <Route path="settings" element={<SettingsPage />} />
        <Route path="account" element={<AccountPage />} />

        {/* Catch-all redirect to overview */}
        <Route path="*" element={<Navigate to="/guard/overview" replace />} />
      </Routes>
    );
  };

  // Render the AI Console with unified layout
  return (
    <QueryClientProvider client={queryClient}>
      {/* PIN-189: Founder Beta banner - remove after subdomain deployment */}
      <BetaBanner />
      <AIConsoleLayout
        activeTab={activeTab}
        onTabChange={handleTabChange}
        onLogout={handleLogout}
        user={authMode === 'oauth' ? user : undefined}
      >
        {renderRoutes()}
      </AIConsoleLayout>
    </QueryClientProvider>
  );
}

// Default export for lazy loading (routes/index.tsx uses dynamic import)
export default AIConsoleApp;
