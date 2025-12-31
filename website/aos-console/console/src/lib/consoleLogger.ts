// Layer: L1 — Product Experience
// Product: ai-console
// Temporal:
//   Trigger: user
//   Execution: sync
// Role: Console logging utility
// Callers: All frontend components
// Allowed Imports: L2
// Forbidden Imports: L3, L4, L5, L6
// Reference: Frontend Utilities

/**
 * Console Logger - Browser Event Capture System
 *
 * Captures and logs all console events for debugging.
 * Outputs structured logs to browser console and optional external collector.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEvent {
  timestamp: string;
  level: LogLevel;
  category: string;
  message: string;
  data?: unknown;
  stack?: string;
}

class ConsoleLogger {
  private enabled: boolean = true;
  private events: LogEvent[] = [];
  private maxEvents: number = 100;

  constructor() {
    // Initialize with environment check
    this.enabled = typeof window !== 'undefined';

    if (this.enabled) {
      this.setupGlobalErrorHandlers();
    }
  }

  private setupGlobalErrorHandlers() {
    // Capture unhandled errors
    window.addEventListener('error', (event) => {
      this.error('UNHANDLED_ERROR', event.message, {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
      });
    });

    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.error('UNHANDLED_REJECTION', String(event.reason), {
        reason: event.reason,
      });
    });
  }

  private formatTimestamp(): string {
    return new Date().toISOString();
  }

  private log(level: LogLevel, category: string, message: string, data?: unknown) {
    if (!this.enabled) return;

    const event: LogEvent = {
      timestamp: this.formatTimestamp(),
      level,
      category,
      message,
      data,
    };

    // Store event
    this.events.push(event);
    if (this.events.length > this.maxEvents) {
      this.events.shift();
    }

    // Format console output
    const prefix = `[${event.timestamp.split('T')[1].split('.')[0]}] [${category}]`;
    const style = this.getStyle(level);

    switch (level) {
      case 'debug':
        console.debug(`%c${prefix} ${message}`, style, data || '');
        break;
      case 'info':
        console.info(`%c${prefix} ${message}`, style, data || '');
        break;
      case 'warn':
        console.warn(`%c${prefix} ${message}`, style, data || '');
        break;
      case 'error':
        console.error(`%c${prefix} ${message}`, style, data || '');
        break;
    }
  }

  private getStyle(level: LogLevel): string {
    switch (level) {
      case 'debug':
        return 'color: #6b7280';
      case 'info':
        return 'color: #3b82f6';
      case 'warn':
        return 'color: #f59e0b; font-weight: bold';
      case 'error':
        return 'color: #ef4444; font-weight: bold';
    }
  }

  // Public API
  debug(category: string, message: string, data?: unknown) {
    this.log('debug', category, message, data);
  }

  info(category: string, message: string, data?: unknown) {
    this.log('info', category, message, data);
  }

  warn(category: string, message: string, data?: unknown) {
    this.log('warn', category, message, data);
  }

  error(category: string, message: string, data?: unknown) {
    this.log('error', category, message, data);
  }

  // API call logging
  apiCall(endpoint: string, method: string, status?: number, duration?: number) {
    const level = status && status >= 400 ? 'error' : 'info';
    this.log(level, 'API', `${method} ${endpoint}`, { status, duration });
  }

  // Event tracking
  userEvent(action: string, target: string, data?: unknown) {
    this.log('info', 'USER_EVENT', `${action} on ${target}`, data);
  }

  // Component lifecycle
  componentMount(name: string) {
    this.log('debug', 'COMPONENT', `Mounted: ${name}`);
  }

  componentUnmount(name: string) {
    this.log('debug', 'COMPONENT', `Unmounted: ${name}`);
  }

  // State changes
  stateChange(name: string, oldValue: unknown, newValue: unknown) {
    this.log('debug', 'STATE', `${name} changed`, { from: oldValue, to: newValue });
  }

  // Get all events for debugging
  getEvents(): LogEvent[] {
    return [...this.events];
  }

  // Clear events
  clearEvents() {
    this.events = [];
  }

  // Export events as JSON
  exportEvents(): string {
    return JSON.stringify(this.events, null, 2);
  }
}

// Singleton instance
export const logger = new ConsoleLogger();

// Export for global access (debugging) - only in dev/demo mode
// Production should access via UI export, not global window object
if (typeof window !== 'undefined') {
  // Check if we're in production mode
  const isProduction = window.location.hostname === 'agenticverz.com' &&
    !window.location.pathname.includes('demo');

  if (isProduction) {
    // In production: use namespaced, less obvious name
    // Access via: window.__aosDebug?.getEvents()
    (window as unknown as { __aosDebug?: ConsoleLogger }).__aosDebug = logger;
  } else {
    // In dev/demo: full access
    (window as unknown as { __guardLogger: ConsoleLogger }).__guardLogger = logger;
    // Also expose help text
    console.info('%c[Guard Console] Debug logger available:', 'color: #3b82f6; font-weight: bold');
    console.info('  window.__guardLogger.getEvents()   - View captured events');
    console.info('  window.__guardLogger.exportEvents() - Export as JSON');
    console.info('  window.__guardLogger.clearEvents()  - Clear event buffer');
  }
}

export default logger;
