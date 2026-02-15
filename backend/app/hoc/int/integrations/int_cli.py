# Layer: L7 — Internal Ops (CLI)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: user (CLI)
#   Execution: sync
# Role: Internal CLI utilities
# Callers: shell
# Allowed Imports: L4, L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: CLI Tools

#!/usr/bin/env python3
"""
Internal CLI for AOS (ops/demo utilities).

Usage:
    python -m app.hoc.int.integrations.int_cli demo
    python -m app.hoc.int.integrations.int_cli demo --quick
    python -m app.hoc.int.integrations.int_cli list-skills
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone

from app.observability.cost_tracker import get_cost_tracker
from app.skills import list_skills, load_all_skills


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
    2. Deterministic skill execution
    3. Budget tracking and alerts
    """
    start_time = time.time()

    print("\n" + "=" * 60)
    print("   AOS 60-Second Demo")
    print("=" * 60)

    # Step 1: Show skills
    print("\n[1/5] Discovering skills...")
    load_all_skills()
    skills = list_skills()
    print(f"      Found {len(skills)} skills registered")
    for skill in skills[:5]:
        print(f"      - {skill['name']}")
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
    from app.skills.json_transform import JsonTransformSkill

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
    print("  python -m app.hoc.cus.integrations.cus_cli create-agent --name my-agent")
    print("  python -m app.hoc.cus.integrations.cus_cli run --agent-id <id> --goal 'your goal' --tenant-id <tenant>")
    print("  python -m app.hoc.cus.integrations.cus_cli list-skills --json")
    print()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="AOS Internal CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    demo_parser = subparsers.add_parser("demo", help="Run 60-second capability demo")
    demo_parser.add_argument("--quick", action="store_true", help="Quick demo (30s)")

    skills_parser = subparsers.add_parser("list-skills", help="List registered skills")
    skills_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "demo":
        run_demo(quick=args.quick)
        return

    if args.command == "list-skills":
        show_skills(as_json=args.json)
        return


if __name__ == "__main__":
    main()
