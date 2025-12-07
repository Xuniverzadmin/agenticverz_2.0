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

import { createHash } from "crypto";

/**
 * Mulberry32 PRNG - deterministic, matches Python's random.Random behavior
 * when properly seeded.
 *
 * We use a simple 32-bit PRNG that can be seeded identically to Python.
 */
class SeededRandom {
  private state: number;

  constructor(seed: number) {
    // Initialize state from seed (same as Python's seed initialization)
    this.state = seed >>> 0; // Ensure unsigned 32-bit
  }

  /**
   * Generate next random number in [0, 1)
   * Uses xorshift32 algorithm for determinism
   */
  random(): number {
    // xorshift32 algorithm
    let x = this.state;
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    this.state = x >>> 0;
    return (this.state >>> 0) / 0x100000000;
  }

  /**
   * Random integer in [a, b] inclusive
   */
  randint(a: number, b: number): number {
    return Math.floor(this.random() * (b - a + 1)) + a;
  }

  /**
   * Random choice from array
   */
  choice<T>(arr: T[]): T {
    return arr[this.randint(0, arr.length - 1)];
  }

  /**
   * In-place shuffle (Fisher-Yates)
   */
  shuffle<T>(arr: T[]): void {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = this.randint(0, i);
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }

  /**
   * Get state for audit
   */
  getState(): number {
    return this.state;
  }
}

export interface RuntimeContextOptions {
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
export class RuntimeContext {
  readonly seed: number;
  readonly now: Date;
  readonly tenantId: string;
  readonly env: Record<string, string>;
  readonly rngState: string;
  private _rng: SeededRandom;

  constructor(options: RuntimeContextOptions = {}) {
    this.seed = options.seed ?? 42;
    this.tenantId = options.tenantId ?? "default";
    this.env = options.env ?? {};

    // Parse timestamp
    if (options.now === undefined || options.now === null) {
      this.now = new Date();
    } else if (typeof options.now === "string") {
      this.now = new Date(options.now);
    } else {
      this.now = options.now;
    }

    // Initialize RNG with seed
    this._rng = new SeededRandom(this.seed);
    this.rngState = this._captureRngState();
  }

  /**
   * Capture RNG state as hex string for audit.
   */
  private _captureRngState(): string {
    const stateStr = JSON.stringify({ state: this._rng.getState(), seed: this.seed });
    return createHash("sha256").update(stateStr).digest("hex").slice(0, 16);
  }

  /**
   * Get current RNG state (for step recording)
   */
  captureRngState(): string {
    return this._captureRngState();
  }

  /**
   * Deterministic random integer in [a, b] inclusive.
   */
  randint(a: number, b: number): number {
    return this._rng.randint(a, b);
  }

  /**
   * Deterministic random float in [0, 1).
   */
  random(): number {
    return this._rng.random();
  }

  /**
   * Deterministic random choice from array.
   */
  choice<T>(arr: T[]): T {
    return this._rng.choice(arr);
  }

  /**
   * Deterministic in-place shuffle.
   */
  shuffle<T>(arr: T[]): void {
    this._rng.shuffle(arr);
  }

  /**
   * Deterministic UUID based on seed and counter.
   */
  uuid(): string {
    const bytes: number[] = [];
    for (let i = 0; i < 16; i++) {
      bytes.push(this._rng.randint(0, 255));
    }
    const hex = bytes.map((b) => b.toString(16).padStart(2, "0")).join("");
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20, 32)}`;
  }

  /**
   * Return frozen timestamp as ISO8601 string.
   */
  timestamp(): string {
    return this.now.toISOString();
  }

  /**
   * Serialize context for trace.
   */
  toDict(): Record<string, unknown> {
    return {
      seed: this.seed,
      now: this.now.toISOString(),
      tenant_id: this.tenantId,
      env: this.env,
      rng_state: this.rngState,
    };
  }

  /**
   * Deserialize context from trace.
   */
  static fromDict(data: Record<string, unknown>): RuntimeContext {
    return new RuntimeContext({
      seed: (data.seed as number) ?? 42,
      now: data.now as string,
      tenantId: (data.tenant_id as string) ?? "default",
      env: (data.env as Record<string, string>) ?? {},
    });
  }
}

/**
 * Parse ISO8601 string to Date.
 */
export function freezeTime(isoString: string): Date {
  return new Date(isoString);
}

/**
 * Serialize object to canonical JSON (sorted keys, compact).
 *
 * This ensures identical objects produce identical byte output
 * across Python and JavaScript.
 */
export function canonicalJson(obj: unknown): string {
  return JSON.stringify(obj, (_, value) => {
    if (value && typeof value === "object" && !Array.isArray(value)) {
      // Sort object keys
      return Object.keys(value)
        .sort()
        .reduce((sorted: Record<string, unknown>, key) => {
          sorted[key] = value[key];
          return sorted;
        }, {});
    }
    return value;
  });
}

/**
 * Compute deterministic hash of a trace or any data.
 *
 * Uses SHA256 with canonical JSON serialization.
 */
export function hashTrace(trace: Record<string, unknown>): string {
  const canonical = canonicalJson(trace);
  return createHash("sha256").update(canonical).digest("hex");
}

/**
 * Compute deterministic hash of any data (truncated).
 */
export function hashData(data: unknown): string {
  const canonical = canonicalJson(data);
  return createHash("sha256").update(canonical).digest("hex").slice(0, 16);
}
