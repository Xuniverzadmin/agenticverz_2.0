/**
 * AutoExecuteReviewPage - PIN-333
 *
 * Founder AUTO_EXECUTE Review Dashboard (Evidence-Only)
 *
 * CRITICAL CONSTRAINTS:
 * - READ-ONLY: No approve/reject/pause/override actions
 * - EVIDENCE-ONLY: Backed strictly by execution envelopes + safety flags
 * - FOUNDER-ONLY: FOPS token required
 * - NO BEHAVIOR CHANGE: Does not alter AUTO_EXECUTE logic
 *
 * This is an evidence viewer, not a control panel.
 *
 * Reference: PIN-333 - Founder AUTO_EXECUTE Review Dashboard
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Eye,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Search,
  Filter,
  ChevronRight,
  Clock,
  Shield,
  Hash,
  FileText,
  Activity,
  BarChart3,
  X,
} from 'lucide-react';
import {
  listAutoExecuteDecisions,
  getAutoExecuteDecision,
  getAutoExecuteStats,
  getDecisionColor,
  getConfidenceColor,
  getSafetyFlagColor,
  formatConfidence,
  formatTimestamp,
  getSafetyStatus,
  type AutoExecuteReviewItem,
  type AutoExecuteReviewFilter,
  type AutoExecuteReviewStats,
} from '@/api/autoExecuteReview';

// =============================================================================
// Constants
// =============================================================================

const PAGE_SIZE = 25;
const POLL_INTERVAL_MS = 30000; // 30 seconds

// =============================================================================
// Sub-components
// =============================================================================

/**
 * Daily Trend Chart - Shows decision counts over time
 * Evidence-only visualization (no control affordances)
 */
function DailyTrendChart({ stats }: { stats: AutoExecuteReviewStats | undefined }) {
  if (!stats || !stats.daily_counts || stats.daily_counts.length === 0) {
    return null;
  }

  const maxValue = Math.max(
    ...stats.daily_counts.map((d) => Math.max(d.executed, d.skipped, d.flagged))
  );

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="h-5 w-5 text-primary-400" />
        <h3 className="text-lg font-semibold text-white">Daily Decision Trend</h3>
      </div>

      {/* Legend */}
      <div className="flex gap-4 mb-4 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500 rounded" />
          <span className="text-gray-400">Executed</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-yellow-500 rounded" />
          <span className="text-gray-400">Skipped</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-orange-500 rounded" />
          <span className="text-gray-400">Flagged</span>
        </div>
      </div>

      {/* Chart */}
      <div className="flex items-end gap-1 h-32">
        {stats.daily_counts.slice(-14).map((day, idx) => {
          const executedHeight = maxValue > 0 ? (day.executed / maxValue) * 100 : 0;
          const skippedHeight = maxValue > 0 ? (day.skipped / maxValue) * 100 : 0;
          const flaggedHeight = maxValue > 0 ? (day.flagged / maxValue) * 100 : 0;

          return (
            <div
              key={idx}
              className="flex-1 flex flex-col items-center gap-0.5 group relative"
              title={`${day.date}: ${day.executed} executed, ${day.skipped} skipped, ${day.flagged} flagged`}
            >
              {/* Stacked bars */}
              <div className="w-full flex flex-col-reverse gap-0.5" style={{ height: '100px' }}>
                <div
                  className="w-full bg-green-500 rounded-t transition-all"
                  style={{ height: `${executedHeight}%`, minHeight: day.executed > 0 ? '2px' : '0' }}
                />
                <div
                  className="w-full bg-yellow-500 rounded-t transition-all"
                  style={{ height: `${skippedHeight}%`, minHeight: day.skipped > 0 ? '2px' : '0' }}
                />
                <div
                  className="w-full bg-orange-500 rounded-t transition-all"
                  style={{ height: `${flaggedHeight}%`, minHeight: day.flagged > 0 ? '2px' : '0' }}
                />
              </div>
              {/* Date label (show every other for readability) */}
              {idx % 2 === 0 && (
                <span className="text-[10px] text-gray-500 mt-1">
                  {new Date(day.date).toLocaleDateString('en', { month: 'short', day: 'numeric' })}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Confidence Distribution Chart - Shows distribution of confidence scores
 * Evidence-only visualization
 */
function ConfidenceDistributionChart({ stats }: { stats: AutoExecuteReviewStats | undefined }) {
  if (!stats || !stats.confidence_distribution) return null;

  const distribution = stats.confidence_distribution;
  const bands = ['0.0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0'];
  const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-emerald-500', 'bg-green-500'];
  const total = Object.values(distribution).reduce((a, b) => a + b, 0);

  if (total === 0) return null;

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-semibold text-gray-300 mb-3">Confidence Distribution</h3>
      <div className="space-y-2">
        {bands.map((band, idx) => {
          const count = distribution[band] || 0;
          const pct = total > 0 ? (count / total) * 100 : 0;
          return (
            <div key={band} className="flex items-center gap-2">
              <span className="text-xs text-gray-500 w-16">{band}</span>
              <div className="flex-1 h-4 bg-gray-700 rounded overflow-hidden">
                <div
                  className={`h-full ${colors[idx]} transition-all`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-xs text-gray-400 w-12 text-right">{count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Safety Flag Breakdown Chart - Shows which safety flags are most common
 * Evidence-only visualization
 */
function SafetyFlagBreakdownChart({ stats }: { stats: AutoExecuteReviewStats | undefined }) {
  if (!stats || !stats.flag_counts) return null;

  const flags = Object.entries(stats.flag_counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);

  if (flags.length === 0) return null;

  const maxCount = Math.max(...flags.map(([, c]) => c));

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
        <Shield className="h-4 w-4" />
        Safety Flag Breakdown
      </h3>
      <div className="space-y-2">
        {flags.map(([flag, count]) => {
          const pct = maxCount > 0 ? (count / maxCount) * 100 : 0;
          return (
            <div key={flag} className="flex items-center gap-2">
              <span className="text-xs text-gray-400 truncate flex-1">{flag}</span>
              <div className="w-24 h-3 bg-gray-700 rounded overflow-hidden">
                <div
                  className={`h-full ${getSafetyFlagColor(flag).split(' ')[0].replace('text-', 'bg-')} transition-all`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-xs text-gray-500 w-8 text-right">{count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatsOverview({ stats }: { stats: AutoExecuteReviewStats | undefined }) {
  if (!stats) return null;

  const executedPct = stats.total_decisions > 0
    ? ((stats.executed_count / stats.total_decisions) * 100).toFixed(1)
    : '0';

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="h-4 w-4 text-primary-400" />
          <span className="text-sm text-gray-400">Total Decisions</span>
        </div>
        <div className="text-2xl font-bold text-white">
          {stats.total_decisions.toLocaleString()}
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle className="h-4 w-4 text-green-400" />
          <span className="text-sm text-gray-400">Executed</span>
        </div>
        <div className="text-2xl font-bold text-green-400">
          {stats.executed_count.toLocaleString()}
          <span className="text-sm text-gray-500 ml-2">({executedPct}%)</span>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <XCircle className="h-4 w-4 text-yellow-400" />
          <span className="text-sm text-gray-400">Skipped</span>
        </div>
        <div className="text-2xl font-bold text-yellow-400">
          {stats.skipped_count.toLocaleString()}
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="h-4 w-4 text-orange-400" />
          <span className="text-sm text-gray-400">Flagged</span>
        </div>
        <div className="text-2xl font-bold text-orange-400">
          {stats.flagged_count.toLocaleString()}
        </div>
      </div>
    </div>
  );
}

function FilterBar({
  filter,
  onFilterChange,
  onRefresh,
  isRefreshing,
}: {
  filter: AutoExecuteReviewFilter;
  onFilterChange: (filter: AutoExecuteReviewFilter) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 mb-4">
      <div className="flex flex-wrap gap-4 items-center">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <span className="text-sm text-gray-400">Filters:</span>
        </div>

        {/* Decision Filter */}
        <select
          value={filter.decision || ''}
          onChange={(e) =>
            onFilterChange({
              ...filter,
              decision: e.target.value as 'EXECUTED' | 'SKIPPED' | undefined || undefined,
              page: 1,
            })
          }
          className="bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Decisions</option>
          <option value="EXECUTED">Executed</option>
          <option value="SKIPPED">Skipped</option>
        </select>

        {/* Safety Flags Filter */}
        <select
          value={filter.has_safety_flags === undefined ? '' : String(filter.has_safety_flags)}
          onChange={(e) =>
            onFilterChange({
              ...filter,
              has_safety_flags: e.target.value === '' ? undefined : e.target.value === 'true',
              page: 1,
            })
          }
          className="bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="">All Safety Status</option>
          <option value="true">With Flags</option>
          <option value="false">No Flags</option>
        </select>

        {/* Confidence Range */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">Confidence:</span>
          <input
            type="number"
            placeholder="Min"
            min="0"
            max="1"
            step="0.1"
            value={filter.min_confidence || ''}
            onChange={(e) =>
              onFilterChange({
                ...filter,
                min_confidence: e.target.value ? parseFloat(e.target.value) : undefined,
                page: 1,
              })
            }
            className="bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-white w-16 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <span className="text-gray-500">-</span>
          <input
            type="number"
            placeholder="Max"
            min="0"
            max="1"
            step="0.1"
            value={filter.max_confidence || ''}
            onChange={(e) =>
              onFilterChange({
                ...filter,
                max_confidence: e.target.value ? parseFloat(e.target.value) : undefined,
                page: 1,
              })
            }
            className="bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-sm text-white w-16 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div className="flex-1" />

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>
    </div>
  );
}

function DecisionTable({
  items,
  totalCount,
  page,
  pageSize,
  onPageChange,
  onSelectItem,
  isLoading,
}: {
  items: AutoExecuteReviewItem[];
  totalCount: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onSelectItem: (item: AutoExecuteReviewItem) => void;
  isLoading: boolean;
}) {
  const totalPages = Math.ceil(totalCount / pageSize);

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-400" />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
        <Eye className="h-12 w-12 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-400">No AUTO_EXECUTE decisions found</p>
        <p className="text-sm text-gray-500 mt-2">
          Adjust filters or wait for new decisions
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      {/* Table Header */}
      <div className="grid grid-cols-12 gap-2 p-3 bg-gray-900/50 border-b border-gray-700 text-sm font-medium text-gray-400">
        <div className="col-span-2">Timestamp</div>
        <div className="col-span-2">Invocation ID</div>
        <div className="col-span-2">Tenant</div>
        <div className="col-span-1 text-center">Decision</div>
        <div className="col-span-2 text-center">Confidence</div>
        <div className="col-span-2">Safety</div>
        <div className="col-span-1" />
      </div>

      {/* Table Rows */}
      {items.map((item) => {
        const safetyStatus = getSafetyStatus(
          item.safety_checked,
          item.safety_passed,
          item.safety_flags
        );

        return (
          <button
            key={item.invocation_id}
            onClick={() => onSelectItem(item)}
            className="w-full grid grid-cols-12 gap-2 p-3 border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors text-left group"
          >
            <div className="col-span-2 text-sm text-gray-300">
              {formatTimestamp(item.timestamp)}
            </div>
            <div className="col-span-2 font-mono text-xs text-gray-400 truncate">
              {item.invocation_id.slice(0, 12)}...
            </div>
            <div className="col-span-2 font-mono text-xs text-gray-400 truncate">
              {item.tenant_id.slice(0, 8)}...
            </div>
            <div className="col-span-1 text-center">
              <span
                className={`px-2 py-0.5 rounded text-xs font-medium ${getDecisionColor(item.decision)}`}
              >
                {item.decision}
              </span>
            </div>
            <div className="col-span-2 text-center">
              <span
                className={`font-mono text-sm ${getConfidenceColor(item.confidence_score, item.threshold)}`}
              >
                {formatConfidence(item.confidence_score)}
              </span>
              <span className="text-xs text-gray-500 ml-1">
                (≥{formatConfidence(item.threshold)})
              </span>
            </div>
            <div className="col-span-2">
              <span className={`px-2 py-0.5 rounded text-xs ${safetyStatus.color}`}>
                {safetyStatus.label}
              </span>
              {item.safety_flags.length > 0 && (
                <span className="ml-1 text-xs text-gray-500">
                  ({item.safety_flags.length})
                </span>
              )}
            </div>
            <div className="col-span-1 flex justify-end">
              <ChevronRight className="h-4 w-4 text-gray-600 group-hover:text-primary-400 transition-colors" />
            </div>
          </button>
        );
      })}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between p-3 bg-gray-900/50">
          <div className="text-sm text-gray-400">
            Showing {(page - 1) * pageSize + 1}-
            {Math.min(page * pageSize, totalCount)} of {totalCount}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm text-gray-400">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function EvidenceDrawer({
  item,
  onClose,
}: {
  item: AutoExecuteReviewItem;
  onClose: () => void;
}) {
  const safetyStatus = getSafetyStatus(
    item.safety_checked,
    item.safety_passed,
    item.safety_flags
  );

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-gray-800 border-l border-gray-700 shadow-xl z-50 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-primary-400" />
          <h2 className="text-lg font-semibold text-white">Evidence Detail</h2>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-700 rounded transition-colors"
        >
          <X className="h-5 w-5 text-gray-400" />
        </button>
      </div>

      <div className="p-4 space-y-6">
        {/* Decision Summary */}
        <div className="bg-gray-900/50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Decision Summary
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-gray-500 mb-1">Decision</div>
              <span className={`px-2 py-1 rounded text-sm font-medium ${getDecisionColor(item.decision)}`}>
                {item.decision}
              </span>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Confidence</div>
              <span className={`text-lg font-bold ${getConfidenceColor(item.confidence_score, item.threshold)}`}>
                {formatConfidence(item.confidence_score)}
              </span>
              <span className="text-xs text-gray-500 ml-1">
                (threshold: {formatConfidence(item.threshold)})
              </span>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Timestamp</div>
              <div className="text-sm text-gray-300">{formatTimestamp(item.timestamp)}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Recovery Action</div>
              <div className="text-sm text-gray-300">{item.recovery_action || 'None'}</div>
            </div>
          </div>
        </div>

        {/* Identifiers */}
        <div className="bg-gray-900/50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <Hash className="h-4 w-4" />
            Identifiers
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Invocation ID</span>
              <span className="font-mono text-gray-300">{item.invocation_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Envelope ID</span>
              <span className="font-mono text-gray-300">{item.envelope_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Tenant ID</span>
              <span className="font-mono text-gray-300">{item.tenant_id}</span>
            </div>
            {item.agent_id && (
              <div className="flex justify-between">
                <span className="text-gray-500">Agent ID</span>
                <span className="font-mono text-gray-300">{item.agent_id}</span>
              </div>
            )}
            {item.run_id && (
              <div className="flex justify-between">
                <span className="text-gray-500">Run ID</span>
                <span className="font-mono text-gray-300">{item.run_id}</span>
              </div>
            )}
          </div>
        </div>

        {/* Safety Status */}
        <div className="bg-gray-900/50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Safety Status (PIN-332)
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Status</span>
              <span className={`px-2 py-1 rounded text-sm ${safetyStatus.color}`}>
                {safetyStatus.label}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Checked</span>
              <span className={item.safety_checked ? 'text-green-400' : 'text-gray-500'}>
                {item.safety_checked ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Passed</span>
              <span className={item.safety_passed ? 'text-green-400' : 'text-red-400'}>
                {item.safety_passed ? 'Yes' : 'No'}
              </span>
            </div>

            {/* Safety Flags */}
            {item.safety_flags.length > 0 && (
              <div>
                <div className="text-xs text-gray-500 mb-2">Flags</div>
                <div className="flex flex-wrap gap-2">
                  {item.safety_flags.map((flag, idx) => (
                    <span
                      key={idx}
                      className={`px-2 py-1 rounded text-xs ${getSafetyFlagColor(flag)}`}
                    >
                      {flag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Safety Warnings */}
            {item.safety_warnings.length > 0 && (
              <div>
                <div className="text-xs text-gray-500 mb-2">Warnings</div>
                <div className="space-y-1">
                  {item.safety_warnings.map((warning, idx) => (
                    <div
                      key={idx}
                      className="text-xs text-yellow-400 bg-yellow-900/20 px-2 py-1 rounded"
                    >
                      {warning}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Identity & Authority */}
        <div className="bg-gray-900/50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Identity & Authority
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Caller ID</span>
              <span className="font-mono text-gray-300">{item.caller_id || 'Not set'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Impersonation Declared</span>
              <span className={item.impersonation_declared ? 'text-yellow-400' : 'text-gray-400'}>
                {item.impersonation_declared ? 'Yes' : 'No'}
              </span>
            </div>
            {item.impersonation_reason && (
              <div className="flex justify-between">
                <span className="text-gray-500">Impersonation Reason</span>
                <span className="text-gray-300">{item.impersonation_reason}</span>
              </div>
            )}
            {item.authority_path.length > 0 && (
              <div>
                <div className="text-xs text-gray-500 mb-1">Authority Path</div>
                <div className="font-mono text-xs text-gray-400">
                  {item.authority_path.join(' → ')}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Integrity Hashes */}
        <div className="bg-gray-900/50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
            <Hash className="h-4 w-4" />
            Integrity Hashes
          </h3>
          <div className="space-y-2 text-sm">
            <div>
              <div className="text-xs text-gray-500 mb-1">Input Hash</div>
              <div className="font-mono text-xs text-gray-400 break-all">{item.input_hash}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Plan Hash</div>
              <div className="font-mono text-xs text-gray-400 break-all">{item.plan_hash}</div>
            </div>
            {item.trace_hash && (
              <div>
                <div className="text-xs text-gray-500 mb-1">Trace Hash</div>
                <div className="font-mono text-xs text-gray-400 break-all">{item.trace_hash}</div>
              </div>
            )}
          </div>
        </div>

        {/* Evidence Snapshot */}
        {item.evidence_snapshot && Object.keys(item.evidence_snapshot).length > 0 && (
          <div className="bg-gray-900/50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Evidence Snapshot
            </h3>
            <pre className="text-xs text-gray-400 bg-gray-950 p-3 rounded overflow-x-auto">
              {JSON.stringify(item.evidence_snapshot, null, 2)}
            </pre>
          </div>
        )}

        {/* Read-Only Notice */}
        <div className="bg-emerald-900/20 border border-emerald-800 rounded-lg p-3 text-sm text-emerald-400">
          <strong>READ-ONLY:</strong> This is an evidence view only. No actions can be
          taken from this dashboard. AUTO_EXECUTE behavior is not affected.
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function AutoExecuteReviewPage() {
  const [filter, setFilter] = useState<AutoExecuteReviewFilter>({
    page: 1,
    page_size: PAGE_SIZE,
  });
  const [selectedItem, setSelectedItem] = useState<AutoExecuteReviewItem | null>(null);

  // Fetch decisions list
  const {
    data: listData,
    isLoading: listLoading,
    refetch: refetchList,
    isFetching: listFetching,
  } = useQuery({
    queryKey: ['autoExecuteReview', 'list', filter],
    queryFn: () => listAutoExecuteDecisions(filter),
    staleTime: 10000,
    refetchInterval: POLL_INTERVAL_MS,
  });

  // Fetch stats
  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['autoExecuteReview', 'stats'],
    queryFn: () => getAutoExecuteStats(),
    staleTime: 30000,
    refetchInterval: POLL_INTERVAL_MS,
  });

  const handleRefresh = useCallback(() => {
    refetchList();
    refetchStats();
  }, [refetchList, refetchStats]);

  const handlePageChange = useCallback((newPage: number) => {
    setFilter((prev) => ({ ...prev, page: newPage }));
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Eye className="h-8 w-8 text-amber-400" />
          <h1 className="text-2xl font-bold text-white">AUTO_EXECUTE Review</h1>
        </div>
        <p className="text-gray-400">
          Evidence dashboard for SUB-019 AUTO_EXECUTE decisions
        </p>

        {/* Advisory Notice - PIN-333 Constraint */}
        <div className="mt-4 p-3 bg-amber-900/20 border border-amber-800 rounded-lg text-sm text-amber-400">
          <strong>EVIDENCE-ONLY:</strong> This dashboard displays execution evidence
          only. No approval, rejection, pause, or override actions are available.
          AUTO_EXECUTE behavior and thresholds are not modified by this view.
        </div>
      </div>

      {/* Stats Overview */}
      <StatsOverview stats={stats} />

      {/* Daily Trend Chart - Evidence-only visualization */}
      <DailyTrendChart stats={stats} />

      {/* Additional Charts - Confidence & Safety */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <ConfidenceDistributionChart stats={stats} />
        <SafetyFlagBreakdownChart stats={stats} />
      </div>

      {/* Filter Bar */}
      <FilterBar
        filter={filter}
        onFilterChange={setFilter}
        onRefresh={handleRefresh}
        isRefreshing={listFetching}
      />

      {/* Decision Table */}
      <DecisionTable
        items={listData?.items || []}
        totalCount={listData?.total_count || 0}
        page={filter.page || 1}
        pageSize={filter.page_size || PAGE_SIZE}
        onPageChange={handlePageChange}
        onSelectItem={setSelectedItem}
        isLoading={listLoading}
      />

      {/* Summary Footer */}
      {listData && (
        <div className="mt-4 flex gap-4 text-sm text-gray-500">
          <span>
            Executed: <span className="text-green-400">{listData.executed_count}</span>
          </span>
          <span>
            Skipped: <span className="text-yellow-400">{listData.skipped_count}</span>
          </span>
          <span>
            Flagged: <span className="text-orange-400">{listData.flagged_count}</span>
          </span>
        </div>
      )}

      {/* Evidence Drawer */}
      {selectedItem && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setSelectedItem(null)}
          />
          <EvidenceDrawer item={selectedItem} onClose={() => setSelectedItem(null)} />
        </>
      )}
    </div>
  );
}
