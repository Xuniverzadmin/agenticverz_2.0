/**
 * UcUatConsolePage — UC Codebase Elicitation UAT Console
 *
 * Layer: L1 — Product Experience (UI)
 * AUDIENCE: FOUNDER
 * Role: Main UAT console page for UC mapping validation and scenario execution
 * Reference: UC_CODEBASE_ELICITATION_VALIDATION_UAT_TASKPACK_2026-02-15
 * artifact_class: CODE
 *
 * Displays:
 * - Summary statistics (ASSIGN/SPLIT/HOLD counts, scenario pass/fail)
 * - Filter bar (ALL, ASSIGN, SPLIT, HOLD, FAILED_LAST_RUN)
 * - Result cards for each manifest entry
 * - Evidence panel sidebar
 */

import { useEffect, useState, useMemo } from 'react';
import {
  fetchManifest,
  fetchScenarios,
  filterEntries,
  computeStats,
  type ManifestEntry,
  type ScenarioResult,
  type UatState,
} from './ucUatClient';
import { UcUatResultCard } from './UcUatResultCard';
import { UcUatEvidencePanel } from './UcUatEvidencePanel';

// ============================================================================
// Filter Tabs
// ============================================================================

type FilterKey = UatState['filter'];

const FILTER_TABS: { key: FilterKey; label: string }[] = [
  { key: 'ALL', label: 'All' },
  { key: 'ASSIGN', label: 'Assign' },
  { key: 'SPLIT', label: 'Split' },
  { key: 'HOLD', label: 'Hold' },
  { key: 'FAILED_LAST_RUN', label: 'Failed' },
];

// ============================================================================
// Page Component
// ============================================================================

export default function UcUatConsolePage() {
  const [manifest, setManifest] = useState<ManifestEntry[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterKey>('ALL');
  const [selectedEntry, setSelectedEntry] = useState<ManifestEntry | null>(
    null,
  );

  // Load data on mount
  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [m, s] = await Promise.all([fetchManifest(), fetchScenarios()]);
        if (!cancelled) {
          setManifest(m);
          setScenarios(s);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load UAT data',
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const stats = useMemo(
    () => computeStats(manifest, scenarios),
    [manifest, scenarios],
  );
  const filtered = useMemo(
    () => filterEntries(manifest, scenarios, filter),
    [manifest, scenarios, filter],
  );

  // ========================================================================
  // Render
  // ========================================================================

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        Loading UAT data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-400">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold">UC UAT Console</h1>
        <p className="text-sm text-gray-400 mt-1">
          Codebase Elicitation Validation — Iteration 3 Decision Table
        </p>
      </div>

      {/* Stats Bar */}
      <div
        className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-6"
        data-testid="uat-stats"
      >
        <StatCard label="Total" value={stats.total} />
        <StatCard label="Assign" value={stats.assign} color="green" />
        <StatCard label="Split" value={stats.split} color="yellow" />
        <StatCard label="Hold" value={stats.hold} color="gray" />
        <StatCard label="Scenarios Run" value={stats.scenariosRun} />
        <StatCard
          label="Passed"
          value={stats.scenariosPassed}
          color="green"
        />
        <StatCard label="Failed" value={stats.scenariosFailed} color="red" />
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-1 mb-4" data-testid="uat-filters">
        {FILTER_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              filter === tab.key
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:text-gray-200'
            }`}
            data-testid={`filter-${tab.key.toLowerCase()}`}
          >
            {tab.label}
            {tab.key !== 'ALL' && tab.key !== 'FAILED_LAST_RUN' && (
              <span className="ml-1 text-xs opacity-70">
                (
                {tab.key === 'ASSIGN'
                  ? stats.assign
                  : tab.key === 'SPLIT'
                    ? stats.split
                    : stats.hold}
                )
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Results */}
      <div className="space-y-2" data-testid="uat-results">
        {filtered.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            No entries match the selected filter.
          </div>
        )}
        {filtered.map((entry) => (
          <UcUatResultCard
            key={`${entry.uc_id}-${entry.operation_name}`}
            entry={entry}
            scenarios={scenarios}
            onSelectEvidence={setSelectedEntry}
          />
        ))}
      </div>

      {/* Evidence Panel */}
      <UcUatEvidencePanel
        entry={selectedEntry}
        scenarios={scenarios}
        onClose={() => setSelectedEntry(null)}
      />
    </div>
  );
}

// ============================================================================
// Stat Card
// ============================================================================

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color?: string;
}) {
  const valueColor =
    color === 'green'
      ? 'text-green-400'
      : color === 'yellow'
        ? 'text-yellow-400'
        : color === 'red'
          ? 'text-red-400'
          : color === 'gray'
            ? 'text-gray-400'
            : 'text-gray-100';

  return (
    <div className="bg-gray-800 rounded-lg p-3 text-center">
      <div className={`text-lg font-bold ${valueColor}`}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}
