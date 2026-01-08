/**
 * Preflight Console Debug Logger
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: runtime
 *   Execution: sync
 * Role: Browser console logging for L2.1 projection debugging
 * Reference: PIN-352
 *
 * Only active when VITE_PREFLIGHT_MODE=true
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  category: string;
  message: string;
  data?: unknown;
}

// Check if preflight mode is active
const isPreflight = import.meta.env.VITE_PREFLIGHT_MODE === 'true';

// Log history for export
const logHistory: LogEntry[] = [];
const MAX_HISTORY = 500;

// Styling for console output
const STYLES = {
  prefix: 'background: #d97706; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold;',
  debug: 'color: #9ca3af;',
  info: 'color: #60a5fa;',
  warn: 'color: #fbbf24;',
  error: 'color: #f87171;',
  category: 'color: #a78bfa; font-weight: bold;',
  data: 'color: #34d399;',
};

function formatTimestamp(): string {
  return new Date().toISOString().split('T')[1].slice(0, 12);
}

function addToHistory(entry: LogEntry): void {
  logHistory.push(entry);
  if (logHistory.length > MAX_HISTORY) {
    logHistory.shift();
  }
}

function log(level: LogLevel, category: string, message: string, data?: unknown): void {
  if (!isPreflight) return;

  const timestamp = formatTimestamp();
  const entry: LogEntry = { timestamp, level, category, message, data };
  addToHistory(entry);

  const levelStyle = STYLES[level];
  const prefix = `%c PREFLIGHT %c ${timestamp} %c[${category}]%c ${message}`;

  if (data !== undefined) {
    console[level](
      prefix,
      STYLES.prefix,
      levelStyle,
      STYLES.category,
      levelStyle,
      data
    );
  } else {
    console[level](
      prefix,
      STYLES.prefix,
      levelStyle,
      STYLES.category,
      levelStyle
    );
  }
}

// ============================================================================
// Public API
// ============================================================================

export const preflightLogger = {
  // Basic logging
  debug: (category: string, message: string, data?: unknown) => log('debug', category, message, data),
  info: (category: string, message: string, data?: unknown) => log('info', category, message, data),
  warn: (category: string, message: string, data?: unknown) => log('warn', category, message, data),
  error: (category: string, message: string, data?: unknown) => log('error', category, message, data),

  // Projection-specific logging
  projection: {
    loadStart: () => log('info', 'PROJECTION', 'Loading ui_projection_lock.json...'),
    loadSuccess: (stats: { domains: number; panels: number; controls: number }) =>
      log('info', 'PROJECTION', `Loaded: ${stats.domains} domains, ${stats.panels} panels, ${stats.controls} controls`, stats),
    loadError: (error: Error) => log('error', 'PROJECTION', `Failed to load: ${error.message}`, error),
    cached: () => log('debug', 'PROJECTION', 'Using cached projection'),
  },

  // Navigation logging
  nav: {
    domainClick: (domain: string) => log('info', 'NAV', `Domain clicked: ${domain}`),
    panelClick: (panelId: string, panelName: string) => log('info', 'NAV', `Panel clicked: ${panelName}`, { panelId }),
    routeChange: (from: string, to: string) => log('debug', 'NAV', `Route: ${from} → ${to}`),
  },

  // Sidebar logging
  sidebar: {
    render: (domainCount: number) => log('debug', 'SIDEBAR', `Rendering ${domainCount} domains`),
    expand: (domain: string) => log('debug', 'SIDEBAR', `Expanded: ${domain}`),
    collapse: (domain: string) => log('debug', 'SIDEBAR', `Collapsed: ${domain}`),
  },

  // Domain page logging
  domain: {
    render: (domain: string, subdomains: number, panels: number) =>
      log('info', 'DOMAIN', `Rendering ${domain}: ${subdomains} subdomains, ${panels} panels`),
    subdomainExpand: (subdomain: string) => log('debug', 'DOMAIN', `Subdomain expanded: ${subdomain}`),
    topicExpand: (topic: string) => log('debug', 'DOMAIN', `Topic expanded: ${topic}`),
  },

  // Panel view logging
  panel: {
    render: (panelId: string, panelName: string) =>
      log('info', 'PANEL', `Rendering panel: ${panelName}`, { panelId }),
    controlClick: (controlType: string, panelId: string) =>
      log('debug', 'PANEL', `Control clicked: ${controlType}`, { panelId }),
    notFound: (route: string) =>
      log('warn', 'PANEL', `Panel not found at route: ${route}`),
  },

  // API/fetch logging
  api: {
    request: (endpoint: string) => log('debug', 'API', `Request: ${endpoint}`),
    success: (endpoint: string, status: number) => log('debug', 'API', `Success: ${endpoint} (${status})`),
    error: (endpoint: string, error: Error) => log('error', 'API', `Error: ${endpoint}`, error),
  },

  // Utility methods
  group: (label: string) => {
    if (isPreflight) console.group(`%c PREFLIGHT %c ${label}`, STYLES.prefix, 'color: white; font-weight: bold;');
  },
  groupEnd: () => {
    if (isPreflight) console.groupEnd();
  },
  table: (data: unknown) => {
    if (isPreflight) console.table(data);
  },

  // Export log history
  getHistory: () => [...logHistory],
  exportHistory: () => {
    if (!isPreflight) return;
    const blob = new Blob([JSON.stringify(logHistory, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `preflight-logs-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    log('info', 'EXPORT', `Exported ${logHistory.length} log entries`);
  },

  // Clear history
  clear: () => {
    logHistory.length = 0;
    if (isPreflight) {
      console.clear();
      log('info', 'LOGGER', 'Log history cleared');
    }
  },

  // Check if active
  isActive: () => isPreflight,
};

// Expose to window for debugging
if (isPreflight && typeof window !== 'undefined') {
  (window as any).preflightLogger = preflightLogger;
  (window as any).exportPreflightLogs = preflightLogger.exportHistory;

  // Initial log on load
  console.log(
    '%c PREFLIGHT MODE ACTIVE %c Use window.preflightLogger for debugging',
    'background: #d97706; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 14px;',
    'color: #9ca3af; font-size: 12px;'
  );
}

export default preflightLogger;
