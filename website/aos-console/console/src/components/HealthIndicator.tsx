/**
 * Health Status Indicator Component
 *
 * Displays system health status in the UI with:
 * - Color-coded status badge
 * - Expandable details panel
 * - Auto-refresh
 */

import React, { useState, useEffect } from 'react';
import { healthMonitor, SystemHealth, EndpointHealth } from '@/lib/healthCheck';

interface HealthIndicatorProps {
  showDetails?: boolean;
  position?: 'top-right' | 'bottom-right' | 'inline';
}

export function HealthIndicator({ showDetails = false, position = 'inline' }: HealthIndicatorProps) {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    // Get initial health
    setHealth(healthMonitor.getHealth());

    // Subscribe to updates
    const unsubscribe = healthMonitor.subscribe(setHealth);

    // Start periodic checks
    healthMonitor.startPeriodicCheck(30000);

    return () => {
      unsubscribe();
    };
  }, []);

  if (!health) return null;

  const statusConfig = {
    healthy: {
      color: 'bg-green-500',
      text: 'text-green-400',
      bg: 'bg-green-500/20',
      border: 'border-green-500/50',
      label: 'All Systems Operational',
      icon: '✓',
    },
    degraded: {
      color: 'bg-amber-500',
      text: 'text-amber-400',
      bg: 'bg-amber-500/20',
      border: 'border-amber-500/50',
      label: 'Degraded Performance',
      icon: '⚠',
    },
    down: {
      color: 'bg-red-500',
      text: 'text-red-400',
      bg: 'bg-red-500/20',
      border: 'border-red-500/50',
      label: 'Service Disruption',
      icon: '✕',
    },
  };

  const config = statusConfig[health.overall];

  const positionClasses = {
    'top-right': 'fixed top-4 right-4 z-50',
    'bottom-right': 'fixed bottom-4 right-4 z-50',
    'inline': '',
  };

  return (
    <div className={positionClasses[position]}>
      {/* Status Badge */}
      <button
        onClick={() => showDetails && setExpanded(!expanded)}
        className={`
          flex items-center gap-2 px-3 py-1.5 rounded-lg border
          ${config.bg} ${config.border} ${config.text}
          ${showDetails ? 'cursor-pointer hover:opacity-80' : 'cursor-default'}
          transition-all
        `}
      >
        <span className={`w-2 h-2 rounded-full ${config.color} animate-pulse`} />
        <span className="text-sm font-medium">{config.label}</span>
        {showDetails && (
          <span className="text-xs opacity-60">{expanded ? '▲' : '▼'}</span>
        )}
      </button>

      {/* Expanded Details Panel */}
      {showDetails && expanded && (
        <div className={`
          mt-2 p-4 rounded-lg border bg-slate-800 border-slate-700
          ${position !== 'inline' ? 'w-80 shadow-xl' : ''}
        `}>
          <h4 className="text-sm font-semibold text-slate-200 mb-3">Endpoint Status</h4>

          <div className="space-y-2">
            {Object.values(health.endpoints).map((ep: EndpointHealth) => (
              <EndpointRow key={ep.endpoint} endpoint={ep} />
            ))}
          </div>

          {/* Circuit Breaker Status */}
          {Object.keys(health.circuits).length > 0 && (
            <>
              <h4 className="text-sm font-semibold text-slate-200 mt-4 mb-2">Circuit Breakers</h4>
              <div className="space-y-1">
                {Object.entries(health.circuits).map(([path, circuit]) => (
                  <div
                    key={path}
                    className="flex items-center justify-between text-xs"
                  >
                    <span className="text-slate-400 truncate">{path}</span>
                    <span className={`
                      px-1.5 py-0.5 rounded
                      ${circuit.state === 'closed' ? 'bg-green-500/20 text-green-400' : ''}
                      ${circuit.state === 'open' ? 'bg-red-500/20 text-red-400' : ''}
                      ${circuit.state === 'half-open' ? 'bg-amber-500/20 text-amber-400' : ''}
                    `}>
                      {circuit.state}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}

          <div className="mt-3 pt-3 border-t border-slate-700 flex justify-between items-center">
            <span className="text-xs text-slate-500">
              Last check: {health.lastFullCheck.toLocaleTimeString()}
            </span>
            <button
              onClick={() => healthMonitor.checkAll()}
              className="text-xs text-blue-400 hover:text-blue-300"
            >
              Refresh
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function EndpointRow({ endpoint }: { endpoint: EndpointHealth }) {
  const statusColors = {
    healthy: 'bg-green-500',
    degraded: 'bg-amber-500',
    down: 'bg-red-500',
  };

  return (
    <div className="flex items-center justify-between py-1.5 px-2 bg-slate-900/50 rounded">
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${statusColors[endpoint.status]}`} />
        <span className="text-sm text-slate-300 truncate max-w-[150px]">
          {endpoint.endpoint.replace('/guard/', '')}
        </span>
      </div>
      <div className="flex items-center gap-2 text-xs">
        <span className="text-slate-500">
          {endpoint.responseTime > 0 ? `${Math.round(endpoint.responseTime)}ms` : '—'}
        </span>
        {endpoint.status === 'down' && endpoint.lastError && (
          <span className="text-red-400">{endpoint.lastError}</span>
        )}
      </div>
    </div>
  );
}

export default HealthIndicator;
