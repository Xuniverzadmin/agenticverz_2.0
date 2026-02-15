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
        <KeyValueTable data={detail.request_fields} testId="api-request-fields-table" />
      </Section>

      <Section title="Response Fields">
        <KeyValueTable data={detail.response_fields} testId="api-response-fields-table" />
      </Section>

      {/* Synthetic Input */}
      <Section title="Synthetic Input">
        <KeyValueTable data={detail.synthetic_input} testId="synthetic-input-table" />
      </Section>

      {/* Produced Output */}
      <Section title="Produced Output">
        <KeyValueTable data={detail.observed_output} testId="produced-output-table" />
      </Section>

      {/* APIs Used */}
      <Section title={`APIs Used (${detail.api_calls_used?.length ?? 0})`}>
        {(!detail.api_calls_used || detail.api_calls_used.length === 0) ? (
          <p className="text-gray-500 text-xs">No API calls recorded.</p>
        ) : (
          <table className="w-full text-xs" data-testid="apis-used-table">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-700">
                <th className="pb-1 pr-3">Method</th>
                <th className="pb-1 pr-3">Path</th>
                <th className="pb-1 pr-3">Operation</th>
                <th className="pb-1 pr-3">Status</th>
                <th className="pb-1">Duration (ms)</th>
              </tr>
            </thead>
            <tbody>
              {detail.api_calls_used.map((call, i) => (
                <tr key={i} className="border-b border-gray-800">
                  <td className="py-1 pr-3 font-mono text-blue-400">{call.method}</td>
                  <td className="py-1 pr-3 font-mono text-gray-300">{call.path}</td>
                  <td className="py-1 pr-3 text-gray-400">{call.operation}</td>
                  <td className="py-1 pr-3">
                    <span className={call.status_code < 400 ? 'text-green-400' : 'text-red-400'}>
                      {call.status_code}
                    </span>
                  </td>
                  <td className="py-1 font-mono text-gray-400">{call.duration_ms}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>

      {/* Execution Trace */}
      <Section title={`Execution Trace (${detail.execution_trace?.length ?? 0})`}>
        {(!detail.execution_trace || detail.execution_trace.length === 0) ? (
          <p className="text-gray-500 text-xs">No execution trace recorded.</p>
        ) : (
          <table className="w-full text-xs" data-testid="execution-trace-table">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-700">
                <th className="pb-1 pr-3">Seq</th>
                <th className="pb-1 pr-3">Time (UTC)</th>
                <th className="pb-1 pr-3">Layer</th>
                <th className="pb-1 pr-3">Component</th>
                <th className="pb-1 pr-3">Event</th>
                <th className="pb-1 pr-3">Status</th>
                <th className="pb-1">Trigger</th>
              </tr>
            </thead>
            <tbody>
              {detail.execution_trace.map((event, i) => (
                <tr key={i} className="border-b border-gray-800">
                  <td className="py-1 pr-3 font-mono text-gray-400">{event.seq}</td>
                  <td className="py-1 pr-3 font-mono text-gray-400">{event.ts_utc}</td>
                  <td className="py-1 pr-3 text-blue-300">{event.layer}</td>
                  <td className="py-1 pr-3 text-gray-300">{event.component}</td>
                  <td className="py-1 pr-3 text-gray-300">{event.event_type}</td>
                  <td className="py-1 pr-3">
                    <span className={event.status === 'PASS' ? 'text-green-400' : event.status === 'FAIL' ? 'text-red-400' : 'text-gray-400'}>
                      {event.status}
                    </span>
                  </td>
                  <td className="py-1 font-mono text-gray-400">{event.trigger}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>

      {/* DB Writes */}
      <Section title={`DB Writes (${detail.db_writes?.length ?? 0})`}>
        {(!detail.db_writes || detail.db_writes.length === 0) ? (
          <p className="text-gray-500 text-xs">No DB writes recorded.</p>
        ) : (
          <table className="w-full text-xs" data-testid="db-writes-table">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-700">
                <th className="pb-1 pr-3">Seq</th>
                <th className="pb-1 pr-3">Table</th>
                <th className="pb-1 pr-3">Op</th>
                <th className="pb-1 pr-3">Rows</th>
                <th className="pb-1 pr-3">Layer</th>
                <th className="pb-1 pr-3">Component</th>
                <th className="pb-1">Fingerprint</th>
              </tr>
            </thead>
            <tbody>
              {detail.db_writes.map((write, i) => (
                <tr key={i} className="border-b border-gray-800">
                  <td className="py-1 pr-3 font-mono text-gray-400">{write.seq}</td>
                  <td className="py-1 pr-3 font-mono text-gray-300">{write.table}</td>
                  <td className="py-1 pr-3 text-amber-300">{write.sql_op}</td>
                  <td className="py-1 pr-3 font-mono text-gray-300">{write.rowcount}</td>
                  <td className="py-1 pr-3 text-blue-300">{write.layer}</td>
                  <td className="py-1 pr-3 text-gray-400">{write.component}</td>
                  <td className="py-1 font-mono text-gray-500">{write.statement_fingerprint}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
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

function KeyValueTable({ data, testId }: { data: Record<string, unknown>; testId: string }) {
  const entries = Object.entries(data);
  if (entries.length === 0) {
    return <p className="text-gray-500 text-xs" data-testid={testId}>No data.</p>;
  }
  return (
    <table className="w-full text-xs" data-testid={testId}>
      <thead>
        <tr className="text-left text-gray-500 border-b border-gray-700">
          <th className="pb-1 pr-4">Field</th>
          <th className="pb-1">Value</th>
        </tr>
      </thead>
      <tbody>
        {entries.map(([key, val]) => (
          <tr key={key} className="border-b border-gray-800">
            <td className="py-1 pr-4 font-mono text-gray-400">{key}</td>
            <td className="py-1 font-mono text-gray-300">
              {typeof val === 'object' ? JSON.stringify(val) : String(val)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
