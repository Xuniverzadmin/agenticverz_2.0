/**
 * Logs Page - Phase 4 Implementation (Historical)
 *
 * Historical log viewing:
 * - Time-indexed log feed
 * - Click any log to view incident detail
 * - Export capability
 * - Search and filter
 *
 * Complement to Live Activity - this is the archive.
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { guardApi } from '../../api/guard';
import { logger } from '../../lib/consoleLogger';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  category: 'request' | 'policy' | 'killswitch' | 'system';
  message: string;
  incident_id?: string;
  user_id?: string;
  call_id?: string;
  metadata?: Record<string, any>;
}

const LEVEL_CONFIG = {
  info: { icon: 'ℹ️', color: 'text-blue-400', bg: 'bg-blue-500/10' },
  warning: { icon: '⚠️', color: 'text-amber-400', bg: 'bg-amber-500/10' },
  error: { icon: '❌', color: 'text-red-400', bg: 'bg-red-500/10' },
};

const CATEGORY_CONFIG = {
  request: { icon: '📥', label: 'Request' },
  policy: { icon: '🔒', label: 'Policy' },
  killswitch: { icon: '🚨', label: 'Kill Switch' },
  system: { icon: '⚙️', label: 'System' },
};

// Demo log data
function generateDemoLogs(): LogEntry[] {
  const logs: LogEntry[] = [];
  const now = Date.now();

  for (let i = 0; i < 100; i++) {
    const timestamp = new Date(now - i * 60000 * Math.random() * 10).toISOString();
    const levels: Array<'info' | 'warning' | 'error'> = ['info', 'info', 'info', 'warning', 'error'];
    const categories: Array<'request' | 'policy' | 'killswitch' | 'system'> = ['request', 'request', 'policy', 'system'];

    const level = levels[Math.floor(Math.random() * levels.length)];
    const category = categories[Math.floor(Math.random() * categories.length)];

    logs.push({
      id: `log_${i}`,
      timestamp,
      level,
      category,
      message: getDemoLogMessage(category, level),
      user_id: Math.random() > 0.3 ? `user_${Math.floor(Math.random() * 1000)}` : undefined,
      call_id: Math.random() > 0.5 ? `call_${Math.floor(Math.random() * 10000)}` : undefined,
      incident_id: level === 'error' ? `inc_${Math.floor(Math.random() * 100)}` : undefined,
    });
  }

  return logs.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

function getDemoLogMessage(category: string, level: string): string {
  const messages: Record<string, Record<string, string[]>> = {
    request: {
      info: ['Chat completion processed', 'Embedding generated', 'Request queued'],
      warning: ['High latency detected (>2s)', 'Approaching rate limit'],
      error: ['Request timeout', 'Model unavailable'],
    },
    policy: {
      info: ['All policies passed', 'Content check: PASS'],
      warning: ['Content flagged for review', 'Near budget threshold'],
      error: ['Policy violation: prompt injection', 'Rate limit exceeded'],
    },
    killswitch: {
      info: ['Kill switch check: OK'],
      warning: ['Kill switch primed'],
      error: ['Kill switch activated'],
    },
    system: {
      info: ['Health check passed', 'Connection pool refreshed'],
      warning: ['Memory usage high', 'Connection pool low'],
      error: ['Database connection lost', 'Redis unavailable'],
    },
  };

  const categoryMessages = messages[category] || messages.system;
  const levelMessages = categoryMessages[level] || categoryMessages.info;
  return levelMessages[Math.floor(Math.random() * levelMessages.length)];
}

export function LogsPage() {
  const [logs] = useState<LogEntry[]>(generateDemoLogs());
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null);
  const [filters, setFilters] = useState({
    level: 'all' as 'all' | 'info' | 'warning' | 'error',
    category: 'all' as 'all' | 'request' | 'policy' | 'killswitch' | 'system',
    search: '',
    timeRange: '1h' as '1h' | '6h' | '24h' | '7d',
  });

  useEffect(() => {
    logger.componentMount('LogsPage');
    return () => logger.componentUnmount('LogsPage');
  }, []);

  // Filter logs
  const filteredLogs = logs.filter(log => {
    if (filters.level !== 'all' && log.level !== filters.level) return false;
    if (filters.category !== 'all' && log.category !== filters.category) return false;
    if (filters.search && !log.message.toLowerCase().includes(filters.search.toLowerCase())) return false;
    return true;
  });

  // Stats
  const stats = {
    total: filteredLogs.length,
    errors: filteredLogs.filter(l => l.level === 'error').length,
    warnings: filteredLogs.filter(l => l.level === 'warning').length,
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <span className="text-2xl">📜</span>
              Event Logs
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              {stats.total} entries • {stats.errors} errors • {stats.warnings} warnings
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Time Range */}
            <select
              value={filters.timeRange}
              onChange={(e) => setFilters(f => ({ ...f, timeRange: e.target.value as any }))}
              className="bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm"
            >
              <option value="1h">Last Hour</option>
              <option value="6h">Last 6 Hours</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
            </select>

            {/* Level Filter */}
            <select
              value={filters.level}
              onChange={(e) => setFilters(f => ({ ...f, level: e.target.value as any }))}
              className="bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm"
            >
              <option value="all">All Levels</option>
              <option value="error">🔴 Errors</option>
              <option value="warning">⚠️ Warnings</option>
              <option value="info">ℹ️ Info</option>
            </select>

            {/* Category Filter */}
            <select
              value={filters.category}
              onChange={(e) => setFilters(f => ({ ...f, category: e.target.value as any }))}
              className="bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm"
            >
              <option value="all">All Categories</option>
              <option value="request">📥 Requests</option>
              <option value="policy">🔒 Policy</option>
              <option value="killswitch">🚨 Kill Switch</option>
              <option value="system">⚙️ System</option>
            </select>

            {/* Search */}
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters(f => ({ ...f, search: e.target.value }))}
              placeholder="Search logs..."
              className="bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm w-48"
            />

            {/* Export */}
            <button className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium">
              📥 Export
            </button>
          </div>
        </div>
      </div>

      {/* Log List */}
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-slate-800 border-b border-slate-700">
            <tr className="text-left text-xs text-slate-400">
              <th className="p-3 w-40">Timestamp</th>
              <th className="p-3 w-20">Level</th>
              <th className="p-3 w-28">Category</th>
              <th className="p-3">Message</th>
              <th className="p-3 w-28">User</th>
              <th className="p-3 w-20">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {filteredLogs.map((log) => {
              const levelConfig = LEVEL_CONFIG[log.level];
              const catConfig = CATEGORY_CONFIG[log.category];

              return (
                <tr
                  key={log.id}
                  onClick={() => setSelectedLog(log)}
                  className={`
                    hover:bg-slate-800/50 cursor-pointer transition-colors
                    ${selectedLog?.id === log.id ? 'bg-blue-500/10' : ''}
                  `}
                >
                  <td className="p-3 text-xs font-mono text-slate-400">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="p-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${levelConfig.bg} ${levelConfig.color}`}>
                      {levelConfig.icon} {log.level}
                    </span>
                  </td>
                  <td className="p-3 text-sm text-slate-400">
                    {catConfig.icon} {catConfig.label}
                  </td>
                  <td className="p-3 text-sm">
                    {log.message}
                    {log.incident_id && (
                      <span className="ml-2 text-xs bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded">
                        {log.incident_id}
                      </span>
                    )}
                  </td>
                  <td className="p-3 text-xs font-mono text-slate-500">
                    {log.user_id || '—'}
                  </td>
                  <td className="p-3">
                    {log.incident_id && (
                      <button className="text-xs text-blue-400 hover:text-blue-300">
                        Inspect →
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Detail Panel */}
      {selectedLog && (
        <div className="h-48 bg-slate-800 border-t border-slate-700 p-4 overflow-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold">Log Details</h3>
            <button
              onClick={() => setSelectedLog(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-slate-400">Log ID:</span>
              <span className="ml-2 font-mono">{selectedLog.id}</span>
            </div>
            <div>
              <span className="text-slate-400">Timestamp:</span>
              <span className="ml-2">{new Date(selectedLog.timestamp).toISOString()}</span>
            </div>
            <div>
              <span className="text-slate-400">Call ID:</span>
              <span className="ml-2 font-mono">{selectedLog.call_id || 'N/A'}</span>
            </div>
            <div>
              <span className="text-slate-400">Incident:</span>
              {selectedLog.incident_id ? (
                <button className="ml-2 text-blue-400 hover:underline">{selectedLog.incident_id}</button>
              ) : (
                <span className="ml-2">N/A</span>
              )}
            </div>
          </div>

          <div className="mt-4">
            <span className="text-slate-400 text-sm">Full Message:</span>
            <div className="mt-2 bg-slate-900 rounded p-3 text-sm">
              {selectedLog.message}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LogsPage;
