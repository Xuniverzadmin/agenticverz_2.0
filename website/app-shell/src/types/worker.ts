/**
 * Worker Types
 * Types for worker execution and streaming
 */

export interface BrandRequest {
  company_name: string;
  mission: string;
  value_proposition: string;
  tagline?: string;
  tone?: {
    primary: 'casual' | 'neutral' | 'professional' | 'formal' | 'luxury';
    secondary?: string;
  };
  target_audience?: 'b2c_consumer' | 'b2c_prosumer' | 'b2b_smb' | 'b2b_enterprise' | 'b2b_developer';
  industry?: string;
  competitors?: string[];
}

export interface RunHistoryItem {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  brand_request: BrandRequest;
  started_at: string;
  completed_at?: string;
  artifacts?: Record<string, unknown>;
  error?: string;
}

export interface WorkerDefinition {
  id: string;
  name: string;
  description: string;
  status: 'available' | 'coming_soon' | 'beta';
  moats: string[];
}

export type StageStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

export interface StageState {
  id: string;
  name: string;
  status: StageStatus;
  started_at?: string;
  completed_at?: string;
  progress?: number;
  substeps?: SubstepState[];
}

export interface SubstepState {
  id: string;
  name: string;
  status: StageStatus;
  started_at?: string;
  completed_at?: string;
}

export interface LogEvent {
  event_id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  stage_id?: string;
  metadata?: Record<string, unknown>;
}

export interface ArtifactEvent {
  event_id: string;
  timestamp: string;
  artifact_type: string;
  artifact_id: string;
  stage_id?: string;
  preview?: string;
  data?: Record<string, unknown>;
}

export interface RoutingDecisionEvent {
  event_id: string;
  timestamp: string;
  decision_type: 'model_selection' | 'skill_routing' | 'fallback' | 'escalation';
  from?: string;
  to: string;
  reason: string;
  confidence?: number;
  metadata?: Record<string, unknown>;
}

export interface DriftEvent {
  event_id: string;
  timestamp: string;
  drift_type: 'cost' | 'latency' | 'quality' | 'policy';
  severity: 'low' | 'medium' | 'high' | 'critical';
  expected?: number | string;
  actual?: number | string;
  message: string;
  stage_id?: string;
}

export interface PolicyEvent {
  event_id: string;
  timestamp: string;
  policy_id: string;
  policy_type: 'budget' | 'rate_limit' | 'guardrail' | 'approval';
  action: 'allowed' | 'blocked' | 'warned' | 'escalated';
  message: string;
  metadata?: Record<string, unknown>;
}

export interface WorkerStreamState {
  status: 'idle' | 'connecting' | 'connected' | 'error' | 'completed';
  run_id?: string;
  stages: StageState[];
  logs: LogEvent[];
  artifacts: ArtifactEvent[];
  routingDecisions: RoutingDecisionEvent[];
  driftEvents: DriftEvent[];
  policyEvents: PolicyEvent[];
  error?: string;
  progress?: number;
}
