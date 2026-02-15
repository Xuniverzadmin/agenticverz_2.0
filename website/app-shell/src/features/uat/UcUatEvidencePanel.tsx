/**
 * UcUatEvidencePanel — Evidence Detail Sidebar for UAT Console
 *
 * Layer: L1 — Product Experience (UI)
 * AUDIENCE: FOUNDER
 * Role: Display detailed evidence for a selected UC operation mapping
 * Reference: UC_CODEBASE_ELICITATION_VALIDATION_UAT_TASKPACK_2026-02-15
 * artifact_class: CODE
 */

import type { ManifestEntry, ScenarioResult } from './ucUatClient';

// ============================================================================
// Evidence Panel
// ============================================================================

interface Props {
  entry: ManifestEntry | null;
  scenarios: ScenarioResult[];
  onClose: () => void;
}

export function UcUatEvidencePanel({ entry, scenarios, onClose }: Props) {
  if (!entry) return null;

  const relatedScenarios = scenarios.filter((s) => s.uc_id === entry.uc_id);

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-gray-900 border-l border-gray-700 shadow-xl z-50 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <h2 className="text-sm font-semibold text-gray-100">
          Evidence: {entry.uc_id}
        </h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-200 text-lg"
        >
          x
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Operation */}
        <Section title="Operation">
          <CopyableField label="Name" value={entry.operation_name} />
          <CopyableField label="Route" value={entry.route_path || 'N/A'} />
          <CopyableField label="Decision" value={entry.decision_type} />
          {entry.hold_status && (
            <CopyableField label="Hold Status" value={entry.hold_status} />
          )}
        </Section>

        {/* Handler */}
        <Section title="Handler">
          <CopyableField label="File" value={entry.handler_file} />
        </Section>

        {/* Engine/Driver Files */}
        {entry.engine_or_driver_files.length > 0 && (
          <Section title="Engine / Driver Files">
            {entry.engine_or_driver_files.map((f) => (
              <CopyableField key={f} label="" value={f} />
            ))}
          </Section>
        )}

        {/* Test References */}
        {entry.test_refs.length > 0 && (
          <Section title="Test References">
            {entry.test_refs.map((t) => (
              <CopyableField key={t} label="" value={t} />
            ))}
          </Section>
        )}

        {/* Scenario Execution Evidence */}
        {relatedScenarios.length > 0 && (
          <Section title="Scenario Results">
            {relatedScenarios.map((s) => (
              <div
                key={s.test_id}
                className="border border-gray-700 rounded p-3 space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-gray-200">
                    {s.test_id}
                  </span>
                  <StatusBadge status={s.status} />
                </div>
                <div className="text-xs text-gray-400">{s.test_name}</div>
                <CopyableField label="Evidence" value={s.evidence} />
                <div className="text-xs text-gray-500">{s.timestamp}</div>
              </div>
            ))}
          </Section>
        )}

        {relatedScenarios.length === 0 && (
          <Section title="Scenario Results">
            <p className="text-xs text-gray-500">
              No scenario results available. Run UAT tests to generate evidence.
            </p>
          </Section>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Sub-components
// ============================================================================

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
        {title}
      </h3>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function CopyableField({ label, value }: { label: string; value: string }) {
  const handleCopy = () => {
    navigator.clipboard.writeText(value).catch(() => {
      /* clipboard not available */
    });
  };

  return (
    <div className="flex items-start gap-2 group">
      {label && (
        <span className="text-xs text-gray-500 min-w-[60px] shrink-0">
          {label}:
        </span>
      )}
      <span className="text-xs font-mono text-gray-300 break-all flex-1">
        {value}
      </span>
      <button
        onClick={handleCopy}
        className="text-xs text-gray-600 hover:text-gray-400 opacity-0 group-hover:opacity-100 shrink-0"
        title="Copy"
      >
        copy
      </button>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === 'PASS'
      ? 'bg-green-600 text-white'
      : status === 'FAIL'
        ? 'bg-red-600 text-white'
        : 'bg-gray-600 text-white';
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${color}`}>
      {status}
    </span>
  );
}
