/**
 * Account Page - Customer Account Management
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console
 * Role: Account and organization management
 *
 * STATUS: PARTIAL - Some APIs not implemented.
 * Required endpoints for full functionality:
 *   GET /api/v1/organization - Organization details
 *   GET /api/v1/team - Team members
 *
 * NO FAKE DATA. NO SIMULATED RESPONSES.
 */

import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { guardApi } from '@/api/guard';
import { logger } from '@/lib/consoleLogger';
import { useAuthStore } from '@/stores/authStore';

export function AccountPage() {
  const tenantId = useAuthStore((state) => state.tenantId);

  useEffect(() => {
    logger.componentMount('AccountPage');
    return () => logger.componentUnmount('AccountPage');
  }, []);

  // NO FALLBACK - missing tenant is a hard error
  if (!tenantId) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-red-500/10 border border-red-400/40 rounded-xl p-6">
          <h3 className="font-bold text-red-400">Authentication Required</h3>
          <p className="text-sm text-slate-300 mt-1">No tenant ID available. Please sign in.</p>
        </div>
      </div>
    );
  }

  // Fetch settings from real API
  const { data: settings, isLoading, error } = useQuery({
    queryKey: ['guard', 'settings'],
    queryFn: guardApi.getSettings,
    retry: false,
  });

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="text-slate-400">Loading account...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-red-500/10 border border-red-400/40 rounded-xl p-6">
          <h3 className="font-bold text-red-400">Failed to Load Account</h3>
          <p className="text-sm text-slate-300 mt-1">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Organization Card */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span>🏢</span> Organization
          </h2>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-2 gap-6">
            <InfoItem label="Tenant ID" value={tenantId} />
            <InfoItem label="Plan" value={settings?.plan || 'Unknown'} />
          </div>
          <div className="mt-4 pt-4 border-t border-slate-700">
            <p className="text-sm text-slate-500">
              Organization API not implemented. Contact support for account changes.
            </p>
          </div>
        </div>
      </div>

      {/* Plan & Limits - Real data from settings API */}
      {settings && (
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="p-4 border-b border-slate-700">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <span>📊</span> Plan & Limits
            </h2>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-2 gap-4">
              {settings.budget_limit_cents && (
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <span className="text-sm text-slate-400">Monthly Budget</span>
                  <div className="text-2xl font-bold mt-1">
                    ${(settings.budget_limit_cents / 100).toFixed(2)}
                  </div>
                </div>
              )}
              {settings.guardrails && (
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <span className="text-sm text-slate-400">Active Guardrails</span>
                  <div className="text-2xl font-bold mt-1">
                    {settings.guardrails.length}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Team Members - API not implemented */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span>👥</span> Team Members
          </h2>
        </div>
        <div className="p-4">
          <div className="bg-amber-500/10 border border-amber-400/30 rounded-lg p-4">
            <p className="text-sm text-amber-400">
              Team management API not implemented.
            </p>
            <p className="text-xs text-slate-500 mt-1 font-mono">
              Required: GET /api/v1/team
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-sm text-slate-400">{label}</span>
      <span className="block font-medium text-white mt-1">{value}</span>
    </div>
  );
}

export default AccountPage;
