/**
 * Simulation Context - Phase-2A.2 Simulation Mode
 *
 * Layer: L1 — Product Experience (UI)
 * Product: system-wide
 * Temporal:
 *   Trigger: user (control click)
 *   Execution: sync (immediate UI feedback)
 * Role: Handle simulated control actions without backend mutation
 * Reference: PIN-368, Phase-2A.2 Simulation Specification
 *
 * SIMULATION RULES (Non-Negotiable):
 * - NO backend API calls
 * - NO state mutation
 * - NO DB writes
 * - Immediate UI feedback required
 * - Self-explanatory action required
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { toast, toastInfo, toastWarning, toastSuccess, toastError } from '@/components/common/Toast';
import { retryRun } from '@/api/worker';

// ============================================================================
// Types
// ============================================================================

export type SimulationMode = 'BLOCKED' | 'SIMULATED' | 'LIVE';

export interface SimulatedAction {
  controlType: string;
  panelId: string;
  timestamp: Date;
  result: 'simulated' | 'blocked';
  message: string;
}

interface SimulationContextValue {
  mode: SimulationMode;
  setMode: (mode: SimulationMode) => void;
  actionLog: SimulatedAction[];
  executeSimulatedAction: (
    controlType: string,
    panelId: string,
    options?: {
      requiresConfirmation?: boolean;
      actionLabel?: string;
    }
  ) => Promise<boolean>;
  executeRealAction: (
    controlType: string,
    panelId: string,
    runId: string
  ) => Promise<{ success: boolean; newRunId?: string; error?: string }>;
  isRealMode: (controlType: string) => boolean;
  clearLog: () => void;
  isSimulationEnabled: boolean;
}

// ============================================================================
// Simulation Messages (Authoritative)
// ============================================================================

const SIMULATION_MESSAGES: Record<string, { toast: string; inline: string }> = {
  // Activity Domain
  STOP: {
    toast: 'Stop requested (simulation only)',
    inline: 'Execution continues. No stop signal sent.',
  },
  RETRY: {
    toast: 'Retry requested (simulation only)',
    inline: 'No execution was triggered. This is a preview.',
  },
  REPLAY_EXPORT: {
    toast: 'Export requested (simulation only)',
    inline: 'No file was created. This is a preview.',
  },
  // Incidents Domain (careful tone, not permissive)
  MITIGATE: {
    toast: 'Mitigation request recorded (simulation only)',
    inline: 'No mitigation action was executed. Incident state unchanged.',
  },
  CLOSE: {
    toast: 'Incident closure acknowledged (simulation only)',
    inline: 'Incident remains visible for audit purposes.',
  },
  ESCALATE: {
    toast: 'Escalation recorded (simulation only)',
    inline: 'No ownership transfer occurred. Escalation path shown for reference.',
  },
  // Policies Domain
  TOGGLE: {
    toast: 'Toggle requested (simulation only)',
    inline: 'Policy state unchanged. This is a preview.',
  },
  EDIT: {
    toast: 'Edit requested (simulation only)',
    inline: 'No changes were saved. This is a preview.',
  },
  // Logs Domain
  ARCHIVE: {
    toast: 'Archive requested (simulation only)',
    inline: 'No logs were archived. This is a preview.',
  },
  DELETE: {
    toast: 'Deletion blocked',
    inline: 'Logs are immutable and cannot be deleted.',
  },
  // Default
  DEFAULT: {
    toast: 'Action requested (simulation only)',
    inline: 'No actual change occurred. This is a preview.',
  },
};

// Actions that require confirmation modal
// Activity: STOP
// Incidents: MITIGATE, CLOSE, ESCALATE (all require careful acknowledgment)
// Logs: DELETE
const CONFIRMATION_REQUIRED: string[] = ['STOP', 'DELETE', 'CLOSE', 'MITIGATE', 'ESCALATE'];

// Actions that are always blocked (even in simulation)
const ALWAYS_BLOCKED: string[] = ['DELETE'];

// Phase-2.5: Controls that have graduated to REAL execution
// Only RETRY for now - others remain SIMULATED
const REAL_MODE_CONTROLS: string[] = ['RETRY'];

// ============================================================================
// Context
// ============================================================================

const SimulationContext = createContext<SimulationContextValue | undefined>(undefined);

// ============================================================================
// Provider
// ============================================================================

interface SimulationProviderProps {
  children: ReactNode;
  initialMode?: SimulationMode;
}

export function SimulationProvider({
  children,
  initialMode = 'SIMULATED',
}: SimulationProviderProps) {
  const [mode, setMode] = useState<SimulationMode>(initialMode);
  const [actionLog, setActionLog] = useState<SimulatedAction[]>([]);

  const executeSimulatedAction = useCallback(
    async (
      controlType: string,
      panelId: string,
      options?: { requiresConfirmation?: boolean; actionLabel?: string }
    ): Promise<boolean> => {
      // Get messages for this control type
      const messages = SIMULATION_MESSAGES[controlType] || SIMULATION_MESSAGES.DEFAULT;

      // Check if action is always blocked
      if (ALWAYS_BLOCKED.includes(controlType)) {
        toastWarning(messages.toast);

        const action: SimulatedAction = {
          controlType,
          panelId,
          timestamp: new Date(),
          result: 'blocked',
          message: messages.inline,
        };
        setActionLog((prev) => [...prev, action]);

        // Log to console for debugging
        console.log(`[SIMULATION] BLOCKED: ${controlType} on ${panelId}`);
        console.log(`[SIMULATION] Reason: ${messages.inline}`);

        return false;
      }

      // In BLOCKED mode, show blocked message
      if (mode === 'BLOCKED') {
        toastWarning(`${controlType} is not available on this surface`);
        return false;
      }

      // In SIMULATED mode, show simulation feedback
      if (mode === 'SIMULATED') {
        toastInfo(messages.toast);

        const action: SimulatedAction = {
          controlType,
          panelId,
          timestamp: new Date(),
          result: 'simulated',
          message: messages.inline,
        };
        setActionLog((prev) => [...prev, action]);

        // Log to console for debugging
        console.log(`[SIMULATION] SIMULATED: ${controlType} on ${panelId}`);
        console.log(`[SIMULATION] Message: ${messages.inline}`);

        return true;
      }

      // LIVE mode would call backend (not implemented yet)
      console.warn(`[SIMULATION] LIVE mode not implemented for ${controlType}`);
      return false;
    },
    [mode]
  );

  const clearLog = useCallback(() => {
    setActionLog([]);
  }, []);

  // Phase-2.5: Check if control should use real execution
  const isRealMode = useCallback((controlType: string): boolean => {
    return REAL_MODE_CONTROLS.includes(controlType);
  }, []);

  // Phase-2.5: Execute real action (RETRY only for now)
  const executeRealAction = useCallback(
    async (
      controlType: string,
      panelId: string,
      runId: string
    ): Promise<{ success: boolean; newRunId?: string; error?: string }> => {
      console.log(`[REAL] Executing: ${controlType} on ${panelId} (run: ${runId})`);

      try {
        if (controlType === 'RETRY') {
          const result = await retryRun(runId);
          toastSuccess('Retry started');

          // Log the real action
          const action: SimulatedAction = {
            controlType,
            panelId,
            timestamp: new Date(),
            result: 'simulated', // Still log it, but it was real
            message: `New run created: ${result.id}`,
          };
          setActionLog((prev) => [...prev, action]);

          console.log(`[REAL] SUCCESS: New run ${result.id} created from ${runId}`);
          return { success: true, newRunId: result.id };
        }

        // Unknown real action
        console.warn(`[REAL] Unknown control type: ${controlType}`);
        return { success: false, error: 'Unknown action' };

      } catch (err) {
        const error = err instanceof Error ? err.message : 'Unknown error';
        console.error(`[REAL] FAILED: ${controlType} - ${error}`);
        toastError(`Retry failed: ${error}`);
        return { success: false, error };
      }
    },
    []
  );

  const value: SimulationContextValue = {
    mode,
    setMode,
    actionLog,
    executeSimulatedAction,
    executeRealAction,
    isRealMode,
    clearLog,
    isSimulationEnabled: mode === 'SIMULATED',
  };

  return (
    <SimulationContext.Provider value={value}>{children}</SimulationContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

export function useSimulation() {
  const context = useContext(SimulationContext);
  if (!context) {
    throw new Error('useSimulation must be used within a SimulationProvider');
  }
  return context;
}

// ============================================================================
// Utilities
// ============================================================================

export function getSimulationMessage(controlType: string): { toast: string; inline: string } {
  return SIMULATION_MESSAGES[controlType] || SIMULATION_MESSAGES.DEFAULT;
}

export function requiresConfirmation(controlType: string): boolean {
  return CONFIRMATION_REQUIRED.includes(controlType);
}

export function isRealModeControl(controlType: string): boolean {
  return REAL_MODE_CONTROLS.includes(controlType);
}

export function isAlwaysBlocked(controlType: string): boolean {
  return ALWAYS_BLOCKED.includes(controlType);
}
