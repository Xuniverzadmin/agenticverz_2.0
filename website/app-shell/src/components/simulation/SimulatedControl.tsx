/**
 * Simulated Control Component - Phase-2A.2
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Role: Render a control that responds to clicks in simulation mode
 * Reference: PIN-368, Phase-2A.2 Simulation Specification
 *
 * SIMULATION RULES:
 * - Shows immediate visual feedback
 * - Displays inline message explaining what WOULD happen
 * - NEVER calls backend
 * - NEVER mutates state
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
  Play,
  Info,
} from 'lucide-react';
import {
  useSimulation,
  getSimulationMessage,
  requiresConfirmation,
  isAlwaysBlocked,
  isRealModeControl,
} from '@/contexts/SimulationContext';
import { ConfirmationModal } from './ConfirmationModal';
import type { Control } from '@/contracts/ui_projection_types';

// ============================================================================
// Control Icons
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
  // Action controls (simulation targets)
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

// Modal configurations per control type (careful, domain-appropriate wording)
const MODAL_CONFIG: Record<string, { title: string; message: string; confirmText: string }> = {
  // Activity Domain
  STOP: {
    title: 'Stop execution?',
    message: 'This will simulate stopping the execution. The run will continue unaffected.',
    confirmText: 'Stop (Preview)',
  },
  // Incidents Domain (careful tone - emotionally charged)
  MITIGATE: {
    title: 'Mitigate incident?',
    message: 'This will record a mitigation request. No actual mitigation action will be executed.',
    confirmText: 'Record Mitigation (Preview)',
  },
  CLOSE: {
    title: 'Close incident?',
    message: 'This will acknowledge closure intent. The incident remains visible for audit purposes.',
    confirmText: 'Acknowledge Closure (Preview)',
  },
  ESCALATE: {
    title: 'Escalate incident?',
    message: 'This will record an escalation request. No ownership transfer will occur.',
    confirmText: 'Record Escalation (Preview)',
  },
  // Logs Domain
  DELETE: {
    title: 'Delete logs?',
    message: 'Log deletion is blocked. Logs are immutable and cannot be removed.',
    confirmText: 'Understood',
  },
};

// ============================================================================
// Props
// ============================================================================

interface SimulatedControlProps {
  control: Control;
  panelId: string;
  entityId?: string; // Phase-2.5: Run ID for real actions like RETRY
  showType?: boolean;
  disabled?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function SimulatedControl({
  control,
  panelId,
  entityId,
  showType = false,
  disabled = false,
}: SimulatedControlProps) {
  const { executeSimulatedAction, executeRealAction, isRealMode, isSimulationEnabled } = useSimulation();

  const [showConfirm, setShowConfirm] = useState(false);
  const [inlineMessage, setInlineMessage] = useState<string | null>(null);
  const [isActivated, setIsActivated] = useState(false);

  const Icon = CONTROL_ICONS[control.type] || Info;
  const colors = CATEGORY_COLORS[control.category] || CATEGORY_COLORS.unknown;
  const messages = getSimulationMessage(control.type);

  // Is this control interactive in simulation mode?
  const isActionControl = control.category === 'action';
  const isInteractive = isSimulationEnabled && isActionControl && !disabled;
  const isBlocked = isAlwaysBlocked(control.type);
  const needsConfirmation = requiresConfirmation(control.type);

  const handleClick = useCallback(async () => {
    if (!isInteractive) return;

    // If confirmation is required, show modal first
    if (needsConfirmation && !isBlocked) {
      setShowConfirm(true);
      return;
    }

    // Phase-2.5: Check if this control has graduated to real execution
    if (isRealMode(control.type) && entityId) {
      const result = await executeRealAction(control.type, panelId, entityId);
      if (result.success) {
        setInlineMessage(`New run created: ${result.newRunId}`);
      } else {
        setInlineMessage(`Failed: ${result.error}`);
      }
      setIsActivated(true);

      setTimeout(() => {
        setInlineMessage(null);
        setIsActivated(false);
      }, 5000);
      return;
    }

    // Execute simulated action
    const success = await executeSimulatedAction(control.type, panelId);

    // Show inline message
    setInlineMessage(messages.inline);
    setIsActivated(true);

    // Clear inline message after 5 seconds
    setTimeout(() => {
      setInlineMessage(null);
      setIsActivated(false);
    }, 5000);
  }, [isInteractive, needsConfirmation, isBlocked, isRealMode, entityId, executeRealAction, executeSimulatedAction, control.type, panelId, messages.inline]);

  const handleConfirm = useCallback(async () => {
    setShowConfirm(false);

    // Phase-2.5: Check if this control has graduated to real execution
    if (isRealMode(control.type) && entityId) {
      const result = await executeRealAction(control.type, panelId, entityId);
      if (result.success) {
        setInlineMessage(`New run created: ${result.newRunId}`);
      } else {
        setInlineMessage(`Failed: ${result.error}`);
      }
      setIsActivated(true);

      setTimeout(() => {
        setInlineMessage(null);
        setIsActivated(false);
      }, 5000);
      return;
    }

    const success = await executeSimulatedAction(control.type, panelId);

    setInlineMessage(messages.inline);
    setIsActivated(true);

    setTimeout(() => {
      setInlineMessage(null);
      setIsActivated(false);
    }, 5000);
  }, [isRealMode, entityId, executeRealAction, executeSimulatedAction, control.type, panelId, messages.inline]);

  return (
    <>
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
          isInteractive && [
            colors.hover,
            'cursor-pointer',
          ],
          // Activated state
          isActivated && colors.active,
          // Disabled styles
          !control.enabled && !isSimulationEnabled && 'opacity-50',
          // Blocked action indicator
          isBlocked && 'border-red-700/50',
        )}
      >
        {/* Main control row */}
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Icon size={16} className={cn(
              isBlocked && 'text-red-400',
              isActivated && 'animate-pulse',
            )} />
            <span className="text-sm font-mono">{control.type}</span>
            {showType && (
              <span className="text-xs opacity-70">({control.category})</span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {/* Execution mode badge */}
            {isInteractive && (
              <span className={cn(
                'text-xs px-2 py-0.5 rounded border',
                isBlocked
                  ? 'bg-red-900/50 text-red-400 border-red-700/50'
                  : isRealMode(control.type) && entityId
                    ? 'bg-green-900/50 text-green-400 border-green-700/50'
                    : 'bg-amber-900/50 text-amber-400 border-amber-700/50'
              )}>
                {isBlocked ? 'BLOCKED' : isRealMode(control.type) && entityId ? 'REAL' : 'SIMULATED'}
              </span>
            )}
            {showType && (
              <span className="text-xs opacity-70">Order: {control.order}</span>
            )}
            {control.enabled ? (
              <CheckCircle size={14} className="text-green-400" />
            ) : (
              <XCircle size={14} className="text-gray-500" />
            )}
          </div>
        </div>

        {/* Inline message (shown after click) */}
        {inlineMessage && (
          <div className={cn(
            'px-4 py-2 text-xs border-t',
            isBlocked
              ? 'bg-red-900/20 border-red-700/30 text-red-300'
              : 'bg-amber-900/20 border-amber-700/30 text-amber-300',
          )}>
            <span className="opacity-80">{inlineMessage}</span>
          </div>
        )}

        {/* Disabled reason (always shown for blocked controls) */}
        {control.disabled_reason && !inlineMessage && (
          <div className="px-4 py-2 text-xs border-t border-gray-700/50 bg-gray-800/50 text-gray-400">
            {control.disabled_reason}
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      <ConfirmationModal
        open={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleConfirm}
        title={MODAL_CONFIG[control.type]?.title || `${control.type}?`}
        subtitle="Simulation only"
        message={MODAL_CONFIG[control.type]?.message || `This will simulate the ${control.type.toLowerCase()} action. No actual changes will be made.`}
        confirmText={MODAL_CONFIG[control.type]?.confirmText || `${control.type} (Preview)`}
        cancelText="Cancel"
        variant={isBlocked ? 'destructive' : 'default'}
      />
    </>
  );
}
