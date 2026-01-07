/**
 * useWorkerStream Hook
 * Manages SSE connection for real-time worker execution updates
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  WorkerStreamState,
  StageState,
  LogEvent,
  ArtifactEvent,
  RoutingDecisionEvent,
  DriftEvent,
  PolicyEvent,
} from '@/types/worker';

interface UseWorkerStreamOptions {
  onComplete?: (success: boolean) => void;
  onError?: (error: string) => void;
  onStageChange?: (stage: StageState) => void;
  onArtifact?: (artifact: ArtifactEvent) => void;
}

const initialState: WorkerStreamState = {
  status: 'idle',
  stages: [],
  logs: [],
  artifacts: [],
  routingDecisions: [],
  driftEvents: [],
  policyEvents: [],
  progress: 0,
};

export function useWorkerStream(
  runId: string | null,
  options: UseWorkerStreamOptions = {}
) {
  const [state, setState] = useState<WorkerStreamState>(initialState);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const optionsRef = useRef(options);

  // Keep options ref updated
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const reset = useCallback(() => {
    setState(initialState);
    setIsConnected(false);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!runId) {
      reset();
      return;
    }

    setState((prev) => ({ ...prev, status: 'connecting', run_id: runId }));

    const eventSource = new EventSource(
      `/api/v1/workers/business-builder/stream/${runId}`
    );
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setState((prev) => ({ ...prev, status: 'connected' }));
    };

    eventSource.onerror = () => {
      // Check if we're in a completed state - SSE close after success is expected
      setState((prev) => {
        if (prev.status === 'completed') {
          return prev;
        }
        return { ...prev, status: 'error', error: 'Connection lost' };
      });
      setIsConnected(false);
    };

    // Stage updates
    eventSource.addEventListener('stage', (e) => {
      const data = JSON.parse(e.data) as StageState;
      setState((prev) => {
        const stages = [...prev.stages];
        const index = stages.findIndex((s) => s.id === data.id);
        if (index >= 0) {
          stages[index] = data;
        } else {
          stages.push(data);
        }
        return { ...prev, stages };
      });
      optionsRef.current.onStageChange?.(data);
    });

    // Log events
    eventSource.addEventListener('log', (e) => {
      const data = JSON.parse(e.data) as LogEvent;
      setState((prev) => ({
        ...prev,
        logs: [...prev.logs, data],
      }));
    });

    // Artifact events
    eventSource.addEventListener('artifact', (e) => {
      const data = JSON.parse(e.data) as ArtifactEvent;
      setState((prev) => ({
        ...prev,
        artifacts: [...prev.artifacts, data],
      }));
      optionsRef.current.onArtifact?.(data);
    });

    // Routing decision events
    eventSource.addEventListener('routing', (e) => {
      const data = JSON.parse(e.data) as RoutingDecisionEvent;
      setState((prev) => ({
        ...prev,
        routingDecisions: [...prev.routingDecisions, data],
      }));
    });

    // Drift events
    eventSource.addEventListener('drift', (e) => {
      const data = JSON.parse(e.data) as DriftEvent;
      setState((prev) => ({
        ...prev,
        driftEvents: [...prev.driftEvents, data],
      }));
    });

    // Policy events
    eventSource.addEventListener('policy', (e) => {
      const data = JSON.parse(e.data) as PolicyEvent;
      setState((prev) => ({
        ...prev,
        policyEvents: [...prev.policyEvents, data],
      }));
    });

    // Progress updates
    eventSource.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data) as { progress: number };
      setState((prev) => ({ ...prev, progress: data.progress }));
    });

    // Completion
    eventSource.addEventListener('complete', (e) => {
      const data = JSON.parse(e.data) as { success: boolean; error?: string };
      setState((prev) => ({
        ...prev,
        status: 'completed',
        error: data.error,
        progress: 100,
      }));
      eventSource.close();
      setIsConnected(false);
      optionsRef.current.onComplete?.(data.success);
    });

    // Error event from server
    eventSource.addEventListener('error_event', (e) => {
      const data = JSON.parse(e.data) as { error: string };
      setState((prev) => ({
        ...prev,
        status: 'error',
        error: data.error,
      }));
      optionsRef.current.onError?.(data.error);
    });

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [runId, reset]);

  return { state, isConnected, reset };
}
