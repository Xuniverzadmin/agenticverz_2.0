// Layer: L1 — Product Experience
// Product: ai-console
// Temporal:
//   Trigger: import-time
//   Execution: sync
// Role: Worker type definitions
// Callers: Worker components
// Allowed Imports: L2
// Forbidden Imports: L3, L4, L5, L6
// Reference: Frontend Types

// Worker Execution Types for Business Builder Worker v0.2

export interface BrandRequest {
  company_name: string;
  tagline?: string;
  mission: string;
  vision?: string;
  value_proposition: string;
  target_audience?: string[];
  audience_pain_points?: string[];
  tone?: {
    primary: string;
    avoid?: string[];
    examples_good?: string[];
    examples_bad?: string[];
  };
  voice_attributes?: string[];
  forbidden_claims?: Array<{
    pattern: string;
    reason: string;
    severity: string;
  }>;
  required_disclosures?: string[];
  visual?: {
    primary_color?: string;
    secondary_color?: string;
    font_heading?: string;
    font_body?: string;
    logo_placement?: string;
  };
  budget_tokens?: number;
}

export interface WorkerRunRequest {
  task: string;
  brand?: BrandRequest;
  budget?: number;
  strict_mode?: boolean;
  depth?: 'auto' | 'shallow' | 'deep';
  async_mode?: boolean;
  stream?: boolean;
}

export interface WorkerRunResponse {
  run_id: string;
  success: boolean;
  status: 'queued' | 'running' | 'completed' | 'failed';
  artifacts?: Record<string, unknown>;
  replay_token?: Record<string, unknown>;
  cost_report?: {
    total_tokens: number;
    budget: number | null;
    under_budget: boolean;
    stages: Record<string, unknown>;
    policy_violations: number;
    recoveries: number;
  };
  policy_violations?: Array<{
    policy: string;
    reason: string;
    pattern?: string;
    severity?: string;
    stage?: string;
    type?: string;
  }>;
  recovery_log?: Array<{
    stage: string;
    recovery: string;
  }>;
  drift_metrics?: Record<string, number>;
  execution_trace?: Array<{
    stage: string;
    status: string;
    latency_ms: number;
    agent_used?: string;
  }>;
  routing_decisions?: Array<{
    stage_id: string;
    selected_agent: string;
    complexity: number;
    confidence: number;
    alternatives?: string[];
  }>;
  error?: string;
  total_tokens_used?: number;
  total_latency_ms?: number;
  created_at?: string;
}

// SSE Event Types
export type WorkerEventType =
  | 'connected'
  | 'run_started'
  | 'stage_started'
  | 'stage_completed'
  | 'stage_failed'
  | 'log'
  | 'routing_decision'
  | 'policy_check'
  | 'policy_violation'
  | 'drift_detected'
  | 'failure_detected'
  | 'recovery_started'
  | 'recovery_completed'
  | 'artifact_created'
  | 'run_completed'
  | 'run_failed'
  | 'stream_end';

export interface WorkerEvent {
  type: WorkerEventType;
  timestamp: string;
  run_id: string;
  data: Record<string, unknown>;
}

export interface StageEvent {
  stage_id: string;
  stage_index?: number;
  total_stages?: number;
  duration_ms?: number;
  tokens_used?: number;
  error?: string;
}

export interface LogEvent {
  stage_id: string;
  agent: string;
  message: string;
  level: 'debug' | 'info' | 'warning' | 'error';
}

export interface RoutingDecisionEvent {
  stage_id: string;
  selected_agent: string;
  complexity: number;
  confidence: number;
  alternatives?: string[];
}

export interface PolicyEvent {
  stage_id: string;
  policy: string;
  passed?: boolean;
  reason?: string;
  pattern?: string;
  severity?: string;
}

export interface DriftEvent {
  stage_id: string;
  drift_score: number;
  threshold: number;
  aligned: boolean;
}

export interface ArtifactEvent {
  stage_id: string;
  artifact_name: string;
  artifact_type: string;
  content?: string;
}

export interface ArtifactContent {
  name: string;
  type: string;
  content: string;
  stage_id: string;
  timestamp?: string;
}

export interface RunCompletedEvent {
  success: boolean;
  total_tokens?: number;
  total_latency_ms?: number;
  artifacts_count?: number;
  error?: string;
}

// Stage status for UI
export type StageStatus = 'pending' | 'running' | 'completed' | 'failed' | 'recovered';

export interface StageState {
  id: string;
  name: string;
  status: StageStatus;
  agent?: string;
  startedAt?: string;
  completedAt?: string;
  duration_ms?: number;
  tokens?: number;
  drift_score?: number;
  policy_passed?: boolean;
  error?: string;
}

// UI State
export interface WorkerExecutionState {
  runId: string | null;
  status: 'idle' | 'running' | 'completed' | 'failed';
  task: string;
  stages: StageState[];
  logs: LogEvent[];
  routingDecisions: RoutingDecisionEvent[];
  policyEvents: PolicyEvent[];
  driftEvents: DriftEvent[];
  artifacts: ArtifactEvent[];
  artifactContents: Record<string, ArtifactContent>;
  recoveries: Array<{ stage: string; recovery: string }>;
  error?: string;
  totalTokens: number;
  totalLatency: number;
  replayToken?: Record<string, unknown>;
}

// Worker definition for multi-worker support
export interface WorkerDefinition {
  id: string;
  name: string;
  description: string;
  status: 'available' | 'coming_soon' | 'beta';
  moats: string[];
}

// Run history item
export interface RunHistoryItem {
  run_id: string;
  task: string;
  status: string;
  success: boolean | null;
  created_at: string;
  total_latency_ms: number | null;
  worker_id?: string;
}
