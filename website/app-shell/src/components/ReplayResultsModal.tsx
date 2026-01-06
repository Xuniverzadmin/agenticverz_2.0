/**
 * Replay Evidence Modal - M4 Golden Replay Evidence
 *
 * P2FC-3: Surface determinism verification as EVIDENCE in Incident Console.
 *
 * This is evidence-grade, not debug-grade:
 * - Immutable replay artifact
 * - Determinism badge
 * - Trace ID visible
 * - Read-only (no actions)
 *
 * Related PINs:
 * - PIN-127: Replay determinism proof
 * - PIN-131: Evidence trail protocol
 * - PIN-117: Evidence report enhancements
 */

import React from 'react';
import { ReplayResult } from '@/api/guard';

interface ReplayEvidenceModalProps {
  result: ReplayResult;
  incidentId?: string;
  incidentTitle?: string;
  onClose: () => void;
}

// Match level to verdict display
const MATCH_CONFIG = {
  exact: {
    verdict: 'DETERMINISTIC',
    verdictColor: 'text-accent-success',
    borderColor: 'border-accent-success/40',
    icon: '✓',
    description: 'Byte-for-byte exact match - evidence-grade',
  },
  logical: {
    verdict: 'DETERMINISTIC',
    verdictColor: 'text-accent-success',
    borderColor: 'border-accent-success/40',
    icon: '✓',
    description: 'Policy decisions match - evidence-grade',
  },
  semantic: {
    verdict: 'EQUIVALENT',
    verdictColor: 'text-accent-info',
    borderColor: 'border-accent-info/40',
    icon: '~',
    description: 'Semantically equivalent output',
  },
  mismatch: {
    verdict: 'NON-DETERMINISTIC',
    verdictColor: 'text-accent-danger',
    borderColor: 'border-accent-danger/40',
    icon: '✗',
    description: 'Outputs differ - review required',
  },
};

export function ReplayResultsModal({ result, incidentId, incidentTitle, onClose }: ReplayEvidenceModalProps) {
  const matchConfig = MATCH_CONFIG[result.match_level] || MATCH_CONFIG.mismatch;
  const isDeterministic = result.match_level === 'exact' || result.match_level === 'logical';

  // Compare helper - shows if values match
  const CompareCell = ({
    original,
    replay,
    format,
  }: {
    original: string | number;
    replay: string | number;
    format?: (v: string | number) => string;
  }) => {
    const origStr = format ? format(original) : String(original);
    const replayStr = format ? format(replay) : String(replay);
    const match = origStr === replayStr;

    return (
      <>
        <td className="px-4 py-3 text-slate-300 font-mono text-sm">{origStr}</td>
        <td className="px-4 py-3 text-slate-300 font-mono text-sm">{replayStr}</td>
        <td className="px-4 py-3 text-center">
          {match ? (
            <span className="text-accent-success">✓</span>
          ) : (
            <span className="text-accent-warning">~</span>
          )}
        </td>
      </>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
      <div className="bg-navy-surface border border-navy-border rounded-xl w-full max-w-2xl overflow-hidden">
        {/* Header - Evidence framing */}
        <div className="flex items-center justify-between p-4 border-b border-navy-border">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-white">Replay Evidence</h2>
            {/* Determinism Badge */}
            {isDeterministic && (
              <span className="px-2 py-1 text-xs font-medium rounded bg-accent-success/20 text-accent-success border border-accent-success/40">
                Deterministic ✓
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Evidence Metadata */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-navy-elevated rounded-lg text-sm">
            {/* Trace ID */}
            <div>
              <span className="text-slate-500 text-xs uppercase tracking-wide">Trace ID</span>
              <p className="font-mono text-slate-300 mt-1">
                {result.call_id || incidentId || 'N/A'}
              </p>
            </div>
            {/* Timestamp */}
            <div>
              <span className="text-slate-500 text-xs uppercase tracking-wide">Timestamp</span>
              <p className="font-mono text-slate-300 mt-1">
                {result.original.timestamp || new Date().toISOString()}
              </p>
            </div>
            {/* Incident */}
            {incidentTitle && (
              <div className="col-span-2">
                <span className="text-slate-500 text-xs uppercase tracking-wide">Incident</span>
                <p className="text-slate-300 mt-1">"{incidentTitle}"</p>
              </div>
            )}
          </div>

          {/* Comparison Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-xs text-slate-500 uppercase tracking-wide">
                  <th className="px-4 py-2 text-left">Metric</th>
                  <th className="px-4 py-2 text-left">Original</th>
                  <th className="px-4 py-2 text-left">Replay</th>
                  <th className="px-4 py-2 text-center">Match</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-border">
                <tr className="hover:bg-navy-elevated transition-colors">
                  <td className="px-4 py-3 text-slate-400">Tokens</td>
                  <CompareCell
                    original={result.original.tokens_used}
                    replay={result.replay.tokens_used}
                    format={(v) => String(v).toLocaleString()}
                  />
                </tr>
                <tr className="hover:bg-navy-elevated transition-colors">
                  <td className="px-4 py-3 text-slate-400">Cost</td>
                  <CompareCell
                    original={result.original.cost_cents}
                    replay={result.replay.cost_cents}
                    format={(v) => `$${(Number(v) / 100).toFixed(2)}`}
                  />
                </tr>
                <tr className="hover:bg-navy-elevated transition-colors">
                  <td className="px-4 py-3 text-slate-400">Model</td>
                  <CompareCell
                    original={result.original.model_id}
                    replay={result.replay.model_id}
                  />
                </tr>
                <tr className="hover:bg-navy-elevated transition-colors">
                  <td className="px-4 py-3 text-slate-400">Output Hash</td>
                  <CompareCell
                    original={result.original.response_hash.slice(0, 8) + '...'}
                    replay={result.replay.response_hash.slice(0, 8) + '...'}
                  />
                </tr>
              </tbody>
            </table>
          </div>

          {/* Policy Match */}
          <div className="flex items-center justify-between p-4 bg-navy-elevated rounded-lg">
            <span className="text-slate-400">Policy Match</span>
            <span className={result.policy_match ? 'text-accent-success' : 'text-accent-danger'}>
              {result.policy_match ? '✓ Policies matched' : '✗ Policy mismatch'}
            </span>
          </div>

          {/* Model Drift Warning */}
          {result.model_drift_detected && (
            <div className="p-4 border-l-4 border-accent-warning bg-navy-elevated rounded-r-lg">
              <span className="text-accent-warning font-medium">Model Drift Detected</span>
              <p className="text-sm text-slate-400 mt-1">
                The model behavior has changed since the original execution.
              </p>
            </div>
          )}

          {/* Verdict */}
          <div className={`p-4 rounded-lg border-2 text-center ${matchConfig.borderColor}`}>
            <div className={`text-2xl font-bold ${matchConfig.verdictColor}`}>
              {matchConfig.icon} {matchConfig.verdict}
            </div>
            <div className="text-sm text-slate-400 mt-1">
              {matchConfig.description}
            </div>
          </div>

          {/* Evidence Integrity Notice */}
          <div className="text-xs text-slate-500 text-center border-t border-navy-border pt-4">
            This replay is immutable and evidence-grade. It cannot be modified or re-executed.
          </div>
        </div>

        {/* Footer - Read-only, no actions */}
        <div className="flex justify-end gap-3 p-4 border-t border-navy-border">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-navy-elevated hover:bg-navy-subtle border border-navy-border text-slate-300 rounded-lg text-sm font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default ReplayResultsModal;
