/**
 * Kill Switch Page - Ops-Grade Console (v3)
 *
 * HARD CONSTRAINTS (non-negotiable):
 * - Everything fits in 1366×768 viewport
 * - Zero scrolling
 * - Status strip: 56-64px max
 * - Demo banner: 32px
 * - History rows: 44px each
 * - Max 3 rows shown
 * - Font: 13-14px
 *
 * Layout:
 * ┌─────────────────────────────────────────────────┐
 * │ ⚠ Demo mode — actions do not affect live traffic│  32px
 * ├─────────────────────────────────────────────────┤
 * │ ● GREEN  Traffic flowing   Guardrails: ON [STOP]│  56px
 * ├─────────────────────────────────────────────────┤
 * │ Kill Switch History                    timezone │  40px
 * ├─────────────────────────────────────────────────┤
 * │ ▶ Traffic Resumed    reason             1h ago │  44px
 * │ ■ Kill Switch        reason             2h ago │  44px
 * │ ▶ Traffic Resumed    reason             1d ago │  44px
 * ├─────────────────────────────────────────────────┤
 * │ View full history →                            │  32px
 * └─────────────────────────────────────────────────┘
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { guardApi } from '../../api/guard';
import { logger } from '../../lib/consoleLogger';

interface KillEvent {
  id: string;
  action: 'activated' | 'deactivated';
  triggered_by: string;
  reason: string;
  timestamp: string;
  blast_radius?: {
    requests_blocked: number;
    cost_avoided_cents: number;
  };
}

// Demo kill history
const DEMO_KILL_HISTORY: KillEvent[] = [
  {
    id: 'kill_001',
    action: 'deactivated',
    triggered_by: 'admin@company.com',
    reason: 'Incident resolved — safe to resume',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 'kill_002',
    action: 'activated',
    triggered_by: 'auto-trigger',
    reason: 'Cost threshold exceeded ($50)',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    blast_radius: { requests_blocked: 1247, cost_avoided_cents: 2340 },
  },
  {
    id: 'kill_003',
    action: 'deactivated',
    triggered_by: 'admin@company.com',
    reason: 'Manual resume after investigation',
    timestamp: new Date(Date.now() - 86400000).toISOString(),
  },
];

export function KillSwitchPage() {
  const queryClient = useQueryClient();
  const [showActivateModal, setShowActivateModal] = useState(false);
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);
  const [showFullHistory, setShowFullHistory] = useState(false);
  const [activationReason, setActivationReason] = useState('');

  useEffect(() => {
    logger.componentMount('KillSwitchPage');
    return () => logger.componentUnmount('KillSwitchPage');
  }, []);

  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  // Fetch current status
  const { data: status } = useQuery({
    queryKey: ['guard', 'status'],
    queryFn: guardApi.getStatus,
    refetchInterval: 2000,
  });

  // Mutations
  const activateMutation = useMutation({
    mutationFn: guardApi.activateKillSwitch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guard'] });
      setShowActivateModal(false);
      setActivationReason('');
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: guardApi.deactivateKillSwitch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guard'] });
      setShowDeactivateModal(false);
    },
  });

  const isActive = status?.is_frozen ?? false;
  const historyToShow = showFullHistory ? DEMO_KILL_HISTORY : DEMO_KILL_HISTORY.slice(0, 3);

  return (
    <div className="p-3 max-w-4xl mx-auto text-[13px]">
      {/* ══════════ DEMO BANNER (32px) ══════════ */}
      <div className="h-8 flex items-center text-amber-400/80 mb-3">
        <span>⚠</span>
        <span className="ml-2">Demo mode — actions do not affect live traffic</span>
      </div>

      {/* ══════════ STATUS STRIP (56px) ══════════ */}
      <div className={`
        h-14 flex items-center justify-between px-4 rounded-lg mb-3
        border ${isActive ? 'border-red-500/50' : 'border-emerald-500/30'}
      `}>
        {/* Left: Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${isActive ? 'bg-red-500 animate-pulse' : 'bg-emerald-500'}`} />
            <span className={`font-bold ${isActive ? 'text-red-400' : 'text-emerald-400'}`}>
              {isActive ? 'STOPPED' : 'GREEN'}
            </span>
          </div>
          <span className="text-slate-400">
            {isActive ? 'All traffic halted' : 'Traffic flowing normally'}
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">
            Guardrails: <span className="text-emerald-400">ON</span>
          </span>
        </div>

        {/* Right: Action Button */}
        {isActive ? (
          <button
            onClick={() => setShowDeactivateModal(true)}
            className="h-9 px-4 bg-transparent border border-emerald-500/50 text-emerald-400
                       hover:bg-emerald-500/10 rounded text-[13px] font-medium transition-colors"
          >
            ▶ RESUME TRAFFIC
          </button>
        ) : (
          <button
            onClick={() => setShowActivateModal(true)}
            className="h-9 px-4 bg-transparent border border-red-500/50 text-red-400
                       hover:bg-red-500/10 rounded text-[13px] font-medium transition-colors"
          >
            ⏹ STOP TRAFFIC
          </button>
        )}
      </div>

      {/* ══════════ HISTORY HEADER (40px) ══════════ */}
      <div className="h-10 flex items-center justify-between px-3 border-b border-slate-700/50">
        <span className="font-medium text-slate-300">Kill Switch History</span>
        <span className="text-slate-500 text-[12px]">{timezone}</span>
      </div>

      {/* ══════════ HISTORY ROWS (44px each) ══════════ */}
      <div className="divide-y divide-slate-700/30">
        {historyToShow.map((event, idx) => (
          <HistoryRow key={event.id} event={event} isLatest={idx === 0} />
        ))}
      </div>

      {/* ══════════ VIEW FULL HISTORY (32px) ══════════ */}
      {!showFullHistory && DEMO_KILL_HISTORY.length > 3 && (
        <button
          onClick={() => setShowFullHistory(true)}
          className="h-8 w-full text-left px-3 text-blue-400 hover:text-blue-300 text-[12px]"
        >
          View full history →
        </button>
      )}

      {/* ══════════ ACTIVATE MODAL ══════════ */}
      {showActivateModal && (
        <Modal onClose={() => setShowActivateModal(false)}>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-red-400 text-xl">⏹</span>
              <h2 className="text-lg font-bold">Stop All Traffic?</h2>
            </div>

            <p className="text-slate-400 text-[13px]">
              This will immediately block all API traffic for all users.
            </p>

            <div>
              <label className="block text-[12px] text-slate-500 mb-1">Reason (required)</label>
              <input
                type="text"
                value={activationReason}
                onChange={(e) => setActivationReason(e.target.value)}
                placeholder="Why are you stopping traffic?"
                className="w-full h-9 bg-transparent border border-slate-600 rounded px-3 text-[13px]
                           focus:border-slate-500 focus:outline-none"
              />
            </div>

            <div className="text-[12px] text-red-400/80 border-l-2 border-red-500/50 pl-3">
              Nuclear action: All connected clients will receive errors until you resume.
            </div>

            <div className="flex gap-2 justify-end pt-2">
              <button
                onClick={() => setShowActivateModal(false)}
                className="h-9 px-4 text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <HoldToConfirmButton
                onConfirm={() => {
                  logger.userEvent('click', 'kill_switch_activated', { reason: activationReason });
                  activateMutation.mutate();
                }}
                disabled={!activationReason.trim() || activateMutation.isPending}
                isPending={activateMutation.isPending}
              />
            </div>
          </div>
        </Modal>
      )}

      {/* ══════════ DEACTIVATE MODAL ══════════ */}
      {showDeactivateModal && (
        <Modal onClose={() => setShowDeactivateModal(false)}>
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-emerald-400 text-xl">▶</span>
              <h2 className="text-lg font-bold">Resume Traffic?</h2>
            </div>

            <p className="text-slate-400 text-[13px]">
              Traffic will resume. Guardrails remain active.
            </p>

            <div className="flex gap-2 justify-end pt-2">
              <button
                onClick={() => setShowDeactivateModal(false)}
                className="h-9 px-4 text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => deactivateMutation.mutate()}
                disabled={deactivateMutation.isPending}
                className="h-9 px-4 bg-transparent border border-emerald-500/50 text-emerald-400
                           hover:bg-emerald-500/10 rounded text-[13px] font-medium transition-colors
                           disabled:opacity-50"
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

// ═══════════════════════════════════════════════════════════════════════════
// HISTORY ROW - 44px height, dense, informative
// ═══════════════════════════════════════════════════════════════════════════

function HistoryRow({ event, isLatest }: { event: KillEvent; isLatest: boolean }) {
  const isActivation = event.action === 'activated';
  const isAuto = event.triggered_by === 'auto-trigger';

  return (
    <div className={`
      h-11 flex items-center justify-between px-3
      border-l-3 ${isActivation ? 'border-l-red-500' : 'border-l-emerald-500'}
    `} style={{ borderLeftWidth: '3px' }}>
      {/* Left: Icon + Title + Reason */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <span className={isActivation ? 'text-red-400' : 'text-emerald-400'}>
          {isActivation ? '■' : '▶'}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-200 truncate">
              {isActivation ? 'Kill Switch Activated' : 'Traffic Resumed'}
            </span>
            {isAuto && (
              <span className="text-[10px] text-slate-500 border border-slate-600 px-1 rounded">auto</span>
            )}
          </div>
          <div className="flex items-center gap-2 text-[12px] text-slate-500 truncate">
            <span className="truncate">{event.reason}</span>
            {event.blast_radius && (
              <>
                <span>·</span>
                <span className="text-emerald-400/70">
                  {event.blast_radius.requests_blocked.toLocaleString()} blocked
                </span>
                <span>·</span>
                <span className="text-emerald-400/70">
                  ${(event.blast_radius.cost_avoided_cents / 100).toFixed(2)} saved
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Right: Time + Actor + Link */}
      <div className="flex items-center gap-4 flex-shrink-0 text-right">
        <div>
          <span className="text-slate-400">{formatTimeAgo(new Date(event.timestamp))}</span>
          <span className="block text-[11px] text-slate-600">{event.triggered_by}</span>
        </div>
        {isActivation && (
          <button className="text-blue-400/70 hover:text-blue-400 text-[12px]">
            View →
          </button>
        )}
        {!isActivation && (
          <span className="text-emerald-500/70">✓</span>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MODAL - Minimal, dark
// ═══════════════════════════════════════════════════════════════════════════

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <div className="relative bg-slate-900 border border-slate-700 rounded-lg p-5 max-w-sm w-full mx-4">
        {children}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// HOLD-TO-CONFIRM BUTTON
// ═══════════════════════════════════════════════════════════════════════════

function HoldToConfirmButton({
  onConfirm,
  disabled,
  isPending,
}: {
  onConfirm: () => void;
  disabled: boolean;
  isPending: boolean;
}) {
  const [progress, setProgress] = useState(0);
  const [isHolding, setIsHolding] = useState(false);
  const holdDuration = 1500;
  const intervalRef = React.useRef<number | null>(null);

  const startHold = useCallback(() => {
    if (disabled) return;
    setIsHolding(true);
    const startTime = Date.now();

    intervalRef.current = window.setInterval(() => {
      const elapsed = Date.now() - startTime;
      const newProgress = Math.min((elapsed / holdDuration) * 100, 100);
      setProgress(newProgress);

      if (newProgress >= 100) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        setIsHolding(false);
        setProgress(0);
        onConfirm();
      }
    }, 30);
  }, [disabled, onConfirm]);

  const stopHold = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsHolding(false);
    setProgress(0);
  }, []);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <button
      onMouseDown={startHold}
      onMouseUp={stopHold}
      onMouseLeave={stopHold}
      onTouchStart={startHold}
      onTouchEnd={stopHold}
      disabled={disabled}
      className={`
        relative h-9 px-4 rounded text-[13px] font-medium overflow-hidden
        ${disabled
          ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
          : 'bg-transparent border border-red-500/50 text-red-400 hover:bg-red-500/10'
        }
      `}
    >
      {isHolding && (
        <div
          className="absolute left-0 top-0 h-full bg-red-500/20 transition-none"
          style={{ width: `${progress}%` }}
        />
      )}
      <span className="relative">
        {isPending ? 'Stopping...' : isHolding ? 'Hold...' : 'HOLD TO STOP'}
      </span>
    </button>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════

function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'now';
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default KillSwitchPage;
