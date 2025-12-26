/**
 * Ops Console Entry Point
 *
 * M28: Two views for founders:
 * - Pulse: 10-second situation awareness (default landing)
 * - Console: Full detailed dashboard
 *
 * Standalone entry for the Founder Ops Console.
 * Handles API key authentication independently from the main AOS console.
 *
 * Access: https://agenticverz.com/console/ops
 *
 * Authentication:
 * - API key can be provided via URL query param: ?key=xxx
 * - Or entered in the login form
 * - Stored in localStorage for session persistence
 */

import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Clock, Power } from 'lucide-react';
import FounderOpsConsole from './FounderOpsConsole';
import { FounderPulsePage } from './FounderPulsePage';

// Create query client for Pulse page
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 2,
    },
  },
});

type OpsView = 'pulse' | 'console';

const API_BASE = import.meta.env.VITE_API_BASE || 'https://agenticverz.com';
const STORAGE_KEY = 'ops-console-api-key';

export default function OpsConsoleEntry() {
  const [searchParams] = useSearchParams();
  const [apiKey, setApiKey] = useState('');
  const [inputKey, setInputKey] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeView, setActiveView] = useState<OpsView>('pulse');

  // Check for API key from URL or localStorage on mount
  useEffect(() => {
    const urlKey = searchParams.get('key');
    const storedKey = localStorage.getItem(STORAGE_KEY);

    if (urlKey) {
      validateAndSetKey(urlKey);
    } else if (storedKey) {
      validateAndSetKey(storedKey);
    }
  }, [searchParams]);

  const validateAndSetKey = async (key: string) => {
    if (!key.trim()) return;

    setIsValidating(true);
    setError('');

    try {
      // Validate against ops endpoint (requires valid API key)
      const response = await fetch(`${API_BASE}/ops/pulse`, {
        headers: { 'X-API-Key': key },
      });

      if (response.ok) {
        setApiKey(key);
        setIsAuthenticated(true);
        localStorage.setItem(STORAGE_KEY, key);
        // Remove key from URL for security
        if (searchParams.get('key')) {
          window.history.replaceState({}, '', window.location.pathname);
        }
      } else if (response.status === 401 || response.status === 403) {
        setError('Invalid API key or insufficient permissions');
        localStorage.removeItem(STORAGE_KEY);
      } else {
        setError('Failed to connect to Ops API');
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (err) {
      setError('Failed to connect to server');
    } finally {
      setIsValidating(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    validateAndSetKey(inputKey);
  };

  const handleLogout = () => {
    setApiKey('');
    setIsAuthenticated(false);
    localStorage.removeItem(STORAGE_KEY);
  };

  // Show login form if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950 p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-emerald-500 rounded-xl flex items-center justify-center">
                <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
            </div>
            <h1 className="text-2xl font-bold text-white">
              Founder Ops Console
            </h1>
            <p className="text-gray-400 mt-2">
              AI Mission Control - System health & customer intelligence
            </p>
          </div>

          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Ops API Key
                </label>
                <input
                  type="password"
                  value={inputKey}
                  onChange={(e) => setInputKey(e.target.value)}
                  placeholder="Enter your Ops API key"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  autoFocus
                  disabled={isValidating}
                />
              </div>

              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isValidating || !inputKey.trim()}
                className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
              >
                {isValidating ? 'Connecting...' : 'Connect to Ops Console'}
              </button>
            </form>

            <div className="mt-6 pt-6 border-t border-gray-800">
              <p className="text-xs text-gray-500 text-center">
                This console is for founders and operators only.
                <br />
                Requires Ops-level API key access.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Render the Ops Console with view tabs
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-950 flex flex-col">
        {/* View Tabs Header */}
        <div className="bg-gray-900 border-b border-gray-800 px-6 py-2 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-bold">F</span>
              </div>
              <span className="text-white font-semibold">Founder Ops</span>
            </div>

            {/* View Tabs */}
            <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setActiveView('pulse')}
                className={`
                  px-4 py-1.5 rounded-md text-sm font-medium transition-colors
                  ${activeView === 'pulse'
                    ? 'bg-emerald-500 text-white'
                    : 'text-gray-400 hover:text-white'
                  }
                `}
              >
                Pulse
              </button>
              <button
                onClick={() => setActiveView('console')}
                className={`
                  px-4 py-1.5 rounded-md text-sm font-medium transition-colors
                  ${activeView === 'console'
                    ? 'bg-emerald-500 text-white'
                    : 'text-gray-400 hover:text-white'
                  }
                `}
              >
                Console
              </button>
            </div>

            {/* Founder Pages (Phase 5E) */}
            <div className="flex items-center gap-3 border-l border-gray-700 pl-4 ml-2">
              <Link
                to="/founder/timeline"
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
              >
                <Clock className="w-4 h-4" />
                Timeline
              </Link>
              <Link
                to="/founder/controls"
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
              >
                <Power className="w-4 h-4" />
                Controls
              </Link>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="text-gray-400 hover:text-white text-sm transition-colors"
          >
            Logout
          </button>
        </div>

        {/* View Content */}
        <div className="flex-1 overflow-auto">
          {activeView === 'pulse' ? (
            <FounderPulsePage />
          ) : (
            <FounderOpsConsole />
          )}
        </div>
      </div>
    </QueryClientProvider>
  );
}
