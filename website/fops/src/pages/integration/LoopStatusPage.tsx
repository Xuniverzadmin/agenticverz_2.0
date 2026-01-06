/**
 * M25 Integration Loop Status Page
 *
 * Visualizes the 5-pillar integration feedback loop:
 * Incident → Pattern → Recovery → Policy → Routing
 *
 * Features:
 * - Pipeline-style stage visualization
 * - Confidence band indicators (strong/weak/novel)
 * - Human checkpoint resolution
 * - Failure state handling
 * - Narrative artifacts for storytelling
 * - Real-time SSE updates
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { logger } from '@/lib/consoleLogger';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { Modal } from '@/components/common/Modal';
import { Spinner } from '@/components/common/Spinner';
import {
  integrationApi,
  LoopStage,
  LoopStatus,
  StageStatus,
  HumanCheckpoint,
  ConfidenceBand,
  LoopFailureState,
  NarrativeArtifact,
} from '@/api/integration';

// ============================================================================
// Constants
// ============================================================================

const STAGES: { key: LoopStage; label: string; icon: string }[] = [
  { key: 'incident_detected', label: 'Incident', icon: '🚨' },
  { key: 'pattern_matched', label: 'Pattern', icon: '🔍' },
  { key: 'recovery_suggested', label: 'Recovery', icon: '💡' },
  { key: 'policy_generated', label: 'Policy', icon: '📋' },
  { key: 'routing_adjusted', label: 'Routing', icon: '🔀' },
];

const CONFIDENCE_CONFIG: Record<ConfidenceBand, { label: string; color: string; bgColor: string }> = {
  strong: { label: 'Strong', color: 'text-green-400', bgColor: 'bg-green-500/20' },
  weak: { label: 'Weak', color: 'text-yellow-400', bgColor: 'bg-yellow-500/20' },
  novel: { label: 'Novel', color: 'text-purple-400', bgColor: 'bg-purple-500/20' },
};

const FAILURE_MESSAGES: Record<LoopFailureState, string> = {
  match_failed: 'No pattern match found - this is a novel incident',
  match_low_confidence: 'Pattern match confidence below threshold',
  recovery_rejected: 'Suggested recovery was rejected',
  recovery_needs_confirmation: 'Recovery requires human confirmation',
  policy_low_confidence: 'Generated policy has low confidence',
  policy_shadow_mode: 'Policy is in shadow mode (observing only)',
  policy_rejected: 'Generated policy was rejected',
  routing_guardrail_blocked: 'Routing adjustment blocked by guardrail',
  routing_kpi_regression: 'Routing rollback due to KPI regression',
  human_checkpoint_pending: 'Waiting for human decision',
  human_checkpoint_rejected: 'Human rejected the action',
};

// ============================================================================
// Main Component
// ============================================================================

export function LoopStatusPage() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<HumanCheckpoint | null>(null);
  const [showNarrative, setShowNarrative] = useState(false);

  // Component logging
  useEffect(() => {
    logger.componentMount('LoopStatusPage');
    return () => logger.componentUnmount('LoopStatusPage');
  }, []);

  // Fetch loop status
  const { data: loopStatus, isLoading, error } = useQuery({
    queryKey: ['integration', 'loop', incidentId],
    queryFn: () => integrationApi.getLoopStatus(incidentId!),
    enabled: !!incidentId,
    refetchInterval: 5000,
  });

  // Fetch narrative
  const { data: narrative } = useQuery({
    queryKey: ['integration', 'narrative', incidentId],
    queryFn: () => integrationApi.getNarrative(incidentId!),
    enabled: !!incidentId && loopStatus?.is_complete,
  });

  // SSE for real-time updates
  useEffect(() => {
    if (!incidentId) return;

    const eventSource = integrationApi.createLoopStream(incidentId);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      queryClient.setQueryData(['integration', 'loop', incidentId], data);
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => eventSource.close();
  }, [incidentId, queryClient]);

  // Retry mutation
  const retryMutation = useMutation({
    mutationFn: (stage: LoopStage) => integrationApi.retryStage(incidentId!, stage),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'loop', incidentId] });
    },
    onError: (error) => {
      logger.error('INTEGRATION', 'Failed to retry stage', error);
    },
  });

  // Revert mutation
  const revertMutation = useMutation({
    mutationFn: (toStage: LoopStage) => integrationApi.revertLoop(incidentId!, toStage),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'loop', incidentId] });
    },
    onError: (error) => {
      logger.error('INTEGRATION', 'Failed to revert loop', error);
    },
  });

  // Resolve checkpoint mutation
  const resolveCheckpointMutation = useMutation({
    mutationFn: ({ id, resolution }: { id: string; resolution: string }) =>
      integrationApi.resolveCheckpoint(id, resolution),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration'] });
      setSelectedCheckpoint(null);
    },
    onError: (error) => {
      logger.error('INTEGRATION', 'Failed to resolve checkpoint', error);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !loopStatus) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="text-red-400 text-5xl mb-4">⚠️</div>
          <h3 className="text-lg font-medium text-gray-100">Loop Not Found</h3>
          <p className="text-gray-400 mt-2">Unable to load integration loop status</p>
          <Button className="mt-4" onClick={() => navigate(-1)}>
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Integration Loop</h1>
          <p className="text-gray-400 mt-1">
            Incident: <span className="font-mono">{incidentId}</span>
          </p>
        </div>
        <div className="flex items-center gap-4">
          {loopStatus.is_complete && (
            <Button variant="secondary" onClick={() => setShowNarrative(true)}>
              View Narrative
            </Button>
          )}
          <StatusBadge status={loopStatus} />
        </div>
      </div>

      {/* Pipeline Visualization */}
      <Card className="p-6 bg-slate-800/50 border-slate-700">
        <h2 className="text-lg font-semibold text-gray-100 mb-6">Loop Progress</h2>
        <PipelineVisualization loopStatus={loopStatus} onRetry={retryMutation.mutate} />
      </Card>

      {/* Failure Alert */}
      {loopStatus.failure_state && (
        <FailureAlert
          failureState={loopStatus.failure_state}
          onRetry={() => {
            const currentStage = getCurrentStage(loopStatus);
            if (currentStage) retryMutation.mutate(currentStage);
          }}
        />
      )}

      {/* Pending Checkpoints */}
      {loopStatus.pending_checkpoints.length > 0 && (
        <Card className="p-6 bg-amber-900/20 border-amber-600">
          <h2 className="text-lg font-semibold text-amber-400 mb-4">
            ⏳ Pending Human Decisions ({loopStatus.pending_checkpoints.length})
          </h2>
          <div className="space-y-3">
            {loopStatus.pending_checkpoints.map((checkpoint) => (
              <CheckpointCard
                key={checkpoint.id}
                checkpoint={checkpoint}
                onClick={() => setSelectedCheckpoint(checkpoint)}
              />
            ))}
          </div>
        </Card>
      )}

      {/* Stage Details */}
      <Card className="p-6 bg-slate-800/50 border-slate-700">
        <h2 className="text-lg font-semibold text-gray-100 mb-4">Stage Details</h2>
        <StageDetailsGrid stages={loopStatus.stages} />
      </Card>

      {/* Checkpoint Resolution Modal */}
      <CheckpointModal
        checkpoint={selectedCheckpoint}
        onClose={() => setSelectedCheckpoint(null)}
        onResolve={(resolution) => {
          if (selectedCheckpoint) {
            resolveCheckpointMutation.mutate({
              id: selectedCheckpoint.id,
              resolution,
            });
          }
        }}
        isLoading={resolveCheckpointMutation.isPending}
      />

      {/* Narrative Modal */}
      <NarrativeModal
        open={showNarrative}
        onClose={() => setShowNarrative(false)}
        narrative={narrative}
      />
    </div>
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

function StatusBadge({ status }: { status: LoopStatus }) {
  if (status.is_complete) {
    return (
      <Badge variant="success" className="text-lg px-4 py-2">
        ✓ Loop Complete
      </Badge>
    );
  }
  if (status.is_blocked) {
    return (
      <Badge variant="warning" className="text-lg px-4 py-2">
        ⏸ Blocked
      </Badge>
    );
  }
  return (
    <Badge variant="default" className="text-lg px-4 py-2">
      <span className="animate-pulse mr-2">●</span> In Progress
    </Badge>
  );
}

function PipelineVisualization({
  loopStatus,
  onRetry,
}: {
  loopStatus: LoopStatus;
  onRetry: (stage: LoopStage) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      {STAGES.map((stage, index) => {
        const stageStatus = loopStatus.stages[stage.key];
        const isComplete = stageStatus?.completed ?? false;
        const isCurrent = loopStatus.current_stage === stage.key;
        const hasFailed = stageStatus?.failure_state != null;
        const confidenceBand = stageStatus?.confidence_band;

        return (
          <React.Fragment key={stage.key}>
            <div className="flex flex-col items-center">
              {/* Stage Circle */}
              <div
                className={`
                  w-16 h-16 rounded-full flex items-center justify-center text-2xl
                  border-2 transition-all
                  ${isComplete
                    ? 'bg-green-600 border-green-500'
                    : hasFailed
                    ? 'bg-red-600 border-red-500'
                    : isCurrent
                    ? 'bg-blue-600 border-blue-400 animate-pulse'
                    : 'bg-slate-700 border-slate-600'
                  }
                `}
              >
                {isComplete ? '✓' : hasFailed ? '✗' : stage.icon}
              </div>

              {/* Stage Label */}
              <span
                className={`mt-2 text-sm font-medium ${
                  isComplete ? 'text-green-400' : isCurrent ? 'text-blue-400' : 'text-gray-400'
                }`}
              >
                {stage.label}
              </span>

              {/* Confidence Band */}
              {confidenceBand && (
                <ConfidenceBadge band={confidenceBand} />
              )}

              {/* Retry Button */}
              {hasFailed && (
                <Button
                  size="sm"
                  variant="secondary"
                  className="mt-2"
                  onClick={() => onRetry(stage.key)}
                >
                  Retry
                </Button>
              )}
            </div>

            {/* Connector Line */}
            {index < STAGES.length - 1 && (
              <div
                className={`flex-1 h-1 mx-4 rounded ${
                  loopStatus.stages[STAGES[index + 1].key]?.completed ||
                  STAGES.findIndex((s) => s.key === loopStatus.current_stage) > index
                    ? 'bg-green-500'
                    : 'bg-slate-600'
                }`}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

function ConfidenceBadge({ band }: { band: ConfidenceBand }) {
  const config = CONFIDENCE_CONFIG[band];
  return (
    <span className={`mt-1 px-2 py-0.5 rounded text-xs font-medium ${config.color} ${config.bgColor}`}>
      {config.label}
    </span>
  );
}

function FailureAlert({
  failureState,
  onRetry,
}: {
  failureState: LoopFailureState;
  onRetry: () => void;
}) {
  const message = FAILURE_MESSAGES[failureState] || 'Unknown failure';

  return (
    <Card className="p-4 bg-red-900/20 border-red-600 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className="text-2xl">⚠️</span>
        <div>
          <p className="font-medium text-red-400">Loop Blocked</p>
          <p className="text-sm text-red-300">{message}</p>
        </div>
      </div>
      <Button variant="secondary" onClick={onRetry}>
        Retry Stage
      </Button>
    </Card>
  );
}

function CheckpointCard({
  checkpoint,
  onClick,
}: {
  checkpoint: HumanCheckpoint;
  onClick: () => void;
}) {
  return (
    <div
      className="p-4 bg-slate-800 rounded-lg border border-amber-600/50 cursor-pointer hover:border-amber-500 transition-all"
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium text-gray-100">{checkpoint.description}</p>
          <p className="text-sm text-gray-400 mt-1">
            Stage: {checkpoint.stage} • Target: {checkpoint.target_id}
          </p>
        </div>
        <Button size="sm" variant="primary">
          Resolve
        </Button>
      </div>
    </div>
  );
}

function StageDetailsGrid({ stages }: { stages: Record<string, StageStatus> }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {STAGES.map((stage) => {
        const status = stages[stage.key];
        if (!status) return null;

        return (
          <Card key={stage.key} className="p-4 bg-slate-700/50 border-slate-600">
            <div className="flex items-center gap-2 mb-2">
              <span>{stage.icon}</span>
              <span className="font-medium text-gray-100">{stage.label}</span>
              {status.completed && <Badge variant="success">Complete</Badge>}
            </div>

            {status.confidence_band && (
              <div className="mb-2">
                <ConfidenceBadge band={status.confidence_band} />
              </div>
            )}

            {status.timestamp && (
              <p className="text-xs text-gray-400">
                {new Date(status.timestamp).toLocaleString()}
              </p>
            )}

            {status.details && Object.keys(status.details).length > 0 && (
              <div className="mt-2 text-xs text-gray-400">
                <pre className="bg-slate-800 p-2 rounded overflow-auto max-h-20">
                  {JSON.stringify(status.details, null, 2)}
                </pre>
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
}

function CheckpointModal({
  checkpoint,
  onClose,
  onResolve,
  isLoading,
}: {
  checkpoint: HumanCheckpoint | null;
  onClose: () => void;
  onResolve: (resolution: string) => void;
  isLoading: boolean;
}) {
  if (!checkpoint) return null;

  return (
    <Modal open={!!checkpoint} onClose={onClose} title="Resolve Checkpoint" size="lg">
      <div className="space-y-4">
        <div>
          <p className="text-gray-600 dark:text-gray-300">{checkpoint.description}</p>
          <p className="text-sm text-gray-400 mt-2">
            Type: {checkpoint.checkpoint_type} • Stage: {checkpoint.stage}
          </p>
        </div>

        <div className="space-y-2">
          <p className="font-medium text-gray-700 dark:text-gray-200">Choose an action:</p>
          {checkpoint.options.map((option) => (
            <button
              key={option.action}
              onClick={() => onResolve(option.action)}
              disabled={isLoading}
              className={`
                w-full p-3 text-left rounded-lg border transition-all
                ${option.is_destructive
                  ? 'border-red-300 hover:border-red-500 hover:bg-red-50 dark:hover:bg-red-900/20'
                  : 'border-gray-200 hover:border-blue-500 hover:bg-blue-50 dark:border-slate-600 dark:hover:bg-blue-900/20'
                }
              `}
            >
              <p className={`font-medium ${option.is_destructive ? 'text-red-600' : 'text-gray-900 dark:text-gray-100'}`}>
                {option.label}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{option.description}</p>
            </button>
          ))}
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function NarrativeModal({
  open,
  onClose,
  narrative,
}: {
  open: boolean;
  onClose: () => void;
  narrative: NarrativeArtifact | null | undefined;
}) {
  if (!narrative) return null;

  return (
    <Modal open={open} onClose={onClose} title="Loop Narrative" size="xl">
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="p-4 bg-blue-900/20 border-blue-600">
            <h4 className="font-medium text-blue-400 mb-2">What Happened</h4>
            <p className="text-sm text-gray-300">{narrative.what_happened}</p>
          </Card>
          <Card className="p-4 bg-green-900/20 border-green-600">
            <h4 className="font-medium text-green-400 mb-2">What We Learned</h4>
            <p className="text-sm text-gray-300">{narrative.what_we_learned}</p>
          </Card>
          <Card className="p-4 bg-purple-900/20 border-purple-600">
            <h4 className="font-medium text-purple-400 mb-2">What We Changed</h4>
            <p className="text-sm text-gray-300">{narrative.what_we_changed}</p>
          </Card>
        </div>

        {/* Confidence Summary */}
        <Card className="p-4 bg-slate-800">
          <h4 className="font-medium text-gray-200 mb-2">Confidence Summary</h4>
          <p className="text-sm text-gray-400">{narrative.confidence_summary}</p>
        </Card>

        {/* Human Decisions */}
        {narrative.human_decisions.length > 0 && (
          <div>
            <h4 className="font-medium text-gray-200 mb-2">Human Decisions</h4>
            <ul className="space-y-1">
              {narrative.human_decisions.map((decision, i) => (
                <li key={i} className="text-sm text-gray-400 flex items-center gap-2">
                  <span className="text-amber-400">👤</span> {decision}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Timeline */}
        <div>
          <h4 className="font-medium text-gray-200 mb-3">Timeline</h4>
          <div className="space-y-2">
            {narrative.timeline.map((event, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg border ${
                  event.requires_attention
                    ? 'bg-amber-900/20 border-amber-600'
                    : 'bg-slate-800 border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-200">{event.description}</span>
                  {event.confidence_band && <ConfidenceBadge band={event.confidence_band} />}
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(event.timestamp).toLocaleString()} • {event.stage}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button variant="primary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// ============================================================================
// Helpers
// ============================================================================

function getCurrentStage(loopStatus: LoopStatus): LoopStage | null {
  const stageOrder: LoopStage[] = [
    'incident_detected',
    'pattern_matched',
    'recovery_suggested',
    'policy_generated',
    'routing_adjusted',
  ];

  for (const stage of stageOrder) {
    const status = loopStatus.stages[stage];
    if (!status?.completed) {
      return stage;
    }
  }
  return null;
}

export default LoopStatusPage;
