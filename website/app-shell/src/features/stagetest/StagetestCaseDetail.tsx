/**
 * StagetestCaseDetail — Case Detail View for Stagetest Evidence Console
 *
 * Layer: L1 — Product Experience (UI)
 * AUDIENCE: FOUNDER
 * Role: Display full case detail with API fields, synthetic input, observed output,
 *        assertions, determinism hash, and evidence files
 * artifact_class: CODE
 */

import { useEffect, useState } from 'react';
import {
  fetchCaseDetail,
  type CaseDetail,
  statusColor,
  truncateHash,
} from './stagetestClient';

interface Props {
  runId: string;
  caseId: string;
  onBack: () => void;
}

export function StagetestCaseDetail({ runId, caseId, onBack }: Props) {
  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      const data = await fetchCaseDetail(runId, caseId);
      if (!cancelled) {
        setDetail(data);
        setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [runId, caseId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400">
        Loading case detail...
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="text-center text-red-400 py-8">
        Case not found: {caseId}
        <button onClick={onBack} className="ml-4 text-blue-400 underline text-sm">
          Back to cases
        </button>
      </div>
    );
  }

  return (
    <div data-testid="stagetest-case-detail" className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={onBack}
            className="text-xs text-blue-400 hover:underline mb-1"
          >
            ← Back to cases
          </button>
          <h3 className="text-lg font-semibold">
            {detail.operation_name}
            <span
              className="ml-2 text-xs px-2 py-0.5 rounded"
              style={{
                color: statusColor(detail.status),
                backgroundColor: `${statusColor(detail.status)}15`,
                border: `1px solid ${statusColor(detail.status)}40`,
              }}
            >
              {detail.status}
            </span>
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {detail.uc_id} / {detail.stage} — {detail.api_method} {detail.route_path}
          </p>
        </div>
      </div>

      {/* API Fields */}
      <Section title="Request Fields">
        <JsonBlock data={detail.request_fields} testId="request-fields" />
      </Section>

      <Section title="Response Fields">
        <JsonBlock data={detail.response_fields} testId="response-fields" />
      </Section>

      {/* Synthetic Input */}
      <Section title="Synthetic Input">
        <JsonBlock data={detail.synthetic_input} testId="synthetic-input" />
      </Section>

      {/* Observed Output */}
      <Section title="Observed Output">
        <JsonBlock data={detail.observed_output} testId="observed-output" />
      </Section>

      {/* Assertions */}
      <Section title={`Assertions (${detail.assertions.length})`}>
        {detail.assertions.length === 0 ? (
          <p className="text-gray-500 text-xs">No assertions recorded.</p>
        ) : (
          <table className="w-full text-xs" data-testid="assertions-table">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-700">
                <th className="pb-1 pr-3">ID</th>
                <th className="pb-1 pr-3">Status</th>
                <th className="pb-1">Message</th>
              </tr>
            </thead>
            <tbody>
              {detail.assertions.map((a) => (
                <tr key={a.id} className="border-b border-gray-800">
                  <td className="py-1 pr-3 font-mono text-gray-400">{a.id}</td>
                  <td className="py-1 pr-3">
                    <span className={a.status === 'PASS' ? 'text-green-400' : 'text-red-400'}>
                      {a.status}
                    </span>
                  </td>
                  <td className="py-1 text-gray-300">{a.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>

      {/* Determinism & Signature */}
      <Section title="Determinism & Integrity">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div>
            <span className="text-gray-500">Determinism Hash:</span>
            <code className="ml-2 font-mono text-green-400" data-testid="determinism-hash">
              {detail.determinism_hash}
            </code>
          </div>
          <div>
            <span className="text-gray-500">Signature:</span>
            <code className="ml-2 font-mono text-gray-400" data-testid="signature">
              {truncateHash(detail.signature, 24)}
            </code>
          </div>
        </div>
      </Section>

      {/* Evidence Files */}
      {detail.evidence_files.length > 0 && (
        <Section title={`Evidence Files (${detail.evidence_files.length})`}>
          <ul className="text-xs space-y-1" data-testid="evidence-files">
            {detail.evidence_files.map((f) => (
              <li key={f} className="font-mono text-gray-400">
                {f}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

// ============================================================================
// Helpers
// ============================================================================

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-gray-800/50 rounded-lg p-3">
      <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
        {title}
      </h4>
      {children}
    </div>
  );
}

function JsonBlock({ data, testId }: { data: Record<string, unknown>; testId: string }) {
  const json = JSON.stringify(data, null, 2);
  return (
    <pre
      className="bg-gray-900 rounded p-2 text-xs text-gray-300 overflow-x-auto max-h-48"
      data-testid={testId}
    >
      {json}
    </pre>
  );
}
