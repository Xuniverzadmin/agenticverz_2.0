# Layer: L7 — Ops & Deployment
# Product: system-wide
# Temporal:
#   Trigger: user (CLI)
#   Execution: sync
# Role: Backend CLI utilities
# Callers: shell
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: CLI Tools

#!/usr/bin/env python3
"""
CLI adapter for AOS - unified execution from command line.

Usage:
    aos run --agent-id <id> --goal "your goal here"
    aos list-agents
    aos list-skills
    aos get-run <run_id>
    aos demo           # Run 60-second demo
    aos demo --quick   # Run quick demo (30s)

This provides a command-line interface that uses the same execution path
as the API endpoints, ensuring consistency.

M3.5 CLI (Machine-Native SDK Demo):
- Quick 60-second demo showing core capabilities
- Skill listing with cost/constraint info
- Budget tracking visibility
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from typing import Optional


# Lazy imports for database-dependent modules (avoid requiring DATABASE_URL for demo)
def _get_db_imports():
    """Lazy import database-dependent modules.

    Uses L4-provided session and sql_text helpers instead of direct
    sqlmodel/sqlalchemy imports per L2 DB hygiene rules.
    """
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
        get_sync_session_dep,
        sql_text,
    )

    from .db import Agent, Run, engine, init_db
    from .events import get_publisher
    from .planners import get_planner
    from .worker.runner import RunRunner

    return get_sync_session_dep, sql_text, Agent, Run, engine, init_db, get_planner, RunRunner, get_publisher


# These don't require database - use absolute imports for CLI compatibility
from app.observability.cost_tracker import get_cost_tracker
from app.skills import list_skills, load_all_skills


# Setup logging (doesn't need DB)
def _get_logger():
    from .logging_config import setup_logging

    return setup_logging()


logger = None  # Lazy init


def create_agent(name: str) -> str:
    """Create a new agent and return its ID."""
    get_sync_session_dep, sql_text, Agent, Run, engine, init_db, _, _, _ = _get_db_imports()
    session = next(get_sync_session_dep())
    try:
        agent = Agent(name=name, status="active")
        session.add(agent)
        session.commit()
        session.refresh(agent)
        # Extract ID while session is open (returns scalar, not ORM object)
        agent_id = agent.id
    finally:
        session.close()
    return agent_id


def list_agents() -> list:
    """List all agents."""
    get_sync_session_dep, sql_text, Agent, Run, engine, init_db, _, _, _ = _get_db_imports()
    session = next(get_sync_session_dep())
    try:
        result = session.execute(sql_text("SELECT id, name, status, created_at FROM agent"))
        rows = result.mappings().all()
        return [
            {
                "id": a["id"],
                "name": a["name"],
                "status": a["status"],
                "created_at": a["created_at"].isoformat() if a["created_at"] else None,
            }
            for a in rows
        ]
    finally:
        session.close()


def get_run(run_id: str) -> Optional[dict]:
    """Get run status and details."""
    get_sync_session_dep, sql_text, Agent, Run, engine, init_db, _, _, _ = _get_db_imports()
    session = next(get_sync_session_dep())
    try:
        result = session.execute(
            sql_text(
                "SELECT id, agent_id, goal, status, attempts, error_message, "
                "plan_json, tool_calls_json, created_at, started_at, completed_at, duration_ms "
                "FROM run WHERE id = :run_id"
            ),
            {"run_id": run_id},
        )
        run = result.mappings().first()
        if not run:
            return None
        return {
            "run_id": run["id"],
            "agent_id": run["agent_id"],
            "goal": run["goal"],
            "status": run["status"],
            "attempts": run["attempts"],
            "error_message": run["error_message"],
            "plan": json.loads(run["plan_json"]) if run["plan_json"] else None,
            "tool_calls": json.loads(run["tool_calls_json"]) if run["tool_calls_json"] else None,
            "created_at": run["created_at"].isoformat() if run["created_at"] else None,
            "started_at": run["started_at"].isoformat() if run["started_at"] else None,
            "completed_at": run["completed_at"].isoformat() if run["completed_at"] else None,
            "duration_ms": run["duration_ms"],
        }
    finally:
        session.close()


def create_run(agent_id: str, goal: str) -> str:
    """Create a new run for an agent and return its ID."""
    get_sync_session_dep, sql_text, Agent, Run, engine, init_db, _, _, _ = _get_db_imports()
    session = next(get_sync_session_dep())
    try:
        # Verify agent exists
        agent_result = session.execute(
            sql_text("SELECT id FROM agent WHERE id = :agent_id"),
            {"agent_id": agent_id},
        )
        if not agent_result.mappings().first():
            raise ValueError(f"Agent not found: {agent_id}")

        run = Run(
            agent_id=agent_id,
            goal=goal,
            status="queued",
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        return run.id
    finally:
        session.close()


def execute_run_sync(run_id: str, wait: bool = True, poll_interval: float = 1.0) -> dict:
    """
    Execute a run synchronously using the worker runner.

    Args:
        run_id: The run ID to execute
        wait: If True, wait for completion and return result
        poll_interval: Seconds between status checks when waiting

    Returns:
        Final run status dict
    """
    _, _, _, _, _, _, _, RunRunner, _ = _get_db_imports()
    runner = RunRunner(run_id)
    runner.run()  # This runs the async execute in a new event loop

    if wait:
        # Poll for completion
        while True:
            result = get_run(run_id)
            if result and result["status"] in ("succeeded", "failed"):
                return result
            time.sleep(poll_interval)

    return get_run(run_id)


def run_goal(agent_id: str, goal: str, wait: bool = True, verbose: bool = False) -> dict:
    """
    High-level function to run a goal on an agent.

    Args:
        agent_id: Agent ID to run the goal on
        goal: The goal text
        wait: If True, wait for completion
        verbose: If True, print progress

    Returns:
        Final run status dict
    """
    get_sync_session_dep, sql_text, Agent, Run, engine, init_db, _, _, _ = _get_db_imports()

    if verbose:
        print(f"Creating run for agent {agent_id}...")
        print(f"Goal: {goal}")

    run_id = create_run(agent_id, goal)

    if verbose:
        print(f"Run created: {run_id}")
        print("Executing...")

    # Mark as running
    session = next(get_sync_session_dep())
    try:
        now = datetime.now(timezone.utc)
        session.execute(
            sql_text(
                "UPDATE run SET status = 'running', started_at = :now, attempts = 1 "
                "WHERE id = :run_id"
            ),
            {"now": now, "run_id": run_id},
        )
        session.commit()
    finally:
        session.close()

    result = execute_run_sync(run_id, wait=wait)

    if verbose:
        print(f"Status: {result['status']}")
        if result.get("error_message"):
            print(f"Error: {result['error_message']}")
        if result.get("duration_ms"):
            print(f"Duration: {result['duration_ms']:.0f}ms")

    return result


def show_skills(as_json: bool = False) -> None:
    """List all registered skills with their capabilities."""
    load_all_skills()
    skills = list_skills()

    if as_json:
        print(json.dumps(skills, indent=2))
        return

    print("\n=== AOS Registered Skills ===\n")
    for skill in skills:
        name = skill.get("name", "unknown")
        version = skill.get("version", "1.0.0")
        desc = skill.get("description", "No description")[:60]
        print(f"  {name} (v{version})")
        print(f"    {desc}")
        print()


def run_demo(quick: bool = False) -> None:
    """
    Run 60-second demo showcasing AOS capabilities.

    Demonstrates:
    1. Skill discovery and listing
    2. Agent creation
    3. Budget tracking
    4. Skill execution (json_transform)
    5. Cost enforcement
    """
    print("\n" + "=" * 60)
    print("   AOS Machine-Native SDK Demo")
    print("   Version: M3.5 | Runtime: Deterministic")
    print("=" * 60)

    start_time = time.time()

    # Step 1: Load and show skills
    print("\n[1/5] Loading skills...")
    load_all_skills()
    skills = list_skills()
    print(f"      Loaded {len(skills)} skills:")
    for s in skills[:5]:
        print(f"        - {s.get('name')}")
    if len(skills) > 5:
        print(f"        ... and {len(skills) - 5} more")

    if not quick:
        time.sleep(1)

    # Step 2: Show budget tracking
    print("\n[2/5] Budget tracking status...")
    tracker = get_cost_tracker()
    print(f"      Daily limit: {tracker.quota.daily_limit_cents}c")
    print(f"      Hourly limit: {tracker.quota.hourly_limit_cents}c")
    print(f"      Per-request limit: {tracker.quota.per_request_limit_cents}c")
    print(f"      Hard enforcement: {'ENABLED' if tracker.quota.enforce_hard_limit else 'disabled'}")

    if not quick:
        time.sleep(1)

    # Step 3: Execute json_transform skill
    print("\n[3/5] Executing json_transform skill...")
    from .skills.json_transform import JsonTransformSkill

    skill = JsonTransformSkill()
    test_data = {"user": "demo_user", "action": "test", "timestamp": datetime.now(timezone.utc).isoformat()}

    async def run_skill():
        result = await skill.execute({"data": test_data, "operation": "identity"})
        return result

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(run_skill())
    loop.close()

    print(f"      Input: {json.dumps(test_data)[:50]}...")
    print(f"      Output status: {result.get('status', 'unknown')}")
    print("      Deterministic: Yes (same input -> same output)")

    if not quick:
        time.sleep(1)

    # Step 4: Demonstrate cost tracking
    print("\n[4/5] Recording cost event...")
    alerts = tracker.record_cost(
        tenant_id="demo-tenant",
        workflow_id="demo-workflow",
        skill_id="json_transform",
        cost_cents=0.1,
        input_tokens=50,
        output_tokens=50,
        model="demo",
    )
    spend = tracker.get_spend("demo-tenant", "daily")
    print("      Recorded: 0.1c for json_transform")
    print(f"      Tenant daily spend: {spend:.2f}c")
    print(f"      Alerts triggered: {len(alerts)}")

    if not quick:
        time.sleep(1)

    # Step 5: Summary
    elapsed = time.time() - start_time
    print("\n[5/5] Demo complete!")
    print(f"      Elapsed time: {elapsed:.1f}s")
    print("\n" + "=" * 60)
    print("   AOS Core Capabilities Demonstrated:")
    print("   - Skill registration and discovery")
    print("   - Deterministic skill execution")
    print("   - Cost tracking and enforcement")
    print("   - Budget alerting system")
    print("=" * 60 + "\n")

    print("Next steps:")
    print("  aos create-agent --name my-agent")
    print("  aos run --agent-id <id> --goal 'your goal'")
    print("  aos list-skills --json")
    print()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="AOS CLI - Machine-Native Agent Operating System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # demo command (M3.5)
    demo_parser = subparsers.add_parser("demo", help="Run 60-second capability demo")
    demo_parser.add_argument("--quick", action="store_true", help="Quick demo (30s)")

    # list-skills command (M3.5)
    skills_parser = subparsers.add_parser("list-skills", help="List registered skills")
    skills_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a goal on an agent")
    run_parser.add_argument("--agent-id", "-a", required=True, help="Agent ID")
    run_parser.add_argument("--goal", "-g", required=True, help="Goal to execute")
    run_parser.add_argument("--no-wait", action="store_true", help="Don't wait for completion")
    run_parser.add_argument("--json", action="store_true", help="Output as JSON")
    run_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # create-agent command
    create_parser = subparsers.add_parser("create-agent", help="Create a new agent")
    create_parser.add_argument("--name", "-n", required=True, help="Agent name")
    create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # list-agents command
    list_parser = subparsers.add_parser("list-agents", help="List all agents")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # get-run command
    get_parser = subparsers.add_parser("get-run", help="Get run status")
    get_parser.add_argument("run_id", help="Run ID")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Handle commands that don't need database
    if args.command == "demo":
        run_demo(quick=args.quick)
        return

    if args.command == "list-skills":
        show_skills(as_json=args.json)
        return

    # Initialize database for other commands
    _, _, _, _, _, init_db, _, _, _ = _get_db_imports()  # noqa: F841 — only init_db used
    init_db()

    try:
        if args.command == "run":
            result = run_goal(
                agent_id=args.agent_id,
                goal=args.goal,
                wait=not args.no_wait,
                verbose=args.verbose,
            )
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"\nRun ID: {result['run_id']}")
                print(f"Status: {result['status']}")
                if result.get("error_message"):
                    print(f"Error: {result['error_message']}")
                if result.get("tool_calls"):
                    print(f"Steps executed: {len(result['tool_calls'])}")

        elif args.command == "create-agent":
            agent_id = create_agent(args.name)
            if args.json:
                print(json.dumps({"agent_id": agent_id, "name": args.name}))
            else:
                print(f"Created agent: {agent_id}")

        elif args.command == "list-agents":
            agents = list_agents()
            if args.json:
                print(json.dumps(agents, indent=2))
            else:
                if not agents:
                    print("No agents found")
                else:
                    for a in agents:
                        print(f"{a['id']}: {a['name']} ({a['status']})")

        elif args.command == "get-run":
            result = get_run(args.run_id)
            if not result:
                print(f"Run not found: {args.run_id}", file=sys.stderr)
                sys.exit(1)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Run ID: {result['run_id']}")
                print(f"Agent: {result['agent_id']}")
                print(f"Goal: {result['goal']}")
                print(f"Status: {result['status']}")
                if result.get("error_message"):
                    print(f"Error: {result['error_message']}")
                if result.get("duration_ms"):
                    print(f"Duration: {result['duration_ms']:.0f}ms")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
