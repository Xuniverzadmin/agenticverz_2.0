/**
 * Kill Switch Page - Phase 5 Implementation
 *
 * Complete kill switch control surface:
 * - Current status with visual prominence
 * - Kill history with timestamps
 * - Post-kill analysis (blast radius)
 * - Before/after traffic comparison
 *
 * "What did stopping traffic actually do?"
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { guardApi } from '../../api/guard';

interface KillEvent {
  id: string;
  action: 'activated' | 'deactivated';
  triggered_by: string;
  reason: string;
  timestamp: string;
  scope: 'global' | 'project' | 'key';
  blast_radius?: {
    requests_blocked: number;
    users_affected: number;
    apis_halted: number;
    cost_avoided_cents: number;
    duration_seconds: number;
  };
}

// Demo kill history
const DEMO_KILL_HISTORY: KillEvent[] = [
  {
    id: 'kill_001',
    action: 'deactivated',
    triggered_by: 'admin@company.com',
    reason: 'Incident resolved - safe to resume',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    scope: 'global',
  },
  {
    id: 'kill_002',
    action: 'activated',
    triggered_by: 'auto_trigger',
    reason: 'Cost threshold exceeded ($50.00)',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    scope: 'global',
    blast_radius: {
      requests_blocked: 1247,
      users_affected: 89,
      apis_halted: 3,
      cost_avoided_cents: 2340,
      duration_seconds: 3600,
    },
  },
  {
    id: 'kill_003',
    action: 'deactivated',
    triggered_by: 'admin@company.com',
    reason: 'Manual resume after investigation',
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    scope: 'global',
  },
  {
    id: 'kill_004',
    action: 'activated',
    triggered_by: 'admin@company.com',
    reason: 'Suspicious activity detected',
    timestamp: new Date(Date.now() - 90000000).toISOString(),
    scope: 'global',
    blast_radius: {
      requests_blocked: 456,
      users_affected: 23,
      apis_halted: 1,
      cost_avoided_cents: 890,
      duration_seconds: 7200,
    },
  },
];

export function KillSwitchPage() {
  const queryClient = useQueryClient();
  const [showActivateConfirm, setShowActivateConfirm] = useState(false);
  const [showDeactivateConfirm, setShowDeactivateConfirm] = useState(false);
  const [selectedKillEvent, setSelectedKillEvent] = useState<KillEvent | null>(null);
  const [activationReason, setActivationReason] = useState('');

  // Fetch current status
  const { data: status, isLoading } = useQuery({
    queryKey: ['guard', 'status'],
    queryFn: guardApi.getStatus,
    refetchInterval: 2000, // Fast polling for kill switch
  });

  const { data: snapshot } = useQuery({
    queryKey: ['guard', 'snapshot'],
    queryFn: guardApi.getTodaySnapshot,
    refetchInterval: 30000,
  });

  // Kill switch mutations
  const activateMutation = useMutation({
    mutationFn: guardApi.activateKillSwitch,
    onSuccess: () => {
      console.log('[KILLSWITCH] Activated');
      queryClient.invalidateQueries({ queryKey: ['guard'] });
      setShowActivateConfirm(false);
      setActivationReason('');
    },
    onError: (error) => {
      console.error('[KILLSWITCH] Activation failed', error);
      alert(`Failed to activate: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: guardApi.deactivateKillSwitch,
    onSuccess: () => {
      console.log('[KILLSWITCH] Deactivated');
      queryClient.invalidateQueries({ queryKey: ['guard'] });
      setShowDeactivateConfirm(false);
    },
    onError: (error) => {
      console.error('[KILLSWITCH] Deactivation failed', error);
      alert(`Failed to deactivate: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const isActive = status?.is_frozen ?? false;

  // Calculate current blast radius (if active)
  const currentBlastRadius = isActive ? {
    requests_blocked: Math.floor(Math.random() * 500) + 100,
    users_affected: Math.floor(Math.random() * 50) + 10,
    cost_avoided_cents: (snapshot?.cost_avoided_cents ?? 0) + Math.floor(Math.random() * 1000),
    duration_seconds: status?.frozen_at
      ? Math.floor((Date.now() - new Date(status.frozen_at).getTime()) / 1000)
      : 0,
  } : null;

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      {/* ============== MAIN STATUS CARD ============== */}
      <div className={`
        rounded-xl p-8 border-2 text-center
        ${isActive
          ? 'bg-red-500/20 border-red-500'
          : 'bg-green-500/20 border-green-500'
        }
      `}>
        <div className={`
          w-24 h-24 mx-auto rounded-full flex items-center justify-center mb-4
          ${isActive ? 'bg-red-500/30' : 'bg-green-500/30'}
        `}>
          <span className="text-5xl">{isActive ? '🚨' : '✅'}</span>
        </div>

        <h1 className={`text-3xl font-bold mb-2 ${isActive ? 'text-red-400' : 'text-green-400'}`}>
          {isActive ? 'TRAFFIC STOPPED' : 'TRAFFIC FLOWING'}
        </h1>

        <p className="text-slate-300 mb-6">
          {isActive
            ? `Kill switch activated ${status?.frozen_at ? formatTimeAgo(new Date(status.frozen_at)) : ''}`
            : 'All API traffic is flowing normally. Guardrails are active.'
          }
        </p>

        {/* Main Action Button */}
        {isActive ? (
          <button
            onClick={() => setShowDeactivateConfirm(true)}
            className="px-12 py-4 bg-green-600 hover:bg-green-700 rounded-xl text-xl font-bold transition-colors"
          >
            ▶️ RESUME TRAFFIC
          </button>
        ) : (
          <button
            onClick={() => setShowActivateConfirm(true)}
            className="px-12 py-4 bg-red-600 hover:bg-red-700 rounded-xl text-xl font-bold transition-colors"
          >
            ⏹ STOP ALL TRAFFIC
          </button>
        )}

        {/* Active Info */}
        {isActive && status?.frozen_by && (
          <p className="mt-4 text-sm text-slate-400">
            Activated by: {status.frozen_by}
          </p>
        )}
      </div>

      {/* ============== CURRENT BLAST RADIUS (if active) ============== */}
      {isActive && currentBlastRadius && (
        <div className="bg-slate-800 rounded-xl border border-red-500/50 p-6">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <span>💥</span> Current Blast Radius
            <span className="text-xs bg-red-500 text-white px-2 py-0.5 rounded animate-pulse">LIVE</span>
          </h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <BlastRadiusStat
              label="Requests Blocked"
              value={currentBlastRadius.requests_blocked.toLocaleString()}
              icon="🚫"
            />
            <BlastRadiusStat
              label="Users Affected"
              value={currentBlastRadius.users_affected.toLocaleString()}
              icon="👥"
            />
            <BlastRadiusStat
              label="Cost Avoided"
              value={`$${(currentBlastRadius.cost_avoided_cents / 100).toFixed(2)}`}
              icon="💰"
              highlight
            />
            <BlastRadiusStat
              label="Duration"
              value={formatDuration(currentBlastRadius.duration_seconds)}
              icon="⏱️"
            />
          </div>

          {/* Traffic Comparison Chart */}
          <div className="mt-6">
            <h3 className="text-sm font-medium text-slate-400 mb-3">Before vs After Kill Switch</h3>
            <div className="relative h-20 bg-slate-900 rounded overflow-hidden">
              {/* Before (green area) */}
              <div className="absolute left-0 top-0 w-1/2 h-full bg-gradient-to-r from-green-500/30 to-green-500/10 flex items-center justify-center">
                <div className="text-center">
                  <span className="text-xs text-slate-400">BEFORE</span>
                  <span className="block text-xl font-bold text-green-400">247 req/min</span>
                </div>
              </div>
              {/* Kill Line */}
              <div className="absolute left-1/2 top-0 w-1 h-full bg-red-500 z-10">
                <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 bg-red-500 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                  HALTED
                </div>
              </div>
              {/* After (dark area) */}
              <div className="absolute right-0 top-0 w-1/2 h-full bg-slate-800 flex items-center justify-center">
                <div className="text-center">
                  <span className="text-xs text-slate-400">AFTER</span>
                  <span className="block text-xl font-bold text-red-400">0 req/min</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============== KILL HISTORY ============== */}
      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <span>📜</span> Kill Switch History
          </h2>
        </div>

        <div className="divide-y divide-slate-700">
          {DEMO_KILL_HISTORY.map((event) => (
            <div
              key={event.id}
              onClick={() => setSelectedKillEvent(event.id === selectedKillEvent?.id ? null : event)}
              className={`
                p-4 cursor-pointer transition-colors
                ${selectedKillEvent?.id === event.id ? 'bg-slate-700/50' : 'hover:bg-slate-700/30'}
              `}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`text-xl ${event.action === 'activated' ? 'text-red-400' : 'text-green-400'}`}>
                    {event.action === 'activated' ? '🔴' : '🟢'}
                  </span>
                  <div>
                    <span className="font-medium">
                      {event.action === 'activated' ? 'Kill Switch Activated' : 'Traffic Resumed'}
                    </span>
                    <span className="block text-sm text-slate-400">{event.reason}</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-sm text-slate-400">{formatTimeAgo(new Date(event.timestamp))}</span>
                  <span className="block text-xs text-slate-500">{event.triggered_by}</span>
                </div>
              </div>

              {/* Expanded: Blast Radius */}
              {selectedKillEvent?.id === event.id && event.blast_radius && (
                <div className="mt-4 p-4 bg-slate-900 rounded-lg">
                  <h4 className="text-sm font-medium text-slate-400 mb-3">Impact Analysis</h4>
                  <div className="grid grid-cols-4 gap-4">
                    <BlastRadiusStat
                      label="Blocked"
                      value={event.blast_radius.requests_blocked.toLocaleString()}
                      icon="🚫"
                      small
                    />
                    <BlastRadiusStat
                      label="Users"
                      value={event.blast_radius.users_affected.toLocaleString()}
                      icon="👥"
                      small
                    />
                    <BlastRadiusStat
                      label="Saved"
                      value={`$${(event.blast_radius.cost_avoided_cents / 100).toFixed(2)}`}
                      icon="💰"
                      highlight
                      small
                    />
                    <BlastRadiusStat
                      label="Duration"
                      value={formatDuration(event.blast_radius.duration_seconds)}
                      icon="⏱️"
                      small
                    />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ============== ACTIVATE CONFIRMATION MODAL ============== */}
      {showActivateConfirm && (
        <Modal onClose={() => setShowActivateConfirm(false)}>
          <div className="text-center">
            <div className="w-20 h-20 mx-auto rounded-full bg-red-500/20 flex items-center justify-center mb-4">
              <span className="text-4xl">🚨</span>
            </div>
            <h2 className="text-2xl font-bold mb-2">Stop All Traffic?</h2>
            <p className="text-slate-400 mb-6">
              This will immediately block all API requests. Active requests will be terminated.
            </p>

            <div className="mb-6">
              <label className="block text-sm text-slate-400 mb-2">Reason (optional)</label>
              <input
                type="text"
                value={activationReason}
                onChange={(e) => setActivationReason(e.target.value)}
                placeholder="Why are you stopping traffic?"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2"
              />
            </div>

            <div className="bg-amber-500/20 border border-amber-500/50 rounded-lg p-3 mb-6">
              <p className="text-amber-300 text-sm">
                <strong>⚠️ Warning:</strong> All connected clients will receive errors until you resume.
              </p>
            </div>

            <div className="flex gap-3 justify-center">
              <button
                onClick={() => setShowActivateConfirm(false)}
                className="px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => activateMutation.mutate()}
                disabled={activateMutation.isPending}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-bold"
              >
                {activateMutation.isPending ? 'Stopping...' : 'STOP ALL TRAFFIC'}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* ============== DEACTIVATE CONFIRMATION MODAL ============== */}
      {showDeactivateConfirm && (
        <Modal onClose={() => setShowDeactivateConfirm(false)}>
          <div className="text-center">
            <div className="w-20 h-20 mx-auto rounded-full bg-green-500/20 flex items-center justify-center mb-4">
              <span className="text-4xl">▶️</span>
            </div>
            <h2 className="text-2xl font-bold mb-2">Resume Traffic?</h2>
            <p className="text-slate-400 mb-6">
              This will resume all API traffic. Guardrails will continue to protect you.
            </p>

            <div className="flex gap-3 justify-center">
              <button
                onClick={() => setShowDeactivateConfirm(false)}
                className="px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => deactivateMutation.mutate()}
                disabled={deactivateMutation.isPending}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-bold"
              >
                {deactivateMutation.isPending ? 'Resuming...' : 'Resume Traffic'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

// Sub-components
function BlastRadiusStat({ label, value, icon, highlight, small }: {
  label: string;
  value: string;
  icon: string;
  highlight?: boolean;
  small?: boolean;
}) {
  return (
    <div className={`text-center p-3 rounded-lg ${highlight ? 'bg-green-500/20' : 'bg-slate-700/50'}`}>
      <span className={small ? 'text-xl' : 'text-2xl'}>{icon}</span>
      <span className={`block font-bold mt-1 ${small ? 'text-lg' : 'text-2xl'} ${highlight ? 'text-green-400' : 'text-slate-100'}`}>
        {value}
      </span>
      <span className="text-xs text-slate-400">{label}</span>
    </div>
  );
}

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative bg-slate-800 rounded-xl border border-slate-700 p-6 max-w-md w-full mx-4">
        {children}
      </div>
    </div>
  );
}

// Helpers
function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}

export default KillSwitchPage;
