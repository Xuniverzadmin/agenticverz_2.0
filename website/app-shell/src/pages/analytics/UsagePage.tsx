/**
 * Usage Page - Analytics Domain
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console (Customer Console)
 * Temporal:
 *   Trigger: runtime (navigation)
 *   Execution: async (API fetch)
 * Role: Display usage statistics with export capabilities
 * Reference: Analytics Domain Declaration v1
 *
 * COMPONENTS:
 * A. Time Window Control (From/To, Resolution, Scope)
 * B. Usage Table (Authoritative View)
 * C. Inline Totals (Pinned Header)
 * D. Export Buttons (CSV, JSON)
 *
 * RULES:
 * - Totals update with filters
 * - Matches facade response exactly (no client math)
 * - Max window enforced (90 days)
 */

import { useState, useEffect, useCallback } from 'react';
import {
  BarChart2,
  Calendar,
  Clock,
  Download,
  FileJson,
  FileSpreadsheet,
  Layers,
  Loader2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

interface UsageDataPoint {
  ts: string;
  requests: number;
  compute_units: number;
  tokens: number;
}

interface UsageTotals {
  requests: number;
  compute_units: number;
  tokens: number;
}

interface UsageWindow {
  from: string;
  to: string;
  resolution: 'hour' | 'day';
}

interface UsageSignals {
  sources: string[];
  freshness_sec: number;
}

interface UsageStatisticsResponse {
  window: UsageWindow;
  totals: UsageTotals;
  series: UsageDataPoint[];
  signals: UsageSignals;
}

type ResolutionType = 'hour' | 'day';
type ScopeType = 'org' | 'project' | 'env';

// ============================================================================
// API Functions
// ============================================================================

async function fetchUsageStatistics(
  from: Date,
  to: Date,
  resolution: ResolutionType = 'day',
  scope: ScopeType = 'org'
): Promise<UsageStatisticsResponse> {
  const params = new URLSearchParams({
    from: from.toISOString(),
    to: to.toISOString(),
    resolution,
    scope,
  });

  const response = await fetch(`/api/v1/analytics/statistics/usage?${params}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch usage statistics: ${response.statusText}`);
  }

  return response.json();
}

function getExportUrl(
  format: 'csv' | 'json',
  from: Date,
  to: Date,
  resolution: ResolutionType = 'day',
  scope: ScopeType = 'org'
): string {
  const params = new URLSearchParams({
    from: from.toISOString(),
    to: to.toISOString(),
    resolution,
    scope,
  });

  return `/api/v1/analytics/statistics/usage/export.${format}?${params}`;
}

// ============================================================================
// Helper Functions
// ============================================================================

function getDefaultDateRange(): { from: Date; to: Date } {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 7); // Last 7 days default
  return { from, to };
}

function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num);
}

function getFreshnessLabel(sec: number): { label: string; color: string } {
  if (sec <= 60) {
    return { label: 'Live', color: 'text-green-400' };
  } else if (sec <= 300) {
    return { label: 'Delayed', color: 'text-yellow-400' };
  } else {
    return { label: 'Stale', color: 'text-red-400' };
  }
}

// ============================================================================
// Components
// ============================================================================

interface TimeWindowControlProps {
  from: Date;
  to: Date;
  resolution: ResolutionType;
  scope: ScopeType;
  onFromChange: (date: Date) => void;
  onToChange: (date: Date) => void;
  onResolutionChange: (resolution: ResolutionType) => void;
  onScopeChange: (scope: ScopeType) => void;
  onRefresh: () => void;
  loading: boolean;
}

function TimeWindowControl({
  from,
  to,
  resolution,
  scope,
  onFromChange,
  onToChange,
  onResolutionChange,
  onScopeChange,
  onRefresh,
  loading,
}: TimeWindowControlProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
      {/* From Date */}
      <div className="flex items-center gap-2">
        <Calendar size={16} className="text-gray-400" />
        <label className="text-sm text-gray-400">From:</label>
        <input
          type="date"
          value={from.toISOString().split('T')[0]}
          onChange={(e) => onFromChange(new Date(e.target.value))}
          className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-gray-200"
        />
      </div>

      {/* To Date */}
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-400">To:</label>
        <input
          type="date"
          value={to.toISOString().split('T')[0]}
          onChange={(e) => onToChange(new Date(e.target.value))}
          className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-gray-200"
        />
      </div>

      {/* Resolution */}
      <div className="flex items-center gap-2">
        <Clock size={16} className="text-gray-400" />
        <select
          value={resolution}
          onChange={(e) => onResolutionChange(e.target.value as ResolutionType)}
          className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-gray-200"
        >
          <option value="hour">Hourly</option>
          <option value="day">Daily</option>
        </select>
      </div>

      {/* Scope */}
      <div className="flex items-center gap-2">
        <Layers size={16} className="text-gray-400" />
        <select
          value={scope}
          onChange={(e) => onScopeChange(e.target.value as ScopeType)}
          className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-gray-200"
        >
          <option value="org">Organization</option>
          <option value="project">Project</option>
          <option value="env">Environment</option>
        </select>
      </div>

      {/* Refresh Button */}
      <button
        onClick={onRefresh}
        disabled={loading}
        className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 hover:bg-primary-700 rounded text-sm text-white disabled:opacity-50"
      >
        <RefreshCw size={14} className={cn(loading && 'animate-spin')} />
        Refresh
      </button>
    </div>
  );
}

interface TotalsSummaryProps {
  totals: UsageTotals | null;
}

function TotalsSummary({ totals }: TotalsSummaryProps) {
  if (!totals) return null;

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="text-sm text-gray-400">Total Requests</div>
        <div className="text-2xl font-semibold text-gray-100">
          {formatNumber(totals.requests)}
        </div>
      </div>
      <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="text-sm text-gray-400">Compute Units</div>
        <div className="text-2xl font-semibold text-gray-100">
          {formatNumber(totals.compute_units)}
        </div>
      </div>
      <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="text-sm text-gray-400">Tokens</div>
        <div className="text-2xl font-semibold text-gray-100">
          {formatNumber(totals.tokens)}
        </div>
      </div>
    </div>
  );
}

interface UsageTableProps {
  data: UsageDataPoint[];
  loading: boolean;
}

function UsageTable({ data, loading }: UsageTableProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-gray-400" size={24} />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="py-12 text-center text-gray-500">
        No usage data for the selected time window.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">
              Timestamp
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Requests
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Compute Units
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Tokens
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((point) => (
            <tr
              key={point.ts}
              className="border-b border-gray-700/50 hover:bg-gray-800/50"
            >
              <td className="px-4 py-3 text-sm text-gray-300 font-mono">
                {point.ts}
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {formatNumber(point.requests)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {formatNumber(point.compute_units)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {formatNumber(point.tokens)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface ExportButtonsProps {
  from: Date;
  to: Date;
  resolution: ResolutionType;
  scope: ScopeType;
}

function ExportButtons({ from, to, resolution, scope }: ExportButtonsProps) {
  const handleExport = (format: 'csv' | 'json') => {
    const url = getExportUrl(format, from, to, resolution, scope);
    window.open(url, '_blank');
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => handleExport('csv')}
        className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-200"
      >
        <FileSpreadsheet size={14} />
        Export CSV
      </button>
      <button
        onClick={() => handleExport('json')}
        className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm text-gray-200"
      >
        <FileJson size={14} />
        Export JSON
      </button>
    </div>
  );
}

interface SignalFreshnessProps {
  signals: UsageSignals | null;
}

function SignalFreshness({ signals }: SignalFreshnessProps) {
  if (!signals) return null;

  const { label, color } = getFreshnessLabel(signals.freshness_sec);

  return (
    <div className="flex items-center gap-4 text-sm">
      <div className="flex items-center gap-2">
        <span className="text-gray-400">Freshness:</span>
        <span className={color}>{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-gray-400">Sources:</span>
        <span className="text-gray-300">{signals.sources.join(', ')}</span>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function UsagePage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<UsageStatisticsResponse | null>(null);

  // Time window state
  const { from: defaultFrom, to: defaultTo } = getDefaultDateRange();
  const [from, setFrom] = useState<Date>(defaultFrom);
  const [to, setTo] = useState<Date>(defaultTo);
  const [resolution, setResolution] = useState<ResolutionType>('day');
  const [scope, setScope] = useState<ScopeType>('org');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchUsageStatistics(from, to, resolution, scope);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load usage data');
    } finally {
      setLoading(false);
    }
  }, [from, to, resolution, scope]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary-900/30 rounded-lg">
            <BarChart2 size={24} className="text-primary-400" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-gray-100">Usage Statistics</h1>
            <p className="text-sm text-gray-400">
              Analytics / Statistics / Usage
            </p>
          </div>
        </div>
        <ExportButtons from={from} to={to} resolution={resolution} scope={scope} />
      </div>

      {/* Time Window Controls */}
      <TimeWindowControl
        from={from}
        to={to}
        resolution={resolution}
        scope={scope}
        onFromChange={setFrom}
        onToChange={setTo}
        onResolutionChange={setResolution}
        onScopeChange={setScope}
        onRefresh={loadData}
        loading={loading}
      />

      {/* Error State */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-900/20 border border-red-700/50 rounded-lg text-red-400">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Totals Summary (Pinned Header) */}
      <TotalsSummary totals={data?.totals ?? null} />

      {/* Usage Table */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700">
        <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
          <h2 className="font-medium text-gray-200">Usage Data</h2>
          <SignalFreshness signals={data?.signals ?? null} />
        </div>
        <UsageTable data={data?.series ?? []} loading={loading} />
      </div>

      {/* Empty State */}
      {!loading && !error && (!data?.series || data.series.length === 0) && (
        <div className="py-8 text-center">
          <BarChart2 size={48} className="mx-auto text-gray-600 mb-4" />
          <p className="text-gray-400">
            Usage data will appear once signals are ingested. No configuration required.
          </p>
        </div>
      )}
    </div>
  );
}

export default UsagePage;
