/**
 * StagetestCaseTable — Case Table for Stagetest Evidence Console
 *
 * Layer: L1 — Product Experience (UI)
 * AUDIENCE: FOUNDER
 * Role: Display test cases for a selected run with status, UC, stage, and determinism hash
 * artifact_class: CODE
 */

import {
  type CaseSummary,
  statusColor,
  truncateHash,
} from './stagetestClient';

interface Props {
  runId: string;
  cases: CaseSummary[];
  onSelectCase: (caseId: string) => void;
}

export function StagetestCaseTable({ runId, cases, onSelectCase }: Props) {
  if (cases.length === 0) {
    return (
      <div className="text-center text-gray-500 py-6">
        No cases found for run {truncateHash(runId, 16)}.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto" data-testid="stagetest-case-table">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-500 border-b border-gray-700">
            <th className="pb-2 pr-4">Status</th>
            <th className="pb-2 pr-4">Case ID</th>
            <th className="pb-2 pr-4">UC</th>
            <th className="pb-2 pr-4">Stage</th>
            <th className="pb-2 pr-4">Operation</th>
            <th className="pb-2">Hash</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => (
            <tr
              key={c.case_id}
              onClick={() => onSelectCase(c.case_id)}
              className="cursor-pointer border-b border-gray-800 hover:bg-gray-800/50 transition-colors"
              data-testid={`case-row-${c.case_id}`}
            >
              <td className="py-2 pr-4">
                <span
                  className="inline-block px-2 py-0.5 rounded text-xs font-medium"
                  style={{
                    color: statusColor(c.status),
                    backgroundColor: `${statusColor(c.status)}15`,
                    border: `1px solid ${statusColor(c.status)}40`,
                  }}
                >
                  {c.status}
                </span>
              </td>
              <td className="py-2 pr-4 font-mono text-xs text-blue-400">
                {truncateHash(c.case_id, 16)}
              </td>
              <td className="py-2 pr-4 text-xs">{c.uc_id}</td>
              <td className="py-2 pr-4 text-xs text-gray-400">{c.stage}</td>
              <td className="py-2 pr-4 text-xs">{c.operation_name}</td>
              <td className="py-2 font-mono text-xs text-gray-500">
                {truncateHash(c.determinism_hash)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
