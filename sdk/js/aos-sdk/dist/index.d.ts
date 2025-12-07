/**
 * AOS SDK Type Definitions
 */
interface AOSClientOptions {
    /** API key for authentication. If not provided, reads from AOS_API_KEY env var */
    apiKey?: string;
    /** Base URL of the AOS server */
    baseUrl?: string;
    /** Request timeout in milliseconds */
    timeout?: number;
}
interface PlanStep {
    /** Skill to execute */
    skill: string;
    /** Skill parameters */
    params: Record<string, unknown>;
}
interface SimulateResult {
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
interface StepSimulation {
    /** Step index */
    index: number;
    /** Skill name */
    skill: string;
    /** Estimated cost for this step */
    estimated_cost_cents: number;
    /** Whether this step is feasible */
    feasible: boolean;
}
type QueryType = "remaining_budget_cents" | "what_did_i_try_already" | "allowed_skills" | "last_step_outcome" | "skills_available_for_goal";
interface QueryResult {
    /** Query type */
    query_type: string;
    /** Query result */
    result: unknown;
}
interface Skill {
    /** Skill ID */
    id: string;
    /** Skill name */
    name: string;
    /** Description */
    description: string;
    /** Version */
    version: string;
}
interface SkillDescriptor extends Skill {
    /** Cost model */
    cost_model: CostModel;
    /** Failure modes */
    failure_modes: FailureMode[];
    /** Parameters schema */
    params_schema: Record<string, unknown>;
    /** Return schema */
    return_schema: Record<string, unknown>;
}
interface CostModel {
    /** Fixed cost in cents */
    fixed_cents: number;
    /** Variable cost per unit */
    variable_cents_per_unit?: number;
    /** Unit type */
    unit?: string;
}
interface FailureMode {
    /** Error code */
    code: string;
    /** Description */
    description: string;
    /** Whether retryable */
    retryable: boolean;
}
interface Capabilities {
    /** List of available skill IDs */
    skills_available: string[];
    /** Budget remaining in cents */
    budget_remaining_cents: number;
    /** Rate limit info */
    rate_limits: RateLimit[];
    /** Permissions */
    permissions: string[];
}
interface RateLimit {
    /** Resource being limited */
    resource: string;
    /** Limit value */
    limit: number;
    /** Current usage */
    current: number;
    /** Reset time (ISO 8601) */
    resets_at: string;
}
interface ResourceContract {
    /** Resource ID */
    resource_id: string;
    /** Budget allocation */
    budget_cents: number;
    /** Rate limits */
    rate_limits: RateLimit[];
    /** Concurrency limit */
    max_concurrency: number;
}
interface Agent {
    /** Agent ID */
    id: string;
    /** Agent name */
    name: string;
}
interface Run {
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
type RunStatus = "pending" | "running" | "succeeded" | "failed";
interface RunOutcome {
    /** Success flag */
    success: boolean;
    /** Result data */
    data?: unknown;
    /** Error if failed */
    error?: AOSErrorResponse;
}
interface AOSErrorResponse {
    /** Error code */
    code: string;
    /** Error message */
    message: string;
    /** Additional details */
    details?: Record<string, unknown>;
}
interface MemoryResult {
    /** Memory entries */
    entries: MemoryEntry[];
    /** Total count */
    total: number;
}
interface MemoryEntry {
    /** Entry ID */
    id: string;
    /** Content */
    content: string;
    /** Relevance score */
    score: number;
    /** Timestamp */
    timestamp: string;
}

/**
 * AOS JavaScript/TypeScript SDK Client
 *
 * Usage:
 *   import { AOSClient } from '@agenticverz/aos-sdk';
 *   const client = new AOSClient({ apiKey: '...', baseUrl: 'http://localhost:8000' });
 *
 *   // Machine-native APIs
 *   const caps = await client.getCapabilities();
 *   const result = await client.simulate([{ skill: 'http_call', params: { url: '...' } }]);
 */

declare class AOSError extends Error {
    statusCode?: number;
    response?: unknown;
    constructor(message: string, statusCode?: number, response?: unknown);
}
declare class AOSClient {
    private baseUrl;
    private apiKey?;
    private timeout;
    private headers;
    /**
     * Create a new AOS client.
     *
     * @param options - Client configuration options
     *
     * @example
     * ```typescript
     * const client = new AOSClient({
     *   apiKey: 'your-api-key',
     *   baseUrl: 'http://localhost:8000'
     * });
     * ```
     */
    constructor(options?: AOSClientOptions);
    private url;
    private request;
    /**
     * Simulate a plan before execution.
     *
     * Pre-execution validation to check if a plan is feasible given
     * current constraints (budget, rate limits, permissions).
     *
     * @param plan - List of steps with skill and params
     * @param budgetCents - Available budget in cents (default: 1000)
     * @param agentId - Optional agent ID for permission checking
     * @param tenantId - Optional tenant ID for isolation
     *
     * @example
     * ```typescript
     * const result = await client.simulate([
     *   { skill: 'http_call', params: { url: 'https://api.example.com' } },
     *   { skill: 'llm_invoke', params: { prompt: 'Summarize' } }
     * ]);
     * if (result.feasible) {
     *   console.log(`Plan OK, cost: ${result.estimated_cost_cents}c`);
     * }
     * ```
     */
    simulate(plan: PlanStep[], budgetCents?: number, agentId?: string, tenantId?: string): Promise<SimulateResult>;
    /**
     * Query runtime state.
     *
     * @param queryType - Type of query to execute
     * @param params - Query-specific parameters
     * @param agentId - Optional agent ID for context
     * @param runId - Optional run ID for context
     *
     * Supported query types:
     * - remaining_budget_cents: Current budget remaining
     * - what_did_i_try_already: Previous execution attempts
     * - allowed_skills: List of available skills
     * - last_step_outcome: Most recent execution outcome
     * - skills_available_for_goal: Skills matching a goal
     */
    query(queryType: QueryType, params?: Record<string, unknown>, agentId?: string, runId?: string): Promise<QueryResult>;
    /**
     * List all available skills.
     *
     * @example
     * ```typescript
     * const { skills } = await client.listSkills();
     * for (const skill of skills) {
     *   console.log(`${skill.name}: ${skill.description}`);
     * }
     * ```
     */
    listSkills(): Promise<{
        skills: Skill[];
        count: number;
    }>;
    /**
     * Get detailed descriptor for a skill.
     *
     * @param skillId - The skill to describe (e.g., 'http_call', 'llm_invoke')
     */
    describeSkill(skillId: string): Promise<SkillDescriptor>;
    /**
     * Get available capabilities for an agent/tenant.
     *
     * @param agentId - Optional agent ID
     * @param tenantId - Optional tenant ID
     *
     * @example
     * ```typescript
     * const caps = await client.getCapabilities();
     * console.log(`Budget: ${caps.budget_remaining_cents}c`);
     * console.log(`Skills: ${caps.skills_available.join(', ')}`);
     * ```
     */
    getCapabilities(agentId?: string, tenantId?: string): Promise<Capabilities>;
    /**
     * Get resource contract for a specific resource.
     *
     * @param resourceId - The resource to get contract for
     */
    getResourceContract(resourceId: string): Promise<ResourceContract>;
    /**
     * Create a new agent.
     *
     * @param name - Name for the agent
     * @returns Agent ID
     */
    createAgent(name: string): Promise<string>;
    /**
     * Post a goal for an agent to execute.
     *
     * @param agentId - Agent ID to execute the goal
     * @param goal - Goal description
     * @param forceSkill - Optional skill to force use
     * @returns Run ID for tracking execution
     */
    postGoal(agentId: string, goal: string, forceSkill?: string): Promise<string>;
    /**
     * Poll for run completion.
     *
     * @param agentId - Agent ID
     * @param runId - Run ID to poll
     * @param timeout - Maximum wait time in milliseconds (default: 30000)
     * @param interval - Poll interval in milliseconds (default: 500)
     * @returns Run result when completed
     * @throws Error if run doesn't complete within timeout
     */
    pollRun(agentId: string, runId: string, timeout?: number, interval?: number): Promise<Run>;
    /**
     * Query agent memory.
     *
     * @param agentId - Agent ID
     * @param query - Search query
     * @param k - Number of results to return (default: 5)
     */
    recall(agentId: string, query: string, k?: number): Promise<MemoryResult>;
    /**
     * Create a new run for an agent.
     *
     * @param agentId - Agent ID
     * @param goal - Goal description
     * @param plan - Optional pre-defined plan
     */
    createRun(agentId: string, goal: string, plan?: PlanStep[]): Promise<Run>;
    /**
     * Get run status and details.
     *
     * @param runId - Run ID
     */
    getRun(runId: string): Promise<Run>;
}
declare const NovaClient: typeof AOSClient;

/**
 * AOS SDK for JavaScript/TypeScript
 *
 * The official JavaScript/TypeScript SDK for AOS (Agentic Operating System).
 * The most predictable, reliable, deterministic SDK for building machine-native agents.
 *
 * @packageDocumentation
 */

declare const VERSION = "0.1.0";

export { AOSClient, type AOSClientOptions, AOSError, type AOSErrorResponse, type Agent, type Capabilities, type CostModel, type FailureMode, type MemoryEntry, type MemoryResult, NovaClient, type PlanStep, type QueryResult, type QueryType, type RateLimit, type ResourceContract, type Run, type RunOutcome, type RunStatus, type SimulateResult, type Skill, type SkillDescriptor, type StepSimulation, VERSION };
