#!/usr/bin/env python3
"""
BTC Price to Slack Demo

Demonstrates the AOS machine-native workflow:
1. Simulate the plan (check feasibility before execution)
2. Execute with budget constraints
3. Handle failures gracefully with structured outcomes
4. Save and verify traces for replay

Requirements:
    pip install aos-sdk
    export AOS_API_KEY=your-api-key
    export AOS_BASE_URL=http://localhost:8000  # optional
    export SLACK_WEBHOOK_URL=https://hooks.slack.com/...  # for real execution

Determinism Flags:
    --seed <int>         Set random seed (default: 42)
    --save-trace <path>  Save execution trace for replay
"""

import argparse
import json
import os
import sys
import time

from aos_sdk import AOSClient, AOSError, RuntimeContext, Trace, hash_data, generate_idempotency_key

# Configuration
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/TEST")
BTC_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"


def create_plan(slack_webhook: str) -> list:
    """Create the execution plan for BTC -> Slack notification."""
    return [
        {
            "skill": "http_call",
            "params": {
                "method": "GET",
                "url": BTC_API_URL,
                "timeout_seconds": 10
            },
            "description": "Fetch current BTC price from CoinGecko"
        },
        {
            "skill": "json_transform",
            "params": {
                "query": ".bitcoin.usd",
                "input_path": "$.steps[0].result.body"
            },
            "description": "Extract USD price from response"
        },
        {
            "skill": "http_call",
            "params": {
                "method": "POST",
                "url": slack_webhook,
                "headers": {"Content-Type": "application/json"},
                "body": {"text": "Current BTC price: ${{steps[1].result}}"}
            },
            "description": "Send price to Slack webhook"
        }
    ]


def simulate_plan(client: AOSClient, plan: list, budget_cents: int = 100) -> dict:
    """
    Simulate the plan before execution.

    This is a key machine-native capability: check if a plan is feasible
    given current constraints (budget, rate limits, permissions) before
    committing any resources.
    """
    print("\n=== SIMULATION PHASE ===")
    print(f"Budget: {budget_cents} cents")
    print(f"Steps: {len(plan)}")

    try:
        result = client.simulate(plan, budget_cents=budget_cents)

        print(f"\nSimulation Result:")
        print(f"  Feasible: {result.get('feasible', 'unknown')}")
        print(f"  Estimated Cost: {result.get('estimated_cost_cents', 0)} cents")

        if result.get('risks'):
            print(f"  Risks:")
            for risk in result['risks']:
                print(f"    - {risk}")

        if result.get('step_simulations'):
            print(f"\n  Step Breakdown:")
            for i, step in enumerate(result['step_simulations']):
                status = step.get('feasible', 'unknown')
                cost = step.get('estimated_cost_cents', 0)
                print(f"    Step {i+1}: feasible={status}, cost={cost}c")

        return result

    except AOSError as e:
        print(f"\nSimulation failed: {e}")
        if e.response:
            print(f"  Details: {json.dumps(e.response, indent=2)}")
        raise


def execute_plan(client: AOSClient, plan: list, budget_cents: int = 100) -> dict:
    """
    Execute the plan after successful simulation.

    Returns a StructuredOutcome with deterministic fields for replay.
    """
    print("\n=== EXECUTION PHASE ===")

    try:
        # Create a run with the plan
        run = client.create_run(
            agent_id="btc-notifier",
            goal="Fetch BTC price and notify Slack",
            plan=plan
        )

        run_id = run.get('run_id') or run.get('id')
        print(f"Run created: {run_id}")

        # Poll for completion
        print("Waiting for execution...")
        result = client.get_run(run_id)

        status = result.get('status', 'unknown')
        print(f"\nExecution Result:")
        print(f"  Status: {status}")

        if result.get('outcome'):
            outcome = result['outcome']
            print(f"  Success: {outcome.get('success', False)}")
            if outcome.get('error'):
                print(f"  Error: {outcome['error']}")
            if outcome.get('result'):
                print(f"  Result: {outcome['result']}")

        return result

    except AOSError as e:
        print(f"\nExecution failed: {e}")
        if e.response:
            print(f"  Details: {json.dumps(e.response, indent=2)}")
        raise


def main():
    """Main demo flow: Simulate -> Execute -> Report"""
    # Parse arguments
    parser = argparse.ArgumentParser(description="AOS BTC Price to Slack Demo")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--save-trace", type=str, help="Save trace to file")
    parser.add_argument("--timestamp", type=str, help="Frozen timestamp (ISO8601)")
    args = parser.parse_args()

    print("=" * 60)
    print("AOS Demo: BTC Price -> Slack Notification")
    print("=" * 60)

    # Create deterministic context
    ctx = RuntimeContext(
        seed=args.seed,
        now=args.timestamp if args.timestamp else None
    )

    print(f"\nDeterminism Context:")
    print(f"  Seed: {ctx.seed}")
    print(f"  Timestamp: {ctx.timestamp()}")
    print(f"  RNG State: {ctx.rng_state}")

    # Check environment
    api_key = os.getenv("AOS_API_KEY")
    base_url = os.getenv("AOS_BASE_URL", "http://127.0.0.1:8000")

    if not api_key:
        print("\nWarning: AOS_API_KEY not set. Using demo mode.")
        print("Set AOS_API_KEY for real execution.")

    print(f"\nConfiguration:")
    print(f"  API URL: {base_url}")
    print(f"  BTC API: {BTC_API_URL}")
    print(f"  Slack: {SLACK_WEBHOOK[:50]}...")

    # Create client
    client = AOSClient(api_key=api_key, base_url=base_url)

    # Create plan
    plan = create_plan(SLACK_WEBHOOK)
    print(f"\nPlan created with {len(plan)} steps:")
    for i, step in enumerate(plan):
        print(f"  {i+1}. [{step['skill']}] {step.get('description', '')}")
    print(f"  Plan hash: {hash_data(plan)}")

    # Create trace for recording
    trace = Trace(
        seed=ctx.seed,
        timestamp=ctx.timestamp(),
        plan=plan,
        metadata={"demo": "btc_price_slack"}
    )

    # Phase 1: Simulate
    try:
        start = time.time()
        sim_result = simulate_plan(client, plan, budget_cents=100)
        duration = int((time.time() - start) * 1000)

        trace.add_step(
            skill_id="simulate",
            input_data=plan,
            output_data=sim_result,
            rng_state=ctx.rng_state,
            duration_ms=duration,
            outcome="success" if sim_result.get('feasible', False) else "failure"
        )

        if not sim_result.get('feasible', False):
            print("\n[ABORT] Plan is not feasible. Exiting without execution.")
            trace.finalize()
            if args.save_trace:
                trace.save(args.save_trace)
                print(f"[TRACE] Saved to {args.save_trace}")
            sys.exit(1)

    except AOSError:
        print("\n[ABORT] Simulation failed. Exiting.")
        sys.exit(1)

    # Phase 2: Execute (only if simulation passed)
    try:
        start = time.time()
        exec_result = execute_plan(client, plan, budget_cents=100)
        duration = int((time.time() - start) * 1000)

        # Generate idempotency key for non-idempotent operation (Slack POST)
        run_id = exec_result.get('run_id') or exec_result.get('id', 'unknown')
        idem_key = generate_idempotency_key(run_id, 1, "execute", hash_data({"plan": plan}))

        trace.add_step(
            skill_id="execute",
            input_data={"plan": plan},
            output_data=exec_result,
            rng_state=ctx._capture_rng_state(),
            duration_ms=duration,
            outcome="success" if exec_result.get('status') == 'succeeded' else "failure",
            idempotency_key=idem_key,
            replay_behavior="skip"  # Skip re-execution on replay (already sent to Slack)
        )

        # Finalize and save trace
        trace.finalize()
        print(f"\n[TRACE] Root hash: {trace.root_hash}")

        if args.save_trace:
            trace.save(args.save_trace)
            print(f"[TRACE] Saved to {args.save_trace}")

        if exec_result.get('status') == 'succeeded':
            print("\n[SUCCESS] BTC price sent to Slack!")
            print(f"  Trace hash: {trace.root_hash}")
            sys.exit(0)
        else:
            print("\n[FAILURE] Execution did not succeed.")
            sys.exit(1)

    except AOSError:
        print("\n[FAILURE] Execution failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
