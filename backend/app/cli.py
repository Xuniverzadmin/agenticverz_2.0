#!/usr/bin/env python3
"""
CLI adapter for AOS - unified execution from command line.

Usage:
    python -m app.cli run --agent-id <id> --goal "your goal here"
    python -m app.cli list-agents
    python -m app.cli get-run <run_id>

This provides a command-line interface that uses the same execution path
as the API endpoints, ensuring consistency.
"""
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from .db import Agent, Run, engine, init_db
from .planners import get_planner
from .skills import get_skill_manifest
from .worker.runner import RunRunner
from .events import get_publisher
from .logging_config import setup_logging

logger = setup_logging()


def create_agent(name: str) -> str:
    """Create a new agent and return its ID."""
    with Session(engine) as session:
        agent = Agent(name=name, status="active")
        session.add(agent)
        session.commit()
        session.refresh(agent)
        return agent.id


def list_agents() -> list:
    """List all agents."""
    with Session(engine) as session:
        agents = session.exec(select(Agent)).all()
        return [
            {
                "id": a.id,
                "name": a.name,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in agents
        ]


def get_run(run_id: str) -> Optional[dict]:
    """Get run status and details."""
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


def create_run(agent_id: str, goal: str) -> str:
    """Create a new run for an agent and return its ID."""
    with Session(engine) as session:
        agent = session.get(Agent, agent_id)
        if not agent:
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
    if verbose:
        print(f"Creating run for agent {agent_id}...")
        print(f"Goal: {goal}")

    run_id = create_run(agent_id, goal)

    if verbose:
        print(f"Run created: {run_id}")
        print("Executing...")

    # Mark as running
    with Session(engine) as session:
        run = session.get(Run, run_id)
        run.status = "running"
        run.started_at = datetime.utcnow()
        run.attempts = 1
        session.add(run)
        session.commit()

    result = execute_run_sync(run_id, wait=wait)

    if verbose:
        print(f"Status: {result['status']}")
        if result.get("error_message"):
            print(f"Error: {result['error_message']}")
        if result.get("duration_ms"):
            print(f"Duration: {result['duration_ms']:.0f}ms")

    return result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AOS CLI - Run agents from the command line"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

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

    # Initialize database
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
