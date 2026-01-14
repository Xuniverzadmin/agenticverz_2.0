/**
 * Real Control Component
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: Render action controls that execute real backend operations
 * Reference: AURORA L2.1 Projection Pipeline
 *
 * RULES (NON-NEGOTIABLE):
 * - If control.enabled === false → Render disabled, no click handler
 * - If control.enabled === true → Click calls real backend
 * - No simulation. No preview. No fake acknowledgement.
 * - If it's clickable, it's real. If it's not real, it's not clickable.
 *
 * PROJECTION-DRIVEN:
 * - Control existence comes from AURORA projection
 * - Control enabled state comes from binding_status
 * - Frontend does NOT infer behavior
 */

import { useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import {
  CheckCircle,
  XCircle,
  StopCircle,
  RefreshCw,
  FileOutput,
  Shield,
  XOctagon,
  AlertTriangle,
  ToggleLeft,
  Edit2,
  Archive,
  Trash2,
  Info,
  Loader2,
} from 'lucide-react';
import { toastSuccess, toastError } from '@/components/common/Toast';
import { retryRun } from '@/api/worker';
import type { Control } from '@/contracts/ui_projection_types';

// ============================================================================
// Control Icons (from projection control types)
// ============================================================================

const CONTROL_ICONS: Record<string, React.ElementType> = {
  // Standard controls
  FILTER: Info,
  SORT: Info,
  SELECT_SINGLE: Info,
  SELECT_MULTI: Info,
  NAVIGATE: Info,
  DOWNLOAD: FileOutput,
  ACKNOWLEDGE: CheckCircle,
  RESOLVE: CheckCircle,
  // Action controls
  STOP: StopCircle,
  RETRY: RefreshCw,
  REPLAY_EXPORT: FileOutput,
  MITIGATE: Shield,
  CLOSE: XOctagon,
  ESCALATE: AlertTriangle,
  TOGGLE: ToggleLeft,
  EDIT: Edit2,
  ARCHIVE: Archive,
  DELETE: Trash2,
};

// Control category colors
const CATEGORY_COLORS: Record<string, { base: string; hover: string; active: string }> = {
  data_control: {
    base: 'bg-blue-900/30 text-blue-400 border-blue-700',
    hover: 'hover:bg-blue-900/50 hover:border-blue-600',
    active: 'bg-blue-800/50 border-blue-500',
  },
  selection: {
    base: 'bg-purple-900/30 text-purple-400 border-purple-700',
    hover: 'hover:bg-purple-900/50 hover:border-purple-600',
    active: 'bg-purple-800/50 border-purple-500',
  },
  navigation: {
    base: 'bg-cyan-900/30 text-cyan-400 border-cyan-700',
    hover: 'hover:bg-cyan-900/50 hover:border-cyan-600',
    active: 'bg-cyan-800/50 border-cyan-500',
  },
  action: {
    base: 'bg-green-900/30 text-green-400 border-green-700',
    hover: 'hover:bg-green-900/50 hover:border-green-600',
    active: 'bg-green-800/50 border-green-500',
  },
  unknown: {
    base: 'bg-gray-700 text-gray-400 border-gray-600',
    hover: 'hover:bg-gray-600 hover:border-gray-500',
    active: 'bg-gray-600 border-gray-500',
  },
};

// ============================================================================
// Backend Action Handlers
// ============================================================================

/**
 * Execute a real backend action.
 *
 * RULE: If a control is enabled in the projection, it MUST have a real backend handler.
 * If it does not, that is an AURORA or SDSR error—not a frontend concern.
 */
async function executeRealAction(
  controlType: string,
  entityId: string
): Promise<{ success: boolean; message: string; data?: unknown }> {
  switch (controlType) {
    case 'RETRY':
      try {
        const result = await retryRun(entityId);
        return {
          success: true,
          message: `New run created: ${result.id}`,
          data: result,
        };
      } catch (err) {
        const error = err instanceof Error ? err.message : 'Unknown error';
        return { success: false, message: `Retry failed: ${error}` };
      }

    // Add more real action handlers here as they graduate from AURORA
    // Each case MUST call a real backend endpoint

    default:
      // If we get here, the control is enabled but has no handler.
      // This is an AURORA configuration error, not a frontend problem.
      console.error(
        `[RealControl] No backend handler for control type: ${controlType}. ` +
        `This control should not be enabled in the projection.`
      );
      return {
        success: false,
        message: `Action ${controlType} has no backend implementation`,
      };
  }
}

// ============================================================================
// Props
// ============================================================================

interface RealControlProps {
  control: Control;
  panelId: string;
  entityId?: string; // Run ID for actions like RETRY
  showType?: boolean;
  disabled?: boolean; // Override from parent (binding_status)
}

// ============================================================================
// Component
// ============================================================================

export function RealControl({
  control,
  panelId,
  entityId,
  showType = false,
  disabled = false,
}: RealControlProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  const Icon = CONTROL_ICONS[control.type] || Info;
  const colors = CATEGORY_COLORS[control.category] || CATEGORY_COLORS.unknown;

  // Control is interactive only if:
  // 1. It's an action control
  // 2. It's enabled in the projection
  // 3. Not overridden by parent (binding_status !== BOUND)
  const isActionControl = control.category === 'action';
  const isEnabled = control.enabled && !disabled;
  const isInteractive = isActionControl && isEnabled;

  const handleClick = useCallback(async () => {
    if (!isInteractive || isLoading) return;

    // entityId required for real actions
    if (!entityId) {
      console.warn(`[RealControl] Action ${control.type} requires entityId`);
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const actionResult = await executeRealAction(control.type, entityId);
      setResult(actionResult);

      if (actionResult.success) {
        toastSuccess(actionResult.message);
      } else {
        toastError(actionResult.message);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Action failed';
      setResult({ success: false, message });
      toastError(message);
    } finally {
      setIsLoading(false);

      // Clear result message after 5 seconds
      setTimeout(() => setResult(null), 5000);
    }
  }, [isInteractive, isLoading, entityId, control.type]);

  return (
    <div
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      onClick={handleClick}
      onKeyDown={(e) => {
        if (isInteractive && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          handleClick();
        }
      }}
      className={cn(
        'flex flex-col rounded-lg border transition-all duration-200',
        colors.base,
        // Interactive styles
        isInteractive && !isLoading && [colors.hover, 'cursor-pointer'],
        // Loading state
        isLoading && 'opacity-70 cursor-wait',
        // Disabled styles
        !isEnabled && 'opacity-50 cursor-not-allowed',
      )}
    >
      {/* Main control row */}
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          {isLoading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Icon size={16} />
          )}
          <span className="text-sm font-mono">{control.type}</span>
          {showType && (
            <span className="text-xs opacity-70">({control.category})</span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {showType && (
            <span className="text-xs opacity-70">Order: {control.order}</span>
          )}
          {isEnabled ? (
            <CheckCircle size={14} className="text-green-400" />
          ) : (
            <XCircle size={14} className="text-gray-500" />
          )}
        </div>
      </div>

      {/* Result message (shown after action) */}
      {result && (
        <div
          className={cn(
            'px-4 py-2 text-xs border-t',
            result.success
              ? 'bg-green-900/20 border-green-700/30 text-green-300'
              : 'bg-red-900/20 border-red-700/30 text-red-300'
          )}
        >
          <span className="opacity-80">{result.message}</span>
        </div>
      )}

      {/* Disabled reason (if control has one) */}
      {control.disabled_reason && !result && (
        <div className="px-4 py-2 text-xs border-t border-gray-700/50 bg-gray-800/50 text-gray-400">
          {control.disabled_reason}
        </div>
      )}
    </div>
  );
}
