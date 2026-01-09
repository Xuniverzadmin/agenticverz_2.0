/**
 * Simulation Action Log Panel - Phase-2A.2
 *
 * Layer: L1 — Product Experience (UI)
 * Role: Display log of simulated actions for debugging/verification
 * Reference: PIN-368, Phase-2A.2 Simulation Specification
 *
 * This panel shows all simulated actions taken during the session.
 * Useful for:
 * - Verifying simulation is working
 * - UX walkthrough testing
 * - Debugging action handling
 */

import { useState } from 'react';
import { cn } from '@/lib/utils';
import { useSimulation, SimulatedAction } from '@/contexts/SimulationContext';
import {
  Beaker,
  ChevronDown,
  ChevronUp,
  Trash2,
  Clock,
  CheckCircle,
  XCircle,
  Copy,
  Check,
} from 'lucide-react';
import { Button } from '@/components/common/Button';

export function SimulationLog() {
  const { actionLog, clearLog, mode } = useSimulation();
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const copyLog = async () => {
    const logText = actionLog.map(action => {
      const time = action.timestamp.toLocaleTimeString();
      return `${action.controlType} [${action.result}] - ${time}\nPanel: ${action.panelId}\n${action.message}`;
    }).join('\n\n---\n\n');

    const header = `Simulation Log - ${new Date().toLocaleString()}\nTotal actions: ${actionLog.length}\n\n`;

    try {
      await navigator.clipboard.writeText(header + logText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  if (mode !== 'SIMULATED') {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 z-40 w-80">
      {/* Header - Always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          'w-full flex items-center justify-between px-4 py-2 rounded-t-lg',
          'bg-amber-900/80 text-amber-200 border border-amber-700',
          'hover:bg-amber-900/90 transition-colors',
          !expanded && 'rounded-b-lg'
        )}
      >
        <div className="flex items-center gap-2">
          <Beaker size={16} />
          <span className="font-medium text-sm">Simulation Log</span>
          {actionLog.length > 0 && (
            <span className="px-1.5 py-0.5 text-xs rounded bg-amber-700">
              {actionLog.length}
            </span>
          )}
        </div>
        {expanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
      </button>

      {/* Log Panel - Expandable */}
      {expanded && (
        <div className="bg-gray-900 border border-t-0 border-amber-700 rounded-b-lg max-h-64 overflow-hidden flex flex-col">
          {/* Actions */}
          {actionLog.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              No simulated actions yet.
              <br />
              <span className="text-xs">Click an action control to test.</span>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto divide-y divide-gray-800">
              {actionLog.map((action, idx) => (
                <ActionLogItem key={idx} action={action} />
              ))}
            </div>
          )}

          {/* Footer */}
          {actionLog.length > 0 && (
            <div className="p-2 border-t border-gray-800 flex justify-between">
              <Button
                variant="ghost"
                size="sm"
                onClick={copyLog}
                className={cn(
                  "text-xs",
                  copied
                    ? "text-green-400 hover:text-green-300"
                    : "text-gray-400 hover:text-gray-200"
                )}
              >
                {copied ? (
                  <>
                    <Check size={12} className="mr-1" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy size={12} className="mr-1" />
                    Copy
                  </>
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearLog}
                className="text-xs text-gray-400 hover:text-gray-200"
              >
                <Trash2 size={12} className="mr-1" />
                Clear
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ActionLogItem({ action }: { action: SimulatedAction }) {
  const isBlocked = action.result === 'blocked';

  return (
    <div className="px-3 py-2 hover:bg-gray-800/50">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isBlocked ? (
            <XCircle size={12} className="text-red-400" />
          ) : (
            <CheckCircle size={12} className="text-green-400" />
          )}
          <span className="text-sm font-mono text-gray-200">
            {action.controlType}
          </span>
        </div>
        <span className={cn(
          'text-xs px-1.5 py-0.5 rounded',
          isBlocked
            ? 'bg-red-900/50 text-red-400'
            : 'bg-green-900/50 text-green-400'
        )}>
          {action.result}
        </span>
      </div>
      <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
        <Clock size={10} />
        <span>{action.timestamp.toLocaleTimeString()}</span>
        <span className="text-gray-600">•</span>
        <span className="font-mono truncate">{action.panelId}</span>
      </div>
      <p className="mt-1 text-xs text-gray-400 truncate">{action.message}</p>
    </div>
  );
}
