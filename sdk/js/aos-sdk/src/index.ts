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

// Client exports
export { AOSClient, AOSError, NovaClient } from "./client";

// Runtime exports (determinism)
export {
  RuntimeContext,
  freezeTime,
  canonicalJson,
  hashTrace,
  hashData,
} from "./runtime";
export type { RuntimeContextOptions } from "./runtime";

// Trace exports (v1.1 schema)
export {
  Trace,
  TraceStep,
  diffTraces,
  createTraceFromContext,
  TRACE_SCHEMA_VERSION,
  // Idempotency & Replay
  resetIdempotencyState,
  markIdempotencyKeyExecuted,
  isIdempotencyKeyExecuted,
  replayStep,
  generateIdempotencyKey,
} from "./trace";
export type {
  TraceData,
  TraceStepData,
  StepOutcome,
  ReplayBehavior,
  AddStepOptions,
  DiffResult,
  ReplayResult,
} from "./trace";

// Type exports
export type {
  AOSClientOptions,
  PlanStep,
  SimulateResult,
  StepSimulation,
  QueryType,
  QueryResult,
  Skill,
  SkillDescriptor,
  CostModel,
  FailureMode,
  Capabilities,
  RateLimit,
  ResourceContract,
  Agent,
  Run,
  RunStatus,
  RunOutcome,
  AOSErrorResponse,
  MemoryResult,
  MemoryEntry,
} from "./types";

export const VERSION = "0.1.0";
