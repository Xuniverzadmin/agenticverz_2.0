/**
 * Customer API Keys Page
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console
 * Role: API key management for customers
 *
 * STATUS: DISABLED - Backend API not implemented.
 * Required endpoints:
 *   GET    /api/v1/keys           - List keys
 *   POST   /api/v1/keys           - Create key
 *   POST   /api/v1/keys/{id}/rotate - Rotate key
 *   DELETE /api/v1/keys/{id}      - Revoke key
 *
 * When backend is ready, wire real API calls here.
 * NO FAKE DATA. NO SIMULATED RESPONSES.
 */

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { logger } from '@/lib/consoleLogger';
import { apiClient } from '@/api/client';

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  status: 'active' | 'frozen' | 'revoked';
  created_at: string;
  last_used_at: string | null;
  requests_today: number;
  spend_today_cents: number;
}

export function KeysPage() {
  useEffect(() => {
    logger.componentMount('CustomerKeysPage');
    return () => logger.componentUnmount('CustomerKeysPage');
  }, []);

  // Real API call - will fail until backend is implemented
  const { data: keys, isLoading, error } = useQuery<ApiKey[]>({
    queryKey: ['customer', 'keys'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/keys');
      return response.data;
    },
    retry: false, // Don't retry - let it fail clearly
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading keys...</div>
      </div>
    );
  }

  // API not implemented - show clear error
  if (error) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <span>🔑</span> API Keys
            </h1>
            <p className="text-slate-400 mt-1">
              Manage your API keys for accessing the service
            </p>
          </div>
        </div>

        <div className="bg-red-500/10 border border-red-400/40 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <h3 className="font-bold text-red-400">API Not Available</h3>
              <p className="text-sm text-slate-300 mt-1">
                The keys management API is not yet implemented.
              </p>
              <p className="text-xs text-slate-500 mt-2 font-mono">
                Required: GET /api/v1/keys
              </p>
              <p className="text-xs text-slate-500 font-mono">
                Error: {error instanceof Error ? error.message : 'Unknown error'}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Real data from backend
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span>🔑</span> API Keys
          </h1>
          <p className="text-slate-400 mt-1">
            Manage your API keys for accessing the service
          </p>
        </div>
        {/* Create button disabled until POST /api/v1/keys is implemented */}
        <button
          disabled
          className="px-4 py-2 bg-slate-700 text-slate-500 cursor-not-allowed rounded-lg text-sm font-medium"
          title="Create key API not implemented"
        >
          + Create Key
        </button>
      </div>

      {/* Keys Table */}
      {keys && keys.length > 0 ? (
        <div className="bg-navy-surface rounded-xl border border-navy-border overflow-hidden">
          <table className="w-full">
            <thead className="bg-navy-elevated">
              <tr className="text-left text-sm text-slate-400">
                <th className="p-4">Name</th>
                <th className="p-4">Key</th>
                <th className="p-4">Status</th>
                <th className="p-4">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-border">
              {keys.map((key) => (
                <tr key={key.id}>
                  <td className="p-4 font-medium text-white">{key.name}</td>
                  <td className="p-4 font-mono text-sm text-slate-400">{key.prefix}</td>
                  <td className="p-4">
                    <span className={`
                      px-2 py-1 rounded border text-xs font-medium bg-transparent
                      ${key.status === 'active' ? 'text-green-400 border-green-400/40' : ''}
                      ${key.status === 'frozen' ? 'text-amber-400 border-amber-400/40' : ''}
                      ${key.status === 'revoked' ? 'text-red-400 border-red-400/40' : ''}
                    `}>
                      {key.status}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-slate-400">
                    {new Date(key.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-navy-surface rounded-xl border border-navy-border p-8 text-center">
          <p className="text-slate-400">No API keys found.</p>
        </div>
      )}
    </div>
  );
}

export default KeysPage;
