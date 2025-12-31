/**
 * IncidentDetailPage - O3 Accountability Page for Incidents
 *
 * Phase A-Fix-2: Closes V-001 (PIN-187)
 *
 * This restructures the modal content into a proper O3 page.
 * Enforces PIN-186 invariants:
 * - INV-3: Cross-links land on O3
 * - INV-4: O5 modals are confirm-only (no content/navigation)
 * - INV-5: Breadcrumb shows Incidents > INC-xxx
 * - INV-6: Values truncated by default
 *
 * NAVIGATION LIVES HERE (O3), NOT IN MODALS
 * O5 MODALS ARE CONFIRM-ONLY
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Play,
  FileText,
  ExternalLink,
  Shield,
  Activity,
} from 'lucide-react';
import { guardApi, DecisionTimelineResponse, ReplayResult } from '@/api/guard';
import { DecisionTimeline } from './DecisionTimeline';
import { CanonicalBreadcrumb } from '@/components/navigation/CanonicalBreadcrumb';
import { truncateValue } from '@/utils/truncateValue';
import { logger } from '@/lib/consoleLogger';

// =============================================================================
// Severity Configuration - Navy-First
// =============================================================================

const SEVERITY_CONFIG = {
  critical: { label: 'Critical', color: 'text-red-400', border: 'border-red-500' },
  high: { label: 'High', color: 'text-amber-400', border: 'border-amber-500' },
  medium: { label: 'Medium', color: 'text-yellow-400', border: 'border-yellow-500' },
  low: { label: 'Low', color: 'text-slate-400', border: 'border-slate-500' },
};

// =============================================================================
// V-003 Fix: Local Breadcrumb removed - using CanonicalBreadcrumb
// =============================================================================

// =============================================================================
// Section Component
// =============================================================================

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-6">
      <h2 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3 border-b border-slate-700 pb-2">
        {title}
      </h2>
      {children}
    </div>
  );
}

// =============================================================================
// Replay Confirmation Modal (O5 - Terminal)
// =============================================================================

function ReplayConfirmModal({
  incidentId,
  onConfirm,
  onCancel,
  isLoading,
}: {
  incidentId: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-white mb-4">Confirm Replay</h3>
        <div className="space-y-3 mb-6">
          <p className="text-slate-300 text-sm">
            This will replay the incident execution to verify determinism.
          </p>
          <div className="bg-slate-900 rounded p-3 text-sm">
            <span className="text-slate-500">Incident:</span>{' '}
            <span className="font-mono text-white">{incidentId.slice(0, 16)}...</span>
          </div>
        </div>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white text-sm transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white text-sm transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading && (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            )}
            {isLoading ? 'Replaying...' : 'Confirm Replay'}
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Replay Results Modal (O5 - Read-only summary)
// =============================================================================

function ReplayResultsModal({
  result,
  onClose,
}: {
  result: ReplayResult;
  onClose: () => void;
}) {
  const isDeterministic = result.match_level === 'exact' || result.match_level === 'logical';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-white mb-4">Replay Complete</h3>
        <div className="space-y-4 mb-6">
          {/* Verdict */}
          <div
            className={`p-4 rounded-lg border-2 text-center ${
              isDeterministic ? 'border-green-500/40' : 'border-red-500/40'
            }`}
          >
            <div className={`text-xl font-bold ${isDeterministic ? 'text-green-400' : 'text-red-400'}`}>
              {isDeterministic ? '✓ DETERMINISTIC' : '✗ NON-DETERMINISTIC'}
            </div>
            <div className="text-sm text-slate-400 mt-1">
              {isDeterministic
                ? 'Execution is reproducible'
                : 'Outputs differ - review required'}
            </div>
          </div>
          {/* Summary */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-slate-500">Match Level</span>
              <p className="text-white capitalize">{result.match_level}</p>
            </div>
            <div>
              <span className="text-slate-500">Policy Match</span>
              <p className={result.policy_match ? 'text-green-400' : 'text-red-400'}>
                {result.policy_match ? 'Yes' : 'No'}
              </p>
            </div>
          </div>
        </div>
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white text-sm transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function IncidentDetailPage() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const navigate = useNavigate();

  const [showReplayConfirm, setShowReplayConfirm] = useState(false);
  const [replayResult, setReplayResult] = useState<ReplayResult | null>(null);

  // Fetch timeline data
  const {
    data: timeline,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['guard', 'incidents', incidentId, 'timeline'],
    queryFn: () => guardApi.getDecisionTimeline(incidentId!),
    enabled: !!incidentId,
  });

  // Log page mount
  useEffect(() => {
    logger.componentMount('IncidentDetailPage');
    logger.info('INCIDENT_DETAIL', 'Page loaded', { incident_id: incidentId });
    return () => logger.componentUnmount('IncidentDetailPage');
  }, [incidentId]);

  // Replay mutation
  const replayMutation = useMutation({
    mutationFn: (callId: string) => guardApi.replayCall(callId),
    onSuccess: (result) => {
      logger.info('INCIDENT_DETAIL', 'Replay completed', { match_level: result.match_level });
      setShowReplayConfirm(false);
      setReplayResult(result);
    },
    onError: (error) => {
      logger.error('INCIDENT_DETAIL', 'Replay failed', error);
      setShowReplayConfirm(false);
    },
  });

  // Handle replay action
  const handleReplay = () => {
    const callId = timeline?.call_id || timeline?.incident_id || incidentId;
    if (callId) {
      replayMutation.mutate(callId);
    }
  };

  // Handle export action
  const handleExport = async () => {
    if (!timeline) return;
    try {
      await guardApi.downloadEvidenceReport(timeline.incident_id, {
        includeReplay: true,
        includePrevention: true,
        isDemo: true,
      });
      logger.info('INCIDENT_DETAIL', 'Evidence exported');
    } catch (error) {
      logger.error('INCIDENT_DETAIL', 'Export failed', error);
    }
  };

  // Determine severity
  const isCritical = timeline?.events.some(
    (e) => e.data?.action === 'block' || e.data?.action === 'freeze'
  );
  const failedPolicies = timeline?.policy_evaluations.filter((pe) => pe.result === 'FAIL') || [];
  const severity = isCritical ? 'critical' : failedPolicies.length > 0 ? 'high' : 'medium';
  const severityConfig = SEVERITY_CONFIG[severity];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-4xl mx-auto">
          <CanonicalBreadcrumb
            root={{ label: 'Incidents', path: '/guard/incidents' }}
            entity={{ label: incidentId || '', id: incidentId, path: `/guard/incidents/${incidentId}` }}
          />
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !timeline) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-4xl mx-auto">
          <CanonicalBreadcrumb
            root={{ label: 'Incidents', path: '/guard/incidents' }}
            entity={{ label: incidentId || '', id: incidentId, path: `/guard/incidents/${incidentId}` }}
          />
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-8 text-center">
            <AlertTriangle className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-white mb-2">Incident Not Found</h2>
            <p className="text-slate-400 mb-4">The requested incident could not be loaded.</p>
            <button
              onClick={() => navigate('/guard/incidents')}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white text-sm"
            >
              Back to Incidents
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* V-003 Fix: Using CanonicalBreadcrumb (INV-5) */}
        <CanonicalBreadcrumb
          root={{ label: 'Incidents', path: '/guard/incidents' }}
          entity={{ label: timeline.incident_id, id: timeline.incident_id, path: `/guard/incidents/${timeline.incident_id}` }}
        />

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={() => navigate('/guard/incidents')}
                className="p-1 hover:bg-slate-800 rounded"
              >
                <ArrowLeft className="w-5 h-5 text-slate-400" />
              </button>
              <Shield className="w-6 h-6 text-slate-500" />
              <h1 className="text-2xl font-bold text-white">Incident Detail</h1>
            </div>
            <p className="text-slate-400 text-sm">O3 Accountability View - PIN-186 Compliant</p>
          </div>

          {/* Severity Badge */}
          <div
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${severityConfig.border}/30`}
          >
            {isCritical ? (
              <XCircle className={`w-5 h-5 ${severityConfig.color}`} />
            ) : failedPolicies.length > 0 ? (
              <AlertTriangle className={`w-5 h-5 ${severityConfig.color}`} />
            ) : (
              <CheckCircle className={`w-5 h-5 ${severityConfig.color}`} />
            )}
            <span className={`font-bold text-sm ${severityConfig.color}`}>
              {severityConfig.label.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          {/* INCIDENT IDENTITY */}
          <Section title="Incident Identity">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-slate-500">Incident ID</span>
                <p className="font-mono text-white mt-1">{timeline.incident_id}</p>
              </div>
              <div>
                <span className="text-slate-500">Timestamp</span>
                <p className="text-white mt-1">
                  {new Date(timeline.events[0]?.timestamp || Date.now()).toLocaleString()}
                </p>
              </div>
              <div>
                <span className="text-slate-500">Model</span>
                <p className="text-white mt-1">{timeline.model}</p>
              </div>
              <div>
                <span className="text-slate-500">Latency</span>
                <p className="text-white mt-1">{timeline.latency_ms}ms</p>
              </div>
            </div>
          </Section>

          {/* VERDICT */}
          <Section title="Verdict">
            <div
              className={`p-4 rounded-lg border-l-4 ${severityConfig.border} bg-slate-900/50`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium border ${
                      isCritical
                        ? 'border-red-500/40 text-red-400'
                        : failedPolicies.length > 0
                          ? 'border-amber-500/40 text-amber-400'
                          : 'border-green-500/40 text-green-400'
                    }`}
                  >
                    {isCritical
                      ? 'Traffic Blocked'
                      : failedPolicies.length > 0
                        ? 'Policy Gap'
                        : 'OK'}
                  </span>
                  <span className="text-slate-400 text-sm">
                    {failedPolicies.length} of {timeline.policy_evaluations.length} policies failed
                  </span>
                </div>
                <span className="text-slate-500 text-sm">
                  Cost: ${(timeline.cost_cents / 100).toFixed(4)}
                </span>
              </div>
            </div>
          </Section>

          {/* ROOT CAUSE */}
          {timeline.root_cause_badge && (
            <Section title="Root Cause">
              <div className="bg-slate-900/50 border-l-4 border-amber-500 p-4 rounded-r">
                <p className="font-medium text-amber-400 mb-2">{timeline.root_cause_badge}</p>
                <p className="text-slate-400 text-sm">{timeline.root_cause}</p>
              </div>
            </Section>
          )}

          {/* CROSS-ENTITY NAVIGATION - Lives on O3 page, NOT in modals */}
          <Section title="Related Entities">
            <div className="flex flex-wrap gap-3">
              {timeline.call_id && (
                <Link
                  to={`/traces/${timeline.call_id}`}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white text-sm transition-colors"
                >
                  <Activity className="w-4 h-4" />
                  View Trace
                  <ExternalLink className="w-3 h-3 text-slate-400" />
                </Link>
              )}
              {/* Future: Link to Run when run_id is available */}
            </div>
          </Section>

          {/* ACTIONS - O5 triggers, not navigation */}
          <Section title="Actions">
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => setShowReplayConfirm(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white text-sm transition-colors"
              >
                <Play className="w-4 h-4" />
                Replay Execution
              </button>
              <button
                onClick={handleExport}
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white text-sm transition-colors"
              >
                <FileText className="w-4 h-4" />
                Export Evidence
              </button>
            </div>
          </Section>

          {/* POLICY EVALUATIONS & TIMELINE - Inline on O3 */}
          <Section title="Decision Timeline">
            <DecisionTimeline timeline={timeline} />
          </Section>
        </div>
      </div>

      {/* O5 Modal: Replay Confirmation (confirm-only, no navigation) */}
      {showReplayConfirm && (
        <ReplayConfirmModal
          incidentId={timeline.incident_id}
          onConfirm={handleReplay}
          onCancel={() => setShowReplayConfirm(false)}
          isLoading={replayMutation.isPending}
        />
      )}

      {/* O5 Modal: Replay Results (read-only summary, no navigation) */}
      {replayResult && (
        <ReplayResultsModal result={replayResult} onClose={() => setReplayResult(null)} />
      )}
    </div>
  );
}
