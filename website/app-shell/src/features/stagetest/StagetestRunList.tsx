/**
 * StagetestRunList — Run List Table for Stagetest Evidence Console
 *
 * Layer: L1 — Product Experience (UI)
 * AUDIENCE: FOUNDER
 * Role: Display all stagetest runs with summary stats and drill-down
 * artifact_class: CODE
 */

import { type RunSummary, truncateHash } from './stagetestClient';

interface Props {
  runs: RunSummary[];
  selectedRunId: string | null;
  onSelectRun: (runId: string) => void;
}

export function StagetestRunList({ runs, selectedRunId, onSelectRun }: Props) {
  if (runs.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No stagetest runs found. Run the test suite with STAGETEST_EMIT=1 to generate artifacts.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto" data-testid="stagetest-run-list">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-500 border-b border-gray-700">
            <th className="pb-2 pr-4">Run ID</th>
            <th className="pb-2 pr-4">Created</th>
            <th className="pb-2 pr-4">Stages</th>
            <th className="pb-2 pr-4 text-right">Total</th>
            <th className="pb-2 pr-4 text-right">Pass</th>
            <th className="pb-2 pr-4 text-right">Fail</th>
            <th className="pb-2 pr-4">Digest</th>
            <th className="pb-2">Version</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => {
            const isSelected = run.run_id === selectedRunId;
            const allPass = run.fail_count === 0 && run.total_cases > 0;
            return (
              <tr
                key={run.run_id}
                onClick={() => onSelectRun(run.run_id)}
                className={`cursor-pointer border-b border-gray-800 transition-colors ${
                  isSelected
                    ? 'bg-blue-900/30 border-blue-700'
                    : 'hover:bg-gray-800/50'
                }`}
                data-testid={`run-row-${run.run_id}`}
              >
                <td className="py-2 pr-4 font-mono text-xs text-blue-400">
                  {truncateHash(run.run_id, 16)}
                </td>
                <td className="py-2 pr-4 text-gray-400 text-xs">
                  {run.created_at}
                </td>
                <td className="py-2 pr-4 text-xs">
                  {run.stages_executed.join(', ')}
                </td>
                <td className="py-2 pr-4 text-right">{run.total_cases}</td>
                <td className="py-2 pr-4 text-right text-green-400">
                  {run.pass_count}
                </td>
                <td className="py-2 pr-4 text-right text-red-400">
                  {run.fail_count > 0 ? run.fail_count : '—'}
                </td>
                <td className="py-2 pr-4 font-mono text-xs text-gray-500">
                  {truncateHash(run.determinism_digest)}
                  {allPass && (
                    <span className="ml-1 text-green-400" title="All cases pass">
                      ✓
                    </span>
                  )}
                </td>
                <td className="py-2 text-xs text-gray-500">
                  {run.artifact_version}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
