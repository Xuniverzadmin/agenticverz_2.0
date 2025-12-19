// SSE Hook for Real-Time Worker Event Streaming
import { useEffect, useRef, useCallback, useState } from 'react';
import type {
  WorkerEvent,
  WorkerEventType,
  LogEvent,
  RoutingDecisionEvent,
  PolicyEvent,
  DriftEvent,
  ArtifactEvent,
  ArtifactContent,
  StageState,
  StageStatus,
  WorkerExecutionState,
} from '@/types/worker';
import { getStreamUrl } from '@/api/worker';

// === DEBUG LOGGING ===
const DEBUG = true;
const log = (area: string, message: string, data?: unknown) => {
  if (DEBUG) {
    const timestamp = new Date().toISOString().split('T')[1].slice(0, 12);
    console.log(`%c[${timestamp}] [SSE-HOOK] [${area}]`, 'color: #10b981; font-weight: bold', message, data ?? '');
  }
};

const STAGE_NAMES: Record<string, string> = {
  preflight: 'Preflight Validation',
  research: 'Market Research',
  strategy: 'Strategy Synthesis',
  copy: 'Copy Generation',
  ux: 'UX Layout',
  consistency: 'Consistency Check',
  recovery: 'Recovery & Normalization',
  bundle: 'Final Packaging',
};

const DEFAULT_STAGES: StageState[] = [
  { id: 'preflight', name: 'Preflight Validation', status: 'pending' },
  { id: 'research', name: 'Market Research', status: 'pending' },
  { id: 'strategy', name: 'Strategy Synthesis', status: 'pending' },
  { id: 'copy', name: 'Copy Generation', status: 'pending' },
  { id: 'ux', name: 'UX Layout', status: 'pending' },
  { id: 'consistency', name: 'Consistency Check', status: 'pending' },
  { id: 'recovery', name: 'Recovery & Normalization', status: 'pending' },
  { id: 'bundle', name: 'Final Packaging', status: 'pending' },
];

interface UseWorkerStreamOptions {
  onEvent?: (event: WorkerEvent) => void;
  onError?: (error: Event) => void;
  onComplete?: (success: boolean) => void;
}

export function useWorkerStream(
  runId: string | null,
  options: UseWorkerStreamOptions = {}
) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const optionsRef = useRef(options);
  optionsRef.current = options; // Always keep latest options
  // Final-state latch: prevents reconnection after run completes/fails
  const streamEndedForRunRef = useRef<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [state, setState] = useState<WorkerExecutionState>({
    runId: null,
    status: 'idle',
    task: '',
    stages: [...DEFAULT_STAGES],
    logs: [],
    routingDecisions: [],
    policyEvents: [],
    driftEvents: [],
    artifacts: [],
    artifactContents: {},
    recoveries: [],
    totalTokens: 0,
    totalLatency: 0,
  });

  const updateStage = useCallback((stageId: string, updates: Partial<StageState>) => {
    setState((prev) => ({
      ...prev,
      stages: prev.stages.map((s) =>
        s.id === stageId ? { ...s, ...updates } : s
      ),
    }));
  }, []);

  const handleEvent = useCallback(
    (event: WorkerEvent) => {
      const { type, data, timestamp } = event;

      log('HANDLE', `Processing event: ${type}`, { timestamp, dataKeys: Object.keys(data || {}) });

      // Call external handler
      options.onEvent?.(event);

      switch (type) {
        case 'connected':
          log('STATE', '🟢 Connected - setting isConnected=true');
          setIsConnected(true);
          setState((prev) => ({
            ...prev,
            runId: event.run_id,
          }));
          break;

        case 'run_started':
          log('STATE', '🚀 Run started - resetting state', { task: data.task });
          setState((prev) => ({
            ...prev,
            status: 'running',
            task: (data.task as string) || prev.task,
            stages: [...DEFAULT_STAGES],
            logs: [],
            routingDecisions: [],
            policyEvents: [],
            driftEvents: [],
            artifacts: [],
            artifactContents: {},
            recoveries: [],
            totalTokens: 0,
            totalLatency: 0,
          }));
          break;

        case 'stage_started':
          updateStage(data.stage_id as string, {
            status: 'running',
            startedAt: timestamp,
          });
          break;

        case 'stage_completed':
          updateStage(data.stage_id as string, {
            status: 'completed',
            completedAt: timestamp,
            duration_ms: data.duration_ms as number,
            tokens: data.tokens_used as number,
          });
          break;

        case 'stage_failed':
          updateStage(data.stage_id as string, {
            status: 'failed',
            error: data.error as string,
          });
          break;

        case 'log':
          log('STATE', `📝 Log: [${data.agent}] ${(data.message as string)?.slice(0, 50)}`);
          setState((prev) => ({
            ...prev,
            logs: [
              ...prev.logs,
              {
                stage_id: data.stage_id as string,
                agent: data.agent as string,
                message: data.message as string,
                level: (data.level as LogEvent['level']) || 'info',
              },
            ],
          }));
          break;

        case 'routing_decision':
          const routingDecision: RoutingDecisionEvent = {
            stage_id: data.stage_id as string,
            selected_agent: data.selected_agent as string,
            complexity: data.complexity as number,
            confidence: data.confidence as number,
            alternatives: data.alternatives as string[],
          };
          setState((prev) => ({
            ...prev,
            routingDecisions: [...prev.routingDecisions, routingDecision],
          }));
          updateStage(data.stage_id as string, {
            agent: data.selected_agent as string,
          });
          break;

        case 'policy_check':
        case 'policy_violation':
          const policyEvent: PolicyEvent = {
            stage_id: data.stage_id as string,
            policy: data.policy as string,
            passed: data.passed as boolean,
            reason: data.reason as string,
            pattern: data.pattern as string,
            severity: data.severity as string,
          };
          setState((prev) => ({
            ...prev,
            policyEvents: [...prev.policyEvents, policyEvent],
          }));
          if (type === 'policy_check') {
            updateStage(data.stage_id as string, {
              policy_passed: data.passed as boolean,
            });
          }
          break;

        case 'drift_detected':
          const driftEvent: DriftEvent = {
            stage_id: data.stage_id as string,
            drift_score: data.drift_score as number,
            threshold: data.threshold as number,
            aligned: data.aligned as boolean,
          };
          setState((prev) => ({
            ...prev,
            driftEvents: [...prev.driftEvents, driftEvent],
          }));
          updateStage(data.stage_id as string, {
            drift_score: data.drift_score as number,
          });
          break;

        case 'failure_detected':
          setState((prev) => ({
            ...prev,
            logs: [
              ...prev.logs,
              {
                stage_id: data.stage_id as string,
                agent: 'M9',
                message: `Failure pattern detected: ${data.pattern || 'unknown'}`,
                level: 'warning',
              },
            ],
          }));
          break;

        case 'recovery_started':
          setState((prev) => ({
            ...prev,
            logs: [
              ...prev.logs,
              {
                stage_id: data.stage_id as string,
                agent: 'M10',
                message: `Recovery started: ${data.action || 'retry'}`,
                level: 'info',
              },
            ],
          }));
          break;

        case 'recovery_completed':
          setState((prev) => ({
            ...prev,
            recoveries: [
              ...prev.recoveries,
              {
                stage: data.stage_id as string,
                recovery: data.action as string,
              },
            ],
          }));
          updateStage(data.stage_id as string, {
            status: 'recovered' as StageStatus,
          });
          break;

        case 'artifact_created':
          const artifactName = data.artifact_name as string;
          const artifactType = data.artifact_type as string;
          const artifactKey = `${artifactName}.${artifactType}`;
          const artifact: ArtifactEvent = {
            stage_id: data.stage_id as string,
            artifact_name: artifactName,
            artifact_type: artifactType,
            content: data.content as string | undefined,
          };
          setState((prev) => {
            const newState = {
              ...prev,
              artifacts: [...prev.artifacts, artifact],
            };
            // If content is provided, store it
            if (data.content) {
              newState.artifactContents = {
                ...prev.artifactContents,
                [artifactKey]: {
                  name: artifactName,
                  type: artifactType,
                  content: data.content as string,
                  stage_id: data.stage_id as string,
                  timestamp,
                },
              };
            }
            return newState;
          });
          break;

        case 'run_completed':
          log('STATE', '✅ Run COMPLETED', { total_tokens: data.total_tokens, artifacts: data.artifacts_count });
          // Set final-state latch to prevent reconnection
          streamEndedForRunRef.current = event.run_id || runId;
          setState((prev) => ({
            ...prev,
            status: 'completed',
            totalTokens: (data.total_tokens as number) || prev.totalTokens,
            totalLatency: (data.total_latency_ms as number) || prev.totalLatency,
            replayToken: data.replay_token as Record<string, unknown> | undefined,
          }));
          options.onComplete?.(true);
          break;

        case 'run_failed':
          log('STATE', `❌ Run FAILED: ${data.error}`);
          // Set final-state latch to prevent reconnection
          streamEndedForRunRef.current = event.run_id || runId;
          setState((prev) => ({
            ...prev,
            status: 'failed',
            error: data.error as string,
          }));
          options.onComplete?.(false);
          break;

        case 'stream_end':
          // Stream ended, will disconnect
          break;
      }
    },
    [options, updateStage]
  );

  // Connect to SSE stream when runId changes
  useEffect(() => {
    log('CONNECT', `useEffect triggered - runId: ${runId || 'null'}`);

    if (!runId) {
      log('CONNECT', '⏸️ No runId, skipping SSE connection');
      return;
    }

    // Final-state latch check: never reconnect to a run that already completed/failed
    if (streamEndedForRunRef.current === runId) {
      log('CONNECT', `⏹️ Run ${runId} already ended, skipping SSE reconnection`);
      return;
    }

    const url = getStreamUrl(runId);
    log('CONNECT', `🔌 Creating EventSource for: ${url}`);

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    log('CONNECT', `EventSource created, readyState: ${eventSource.readyState} (0=CONNECTING, 1=OPEN, 2=CLOSED)`);

    eventSource.onopen = () => {
      log('CONNECT', '✅ SSE connection OPENED');
      setIsConnected(true);
    };

    eventSource.onerror = (error) => {
      // SSE onerror fires when stream closes - this is expected after run completes
      if (streamEndedForRunRef.current === runId) {
        log('CONNECT', `ℹ️ SSE closed after run ended (expected behavior)`);
        setIsConnected(false);
        return; // Don't report error for expected close
      }
      log('CONNECT', `❌ SSE ERROR - readyState: ${eventSource.readyState}`, error);
      console.error('SSE error:', error);
      setIsConnected(false);
      options.onError?.(error);
    };

    // Handle all events
    eventSource.onmessage = (event) => {
      log('EVENT', `📨 onmessage received`, event.data?.slice(0, 100));
      try {
        const data = JSON.parse(event.data) as WorkerEvent;
        log('EVENT', `Parsed event type: ${data.type}`);
        handleEvent(data);
      } catch (e) {
        log('EVENT', `❌ Failed to parse SSE event`, e);
        console.error('Failed to parse SSE event:', e);
      }
    };

    // Handle specific event types
    const eventTypes: WorkerEventType[] = [
      'connected',
      'run_started',
      'stage_started',
      'stage_completed',
      'stage_failed',
      'log',
      'routing_decision',
      'policy_check',
      'policy_violation',
      'drift_detected',
      'failure_detected',
      'recovery_started',
      'recovery_completed',
      'artifact_created',
      'run_completed',
      'run_failed',
      'stream_end',
    ];

    log('LISTENERS', `Adding ${eventTypes.length} event type listeners`);

    eventTypes.forEach((eventType) => {
      eventSource.addEventListener(eventType, (event) => {
        log('EVENT-TYPE', `📬 [${eventType}] event received`);
        try {
          const data = JSON.parse((event as MessageEvent).data) as WorkerEvent;
          handleEvent(data);
        } catch (e) {
          log('EVENT-TYPE', `❌ Failed to parse ${eventType} event`, e);
          console.error(`Failed to parse ${eventType} event:`, e);
        }
      });
    });

    return () => {
      log('CLEANUP', `🧹 Closing SSE connection for runId: ${runId}`);
      eventSource.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]); // Only reconnect when runId changes, not on every render

  const disconnect = useCallback(() => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setIsConnected(false);
  }, []);

  const reset = useCallback(() => {
    disconnect();
    // Clear final-state latch to allow new runs
    streamEndedForRunRef.current = null;
    setState({
      runId: null,
      status: 'idle',
      task: '',
      stages: [...DEFAULT_STAGES],
      logs: [],
      routingDecisions: [],
      policyEvents: [],
      driftEvents: [],
      artifacts: [],
      artifactContents: {},
      recoveries: [],
      totalTokens: 0,
      totalLatency: 0,
    });
  }, [disconnect]);

  return {
    state,
    isConnected,
    disconnect,
    reset,
  };
}
