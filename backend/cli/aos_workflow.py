#!/usr/bin/env python3
# AOS Workflow CLI - Forensic & Inspection Tool
"""
CLI tool for workflow engine inspection, debugging, and recovery.

Usage:
    aos workflow inspect --run <run_id>
    aos workflow list-running
    aos workflow golden-tail --run <run_id> --lines 20
    aos workflow replay-local --run <run_id>
    aos workflow stats --spec <spec_id>

Installation:
    chmod +x cli/aos_workflow.py
    ln -s $(pwd)/cli/aos_workflow.py /usr/local/bin/aos-workflow
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Optional

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_db_connection():
    """Get database connection using environment config."""
    try:
        import psycopg2

        db_url = os.getenv("DATABASE_URL", "postgresql://nova:novapass@localhost:5433/nova_aos")
        return psycopg2.connect(db_url)
    except ImportError:
        print("Error: psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)


def format_timestamp(ts: Optional[datetime]) -> str:
    """Format timestamp for display."""
    if ts is None:
        return "N/A"
    if isinstance(ts, str):
        return ts
    return ts.isoformat()


def format_json(obj: Any, indent: int = 2) -> str:
    """Format JSON for display."""
    if obj is None:
        return "null"
    if isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except json.JSONDecodeError:
            return obj
    return json.dumps(obj, indent=indent, default=str)


# ============== Inspect Command ==============


def cmd_inspect(args):
    """
    Inspect a workflow run - shows checkpoint state, golden events, and recovery hints.

    Usage: aos workflow inspect --run <run_id>
    """
    run_id = args.run
    print(f"\n{'='*60}")
    print(f"  WORKFLOW INSPECTION: {run_id}")
    print(f"{'='*60}\n")

    # 1. Load checkpoint from database
    print("## Checkpoint State\n")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                run_id, workflow_id, tenant_id, next_step_index,
                last_result_hash, status, version,
                created_at, updated_at, started_at, ended_at,
                step_outputs_json
            FROM workflow_checkpoints
            WHERE run_id = %s
        """,
            (run_id,),
        )

        row = cur.fetchone()
        if row:
            (
                run_id,
                workflow_id,
                tenant_id,
                next_step_index,
                last_result_hash,
                status,
                version,
                created_at,
                updated_at,
                started_at,
                ended_at,
                step_outputs_json,
            ) = row

            print(f"  Run ID:           {run_id}")
            print(f"  Workflow ID:      {workflow_id}")
            print(f"  Tenant ID:        {tenant_id or 'N/A'}")
            print(f"  Status:           {status}")
            print(f"  Next Step Index:  {next_step_index}")
            print(f"  Version:          {version}")
            print(f"  Last Result Hash: {last_result_hash or 'N/A'}")
            print(f"  Created At:       {format_timestamp(created_at)}")
            print(f"  Started At:       {format_timestamp(started_at)}")
            print(f"  Ended At:         {format_timestamp(ended_at)}")
            print(f"  Updated At:       {format_timestamp(updated_at)}")

            if step_outputs_json:
                outputs = json.loads(step_outputs_json) if isinstance(step_outputs_json, str) else step_outputs_json
                print(f"\n  Step Outputs ({len(outputs)} steps):")
                for step_id, output in outputs.items():
                    output_preview = str(output)[:100] + "..." if len(str(output)) > 100 else str(output)
                    print(f"    - {step_id}: {output_preview}")
        else:
            print(f"  No checkpoint found for run_id: {run_id}")
            print("\n  Possible causes:")
            print("    - Run has not started yet")
            print("    - Run ID is incorrect")
            print("    - Checkpoint was deleted/archived")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"  Error loading checkpoint: {e}")

    # 2. Load golden file (last 20 events)
    print("\n## Golden File (last 20 events)\n")
    golden_dir = os.getenv("GOLDEN_DIR", "/tmp/golden")
    golden_path = os.path.join(golden_dir, f"{run_id}.steps.jsonl")

    if os.path.exists(golden_path):
        try:
            with open(golden_path, "r") as f:
                lines = f.readlines()

            print(f"  Golden file: {golden_path}")
            print(f"  Total events: {len(lines)}")
            print()

            # Show last 20 events
            for i, line in enumerate(lines[-20:], start=max(1, len(lines) - 19)):
                try:
                    event = json.loads(line)
                    event_type = event.get("event_type", "unknown")
                    timestamp = event.get("timestamp", "")[:19]

                    if event_type == "run_start":
                        spec_id = event.get("data", {}).get("spec_id", "")
                        seed = event.get("data", {}).get("seed", "")
                        budget = event.get("data", {}).get("budget_snapshot", {})
                        print(f"  [{i:3d}] {timestamp} | START | spec={spec_id} seed={seed}")
                        if budget:
                            print(
                                f"        Budget: step_ceiling={budget.get('step_ceiling_cents')}c workflow_ceiling={budget.get('workflow_ceiling_cents')}c"
                            )

                    elif event_type == "step":
                        step_id = event.get("data", {}).get("step_id", "")
                        skill_id = event.get("data", {}).get("skill_id", "")
                        success = event.get("data", {}).get("success", True)
                        error_code = event.get("data", {}).get("error_code", "")
                        status_icon = "OK" if success else f"FAIL:{error_code}"
                        print(f"  [{i:3d}] {timestamp} | STEP  | {step_id} ({skill_id}) [{status_icon}]")

                    elif event_type == "run_end":
                        status = event.get("data", {}).get("status", "")
                        print(f"  [{i:3d}] {timestamp} | END   | status={status}")

                    else:
                        print(f"  [{i:3d}] {timestamp} | {event_type.upper()}")

                except json.JSONDecodeError:
                    print(f"  [{i:3d}] <invalid JSON>")

        except Exception as e:
            print(f"  Error reading golden file: {e}")
    else:
        print(f"  No golden file found at: {golden_path}")
        print("  Set GOLDEN_DIR environment variable if using different path.")

    # 3. Recovery suggestions
    print("\n## Recovery Suggestions\n")

    if row:
        if status == "running":
            print("  Status: RUNNING")
            print("  - Workflow is currently executing or was interrupted")
            print(f"  - Can resume from step index: {next_step_index}")
            print("  - To resume: Restart the worker or call engine.run() with same run_id")

        elif status == "failed":
            print("  Status: FAILED")
            print("  - Check error_code in the last step event above")
            print("  - Review golden file for the failing step's inputs")
            print("  - Fix the issue and use admin/rerun endpoint to retry")
            print(f'  - Rerun command: curl -X POST /admin/rerun -d \'{{"run_id": "{run_id}"}}\'')

        elif status == "completed":
            print("  Status: COMPLETED")
            print("  - Workflow finished successfully")
            print("  - Use golden file for replay verification")

        elif status == "budget_exceeded":
            print("  Status: BUDGET_EXCEEDED")
            print("  - Workflow stopped due to budget constraints")
            print("  - Review step cost estimates and budget ceilings")
            print("  - Adjust policy settings or increase budget")

        elif status == "sandbox_rejected":
            print("  Status: SANDBOX_REJECTED")
            print("  - Planner output was rejected by sandbox validation")
            print("  - Check for forbidden skills or policy violations")
            print("  - Review planner configuration")
    else:
        print("  Cannot provide suggestions without checkpoint data.")
        print("  - Verify run_id is correct")
        print("  - Check if run was ever started")

    print()


# ============== List Running Command ==============


def cmd_list_running(args):
    """
    List all currently running workflows.

    Usage: aos workflow list-running
    """
    print(f"\n{'='*60}")
    print("  RUNNING WORKFLOWS")
    print(f"{'='*60}\n")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT run_id, workflow_id, tenant_id, next_step_index,
                   started_at, updated_at, version
            FROM workflow_checkpoints
            WHERE status = 'running'
            ORDER BY started_at DESC
            LIMIT 100
        """
        )

        rows = cur.fetchall()

        if rows:
            print(f"  Found {len(rows)} running workflow(s):\n")
            print(f"  {'RUN_ID':<40} {'WORKFLOW_ID':<20} {'STEP':<6} {'STARTED':<20}")
            print(f"  {'-'*40} {'-'*20} {'-'*6} {'-'*20}")

            for row in rows:
                run_id, workflow_id, tenant_id, step_idx, started_at, updated_at, version = row
                started_str = format_timestamp(started_at)[:19] if started_at else "N/A"
                print(f"  {run_id:<40} {workflow_id or 'N/A':<20} {step_idx:<6} {started_str}")
        else:
            print("  No running workflows found.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"  Error: {e}")

    print()


# ============== Golden Tail Command ==============


def cmd_golden_tail(args):
    """
    Show last N events from golden file.

    Usage: aos workflow golden-tail --run <run_id> --lines 20
    """
    run_id = args.run
    lines_count = args.lines or 20

    print(f"\n{'='*60}")
    print(f"  GOLDEN TAIL: {run_id} (last {lines_count} lines)")
    print(f"{'='*60}\n")

    golden_dir = os.getenv("GOLDEN_DIR", "/tmp/golden")
    golden_path = os.path.join(golden_dir, f"{run_id}.steps.jsonl")

    if not os.path.exists(golden_path):
        print(f"  Golden file not found: {golden_path}")
        return

    try:
        with open(golden_path, "r") as f:
            all_lines = f.readlines()

        tail_lines = all_lines[-lines_count:]

        for i, line in enumerate(tail_lines, start=max(1, len(all_lines) - lines_count + 1)):
            try:
                event = json.loads(line)
                print(f"[{i}] {json.dumps(event, indent=2)}")
                print()
            except json.JSONDecodeError:
                print(f"[{i}] <invalid JSON>: {line[:100]}")

    except Exception as e:
        print(f"  Error: {e}")

    print()


# ============== Stats Command ==============


def cmd_stats(args):
    """
    Show statistics for a workflow spec.

    Usage: aos workflow stats --spec <spec_id>
    """
    spec_id = args.spec

    print(f"\n{'='*60}")
    print(f"  WORKFLOW STATS: {spec_id}")
    print(f"{'='*60}\n")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Count by status
        cur.execute(
            """
            SELECT status, COUNT(*) as count
            FROM workflow_checkpoints
            WHERE workflow_id = %s
            GROUP BY status
            ORDER BY count DESC
        """,
            (spec_id,),
        )

        rows = cur.fetchall()

        if rows:
            print("  Status Distribution:")
            total = sum(r[1] for r in rows)
            for status, count in rows:
                pct = (count / total * 100) if total > 0 else 0
                bar = "#" * int(pct / 5)
                print(f"    {status:<20} {count:>5} ({pct:5.1f}%) {bar}")
            print(f"    {'TOTAL':<20} {total:>5}")
        else:
            print(f"  No workflows found for spec_id: {spec_id}")

        # Recent runs
        print("\n  Recent Runs (last 10):")
        cur.execute(
            """
            SELECT run_id, status, started_at, ended_at
            FROM workflow_checkpoints
            WHERE workflow_id = %s
            ORDER BY created_at DESC
            LIMIT 10
        """,
            (spec_id,),
        )

        rows = cur.fetchall()
        for run_id, status, started_at, ended_at in rows:
            duration = ""
            if started_at and ended_at:
                try:
                    delta = ended_at - started_at
                    duration = f" ({delta.total_seconds():.1f}s)"
                except:
                    pass
            print(f"    {run_id[:20]}... | {status:<15} | {format_timestamp(started_at)[:19]}{duration}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"  Error: {e}")

    print()


# ============== Replay Local Command ==============


def cmd_replay_local(args):
    """
    Replay a workflow locally using golden file.

    Usage: aos workflow replay-local --run <run_id>
    """
    run_id = args.run

    print(f"\n{'='*60}")
    print(f"  LOCAL REPLAY: {run_id}")
    print(f"{'='*60}\n")

    golden_dir = os.getenv("GOLDEN_DIR", "/tmp/golden")
    golden_path = os.path.join(golden_dir, f"{run_id}.steps.jsonl")

    if not os.path.exists(golden_path):
        print(f"  Golden file not found: {golden_path}")
        print("  Cannot replay without golden file.")
        return

    print(f"  Golden file: {golden_path}")
    print()

    # Load golden events
    events = []
    with open(golden_path, "r") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    print(f"  Loaded {len(events)} events")

    # Extract spec and seed from run_start
    run_start = next((e for e in events if e.get("event_type") == "run_start"), None)
    if not run_start:
        print("  Error: No run_start event found")
        return

    spec_id = run_start.get("data", {}).get("spec_id", "unknown")
    seed = run_start.get("data", {}).get("seed", 0)
    budget_snapshot = run_start.get("data", {}).get("budget_snapshot", {})

    print(f"  Spec ID: {spec_id}")
    print(f"  Seed: {seed}")
    if budget_snapshot:
        print(f"  Budget Snapshot: step_ceiling={budget_snapshot.get('step_ceiling_cents')}c")

    print("\n  Replaying steps:")

    step_events = [e for e in events if e.get("event_type") == "step"]
    for i, event in enumerate(step_events):
        data = event.get("data", {})
        step_id = data.get("step_id", "?")
        skill_id = data.get("skill_id", "?")
        success = data.get("success", True)
        output_hash = data.get("output_hash", "")[:8] if data.get("output_hash") else ""

        status = "OK" if success else "FAIL"
        error_code = data.get("error_code", "") if not success else ""

        print(f"    [{i+1}] {step_id:<20} ({skill_id:<15}) [{status}] hash={output_hash}")
        if error_code:
            print(f"        Error: {error_code}")

    # Summary
    run_end = next((e for e in events if e.get("event_type") == "run_end"), None)
    if run_end:
        final_status = run_end.get("data", {}).get("status", "unknown")
        print(f"\n  Final Status: {final_status}")

    print("\n  Note: This is a read-only replay. For actual re-execution, use:")
    print(f'    curl -X POST /admin/rerun -d \'{{"run_id": "{run_id}"}}\'')
    print()


# ============== Main ==============


def main():
    parser = argparse.ArgumentParser(
        prog="aos-workflow", description="AOS Workflow Engine CLI - Inspection & Forensics Tool"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a workflow run")
    inspect_parser.add_argument("--run", "-r", required=True, help="Run ID to inspect")

    # list-running command
    list_parser = subparsers.add_parser("list-running", help="List running workflows")

    # golden-tail command
    tail_parser = subparsers.add_parser("golden-tail", help="Show last N golden events")
    tail_parser.add_argument("--run", "-r", required=True, help="Run ID")
    tail_parser.add_argument("--lines", "-n", type=int, default=20, help="Number of lines (default: 20)")

    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show workflow spec statistics")
    stats_parser.add_argument("--spec", "-s", required=True, help="Spec ID")

    # replay-local command
    replay_parser = subparsers.add_parser("replay-local", help="Replay workflow from golden file")
    replay_parser.add_argument("--run", "-r", required=True, help="Run ID to replay")

    args = parser.parse_args()

    if args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "list-running":
        cmd_list_running(args)
    elif args.command == "golden-tail":
        cmd_golden_tail(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "replay-local":
        cmd_replay_local(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
