/**
 * RuntimeContext Tests
 *
 * Tests deterministic behavior and cross-language parity with Python.
 */

import { describe, it, expect } from "vitest";
import { RuntimeContext, canonicalJson, hashData, freezeTime } from "../src/runtime";

describe("RuntimeContext", () => {
  it("should use default seed of 42", () => {
    const ctx = new RuntimeContext();
    expect(ctx.seed).toBe(42);
  });

  it("should accept custom seed", () => {
    const ctx = new RuntimeContext({ seed: 1337 });
    expect(ctx.seed).toBe(1337);
  });

  it("should produce deterministic random integers", () => {
    const ctx1 = new RuntimeContext({ seed: 42 });
    const ctx2 = new RuntimeContext({ seed: 42 });

    const vals1 = Array.from({ length: 10 }, () => ctx1.randint(0, 1000));
    const vals2 = Array.from({ length: 10 }, () => ctx2.randint(0, 1000));

    expect(vals1).toEqual(vals2);
  });

  it("should produce different values for different seeds", () => {
    const ctx1 = new RuntimeContext({ seed: 42 });
    const ctx2 = new RuntimeContext({ seed: 43 });

    const vals1 = Array.from({ length: 10 }, () => ctx1.randint(0, 1000));
    const vals2 = Array.from({ length: 10 }, () => ctx2.randint(0, 1000));

    expect(vals1).not.toEqual(vals2);
  });

  it("should produce deterministic UUIDs", () => {
    const ctx1 = new RuntimeContext({ seed: 42 });
    const ctx2 = new RuntimeContext({ seed: 42 });

    const uuid1 = ctx1.uuid();
    const uuid2 = ctx2.uuid();

    expect(uuid1).toBe(uuid2);
    expect(uuid1).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
  });

  it("should freeze time from ISO string", () => {
    const ctx = new RuntimeContext({ now: "2025-01-01T00:00:00Z" });
    expect(ctx.timestamp()).toBe("2025-01-01T00:00:00.000Z");
  });

  it("should capture RNG state", () => {
    const ctx = new RuntimeContext({ seed: 42 });
    expect(ctx.rngState).toBeTruthy();
    expect(ctx.rngState.length).toBe(16);
  });

  it("should serialize to dict", () => {
    const ctx = new RuntimeContext({
      seed: 42,
      now: "2025-01-01T00:00:00Z",
      tenantId: "test-tenant",
    });

    const dict = ctx.toDict();
    expect(dict.seed).toBe(42);
    expect(dict.tenant_id).toBe("test-tenant");
    expect(dict.rng_state).toBeTruthy();
  });

  it("should deserialize from dict", () => {
    const original = new RuntimeContext({
      seed: 777,
      now: "2025-06-15T12:00:00Z",
      tenantId: "restored",
    });

    const dict = original.toDict();
    const restored = RuntimeContext.fromDict(dict);

    expect(restored.seed).toBe(777);
    expect(restored.tenantId).toBe("restored");
  });
});

describe("canonicalJson", () => {
  it("should sort keys deterministically", () => {
    const obj1 = { b: 2, a: 1, c: 3 };
    const obj2 = { c: 3, a: 1, b: 2 };

    expect(canonicalJson(obj1)).toBe(canonicalJson(obj2));
  });

  it("should handle nested objects", () => {
    const obj1 = { outer: { z: 26, a: 1 }, x: 1 };
    const obj2 = { x: 1, outer: { a: 1, z: 26 } };

    expect(canonicalJson(obj1)).toBe(canonicalJson(obj2));
  });

  it("should preserve arrays in order", () => {
    const obj = { arr: [3, 1, 2] };
    const json = canonicalJson(obj);
    expect(json).toContain("[3,1,2]");
  });

  it("should produce compact JSON", () => {
    const obj = { a: 1, b: 2 };
    const json = canonicalJson(obj);
    expect(json).not.toContain(" ");
  });
});

describe("hashData", () => {
  it("should produce same hash for same data", () => {
    const data = { x: 1, y: 2 };
    expect(hashData(data)).toBe(hashData(data));
  });

  it("should produce same hash regardless of key order", () => {
    const data1 = { b: 2, a: 1 };
    const data2 = { a: 1, b: 2 };
    expect(hashData(data1)).toBe(hashData(data2));
  });

  it("should produce 16-char hex string", () => {
    const hash = hashData({ test: "data" });
    expect(hash.length).toBe(16);
    expect(hash).toMatch(/^[0-9a-f]{16}$/);
  });

  it("should produce different hashes for different data", () => {
    expect(hashData({ x: 1 })).not.toBe(hashData({ x: 2 }));
  });
});

describe("freezeTime", () => {
  it("should parse ISO string with Z suffix", () => {
    const date = freezeTime("2025-01-01T00:00:00Z");
    expect(date.toISOString()).toBe("2025-01-01T00:00:00.000Z");
  });

  it("should parse ISO string with timezone offset", () => {
    const date = freezeTime("2025-01-01T05:00:00+05:00");
    expect(date.toISOString()).toBe("2025-01-01T00:00:00.000Z");
  });
});

describe("Multi-seed determinism", () => {
  const seeds = [0, 1, 42, 1337, 999999, 2147483647];

  seeds.forEach((seed) => {
    it(`should be deterministic for seed ${seed}`, () => {
      const ctx1 = new RuntimeContext({ seed });
      const ctx2 = new RuntimeContext({ seed });

      const vals1 = Array.from({ length: 100 }, () => ctx1.randint(0, 1000000));
      const vals2 = Array.from({ length: 100 }, () => ctx2.randint(0, 1000000));

      expect(vals1).toEqual(vals2);
    });
  });
});
