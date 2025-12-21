/**
 * Account Page - Customer Account Management
 *
 * Essential customer lifecycle features:
 * - Organization details
 * - Environment info (Demo/Prod)
 * - Plan & limits
 * - Team members (read-only for now)
 */

import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { guardApi } from '../../api/guard';
import { logger } from '../../lib/consoleLogger';
import { useAuthStore } from '../../stores/authStore';

export function AccountPage() {
  const tenantId = useAuthStore((state) => state.tenantId) || 'demo-tenant';

  useEffect(() => {
    logger.componentMount('AccountPage');
    return () => logger.componentUnmount('AccountPage');
  }, []);

  // Fetch settings for plan info
  const { data: settings, isLoading, error } = useQuery({
    queryKey: ['guard', 'settings'],
    queryFn: guardApi.getSettings,
    retry: 1,
  });

  // Demo organization data
  const orgData = {
    name: 'Acme Corp',
    environment: 'demo',
    region: 'us-west-2',
    created: '2024-11-15',
    plan: settings?.plan || 'starter',
    owner: 'admin@company.com',
  };

  const teamMembers = [
    { email: 'admin@company.com', role: 'Owner', lastActive: '2 hours ago' },
    { email: 'ops@company.com', role: 'Admin', lastActive: '1 day ago' },
    { email: 'dev@company.com', role: 'Viewer', lastActive: '3 days ago' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* Demo Mode Banner */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg px-4 py-2 text-center">
        <span className="text-amber-400 text-sm">
          ⚠️ You are viewing <strong>Demo mode</strong> — settings are read-only.
        </span>
      </div>

      {/* Organization Card */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span>🏢</span> Organization
          </h2>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-2 gap-6">
            <InfoItem label="Organization Name" value={orgData.name} />
            <InfoItem label="Environment" value={orgData.environment.toUpperCase()} badge />
            <InfoItem label="Region" value={orgData.region} />
            <InfoItem label="Created" value={new Date(orgData.created).toLocaleDateString()} />
            <InfoItem label="Plan" value={orgData.plan.charAt(0).toUpperCase() + orgData.plan.slice(1)} />
            <InfoItem label="Owner" value={orgData.owner} />
          </div>
        </div>
      </div>

      {/* Plan & Limits */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span>📊</span> Plan & Limits
          </h2>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-3 gap-4">
            <LimitCard
              label="Monthly Budget"
              current={settings?.budget_limit_cents ? settings.budget_limit_cents / 100 : 100}
              max={500}
              unit="$"
            />
            <LimitCard
              label="API Keys"
              current={3}
              max={10}
              unit="keys"
            />
            <LimitCard
              label="Guardrails"
              current={settings?.guardrails?.length || 5}
              max={20}
              unit="rules"
            />
          </div>
          <div className="mt-4 pt-4 border-t border-slate-700">
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors">
              Upgrade Plan
            </button>
          </div>
        </div>
      </div>

      {/* Team Members */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700 flex items-center justify-between">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span>👥</span> Team Members
          </h2>
          <span className="text-xs bg-slate-700 px-2 py-1 rounded">Read-only in demo</span>
        </div>
        <div className="divide-y divide-slate-700">
          {teamMembers.map((member, idx) => (
            <div key={idx} className="p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center">
                  <span className="text-lg">👤</span>
                </div>
                <div>
                  <span className="font-medium">{member.email}</span>
                  <span className="block text-sm text-slate-400">Last active: {member.lastActive}</span>
                </div>
              </div>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                member.role === 'Owner' ? 'bg-purple-500/20 text-purple-400' :
                member.role === 'Admin' ? 'bg-blue-500/20 text-blue-400' :
                'bg-slate-600 text-slate-300'
              }`}>
                {member.role}
              </span>
            </div>
          ))}
        </div>
        <div className="p-4 border-t border-slate-700 bg-slate-700/30">
          <button className="text-sm text-slate-400 hover:text-white transition-colors" disabled>
            + Invite team member (upgrade required)
          </button>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-slate-800 rounded-xl border border-red-500/30 overflow-hidden">
        <div className="p-4 border-b border-red-500/30">
          <h2 className="text-lg font-bold text-red-400 flex items-center gap-2">
            <span>⚠️</span> Danger Zone
          </h2>
        </div>
        <div className="p-4">
          <p className="text-sm text-slate-400 mb-4">
            Permanently delete your organization and all associated data. This action cannot be undone.
          </p>
          <button className="px-4 py-2 border border-red-500 text-red-400 hover:bg-red-500/20 rounded-lg text-sm font-medium transition-colors" disabled>
            Delete Organization (disabled in demo)
          </button>
        </div>
      </div>
    </div>
  );
}

function InfoItem({ label, value, badge }: { label: string; value: string; badge?: boolean }) {
  return (
    <div>
      <span className="text-sm text-slate-400">{label}</span>
      {badge ? (
        <span className="block mt-1">
          <span className="px-2 py-1 bg-amber-500/20 text-amber-400 rounded text-sm font-medium">
            {value}
          </span>
        </span>
      ) : (
        <span className="block font-medium text-white mt-1">{value}</span>
      )}
    </div>
  );
}

function LimitCard({ label, current, max, unit }: { label: string; current: number; max: number; unit: string }) {
  const percentage = (current / max) * 100;
  return (
    <div className="bg-slate-700/50 rounded-lg p-4">
      <span className="text-sm text-slate-400">{label}</span>
      <div className="flex items-end gap-1 mt-1">
        <span className="text-2xl font-bold">{unit === '$' ? `$${current}` : current}</span>
        <span className="text-slate-400 text-sm mb-0.5">/ {unit === '$' ? `$${max}` : `${max} ${unit}`}</span>
      </div>
      <div className="mt-2 h-2 bg-slate-600 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${percentage > 80 ? 'bg-red-500' : percentage > 50 ? 'bg-amber-500' : 'bg-emerald-500'}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

export default AccountPage;
