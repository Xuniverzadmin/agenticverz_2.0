// SBA (Strategy-Bound Agents) TypeScript Types
// M15.1.1 SBA Inspector UI

// ============================================================================
// SBA Schema Types (mirrors backend app/agents/sba/schema.py)
// ============================================================================

export interface WinningAspiration {
  description: string;
}

export interface WhereToPlay {
  domain: string;
  input_constraints?: Record<string, unknown>;
  allowed_tools: string[];
  allowed_contexts: string[];
  boundaries?: string;
}

export interface FulfillmentHistoryEntry {
  old_metric: number;
  new_metric: number;
  reason?: string;
  job_id?: string;
  timestamp: string;
}

export interface HowToWin {
  tasks: string[];
  tests: string[];
  fulfillment_metric: number;
  fulfillment_history?: FulfillmentHistoryEntry[];
}

export type DependencyType = 'tool' | 'agent' | 'api' | 'service';

export interface Dependency {
  type: DependencyType;
  name: string;
  version?: string;
  required: boolean;
  fallback?: string;
}

export interface EnvironmentRequirements {
  cpu?: string;
  memory?: string;
  budget_tokens?: number;
  timeout_seconds?: number;
}

export interface CapabilitiesCapacity {
  dependencies: Dependency[];
  legacy_dependencies: string[];
  env: EnvironmentRequirements;
}

export interface EnablingManagementSystems {
  orchestrator: string;
  governance: 'BudgetLLM' | 'None';
}

export interface SBASchema {
  sba_version: string;
  winning_aspiration: WinningAspiration;
  where_to_play: WhereToPlay;
  how_to_win: HowToWin;
  capabilities_capacity: CapabilitiesCapacity;
  enabling_management_systems: EnablingManagementSystems;
  agent_id?: string;
  created_at?: string;
  updated_at?: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export type AgentType = 'worker' | 'orchestrator' | 'aggregator';
export type AgentStatus = 'active' | 'deprecated' | 'disabled';

export interface SBAAgent {
  agent_id: string;
  agent_name?: string;
  agent_type: AgentType;
  sba?: SBASchema;
  sba_version?: string;
  sba_validated: boolean;
  status: AgentStatus;
  enabled: boolean;
}

export interface SBAAgentWithFulfillment {
  agent_id: string;
  agent_name?: string;
  agent_type: AgentType;
  domain: string;
  orchestrator: string;
  fulfillment_metric: number;
  fulfillment_history: FulfillmentHistoryEntry[];
  sba_validated: boolean;
  marketplace_ready: boolean;
  status: AgentStatus;
}

export interface FulfillmentAggregated {
  agents: SBAAgentWithFulfillment[];
  groups: Record<string, string[]>;
  summary: {
    total_agents: number;
    validated_count: number;
    avg_fulfillment: number;
    marketplace_ready_count: number;
    by_fulfillment_range: Record<string, number>;
  };
}

// ============================================================================
// Filter and UI State Types
// ============================================================================

export interface SBAFilters {
  agent_type?: AgentType | '';
  sba_validated?: boolean | null;
  domain?: string;
  search?: string;
}

export type GroupByOption = 'domain' | 'agent_type' | 'orchestrator';
export type ViewMode = 'list' | 'heatmap';

// ============================================================================
// Validation Types
// ============================================================================

export interface SBAValidationError {
  code: string;
  field: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface SBAValidationResult {
  valid: boolean;
  errors: SBAValidationError[];
  warnings: string[];
}

export interface SpawnCheckResult {
  agent_id: string;
  spawn_allowed: boolean;
  error?: string;
}

// ============================================================================
// Version Negotiation Types
// ============================================================================

export interface SBAVersionInfo {
  current: string;
  supported: string[];
  min_supported: string;
  max_supported: string;
  deprecated: string[];
}

export interface VersionNegotiationResult {
  requested: string;
  negotiated: string | null;
  supported: boolean;
  deprecated: boolean;
  message?: string;
  supported_versions?: string[];
}
