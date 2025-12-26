/**
 * Founder Decision Timeline - Phase 5E-1
 *
 * Raw, chronological consumption of decision records.
 *
 * Rules:
 * - Chronological order only
 * - No grouping
 * - No collapsing
 * - No "status pills"
 * - No interpretation
 *
 * This is a court transcript, not a dashboard.
 *
 * Stop Condition:
 * A founder can reconstruct any run end-to-end without logs or explanation.
 */

import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Clock,
  FileText,
  Search,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Filter,
  Hash,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  listDecisionRecords,
  getRunTimeline,
  countDecisionRecords,
  type DecisionRecordView,
  type RunTimeline,
  type TimelineEntry,
} from '@/api/timeline';

// =============================================================================
// Constants
// =============================================================================

const POLL_INTERVAL_MS = 30000; // 30 seconds
const PAGE_SIZE = 50;

// =============================================================================
// Utility Functions
// =============================================================================

function formatTimestamp(ts: string): string {
  const date = new Date(ts);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

function formatJson(obj: unknown): string {
  return JSON.stringify(obj, null, 2);
}

function getEntryTypeLabel(type: string): string {
  switch (type) {
    case 'pre_run':
      return 'PRE-RUN DECLARATION';
    case 'decision':
      return 'DECISION';
    case 'outcome':
      return 'OUTCOME';
    default:
      return type.toUpperCase();
  }
}

function getEntryTypeColor(type: string): string {
  switch (type) {
    case 'pre_run':
      return 'border-blue-500/50 bg-blue-950/20';
    case 'decision':
      return 'border-yellow-500/50 bg-yellow-950/20';
    case 'outcome':
      return 'border-green-500/50 bg-green-950/20';
    default:
      return 'border-gray-500/50 bg-gray-950/20';
  }
}

function truncateId(id: string | null | undefined, length = 8): string {
  if (!id) return '-';
  return id.length > length ? `${id.substring(0, length)}...` : id;
}

// =============================================================================
// Components
// =============================================================================

interface RecordFieldProps {
  label: string;
  value: unknown;
  mono?: boolean;
}

function RecordField({ label, value, mono = false }: RecordFieldProps) {
  const displayValue = value === null || value === undefined ? '-' : String(value);

  return (
    <div className="flex gap-2">
      <span className="text-gray-500 min-w-32 shrink-0">{label}:</span>
      <span className={cn('text-gray-200 break-all', mono && 'font-mono text-xs')}>
        {displayValue}
      </span>
    </div>
  );
}

interface JsonBlockProps {
  label: string;
  data: unknown;
}

function JsonBlock({ label, data }: JsonBlockProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
    return null;
  }

  return (
    <div className="mt-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-gray-500 hover:text-gray-300 text-sm"
      >
        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        {label}
      </button>
      {isExpanded && (
        <pre className="mt-2 p-3 bg-gray-950 rounded border border-gray-800 text-xs text-gray-300 overflow-x-auto font-mono">
          {formatJson(data)}
        </pre>
      )}
    </div>
  );
}

interface TimelineEntryCardProps {
  entry: TimelineEntry;
  index: number;
}

function TimelineEntryCard({ entry, index }: TimelineEntryCardProps) {
  const record = entry.record;

  return (
    <div className={cn('border-l-4 p-4 rounded-r', getEntryTypeColor(entry.entry_type))}>
      {/* Header */}
      <div className="flex items-center gap-4 mb-3">
        <span className="text-xs font-mono text-gray-500">#{index + 1}</span>
        <span className="text-xs font-bold text-gray-400 uppercase tracking-wide">
          {getEntryTypeLabel(entry.entry_type)}
        </span>
        <span className="text-xs font-mono text-gray-500">{formatTimestamp(entry.timestamp)}</span>
      </div>

      {/* Content based on entry type */}
      {entry.entry_type === 'pre_run' && (
        <div className="space-y-1 text-sm">
          <RecordField label="run_id" value={record.run_id} mono />
          <RecordField label="agent_id" value={record.agent_id} mono />
          <RecordField label="goal" value={record.goal} />
          <RecordField label="max_attempts" value={record.max_attempts} />
          <RecordField label="priority" value={record.priority} />
          <RecordField label="tenant_id" value={record.tenant_id} mono />
          <RecordField label="idempotency_key" value={record.idempotency_key} mono />
          <RecordField label="parent_run_id" value={record.parent_run_id} mono />
          <RecordField label="declared_at" value={record.declared_at} />
        </div>
      )}

      {entry.entry_type === 'decision' && (
        <div className="space-y-1 text-sm">
          <RecordField label="decision_id" value={record.decision_id} mono />
          <RecordField label="decision_type" value={record.decision_type} />
          <RecordField label="decision_source" value={record.decision_source} />
          <RecordField label="decision_trigger" value={record.decision_trigger} />
          <RecordField label="decision_outcome" value={record.decision_outcome} />
          <RecordField label="decision_reason" value={record.decision_reason} />
          <RecordField label="causal_role" value={record.causal_role} />
          <RecordField label="run_id" value={record.run_id} mono />
          <RecordField label="workflow_id" value={record.workflow_id} mono />
          <RecordField label="request_id" value={record.request_id} mono />
          <RecordField label="tenant_id" value={record.tenant_id} mono />
          <JsonBlock label="decision_inputs" data={record.decision_inputs} />
          <JsonBlock label="details" data={record.details} />
        </div>
      )}

      {entry.entry_type === 'outcome' && (
        <div className="space-y-1 text-sm">
          <RecordField label="run_id" value={record.run_id} mono />
          <RecordField label="status" value={record.status} />
          <RecordField label="attempts" value={record.attempts} />
          <RecordField label="error_message" value={record.error_message} />
          <RecordField label="started_at" value={record.started_at} />
          <RecordField label="completed_at" value={record.completed_at} />
          <RecordField label="duration_ms" value={record.duration_ms} />
          {record.pending && (
            <div className="mt-2 text-yellow-500 text-xs">RUN PENDING - OUTCOME NOT FINAL</div>
          )}
        </div>
      )}
    </div>
  );
}

interface DecisionRecordCardProps {
  record: DecisionRecordView;
}

function DecisionRecordCard({ record }: DecisionRecordCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border border-gray-800 rounded bg-gray-900/50 overflow-hidden">
      {/* Header - Always visible */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-800/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-4">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-500 shrink-0" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-500 shrink-0" />
          )}

          {/* Timestamp */}
          <span className="text-xs font-mono text-gray-500 min-w-40">
            {formatTimestamp(record.decided_at)}
          </span>

          {/* Type */}
          <span className="text-xs font-bold text-yellow-400 uppercase min-w-24">
            {record.decision_type}
          </span>

          {/* Outcome */}
          <span className="text-sm text-gray-300">{record.decision_outcome}</span>

          {/* Causal Role */}
          <span className="text-xs text-gray-500 ml-auto">{record.causal_role}</span>

          {/* Run ID */}
          <span className="text-xs font-mono text-gray-600">{truncateId(record.run_id)}</span>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-gray-800 p-4 bg-gray-950/50 space-y-1 text-sm">
          <RecordField label="decision_id" value={record.decision_id} mono />
          <RecordField label="decision_type" value={record.decision_type} />
          <RecordField label="decision_source" value={record.decision_source} />
          <RecordField label="decision_trigger" value={record.decision_trigger} />
          <RecordField label="decision_outcome" value={record.decision_outcome} />
          <RecordField label="decision_reason" value={record.decision_reason} />
          <RecordField label="causal_role" value={record.causal_role} />
          <RecordField label="run_id" value={record.run_id} mono />
          <RecordField label="workflow_id" value={record.workflow_id} mono />
          <RecordField label="request_id" value={record.request_id} mono />
          <RecordField label="tenant_id" value={record.tenant_id} mono />
          <RecordField label="decided_at" value={record.decided_at} />
          <JsonBlock label="decision_inputs" data={record.decision_inputs} />
          <JsonBlock label="details" data={record.details} />
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Views
// =============================================================================

interface RunTimelineViewProps {
  runId: string;
}

function RunTimelineView({ runId }: RunTimelineViewProps) {
  const [timeline, setTimeline] = useState<RunTimeline | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTimeline = useCallback(async () => {
    try {
      const data = await getRunTimeline(runId);
      setTimeline(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch timeline');
    } finally {
      setIsLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-6 h-6 text-gray-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-950/30 border border-red-500/50 rounded text-red-400 text-sm">
        {error}
      </div>
    );
  }

  if (!timeline || timeline.entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <FileText className="w-12 h-12 text-gray-600 mb-4" />
        <p className="text-gray-400">No timeline entries for this run</p>
        <p className="text-gray-600 text-sm mt-2">Run ID: {runId}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Run Header */}
      <div className="bg-gray-900 rounded border border-gray-800 p-4">
        <div className="flex items-center gap-4">
          <Hash className="w-5 h-5 text-gray-500" />
          <span className="font-mono text-white">{timeline.run_id}</span>
          <span className="text-gray-500 ml-auto">{timeline.entry_count} entries</span>
        </div>
      </div>

      {/* Timeline Entries */}
      <div className="space-y-2">
        {timeline.entries.map((entry, index) => (
          <TimelineEntryCard key={`${entry.entry_type}-${index}`} entry={entry} index={index} />
        ))}
      </div>
    </div>
  );
}

function AllDecisionsView() {
  const [records, setRecords] = useState<DecisionRecordView[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [typeFilter, setTypeFilter] = useState<string>('');

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      const [data, countData] = await Promise.all([
        listDecisionRecords({
          limit: PAGE_SIZE,
          offset,
          decision_type: typeFilter || undefined,
        }),
        countDecisionRecords({
          decision_type: typeFilter || undefined,
        }),
      ]);
      setRecords(data);
      setTotalCount(countData.count);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch records');
    } finally {
      setIsLoading(false);
    }
  }, [offset, typeFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Polling
  useEffect(() => {
    const interval = setInterval(fetchData, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchData]);

  const hasMore = offset + PAGE_SIZE < totalCount;
  const hasPrev = offset > 0;

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-gray-900 rounded border border-gray-800 p-4">
        <div className="flex items-center gap-4">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setOffset(0);
            }}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm text-white"
          >
            <option value="">All Types</option>
            <option value="routing">routing</option>
            <option value="recovery">recovery</option>
            <option value="memory">memory</option>
            <option value="policy">policy</option>
            <option value="budget">budget</option>
            <option value="policy_precheck">policy_precheck</option>
            <option value="budget_enforcement">budget_enforcement</option>
          </select>

          <span className="text-gray-500 text-sm ml-auto">
            {totalCount} total records
          </span>

          <button
            onClick={fetchData}
            className="p-1.5 rounded hover:bg-gray-800 text-gray-500 hover:text-white transition-colors"
          >
            <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-950/30 border border-red-500/50 rounded text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Records */}
      {isLoading && records.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-6 h-6 text-gray-500 animate-spin" />
        </div>
      ) : records.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <FileText className="w-12 h-12 text-gray-600 mb-4" />
          <p className="text-gray-400">No decision records found</p>
          <p className="text-gray-600 text-sm mt-2">
            Decision records will appear after production runs with decision emissions
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {records.map((record) => (
            <DecisionRecordCard key={record.decision_id} record={record} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalCount > PAGE_SIZE && (
        <div className="flex items-center justify-between bg-gray-900 rounded border border-gray-800 p-4">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={!hasPrev}
            className={cn(
              'px-3 py-1.5 rounded text-sm',
              hasPrev
                ? 'bg-gray-800 text-white hover:bg-gray-700'
                : 'bg-gray-900 text-gray-600 cursor-not-allowed'
            )}
          >
            Previous
          </button>
          <span className="text-gray-500 text-sm">
            Showing {offset + 1}-{Math.min(offset + PAGE_SIZE, totalCount)} of {totalCount}
          </span>
          <button
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={!hasMore}
            className={cn(
              'px-3 py-1.5 rounded text-sm',
              hasMore
                ? 'bg-gray-800 text-white hover:bg-gray-700'
                : 'bg-gray-900 text-gray-600 cursor-not-allowed'
            )}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function FounderTimelinePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const runId = searchParams.get('run');
  const [searchInput, setSearchInput] = useState(runId || '');

  const handleSearch = () => {
    if (searchInput.trim()) {
      setSearchParams({ run: searchInput.trim() });
    } else {
      setSearchParams({});
    }
  };

  const handleClear = () => {
    setSearchInput('');
    setSearchParams({});
  };

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-500" />
              Founder Decision Timeline
            </h1>
            <p className="text-gray-500 text-sm mt-1">
              Raw, chronological decision records. No interpretation.
            </p>
          </div>

          {/* Run Search */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Enter run_id..."
                className="bg-gray-800 border border-gray-700 rounded pl-9 pr-3 py-1.5 text-sm text-white w-64 focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm text-white transition-colors"
            >
              View Run
            </button>
            {runId && (
              <button
                onClick={handleClear}
                className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-sm text-white transition-colors"
              >
                Show All
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 max-w-5xl mx-auto">
        {runId ? <RunTimelineView runId={runId} /> : <AllDecisionsView />}
      </div>

      {/* Footer */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 px-6 py-2">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Phase 5E-1: Read-only, verbatim display</span>
          <span>Polling every {POLL_INTERVAL_MS / 1000}s</span>
        </div>
      </div>
    </div>
  );
}
