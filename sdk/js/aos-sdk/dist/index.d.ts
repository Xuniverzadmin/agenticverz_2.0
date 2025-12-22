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
 * AOS Deterministic Runtime Context (JavaScript)
 *
 * Provides deterministic primitives for simulation and replay:
 * - Fixed seed for reproducible randomness (using seedrandom algorithm)
 * - Frozen time for time-independent simulation
 * - Tenant isolation
 * - RNG state capture for audit
 *
 * IMPORTANT: This implementation must produce IDENTICAL results to Python
 * for the same seed to ensure cross-language trace parity.
 *
 * Usage:
 *   const ctx = new RuntimeContext({ seed: 42, now: "2025-12-06T12:00:00Z" });
 *   const value = ctx.randint(1, 100);  // Same result for same seed as Python
 *   const ts = ctx.timestamp();  // Frozen timestamp
 *
 * @module runtime
 */
interface RuntimeContextOptions {
    /** Random seed for deterministic behavior (default: 42) */
    seed?: number;
    /** Frozen timestamp as ISO8601 string or Date (default: current UTC time) */
    now?: string | Date;
    /** Tenant identifier for isolation */
    tenantId?: string;
    /** Recorded environment variables (for audit) */
    env?: Record<string, string>;
}
/**
 * Deterministic runtime context for AOS simulation and replay.
 *
 * All randomness and time access must go through this context
 * to ensure reproducible behavior across Python and JavaScript.
 */
declare class RuntimeContext {
    readonly seed: number;
    readonly now: Date;
    readonly tenantId: string;
    readonly env: Record<string, string>;
    readonly rngState: string;
    private _rng;
    constructor(options?: RuntimeContextOptions);
    /**
     * Capture RNG state as hex string for audit.
     */
    private _captureRngState;
    /**
     * Get current RNG state (for step recording)
     */
    captureRngState(): string;
    /**
     * Deterministic random integer in [a, b] inclusive.
     */
    randint(a: number, b: number): number;
    /**
     * Deterministic random float in [0, 1).
     */
    random(): number;
    /**
     * Deterministic random choice from array.
     */
    choice<T>(arr: T[]): T;
    /**
     * Deterministic in-place shuffle.
     */
    shuffle<T>(arr: T[]): void;
    /**
     * Deterministic UUID based on seed and counter.
     */
    uuid(): string;
    /**
     * Return frozen timestamp as ISO8601 string.
     */
    timestamp(): string;
    /**
     * Serialize context for trace.
     */
    toDict(): Record<string, unknown>;
    /**
     * Deserialize context from trace.
     */
    static fromDict(data: Record<string, unknown>): RuntimeContext;
}
/**
 * Parse ISO8601 string to Date.
 */
declare function freezeTime(isoString: string): Date;
/**
 * Serialize object to canonical JSON (sorted keys, compact).
 *
 * This ensures identical objects produce identical byte output
 * across Python and JavaScript.
 */
declare function canonicalJson(obj: unknown): string;
/**
 * Compute deterministic hash of a trace or any data.
 *
 * Uses SHA256 with canonical JSON serialization.
 */
declare function hashTrace(trace: Record<string, unknown>): string;
/**
 * Compute deterministic hash of any data (truncated).
 */
declare function hashData(data: unknown): string;

/**
 * AOS Trace Schema v1.1 (JavaScript)
 *
 * Canonical trace format for simulation replay and verification.
 * Must produce IDENTICAL root_hash as Python for same inputs.
 *
 * Design Principles:
 * - Traces are immutable records of simulation/execution
 * - DETERMINISTIC fields (seed, plan, input/output hashes) form the root_hash
 * - AUDIT fields (timestamps, duration_ms) are preserved but excluded from hash
 * - Canonical JSON ensures identical bytes for identical data
 * - Hash chain provides integrity verification
 *
 * Hash Rules (v1.1):
 * - root_hash computed ONLY from deterministic fields
 * - Audit fields (timestamp, duration_ms) preserved for logging but excluded
 * - Two traces with same seed+plan+inputs+outputs will have IDENTICAL root_hash
 *
 * @module trace
 */

/** Trace schema version - must match Python */
declare const TRACE_SCHEMA_VERSION = "1.1.0";
/** Step outcome types */
type StepOutcome = "success" | "failure" | "skipped";
/** Replay behavior for idempotency */
type ReplayBehavior = "execute" | "skip" | "check";
interface TraceStepData {
    step_index: number;
    skill_id: string;
    input_hash: string;
    output_hash: string;
    rng_state_before: string;
    outcome: StepOutcome;
    idempotency_key?: string | null;
    replay_behavior?: ReplayBehavior;
    duration_ms?: number;
    error_code?: string | null;
    timestamp?: string | null;
}
/**
 * Individual step in a trace.
 *
 * Fields are split into:
 * - DETERMINISTIC: step_index, skill_id, input_hash, output_hash, rng_state_before, outcome, idempotency_key, replay_behavior
 * - AUDIT: timestamp, duration_ms, error_code (for debugging, excluded from hash)
 *
 * Idempotency:
 *   idempotency_key: Unique key for this step's side effects
 *   replay_behavior: How to handle during replay ("execute", "skip", "check")
 */
declare class TraceStep {
    readonly stepIndex: number;
    readonly skillId: string;
    readonly inputHash: string;
    readonly outputHash: string;
    readonly rngStateBefore: string;
    readonly outcome: StepOutcome;
    readonly idempotencyKey: string | null;
    readonly replayBehavior: ReplayBehavior;
    readonly durationMs: number;
    readonly errorCode: string | null;
    readonly timestamp: string;
    constructor(data: TraceStepData);
    /**
     * Return ONLY deterministic fields for hashing.
     *
     * This payload is used to compute the step's contribution to root_hash.
     * Audit fields (timestamp, duration_ms) are excluded.
     * Idempotency fields (idempotency_key, replay_behavior) ARE included.
     */
    deterministicPayload(): Record<string, unknown>;
    /**
     * Compute hash of deterministic payload only.
     * Must match Python's TraceStep.deterministic_hash()
     */
    deterministicHash(): string;
    /**
     * Serialize step to dict (includes all fields for storage).
     */
    toDict(): TraceStepData;
    /**
     * Deserialize step from dict.
     */
    static fromDict(data: TraceStepData): TraceStep;
}
interface TraceData {
    version?: string;
    seed: number;
    timestamp?: string;
    tenant_id?: string;
    plan: Record<string, unknown>[];
    steps?: TraceStepData[];
    root_hash?: string | null;
    finalized?: boolean;
    metadata?: Record<string, unknown>;
}
interface AddStepOptions {
    skillId: string;
    inputData: unknown;
    outputData: unknown;
    rngState: string;
    durationMs: number;
    outcome: StepOutcome;
    errorCode?: string | null;
    /** Unique key for non-idempotent operations (e.g., payment_id) */
    idempotencyKey?: string | null;
    /** How to handle during replay: "execute" (default), "skip", or "check" */
    replayBehavior?: ReplayBehavior;
}
/**
 * Complete execution trace for replay and verification.
 *
 * A trace captures everything needed to replay a simulation:
 * - Random seed (deterministic)
 * - Frozen timestamp (deterministic - part of context)
 * - Plan (deterministic)
 * - Each step's input/output hashes (deterministic)
 * - Audit data (timestamps, durations - for logging only)
 *
 * The root_hash is computed ONLY from deterministic fields, ensuring
 * two traces with identical seeds and inputs produce identical hashes
 * regardless of when they were executed.
 */
declare class Trace {
    readonly version: string;
    readonly seed: number;
    readonly timestamp: string;
    readonly tenantId: string;
    readonly plan: Record<string, unknown>[];
    readonly steps: TraceStep[];
    readonly metadata: Record<string, unknown>;
    rootHash: string | null;
    finalized: boolean;
    constructor(data: TraceData);
    /**
     * Add a step to the trace.
     *
     * @throws Error if trace is already finalized
     */
    addStep(options: AddStepOptions): TraceStep;
    /**
     * Finalize trace and compute root hash.
     *
     * The root_hash is computed from DETERMINISTIC fields only:
     * - seed, timestamp (frozen), tenant_id
     * - Each step's deterministic_payload
     *
     * @throws Error if trace is already finalized
     */
    finalize(): string;
    /**
     * Compute Merkle-like root hash over deterministic fields only.
     *
     * Hash chain construction (must match Python exactly):
     * 1. Start with seed:timestamp:tenant_id
     * 2. For each step, chain with step.deterministic_hash()
     */
    private _computeRootHash;
    /**
     * Verify trace integrity.
     */
    verify(): boolean;
    /**
     * Serialize trace to dict (includes all fields).
     */
    toDict(): TraceData;
    /**
     * Serialize to canonical JSON string.
     */
    toJson(): string;
    /**
     * Deserialize trace from dict.
     */
    static fromDict(data: TraceData): Trace;
    /**
     * Deserialize from JSON string.
     */
    static fromJson(jsonStr: string): Trace;
    /**
     * Save trace to file.
     */
    save(path: string): void;
    /**
     * Load trace from file.
     */
    static load(path: string): Trace;
}
interface DiffResult {
    match: boolean;
    differences: Array<{
        field: string;
        trace1: unknown;
        trace2: unknown;
    }>;
    summary: string;
}
/**
 * Compare two traces for DETERMINISTIC equality.
 *
 * Compares only deterministic fields:
 * - seed, timestamp (frozen), tenant_id
 * - step input/output hashes, rng_state, outcome
 * - root_hash
 *
 * Audit fields (step timestamps, duration_ms) are NOT compared.
 */
declare function diffTraces(trace1: Trace, trace2: Trace): DiffResult;
/**
 * Create a new trace from a RuntimeContext.
 */
declare function createTraceFromContext(ctx: RuntimeContext, plan: Record<string, unknown>[]): Trace;

/**
 * Reset idempotency tracking (for testing).
 */
declare function resetIdempotencyState(): void;
/**
 * Mark an idempotency key as executed.
 */
declare function markIdempotencyKeyExecuted(key: string): void;
/**
 * Check if an idempotency key has been executed.
 */
declare function isIdempotencyKeyExecuted(key: string): boolean;
/** Result of replaying a trace step */
interface ReplayResult {
    stepIndex: number;
    action: "executed" | "skipped" | "checked" | "failed";
    reason?: string | null;
    outputMatch?: boolean | null;
}
/**
 * Replay a single trace step with idempotency safety.
 *
 * Behavior based on replay_behavior:
 * - "execute": Always execute the step
 * - "skip": Skip if idempotency_key already executed
 * - "check": Execute and verify output matches original
 */
declare function replayStep(step: TraceStep, executeFn?: () => unknown, idempotencyStore?: Set<string>): ReplayResult;
/**
 * Generate a deterministic idempotency key for a step.
 *
 * Use this for non-idempotent operations like:
 * - Payment processing
 * - Database writes
 * - External API calls with side effects
 */
declare function generateIdempotencyKey(runId: string, stepIndex: number, skillId: string, inputHash: string): string;

/**
 * AOS SDK for JavaScript/TypeScript
 *
 * The official JavaScript/TypeScript SDK for AOS (Agentic Operating System).
 * The most predictable, reliable, deterministic SDK for building machine-native agents.
 *
 * Core Classes:
 *   AOSClient: HTTP client for AOS API
 *   RuntimeContext: Deterministic runtime context (seed, time, RNG)
 *   Trace: Execution trace for replay and verification
 *
 * Usage:
 *   import { AOSClient, RuntimeContext, Trace } from "@agenticverz/aos-sdk";
 *
 *   // Deterministic simulation
 *   const ctx = new RuntimeContext({ seed: 42, now: "2025-12-06T12:00:00Z" });
 *   const client = new AOSClient();
 *   const result = await client.simulate(plan, { seed: ctx.seed });
 *
 *   // Trace and replay
 *   const trace = new Trace({ seed: 42, plan });
 *   trace.addStep({ ... });
 *   trace.finalize();
 *   trace.save("run.trace.json");
 *
 * @packageDocumentation
 */

declare const VERSION = "0.1.0";

export { AOSClient, type AOSClientOptions, AOSError, type AOSErrorResponse, type AddStepOptions, type Agent, type Capabilities, type CostModel, type DiffResult, type FailureMode, type MemoryEntry, type MemoryResult, NovaClient, type PlanStep, type QueryResult, type QueryType, type RateLimit, type ReplayBehavior, type ReplayResult, type ResourceContract, type Run, type RunOutcome, type RunStatus, RuntimeContext, type RuntimeContextOptions, type SimulateResult, type Skill, type SkillDescriptor, type StepOutcome, type StepSimulation, TRACE_SCHEMA_VERSION, Trace, type TraceData, TraceStep, type TraceStepData, VERSION, canonicalJson, createTraceFromContext, diffTraces, freezeTime, generateIdempotencyKey, hashData, hashTrace, isIdempotencyKeyExecuted, markIdempotencyKeyExecuted, replayStep, resetIdempotencyState };
