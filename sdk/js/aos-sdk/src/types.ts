/**
 * AOS SDK Type Definitions
 */

export interface AOSClientOptions {
  /** API key for authentication. If not provided, reads from AOS_API_KEY env var */
  apiKey?: string;
  /** Base URL of the AOS server */
  baseUrl?: string;
  /** Request timeout in milliseconds */
  timeout?: number;
}

export interface PlanStep {
  /** Skill to execute */
  skill: string;
  /** Skill parameters */
  params: Record<string, unknown>;
}

export interface SimulateRequest {
  /** List of plan steps */
  plan: PlanStep[];
  /** Budget in cents */
  budget_cents: number;
  /** Optional agent ID */
  agent_id?: string;
  /** Optional tenant ID */
  tenant_id?: string;
}

export interface SimulateResult {
  /** Whether the plan is feasible */
  feasible: boolean;
  /** Estimated cost in cents */
  estimated_cost_cents: number;
  /** Risk assessment */
  risks?: string[];
  /** Reason if not feasible */
  reason?: string;
  /** Per-step breakdown */
  steps?: StepSimulation[];
}

export interface StepSimulation {
  /** Step index */
  index: number;
  /** Skill name */
  skill: string;
  /** Estimated cost for this step */
  estimated_cost_cents: number;
  /** Whether this step is feasible */
  feasible: boolean;
}

export interface QueryRequest {
  /** Query type */
  query_type: QueryType;
  /** Query parameters */
  params?: Record<string, unknown>;
  /** Optional agent ID */
  agent_id?: string;
  /** Optional run ID */
  run_id?: string;
}

export type QueryType =
  | "remaining_budget_cents"
  | "what_did_i_try_already"
  | "allowed_skills"
  | "last_step_outcome"
  | "skills_available_for_goal";

export interface QueryResult {
  /** Query type */
  query_type: string;
  /** Query result */
  result: unknown;
}

export interface Skill {
  /** Skill ID */
  id: string;
  /** Skill name */
  name: string;
  /** Description */
  description: string;
  /** Version */
  version: string;
}

export interface SkillDescriptor extends Skill {
  /** Cost model */
  cost_model: CostModel;
  /** Failure modes */
  failure_modes: FailureMode[];
  /** Parameters schema */
  params_schema: Record<string, unknown>;
  /** Return schema */
  return_schema: Record<string, unknown>;
}

export interface CostModel {
  /** Fixed cost in cents */
  fixed_cents: number;
  /** Variable cost per unit */
  variable_cents_per_unit?: number;
  /** Unit type */
  unit?: string;
}

export interface FailureMode {
  /** Error code */
  code: string;
  /** Description */
  description: string;
  /** Whether retryable */
  retryable: boolean;
}

export interface Capabilities {
  /** List of available skill IDs */
  skills_available: string[];
  /** Budget remaining in cents */
  budget_remaining_cents: number;
  /** Rate limit info */
  rate_limits: RateLimit[];
  /** Permissions */
  permissions: string[];
}

export interface RateLimit {
  /** Resource being limited */
  resource: string;
  /** Limit value */
  limit: number;
  /** Current usage */
  current: number;
  /** Reset time (ISO 8601) */
  resets_at: string;
}

export interface ResourceContract {
  /** Resource ID */
  resource_id: string;
  /** Budget allocation */
  budget_cents: number;
  /** Rate limits */
  rate_limits: RateLimit[];
  /** Concurrency limit */
  max_concurrency: number;
}

export interface Agent {
  /** Agent ID */
  id: string;
  /** Agent name */
  name: string;
}

export interface Run {
  /** Run ID */
  id: string;
  /** Run status */
  status: RunStatus;
  /** Agent ID */
  agent_id: string;
  /** Goal */
  goal: string;
  /** Created timestamp */
  created_at: string;
  /** Completed timestamp */
  completed_at?: string;
  /** Outcome if completed */
  outcome?: RunOutcome;
}

export type RunStatus = "pending" | "running" | "succeeded" | "failed";

export interface RunOutcome {
  /** Success flag */
  success: boolean;
  /** Result data */
  data?: unknown;
  /** Error if failed */
  error?: AOSErrorResponse;
}

export interface AOSErrorResponse {
  /** Error code */
  code: string;
  /** Error message */
  message: string;
  /** Additional details */
  details?: Record<string, unknown>;
}

export interface MemoryResult {
  /** Memory entries */
  entries: MemoryEntry[];
  /** Total count */
  total: number;
}

export interface MemoryEntry {
  /** Entry ID */
  id: string;
  /** Content */
  content: string;
  /** Relevance score */
  score: number;
  /** Timestamp */
  timestamp: string;
}
