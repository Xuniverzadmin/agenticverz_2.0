/**
 * UcUatResultCard — Individual UC Mapping Result Card
 *
 * Layer: L1 — Product Experience (UI)
 * AUDIENCE: FOUNDER
 * Role: Render a single UC operation manifest entry with decision type badge and evidence
 * Reference: UC_CODEBASE_ELICITATION_VALIDATION_UAT_TASKPACK_2026-02-15
 * artifact_class: CODE
 */

import { useState } from 'react';
import type { ManifestEntry, ScenarioResult } from './ucUatClient';

// ============================================================================
// Decision Badge
// ============================================================================

const DECISION_COLORS: Record<string, string> = {
  ASSIGN: 'bg-green-600 text-white',
  SPLIT: 'bg-yellow-500 text-black',
  HOLD: 'bg-gray-500 text-white',
};

function DecisionBadge({ type }: { type: string }) {
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${DECISION_COLORS[type] || 'bg-gray-400 text-white'}`}
    >
      {type}
    </span>
  );
}

// ============================================================================
// Scenario Status Indicator
// ============================================================================

function ScenarioStatusDot({ status }: { status: string }) {
  const color =
    status === 'PASS'
      ? 'bg-green-400'
      : status === 'FAIL'
        ? 'bg-red-400'
        : 'bg-gray-400';
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${color}`} />;
}

// ============================================================================
// Result Card
// ============================================================================

interface Props {
  entry: ManifestEntry;
  scenarios: ScenarioResult[];
  onSelectEvidence: (entry: ManifestEntry) => void;
}

export function UcUatResultCard({ entry, scenarios, onSelectEvidence }: Props) {
  const [expanded, setExpanded] = useState(false);

  const relatedScenarios = scenarios.filter((s) => s.uc_id === entry.uc_id);
  const hasFailures = relatedScenarios.some((s) => s.status === 'FAIL');

  return (
    <div
      className={`border rounded-lg p-4 transition-colors ${
        hasFailures
          ? 'border-red-500/50 bg-red-950/20'
          : 'border-gray-700 bg-gray-800/50'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <DecisionBadge type={entry.decision_type} />
          <span className="font-mono text-sm text-gray-200">
            {entry.uc_id}
          </span>
          <span className="text-gray-400 text-sm">{entry.operation_name}</span>
        </div>
        <div className="flex items-center gap-2">
          {relatedScenarios.length > 0 && (
            <div className="flex items-center gap-1">
              {relatedScenarios.map((s) => (
                <ScenarioStatusDot key={s.test_id} status={s.status} />
              ))}
            </div>
          )}
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-gray-400 hover:text-gray-200 text-xs px-2 py-1"
          >
            {expanded ? 'Collapse' : 'Details'}
          </button>
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-gray-700 space-y-2">
          <div className="text-xs text-gray-400">
            <span className="font-semibold text-gray-300">Route:</span>{' '}
            <span className="font-mono">{entry.route_path || 'N/A'}</span>
          </div>
          <div className="text-xs text-gray-400">
            <span className="font-semibold text-gray-300">Handler:</span>{' '}
            <span className="font-mono">{entry.handler_file}</span>
          </div>
          {entry.engine_or_driver_files.length > 0 && (
            <div className="text-xs text-gray-400">
              <span className="font-semibold text-gray-300">
                Engine/Driver:
              </span>
              <ul className="ml-4 mt-1">
                {entry.engine_or_driver_files.map((f) => (
                  <li key={f} className="font-mono">
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {entry.hold_status && (
            <div className="text-xs text-gray-400">
              <span className="font-semibold text-gray-300">Hold Status:</span>{' '}
              <span className="font-mono text-yellow-400">
                {entry.hold_status}
              </span>
            </div>
          )}
          {entry.test_refs.length > 0 && (
            <div className="text-xs text-gray-400">
              <span className="font-semibold text-gray-300">Test Refs:</span>
              <ul className="ml-4 mt-1">
                {entry.test_refs.map((t) => (
                  <li key={t} className="font-mono">
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Scenario Results */}
          {relatedScenarios.length > 0 && (
            <div className="mt-2">
              <span className="text-xs font-semibold text-gray-300">
                Scenarios:
              </span>
              <div className="mt-1 space-y-1">
                {relatedScenarios.map((s) => (
                  <div
                    key={s.test_id}
                    className="flex items-center gap-2 text-xs"
                  >
                    <ScenarioStatusDot status={s.status} />
                    <span className="font-mono text-gray-300">
                      {s.test_id}
                    </span>
                    <span className="text-gray-500">{s.test_name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={() => onSelectEvidence(entry)}
            className="mt-2 text-xs text-blue-400 hover:text-blue-300 underline"
          >
            View Evidence
          </button>
        </div>
      )}
    </div>
  );
}
