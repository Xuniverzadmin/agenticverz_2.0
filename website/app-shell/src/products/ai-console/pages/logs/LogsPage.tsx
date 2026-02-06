/**
 * Customer Logs Page - Raw Truth & Audit Trail
 *
 * Customer Console v1 Constitution: Logs Domain
 * Question: "What is the raw truth?"
 *
 * Shows:
 * - Audit trail (chronological events)
 * - Trace records (execution proof)
 * - Raw log entries (uninterpreted)
 *
 * Design Principles:
 * - No interpretation (raw facts only)
 * - Chronological ordering
 * - Filterable by type, severity, time range
 * - Exportable for compliance
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { logger } from '@/lib/consoleLogger';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  category: 'execution' | 'policy' | 'auth' | 'system' | 'audit';
  message: string;
  metadata?: Record<string, unknown>;
  run_id?: string;
  trace_id?: string;
}

interface LogsResponse {
  logs: LogEntry[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

const LEVEL_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  debug: { label: 'DEBUG', color: 'text-slate-400', bg: 'bg-slate-500/20' },
  info: { label: 'INFO', color: 'text-blue-400', bg: 'bg-blue-500/20' },
  warn: { label: 'WARN', color: 'text-amber-400', bg: 'bg-amber-500/20' },
  error: { label: 'ERROR', color: 'text-red-400', bg: 'bg-red-500/20' },
};

const CATEGORY_CONFIG: Record<string, { label: string; icon: string }> = {
  execution: { label: 'Execution', icon: '⚡' },
  policy: { label: 'Policy', icon: '📜' },
  auth: { label: 'Auth', icon: '🔐' },
  system: { label: 'System', icon: '🖥️' },
  audit: { label: 'Audit', icon: '📋' },
};

function formatTimestamp(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function formatTimestampFull(isoString: string): string {
  const date = new Date(isoString);
  return date.toISOString();
}

export function LogsPage() {
  const [page, setPage] = useState(1);
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    logger.componentMount('CustomerLogsPage');
    return () => logger.componentUnmount('CustomerLogsPage');
  }, []);

  // Fetch logs
  const { data, isLoading, refetch } = useQuery<LogsResponse>({
    queryKey: ['customer', 'logs', page, levelFilter, categoryFilter],
    queryFn: async () => {
      // In production, this would call: GET /api/v1/logs?page={page}&level={level}&category={category}
      // For now, return demo data
      const now = Date.now();

      const demoLogs: LogEntry[] = [
        {
          id: 'log_001',
          timestamp: new Date(now - 30000).toISOString(),
          level: 'info',
          category: 'execution',
          message: 'Execution completed successfully',
          run_id: 'run_abc123',
          trace_id: 'trace_001',
          metadata: { skill: 'web_search', duration_ms: 4523, tokens_used: 1250 },
        },
        {
          id: 'log_002',
          timestamp: new Date(now - 60000).toISOString(),
          level: 'warn',
          category: 'policy',
          message: 'Budget threshold reached (75%)',
          metadata: { budget_used_cents: 3750, budget_limit_cents: 5000, threshold: 0.75 },
        },
        {
          id: 'log_003',
          timestamp: new Date(now - 120000).toISOString(),
          level: 'error',
          category: 'execution',
          message: 'Execution timeout: skill exceeded 30s limit',
          run_id: 'run_def456',
          trace_id: 'trace_002',
          metadata: { skill: 'code_executor', timeout_ms: 30000, actual_ms: 32145 },
        },
        {
          id: 'log_004',
          timestamp: new Date(now - 180000).toISOString(),
          level: 'info',
          category: 'auth',
          message: 'API key authenticated',
          metadata: { key_prefix: 'sk_live_...', ip: '192.168.1.100', user_agent: 'aos-sdk/1.0' },
        },
        {
          id: 'log_005',
          timestamp: new Date(now - 240000).toISOString(),
          level: 'info',
          category: 'audit',
          message: 'Policy updated: max_cost_per_request',
          metadata: { old_value: 25, new_value: 50, updated_by: 'user@example.com' },
        },
        {
          id: 'log_006',
          timestamp: new Date(now - 300000).toISOString(),
          level: 'debug',
          category: 'system',
          message: 'Health check completed',
          metadata: { services: { api: 'healthy', db: 'healthy', redis: 'healthy' } },
        },
        {
          id: 'log_007',
          timestamp: new Date(now - 360000).toISOString(),
          level: 'info',
          category: 'execution',
          message: 'Execution started',
          run_id: 'run_ghi789',
          trace_id: 'trace_003',
          metadata: { skill: 'data_analysis', stages_planned: 4 },
        },
        {
          id: 'log_008',
          timestamp: new Date(now - 420000).toISOString(),
          level: 'warn',
          category: 'policy',
          message: 'Rate limit approaching (80%)',
          metadata: { requests_per_minute: 48, limit_per_minute: 60 },
        },
        {
          id: 'log_009',
          timestamp: new Date(now - 480000).toISOString(),
          level: 'info',
          category: 'execution',
          message: 'Execution completed successfully',
          run_id: 'run_ghi789',
          trace_id: 'trace_003',
          metadata: { skill: 'data_analysis', duration_ms: 18234, tokens_used: 4500 },
        },
        {
          id: 'log_010',
          timestamp: new Date(now - 540000).toISOString(),
          level: 'error',
          category: 'auth',
          message: 'Invalid API key rejected',
          metadata: { key_prefix: 'sk_test_...', ip: '10.0.0.50', reason: 'key_expired' },
        },
      ];

      // Apply filters
      let filteredLogs = demoLogs;
      if (levelFilter !== 'all') {
        filteredLogs = filteredLogs.filter(log => log.level === levelFilter);
      }
      if (categoryFilter !== 'all') {
        filteredLogs = filteredLogs.filter(log => log.category === categoryFilter);
      }
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filteredLogs = filteredLogs.filter(log =>
          log.message.toLowerCase().includes(query) ||
          log.run_id?.toLowerCase().includes(query) ||
          log.trace_id?.toLowerCase().includes(query)
        );
      }

      return {
        logs: filteredLogs,
        total: filteredLogs.length,
        page: 1,
        per_page: 50,
        has_more: false,
      };
    },
    refetchInterval: 30000,
    staleTime: 10000,
  });

  const logs = data?.logs ?? [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading logs...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <span>📋</span> Logs
          </h1>
          <p className="text-slate-400 mt-1">
            What is the raw truth
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 bg-navy-elevated border border-navy-border hover:bg-navy-subtle rounded-lg text-sm text-slate-300 flex items-center gap-2 transition-colors"
          >
            <span>🔄</span> Refresh
          </button>
          <button
            className="px-3 py-1.5 bg-navy-elevated border border-accent-info/30 text-accent-info hover:bg-navy-subtle rounded-lg text-sm flex items-center gap-2 transition-colors"
          >
            <span>📥</span> Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center gap-4">
        {/* Search */}
        <div className="flex-1 max-w-md">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search logs..."
            className="w-full px-4 py-2 bg-navy-inset border border-navy-border rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-accent-info focus:border-transparent"
          />
        </div>

        {/* Level Filter */}
        <select
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="px-4 py-2 bg-navy-elevated border border-navy-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-accent-info"
        >
          <option value="all">All Levels</option>
          <option value="debug">Debug</option>
          <option value="info">Info</option>
          <option value="warn">Warning</option>
          <option value="error">Error</option>
        </select>

        {/* Category Filter */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-4 py-2 bg-navy-elevated border border-navy-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-accent-info"
        >
          <option value="all">All Categories</option>
          <option value="execution">Execution</option>
          <option value="policy">Policy</option>
          <option value="auth">Auth</option>
          <option value="system">System</option>
          <option value="audit">Audit</option>
        </select>
      </div>

      {/* Stats Bar */}
      <div className="mb-6 grid grid-cols-5 gap-4">
        {Object.entries(LEVEL_CONFIG).map(([level, config]) => {
          const count = logs.filter(l => l.level === level).length;
          return (
            <div
              key={level}
              className={`bg-navy-surface border border-navy-border rounded-lg p-3 cursor-pointer hover:border-accent-info/30 transition-colors ${
                levelFilter === level ? 'border-accent-info/50' : ''
              }`}
              onClick={() => setLevelFilter(levelFilter === level ? 'all' : level)}
            >
              <div className={`text-xs ${config.color} font-medium`}>{config.label}</div>
              <div className="text-xl font-bold text-white">{count}</div>
            </div>
          );
        })}
        <div className="bg-navy-surface border border-navy-border rounded-lg p-3">
          <div className="text-xs text-slate-400 font-medium">TOTAL</div>
          <div className="text-xl font-bold text-white">{logs.length}</div>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Logs List */}
        <div className="flex-1">
          <div className="bg-navy-surface rounded-xl border border-navy-border overflow-hidden">
            {logs.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                No logs match the current filters
              </div>
            ) : (
              <div className="divide-y divide-navy-border">
                {logs.map((log) => {
                  const levelConfig = LEVEL_CONFIG[log.level];
                  const categoryConfig = CATEGORY_CONFIG[log.category];
                  const isSelected = selectedLog?.id === log.id;

                  return (
                    <div
                      key={log.id}
                      onClick={() => setSelectedLog(log)}
                      className={`
                        p-4 cursor-pointer transition-colors
                        ${isSelected ? 'bg-navy-elevated' : 'hover:bg-navy-elevated/50'}
                      `}
                    >
                      <div className="flex items-start gap-3">
                        {/* Level Badge */}
                        <span className={`
                          px-2 py-0.5 rounded text-xs font-mono font-medium
                          ${levelConfig.color} ${levelConfig.bg}
                        `}>
                          {levelConfig.label}
                        </span>

                        {/* Category */}
                        <span className="text-slate-400 text-sm flex items-center gap-1">
                          <span>{categoryConfig.icon}</span>
                          <span>{categoryConfig.label}</span>
                        </span>

                        {/* Timestamp */}
                        <span className="text-slate-500 text-sm ml-auto font-mono">
                          {formatTimestamp(log.timestamp)}
                        </span>
                      </div>

                      {/* Message */}
                      <div className="mt-2 text-white">
                        {log.message}
                      </div>

                      {/* Run/Trace IDs */}
                      {(log.run_id || log.trace_id) && (
                        <div className="mt-2 flex items-center gap-4 text-xs">
                          {log.run_id && (
                            <span className="text-slate-400">
                              Run: <span className="font-mono text-slate-300">{log.run_id}</span>
                            </span>
                          )}
                          {log.trace_id && (
                            <span className="text-slate-400">
                              Trace: <span className="font-mono text-slate-300">{log.trace_id}</span>
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Pagination */}
          {data?.has_more && (
            <div className="mt-4 text-center">
              <button
                onClick={() => setPage(p => p + 1)}
                className="px-4 py-2 bg-navy-elevated border border-navy-border rounded-lg text-sm text-slate-300 hover:bg-navy-subtle transition-colors"
              >
                Load More
              </button>
            </div>
          )}
        </div>

        {/* Log Details Panel */}
        {selectedLog && (
          <div className="w-96">
            <LogDetailsPanel log={selectedLog} onClose={() => setSelectedLog(null)} />
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Log Details Panel - Shows full log entry with metadata
 */
function LogDetailsPanel({ log, onClose }: { log: LogEntry; onClose: () => void }) {
  const levelConfig = LEVEL_CONFIG[log.level];
  const categoryConfig = CATEGORY_CONFIG[log.category];

  return (
    <div className="bg-navy-surface rounded-xl border border-navy-border p-4 sticky top-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-white">Log Details</h3>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>

      <div className="space-y-4">
        {/* Level & Category */}
        <div className="flex items-center gap-3">
          <span className={`
            px-2 py-0.5 rounded text-xs font-mono font-medium
            ${levelConfig.color} ${levelConfig.bg}
          `}>
            {levelConfig.label}
          </span>
          <span className="text-slate-300 text-sm flex items-center gap-1">
            <span>{categoryConfig.icon}</span>
            <span>{categoryConfig.label}</span>
          </span>
        </div>

        {/* Timestamp */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Timestamp</div>
          <div className="font-mono text-sm text-slate-300 bg-navy-inset rounded px-2 py-1">
            {formatTimestampFull(log.timestamp)}
          </div>
        </div>

        {/* Message */}
        <div>
          <div className="text-xs text-slate-500 mb-1">Message</div>
          <div className="text-white bg-navy-inset rounded px-3 py-2">
            {log.message}
          </div>
        </div>

        {/* IDs */}
        {(log.run_id || log.trace_id) && (
          <div className="pt-4 border-t border-navy-border">
            <div className="text-xs text-slate-500 font-bold uppercase tracking-wide mb-3">
              References
            </div>
            <div className="space-y-2">
              {log.run_id && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Run ID</span>
                  <span className="font-mono text-slate-300">{log.run_id}</span>
                </div>
              )}
              {log.trace_id && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Trace ID</span>
                  <span className="font-mono text-slate-300">{log.trace_id}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Metadata */}
        {log.metadata && Object.keys(log.metadata).length > 0 && (
          <div className="pt-4 border-t border-navy-border">
            <div className="text-xs text-slate-500 font-bold uppercase tracking-wide mb-3">
              Metadata
            </div>
            <div className="bg-navy-inset rounded-lg p-3 overflow-x-auto">
              <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap">
                {JSON.stringify(log.metadata, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Log ID */}
        <div className="pt-4 border-t border-navy-border">
          <div className="text-xs text-slate-500 mb-1">Log ID</div>
          <div className="font-mono text-xs text-slate-400 bg-navy-inset rounded px-2 py-1">
            {log.id}
          </div>
        </div>
      </div>
    </div>
  );
}

export default LogsPage;
