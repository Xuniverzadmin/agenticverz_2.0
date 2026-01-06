#!/usr/bin/env python3
"""
AOS CLI - Machine-Native Agent Operating System

Usage:
    aos simulate --plan <plan.json>    # Simulate a plan before execution
    aos query <query_type>             # Query runtime state
    aos skills                         # List available skills
    aos skill <skill_id>               # Describe a skill
    aos capabilities                   # Get agent capabilities
    aos version                        # Show version info

Environment:
    AOS_API_URL     Base URL for AOS API (default: http://127.0.0.1:8000)
    AOS_API_KEY     API key for authentication

Examples:
    aos simulate --plan '{"steps": [{"skill": "http_call", "params": {"url": "https://api.example.com"}}]}'
    aos query remaining_budget_cents
    aos skills
    aos skill http_call
    aos capabilities --agent my-agent

Installation:
    chmod +x cli/aos.py
    ln -s $(pwd)/cli/aos.py /usr/local/bin/aos
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

# Configuration
DEFAULT_API_URL = "http://127.0.0.1:8000"


def get_api_url() -> str:
    """Get API base URL from environment or default."""
    return os.getenv("AOS_API_URL", DEFAULT_API_URL)


def get_api_key() -> Optional[str]:
    """Get API key from environment."""
    return os.getenv("AOS_API_KEY")


def api_request(
    method: str, path: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Make API request and return JSON response."""
    base_url = get_api_url()
    url = f"{base_url}{path}"

    # Add query params
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v)
        if query:
            url = f"{url}?{query}"

    # Prepare request
    headers = {"Content-Type": "application/json"}
    api_key = get_api_key()
    if api_key:
        headers["X-Api-Key"] = api_key

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            error_body = json.loads(e.read().decode("utf-8"))
            print(f"Error ({e.code}): {json.dumps(error_body, indent=2)}", file=sys.stderr)
        except Exception:
            print(f"Error ({e.code}): {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        print(f"Check that AOS is running at {base_url}", file=sys.stderr)
        sys.exit(1)


def format_json(obj: Any, indent: int = 2) -> str:
    """Format object as JSON."""
    return json.dumps(obj, indent=indent, default=str)


# ============== SIMULATE Command ==============


def cmd_simulate(args):
    """
    Simulate a plan before execution.

    Shows cost estimates, latency, risks, and feasibility.
    """
    # Parse plan from --plan argument or stdin
    plan_str = args.plan

    if plan_str == "-":
        plan_str = sys.stdin.read()

    try:
        plan_data = json.loads(plan_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing plan JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Handle different plan formats
    if "steps" in plan_data:
        # Full plan format: {"steps": [...]}
        steps = plan_data["steps"]
    elif isinstance(plan_data, list):
        # Direct steps array
        steps = plan_data
    else:
        print('Error: Plan must be {"steps": [...]} or a steps array', file=sys.stderr)
        sys.exit(1)

    # Normalize steps format
    normalized_steps = []
    for step in steps:
        if "skill" in step:
            normalized_steps.append({"skill": step["skill"], "params": step.get("params", {})})
        elif "skill_id" in step:
            normalized_steps.append({"skill": step["skill_id"], "params": step.get("inputs", step.get("params", {}))})
        else:
            print(f"Warning: Skipping step without skill: {step}", file=sys.stderr)

    if not normalized_steps:
        print("Error: No valid steps in plan", file=sys.stderr)
        sys.exit(1)

    # Build request
    request = {
        "plan": normalized_steps,
        "budget_cents": args.budget if args.budget else 1000,
    }

    if args.agent:
        request["agent_id"] = args.agent

    # Call API
    result = api_request("POST", "/api/v1/runtime/simulate", data=request)

    # Format output
    print()
    print("=" * 60)
    print("  PLAN SIMULATION RESULT")
    print("=" * 60)
    print()

    # Summary
    status_icon = "✅" if result["feasible"] else "❌"
    print(f"  Status:      {status_icon} {result['status'].upper()}")
    print(f"  Feasible:    {result['feasible']}")
    print()

    # Costs
    print("  📊 Cost Estimates:")
    print(f"      Total Cost:      {result['estimated_cost_cents']} cents")
    print(f"      Duration:        {result['estimated_duration_ms']} ms")
    print(f"      Budget Used:     {result['estimated_cost_cents']}/{args.budget or 1000} cents")
    print(f"      Remaining:       {result['budget_remaining_cents']} cents")
    print(f"      Budget OK:       {result['budget_sufficient']}")
    print()

    # Step breakdown
    print("  📋 Step Estimates:")
    for step in result.get("step_estimates", []):
        print(
            f"      [{step['step_index']}] {step['skill_id']:<20} cost={step['estimated_cost_cents']}c latency={step['estimated_latency_ms']}ms"
        )
    print()

    # Risks
    risks = result.get("risks", [])
    if risks:
        print("  ⚠️  Risks:")
        for risk in risks:
            prob_pct = int(risk["probability"] * 100)
            print(f"      [{risk['step_index']}] {risk['risk_type']:<20} ({prob_pct}% probability)")
            if risk.get("mitigation"):
                print(f"          → {risk['mitigation']}")
        print()

    # Warnings
    warnings = result.get("warnings", [])
    if warnings:
        print("  ⚡ Warnings:")
        for warning in warnings:
            print(f"      - {warning}")
        print()

    # Permission gaps
    gaps = result.get("permission_gaps", [])
    if gaps:
        print("  🔒 Permission Gaps:")
        for gap in gaps:
            print(f"      - {gap}")
        print()

    # Alternatives
    alts = result.get("alternatives", [])
    if alts:
        print("  💡 Alternatives:")
        for alt in alts:
            print(f"      - {alt}")
        print()

    # Raw output if verbose
    if args.verbose:
        print("  📄 Raw Response:")
        print(format_json(result))
        print()

    # Exit code based on feasibility
    if not result["feasible"]:
        sys.exit(1)


# ============== QUERY Command ==============


def cmd_query(args):
    """
    Query runtime state.

    Supported queries:
    - remaining_budget_cents
    - what_did_i_try_already
    - allowed_skills
    - last_step_outcome
    - skills_available_for_goal
    """
    query_type = args.query_type

    # Build params
    params = {}
    if args.goal:
        params["goal"] = args.goal
    if args.step:
        params["step"] = args.step
    if args.skill:
        params["skill"] = args.skill

    request = {
        "query_type": query_type,
        "params": params,
    }

    if args.agent:
        request["agent_id"] = args.agent
    if args.run:
        request["run_id"] = args.run

    result = api_request("POST", "/api/v1/runtime/query", data=request)

    print()
    print(f"Query: {query_type}")
    print("-" * 40)
    print(format_json(result.get("result", result)))
    print()

    if args.verbose:
        print("Supported queries:", ", ".join(result.get("supported_queries", [])))


# ============== SKILLS Command ==============


def cmd_skills(args):
    """List all available skills."""
    result = api_request("GET", "/api/v1/runtime/skills")

    print()
    print("=" * 60)
    if args.recommended:
        print("  RECOMMENDED SKILLS")
    else:
        print("  AVAILABLE SKILLS")
    print("=" * 60)
    print()

    skills = result.get("skills", [])
    descriptors = result.get("descriptors", {})

    # Filter to recommended skills if flag is set
    if args.recommended:
        # Recommended skills for getting started
        RECOMMENDED_SKILLS = [
            "llm_invoke",  # Core LLM capability
            "http_call",  # API integrations
            "web_search",  # Information gathering
            "write_file",  # Output generation
            "read_file",  # Input processing
        ]
        skills = [s for s in skills if s in RECOMMENDED_SKILLS]
        if not skills:
            # Fallback: show first 5 skills
            skills = result.get("skills", [])[:5]

        print("  💡 These skills are recommended for getting started:")
        print()

    if not skills:
        # Fall back to capabilities endpoint
        caps = api_request("GET", "/api/v1/runtime/capabilities")
        skills = list(caps.get("skills", {}).keys())
        descriptors = caps.get("skills", {})

    if not skills:
        print("  No skills available.")
        print()
        return

    print(f"  Found {len(skills)} skill(s):")
    print()

    for skill_id in sorted(skills):
        desc = descriptors.get(skill_id, {})
        cost = desc.get("cost_estimate_cents", desc.get("cost_model", {}).get("base_cents", 0))
        latency = desc.get("avg_latency_ms", desc.get("latency_ms", 0))
        print(f"    {skill_id:<20} cost={cost}c  latency={latency}ms")

    print()
    print("  Use 'aos skill <skill_id>' for details")
    print()


# ============== SKILL Command ==============


def cmd_skill(args):
    """Describe a specific skill."""
    skill_id = args.skill_id

    result = api_request("GET", f"/api/v1/runtime/skills/{skill_id}")

    print()
    print("=" * 60)
    print(f"  SKILL: {result.get('name', skill_id)}")
    print("=" * 60)
    print()

    print(f"  ID:          {result.get('skill_id', skill_id)}")
    print(f"  Version:     {result.get('version', 'N/A')}")
    print(f"  Description: {result.get('description', 'N/A')}")
    print()

    # Cost model
    cost_model = result.get("cost_model", {})
    print("  💰 Cost Model:")
    print(f"      Base:        {cost_model.get('base_cents', 0)} cents")
    if cost_model.get("per_kb_cents"):
        print(f"      Per KB:      {cost_model.get('per_kb_cents')} cents")
    print()

    # Constraints
    constraints = result.get("constraints", {})
    if constraints:
        print("  🔒 Constraints:")
        for key, value in constraints.items():
            print(f"      {key}: {value}")
        print()

    # Failure modes
    failure_modes = result.get("failure_modes", [])
    if failure_modes:
        print("  ⚠️  Failure Modes:")
        for fm in failure_modes:
            code = fm.get("code", "UNKNOWN")
            category = fm.get("category", "UNKNOWN")
            prob = fm.get("probability", 0)
            print(f"      {code:<25} [{category}] {int(prob * 100)}% probability")
        print()

    # Composition hints
    hints = result.get("composition_hints", {})
    if hints:
        print("  🔗 Composition Hints:")
        if hints.get("often_preceded_by"):
            print(f"      Often preceded by: {', '.join(hints['often_preceded_by'])}")
        if hints.get("often_followed_by"):
            print(f"      Often followed by: {', '.join(hints['often_followed_by'])}")
        if hints.get("anti_patterns"):
            print(f"      Anti-patterns: {', '.join(hints['anti_patterns'])}")
        print()

    if args.verbose:
        print("  📄 Raw Response:")
        print(format_json(result))
        print()


# ============== CAPABILITIES Command ==============


def cmd_capabilities(args):
    """Get capabilities for an agent."""
    params = {}
    if args.agent:
        params["agent_id"] = args.agent
    if args.tenant:
        params["tenant_id"] = args.tenant

    result = api_request("GET", "/api/v1/runtime/capabilities", params=params)

    print()
    print("=" * 60)
    print("  AGENT CAPABILITIES")
    print("=" * 60)
    print()

    if result.get("agent_id"):
        print(f"  Agent ID: {result['agent_id']}")
        print()

    # Budget
    budget = result.get("budget", {})
    print("  💰 Budget:")
    print(f"      Total:     {budget.get('total_cents', 0)} cents")
    print(f"      Remaining: {budget.get('remaining_cents', 0)} cents")
    print(f"      Per Step:  {budget.get('per_step_max_cents', 0)} cents max")
    print()

    # Skills
    skills = result.get("skills", {})
    print(f"  🔧 Skills ({len(skills)}):")
    for skill_id, info in sorted(skills.items()):
        avail = "✅" if info.get("available", True) else "❌"
        cost = info.get("cost_estimate_cents", 0)
        latency = info.get("avg_latency_ms", 0)
        print(f"      {avail} {skill_id:<20} cost={cost}c latency={latency}ms")
    print()

    # Rate limits
    rate_limits = result.get("rate_limits", {})
    if rate_limits:
        print("  ⏱️  Rate Limits:")
        for key, limit in rate_limits.items():
            remaining = limit.get("remaining", 0)
            resets = limit.get("resets_in_seconds", 0)
            print(f"      {key:<20} {remaining} remaining (resets in {resets}s)")
        print()

    # Permissions
    perms = result.get("permissions", [])
    if perms:
        print(f"  🔑 Permissions: {', '.join(perms)}")
        print()

    if args.verbose:
        print("  📄 Raw Response:")
        print(format_json(result))
        print()


# ============== RECOVERY Commands (M10) ==============


def cmd_recovery_candidates(args):
    """
    List recovery candidates for human review.

    Usage:
        aos recovery candidates [--status pending|approved|rejected|all] [--limit 50]
    """
    params = {
        "status": args.status,
        "limit": str(args.limit),
        "offset": str(args.offset),
    }

    result = api_request("GET", "/api/v1/recovery/candidates", params=params)

    candidates = result.get("candidates", [])

    print()
    print("=" * 80)
    print("  RECOVERY CANDIDATES")
    print("=" * 80)
    print()

    if not candidates:
        print(f"  No candidates found with status '{args.status}'")
        print()
        return

    print(f"  Total: {result.get('total', len(candidates))} (showing {len(candidates)})")
    print()
    print(f"  {'ID':<6} {'CONF':>6} {'STATUS':<10} {'ERROR_CODE':<20} {'SUGGESTION':<40}")
    print(f"  {'-' * 6} {'-' * 6} {'-' * 10} {'-' * 20} {'-' * 40}")

    for c in candidates:
        conf = f"{c['confidence']:.2f}"
        suggestion = c["suggestion"][:37] + "..." if len(c["suggestion"]) > 40 else c["suggestion"]
        error_code = (c.get("error_code") or "N/A")[:20]
        print(f"  {c['id']:<6} {conf:>6} {c['decision']:<10} {error_code:<20} {suggestion:<40}")

    print()

    if args.verbose:
        print("  📄 Raw Response:")
        print(format_json(result))
        print()


def cmd_recovery_approve(args):
    """
    Approve or reject a recovery candidate.

    Usage:
        aos recovery approve --id 17 --by mahesh [--note "looks correct"]
        aos recovery reject --id 17 --by mahesh [--note "false positive"]
    """
    decision = "approved" if not args.reject else "rejected"

    data = {
        "candidate_id": args.id,
        "approved_by": args.by,
        "decision": decision,
        "note": args.note or "",
    }

    result = api_request("POST", "/api/v1/recovery/approve", data=data)

    print()
    print("=" * 60)
    print(f"  CANDIDATE {decision.upper()}")
    print("=" * 60)
    print()
    print(f"  ID:          {result.get('id')}")
    print(f"  Decision:    {result.get('decision')}")
    print(f"  Approved By: {result.get('approved_by_human')}")
    print(f"  Approved At: {result.get('approved_at')}")
    if result.get("review_note"):
        print(f"  Note:        {result.get('review_note')}")
    print()


def cmd_recovery_stats(args):
    """
    Show recovery suggestion statistics.

    Usage:
        aos recovery stats
    """
    result = api_request("GET", "/api/v1/recovery/stats")

    print()
    print("=" * 60)
    print("  RECOVERY SUGGESTION STATS")
    print("=" * 60)
    print()
    print(f"  Total Candidates: {result.get('total_candidates', 0)}")
    print(f"  Pending:          {result.get('pending', 0)}")
    print(f"  Approved:         {result.get('approved', 0)}")
    print(f"  Rejected:         {result.get('rejected', 0)}")
    print(f"  Approval Rate:    {result.get('approval_rate', 0):.1%}")
    print()


# ============== VERSION Command ==============


def cmd_version(args):
    """Show version info."""
    # Local CLI version
    print()
    print("AOS CLI v0.1.0")
    print()

    # Try to get API version
    try:
        result = api_request("GET", "/version")
        print(f"API Version:   {result.get('version', 'N/A')}")
        print(f"API Phase:     {result.get('phase', 'N/A')}")
        print(f"Planner:       {result.get('planner_backend', 'N/A')}")
        print(f"Features:      {', '.join(result.get('features', []))}")
    except Exception:
        print("API: Not available")
    print()


# ============== QUICKSTART WIZARD ==============


def cmd_quickstart(args):
    """
    Interactive quickstart wizard for new AOS users.

    Guides through:
    1. API connection check
    2. Creating first agent
    3. Running first workflow
    4. Understanding results
    """
    print()
    print("=" * 60)
    print("  🚀 AOS QUICKSTART WIZARD")
    print("=" * 60)
    print()
    print("  Welcome to AOS - the Machine-Native Agent Operating System!")
    print("  This wizard will help you get started in ~5 minutes.")
    print()

    # Step 1: Check connection
    print("  📡 Step 1: Checking API connection...")
    try:
        result = api_request("GET", "/health")
        if result.get("status") == "healthy":
            print("      ✅ API is healthy and ready!")
        else:
            print(f"      ⚠️  API status: {result.get('status', 'unknown')}")
    except Exception as e:
        print(f"      ❌ Cannot connect to API: {e}")
        print()
        print("  💡 Tip: Make sure AOS is running:")
        print("      docker compose up -d")
        print()
        print("      Or set AOS_API_URL environment variable:")
        print("      export AOS_API_URL=http://your-server:8000")
        return

    # Step 2: Check API key
    print()
    print("  🔑 Step 2: Checking authentication...")
    api_key = get_api_key()
    if api_key:
        print("      ✅ API key found in AOS_API_KEY")
        # Verify it works
        try:
            result = api_request("GET", "/api/v1/runtime/capabilities")
            print("      ✅ API key is valid!")
        except Exception:
            print("      ⚠️  API key may be invalid. Check your credentials.")
    else:
        print("      ⚠️  No API key set. Set AOS_API_KEY environment variable:")
        print("         export AOS_API_KEY=your-api-key")
        print()
        print("      📋 You can find your API key in the AOS console")
        print("         or in your .env file.")

    # Step 3: Show available skills
    print()
    print("  🔧 Step 3: Checking available skills...")
    try:
        result = api_request("GET", "/api/v1/runtime/capabilities")
        skills = list(result.get("skills", {}).keys())
        if skills:
            print(f"      ✅ Found {len(skills)} skill(s): {', '.join(skills[:5])}", end="")
            if len(skills) > 5:
                print(f" ... and {len(skills) - 5} more")
            else:
                print()
        else:
            print("      ⚠️  No skills available. Check your configuration.")
    except Exception:
        print("      ⚠️  Could not fetch skills.")

    # Step 4: Example workflow
    print()
    print("  📝 Step 4: Your first workflow")
    print()
    print("  Try running a simple simulation:")
    print()
    print('    aos simulate --plan \'{"steps": [{"skill": "llm_invoke", "params": {"prompt": "Hello!"}}]}\'')
    print()
    print("  Or query your remaining budget:")
    print()
    print("    aos query remaining_budget_cents")
    print()

    # Step 5: Quick reference
    print("  📚 Quick Reference")
    print("  " + "-" * 56)
    print("  aos simulate --plan <json>    Simulate a plan")
    print("  aos skills                    List all skills")
    print("  aos skills --recommended      Show starter skills")
    print("  aos skill <id>                Get skill details")
    print("  aos capabilities              Show agent capabilities")
    print("  aos query <type>              Query runtime state")
    print("  aos recovery candidates       List recovery candidates")
    print()

    # Step 6: Resources
    print("  🔗 Resources")
    print("  " + "-" * 56)
    print("  Documentation:   docs/API_WORKFLOW_GUIDE.md")
    print("  Memory PINs:     docs/memory-pins/INDEX.md")
    print("  Support:         https://github.com/anthropics/aos/issues")
    print()
    print("  Happy building! 🎉")
    print()


# ============== MAIN ==============


def main():
    parser = argparse.ArgumentParser(
        prog="aos",
        description="AOS CLI - Machine-Native Agent Operating System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aos simulate --plan '{"steps": [{"skill": "http_call", "params": {"url": "..."}}]}'
  aos query remaining_budget_cents
  aos skills
  aos skill http_call
  aos capabilities --agent my-agent
  aos version

Environment:
  AOS_API_URL   API base URL (default: http://127.0.0.1:8000)
  AOS_API_KEY   API key for authentication
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # simulate command
    sim_parser = subparsers.add_parser("simulate", help="Simulate a plan before execution")
    sim_parser.add_argument("--plan", "-p", required=True, help="Plan JSON (or - for stdin)")
    sim_parser.add_argument("--budget", "-b", type=int, default=1000, help="Budget in cents (default: 1000)")
    sim_parser.add_argument("--agent", "-a", help="Agent ID")
    sim_parser.add_argument("--verbose", "-v", action="store_true", help="Show raw response")

    # query command
    query_parser = subparsers.add_parser("query", help="Query runtime state")
    query_parser.add_argument("query_type", help="Query type (e.g. remaining_budget_cents)")
    query_parser.add_argument("--agent", "-a", help="Agent ID")
    query_parser.add_argument("--run", "-r", help="Run ID")
    query_parser.add_argument("--goal", "-g", help="Goal for skills_available_for_goal")
    query_parser.add_argument("--step", help="Step filter for what_did_i_try_already")
    query_parser.add_argument("--skill", help="Skill filter for what_did_i_try_already")
    query_parser.add_argument("--verbose", "-v", action="store_true", help="Show raw response")

    # skills command
    skills_parser = subparsers.add_parser("skills", help="List available skills")
    skills_parser.add_argument("--verbose", "-v", action="store_true", help="Show raw response")
    skills_parser.add_argument(
        "--recommended", "-r", action="store_true", help="Show recommended skills for getting started"
    )

    # skill command
    skill_parser = subparsers.add_parser("skill", help="Describe a specific skill")
    skill_parser.add_argument("skill_id", help="Skill ID to describe")
    skill_parser.add_argument("--verbose", "-v", action="store_true", help="Show raw response")

    # capabilities command
    cap_parser = subparsers.add_parser("capabilities", help="Get agent capabilities")
    cap_parser.add_argument("--agent", "-a", help="Agent ID")
    cap_parser.add_argument("--tenant", "-t", help="Tenant ID")
    cap_parser.add_argument("--verbose", "-v", action="store_true", help="Show raw response")

    # version command
    _ver_parser = subparsers.add_parser("version", help="Show version info")

    # quickstart command
    _qs_parser = subparsers.add_parser("quickstart", help="Interactive quickstart wizard for new users")

    # recovery command group (M10)
    recovery_parser = subparsers.add_parser("recovery", help="Recovery suggestion commands (M10)")
    recovery_subparsers = recovery_parser.add_subparsers(dest="recovery_command", help="Recovery subcommands")

    # recovery candidates
    rc_parser = recovery_subparsers.add_parser("candidates", help="List recovery candidates")
    rc_parser.add_argument(
        "--status",
        "-s",
        default="pending",
        choices=["pending", "approved", "rejected", "all"],
        help="Filter by status (default: pending)",
    )
    rc_parser.add_argument("--limit", "-l", type=int, default=50, help="Max results (default: 50)")
    rc_parser.add_argument("--offset", "-o", type=int, default=0, help="Pagination offset")
    rc_parser.add_argument("--verbose", "-v", action="store_true", help="Show raw response")

    # recovery approve
    ra_parser = recovery_subparsers.add_parser("approve", help="Approve a recovery candidate")
    ra_parser.add_argument("--id", "-i", type=int, required=True, help="Candidate ID to approve")
    ra_parser.add_argument("--by", "-b", required=True, help="User making the decision")
    ra_parser.add_argument("--note", "-n", default="", help="Optional review note")
    ra_parser.add_argument("--reject", "-r", action="store_true", help="Reject instead of approve")

    # recovery reject (alias for approve --reject)
    rr_parser = recovery_subparsers.add_parser("reject", help="Reject a recovery candidate")
    rr_parser.add_argument("--id", "-i", type=int, required=True, help="Candidate ID to reject")
    rr_parser.add_argument("--by", "-b", required=True, help="User making the decision")
    rr_parser.add_argument("--note", "-n", default="", help="Optional review note")

    # recovery stats
    _rs_parser = recovery_subparsers.add_parser("stats", help="Show recovery statistics")

    args = parser.parse_args()

    if args.command == "simulate":
        cmd_simulate(args)
    elif args.command == "query":
        cmd_query(args)
    elif args.command == "skills":
        cmd_skills(args)
    elif args.command == "skill":
        cmd_skill(args)
    elif args.command == "capabilities":
        cmd_capabilities(args)
    elif args.command == "version":
        cmd_version(args)
    elif args.command == "quickstart":
        cmd_quickstart(args)
    elif args.command == "recovery":
        if args.recovery_command == "candidates":
            cmd_recovery_candidates(args)
        elif args.recovery_command == "approve":
            cmd_recovery_approve(args)
        elif args.recovery_command == "reject":
            args.reject = True
            cmd_recovery_approve(args)
        elif args.recovery_command == "stats":
            cmd_recovery_stats(args)
        else:
            recovery_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
