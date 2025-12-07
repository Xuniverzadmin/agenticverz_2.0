"""
AOS CLI - Command-line interface for the AOS SDK.

Usage:
    aos version              Show version
    aos health               Check server health
    aos capabilities         Show runtime capabilities
    aos skills               List available skills
    aos skill <id>           Describe a skill
    aos simulate <json>      Simulate a plan (with determinism flags)
    aos replay <trace>       Replay a saved trace
    aos diff <t1> <t2>       Compare two traces

Determinism Flags (for simulate):
    --seed <int>             Set random seed (default: 42)
    --save-trace <path>      Save execution trace to file
    --load-trace <path>      Load trace for replay verification
    --dry-run                Simulate without execution
"""

import argparse
import json
import sys
import os
import time

from . import __version__
from .client import AOSClient, AOSError
from .runtime import RuntimeContext, canonical_json
from .trace import Trace, TraceStep, diff_traces, hash_data, create_trace_from_context


def get_client() -> AOSClient:
    """Create a client from environment variables."""
    return AOSClient(
        api_key=os.getenv("AOS_API_KEY"),
        base_url=os.getenv("AOS_BASE_URL", "http://127.0.0.1:8000")
    )


def cmd_version(args):
    """Print version."""
    print(f"aos-sdk {__version__}")


def cmd_health(args):
    """Check server health."""
    client = get_client()
    try:
        resp = client._request("GET", "/health")
        print(json.dumps(resp, indent=2))
    except AOSError as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_capabilities(args):
    """Show runtime capabilities."""
    client = get_client()
    try:
        caps = client.get_capabilities()
        print(json.dumps(caps, indent=2))
    except AOSError as e:
        print(f"Failed to get capabilities: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_skills(args):
    """List available skills."""
    client = get_client()
    try:
        skills = client.list_skills()
        print(json.dumps(skills, indent=2))
    except AOSError as e:
        print(f"Failed to list skills: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_skill(args):
    """Describe a skill."""
    client = get_client()
    try:
        skill = client.describe_skill(args.skill_id)
        print(json.dumps(skill, indent=2))
    except AOSError as e:
        print(f"Failed to describe skill: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_simulate(args):
    """Simulate a plan with determinism support."""
    client = get_client()
    try:
        plan = json.loads(args.plan_json)

        # Create runtime context with seed
        ctx = RuntimeContext(
            seed=args.seed,
            now=args.timestamp if args.timestamp else None
        )

        # Create trace if saving
        trace = None
        if args.save_trace or args.load_trace:
            trace = create_trace_from_context(ctx, plan)

        # Dry run mode - only simulate, don't execute
        if args.dry_run:
            print(f"[DRY RUN] Seed: {ctx.seed}, Time: {ctx.timestamp()}")
            print(f"[DRY RUN] Plan hash: {hash_data(plan)}")
            print(f"[DRY RUN] Would simulate {len(plan)} skills")
            for i, step in enumerate(plan):
                skill_id = step.get("skill_id", step.get("skill", "unknown"))
                print(f"  Step {i}: {skill_id}")
            return

        # Run simulation
        start_time = time.time()
        result = client.simulate(
            plan=plan,
            budget_cents=args.budget,
            seed=args.seed  # Pass seed to backend
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Record trace step if tracing
        if trace:
            trace.add_step(
                skill_id="simulate",
                input_data={"plan": plan, "budget": args.budget},
                output_data=result,
                rng_state=ctx.rng_state,
                duration_ms=duration_ms,
                outcome="success" if result.get("feasible", False) else "failure"
            )
            trace.finalize()

        # Save trace if requested
        if args.save_trace:
            trace.save(args.save_trace)
            print(f"[TRACE] Saved to {args.save_trace}", file=sys.stderr)
            print(f"[TRACE] Root hash: {trace.root_hash}", file=sys.stderr)

        # Verify against loaded trace if requested
        if args.load_trace:
            expected = Trace.load(args.load_trace)
            diff_result = diff_traces(expected, trace)
            if diff_result["match"]:
                print("[REPLAY] Traces match", file=sys.stderr)
            else:
                print(f"[REPLAY] MISMATCH: {diff_result['summary']}", file=sys.stderr)
                for diff in diff_result["differences"]:
                    print(f"  {diff['field']}: {diff['trace1']} != {diff['trace2']}", file=sys.stderr)
                sys.exit(2)

        print(json.dumps(result, indent=2))

    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except AOSError as e:
        print(f"Simulation failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_replay(args):
    """Replay a saved trace and verify determinism."""
    try:
        # Load the trace
        trace = Trace.load(args.trace_file)

        if not trace.verify():
            print(f"[ERROR] Trace integrity check failed", file=sys.stderr)
            sys.exit(1)

        print(f"Trace: {args.trace_file}")
        print(f"  Version: {trace.version}")
        print(f"  Seed: {trace.seed}")
        print(f"  Timestamp: {trace.timestamp}")
        print(f"  Steps: {len(trace.steps)}")
        print(f"  Root hash: {trace.root_hash}")
        print(f"  Integrity: VERIFIED")

        if args.verbose:
            print("\nSteps:")
            for step in trace.steps:
                print(f"  [{step.step_index}] {step.skill_id}: {step.outcome}")
                print(f"      Input: {step.input_hash}, Output: {step.output_hash}")

        # Re-execute if --execute flag
        if args.execute:
            print("\nRe-executing trace...")
            client = get_client()

            # Create new context with same seed/time
            ctx = RuntimeContext(
                seed=trace.seed,
                now=trace.timestamp
            )

            # Create new trace for comparison
            new_trace = create_trace_from_context(ctx, trace.plan)

            # Replay simulation
            start_time = time.time()
            result = client.simulate(
                plan=trace.plan,
                budget_cents=1000,  # Use default budget for replay
                seed=trace.seed
            )
            duration_ms = int((time.time() - start_time) * 1000)

            new_trace.add_step(
                skill_id="simulate",
                input_data={"plan": trace.plan, "budget": 1000},
                output_data=result,
                rng_state=ctx.rng_state,
                duration_ms=duration_ms,
                outcome="success" if result.get("feasible", False) else "failure"
            )
            new_trace.finalize()

            # Compare
            diff_result = diff_traces(trace, new_trace)
            if diff_result["match"]:
                print("[REPLAY] SUCCESS - Traces match exactly")
            else:
                print(f"[REPLAY] FAILED - {diff_result['summary']}")
                sys.exit(2)

    except FileNotFoundError:
        print(f"Trace file not found: {args.trace_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Replay failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_diff(args):
    """Compare two traces and show differences."""
    try:
        trace1 = Trace.load(args.trace1)
        trace2 = Trace.load(args.trace2)

        diff_result = diff_traces(trace1, trace2)

        print(f"Comparing:")
        print(f"  Trace 1: {args.trace1} (hash: {trace1.root_hash})")
        print(f"  Trace 2: {args.trace2} (hash: {trace2.root_hash})")
        print()

        if diff_result["match"]:
            print("Result: IDENTICAL")
        else:
            print(f"Result: DIFFERENT ({len(diff_result['differences'])} differences)")
            print()
            for diff in diff_result["differences"]:
                print(f"  {diff['field']}:")
                print(f"    Trace 1: {diff['trace1']}")
                print(f"    Trace 2: {diff['trace2']}")

        sys.exit(0 if diff_result["match"] else 1)

    except FileNotFoundError as e:
        print(f"Trace file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Diff failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="aos",
        description="AOS SDK Command-Line Interface - Machine-Native Agent Runtime"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # version
    subparsers.add_parser("version", help="Show version")

    # health
    subparsers.add_parser("health", help="Check server health")

    # capabilities
    subparsers.add_parser("capabilities", help="Show runtime capabilities")

    # skills
    subparsers.add_parser("skills", help="List available skills")

    # skill <id>
    skill_parser = subparsers.add_parser("skill", help="Describe a skill")
    skill_parser.add_argument("skill_id", help="Skill ID to describe")

    # simulate <json> - with determinism flags
    sim_parser = subparsers.add_parser("simulate", help="Simulate a plan with determinism support")
    sim_parser.add_argument("plan_json", help="Plan as JSON array")
    sim_parser.add_argument(
        "--budget",
        type=int,
        default=1000,
        help="Budget in cents (default: 1000)"
    )
    sim_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic simulation (default: 42)"
    )
    sim_parser.add_argument(
        "--timestamp",
        type=str,
        default=None,
        help="Frozen timestamp (ISO8601) for deterministic time"
    )
    sim_parser.add_argument(
        "--save-trace",
        type=str,
        default=None,
        metavar="PATH",
        help="Save execution trace to file"
    )
    sim_parser.add_argument(
        "--load-trace",
        type=str,
        default=None,
        metavar="PATH",
        help="Load trace for replay verification"
    )
    sim_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview simulation without executing"
    )

    # replay <trace> - replay and verify
    replay_parser = subparsers.add_parser("replay", help="Replay a saved trace")
    replay_parser.add_argument("trace_file", help="Path to trace file (.trace.json)")
    replay_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed step information"
    )
    replay_parser.add_argument(
        "--execute",
        action="store_true",
        help="Re-execute and verify against original trace"
    )

    # diff <trace1> <trace2> - compare traces
    diff_parser = subparsers.add_parser("diff", help="Compare two traces")
    diff_parser.add_argument("trace1", help="First trace file")
    diff_parser.add_argument("trace2", help="Second trace file")

    args = parser.parse_args()

    if args.command == "version":
        cmd_version(args)
    elif args.command == "health":
        cmd_health(args)
    elif args.command == "capabilities":
        cmd_capabilities(args)
    elif args.command == "skills":
        cmd_skills(args)
    elif args.command == "skill":
        cmd_skill(args)
    elif args.command == "simulate":
        cmd_simulate(args)
    elif args.command == "replay":
        cmd_replay(args)
    elif args.command == "diff":
        cmd_diff(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
