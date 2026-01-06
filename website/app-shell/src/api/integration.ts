/**
 * @audience founder
 *
 * M25 Integration Loop API Client
 *
 * API for managing the 5-pillar integration feedback loop.
 * Provides real-time loop status, human checkpoints, and stage management.
 */

import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export type LoopStage =
  | 'incident_detected'
  | 'pattern_matched'
  | 'recovery_suggested'
  | 'policy_generated'
  | 'routing_adjusted'
  | 'loop_complete';

export type LoopFailureState =
  | 'match_failed'
  | 'match_low_confidence'
  | 'recovery_rejected'
  | 'recovery_needs_confirmation'
  | 'policy_low_confidence'
  | 'policy_shadow_mode'
  | 'policy_rejected'
  | 'routing_guardrail_blocked'
  | 'routing_kpi_regression'
  | 'human_checkpoint_pending'
  | 'human_checkpoint_rejected';

export type ConfidenceBand = 'strong' | 'weak' | 'novel';

export type PolicyMode = 'shadow' | 'pending' | 'active' | 'disabled';

export type CheckpointType =
  | 'approve_policy'
  | 'approve_recovery'
  | 'simulate_routing'
  | 'revert_loop'
  | 'override_guardrail';

export interface LoopStatus {
  id: string;
  incident_id: string;
  tenant_id: string;
  current_stage: LoopStage;
  stages: Record<string, StageStatus>;
  is_complete: boolean;
  is_blocked: boolean;
  failure_state: LoopFailureState | null;
  pending_checkpoints: HumanCheckpoint[];
  started_at: string;
  completed_at: string | null;
  narrative: NarrativeArtifact | null;
}

export interface StageStatus {
  stage: LoopStage;
  completed: boolean;
  timestamp: string | null;
  details: Record<string, unknown>;
  failure_state: LoopFailureState | null;
  confidence_band: ConfidenceBand | null;
}

export interface HumanCheckpoint {
  id: string;
  checkpoint_type: CheckpointType;
  incident_id: string;
  tenant_id: string;
  stage: LoopStage;
  target_id: string;
  description: string;
  options: CheckpointOption[];
  created_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution: string | null;
}

export interface CheckpointOption {
  action: string;
  label: string;
  description: string;
  is_destructive: boolean;
}

export interface NarrativeArtifact {
  what_happened: string;
  what_we_learned: string;
  what_we_changed: string;
  confidence_summary: string;
  human_decisions: string[];
  timeline: NarrativeEvent[];
}

export interface NarrativeEvent {
  timestamp: string;
  stage: LoopStage;
  description: string;
  confidence_band: ConfidenceBand | null;
  requires_attention: boolean;
}

export interface IntegrationStats {
  loops_today: number;
  loops_complete: number;
  loops_blocked: number;
  avg_completion_time_ms: number;
  patterns_matched: number;
  recoveries_applied: number;
  policies_activated: number;
  human_checkpoints_pending: number;
  confidence_distribution: Record<ConfidenceBand, number>;
}

// ============================================================================
// M25 Graduation Types
// ============================================================================

export interface GateEvidence {
  name: string;
  description: string;
  passed: boolean;
  evidence: Record<string, unknown>;
}

export interface GraduationStatus {
  status: string;
  is_graduated: boolean;
  gates: {
    gate1_prevention: GateEvidence;
    gate2_rollback: GateEvidence;
    gate3_console: GateEvidence;
  };
  next_action: string;
  prevention_stats: {
    total: number;
    rate: string;
  };
  regret_stats: {
    total_events: number;
    auto_demotions: number;
  };
}

export interface TimelineEvent {
  type: string;
  timestamp: string;
  icon: string;
  headline: string;
  description: string;
  details: Record<string, unknown>;
  is_milestone: boolean;
}

export interface PreventionTimeline {
  incident_id: string;
  tenant_id: string;
  timeline: TimelineEvent[];
  summary: {
    event_count: number;
    has_prevention: boolean;
    has_rollback: boolean;
    is_learning_proof: boolean;
  };
  narrative: string;
}

export interface SimulatePreventionRequest {
  policy_id: string;
  pattern_id: string;
  original_incident_id: string;
  confidence?: number;
}

export interface SimulateRegretRequest {
  policy_id: string;
  regret_type?: string;
  severity?: number;
  description?: string;
}

// ============================================================================
// API Functions
// ============================================================================

export const integrationApi = {
  /**
   * Get loop status for an incident
   */
  async getLoopStatus(incidentId: string): Promise<LoopStatus> {
    const response = await apiClient.get(`/integration/loop/${incidentId}`);
    return response.data;
  },

  /**
   * Get all stages for an incident loop
   */
  async getLoopStages(incidentId: string): Promise<StageStatus[]> {
    const response = await apiClient.get(`/integration/loop/${incidentId}/stages`);
    return response.data;
  },

  /**
   * Get narrative artifacts for an incident
   */
  async getNarrative(incidentId: string): Promise<NarrativeArtifact> {
    const response = await apiClient.get(`/integration/loop/${incidentId}/narrative`);
    return response.data;
  },

  /**
   * Retry a failed stage
   */
  async retryStage(incidentId: string, stage: LoopStage): Promise<LoopStatus> {
    const response = await apiClient.post(`/integration/loop/${incidentId}/retry`, { stage });
    return response.data;
  },

  /**
   * Revert a loop to a previous stage
   */
  async revertLoop(incidentId: string, toStage: LoopStage): Promise<LoopStatus> {
    const response = await apiClient.post(`/integration/loop/${incidentId}/revert`, { to_stage: toStage });
    return response.data;
  },

  /**
   * Get pending human checkpoints
   */
  async getPendingCheckpoints(tenantId?: string): Promise<HumanCheckpoint[]> {
    const params = tenantId ? { tenant_id: tenantId } : {};
    const response = await apiClient.get('/integration/checkpoints', { params });
    return response.data;
  },

  /**
   * Resolve a human checkpoint
   */
  async resolveCheckpoint(
    checkpointId: string,
    resolution: string,
    notes?: string
  ): Promise<HumanCheckpoint> {
    const response = await apiClient.post(`/integration/checkpoints/${checkpointId}/resolve`, {
      resolution,
      notes,
    });
    return response.data;
  },

  /**
   * Get integration statistics
   */
  async getStats(tenantId?: string): Promise<IntegrationStats> {
    const params = tenantId ? { tenant_id: tenantId } : {};
    const response = await apiClient.get('/integration/stats', { params });
    return response.data;
  },

  /**
   * Create SSE connection for real-time loop updates
   */
  createLoopStream(incidentId: string): EventSource {
    const baseUrl = import.meta.env.VITE_API_BASE || '';
    return new EventSource(`${baseUrl}/integration/loop/${incidentId}/stream`);
  },

  // ==========================================================================
  // M25 Graduation API
  // ==========================================================================

  /**
   * Get M25 graduation status
   * Shows progress through the 3 graduation gates
   */
  async getGraduationStatus(): Promise<GraduationStatus> {
    const response = await apiClient.get('/integration/graduation');
    return response.data;
  },

  /**
   * Get prevention timeline for an incident
   * Gate 3 UI - shows the learning loop in action
   */
  async getPreventionTimeline(incidentId: string): Promise<PreventionTimeline> {
    const response = await apiClient.get(`/integration/timeline/${incidentId}`);
    return response.data;
  },

  /**
   * Simulate a prevention event (for demo/testing)
   * Fast-tracks Gate 1 passage
   */
  async simulatePrevention(request: SimulatePreventionRequest): Promise<{ gate1_passed: boolean }> {
    const response = await apiClient.post('/integration/graduation/simulate/prevention', request);
    return response.data;
  },

  /**
   * Simulate a regret event (for demo/testing)
   * Fast-tracks Gate 2 passage
   */
  async simulateRegret(request: SimulateRegretRequest): Promise<{ gate2_passed: boolean }> {
    const response = await apiClient.post('/integration/graduation/simulate/regret', request);
    return response.data;
  },

  /**
   * Simulate viewing timeline (for demo/testing)
   * Fast-tracks Gate 3 passage
   */
  async simulateTimelineView(incidentId: string): Promise<{ gate3_passed: boolean }> {
    const response = await apiClient.post(`/integration/graduation/simulate/timeline-view?incident_id=${incidentId}`);
    return response.data;
  },
};

export default integrationApi;
