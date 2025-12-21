/**
 * Guard Dashboard - Customer AI Safety Console
 *
 * Comprehensive dashboard with:
 * - Current protection status
 * - Today's metrics
 * - Incident history with timeline
 * - Control buttons (Kill Switch, Resume)
 * - Replay functionality
 * - Real-time updates
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { guardApi, Incident, ReplayResult } from '../../api/guard';
import { ErrorBoundary } from '../../components/ErrorBoundary';
import { HealthIndicator } from '../../components/HealthIndicator';
import { circuitBreaker } from '../../lib/healthCheck';
import { logger } from '../../lib/consoleLogger';

// ============== STATUS SECTION ==============
// Navy-First: minimal backgrounds, status via text/border/icon only
type ProtectionStatus = 'protected' | 'at_risk' | 'stopped';
type ConsoleMode = 'live' | 'demo' | 'staging';

const STATUS_CONFIG: Record<ProtectionStatus, { label: string; color: string; bg: string; border: string; description: string }> = {
  protected: {
    label: 'PROTECTED',
    color: 'text-accent-success',
    bg: 'bg-navy-surface',
    border: 'border-accent-success/40',
    description: 'All systems nominal. AI guardrails active.',
  },
  at_risk: {
    label: 'AT RISK',
    color: 'text-accent-warning',
    bg: 'bg-navy-surface',
    border: 'border-accent-warning/40',
    description: 'Incidents detected. Review recommended.',
  },
  stopped: {
    label: 'TRAFFIC STOPPED',
    color: 'text-accent-danger',
    bg: 'bg-navy-surface',
    border: 'border-accent-danger/40',
    description: 'Kill switch active. All traffic halted.',
  },
};

const MODE_CONFIG: Record<ConsoleMode, { label: string; color: string }> = {
  live: { label: 'LIVE', color: 'text-green-400' },
  demo: { label: 'DEMO', color: 'text-amber-400' },
  staging: { label: 'STAGING', color: 'text-blue-400' },
};

// ============== MAIN COMPONENT ==============
interface GuardDashboardProps {
  onLogout?: () => void;
}

export function GuardDashboard({ onLogout }: GuardDashboardProps) {
  const queryClient = useQueryClient();
  const [selectedIncident, setSelectedIncident] = useState<string | null>(null);
  const [showKillConfirm, setShowKillConfirm] = useState(false);
  const [showResumeConfirm, setShowResumeConfirm] = useState(false);
  const [replayingCall, setReplayingCall] = useState<string | null>(null);

  // Component logging
  useEffect(() => {
    logger.componentMount('GuardDashboard');
    logger.info('GUARD', 'Dashboard loaded');
    return () => logger.componentUnmount('GuardDashboard');
  }, []);

  // Health monitoring is handled by GuardLayout
  // No duplicate initialization needed here

  // Default/fallback data
  const defaultStatus = {
    is_frozen: false,
    frozen_at: null,
    frozen_by: null,
    incidents_blocked_24h: 0,
    active_guardrails: ['max_cost_per_request', 'rate_limit_rpm', 'prompt_injection_block'],
    last_incident_time: null,
    mode: 'demo' as const,
  };

  const defaultSnapshot = {
    requests_today: 0,
    spend_today_cents: 0,
    incidents_prevented: 0,
    last_incident_time: null,
    cost_avoided_cents: 0,
  };

  // API Queries with error handling
  // staleTime prevents refetch on remount when data is still fresh
  // Backend caches status for 5s, snapshot for 10s
  const { data: status, isLoading: statusLoading, error: statusError } = useQuery({
    queryKey: ['guard', 'status'],
    queryFn: guardApi.getStatus,
    refetchInterval: 5000,
    staleTime: 4000, // Data is fresh for 4s (< 5s cache TTL)
    retry: 2,
    retryDelay: 1000,
  });

  const { data: snapshot, error: snapshotError } = useQuery({
    queryKey: ['guard', 'snapshot'],
    queryFn: guardApi.getTodaySnapshot,
    refetchInterval: 30000,
    staleTime: 10000, // Data is fresh for 10s (matches backend cache)
    retry: 2,
  });

  const { data: incidents, error: incidentsError } = useQuery({
    queryKey: ['guard', 'incidents'],
    queryFn: () => guardApi.getIncidents({ limit: 20 }),
    refetchInterval: 30000,
    staleTime: 10000, // Incidents refresh slower
    retry: 2,
  });

  const { data: timeline, error: timelineError } = useQuery({
    queryKey: ['guard', 'timeline', selectedIncident],
    queryFn: () => selectedIncident ? guardApi.getDecisionTimeline(selectedIncident) : null,
    enabled: !!selectedIncident,
    retry: 1,
  });

  // Use fallback data if API fails
  const safeStatus = status || defaultStatus;
  const safeSnapshot = snapshot || defaultSnapshot;
  const hasErrors = statusError || snapshotError;

  // Mutations
  const killMutation = useMutation({
    mutationFn: guardApi.activateKillSwitch,
    onSuccess: () => {
      logger.info('KILLSWITCH', 'Traffic stopped');
      queryClient.invalidateQueries({ queryKey: ['guard'] });
      setShowKillConfirm(false);
    },
    onError: (error) => {
      logger.error('KILLSWITCH', 'Failed to stop traffic', error);
      alert(`Failed to stop traffic: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const resumeMutation = useMutation({
    mutationFn: guardApi.deactivateKillSwitch,
    onSuccess: () => {
      logger.info('KILLSWITCH', 'Traffic resumed');
      queryClient.invalidateQueries({ queryKey: ['guard'] });
      setShowResumeConfirm(false);
    },
    onError: (error) => {
      logger.error('KILLSWITCH', 'Failed to resume traffic', error);
      alert(`Failed to resume traffic: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const [replayResult, setReplayResult] = useState<ReplayResult | null>(null);
  const [showReplayResult, setShowReplayResult] = useState(false);

  const replayMutation = useMutation({
    mutationFn: (callId: string) => {
      logger.info('REPLAY', `Starting replay for ${callId}`);
      return guardApi.replayCall(callId);
    },
    onSuccess: (data) => {
      logger.info('REPLAY', 'Replay completed', data);
      setReplayingCall(null);
      setReplayResult(data);
      setShowReplayResult(true);
    },
    onError: (error) => {
      logger.error('REPLAY', 'Replay failed', error);
      setReplayingCall(null);
      alert(`Replay failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  // Derived state
  const protectionStatus: ProtectionStatus = safeStatus.is_frozen
    ? 'stopped'
    : (safeSnapshot.incidents_prevented ?? 0) > 0
      ? 'at_risk'
      : 'protected';

  const statusInfo = STATUS_CONFIG[protectionStatus];
  const mode: ConsoleMode = (safeStatus as any)?.mode || 'demo';
  const modeInfo = MODE_CONFIG[mode];

  if (statusLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-navy-app">
        <div className="animate-spin w-12 h-12 border-4 border-accent-info border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <ErrorBoundary>
    <div className="min-h-screen bg-navy-app text-slate-100">
      {/* ============== HEADER ============== */}
      <header className="bg-navy-surface border-b border-navy-border px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-xl">🛡️</span>
            </div>
            <div>
              <h1 className="text-xl font-bold">AI Guard Console</h1>
              <p className="text-sm text-slate-400">Real-time AI Safety Monitoring</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Health Indicator */}
            <HealthIndicator showDetails={true} />

            {/* Mode Badge */}
            <div className={`px-3 py-1 rounded-full border ${modeInfo.color} border-current/50 bg-current/10 text-sm font-medium`}>
              <span className="inline-block w-2 h-2 rounded-full bg-current mr-2 animate-pulse" />
              {modeInfo.label}
            </div>

            {/* Logout Button */}
            {onLogout && (
              <button
                onClick={onLogout}
                className="px-3 py-1.5 text-sm text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              >
                Logout
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {/* ============== ERROR BANNER (if any) ============== */}
        {hasErrors && (
          <div className="bg-navy-surface border border-accent-warning/40 rounded-lg p-4 flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="font-medium text-accent-warning">Connection Issue</p>
              <p className="text-sm text-slate-400">
                Some data may be unavailable. Showing cached/default values.
              </p>
            </div>
            <button
              onClick={() => queryClient.invalidateQueries({ queryKey: ['guard'] })}
              className="ml-auto px-3 py-1 bg-navy-elevated hover:bg-navy-elevated/80 border border-accent-warning/30 text-accent-warning rounded text-sm"
            >
              Retry
            </button>
          </div>
        )}

        {/* ============== STATUS BANNER ============== */}
        <section className={`rounded-xl ${statusInfo.bg} border-2 ${statusInfo.border} p-6`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`w-16 h-16 rounded-full bg-navy-elevated border-2 ${statusInfo.border} flex items-center justify-center`}>
                <span className={`w-8 h-8 rounded-full ${statusInfo.color} animate-pulse`} style={{backgroundColor: 'currentColor', opacity: 0.8}} />
              </div>
              <div>
                <h2 className={`text-3xl font-bold ${statusInfo.color}`}>{statusInfo.label}</h2>
                <p className="text-slate-300">{statusInfo.description}</p>
                {/* Last Kill Switch Event */}
                <p className="text-xs text-slate-400 mt-1">
                  Last Kill Switch: {safeStatus.frozen_at
                    ? `${formatTimeAgo(new Date(safeStatus.frozen_at))} by ${safeStatus.frozen_by || 'system'}`
                    : 'Never activated'}
                </p>
              </div>
            </div>

            {/* Control Buttons - Navy-First: outline style with accent colors */}
            <div className="flex gap-3">
              {protectionStatus === 'stopped' ? (
                <button
                  onClick={() => setShowResumeConfirm(true)}
                  className="px-6 py-3 bg-navy-elevated hover:bg-navy-elevated/80 border-2 border-accent-success text-accent-success font-bold rounded-lg transition-colors flex items-center gap-2"
                >
                  <span>▶</span> RESUME TRAFFIC
                </button>
              ) : (
                <button
                  onClick={() => setShowKillConfirm(true)}
                  className="px-6 py-3 bg-navy-elevated hover:bg-navy-elevated/80 border-2 border-accent-danger text-accent-danger font-bold rounded-lg transition-colors flex items-center gap-2"
                >
                  <span>⏹</span> STOP ALL TRAFFIC
                </button>
              )}
            </div>
          </div>
        </section>

        {/* ============== METRICS CARDS ============== */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Requests Today"
            value={safeSnapshot.requests_today?.toLocaleString() ?? '0'}
            icon="📊"
          />
          <MetricCard
            label="Spend Today"
            value={`$${((safeSnapshot.spend_today_cents ?? 0) / 100).toFixed(2)}`}
            icon="💵"
          />
          <MetricCard
            label="Incidents Blocked"
            value={safeSnapshot.incidents_prevented?.toString() ?? '0'}
            icon="🛡️"
            highlight={(safeSnapshot.incidents_prevented ?? 0) > 0}
          />
          <MetricCard
            label="Cost Avoided"
            value={`$${((safeSnapshot.cost_avoided_cents ?? 0) / 100).toFixed(2)}`}
            icon="💰"
            highlight={(safeSnapshot.cost_avoided_cents ?? 0) > 0}
          />
        </section>

        {/* ============== ACTIVE GUARDRAILS ============== */}
        <section className="bg-navy-surface rounded-xl border border-navy-border p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>🔒</span> Active Guardrails
          </h3>
          <div className="flex flex-wrap gap-2">
            {safeStatus.active_guardrails?.map((guardrail, i) => (
              <span
                key={i}
                className="px-3 py-1 bg-navy-elevated text-accent-success border border-accent-success/30 rounded-full text-sm"
              >
                ✓ {guardrail.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </section>

        {/* ============== TWO COLUMN LAYOUT ============== */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* INCIDENT HISTORY */}
          <section className="bg-navy-surface rounded-xl border border-navy-border overflow-hidden">
            <div className="p-4 border-b border-navy-border flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <span>📋</span> Incident History
              </h3>
              <span className="text-sm text-slate-400">
                {incidents?.total ?? 0} total
              </span>
            </div>

            <div className="divide-y divide-navy-border max-h-96 overflow-y-auto">
              {incidents?.items?.length === 0 ? (
                <div className="p-8 text-center text-slate-400">
                  <span className="text-4xl mb-2 block">✨</span>
                  No incidents recorded
                </div>
              ) : (
                incidents?.items?.map((incident) => (
                  <IncidentRow
                    key={incident.id}
                    incident={incident}
                    isSelected={selectedIncident === incident.id}
                    onSelect={() => setSelectedIncident(incident.id)}
                    onReplay={(callId) => {
                      setReplayingCall(callId);
                      replayMutation.mutate(callId);
                    }}
                    isReplaying={replayingCall === incident.call_id}
                  />
                ))
              )}
            </div>
          </section>

          {/* DECISION TIMELINE */}
          <section className="bg-navy-surface rounded-xl border border-navy-border overflow-hidden">
            <div className="p-4 border-b border-navy-border">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <span>🔍</span> Decision Timeline
              </h3>
            </div>

            <div className="p-4 max-h-96 overflow-y-auto">
              {!selectedIncident ? (
                <div className="text-center text-slate-400 py-8">
                  <span className="text-4xl mb-2 block">👆</span>
                  Select an incident to view timeline
                </div>
              ) : !timeline ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Root Cause Badge - Navy-First: text/border emphasis only */}
                  {timeline.root_cause && (
                    <div className="bg-navy-elevated border border-accent-danger/40 rounded-lg p-3">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 border border-accent-danger text-accent-danger text-xs font-bold rounded">
                          ROOT CAUSE
                        </span>
                        <span className="text-accent-danger font-medium">{timeline.root_cause}</span>
                      </div>
                    </div>
                  )}

                  {/* Policy Evaluations - Navy-First: same bg, color via text */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-slate-400 uppercase">Policy Decisions</h4>
                    {timeline.policy_evaluations?.map((policy, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-2 rounded bg-navy-subtle"
                      >
                        <span className="text-sm">{policy.policy}</span>
                        <span className={`text-xs font-bold px-2 py-0.5 rounded border ${
                          policy.result === 'PASS' ? 'border-accent-success text-accent-success' :
                          policy.result === 'FAIL' ? 'border-accent-danger text-accent-danger' :
                          'border-accent-warning text-accent-warning'
                        }`}>
                          {policy.result}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Event Timeline */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-slate-400 uppercase">Event Log</h4>
                    <div className="relative pl-4 border-l-2 border-navy-border space-y-3">
                      {timeline.events?.map((event, i) => (
                        <div key={i} className="relative">
                          <div className="absolute -left-[21px] w-3 h-3 bg-accent-info rounded-full border-2 border-navy-surface" />
                          <div className="bg-navy-subtle rounded p-2">
                            <div className="flex justify-between text-xs">
                              <span className="font-medium text-accent-info">{event.event}</span>
                              <span className="text-slate-400">{event.duration_ms}ms</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="bg-navy-subtle rounded p-2">
                      <span className="text-slate-400">Model:</span>
                      <span className="ml-2 text-slate-200">{timeline.model}</span>
                    </div>
                    <div className="bg-navy-subtle rounded p-2">
                      <span className="text-slate-400">Latency:</span>
                      <span className="ml-2 text-slate-200">{timeline.latency_ms}ms</span>
                    </div>
                    <div className="bg-navy-subtle rounded p-2">
                      <span className="text-slate-400">Cost:</span>
                      <span className="ml-2 text-slate-200">${(timeline.cost_cents / 100).toFixed(4)}</span>
                    </div>
                    <div className="bg-navy-subtle rounded p-2">
                      <span className="text-slate-400">User:</span>
                      <span className="ml-2 text-slate-200">{timeline.user_id || 'N/A'}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>
        </div>

        {/* ============== QUICK ACTIONS ============== */}
        <section className="bg-navy-surface rounded-xl border border-navy-border p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span>⚡</span> Quick Actions
          </h3>
          <div className="flex flex-wrap gap-3">
            <ActionButton
              icon="🔄"
              label="Seed Demo Incident"
              onClick={() => guardApi.seedDemoIncident().then(() => queryClient.invalidateQueries({ queryKey: ['guard'] }))}
            />
            <ActionButton
              icon="📥"
              label="Export Report"
              onClick={() => selectedIncident && guardApi.downloadEvidenceReport(selectedIncident)}
              disabled={!selectedIncident}
            />
            <ActionButton
              icon="🔍"
              label="Search Incidents"
              onClick={() => {
                logger.userEvent('click', 'search_incidents');
                window.location.href = '/console/guard/incidents';
              }}
            />
            <ActionButton
              icon="⚙️"
              label="Configure Guardrails"
              onClick={() => {
                logger.userEvent('click', 'configure_guardrails');
                window.location.href = '/console/guard/settings';
              }}
            />
          </div>
        </section>
      </main>

      {/* ============== KILL SWITCH MODAL ============== */}
      {showKillConfirm && (
        <Modal onClose={() => setShowKillConfirm(false)}>
          <div className="text-center">
            <div className="w-16 h-16 bg-navy-elevated border-2 border-accent-danger/40 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">⚠️</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Stop All Traffic?</h3>
            <p className="text-slate-400 mb-6">
              This will immediately block all API requests. Active requests will be terminated.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => setShowKillConfirm(false)}
                className="px-6 py-2 bg-navy-elevated hover:bg-navy-subtle border border-navy-border rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => killMutation.mutate()}
                disabled={killMutation.isPending}
                className="px-6 py-2 bg-navy-elevated hover:bg-navy-subtle border-2 border-accent-danger text-accent-danger rounded-lg font-bold"
              >
                {killMutation.isPending ? 'Stopping...' : 'STOP ALL TRAFFIC'}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* ============== RESUME MODAL ============== */}
      {showResumeConfirm && (
        <Modal onClose={() => setShowResumeConfirm(false)}>
          <div className="text-center">
            <div className="w-16 h-16 bg-navy-elevated border-2 border-accent-success/40 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">▶️</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Resume Traffic?</h3>
            <p className="text-slate-400 mb-6">
              This will resume all API traffic. Guardrails will continue to protect you.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => setShowResumeConfirm(false)}
                className="px-6 py-2 bg-navy-elevated hover:bg-navy-subtle border border-navy-border rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => resumeMutation.mutate()}
                disabled={resumeMutation.isPending}
                className="px-6 py-2 bg-navy-elevated hover:bg-navy-subtle border-2 border-accent-success text-accent-success rounded-lg font-bold"
              >
                {resumeMutation.isPending ? 'Resuming...' : 'Resume Traffic'}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Replay Result Modal */}
      {showReplayResult && replayResult && (
        <Modal onClose={() => setShowReplayResult(false)}>
          <div className="p-6 max-w-md">
            <h3 className="text-xl font-bold text-slate-100 mb-4 flex items-center gap-2">
              {replayResult.match_level === 'exact' ? '✅' : '⚠️'} Replay Result
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Call ID</span>
                <span className="font-mono text-slate-200">{replayResult.call_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Match Level</span>
                <span className={`font-bold ${replayResult.match_level === 'exact' ? 'text-accent-success' : 'text-accent-warning'}`}>
                  {replayResult.match_level?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Policy Match</span>
                <span className={replayResult.policy_match ? 'text-accent-success' : 'text-accent-warning'}>
                  {replayResult.policy_match ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Model Drift</span>
                <span className={!replayResult.model_drift_detected ? 'text-accent-success' : 'text-accent-danger'}>
                  {replayResult.model_drift_detected ? 'Detected' : 'None'}
                </span>
              </div>
              {replayResult.details?.message && (
                <div className="mt-4 p-3 bg-navy-subtle rounded-lg">
                  <p className="text-slate-200">{replayResult.details.message}</p>
                </div>
              )}
            </div>
            <button
              onClick={() => setShowReplayResult(false)}
              className="w-full mt-6 px-4 py-2 bg-navy-elevated hover:bg-navy-subtle border border-accent-info text-accent-info rounded-lg font-medium"
            >
              Close
            </button>
          </div>
        </Modal>
      )}
    </div>
    </ErrorBoundary>
  );
}

// ============== SUB-COMPONENTS ==============

function MetricCard({ label, value, icon, highlight }: {
  label: string;
  value: string;
  icon: string;
  highlight?: boolean;
}) {
  return (
    <div className={`bg-navy-surface rounded-xl border p-4 ${highlight ? 'border-accent-success/50' : 'border-navy-border'}`}>
      <div className="flex items-center gap-2 mb-2">
        <span>{icon}</span>
        <span className="text-sm text-slate-400">{label}</span>
      </div>
      <div className={`text-2xl font-bold ${highlight ? 'text-accent-success' : 'text-slate-100'}`}>
        {value}
      </div>
    </div>
  );
}

function IncidentRow({ incident, isSelected, onSelect, onReplay, isReplaying }: {
  incident: Incident;
  isSelected: boolean;
  onSelect: () => void;
  onReplay: (callId: string) => void;
  isReplaying: boolean;
}) {
  // Navy-First: severity shown via text color, not background
  const severityColors = {
    critical: 'text-accent-danger',
    high: 'text-orange-400',
    medium: 'text-accent-warning',
    low: 'text-accent-info',
  };

  return (
    <div
      className={`p-4 cursor-pointer transition-colors ${isSelected ? 'bg-navy-elevated' : 'hover:bg-navy-subtle'}`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`w-2 h-2 rounded-full ${severityColors[incident.severity]} bg-current`} />
            <span className="font-medium">{incident.title}</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span>{new Date(incident.started_at).toLocaleString()}</span>
            <span className="px-1.5 py-0.5 bg-navy-inset rounded">{incident.trigger_type}</span>
            <span className="text-accent-success">+${(incident.cost_avoided_cents / 100).toFixed(2)} saved</span>
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (incident.call_id) {
              onReplay(incident.call_id);
            }
          }}
          disabled={isReplaying || !incident.call_id}
          title={!incident.call_id ? 'No call associated with this incident' : 'Replay this call'}
          className="px-3 py-1 bg-navy-elevated hover:bg-navy-subtle border border-accent-info/50 text-accent-info disabled:border-navy-border disabled:text-slate-500 disabled:cursor-not-allowed rounded text-xs font-medium transition-colors"
        >
          {isReplaying ? '⏳' : '🔄'} Replay
        </button>
      </div>
    </div>
  );
}

function ActionButton({ icon, label, onClick, disabled }: {
  icon: string;
  label: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="px-4 py-2 bg-navy-elevated hover:bg-navy-subtle border border-navy-border disabled:opacity-50 disabled:cursor-not-allowed rounded-lg flex items-center gap-2 transition-colors"
    >
      <span>{icon}</span>
      <span>{label}</span>
    </button>
  );
}

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <div className="relative bg-navy-surface rounded-xl border border-navy-border p-6 max-w-md w-full mx-4">
        {children}
      </div>
    </div>
  );
}

// Helper: Format time ago
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

export default GuardDashboard;
