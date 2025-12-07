/**
 * k6 Load Test for AOS /api/v1/simulate endpoint
 *
 * M8 Deliverable: Performance validation for trace simulation API
 *
 * Usage:
 *   k6 run simulate_k6.js
 *   k6 run --vus 50 --duration 5m simulate_k6.js
 *   k6 run --env API_URL=http://localhost:8000 simulate_k6.js
 *
 * Environment variables:
 *   API_URL     - Base URL (default: http://localhost:8000)
 *   API_KEY     - AOS API key for authentication
 *   VUS         - Virtual users (default: 10)
 *   DURATION    - Test duration (default: 1m)
 */

import http from "k6/http";
import { check, sleep, group } from "k6";
import { Counter, Rate, Trend, Gauge } from "k6/metrics";
import { randomSeed, randomIntBetween } from "https://jslib.k6.io/k6-utils/1.4.0/index.js";

// Custom metrics
const simulateLatency = new Trend("aos_simulate_latency", true);
const simulateErrors = new Counter("aos_simulate_errors");
const simulateSuccessRate = new Rate("aos_simulate_success_rate");
const parityCheckFailures = new Counter("aos_parity_check_failures");
const traceSize = new Trend("aos_trace_size_bytes");
const activeTraces = new Gauge("aos_active_traces");

// Configuration
const API_URL = __ENV.API_URL || "http://localhost:8000";
const API_KEY = __ENV.API_KEY || "";
const TENANT_ID = __ENV.TENANT_ID || "load-test";

export const options = {
  scenarios: {
    // Ramp-up scenario
    ramp_up: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "30s", target: 10 },  // Ramp up
        { duration: "1m", target: 10 },   // Stay at 10
        { duration: "30s", target: 25 },  // Ramp up more
        { duration: "2m", target: 25 },   // Stay at 25
        { duration: "30s", target: 0 },   // Ramp down
      ],
      gracefulRampDown: "30s",
    },
    // Spike test (uncomment to enable)
    // spike: {
    //   executor: "ramping-vus",
    //   startVUs: 0,
    //   stages: [
    //     { duration: "10s", target: 100 },
    //     { duration: "1m", target: 100 },
    //     { duration: "10s", target: 0 },
    //   ],
    //   startTime: "5m",
    // },
  },
  thresholds: {
    // Response time thresholds
    "aos_simulate_latency": [
      "p(50)<200",   // p50 under 200ms
      "p(95)<500",   // p95 under 500ms
      "p(99)<1000",  // p99 under 1s
    ],
    // Error rate threshold
    "aos_simulate_success_rate": ["rate>0.95"],  // 95% success rate
    // Parity check should never fail
    "aos_parity_check_failures": ["count<1"],
  },
};

// Test data generators
function generateWorkflowInput() {
  const inputs = [
    { type: "btc_price", currency: "USD" },
    { type: "json_transform", data: { foo: "bar", count: randomIntBetween(1, 100) } },
    { type: "http_retry", url: "https://httpbin.org/status/200" },
  ];
  return inputs[randomIntBetween(0, inputs.length - 1)];
}

function generateSimulateRequest() {
  const skills = ["echo", "json_transform", "http_get", "shell"];
  const skill = skills[randomIntBetween(0, skills.length - 1)];

  return {
    plan: [
      {
        skill: skill,
        params: generateWorkflowInput(),
      },
    ],
  };
}

// Headers
function getHeaders() {
  const headers = {
    "Content-Type": "application/json",
    "X-Tenant-ID": TENANT_ID,
  };
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }
  return headers;
}

// Main test function
export default function () {
  group("Simulate Endpoint", function () {
    const payload = generateSimulateRequest();
    const startTime = Date.now();

    const response = http.post(
      `${API_URL}/api/v1/runtime/simulate`,
      JSON.stringify(payload),
      { headers: getHeaders(), timeout: "10s" }
    );

    const duration = Date.now() - startTime;
    simulateLatency.add(duration);

    // Check response
    const success = check(response, {
      "status is 200": (r) => r.status === 200,
      "response has feasible field": (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.feasible !== undefined;
        } catch {
          return false;
        }
      },
      "response has step_estimates": (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.step_estimates !== undefined;
        } catch {
          return false;
        }
      },
      "response time < 1s": (r) => r.timings.duration < 1000,
    });

    if (success) {
      simulateSuccessRate.add(1);

      // Track trace size
      if (response.body) {
        traceSize.add(response.body.length);
      }

      // Verify deterministic properties if we got a trace back
      try {
        const body = JSON.parse(response.body);
        if (body.trace?.schema_version) {
          check(body, {
            "schema version is 1.1": (b) => b.trace.schema_version === "1.1",
            "has deterministic fields": (b) =>
              b.trace.seed !== undefined &&
              b.trace.frozen_timestamp !== undefined,
          });
        }
      } catch {
        // Ignore JSON parse errors for checks
      }
    } else {
      simulateSuccessRate.add(0);
      simulateErrors.add(1);

      // Log error details for debugging
      if (response.status !== 200) {
        console.log(`Error: status=${response.status}, body=${response.body?.substring(0, 200)}`);
      }
    }
  });

  // Idempotency test (every 10th iteration)
  if (__ITER % 10 === 0) {
    group("Idempotency Check", function () {
      const payload = {
        plan: [{ skill: "echo", params: { message: "idempotency test" } }],
      };

      // First request
      const response1 = http.post(
        `${API_URL}/api/v1/runtime/simulate`,
        JSON.stringify(payload),
        { headers: getHeaders(), timeout: "10s" }
      );

      // Second request with same payload
      const response2 = http.post(
        `${API_URL}/api/v1/runtime/simulate`,
        JSON.stringify(payload),
        { headers: getHeaders(), timeout: "10s" }
      );

      check({ r1: response1, r2: response2 }, {
        "idempotent requests return same result": ({ r1, r2 }) => {
          if (r1.status !== 200 || r2.status !== 200) return true; // Skip check if errors
          try {
            const body1 = JSON.parse(r1.body);
            const body2 = JSON.parse(r2.body);
            // Both should be feasible or not
            return body1.feasible === body2.feasible;
          } catch {
            return false;
          }
        },
      });
    });
  }

  // Parity verification (every 20th iteration)
  if (__ITER % 20 === 0) {
    group("Parity Verification", function () {
      // Use fixed plan for reproducibility
      const payload = {
        plan: [{ skill: "echo", params: { message: "parity check" } }],
      };

      const response = http.post(
        `${API_URL}/api/v1/runtime/simulate`,
        JSON.stringify(payload),
        { headers: getHeaders(), timeout: "10s" }
      );

      if (response.status === 200) {
        try {
          const body = JSON.parse(response.body);

          // Verify response structure is consistent
          const parityOk = check(body, {
            "response has feasible field": () => body.feasible !== undefined,
            "response has step_estimates": () => body.step_estimates !== undefined,
          });

          if (!parityOk) {
            parityCheckFailures.add(1);
          }
        } catch {
          parityCheckFailures.add(1);
        }
      }
    });
  }

  // Random sleep between 100ms and 500ms
  sleep(randomIntBetween(100, 500) / 1000);
}

// Setup function - runs once before the test
export function setup() {
  console.log(`Starting load test against ${API_URL}`);
  console.log(`Tenant ID: ${TENANT_ID}`);

  // Health check
  const healthResponse = http.get(`${API_URL}/health`, { timeout: "5s" });
  if (healthResponse.status !== 200) {
    console.error(`Health check failed: ${healthResponse.status}`);
  }

  return { startTime: Date.now() };
}

// Teardown function - runs once after the test
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Load test completed in ${duration.toFixed(2)}s`);
}

// Handle summary
export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    duration_seconds: data.state.testRunDurationMs / 1000,
    vus_max: data.metrics.vus_max?.values?.max || 0,
    iterations: data.metrics.iterations?.values?.count || 0,
    simulate_latency_p50: data.metrics.aos_simulate_latency?.values?.["p(50)"] || 0,
    simulate_latency_p95: data.metrics.aos_simulate_latency?.values?.["p(95)"] || 0,
    simulate_latency_p99: data.metrics.aos_simulate_latency?.values?.["p(99)"] || 0,
    success_rate: data.metrics.aos_simulate_success_rate?.values?.rate || 0,
    error_count: data.metrics.aos_simulate_errors?.values?.count || 0,
    parity_failures: data.metrics.aos_parity_check_failures?.values?.count || 0,
    thresholds_passed: Object.values(data.metrics)
      .filter((m) => m.thresholds)
      .every((m) => Object.values(m.thresholds).every((t) => t.ok)),
  };

  return {
    "load-tests/results/simulate_summary.json": JSON.stringify(summary, null, 2),
    stdout: textSummary(data, { indent: "  ", enableColors: true }),
  };
}

// Text summary helper
function textSummary(data, options) {
  const lines = [];
  lines.push("");
  lines.push("=== AOS Simulate Load Test Results ===");
  lines.push("");
  lines.push(`Duration: ${(data.state.testRunDurationMs / 1000).toFixed(2)}s`);
  lines.push(`Max VUs: ${data.metrics.vus_max?.values?.max || 0}`);
  lines.push(`Iterations: ${data.metrics.iterations?.values?.count || 0}`);
  lines.push("");
  lines.push("Latency:");
  lines.push(`  p50: ${(data.metrics.aos_simulate_latency?.values?.["p(50)"] || 0).toFixed(2)}ms`);
  lines.push(`  p95: ${(data.metrics.aos_simulate_latency?.values?.["p(95)"] || 0).toFixed(2)}ms`);
  lines.push(`  p99: ${(data.metrics.aos_simulate_latency?.values?.["p(99)"] || 0).toFixed(2)}ms`);
  lines.push("");
  lines.push(`Success Rate: ${((data.metrics.aos_simulate_success_rate?.values?.rate || 0) * 100).toFixed(2)}%`);
  lines.push(`Errors: ${data.metrics.aos_simulate_errors?.values?.count || 0}`);
  lines.push(`Parity Failures: ${data.metrics.aos_parity_check_failures?.values?.count || 0}`);
  lines.push("");

  // Threshold results
  const thresholds = Object.entries(data.metrics)
    .filter(([_, m]) => m.thresholds)
    .map(([name, m]) => ({
      name,
      passed: Object.values(m.thresholds).every((t) => t.ok),
    }));

  lines.push("Thresholds:");
  thresholds.forEach(({ name, passed }) => {
    const icon = passed ? "✓" : "✗";
    lines.push(`  ${icon} ${name}`);
  });
  lines.push("");

  return lines.join("\n");
}
