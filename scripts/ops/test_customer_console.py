#!/usr/bin/env python3
"""
Customer Console Test Script
Agenticverz – M24 Ops Console (Phase 2.1)

Purpose:
- Validate Ops Console endpoints
- Surface empty-data states clearly
- Support CI, demo, and local validation

Usage:
  python3 scripts/ops/test_customer_console.py
  python3 scripts/ops/test_customer_console.py --json
  python3 scripts/ops/test_customer_console.py --endpoint customers/at-risk
  python3 scripts/ops/test_customer_console.py --verbose
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

import httpx

# Configuration
BASE_URL = os.getenv("AOS_API_BASE", "http://localhost:8000")
API_KEY = os.getenv(
    "AOS_API_KEY", "edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf"
)
OPS_PREFIX = "/ops"
TIMEOUT = 10

# Endpoints to test
ENDPOINTS = {
    "pulse": "/pulse",
    "customers": "/customers",
    "customers/at-risk": "/customers/at-risk",
    "playbooks": "/playbooks",
    "infra": "/infra",
}

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


# ----------------------------
# API Call with Latency
# ----------------------------


def call(endpoint: str) -> Dict[str, Any]:
    """Call endpoint and return result with latency."""
    url = f"{BASE_URL}{OPS_PREFIX}{endpoint}"
    headers = {"X-API-Key": API_KEY}
    start = time.time()

    try:
        r = httpx.get(url, headers=headers, timeout=TIMEOUT)
        elapsed = round((time.time() - start) * 1000, 2)

        return {
            "url": url,
            "status_code": r.status_code,
            "latency_ms": elapsed,
            "ok": r.status_code == 200,
            "body": r.json()
            if "application/json" in r.headers.get("content-type", "")
            else r.text,
        }
    except Exception as e:
        return {
            "url": url,
            "ok": False,
            "error": str(e),
            "latency_ms": round((time.time() - start) * 1000, 2),
        }


# ----------------------------
# Schema Assertions
# ----------------------------


def assert_shape(name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal schema sanity checks."""
    body = result.get("body", {})

    if not result["ok"]:
        result["assertion"] = "FAILED"
        result["assertion_error"] = result.get(
            "error", f"HTTP {result.get('status_code')}"
        )
        return result

    try:
        if name == "pulse":
            assert "system_state" in body or "system_status" in body, (
                "pulse missing system_state"
            )
            result["data_present"] = body.get("active_tenants_24h", 0) > 0

        elif name == "customers":
            assert isinstance(body, list), "customers must be list"
            result["count"] = len(body)
            result["data_present"] = len(body) > 0

        elif name == "customers/at-risk":
            assert isinstance(body, list), "at-risk must be list"
            result["count"] = len(body)
            result["data_present"] = len(body) > 0

        elif name == "playbooks":
            assert isinstance(body, list), "playbooks must be list"
            result["count"] = len(body)
            result["data_present"] = len(body) > 0
            # Verify expected playbooks exist
            playbook_ids = [p.get("id") for p in body]
            expected = {
                "silent_churn",
                "policy_friction",
                "abandonment",
                "engagement_decay",
                "legal_only",
            }
            result["playbooks_configured"] = expected.issubset(set(playbook_ids))

        elif name == "infra":
            assert "db_connections_current" in body or "db" in body, (
                "infra missing db info"
            )
            assert "redis_memory_used_mb" in body or "redis" in body, (
                "infra missing redis info"
            )
            result["data_present"] = True

        result["assertion"] = "PASSED"

    except AssertionError as e:
        result["assertion"] = "FAILED"
        result["assertion_error"] = str(e)

    return result


# ----------------------------
# Verbose Output
# ----------------------------


def print_verbose(name: str, result: Dict[str, Any]):
    """Print detailed results for verbose mode."""
    body = result.get("body", {})

    if name == "pulse" and result["ok"]:
        print(
            f"      Status: {body.get('system_state', body.get('system_status', 'unknown'))}"
        )
        print(f"      Active tenants (24h): {body.get('active_tenants_24h', 0)}")
        print(f"      Incidents (24h): {body.get('incidents_created_24h', 0)}")
        print(f"      Replays (24h): {body.get('replays_executed_24h', 0)}")

    elif name == "customers" and result["ok"] and body:
        print("      Sample customer segments:")
        for c in body[:3]:
            delta = c.get("stickiness_delta", 1.0)
            trend = "↑" if delta > 1.1 else "↓" if delta < 0.9 else "→"
            print(
                f"        - {c.get('tenant_id', '?')[:20]}... | stickiness: {c.get('stickiness_7d', 0):.1f} (7d) {trend}"
            )

    elif name == "customers/at-risk" and result["ok"] and body:
        print("      At-risk customers:")
        for c in body[:3]:
            risk = c.get("risk_level", "unknown")
            color = RED if risk == "critical" else YELLOW if risk == "high" else RESET
            print(
                f"        - {color}{risk.upper()}{RESET}: {c.get('tenant_id', '?')[:20]}..."
            )
            print(f"          Reason: {c.get('primary_risk_reason', 'unknown')}")

    elif name == "playbooks" and result["ok"] and body:
        print("      Configured playbooks:")
        for p in body:
            risk = p.get("risk_level", "unknown")
            color = RED if risk == "critical" else YELLOW if risk == "high" else RESET
            print(
                f"        - {BOLD}{p.get('id')}{RESET}: {p.get('name')} [{color}{risk}{RESET}]"
            )

    elif name == "infra" and result["ok"]:
        db_pct = (
            body.get("db_storage_used_gb", 0)
            / max(body.get("db_storage_limit_gb", 1), 1)
        ) * 100
        redis_pct = (
            body.get("redis_memory_used_mb", 0)
            / max(body.get("redis_memory_limit_mb", 1), 1)
        ) * 100
        print(
            f"      DB: {body.get('db_storage_used_gb', 0):.2f}/{body.get('db_storage_limit_gb', 0):.0f} GB ({db_pct:.1f}%)"
        )
        print(
            f"      Redis: {body.get('redis_memory_used_mb', 0):.1f}/{body.get('redis_memory_limit_mb', 0):.0f} MB ({redis_pct:.1f}%)"
        )
        print(
            f"      Connections: {body.get('db_connections_current', 0)}/{body.get('db_connections_max', 0)}"
        )


# ----------------------------
# Main Runner
# ----------------------------


def main():
    parser = argparse.ArgumentParser(
        description="M24 Ops Console - Customer Console Test"
    )
    parser.add_argument("--endpoint", help="Run single endpoint (e.g. playbooks)")
    parser.add_argument("--json", action="store_true", help="JSON output for CI")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed results"
    )
    parser.add_argument("--api-base", help="Override API base URL")
    parser.add_argument("--api-key", help="Override API key")
    args = parser.parse_args()

    global BASE_URL, API_KEY
    if args.api_base:
        BASE_URL = args.api_base
    if args.api_key:
        API_KEY = args.api_key

    # Select endpoints to test
    targets = (
        {args.endpoint: ENDPOINTS[args.endpoint]}
        if args.endpoint and args.endpoint in ENDPOINTS
        else ENDPOINTS
    )

    results = {}
    for name, path in targets.items():
        res = call(path)
        res = assert_shape(name, res)
        results[name] = res

    # Detect empty-data state
    empty_ops_events = (
        "customers" in results
        and results["customers"].get("ok")
        and results["customers"].get("count", 0) == 0
    )

    # Check playbooks configured
    playbooks_ok = (
        "playbooks" in results
        and results["playbooks"].get("ok")
        and results["playbooks"].get("playbooks_configured", False)
    )

    all_ok = all(
        r.get("ok") and r.get("assertion") == "PASSED" for r in results.values()
    )

    # JSON output for CI
    if args.json:
        print(
            json.dumps(
                {
                    "timestamp": datetime.now().isoformat(),
                    "api_base": BASE_URL,
                    "summary": {
                        "all_ok": all_ok,
                        "empty_ops_events": empty_ops_events,
                        "playbooks_configured": playbooks_ok,
                        "endpoints_tested": len(results),
                    },
                    "results": {
                        name: {
                            "ok": r["ok"],
                            "latency_ms": r.get("latency_ms"),
                            "assertion": r.get("assertion"),
                            "count": r.get("count"),
                            "data_present": r.get("data_present", False),
                        }
                        for name, r in results.items()
                    },
                },
                indent=2,
            )
        )
        sys.exit(0 if all_ok else 1)

    # Pretty output
    print(f"\n{CYAN}{'=' * 60}{RESET}")
    print(f"{CYAN}{BOLD}  Customer Console – Ops API Test{RESET}")
    print(f"{CYAN}{'=' * 60}{RESET}")
    print(
        f"  {DIM}API: {BASE_URL}  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n"
    )

    for name, r in results.items():
        status_icon = f"{GREEN}✓{RESET}" if r["ok"] else f"{RED}✗{RESET}"
        latency = f"{r.get('latency_ms', '?')}ms"
        assertion = r.get("assertion", "—")
        assertion_color = GREEN if assertion == "PASSED" else RED

        # Count info
        count_info = ""
        if "count" in r:
            count_info = f" ({r['count']} items)"

        print(
            f"  {status_icon} {name:20s} {latency:>8s}  {assertion_color}{assertion}{RESET}{count_info}"
        )

        if args.verbose and r["ok"]:
            print_verbose(name, r)
            print()

    # Summary
    print(f"\n{CYAN}{'─' * 60}{RESET}")

    if playbooks_ok:
        print(f"  {GREEN}✓{RESET} 5 Founder Playbooks configured")
    else:
        print(f"  {YELLOW}⚠{RESET} Playbooks not fully configured")

    if empty_ops_events:
        print(f"\n  {YELLOW}⚠ ops_events table is empty{RESET}")
        print(f"  {DIM}This is EXPECTED for fresh/staging environments.{RESET}")
        print(
            f"  {DIM}At-risk customers appear after friction events are emitted:{RESET}"
        )
        print(f"  {DIM}  - SESSION_STARTED / SESSION_IDLE_TIMEOUT{RESET}")
        print(f"  {DIM}  - REPLAY_ABORTED / EXPORT_ABORTED{RESET}")
        print(f"  {DIM}  - POLICY_BLOCK_REPEAT{RESET}")
    else:
        print(f"  {GREEN}✓{RESET} ops_events data present")

    print(f"\n  {BOLD}Result: {'PASS' if all_ok else 'FAIL'}{RESET}")
    print(f"{CYAN}{'=' * 60}{RESET}\n")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
