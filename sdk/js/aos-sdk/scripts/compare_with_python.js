#!/usr/bin/env node
/**
 * Cross-Language Parity Verification Script
 *
 * Compares a Python-generated trace with JS SDK to verify identical hashing.
 *
 * Usage:
 *   node compare_with_python.js /path/to/python.trace.json
 *
 * Exit codes:
 *   0 - Parity check passed
 *   1 - Parity check failed
 *   2 - Usage error
 */

import fs from "fs";
import crypto from "crypto";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Canonical JSON: sorted keys, compact format (matches Python implementation)
function canonicalJson(obj) {
  if (obj === null || obj === undefined) {
    return "null";
  }
  if (typeof obj !== "object") {
    return JSON.stringify(obj);
  }
  if (Array.isArray(obj)) {
    return "[" + obj.map(canonicalJson).join(",") + "]";
  }
  const keys = Object.keys(obj).sort();
  const pairs = keys.map((k) => JSON.stringify(k) + ":" + canonicalJson(obj[k]));
  return "{" + pairs.join(",") + "}";
}

// SHA256 hash of canonical JSON
function hashData(data) {
  const canonical = canonicalJson(data);
  return crypto.createHash("sha256").update(canonical, "utf8").digest("hex");
}

// Truncated hash (16 chars, matching Python hash_data)
function hashDataTruncated(data) {
  return hashData(data).substring(0, 16);
}

// Compute deterministic step hash (matching Python TraceStep.deterministic_hash)
function stepDeterministicHash(step) {
  const payload = {
    step_index: step.step_index ?? 0,
    skill_id: step.skill_id ?? step.skill_name ?? "unknown",
    input_hash: step.input_hash ?? null,
    output_hash: step.output_hash ?? null,
    rng_state_before: step.rng_state_before ?? step.rng_state ?? null,
    outcome: step.outcome ?? step.status ?? "success",
    idempotency_key: step.idempotency_key ?? null,
    replay_behavior: step.replay_behavior ?? "execute",
  };
  return hashData(payload);
}

// Compute trace root hash (matching Python Trace.finalize)
function computeRootHash(trace) {
  // Base hash from seed, timestamp, tenant
  const seed = trace.seed ?? 42;
  const timestamp = trace.frozen_timestamp ?? trace.timestamp ?? "";
  const tenantId = trace.tenant_id ?? "default";
  const baseString = `${seed}:${timestamp}:${tenantId}`;
  let currentHash = crypto
    .createHash("sha256")
    .update(baseString, "utf8")
    .digest("hex");

  // Chain step hashes
  const steps = trace.steps ?? [];
  for (const step of steps) {
    const stepHash = stepDeterministicHash(step);
    const combined = currentHash + stepHash;
    currentHash = crypto
      .createHash("sha256")
      .update(combined, "utf8")
      .digest("hex");
  }

  return currentHash;
}

// Main verification
function verifyParity(pythonTracePath) {
  console.log("Cross-Language Parity Verification");
  console.log("===================================");
  console.log(`Python trace: ${pythonTracePath}`);
  console.log("");

  // Read Python trace
  let trace;
  try {
    const raw = fs.readFileSync(pythonTracePath, "utf8");
    trace = JSON.parse(raw);
  } catch (err) {
    console.error(`Error reading trace: ${err.message}`);
    process.exit(2);
  }

  // Extract declared values
  const declaredRootHash = trace.root_hash;
  const declaredSeed = trace.seed ?? 42;
  const declaredTimestamp = trace.frozen_timestamp ?? trace.timestamp;
  const declaredSchemaVersion = trace.schema_version ?? trace.trace_version ?? "1.1";

  console.log("Trace metadata:");
  console.log(`  Schema version: ${declaredSchemaVersion}`);
  console.log(`  Seed: ${declaredSeed}`);
  console.log(`  Timestamp: ${declaredTimestamp}`);
  console.log(`  Declared root_hash: ${declaredRootHash || "MISSING"}`);
  console.log(`  Steps: ${(trace.steps ?? []).length}`);
  console.log("");

  // Compute root hash using JS implementation
  const computedRootHash = computeRootHash(trace);
  console.log(`Computed root_hash (JS): ${computedRootHash}`);
  console.log("");

  // Verify parity
  let parityOk = true;
  const failures = [];

  // 1. Root hash parity
  if (declaredRootHash) {
    if (declaredRootHash === computedRootHash) {
      console.log("[PASS] Root hash matches");
    } else {
      console.log("[FAIL] Root hash mismatch");
      console.log(`  Python: ${declaredRootHash}`);
      console.log(`  JS:     ${computedRootHash}`);
      failures.push("root_hash");
      parityOk = false;
    }
  } else {
    console.log("[WARN] No root_hash declared in trace");
  }

  // 2. Step hash verification
  const steps = trace.steps ?? [];
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const jsStepHash = stepDeterministicHash(step);

    // If Python computed step hashes are available
    const pyStepHash = step.deterministic_hash;
    if (pyStepHash) {
      if (pyStepHash === jsStepHash) {
        console.log(`[PASS] Step ${i} hash matches`);
      } else {
        console.log(`[FAIL] Step ${i} hash mismatch`);
        console.log(`  Python: ${pyStepHash}`);
        console.log(`  JS:     ${jsStepHash}`);
        failures.push(`step_${i}_hash`);
        parityOk = false;
      }
    }
  }

  // 3. Canonical JSON test
  const testObj = { b: 2, a: 1, c: { z: 26, y: 25 } };
  const jsCanonical = canonicalJson(testObj);
  const expectedCanonical = '{"a":1,"b":2,"c":{"y":25,"z":26}}';
  if (jsCanonical === expectedCanonical) {
    console.log("[PASS] Canonical JSON format matches");
  } else {
    console.log("[FAIL] Canonical JSON format mismatch");
    console.log(`  Expected: ${expectedCanonical}`);
    console.log(`  Got:      ${jsCanonical}`);
    failures.push("canonical_json");
    parityOk = false;
  }

  // 4. Hash truncation test
  const testHash = hashDataTruncated({ x: 1 });
  if (testHash.length === 16 && /^[0-9a-f]{16}$/.test(testHash)) {
    console.log("[PASS] Hash truncation (16 chars) correct");
  } else {
    console.log(`[FAIL] Hash truncation incorrect: ${testHash}`);
    failures.push("hash_truncation");
    parityOk = false;
  }

  console.log("");
  console.log("===================================");

  if (parityOk) {
    console.log("PARITY CHECK: PASSED");
    console.log("JS SDK produces identical hashes to Python.");
    process.exit(0);
  } else {
    console.log("PARITY CHECK: FAILED");
    console.log(`Failures: ${failures.join(", ")}`);
    process.exit(1);
  }
}

// CLI entry point
const args = process.argv.slice(2);

if (args.length === 0) {
  console.log("Usage: node compare_with_python.js <python-trace.json>");
  console.log("");
  console.log("Verifies that JS SDK produces identical hashes to Python.");
  process.exit(2);
}

const tracePath = args[0];
if (!fs.existsSync(tracePath)) {
  console.error(`Error: File not found: ${tracePath}`);
  process.exit(2);
}

verifyParity(tracePath);
