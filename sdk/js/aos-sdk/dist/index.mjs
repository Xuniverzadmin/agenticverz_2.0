// src/client.ts
var AOSError = class extends Error {
  statusCode;
  response;
  constructor(message, statusCode, response) {
    super(message);
    this.name = "AOSError";
    this.statusCode = statusCode;
    this.response = response;
  }
};
var AOSClient = class {
  baseUrl;
  apiKey;
  timeout;
  headers;
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
  constructor(options = {}) {
    this.baseUrl = (options.baseUrl || process.env.AOS_BASE_URL || "http://127.0.0.1:8000").replace(
      /\/+$/,
      ""
    );
    this.apiKey = options.apiKey || process.env.AOS_API_KEY;
    this.timeout = options.timeout || 3e4;
    this.headers = {
      "Content-Type": "application/json"
    };
    if (this.apiKey) {
      this.headers["X-AOS-Key"] = this.apiKey;
    }
  }
  url(path) {
    return `${this.baseUrl}${path}`;
  }
  async request(method, path, options = {}) {
    let url = this.url(path);
    if (options.params) {
      const searchParams = new URLSearchParams(options.params);
      url = `${url}?${searchParams.toString()}`;
    }
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    try {
      const response = await fetch(url, {
        method,
        headers: this.headers,
        body: options.json ? JSON.stringify(options.json) : void 0,
        signal: controller.signal
      });
      if (!response.ok) {
        let errorBody;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = await response.text();
        }
        throw new AOSError(`Request failed: ${response.status}`, response.status, errorBody);
      }
      if (response.status === 204 || response.headers.get("content-length") === "0") {
        return {};
      }
      return await response.json();
    } catch (error) {
      if (error instanceof AOSError) {
        throw error;
      }
      if (error.name === "AbortError") {
        throw new AOSError(`Request timeout after ${this.timeout}ms`);
      }
      throw new AOSError(`Request error: ${error.message}`);
    } finally {
      clearTimeout(timeoutId);
    }
  }
  // =========== Machine-Native APIs ===========
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
  async simulate(plan, budgetCents = 1e3, agentId, tenantId) {
    const payload = {
      plan,
      budget_cents: budgetCents
    };
    if (agentId) payload.agent_id = agentId;
    if (tenantId) payload.tenant_id = tenantId;
    return this.request("POST", "/api/v1/runtime/simulate", { json: payload });
  }
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
  async query(queryType, params, agentId, runId) {
    const payload = {
      query_type: queryType,
      params: params || {}
    };
    if (agentId) payload.agent_id = agentId;
    if (runId) payload.run_id = runId;
    return this.request("POST", "/api/v1/runtime/query", { json: payload });
  }
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
  async listSkills() {
    return this.request("GET", "/api/v1/runtime/skills");
  }
  /**
   * Get detailed descriptor for a skill.
   *
   * @param skillId - The skill to describe (e.g., 'http_call', 'llm_invoke')
   */
  async describeSkill(skillId) {
    return this.request("GET", `/api/v1/runtime/skills/${skillId}`);
  }
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
  async getCapabilities(agentId, tenantId) {
    const params = {};
    if (agentId) params.agent_id = agentId;
    if (tenantId) params.tenant_id = tenantId;
    return this.request("GET", "/api/v1/runtime/capabilities", {
      params: Object.keys(params).length > 0 ? params : void 0
    });
  }
  /**
   * Get resource contract for a specific resource.
   *
   * @param resourceId - The resource to get contract for
   */
  async getResourceContract(resourceId) {
    return this.request("GET", `/api/v1/runtime/resource-contract/${resourceId}`);
  }
  // =========== Agent Workflow APIs ===========
  /**
   * Create a new agent.
   *
   * @param name - Name for the agent
   * @returns Agent ID
   */
  async createAgent(name) {
    const data = await this.request("POST", "/agents", {
      json: { name }
    });
    return data.agent_id || data.id || "";
  }
  /**
   * Post a goal for an agent to execute.
   *
   * @param agentId - Agent ID to execute the goal
   * @param goal - Goal description
   * @param forceSkill - Optional skill to force use
   * @returns Run ID for tracking execution
   */
  async postGoal(agentId, goal, forceSkill) {
    const payload = { goal };
    if (forceSkill) payload.force_skill = forceSkill;
    const data = await this.request("POST", `/agents/${agentId}/goals`, { json: payload });
    return data.run_id || data.run?.id || data.plan?.plan_id || "";
  }
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
  async pollRun(agentId, runId, timeout = 3e4, interval = 500) {
    const end = Date.now() + timeout;
    while (Date.now() < end) {
      try {
        const data = await this.request(
          "GET",
          `/agents/${agentId}/runs/${runId}`
        );
        const status = data.status || data.run?.status || data.plan?.status;
        if (status === "succeeded" || status === "failed") {
          return data;
        }
      } catch {
      }
      await new Promise((resolve) => setTimeout(resolve, interval));
    }
    throw new AOSError(`Run ${runId} did not complete in ${timeout}ms`);
  }
  /**
   * Query agent memory.
   *
   * @param agentId - Agent ID
   * @param query - Search query
   * @param k - Number of results to return (default: 5)
   */
  async recall(agentId, query, k = 5) {
    return this.request("GET", `/agents/${agentId}/recall`, {
      params: { query, k: String(k) }
    });
  }
  // =========== Run Management APIs ===========
  /**
   * Create a new run for an agent.
   *
   * @param agentId - Agent ID
   * @param goal - Goal description
   * @param plan - Optional pre-defined plan
   */
  async createRun(agentId, goal, plan) {
    const payload = {
      agent_id: agentId,
      goal
    };
    if (plan) payload.plan = plan;
    return this.request("POST", "/api/v1/runs", { json: payload });
  }
  /**
   * Get run status and details.
   *
   * @param runId - Run ID
   */
  async getRun(runId) {
    return this.request("GET", `/api/v1/runs/${runId}`);
  }
};
var NovaClient = AOSClient;

// src/runtime.ts
import { createHash } from "crypto";
var SeededRandom = class {
  state;
  constructor(seed) {
    this.state = seed >>> 0;
  }
  /**
   * Generate next random number in [0, 1)
   * Uses xorshift32 algorithm for determinism
   */
  random() {
    let x = this.state;
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    this.state = x >>> 0;
    return (this.state >>> 0) / 4294967296;
  }
  /**
   * Random integer in [a, b] inclusive
   */
  randint(a, b) {
    return Math.floor(this.random() * (b - a + 1)) + a;
  }
  /**
   * Random choice from array
   */
  choice(arr) {
    return arr[this.randint(0, arr.length - 1)];
  }
  /**
   * In-place shuffle (Fisher-Yates)
   */
  shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = this.randint(0, i);
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }
  /**
   * Get state for audit
   */
  getState() {
    return this.state;
  }
};
var RuntimeContext = class _RuntimeContext {
  seed;
  now;
  tenantId;
  env;
  rngState;
  _rng;
  constructor(options = {}) {
    this.seed = options.seed ?? 42;
    this.tenantId = options.tenantId ?? "default";
    this.env = options.env ?? {};
    if (options.now === void 0 || options.now === null) {
      this.now = /* @__PURE__ */ new Date();
    } else if (typeof options.now === "string") {
      this.now = new Date(options.now);
    } else {
      this.now = options.now;
    }
    this._rng = new SeededRandom(this.seed);
    this.rngState = this._captureRngState();
  }
  /**
   * Capture RNG state as hex string for audit.
   */
  _captureRngState() {
    const stateStr = JSON.stringify({ state: this._rng.getState(), seed: this.seed });
    return createHash("sha256").update(stateStr).digest("hex").slice(0, 16);
  }
  /**
   * Get current RNG state (for step recording)
   */
  captureRngState() {
    return this._captureRngState();
  }
  /**
   * Deterministic random integer in [a, b] inclusive.
   */
  randint(a, b) {
    return this._rng.randint(a, b);
  }
  /**
   * Deterministic random float in [0, 1).
   */
  random() {
    return this._rng.random();
  }
  /**
   * Deterministic random choice from array.
   */
  choice(arr) {
    return this._rng.choice(arr);
  }
  /**
   * Deterministic in-place shuffle.
   */
  shuffle(arr) {
    this._rng.shuffle(arr);
  }
  /**
   * Deterministic UUID based on seed and counter.
   */
  uuid() {
    const bytes = [];
    for (let i = 0; i < 16; i++) {
      bytes.push(this._rng.randint(0, 255));
    }
    const hex = bytes.map((b) => b.toString(16).padStart(2, "0")).join("");
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20, 32)}`;
  }
  /**
   * Return frozen timestamp as ISO8601 string.
   */
  timestamp() {
    return this.now.toISOString();
  }
  /**
   * Serialize context for trace.
   */
  toDict() {
    return {
      seed: this.seed,
      now: this.now.toISOString(),
      tenant_id: this.tenantId,
      env: this.env,
      rng_state: this.rngState
    };
  }
  /**
   * Deserialize context from trace.
   */
  static fromDict(data) {
    return new _RuntimeContext({
      seed: data.seed ?? 42,
      now: data.now,
      tenantId: data.tenant_id ?? "default",
      env: data.env ?? {}
    });
  }
};
function freezeTime(isoString) {
  return new Date(isoString);
}
function canonicalJson(obj) {
  return JSON.stringify(obj, (_, value) => {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      return Object.keys(value).sort().reduce((sorted, key) => {
        sorted[key] = value[key];
        return sorted;
      }, {});
    }
    return value;
  });
}
function hashTrace(trace) {
  const canonical = canonicalJson(trace);
  return createHash("sha256").update(canonical).digest("hex");
}
function hashData(data) {
  const canonical = canonicalJson(data);
  return createHash("sha256").update(canonical).digest("hex").slice(0, 16);
}

// src/trace.ts
import { createHash as createHash2 } from "crypto";
import { readFileSync, writeFileSync } from "fs";
var TRACE_SCHEMA_VERSION = "1.1.0";
var TraceStep = class _TraceStep {
  // Deterministic fields (included in hash)
  stepIndex;
  skillId;
  inputHash;
  outputHash;
  rngStateBefore;
  outcome;
  // Idempotency fields (deterministic - included in hash)
  idempotencyKey;
  replayBehavior;
  // Audit fields (excluded from deterministic hash)
  durationMs;
  errorCode;
  timestamp;
  constructor(data) {
    this.stepIndex = data.step_index;
    this.skillId = data.skill_id;
    this.inputHash = data.input_hash;
    this.outputHash = data.output_hash;
    this.rngStateBefore = data.rng_state_before;
    this.outcome = data.outcome;
    this.idempotencyKey = data.idempotency_key ?? null;
    this.replayBehavior = data.replay_behavior ?? "execute";
    this.durationMs = data.duration_ms ?? 0;
    this.errorCode = data.error_code ?? null;
    this.timestamp = data.timestamp ?? (/* @__PURE__ */ new Date()).toISOString();
  }
  /**
   * Return ONLY deterministic fields for hashing.
   *
   * This payload is used to compute the step's contribution to root_hash.
   * Audit fields (timestamp, duration_ms) are excluded.
   * Idempotency fields (idempotency_key, replay_behavior) ARE included.
   */
  deterministicPayload() {
    return {
      step_index: this.stepIndex,
      skill_id: this.skillId,
      input_hash: this.inputHash,
      output_hash: this.outputHash,
      rng_state_before: this.rngStateBefore,
      outcome: this.outcome,
      idempotency_key: this.idempotencyKey,
      replay_behavior: this.replayBehavior
    };
  }
  /**
   * Compute hash of deterministic payload only.
   * Must match Python's TraceStep.deterministic_hash()
   */
  deterministicHash() {
    const canonical = canonicalJson(this.deterministicPayload());
    return createHash2("sha256").update(canonical).digest("hex");
  }
  /**
   * Serialize step to dict (includes all fields for storage).
   */
  toDict() {
    return {
      step_index: this.stepIndex,
      skill_id: this.skillId,
      input_hash: this.inputHash,
      output_hash: this.outputHash,
      rng_state_before: this.rngStateBefore,
      outcome: this.outcome,
      idempotency_key: this.idempotencyKey,
      replay_behavior: this.replayBehavior,
      duration_ms: this.durationMs,
      error_code: this.errorCode,
      timestamp: this.timestamp
    };
  }
  /**
   * Deserialize step from dict.
   */
  static fromDict(data) {
    return new _TraceStep(data);
  }
};
var Trace = class _Trace {
  version;
  seed;
  timestamp;
  tenantId;
  plan;
  steps;
  metadata;
  rootHash;
  finalized;
  constructor(data) {
    this.version = data.version ?? TRACE_SCHEMA_VERSION;
    this.seed = data.seed;
    this.timestamp = data.timestamp ?? (/* @__PURE__ */ new Date()).toISOString();
    this.tenantId = data.tenant_id ?? "default";
    this.plan = data.plan;
    this.steps = (data.steps ?? []).map((s) => TraceStep.fromDict(s));
    this.rootHash = data.root_hash ?? null;
    this.finalized = data.finalized ?? false;
    this.metadata = data.metadata ?? {};
  }
  /**
   * Add a step to the trace.
   *
   * @throws Error if trace is already finalized
   */
  addStep(options) {
    if (this.finalized) {
      throw new Error("Cannot add steps to finalized trace");
    }
    const step = new TraceStep({
      step_index: this.steps.length,
      skill_id: options.skillId,
      input_hash: hashData(options.inputData),
      output_hash: hashData(options.outputData),
      rng_state_before: options.rngState,
      outcome: options.outcome,
      idempotency_key: options.idempotencyKey ?? null,
      replay_behavior: options.replayBehavior ?? "execute",
      duration_ms: options.durationMs,
      error_code: options.errorCode ?? null,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    });
    this.steps.push(step);
    return step;
  }
  /**
   * Finalize trace and compute root hash.
   *
   * The root_hash is computed from DETERMINISTIC fields only:
   * - seed, timestamp (frozen), tenant_id
   * - Each step's deterministic_payload
   *
   * @throws Error if trace is already finalized
   */
  finalize() {
    if (this.finalized) {
      throw new Error("Trace already finalized");
    }
    this.finalized = true;
    this.rootHash = this._computeRootHash();
    return this.rootHash;
  }
  /**
   * Compute Merkle-like root hash over deterministic fields only.
   *
   * Hash chain construction (must match Python exactly):
   * 1. Start with seed:timestamp:tenant_id
   * 2. For each step, chain with step.deterministic_hash()
   */
  _computeRootHash() {
    const base = `${this.seed}:${this.timestamp}:${this.tenantId}`;
    let chainHash = createHash2("sha256").update(base).digest("hex");
    for (const step of this.steps) {
      const stepDetHash = step.deterministicHash();
      const combined = `${chainHash}:${stepDetHash}`;
      chainHash = createHash2("sha256").update(combined).digest("hex");
    }
    return chainHash;
  }
  /**
   * Verify trace integrity.
   */
  verify() {
    if (!this.finalized || !this.rootHash) {
      return false;
    }
    return this.rootHash === this._computeRootHash();
  }
  /**
   * Serialize trace to dict (includes all fields).
   */
  toDict() {
    return {
      version: this.version,
      seed: this.seed,
      timestamp: this.timestamp,
      tenant_id: this.tenantId,
      plan: this.plan,
      steps: this.steps.map((s) => s.toDict()),
      root_hash: this.rootHash,
      finalized: this.finalized,
      metadata: this.metadata
    };
  }
  /**
   * Serialize to canonical JSON string.
   */
  toJson() {
    return canonicalJson(this.toDict());
  }
  /**
   * Deserialize trace from dict.
   */
  static fromDict(data) {
    return new _Trace(data);
  }
  /**
   * Deserialize from JSON string.
   */
  static fromJson(jsonStr) {
    return _Trace.fromDict(JSON.parse(jsonStr));
  }
  /**
   * Save trace to file.
   */
  save(path) {
    writeFileSync(path, this.toJson());
  }
  /**
   * Load trace from file.
   */
  static load(path) {
    return _Trace.fromJson(readFileSync(path, "utf-8"));
  }
};
function diffTraces(trace1, trace2) {
  const differences = [];
  if (trace1.seed !== trace2.seed) {
    differences.push({
      field: "seed",
      trace1: trace1.seed,
      trace2: trace2.seed
    });
  }
  if (trace1.timestamp !== trace2.timestamp) {
    differences.push({
      field: "timestamp",
      trace1: trace1.timestamp,
      trace2: trace2.timestamp
    });
  }
  if (trace1.tenantId !== trace2.tenantId) {
    differences.push({
      field: "tenant_id",
      trace1: trace1.tenantId,
      trace2: trace2.tenantId
    });
  }
  if (trace1.steps.length !== trace2.steps.length) {
    differences.push({
      field: "step_count",
      trace1: trace1.steps.length,
      trace2: trace2.steps.length
    });
  }
  const minSteps = Math.min(trace1.steps.length, trace2.steps.length);
  for (let i = 0; i < minSteps; i++) {
    const s1 = trace1.steps[i];
    const s2 = trace2.steps[i];
    if (s1.skillId !== s2.skillId) {
      differences.push({
        field: `step[${i}].skill_id`,
        trace1: s1.skillId,
        trace2: s2.skillId
      });
    }
    if (s1.inputHash !== s2.inputHash) {
      differences.push({
        field: `step[${i}].input_hash`,
        trace1: s1.inputHash,
        trace2: s2.inputHash
      });
    }
    if (s1.outputHash !== s2.outputHash) {
      differences.push({
        field: `step[${i}].output_hash`,
        trace1: s1.outputHash,
        trace2: s2.outputHash
      });
    }
    if (s1.rngStateBefore !== s2.rngStateBefore) {
      differences.push({
        field: `step[${i}].rng_state`,
        trace1: s1.rngStateBefore,
        trace2: s2.rngStateBefore
      });
    }
    if (s1.outcome !== s2.outcome) {
      differences.push({
        field: `step[${i}].outcome`,
        trace1: s1.outcome,
        trace2: s2.outcome
      });
    }
  }
  if (trace1.rootHash !== trace2.rootHash) {
    differences.push({
      field: "root_hash",
      trace1: trace1.rootHash,
      trace2: trace2.rootHash
    });
  }
  const match = differences.length === 0;
  let summary;
  if (match) {
    summary = "Traces are deterministically identical";
  } else {
    const fields = differences.slice(0, 3).map((d) => d.field);
    summary = `Traces differ in ${differences.length} field(s): ${fields.join(", ")}`;
    if (differences.length > 3) {
      summary += ` and ${differences.length - 3} more`;
    }
  }
  return { match, differences, summary };
}
function createTraceFromContext(ctx, plan) {
  return new Trace({
    seed: ctx.seed,
    timestamp: ctx.timestamp(),
    tenant_id: ctx.tenantId,
    plan
  });
}
var executedIdempotencyKeys = /* @__PURE__ */ new Set();
function resetIdempotencyState() {
  executedIdempotencyKeys.clear();
}
function markIdempotencyKeyExecuted(key) {
  executedIdempotencyKeys.add(key);
}
function isIdempotencyKeyExecuted(key) {
  return executedIdempotencyKeys.has(key);
}
function replayStep(step, executeFn, idempotencyStore) {
  const store = idempotencyStore ?? executedIdempotencyKeys;
  if (step.replayBehavior === "skip" && step.idempotencyKey) {
    if (store.has(step.idempotencyKey)) {
      return {
        stepIndex: step.stepIndex,
        action: "skipped",
        reason: `Idempotency key '${step.idempotencyKey}' already executed`
      };
    }
  }
  if (!executeFn) {
    if (step.replayBehavior === "skip" && step.idempotencyKey) {
      store.add(step.idempotencyKey);
    }
    return {
      stepIndex: step.stepIndex,
      action: step.replayBehavior !== "check" ? "executed" : "checked",
      reason: "Dry run - no execution function provided",
      outputMatch: step.replayBehavior === "check" ? true : null
    };
  }
  try {
    const output = executeFn();
    const outputHash = hashData(output);
    if (step.idempotencyKey) {
      store.add(step.idempotencyKey);
    }
    if (step.replayBehavior === "check") {
      const matches = outputHash === step.outputHash;
      return {
        stepIndex: step.stepIndex,
        action: matches ? "checked" : "failed",
        reason: matches ? null : `Output hash mismatch: ${outputHash} != ${step.outputHash}`,
        outputMatch: matches
      };
    }
    return {
      stepIndex: step.stepIndex,
      action: "executed",
      reason: null
    };
  } catch (e) {
    return {
      stepIndex: step.stepIndex,
      action: "failed",
      reason: e instanceof Error ? e.message : String(e)
    };
  }
}
function generateIdempotencyKey(runId, stepIndex, skillId, inputHash) {
  const keyData = `${runId}:${stepIndex}:${skillId}:${inputHash}`;
  return createHash2("sha256").update(keyData).digest("hex").slice(0, 32);
}

// src/index.ts
var VERSION = "0.1.0";
export {
  AOSClient,
  AOSError,
  NovaClient,
  RuntimeContext,
  TRACE_SCHEMA_VERSION,
  Trace,
  TraceStep,
  VERSION,
  canonicalJson,
  createTraceFromContext,
  diffTraces,
  freezeTime,
  generateIdempotencyKey,
  hashData,
  hashTrace,
  isIdempotencyKeyExecuted,
  markIdempotencyKeyExecuted,
  replayStep,
  resetIdempotencyState
};
