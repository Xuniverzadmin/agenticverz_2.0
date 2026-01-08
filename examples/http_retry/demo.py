#!/usr/bin/env python3
"""
HTTP Retry Demo

Demonstrates AOS failure handling and recovery:
1. Simulate a plan with a flaky HTTP endpoint
2. Execute and observe failure -> retry -> success
3. Show structured error outcomes from failure catalog
4. Save and verify traces for replay

This is a key machine-native capability: failures are data, not exceptions.

Requirements:
    pip install aos-sdk
    export AOS_API_KEY=your-api-key
    export AOS_BASE_URL=http://localhost:8000  # optional

Determinism Flags:
    --seed <int>         Set random seed (default: 42)
    --save-trace <path>  Save execution trace for replay
    --catalog            Show failure catalog demo
"""

import argparse
import json
import os
import sys
import time as time_module

from aos_sdk import (
    AOSClient,
    AOSError,
    RuntimeContext,
    Trace,
    hash_data,
    generate_idempotency_key,
)

# Flaky endpoint (httpbin returns different status codes)
# First URL fails, fallback URL succeeds
PRIMARY_URL = "https://httpbin.org/status/503"  # Always returns 503
FALLBACK_URL = "https://httpbin.org/status/200"  # Always returns 200


def create_retry_plan() -> list:
    """
    Create a plan that demonstrates retry and fallback.

    This plan:
    1. Tries the primary URL (which fails)
    2. Falls back to the secondary URL
    3. Transforms the result
    """
    return [
        {
            "skill": "http_call",
            "params": {
                "method": "GET",
                "url": PRIMARY_URL,
                "timeout_seconds": 5,
                "retry": {"max_attempts": 2, "backoff_seconds": 1},
            },
            "fallback": {
                "skill": "http_call",
                "params": {"method": "GET", "url": FALLBACK_URL, "timeout_seconds": 5},
            },
            "description": "Try primary URL, fall back on failure",
        },
        {
            "skill": "json_transform",
            "params": {
                "input_path": "$.steps[0].result",
                "query": "{status: .status_code, source: .url}",
            },
            "description": "Extract status and source URL",
        },
    ]


def create_simple_flaky_plan() -> list:
    """
    Simpler plan that just shows retry behavior.
    """
    return [
        {
            "skill": "http_call",
            "params": {
                "method": "GET",
                "url": "https://httpbin.org/delay/2",  # 2 second delay
                "timeout_seconds": 10,
            },
            "description": "Call endpoint with potential timeout",
        }
    ]


def simulate_with_risks(client: AOSClient, plan: list) -> dict:
    """
    Simulate and show risk annotations.

    The simulation phase identifies potential failures before execution.
    """
    print("\n=== SIMULATION (Risk Analysis) ===")

    try:
        result = client.simulate(plan, budget_cents=100)

        print(f"\nFeasibility: {result.get('feasible', 'unknown')}")
        print(f"Estimated Cost: {result.get('estimated_cost_cents', 0)} cents")

        # Show risks identified
        risks = result.get("risks", [])
        if risks:
            print(f"\nIdentified Risks ({len(risks)}):")
            for i, risk in enumerate(risks):
                print(f"  {i + 1}. {risk}")
        else:
            print("\nNo significant risks identified.")

        # Show step simulations
        if result.get("step_simulations"):
            print("\nStep Analysis:")
            for i, step in enumerate(result["step_simulations"]):
                skill = plan[i].get("skill", "unknown")
                desc = plan[i].get("description", "")
                feasible = step.get("feasible", "unknown")
                failure_modes = step.get("failure_modes", [])

                print(f"\n  Step {i + 1}: [{skill}] {desc}")
                print(f"    Feasible: {feasible}")
                if failure_modes:
                    print("    Potential Failures:")
                    for mode in failure_modes[:3]:  # Show top 3
                        print(f"      - {mode}")

        return result

    except AOSError as e:
        print(f"\nSimulation failed: {e}")
        raise


def execute_with_retry(client: AOSClient, plan: list) -> dict:
    """
    Execute the plan and observe retry/fallback behavior.
    """
    print("\n=== EXECUTION (With Retry) ===")

    try:
        run = client.create_run(
            agent_id="http-retry-demo",
            goal="Fetch data with retry and fallback",
            plan=plan,
        )

        run_id = run.get("run_id") or run.get("id")
        print(f"Run created: {run_id}")

        # Poll with progress indication
        print("Executing...", end="", flush=True)
        max_polls = 30
        for i in range(max_polls):
            result = client.get_run(run_id)
            status = result.get("status", "pending")

            if status in ("succeeded", "failed"):
                print(" done!")
                break

            print(".", end="", flush=True)
            time_module.sleep(1)
        else:
            print(" timeout!")

        # Show outcome
        print(f"\nFinal Status: {status}")

        outcome = result.get("outcome", {})
        if outcome:
            print("\nStructured Outcome:")
            print(f"  Success: {outcome.get('success', False)}")

            if outcome.get("error"):
                error = outcome["error"]
                print("\n  Error Details:")
                print(f"    Code: {error.get('code', 'unknown')}")
                print(f"    Message: {error.get('message', 'unknown')}")
                if error.get("catalog_match"):
                    print(f"    Catalog Match: {error['catalog_match']}")
                if error.get("recovery_suggestion"):
                    print(f"    Suggested Recovery: {error['recovery_suggestion']}")

            if outcome.get("result"):
                print(f"\n  Result: {json.dumps(outcome['result'], indent=4)}")

            if outcome.get("retries"):
                print(f"\n  Retry History ({len(outcome['retries'])} attempts):")
                for i, retry in enumerate(outcome["retries"]):
                    print(f"    Attempt {i + 1}: {retry.get('status', 'unknown')}")

        return result

    except AOSError as e:
        print(f"\nExecution failed: {e}")
        raise


def demonstrate_failure_catalog(client: AOSClient):
    """
    Demonstrate how failures are matched to the catalog.
    """
    print("\n=== FAILURE CATALOG DEMO ===")
    print("Intentionally triggering a failure to show catalog matching...")

    # Plan that will definitely fail
    fail_plan = [
        {
            "skill": "http_call",
            "params": {
                "method": "GET",
                "url": "https://httpbin.org/status/500",
                "timeout_seconds": 5,
            },
            "description": "Trigger 500 error",
        }
    ]

    try:
        run = client.create_run(
            agent_id="failure-demo", goal="Demonstrate failure catalog", plan=fail_plan
        )

        run_id = run.get("run_id") or run.get("id")
        time_module.sleep(2)  # Wait for execution
        result = client.get_run(run_id)

        outcome = result.get("outcome", {})
        if outcome.get("error"):
            error = outcome["error"]
            print("\nCaptured Failure:")
            print(f"  Error Code: {error.get('code', 'unknown')}")
            print(f"  Category: {error.get('category', 'unknown')}")

            if error.get("catalog_entry"):
                entry = error["catalog_entry"]
                print("\n  Catalog Match:")
                print(f"    Entry ID: {entry.get('id', 'unknown')}")
                print(f"    Pattern: {entry.get('pattern', 'unknown')}")
                print(f"    Suggested Recovery: {entry.get('recovery', 'unknown')}")
                print(f"    Confidence: {entry.get('confidence', 0):.0%}")

        print("\n[INFO] Failures are data, not exceptions!")
        print("       The error is structured, cataloged, and actionable.")

    except AOSError as e:
        print(f"Failure demo error: {e}")


def main():
    """Main demo flow: Simulate -> Execute -> Report with deterministic tracing."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="AOS HTTP Retry Demo")
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed (default: 42)"
    )
    parser.add_argument("--save-trace", type=str, help="Save trace to file")
    parser.add_argument("--timestamp", type=str, help="Frozen timestamp (ISO8601)")
    parser.add_argument(
        "--catalog", action="store_true", help="Show failure catalog demo"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("AOS Demo: HTTP Retry & Failure Handling")
    print("=" * 60)

    # Create deterministic context
    ctx = RuntimeContext(seed=args.seed, now=args.timestamp if args.timestamp else None)

    print("\nDeterminism Context:")
    print(f"  Seed: {ctx.seed}")
    print(f"  Timestamp: {ctx.timestamp()}")
    print(f"  RNG State: {ctx.rng_state}")

    # Configuration
    api_key = os.getenv("AOS_API_KEY")
    base_url = os.getenv("AOS_BASE_URL", "http://127.0.0.1:8000")

    if not api_key:
        print("\nWarning: AOS_API_KEY not set. Using demo mode.")

    print("\nConfiguration:")
    print(f"  API URL: {base_url}")
    print(f"  Primary URL: {PRIMARY_URL}")
    print(f"  Fallback URL: {FALLBACK_URL}")

    # Create client
    client = AOSClient(api_key=api_key, base_url=base_url)

    # Create plan
    plan = create_retry_plan()
    print(f"\nPlan has {len(plan)} steps with retry/fallback:")
    for i, step in enumerate(plan):
        print(f"  {i + 1}. {step.get('description', step['skill'])}")
        if step.get("fallback"):
            print(f"      Fallback: {step['fallback'].get('skill', 'unknown')}")
    print(f"  Plan hash: {hash_data(plan)}")

    # Create trace for recording
    trace = Trace(
        seed=ctx.seed,
        timestamp=ctx.timestamp(),
        plan=plan,
        metadata={"demo": "http_retry"},
    )

    # Phase 1: Simulate with risk analysis
    sim_result = None
    try:
        start = time_module.time()
        sim_result = simulate_with_risks(client, plan)
        duration = int((time_module.time() - start) * 1000)

        trace.add_step(
            skill_id="simulate",
            input_data=plan,
            output_data=sim_result,
            rng_state=ctx.rng_state,
            duration_ms=duration,
            outcome="success" if sim_result.get("feasible", False) else "failure",
        )

        if not sim_result.get("feasible", False):
            print("\n[WARNING] Plan has feasibility risks, proceeding anyway...")

    except AOSError as e:
        print("\n[WARNING] Simulation failed, proceeding with execution...")
        trace.add_step(
            skill_id="simulate",
            input_data=plan,
            output_data={"error": str(e)},
            rng_state=ctx.rng_state,
            duration_ms=0,
            outcome="failure",
        )

    # Phase 2: Execute with retry observation
    exec_result = None
    try:
        start = time_module.time()
        exec_result = execute_with_retry(client, plan)
        duration = int((time_module.time() - start) * 1000)

        status = exec_result.get("status", "unknown")
        # Generate idempotency key for HTTP call execution
        run_id = exec_result.get("run_id") or exec_result.get("id", "unknown")
        idem_key = generate_idempotency_key(
            run_id, 1, "execute", hash_data({"plan": plan})
        )

        trace.add_step(
            skill_id="execute",
            input_data={"plan": plan},
            output_data=exec_result,
            rng_state=ctx._capture_rng_state(),
            duration_ms=duration,
            outcome="success" if status == "succeeded" else "failure",
            idempotency_key=idem_key,
            replay_behavior="check",  # Verify output matches on replay
        )

        if status == "succeeded":
            print("\n[SUCCESS] Request completed (with retry/fallback)")
        else:
            print(f"\n[RESULT] Final status: {status}")

    except AOSError as e:
        print(f"\n[FAILURE] Execution error: {e}")
        trace.add_step(
            skill_id="execute",
            input_data={"plan": plan},
            output_data={"error": str(e)},
            rng_state=ctx._capture_rng_state(),
            duration_ms=0,
            outcome="failure",
        )

    # Optional: Failure catalog demo
    if args.catalog or os.getenv("SHOW_CATALOG", "false").lower() == "true":
        demonstrate_failure_catalog(client)

    # Finalize and save trace
    trace.finalize()
    print(f"\n[TRACE] Root hash: {trace.root_hash}")

    if args.save_trace:
        trace.save(args.save_trace)
        print(f"[TRACE] Saved to {args.save_trace}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("Key takeaway: Failures are structured data, not exceptions.")
    print(f"Trace hash: {trace.root_hash}")
    print("=" * 60)

    # Exit with appropriate code
    final_status = exec_result.get("status", "unknown") if exec_result else "failed"
    sys.exit(0 if final_status == "succeeded" else 1)


if __name__ == "__main__":
    main()
