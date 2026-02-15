/**
 * StagetestPage — Main Page for Stagetest Evidence Console
 *
 * Layer: L1 — Product Experience (UI)
 * AUDIENCE: FOUNDER
 * Role: Main entry point for stagetest evidence console. Shows runs, drill into
 *        cases, drill into case detail. Three-level navigation via local state.
 * artifact_class: CODE
 */

import { useEffect, useState, useMemo } from 'react';
import {
  fetchRuns,
  fetchCases,
  fetchApis,
  type RunSummary,
  type CaseSummary,
  type ApiEndpoint,
} from './stagetestClient';
import { StagetestRunList } from './StagetestRunList';
import { StagetestCaseTable } from './StagetestCaseTable';
import { StagetestCaseDetail } from './StagetestCaseDetail';

// ============================================================================
// View State
// ============================================================================

type View =
  | { kind: 'runs' }
  | { kind: 'cases'; runId: string }
  | { kind: 'detail'; runId: string; caseId: string };

// ============================================================================
// Page Component
// ============================================================================

export default function StagetestPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [apis, setApis] = useState<ApiEndpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>({ kind: 'runs' });

  // Load runs + API snapshot on mount
  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [r, a] = await Promise.all([fetchRuns(), fetchApis()]);
        if (!cancelled) {
          setRuns(r);
          setApis(a);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load stagetest data');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  // Load cases when a run is selected
  useEffect(() => {
    if (view.kind === 'runs') {
      setCases([]);
      return;
    }

    let cancelled = false;
    const runId = view.runId;

    async function loadCases() {
      const c = await fetchCases(runId);
      if (!cancelled) setCases(c);
    }

    loadCases();
    return () => { cancelled = true; };
  }, [view.kind === 'runs' ? null : view.runId]);

  // Stats
  const stats = useMemo(() => {
    const totalRuns = runs.length;
    const totalCases = runs.reduce((sum, r) => sum + r.total_cases, 0);
    const totalPass = runs.reduce((sum, r) => sum + r.pass_count, 0);
    const totalFail = runs.reduce((sum, r) => sum + r.fail_count, 0);
    return { totalRuns, totalCases, totalPass, totalFail, apiCount: apis.length };
  }, [runs, apis]);

  // Navigation handlers
  const selectRun = (runId: string) => setView({ kind: 'cases', runId });
  const selectCase = (caseId: string) => {
    if (view.kind !== 'runs') {
      setView({ kind: 'detail', runId: view.runId, caseId });
    }
  };
  const backToRuns = () => setView({ kind: 'runs' });
  const backToCases = () => {
    if (view.kind === 'detail') {
      setView({ kind: 'cases', runId: view.runId });
    }
  };

  // ========================================================================
  // Render
  // ========================================================================

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        Loading stagetest evidence...
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
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6" data-testid="stagetest-page">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Stagetest Evidence Console</h1>
        <p className="text-sm text-gray-400 mt-1">
          Audit-ready evidence for HOC API stagetest runs
        </p>
      </div>

      {/* Stats Bar */}
      <div
        className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6"
        data-testid="stagetest-stats"
      >
        <StatCard label="Runs" value={stats.totalRuns} />
        <StatCard label="Total Cases" value={stats.totalCases} />
        <StatCard label="Passed" value={stats.totalPass} color="green" />
        <StatCard label="Failed" value={stats.totalFail} color="red" />
        <StatCard label="API Endpoints" value={stats.apiCount} />
      </div>

      {/* Breadcrumb */}
      {view.kind !== 'runs' && (
        <div className="flex items-center gap-1 text-xs text-gray-500 mb-4" data-testid="breadcrumb">
          <button onClick={backToRuns} className="text-blue-400 hover:underline">
            Runs
          </button>
          <span>/</span>
          {view.kind === 'cases' && (
            <span className="text-gray-300">{view.runId.slice(0, 16)}...</span>
          )}
          {view.kind === 'detail' && (
            <>
              <button onClick={backToCases} className="text-blue-400 hover:underline">
                {view.runId.slice(0, 16)}...
              </button>
              <span>/</span>
              <span className="text-gray-300">{view.caseId.slice(0, 16)}...</span>
            </>
          )}
        </div>
      )}

      {/* Content */}
      <div className="bg-gray-800/30 rounded-lg p-4">
        {view.kind === 'runs' && (
          <StagetestRunList
            runs={runs}
            selectedRunId={null}
            onSelectRun={selectRun}
          />
        )}

        {view.kind === 'cases' && (
          <StagetestCaseTable
            runId={view.runId}
            cases={cases}
            onSelectCase={selectCase}
          />
        )}

        {view.kind === 'detail' && (
          <StagetestCaseDetail
            runId={view.runId}
            caseId={view.caseId}
            onBack={backToCases}
          />
        )}
      </div>

      {/* API Endpoint Snapshot (collapsed by default) */}
      {apis.length > 0 && (
        <div className="mt-6" data-testid="api-snapshot">
          <h2 className="text-sm text-gray-400 mb-2">
            API Endpoint Snapshot ({apis.length} endpoints)
          </h2>
          <div className="bg-gray-800/30 rounded-lg p-4 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-700">
                  <th className="pb-2 pr-4">Method</th>
                  <th className="pb-2 pr-4">Path</th>
                  <th className="pb-2">Operation</th>
                </tr>
              </thead>
              <tbody>
                {apis.map((ep) => (
                  <tr key={`${ep.method}-${ep.path}`} className="border-b border-gray-800">
                    <td className="py-1 pr-4 font-mono text-green-400">{ep.method}</td>
                    <td className="py-1 pr-4 font-mono text-gray-300">{ep.path}</td>
                    <td className="py-1 text-gray-400">{ep.operation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
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
      : color === 'red'
        ? 'text-red-400'
        : 'text-gray-100';

  return (
    <div className="bg-gray-800 rounded-lg p-3 text-center">
      <div className={`text-lg font-bold ${valueColor}`}>{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}
