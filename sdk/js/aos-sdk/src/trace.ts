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

import { createHash } from "crypto";
import { readFileSync, writeFileSync } from "fs";
import { RuntimeContext, canonicalJson, hashData } from "./runtime";

/** Trace schema version - must match Python */
export const TRACE_SCHEMA_VERSION = "1.1.0";

/** Step outcome types */
export type StepOutcome = "success" | "failure" | "skipped";

/** Replay behavior for idempotency */
export type ReplayBehavior = "execute" | "skip" | "check";

export interface TraceStepData {
  step_index: number;
  skill_id: string;
  input_hash: string;
  output_hash: string;
  rng_state_before: string;
  outcome: StepOutcome;
  // Idempotency fields (deterministic)
  idempotency_key?: string | null;
  replay_behavior?: ReplayBehavior;
  // Audit fields
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
export class TraceStep {
  // Deterministic fields (included in hash)
  readonly stepIndex: number;
  readonly skillId: string;
  readonly inputHash: string;
  readonly outputHash: string;
  readonly rngStateBefore: string;
  readonly outcome: StepOutcome;

  // Idempotency fields (deterministic - included in hash)
  readonly idempotencyKey: string | null;
  readonly replayBehavior: ReplayBehavior;

  // Audit fields (excluded from deterministic hash)
  readonly durationMs: number;
  readonly errorCode: string | null;
  readonly timestamp: string;

  constructor(data: TraceStepData) {
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
    this.timestamp = data.timestamp ?? new Date().toISOString();
  }

  /**
   * Return ONLY deterministic fields for hashing.
   *
   * This payload is used to compute the step's contribution to root_hash.
   * Audit fields (timestamp, duration_ms) are excluded.
   * Idempotency fields (idempotency_key, replay_behavior) ARE included.
   */
  deterministicPayload(): Record<string, unknown> {
    return {
      step_index: this.stepIndex,
      skill_id: this.skillId,
      input_hash: this.inputHash,
      output_hash: this.outputHash,
      rng_state_before: this.rngStateBefore,
      outcome: this.outcome,
      idempotency_key: this.idempotencyKey,
      replay_behavior: this.replayBehavior,
    };
  }

  /**
   * Compute hash of deterministic payload only.
   * Must match Python's TraceStep.deterministic_hash()
   */
  deterministicHash(): string {
    const canonical = canonicalJson(this.deterministicPayload());
    return createHash("sha256").update(canonical).digest("hex");
  }

  /**
   * Serialize step to dict (includes all fields for storage).
   */
  toDict(): TraceStepData {
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
      timestamp: this.timestamp,
    };
  }

  /**
   * Deserialize step from dict.
   */
  static fromDict(data: TraceStepData): TraceStep {
    return new TraceStep(data);
  }
}

export interface TraceData {
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

export interface AddStepOptions {
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
export class Trace {
  readonly version: string;
  readonly seed: number;
  readonly timestamp: string;
  readonly tenantId: string;
  readonly plan: Record<string, unknown>[];
  readonly steps: TraceStep[];
  readonly metadata: Record<string, unknown>;
  rootHash: string | null;
  finalized: boolean;

  constructor(data: TraceData) {
    this.version = data.version ?? TRACE_SCHEMA_VERSION;
    this.seed = data.seed;
    this.timestamp = data.timestamp ?? new Date().toISOString();
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
  addStep(options: AddStepOptions): TraceStep {
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
      timestamp: new Date().toISOString(),
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
  finalize(): string {
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
  private _computeRootHash(): string {
    // Base hash from deterministic trace metadata
    const base = `${this.seed}:${this.timestamp}:${this.tenantId}`;
    let chainHash = createHash("sha256").update(base).digest("hex");

    // Chain each step's deterministic hash
    for (const step of this.steps) {
      const stepDetHash = step.deterministicHash();
      const combined = `${chainHash}:${stepDetHash}`;
      chainHash = createHash("sha256").update(combined).digest("hex");
    }

    return chainHash;
  }

  /**
   * Verify trace integrity.
   */
  verify(): boolean {
    if (!this.finalized || !this.rootHash) {
      return false;
    }
    return this.rootHash === this._computeRootHash();
  }

  /**
   * Serialize trace to dict (includes all fields).
   */
  toDict(): TraceData {
    return {
      version: this.version,
      seed: this.seed,
      timestamp: this.timestamp,
      tenant_id: this.tenantId,
      plan: this.plan,
      steps: this.steps.map((s) => s.toDict()),
      root_hash: this.rootHash,
      finalized: this.finalized,
      metadata: this.metadata,
    };
  }

  /**
   * Serialize to canonical JSON string.
   */
  toJson(): string {
    return canonicalJson(this.toDict());
  }

  /**
   * Deserialize trace from dict.
   */
  static fromDict(data: TraceData): Trace {
    return new Trace(data);
  }

  /**
   * Deserialize from JSON string.
   */
  static fromJson(jsonStr: string): Trace {
    return Trace.fromDict(JSON.parse(jsonStr) as TraceData);
  }

  /**
   * Save trace to file.
   */
  save(path: string): void {
    writeFileSync(path, this.toJson());
  }

  /**
   * Load trace from file.
   */
  static load(path: string): Trace {
    return Trace.fromJson(readFileSync(path, "utf-8"));
  }
}

export interface DiffResult {
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
export function diffTraces(trace1: Trace, trace2: Trace): DiffResult {
  const differences: DiffResult["differences"] = [];

  // Check deterministic metadata
  if (trace1.seed !== trace2.seed) {
    differences.push({
      field: "seed",
      trace1: trace1.seed,
      trace2: trace2.seed,
    });
  }

  if (trace1.timestamp !== trace2.timestamp) {
    differences.push({
      field: "timestamp",
      trace1: trace1.timestamp,
      trace2: trace2.timestamp,
    });
  }

  if (trace1.tenantId !== trace2.tenantId) {
    differences.push({
      field: "tenant_id",
      trace1: trace1.tenantId,
      trace2: trace2.tenantId,
    });
  }

  // Check step count
  if (trace1.steps.length !== trace2.steps.length) {
    differences.push({
      field: "step_count",
      trace1: trace1.steps.length,
      trace2: trace2.steps.length,
    });
  }

  // Check individual steps (deterministic fields only)
  const minSteps = Math.min(trace1.steps.length, trace2.steps.length);
  for (let i = 0; i < minSteps; i++) {
    const s1 = trace1.steps[i];
    const s2 = trace2.steps[i];

    if (s1.skillId !== s2.skillId) {
      differences.push({
        field: `step[${i}].skill_id`,
        trace1: s1.skillId,
        trace2: s2.skillId,
      });
    }
    if (s1.inputHash !== s2.inputHash) {
      differences.push({
        field: `step[${i}].input_hash`,
        trace1: s1.inputHash,
        trace2: s2.inputHash,
      });
    }
    if (s1.outputHash !== s2.outputHash) {
      differences.push({
        field: `step[${i}].output_hash`,
        trace1: s1.outputHash,
        trace2: s2.outputHash,
      });
    }
    if (s1.rngStateBefore !== s2.rngStateBefore) {
      differences.push({
        field: `step[${i}].rng_state`,
        trace1: s1.rngStateBefore,
        trace2: s2.rngStateBefore,
      });
    }
    if (s1.outcome !== s2.outcome) {
      differences.push({
        field: `step[${i}].outcome`,
        trace1: s1.outcome,
        trace2: s2.outcome,
      });
    }
  }

  // Check root hash
  if (trace1.rootHash !== trace2.rootHash) {
    differences.push({
      field: "root_hash",
      trace1: trace1.rootHash,
      trace2: trace2.rootHash,
    });
  }

  const match = differences.length === 0;

  let summary: string;
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

/**
 * Create a new trace from a RuntimeContext.
 */
export function createTraceFromContext(
  ctx: RuntimeContext,
  plan: Record<string, unknown>[]
): Trace {
  return new Trace({
    seed: ctx.seed,
    timestamp: ctx.timestamp(),
    tenant_id: ctx.tenantId,
    plan,
  });
}

// Re-export hashData from runtime for convenience
export { hashData } from "./runtime";

// ============================================================================
// Idempotency & Replay Safety
// ============================================================================

/** Global idempotency tracking store */
const executedIdempotencyKeys = new Set<string>();

/**
 * Reset idempotency tracking (for testing).
 */
export function resetIdempotencyState(): void {
  executedIdempotencyKeys.clear();
}

/**
 * Mark an idempotency key as executed.
 */
export function markIdempotencyKeyExecuted(key: string): void {
  executedIdempotencyKeys.add(key);
}

/**
 * Check if an idempotency key has been executed.
 */
export function isIdempotencyKeyExecuted(key: string): boolean {
  return executedIdempotencyKeys.has(key);
}

/** Result of replaying a trace step */
export interface ReplayResult {
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
export function replayStep(
  step: TraceStep,
  executeFn?: () => unknown,
  idempotencyStore?: Set<string>
): ReplayResult {
  const store = idempotencyStore ?? executedIdempotencyKeys;

  // Check idempotency for "skip" behavior
  if (step.replayBehavior === "skip" && step.idempotencyKey) {
    if (store.has(step.idempotencyKey)) {
      return {
        stepIndex: step.stepIndex,
        action: "skipped",
        reason: `Idempotency key '${step.idempotencyKey}' already executed`,
      };
    }
  }

  // Execute the step
  if (!executeFn) {
    // Dry run - no actual execution
    if (step.replayBehavior === "skip" && step.idempotencyKey) {
      store.add(step.idempotencyKey);
    }
    return {
      stepIndex: step.stepIndex,
      action: step.replayBehavior !== "check" ? "executed" : "checked",
      reason: "Dry run - no execution function provided",
      outputMatch: step.replayBehavior === "check" ? true : null,
    };
  }

  try {
    const output = executeFn();
    const outputHash = hashData(output);

    // Mark idempotency key as executed
    if (step.idempotencyKey) {
      store.add(step.idempotencyKey);
    }

    // For "check" behavior, verify output matches
    if (step.replayBehavior === "check") {
      const matches = outputHash === step.outputHash;
      return {
        stepIndex: step.stepIndex,
        action: matches ? "checked" : "failed",
        reason: matches
          ? null
          : `Output hash mismatch: ${outputHash} != ${step.outputHash}`,
        outputMatch: matches,
      };
    }

    return {
      stepIndex: step.stepIndex,
      action: "executed",
      reason: null,
    };
  } catch (e) {
    return {
      stepIndex: step.stepIndex,
      action: "failed",
      reason: e instanceof Error ? e.message : String(e),
    };
  }
}

/**
 * Generate a deterministic idempotency key for a step.
 *
 * Use this for non-idempotent operations like:
 * - Payment processing
 * - Database writes
 * - External API calls with side effects
 */
export function generateIdempotencyKey(
  runId: string,
  stepIndex: number,
  skillId: string,
  inputHash: string
): string {
  const keyData = `${runId}:${stepIndex}:${skillId}:${inputHash}`;
  return createHash("sha256").update(keyData).digest("hex").slice(0, 32);
}
