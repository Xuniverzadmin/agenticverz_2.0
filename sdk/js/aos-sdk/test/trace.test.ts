/**
 * Trace Tests
 *
 * Tests trace schema v1.1, deterministic hashing, and cross-language parity.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { existsSync, unlinkSync } from "fs";
import {
  Trace,
  TraceStep,
  diffTraces,
  createTraceFromContext,
  TRACE_SCHEMA_VERSION,
  hashData,
} from "../src/trace";
import { RuntimeContext } from "../src/runtime";

describe("TRACE_SCHEMA_VERSION", () => {
  it("should be 1.1.0", () => {
    expect(TRACE_SCHEMA_VERSION).toBe("1.1.0");
  });
});

describe("TraceStep", () => {
  it("should create step with all fields", () => {
    const step = new TraceStep({
      step_index: 0,
      skill_id: "test_skill",
      input_hash: "abc123",
      output_hash: "def456",
      rng_state_before: "rng123",
      outcome: "success",
      duration_ms: 100,
      error_code: null,
    });

    expect(step.stepIndex).toBe(0);
    expect(step.skillId).toBe("test_skill");
    expect(step.outcome).toBe("success");
    expect(step.durationMs).toBe(100);
  });

  it("should auto-generate timestamp", () => {
    const step = new TraceStep({
      step_index: 0,
      skill_id: "test",
      input_hash: "a",
      output_hash: "b",
      rng_state_before: "c",
      outcome: "success",
    });

    expect(step.timestamp).toBeTruthy();
    expect(step.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });

  it("should produce deterministic payload excluding audit fields", () => {
    const step = new TraceStep({
      step_index: 0,
      skill_id: "test",
      input_hash: "abc",
      output_hash: "def",
      rng_state_before: "rng",
      outcome: "success",
      duration_ms: 9999, // audit field - should be excluded
      timestamp: "2025-01-01T00:00:00Z", // audit field - should be excluded
    });

    const payload = step.deterministicPayload();

    expect(payload).toHaveProperty("step_index", 0);
    expect(payload).toHaveProperty("skill_id", "test");
    expect(payload).toHaveProperty("outcome", "success");
    expect(payload).not.toHaveProperty("duration_ms");
    expect(payload).not.toHaveProperty("timestamp");
  });

  it("should produce deterministic hash", () => {
    const step1 = new TraceStep({
      step_index: 0,
      skill_id: "test",
      input_hash: "abc",
      output_hash: "def",
      rng_state_before: "rng",
      outcome: "success",
      duration_ms: 100,
    });

    const step2 = new TraceStep({
      step_index: 0,
      skill_id: "test",
      input_hash: "abc",
      output_hash: "def",
      rng_state_before: "rng",
      outcome: "success",
      duration_ms: 9999, // different audit field
    });

    // Hashes should be identical (audit fields excluded)
    expect(step1.deterministicHash()).toBe(step2.deterministicHash());
  });

  it("should serialize and deserialize", () => {
    const step = new TraceStep({
      step_index: 5,
      skill_id: "http_call",
      input_hash: "in123",
      output_hash: "out456",
      rng_state_before: "state789",
      outcome: "failure",
      duration_ms: 250,
      error_code: "HTTP_500",
    });

    const dict = step.toDict();
    const restored = TraceStep.fromDict(dict);

    expect(restored.stepIndex).toBe(5);
    expect(restored.skillId).toBe("http_call");
    expect(restored.outcome).toBe("failure");
    expect(restored.errorCode).toBe("HTTP_500");
  });
});

describe("Trace", () => {
  it("should create trace with required fields", () => {
    const trace = new Trace({
      seed: 42,
      plan: [{ skill: "test", params: {} }],
    });

    expect(trace.seed).toBe(42);
    expect(trace.version).toBe(TRACE_SCHEMA_VERSION);
    expect(trace.finalized).toBe(false);
    expect(trace.rootHash).toBeNull();
  });

  it("should accept frozen timestamp", () => {
    const trace = new Trace({
      seed: 42,
      plan: [],
      timestamp: "2025-01-01T00:00:00Z",
    });

    expect(trace.timestamp).toBe("2025-01-01T00:00:00Z");
  });

  it("should add steps", () => {
    const trace = new Trace({ seed: 42, plan: [] });

    trace.addStep({
      skillId: "test",
      inputData: { x: 1 },
      outputData: { y: 2 },
      rngState: "abc",
      durationMs: 100,
      outcome: "success",
    });

    expect(trace.steps.length).toBe(1);
    expect(trace.steps[0].skillId).toBe("test");
    expect(trace.steps[0].stepIndex).toBe(0);
  });

  it("should reject adding steps after finalize", () => {
    const trace = new Trace({ seed: 42, plan: [] });
    trace.finalize();

    expect(() =>
      trace.addStep({
        skillId: "test",
        inputData: {},
        outputData: {},
        rngState: "a",
        durationMs: 0,
        outcome: "success",
      })
    ).toThrow("Cannot add steps to finalized trace");
  });

  it("should finalize and compute root hash", () => {
    const trace = new Trace({
      seed: 42,
      plan: [{ skill: "test" }],
      timestamp: "2025-01-01T00:00:00Z",
    });

    trace.addStep({
      skillId: "test",
      inputData: { x: 1 },
      outputData: { y: 2 },
      rngState: "abc123",
      durationMs: 100,
      outcome: "success",
    });

    const hash = trace.finalize();

    expect(trace.finalized).toBe(true);
    expect(trace.rootHash).toBeTruthy();
    expect(trace.rootHash).toBe(hash);
    expect(hash.length).toBe(64); // SHA256 hex
  });

  it("should reject double finalization", () => {
    const trace = new Trace({ seed: 42, plan: [] });
    trace.finalize();

    expect(() => trace.finalize()).toThrow("Trace already finalized");
  });

  it("should verify integrity", () => {
    const trace = new Trace({
      seed: 42,
      plan: [],
      timestamp: "2025-01-01T00:00:00Z",
    });

    trace.addStep({
      skillId: "test",
      inputData: {},
      outputData: {},
      rngState: "a",
      durationMs: 0,
      outcome: "success",
    });

    trace.finalize();
    expect(trace.verify()).toBe(true);
  });

  it("should detect tampering", () => {
    const trace = new Trace({
      seed: 42,
      plan: [],
      timestamp: "2025-01-01T00:00:00Z",
    });

    trace.addStep({
      skillId: "test",
      inputData: {},
      outputData: {},
      rngState: "a",
      durationMs: 0,
      outcome: "success",
    });

    trace.finalize();

    // Tamper with the trace
    (trace as any).steps[0] = new TraceStep({
      step_index: 0,
      skill_id: "TAMPERED",
      input_hash: "x",
      output_hash: "y",
      rng_state_before: "z",
      outcome: "success",
    });

    expect(trace.verify()).toBe(false);
  });

  it("should serialize to dict and back", () => {
    const trace = new Trace({
      seed: 777,
      plan: [{ skill: "echo", params: { msg: "hello" } }],
      timestamp: "2025-06-15T12:00:00Z",
      tenant_id: "test-tenant",
      metadata: { demo: true },
    });

    trace.addStep({
      skillId: "echo",
      inputData: { msg: "hello" },
      outputData: { result: "hello" },
      rngState: "state123",
      durationMs: 50,
      outcome: "success",
    });

    trace.finalize();

    const dict = trace.toDict();
    const restored = Trace.fromDict(dict);

    expect(restored.seed).toBe(777);
    expect(restored.tenantId).toBe("test-tenant");
    expect(restored.steps.length).toBe(1);
    expect(restored.rootHash).toBe(trace.rootHash);
    expect(restored.verify()).toBe(true);
  });

  it("should serialize to JSON and back", () => {
    const trace = new Trace({
      seed: 42,
      plan: [{ skill: "test" }],
      timestamp: "2025-01-01T00:00:00Z",
    });

    trace.addStep({
      skillId: "test",
      inputData: { x: 1 },
      outputData: { y: 2 },
      rngState: "abc",
      durationMs: 100,
      outcome: "success",
    });

    trace.finalize();

    const json = trace.toJson();
    const restored = Trace.fromJson(json);

    expect(restored.rootHash).toBe(trace.rootHash);
    expect(restored.verify()).toBe(true);
  });
});

describe("Trace file operations", () => {
  const testPath = "/tmp/test_trace.json";

  beforeEach(() => {
    if (existsSync(testPath)) {
      unlinkSync(testPath);
    }
  });

  it("should save and load trace", () => {
    const trace = new Trace({
      seed: 42,
      plan: [{ skill: "test" }],
      timestamp: "2025-01-01T00:00:00Z",
    });

    trace.addStep({
      skillId: "test",
      inputData: { x: 1 },
      outputData: { y: 2 },
      rngState: "abc",
      durationMs: 100,
      outcome: "success",
    });

    trace.finalize();
    trace.save(testPath);

    const loaded = Trace.load(testPath);

    expect(loaded.rootHash).toBe(trace.rootHash);
    expect(loaded.verify()).toBe(true);

    // Cleanup
    unlinkSync(testPath);
  });
});

describe("diffTraces", () => {
  it("should detect identical traces", () => {
    const trace1 = new Trace({
      seed: 42,
      plan: [],
      timestamp: "2025-01-01T00:00:00Z",
    });
    trace1.addStep({
      skillId: "test",
      inputData: { x: 1 },
      outputData: { y: 2 },
      rngState: "abc",
      durationMs: 100,
      outcome: "success",
    });
    trace1.finalize();

    const trace2 = new Trace({
      seed: 42,
      plan: [],
      timestamp: "2025-01-01T00:00:00Z",
    });
    trace2.addStep({
      skillId: "test",
      inputData: { x: 1 },
      outputData: { y: 2 },
      rngState: "abc",
      durationMs: 999, // different audit field
      outcome: "success",
    });
    trace2.finalize();

    const diff = diffTraces(trace1, trace2);

    expect(diff.match).toBe(true);
    expect(diff.differences.length).toBe(0);
  });

  it("should detect seed difference", () => {
    const trace1 = new Trace({ seed: 42, plan: [], timestamp: "2025-01-01T00:00:00Z" });
    trace1.finalize();

    const trace2 = new Trace({ seed: 43, plan: [], timestamp: "2025-01-01T00:00:00Z" });
    trace2.finalize();

    const diff = diffTraces(trace1, trace2);

    expect(diff.match).toBe(false);
    expect(diff.differences.some((d) => d.field === "seed")).toBe(true);
  });

  it("should detect step count difference", () => {
    const trace1 = new Trace({ seed: 42, plan: [], timestamp: "2025-01-01T00:00:00Z" });
    trace1.addStep({
      skillId: "test",
      inputData: {},
      outputData: {},
      rngState: "a",
      durationMs: 0,
      outcome: "success",
    });
    trace1.finalize();

    const trace2 = new Trace({ seed: 42, plan: [], timestamp: "2025-01-01T00:00:00Z" });
    trace2.finalize();

    const diff = diffTraces(trace1, trace2);

    expect(diff.match).toBe(false);
    expect(diff.differences.some((d) => d.field === "step_count")).toBe(true);
  });
});

describe("createTraceFromContext", () => {
  it("should create trace from RuntimeContext", () => {
    const ctx = new RuntimeContext({
      seed: 777,
      now: "2025-06-15T12:00:00Z",
      tenantId: "context-tenant",
    });

    const plan = [{ skill: "test", params: {} }];
    const trace = createTraceFromContext(ctx, plan);

    expect(trace.seed).toBe(777);
    expect(trace.tenantId).toBe("context-tenant");
    expect(trace.plan).toEqual(plan);
  });
});

describe("Audit fields exclusion (v1.1)", () => {
  it("should produce identical root_hash with different duration_ms", () => {
    const trace1 = new Trace({
      seed: 42,
      plan: [{ skill: "test" }],
      timestamp: "2025-01-01T00:00:00Z",
    });
    trace1.addStep({
      skillId: "test",
      inputData: { x: 1 },
      outputData: { y: 2 },
      rngState: "abc123",
      durationMs: 100,
      outcome: "success",
    });
    trace1.finalize();

    const trace2 = new Trace({
      seed: 42,
      plan: [{ skill: "test" }],
      timestamp: "2025-01-01T00:00:00Z",
    });
    trace2.addStep({
      skillId: "test",
      inputData: { x: 1 },
      outputData: { y: 2 },
      rngState: "abc123",
      durationMs: 9999, // different duration
      outcome: "success",
    });
    trace2.finalize();

    // Root hashes MUST be identical
    expect(trace1.rootHash).toBe(trace2.rootHash);
  });
});

describe("hashData", () => {
  it("should produce 16-char hash", () => {
    const hash = hashData({ test: "data" });
    expect(hash.length).toBe(16);
  });

  it("should be key-order independent", () => {
    const hash1 = hashData({ b: 2, a: 1 });
    const hash2 = hashData({ a: 1, b: 2 });
    expect(hash1).toBe(hash2);
  });
});
