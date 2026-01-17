/**
 * Cost Page - Analytics Domain
 *
 * Layer: L1 — Product Experience (UI)
 * Product: ai-console (Customer Console)
 * Temporal:
 *   Trigger: runtime (navigation)
 *   Execution: async (API fetch)
 * Role: Display cost statistics with breakdowns and export capabilities
 * Reference: Analytics Cost Wiring, PIN-411
 *
 * COMPONENTS:
 * A. Time Window Control (From/To, Resolution, Scope)
 * B. Cost Totals Summary (Spend USD, Requests, Tokens)
 * C. Cost Table (Time Series)
 * D. By Model Breakdown
 * E. By Feature Breakdown
 * F. Export Buttons (CSV, JSON)
 *
 * RULES:
 * - Totals update with filters
 * - Matches facade response exactly (no client math)
 * - Max window enforced (90 days)
 */

import { useState, useEffect, useCallback } from 'react';
import {
  DollarSign,
  Calendar,
  Clock,
  Download,
  FileJson,
  FileSpreadsheet,
  Layers,
  Loader2,
  AlertCircle,
  RefreshCw,
  PieChart,
  Tag,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

interface CostDataPoint {
  ts: string;
  spend_cents: number;
  requests: number;
  input_tokens: number;
  output_tokens: number;
}

interface CostByModel {
  model: string;
  spend_cents: number;
  requests: number;
  input_tokens: number;
  output_tokens: number;
  pct_of_total: number;
}

interface CostByFeature {
  feature_tag: string;
  spend_cents: number;
  requests: number;
  pct_of_total: number;
}

interface CostTotals {
  spend_cents: number;
  spend_usd: number;
  requests: number;
  input_tokens: number;
  output_tokens: number;
}

interface CostWindow {
  from: string;
  to: string;
  resolution: 'hour' | 'day';
}

interface CostSignals {
  sources: string[];
  freshness_sec: number;
}

interface CostStatisticsResponse {
  window: CostWindow;
  totals: CostTotals;
  series: CostDataPoint[];
  by_model: CostByModel[];
  by_feature: CostByFeature[];
  signals: CostSignals;
}

type ResolutionType = 'hour' | 'day';
type ScopeType = 'org' | 'project' | 'env';

// ============================================================================
// API Functions
// ============================================================================

async function fetchCostStatistics(
  from: Date,
  to: Date,
  resolution: ResolutionType = 'day',
  scope: ScopeType = 'org'
): Promise<CostStatisticsResponse> {
  const params = new URLSearchParams({
    from: from.toISOString(),
    to: to.toISOString(),
    resolution,
    scope,
  });

  const response = await fetch(`/api/v1/analytics/statistics/cost?${params}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch cost statistics: ${response.statusText}`);
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

  return `/api/v1/analytics/statistics/cost/export.${format}?${params}`;
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

function formatCurrency(cents: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(cents / 100);
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
  totals: CostTotals | null;
}

function TotalsSummary({ totals }: TotalsSummaryProps) {
  if (!totals) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="text-sm text-gray-400">Total Spend</div>
        <div className="text-2xl font-semibold text-green-400">
          {formatCurrency(totals.spend_cents)}
        </div>
      </div>
      <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="text-sm text-gray-400">Requests</div>
        <div className="text-2xl font-semibold text-gray-100">
          {formatNumber(totals.requests)}
        </div>
      </div>
      <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="text-sm text-gray-400">Input Tokens</div>
        <div className="text-2xl font-semibold text-gray-100">
          {formatNumber(totals.input_tokens)}
        </div>
      </div>
      <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="text-sm text-gray-400">Output Tokens</div>
        <div className="text-2xl font-semibold text-gray-100">
          {formatNumber(totals.output_tokens)}
        </div>
      </div>
      <div className="p-4 bg-gray-800 rounded-lg border border-gray-700">
        <div className="text-sm text-gray-400">Total Tokens</div>
        <div className="text-2xl font-semibold text-gray-100">
          {formatNumber(totals.input_tokens + totals.output_tokens)}
        </div>
      </div>
    </div>
  );
}

interface CostTableProps {
  data: CostDataPoint[];
  loading: boolean;
}

function CostTable({ data, loading }: CostTableProps) {
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
        No cost data for the selected time window.
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
              Spend
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Requests
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Input Tokens
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Output Tokens
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
              <td className="px-4 py-3 text-sm text-green-400 text-right">
                {formatCurrency(point.spend_cents)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {formatNumber(point.requests)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {formatNumber(point.input_tokens)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {formatNumber(point.output_tokens)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface ByModelTableProps {
  data: CostByModel[];
}

function ByModelTable({ data }: ByModelTableProps) {
  if (data.length === 0) {
    return (
      <div className="py-8 text-center text-gray-500">
        No model breakdown data available.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">
              Model
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Spend
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              % of Total
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Requests
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Tokens
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr
              key={item.model}
              className="border-b border-gray-700/50 hover:bg-gray-800/50"
            >
              <td className="px-4 py-3 text-sm text-gray-300 font-mono">
                {item.model}
              </td>
              <td className="px-4 py-3 text-sm text-green-400 text-right">
                {formatCurrency(item.spend_cents)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {item.pct_of_total.toFixed(1)}%
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {formatNumber(item.requests)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {formatNumber(item.input_tokens + item.output_tokens)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface ByFeatureTableProps {
  data: CostByFeature[];
}

function ByFeatureTable({ data }: ByFeatureTableProps) {
  if (data.length === 0) {
    return (
      <div className="py-8 text-center text-gray-500">
        No feature breakdown data available.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">
              Feature
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Spend
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              % of Total
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-gray-400">
              Requests
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr
              key={item.feature_tag}
              className="border-b border-gray-700/50 hover:bg-gray-800/50"
            >
              <td className="px-4 py-3 text-sm text-gray-300">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-700 rounded text-xs">
                  <Tag size={12} />
                  {item.feature_tag}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-green-400 text-right">
                {formatCurrency(item.spend_cents)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {item.pct_of_total.toFixed(1)}%
              </td>
              <td className="px-4 py-3 text-sm text-gray-200 text-right">
                {formatNumber(item.requests)}
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
  signals: CostSignals | null;
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

export function CostPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<CostStatisticsResponse | null>(null);

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
      const result = await fetchCostStatistics(from, to, resolution, scope);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cost data');
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
          <div className="p-2 bg-green-900/30 rounded-lg">
            <DollarSign size={24} className="text-green-400" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-gray-100">Cost Statistics</h1>
            <p className="text-sm text-gray-400">
              Analytics / Statistics / Cost
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

      {/* Totals Summary */}
      <TotalsSummary totals={data?.totals ?? null} />

      {/* Cost Time Series Table */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700">
        <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
          <h2 className="font-medium text-gray-200">Cost Over Time</h2>
          <SignalFreshness signals={data?.signals ?? null} />
        </div>
        <CostTable data={data?.series ?? []} loading={loading} />
      </div>

      {/* Breakdown Tables - Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Model */}
        <div className="bg-gray-800/50 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700 flex items-center gap-2">
            <PieChart size={16} className="text-gray-400" />
            <h2 className="font-medium text-gray-200">By Model</h2>
          </div>
          <ByModelTable data={data?.by_model ?? []} />
        </div>

        {/* By Feature */}
        <div className="bg-gray-800/50 rounded-lg border border-gray-700">
          <div className="px-4 py-3 border-b border-gray-700 flex items-center gap-2">
            <Tag size={16} className="text-gray-400" />
            <h2 className="font-medium text-gray-200">By Feature</h2>
          </div>
          <ByFeatureTable data={data?.by_feature ?? []} />
        </div>
      </div>

      {/* Empty State */}
      {!loading && !error && (!data?.series || data.series.length === 0) && (
        <div className="py-8 text-center">
          <DollarSign size={48} className="mx-auto text-gray-600 mb-4" />
          <p className="text-gray-400">
            Cost data will appear once LLM calls are recorded. No configuration required.
          </p>
        </div>
      )}
    </div>
  );
}

export default CostPage;
