# Layer: L7 — Customer Integration (CLI)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: user (CLI)
#   Execution: sync
# Role: Customer CLI utilities
# Callers: shell
# Allowed Imports: L4, L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: CLI Tools

#!/usr/bin/env python3
"""
Customer CLI for AOS.

Usage:
    python -m app.hoc.cus.integrations.cus_cli run --agent-id <id> --goal "..." --tenant-id <tenant>
    python -m app.hoc.cus.integrations.cus_cli create-agent --name "My Agent"
    python -m app.hoc.cus.integrations.cus_cli list-agents
    python -m app.hoc.cus.integrations.cus_cli get-run <run_id>
    python -m app.hoc.cus.integrations.cus_cli list-skills
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional


def _get_db_imports():
    """Lazy import database-dependent modules."""
    from sqlmodel import Session, select

    from app.db import Agent, Run, engine, init_db
    from app.hoc.int.worker.runner import RunRunner

    return Session, select, Agent, Run, engine, init_db, RunRunner


def _get_trace_imports():
    """Lazy import trace-related modules."""
    from sqlalchemy import text

    from app.hoc.cus.logs.L6_drivers.pg_store import PostgresTraceStore

    return text, PostgresTraceStore


def _jsonable(value):
    """Best-effort conversion to JSON-serializable data."""
    try:
        json.dumps(value)
        return value
    except TypeError:
        if isinstance(value, dict):
            return {str(k): _jsonable(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [_jsonable(v) for v in value]
        return str(value)


def _maybe_backfill_trace_steps(
    run_id: str,
    tool_calls: list,
    *,
    run_status: str,
    tenant_id: str,
    agent_id: Optional[str],
    is_synthetic: bool = False,
    synthetic_scenario_id: Optional[str] = None,
    verbose: bool = False,
) -> None:
    """Backfill trace steps for CLI direct-execution when DB steps are missing."""
    if not tool_calls:
        return

    if os.getenv("USE_POSTGRES_TRACES", "false").lower() != "true":
        return

    Session, select, Agent, Run, engine, init_db, _ = _get_db_imports()
    text, PostgresTraceStore = _get_trace_imports()

    try:
        with Session(engine) as session:
            trace_row = session.execute(
                text("SELECT trace_id FROM aos_traces WHERE run_id = :run_id"),
                {"run_id": run_id},
            ).first()
            if not trace_row:
                return
            trace_id = trace_row[0]
            step_count_row = session.execute(
                text("SELECT COUNT(*) FROM aos_trace_steps WHERE trace_id = :trace_id"),
                {"trace_id": trace_id},
            ).first()
            step_count = int(step_count_row[0]) if step_count_row else 0
            if step_count > 0:
                return
    except Exception:
        return

    async def _backfill():
        store = PostgresTraceStore()
        try:
            for index, call in enumerate(tool_calls):
                params = _jsonable(call.get("request") or {})
                outcome = _jsonable(call.get("response") or {})
                side_effects = call.get("side_effects") or {}
                status = call.get("status") or "unknown"
                duration = call.get("duration") or 0
                attempts = call.get("attempts") or 1

                await store.record_step(
                    trace_id=trace_id,
                    run_id=run_id,
                    step_index=index,
                    skill_name=call.get("skill") or "unknown",
                    params=params,
                    status=status,
                    outcome_category="execution",
                    outcome_code=status,
                    outcome_data=outcome,
                    cost_cents=side_effects.get("cost_cents", 0),
                    duration_ms=float(duration) * 1000,
                    retry_count=max(int(attempts) - 1, 0),
                    source="cli_backfill",
                    is_synthetic=is_synthetic,
                    synthetic_scenario_id=synthetic_scenario_id,
                )

            if run_status in ("succeeded", "failed", "halted"):
                await store.complete_trace(
                    run_id=run_id,
                    status="completed" if run_status == "succeeded" else "failed",
                    metadata={"source": "cli_backfill"},
                )
        finally:
            await store.close()

    try:
        asyncio.run(_backfill())
        if verbose:
            print("Trace steps backfilled.")
    except Exception as exc:
        if verbose:
            print(f"Trace backfill failed: {exc}")


def create_agent(name: str, tenant_id: Optional[str] = None) -> str:
    """Create a new agent and return its ID."""
    Session, select, Agent, Run, engine, init_db, _ = _get_db_imports()
    with Session(engine) as session:
        agent = Agent(name=name, status="active", tenant_id=tenant_id)
        session.add(agent)
        session.commit()
        session.refresh(agent)
        return agent.id


def list_agents(tenant_id: Optional[str] = None) -> list:
    """List all agents, optionally filtered by tenant."""
    Session, select, Agent, Run, engine, init_db, _ = _get_db_imports()
    with Session(engine) as session:
        query = select(Agent)
        if tenant_id:
            query = query.where(Agent.tenant_id == tenant_id)
        agents = session.exec(query).all()
        return [
            {
                "id": a.id,
                "name": a.name,
                "status": a.status,
                "tenant_id": a.tenant_id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in agents
        ]


def get_run(run_id: str) -> Optional[dict]:
    """Get run status and details."""
    Session, select, Agent, Run, engine, init_db, _ = _get_db_imports()
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run:
            return None
        return {
            "run_id": run.id,
            "agent_id": run.agent_id,
            "goal": run.goal,
            "status": run.status,
            "attempts": run.attempts,
            "error_message": run.error_message,
            "plan": json.loads(run.plan_json) if run.plan_json else None,
            "tool_calls": json.loads(run.tool_calls_json) if run.tool_calls_json else None,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "duration_ms": run.duration_ms,
        }


def _generate_plan_or_fail(agent_id: str, goal: str, run_id: str, session, run) -> None:
    """Generate plan via L4 engine and persist to the run."""
    from app.hoc.cus.policies.L5_engines.plan_generation import generate_plan_for_run

    try:
        plan_result = generate_plan_for_run(
            agent_id=agent_id,
            goal=goal,
            run_id=run_id,
        )
        run.plan_json = plan_result.plan_json
        session.add(run)
        session.commit()
    except Exception as exc:
        run.status = "failed"
        run.error_message = f"plan_generation_failed: {exc}"
        session.add(run)
        session.commit()
        raise


def create_run(
    agent_id: str,
    goal: str,
    *,
    tenant_id: str,
    origin_system_id: str,
) -> str:
    """Create a new run with plan generation and return its ID."""
    if not tenant_id:
        raise ValueError("tenant_id is required for run creation")

    Session, select, Agent, Run, engine, init_db, _ = _get_db_imports()
    with Session(engine) as session:
        agent = session.get(Agent, agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        run = Run(
            agent_id=agent_id,
            goal=goal,
            status="queued",
            tenant_id=tenant_id,
            origin_system_id=origin_system_id,
        )
        session.add(run)
        session.commit()
        session.refresh(run)

        _generate_plan_or_fail(agent_id, goal, run.id, session, run)
        return run.id


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
    _, _, _, _, _, _, RunRunner = _get_db_imports()
    runner = RunRunner(run_id)
    runner.run()  # Runs async execute in a new event loop

    if wait:
        while True:
            result = get_run(run_id)
            if result and result["status"] in ("succeeded", "failed", "retry"):
                return result
            time.sleep(poll_interval)

    return get_run(run_id)


def run_goal(
    agent_id: str,
    goal: str,
    *,
    tenant_id: str,
    origin_system_id: str,
    wait: bool = True,
    verbose: bool = False,
) -> dict:
    """Run a goal on an agent using the production execution path."""
    Session, select, Agent, Run, engine, init_db, _ = _get_db_imports()
    from app.skills import load_all_skills

    if verbose:
        print(f"Creating run for agent {agent_id}...")
        print(f"Goal: {goal}")

    load_all_skills()
    run_id = create_run(
        agent_id=agent_id,
        goal=goal,
        tenant_id=tenant_id,
        origin_system_id=origin_system_id,
    )

    if verbose:
        print(f"Run created: {run_id}")
        print("Executing...")

    with Session(engine) as session:
        run = session.get(Run, run_id)
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        run.attempts = 1
        session.add(run)
        session.commit()

    result = execute_run_sync(run_id, wait=wait)
    tool_calls = result.get("tool_calls") or []

    if tool_calls:
        with Session(engine) as session:
            run = session.get(Run, run_id)
            if run:
                _maybe_backfill_trace_steps(
                    run_id=run_id,
                    tool_calls=tool_calls,
                    run_status=result.get("status", "unknown"),
                    tenant_id=tenant_id,
                    agent_id=agent_id,
                    is_synthetic=getattr(run, "is_synthetic", False) or False,
                    synthetic_scenario_id=getattr(run, "synthetic_scenario_id", None),
                    verbose=verbose,
                )

    if verbose:
        print(f"Status: {result['status']}")
        if result.get("error_message"):
            print(f"Error: {result['error_message']}")
        if result.get("duration_ms"):
            print(f"Duration: {result['duration_ms']:.0f}ms")

    return result


def show_skills(as_json: bool = False) -> None:
    """List all registered skills with their capabilities."""
    from app.skills import list_skills, load_all_skills

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


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="AOS Customer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a goal on an agent")
    run_parser.add_argument("--agent-id", "-a", required=True, help="Agent ID")
    run_parser.add_argument("--goal", "-g", required=True, help="Goal to execute")
    run_parser.add_argument("--tenant-id", required=True, help="Tenant ID for the run")
    run_parser.add_argument(
        "--origin-system-id",
        default="cus-cli",
        help="Origin system identifier (default: cus-cli)",
    )
    run_parser.add_argument("--no-wait", action="store_true", help="Don't wait for completion")
    run_parser.add_argument("--json", action="store_true", help="Output as JSON")
    run_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # create-agent command
    create_parser = subparsers.add_parser("create-agent", help="Create a new agent")
    create_parser.add_argument("--name", "-n", required=True, help="Agent name")
    create_parser.add_argument("--tenant-id", help="Tenant ID (optional)")
    create_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # list-agents command
    list_parser = subparsers.add_parser("list-agents", help="List all agents")
    list_parser.add_argument("--tenant-id", help="Tenant ID filter (optional)")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # get-run command
    get_parser = subparsers.add_parser("get-run", help="Get run status")
    get_parser.add_argument("run_id", help="Run ID")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # list-skills command
    skills_parser = subparsers.add_parser("list-skills", help="List registered skills")
    skills_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize database for commands that need it
    if args.command not in ("list-skills",):
        _, _, _, _, _, init_db, _ = _get_db_imports()
        init_db()

    try:
        if args.command == "run":
            result = run_goal(
                agent_id=args.agent_id,
                goal=args.goal,
                tenant_id=args.tenant_id,
                origin_system_id=args.origin_system_id,
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
            agent_id = create_agent(args.name, tenant_id=args.tenant_id)
            if args.json:
                print(json.dumps({"agent_id": agent_id, "name": args.name}))
            else:
                print(f"Created agent: {agent_id}")

        elif args.command == "list-agents":
            agents = list_agents(tenant_id=args.tenant_id)
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

        elif args.command == "list-skills":
            show_skills(as_json=args.json)

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
