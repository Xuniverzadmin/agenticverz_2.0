// LiveLogStream Component - Right Top Pane
// Shows real-time agent output logs with color-coded levels

import { useEffect, useRef } from 'react';
import { Terminal, AlertTriangle, Info, Bug, AlertCircle } from 'lucide-react';
import type { LogEvent } from '@/types/worker';
import clsx from 'clsx';

interface LiveLogStreamProps {
  logs: LogEvent[];
  autoScroll?: boolean;
}

const LogIcon = ({ level }: { level: LogEvent['level'] }) => {
  switch (level) {
    case 'error':
      return <AlertCircle className="w-3.5 h-3.5 text-red-500" />;
    case 'warning':
      return <AlertTriangle className="w-3.5 h-3.5 text-yellow-500" />;
    case 'debug':
      return <Bug className="w-3.5 h-3.5 text-gray-400" />;
    case 'info':
    default:
      return <Info className="w-3.5 h-3.5 text-blue-500" />;
  }
};

const LEVEL_COLORS: Record<LogEvent['level'], string> = {
  debug: 'text-gray-400',
  info: 'text-blue-400',
  warning: 'text-yellow-400',
  error: 'text-red-400',
};

const AGENT_COLORS: Record<string, string> = {
  M9: 'text-orange-400',
  M10: 'text-green-400',
  M17: 'text-purple-400',
  M18: 'text-pink-400',
  M19: 'text-cyan-400',
  M20: 'text-indigo-400',
  preflight_agent_v1: 'text-gray-400',
  research_agent_v1: 'text-blue-400',
  strategy_agent_v1: 'text-purple-400',
  copy_agent_v1: 'text-green-400',
  ux_agent_v1: 'text-pink-400',
  consistency_agent_v1: 'text-yellow-400',
  recovery_agent_v1: 'text-orange-400',
  bundle_agent_v1: 'text-cyan-400',
};

export function LiveLogStream({ logs, autoScroll = true }: LiveLogStreamProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  return (
    <div className="h-full flex flex-col bg-gray-900 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-2 bg-gray-800 flex items-center gap-2 border-b border-gray-700">
        <Terminal className="w-4 h-4 text-green-400" />
        <h3 className="text-sm font-semibold text-white">Live Log Stream</h3>
        <span className="text-xs text-gray-400 ml-auto">
          {logs.length} events
        </span>
      </div>

      {/* Log container */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-3 font-mono text-xs"
      >
        {logs.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            Waiting for logs...
          </div>
        ) : (
          <div className="space-y-1">
            {logs.map((log, index) => (
              <div
                key={index}
                className={clsx(
                  'flex items-start gap-2 py-1 px-2 rounded hover:bg-gray-800/50',
                  log.level === 'error' && 'bg-red-900/20',
                  log.level === 'warning' && 'bg-yellow-900/20'
                )}
              >
                <LogIcon level={log.level} />
                <span className={clsx('flex-shrink-0', LEVEL_COLORS[log.level])}>
                  [{log.level.toUpperCase().padEnd(5)}]
                </span>
                <span
                  className={clsx(
                    'flex-shrink-0',
                    AGENT_COLORS[log.agent] || 'text-gray-400'
                  )}
                >
                  [{log.agent}]
                </span>
                <span className="text-gray-200 break-words">{log.message}</span>
              </div>
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Status bar */}
      <div className="px-4 py-1.5 bg-gray-800 border-t border-gray-700 flex items-center gap-4 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Streaming
        </span>
        <span>
          Errors: {logs.filter((l) => l.level === 'error').length}
        </span>
        <span>
          Warnings: {logs.filter((l) => l.level === 'warning').length}
        </span>
      </div>
    </div>
  );
}
