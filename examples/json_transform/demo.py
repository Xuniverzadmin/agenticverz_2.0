#!/usr/bin/env python3
"""
JSON Transform Demo

Demonstrates pure deterministic transformation with AOS:
1. Define a transform plan
2. Simulate to verify feasibility
3. Execute with deterministic replay guarantees
4. Save and verify traces for replay

This demo is fully deterministic - same input always produces same output.

Requirements:
    pip install aos-sdk
    export AOS_API_KEY=your-api-key
    export AOS_BASE_URL=http://localhost:8000  # optional

Determinism Features:
    --seed <int>             Set random seed (default: 42)
    --save-trace <path>      Save execution trace for replay
    --check-determinism      Run determinism verification
"""

import argparse
import json
import os
import sys
import time

from aos_sdk import AOSClient, AOSError, RuntimeContext, Trace, hash_data

# Sample input data (deterministic)
SAMPLE_DATA = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "active": True},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "active": False},
        {"id": 3, "name": "Charlie", "email": "charlie@example.com", "active": True},
    ],
    "metadata": {"total": 3, "generated_at": "2025-01-01T00:00:00Z"},
}


def create_transform_plan(data: dict) -> list:
    """Create a plan that transforms JSON data."""
    return [
        {
            "skill": "json_transform",
            "params": {
                "input": data,
                "query": ".users[] | select(.active == true) | {name, email}",
            },
            "description": "Filter active users and extract name/email",
        },
        {
            "skill": "json_transform",
            "params": {
                "input_path": "$.steps[0].result",
                "query": "[.[] | {contact: .email, label: .name}]",
            },
            "description": "Reshape into contact list format",
        },
    ]


def simulate_transform(client: AOSClient, plan: list) -> dict:
    """
    Simulate the transform before execution.

    For deterministic transforms, simulation is fast and exact.
    """
    print("\n=== SIMULATION ===")
    print(f"Plan has {len(plan)} transform steps")

    try:
        result = client.simulate(plan, budget_cents=50)

        print("\nSimulation Result:")
        print(f"  Feasible: {result.get('feasible', 'unknown')}")
        print(f"  Estimated Cost: {result.get('estimated_cost_cents', 0)} cents")
        print("  Deterministic: Yes (json_transform is pure)")

        if result.get("step_simulations"):
            print("\nStep Details:")
            for i, step in enumerate(result["step_simulations"]):
                skill = plan[i].get("skill", "unknown")
                desc = plan[i].get("description", "")
                print(f"  {i+1}. [{skill}] {desc}")
                print(f"      Feasible: {step.get('feasible', 'unknown')}")

        return result

    except AOSError as e:
        print(f"\nSimulation failed: {e}")
        raise


def execute_transform(client: AOSClient, plan: list) -> dict:
    """
    Execute the transform.

    Returns structured outcome with deterministic result.
    """
    print("\n=== EXECUTION ===")

    try:
        # Create run
        run = client.create_run(
            agent_id="json-transformer",
            goal="Transform user data to contact list",
            plan=plan,
        )

        run_id = run.get("run_id") or run.get("id")
        print(f"Run created: {run_id}")

        # Get result
        result = client.get_run(run_id)

        status = result.get("status", "unknown")
        print(f"\nExecution Status: {status}")

        if result.get("outcome", {}).get("result"):
            print("\nTransformed Output:")
            output = result["outcome"]["result"]
            print(json.dumps(output, indent=2))

        return result

    except AOSError as e:
        print(f"\nExecution failed: {e}")
        raise


def demonstrate_determinism(client: AOSClient, plan: list):
    """
    Demonstrate that transforms are deterministic.

    Run the same plan twice and verify identical output.
    """
    print("\n=== DETERMINISM CHECK ===")
    print("Running same transform twice to verify determinism...")

    try:
        # First run
        run1 = client.create_run(
            agent_id="json-transformer", goal="Transform user data (run 1)", plan=plan
        )
        result1 = client.get_run(run1.get("run_id") or run1.get("id"))

        # Second run
        run2 = client.create_run(
            agent_id="json-transformer", goal="Transform user data (run 2)", plan=plan
        )
        result2 = client.get_run(run2.get("run_id") or run2.get("id"))

        # Compare
        output1 = result1.get("outcome", {}).get("result")
        output2 = result2.get("outcome", {}).get("result")

        if json.dumps(output1, sort_keys=True) == json.dumps(output2, sort_keys=True):
            print("\n[PASS] Outputs are identical - transform is deterministic!")
            return True
        else:
            print("\n[FAIL] Outputs differ - unexpected non-determinism!")
            print(f"  Run 1: {output1}")
            print(f"  Run 2: {output2}")
            return False

    except AOSError as e:
        print(f"\nDeterminism check failed: {e}")
        return False


def main():
    """Main demo flow with determinism support."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="AOS JSON Transform Demo")
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed (default: 42)"
    )
    parser.add_argument("--save-trace", type=str, help="Save trace to file")
    parser.add_argument(
        "--check-determinism", action="store_true", help="Verify determinism"
    )
    parser.add_argument("--timestamp", type=str, help="Frozen timestamp (ISO8601)")
    args = parser.parse_args()

    print("=" * 60)
    print("AOS Demo: JSON Transform (Deterministic)")
    print("=" * 60)

    # Create runtime context with deterministic seed
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

    # Show input data
    print("\nInput Data:")
    print(json.dumps(SAMPLE_DATA, indent=2))
    print(f"  Input hash: {hash_data(SAMPLE_DATA)}")

    # Create client and plan
    client = AOSClient(api_key=api_key, base_url=base_url)
    plan = create_transform_plan(SAMPLE_DATA)

    print("\nTransform Plan:")
    for i, step in enumerate(plan):
        print(f"  {i+1}. {step.get('description', step['skill'])}")
    print(f"  Plan hash: {hash_data(plan)}")

    # Create trace for recording
    trace = Trace(
        seed=ctx.seed,
        timestamp=ctx.timestamp(),
        plan=plan,
        metadata={"demo": "json_transform", "input_hash": hash_data(SAMPLE_DATA)},
    )

    # Simulate
    try:
        start = time.time()
        sim_result = simulate_transform(client, plan)
        duration = int((time.time() - start) * 1000)

        trace.add_step(
            skill_id="simulate",
            input_data=plan,
            output_data=sim_result,
            rng_state=ctx.rng_state,
            duration_ms=duration,
            outcome="success" if sim_result.get("feasible", False) else "failure",
        )

        if not sim_result.get("feasible", False):
            print("\n[ABORT] Transform not feasible.")
            trace.finalize()
            if args.save_trace:
                trace.save(args.save_trace)
                print(f"[TRACE] Saved to {args.save_trace}")
            sys.exit(1)

    except AOSError:
        print("\n[ABORT] Simulation failed.")
        sys.exit(1)

    # Execute
    try:
        start = time.time()
        exec_result = execute_transform(client, plan)
        duration = int((time.time() - start) * 1000)

        # Note: json_transform is a pure function - no idempotency_key needed
        # It can safely be re-executed on replay (replay_behavior="execute")
        trace.add_step(
            skill_id="execute",
            input_data={"plan": plan},
            output_data=exec_result,
            rng_state=ctx._capture_rng_state(),
            duration_ms=duration,
            outcome="success"
            if exec_result.get("status") == "succeeded"
            else "failure",
            replay_behavior="execute",  # Pure transform - safe to re-execute
        )

        if exec_result.get("status") != "succeeded":
            print("\n[FAILURE] Transform did not succeed.")
            trace.finalize()
            if args.save_trace:
                trace.save(args.save_trace)
                print(f"[TRACE] Saved to {args.save_trace}")
            sys.exit(1)

    except AOSError:
        print("\n[FAILURE] Execution failed.")
        sys.exit(1)

    # Finalize and save trace
    trace.finalize()
    print(f"\n[TRACE] Root hash: {trace.root_hash}")

    if args.save_trace:
        trace.save(args.save_trace)
        print(f"[TRACE] Saved to {args.save_trace}")

    # Determinism check
    if args.check_determinism:
        if not demonstrate_determinism(client, plan):
            sys.exit(1)

    print("\n" + "=" * 60)
    print("[SUCCESS] JSON transform completed!")
    print(f"  Trace hash: {trace.root_hash}")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
