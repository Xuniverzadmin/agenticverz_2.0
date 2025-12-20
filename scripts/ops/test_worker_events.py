#!/usr/bin/env python3
"""
Worker Event Validation Script

Tests drift/recovery/policy events by sending crafted requests
to the Business Builder worker endpoint.

Usage:
    python3 scripts/ops/test_worker_events.py --test policy_violation
    python3 scripts/ops/test_worker_events.py --test all
"""

import argparse
import json
import os
import sys
import httpx
from typing import Optional

# Configuration
API_BASE = os.getenv("AOS_API_BASE", "http://localhost:8000")
API_KEY = os.getenv("AOS_API_KEY", "edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf")
ENDPOINT = f"{API_BASE}/api/v1/workers/business-builder/run-streaming"

# Test scenarios
TEST_SCENARIOS = {
    "policy_violation": {
        "description": "Brand with forbidden claims to trigger policy_violation",
        "task": "Create compelling marketing copy",
        "brand": {
            "company_name": "MegaCorp AI",
            "mission": "We deliver the world's best AI with guaranteed results",
            "value_proposition": "Our 100% accurate predictions are completely risk-free for your enterprise",
            "target_audience": ["b2b_enterprise"],
            "tone": {"primary": "professional"},
            "forbidden_claims": [
                {"pattern": "world's best", "reason": "Unverifiable superlative", "severity": "error"},
                {"pattern": "guaranteed results", "reason": "Cannot guarantee outcomes", "severity": "error"},
                {"pattern": "100% accurate", "reason": "Unverifiable accuracy", "severity": "error"},
                {"pattern": "risk-free", "reason": "All investments carry risk", "severity": "warning"},
            ],
        },
        "expected_events": ["policy_violation", "policy_check"],
    },
    "drift_contradiction": {
        "description": "Luxury brand with casual task to trigger drift_detected",
        "task": "Write super casual copy with lots of slang, emojis, and Gen Z vibes. Make it fun and quirky!",
        "brand": {
            "company_name": "LuxuryTech Elite",
            "mission": "Exclusive premium technology solutions for discerning enterprises",
            "value_proposition": "Bespoke white-glove enterprise solutions with unparalleled sophistication and elegance",
            "tagline": "Excellence Redefined",
            "target_audience": ["b2b_enterprise"],
            "tone": {
                "primary": "luxury",
                "avoid": ["casual"],
                "examples_good": ["curated experience", "bespoke solutions", "distinguished clientele"],
                "examples_bad": ["cheap", "budget", "basic", "easy", "slang"],
            },
        },
        "expected_events": ["drift_detected"],
    },
    "budget_exceeded": {
        "description": "Minimal budget with complex task to trigger budget failure",
        "task": "Create a comprehensive 20-page marketing strategy with full competitive analysis, 100 headline variations, detailed UX specifications, and complete brand guidelines",
        "brand": {
            "company_name": "BudgetTest Inc",
            "mission": "Testing budget constraints in the worker pipeline system",
            "value_proposition": "Minimal budget allocation to force constraint violations and recovery",
            "target_audience": ["b2b_smb"],
            "tone": {"primary": "professional"},
            "budget_tokens": 1000,
        },
        "expected_events": ["failure_detected", "recovery_started"],
    },
    "valid_professional": {
        "description": "Valid professional brand (baseline)",
        "task": "Create a landing page hero section with compelling copy",
        "brand": {
            "company_name": "TechStartup AI",
            "mission": "Making AI accessible to every business through simple powerful tools",
            "value_proposition": "AI-powered solutions that save businesses time and money while being easy to use",
            "tagline": "AI Made Simple",
            "target_audience": ["b2b_smb"],
            "tone": {"primary": "professional"},
        },
        "expected_events": ["run_completed"],
    },
    "valid_casual": {
        "description": "Valid casual brand for B2C",
        "task": "Create a fun app onboarding flow",
        "brand": {
            "company_name": "FunApp",
            "mission": "Making everyday tasks enjoyable through delightful mobile experiences",
            "value_proposition": "A friendly app that turns boring chores into fun activities",
            "tagline": "Life's too short for boring apps",
            "target_audience": ["b2c_consumer"],
            "tone": {"primary": "casual"},
        },
        "expected_events": ["run_completed"],
    },
    "valid_luxury": {
        "description": "Valid luxury brand for enterprise",
        "task": "Design an exclusive client portal experience",
        "brand": {
            "company_name": "Prestige Partners",
            "mission": "Curating exceptional investment opportunities for distinguished clients",
            "value_proposition": "Bespoke wealth management with white-glove service and unparalleled discretion",
            "tagline": "Where Excellence Meets Exclusivity",
            "target_audience": ["b2b_enterprise"],
            "tone": {"primary": "luxury"},
        },
        "expected_events": ["run_completed"],
    },
    "valid_formal": {
        "description": "Valid formal brand for enterprise",
        "task": "Create compliance documentation landing page",
        "brand": {
            "company_name": "Compliance Corp",
            "mission": "Ensuring regulatory compliance through systematic documentation and audit trails",
            "value_proposition": "Enterprise compliance management with comprehensive audit capabilities and regulatory alignment",
            "target_audience": ["b2b_enterprise"],
            "tone": {"primary": "formal"},
        },
        "expected_events": ["run_completed"],
    },
    "valid_developer": {
        "description": "Valid neutral brand for developers",
        "task": "Create API documentation landing page",
        "brand": {
            "company_name": "DevTools API",
            "mission": "Building developer tools that integrate seamlessly into existing workflows",
            "value_proposition": "Clean APIs with excellent documentation and predictable behavior",
            "target_audience": ["b2b_developer"],
            "tone": {"primary": "neutral"},
        },
        "expected_events": ["run_completed"],
    },
}


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_event(event_type: str, data: dict, is_expected: bool):
    """Print an SSE event with formatting."""
    marker = "✅" if is_expected else "📨"
    color = "\033[92m" if is_expected else "\033[94m"
    reset = "\033[0m"
    print(f"{color}{marker} [{event_type}]{reset}")
    if data:
        # Print key fields only
        for key in ["stage_id", "agent", "message", "error", "drift_score", "policy", "passed", "pattern", "severity"]:
            if key in data:
                print(f"   {key}: {data[key]}")


def run_test(test_name: str, scenario: dict) -> dict:
    """Run a single test scenario and collect events."""
    print_header(f"Test: {test_name}")
    print(f"Description: {scenario['description']}")
    print(f"Task: {scenario['task'][:60]}...")
    print(f"Expected events: {scenario['expected_events']}")
    print()

    request_body = {
        "task": scenario["task"],
        "brand": scenario["brand"],
    }

    headers = {
        "Content-Type": "application/json",
        "X-AOS-Key": API_KEY,
    }

    collected_events = []
    found_expected = {e: False for e in scenario["expected_events"]}

    try:
        # Step 1: POST to start the run (returns 202 with run_id)
        print("📤 Starting worker run...")
        response = httpx.post(ENDPOINT, json=request_body, headers=headers, timeout=30.0)

        if response.status_code not in (200, 202):
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Error: {response.text[:300]}")
            return {"success": False, "error": f"HTTP {response.status_code}"}

        result = response.json()
        run_id = result.get("run_id")
        if not run_id:
            print(f"❌ No run_id in response: {result}")
            return {"success": False, "error": "No run_id"}

        print(f"✅ Run started: {run_id}")

        # Step 2: Connect to SSE stream
        stream_url = f"{API_BASE}/api/v1/workers/business-builder/stream/{run_id}"
        print(f"📡 Connecting to SSE stream: {stream_url}\n")

        with httpx.stream("GET", stream_url, timeout=120.0) as sse_response:
            if sse_response.status_code != 200:
                print(f"❌ SSE stream failed with status {sse_response.status_code}")
                return {"success": False, "error": f"SSE HTTP {sse_response.status_code}"}

            print("📡 SSE Stream connected\n")

            for line in sse_response.iter_lines():
                if not line:
                    continue

                # SSE format: "data: {...}" or "event: type\ndata: {...}"
                if line.startswith("data: "):
                    try:
                        event_data = json.loads(line[6:])
                        event_type = event_data.get("type", "unknown")
                        data = event_data.get("data", {})

                        collected_events.append(event_type)

                        # Check if this is an expected event
                        is_expected = event_type in scenario["expected_events"]
                        if is_expected:
                            found_expected[event_type] = True

                        # Print important events
                        if event_type in ["run_started", "run_completed", "run_failed",
                                         "stage_failed", "policy_violation", "policy_check",
                                         "drift_detected", "failure_detected",
                                         "recovery_started", "recovery_completed"]:
                            print_event(event_type, data, is_expected)

                        if event_type == "run_completed":
                            print(f"\n✅ Run completed successfully")
                            break
                        elif event_type == "run_failed":
                            print(f"\n❌ Run failed: {data.get('error', 'unknown')}")
                            break
                        elif event_type == "stream_end":
                            print(f"\n📡 Stream ended")
                            break

                    except json.JSONDecodeError:
                        pass

    except httpx.TimeoutException:
        print("❌ Request timed out")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

    # Summary
    print(f"\n--- Results ---")
    print(f"Total events: {len(collected_events)}")
    print(f"Event types: {set(collected_events)}")

    all_found = all(found_expected.values())
    for event, found in found_expected.items():
        status = "✅" if found else "❌"
        print(f"{status} Expected '{event}': {'found' if found else 'NOT FOUND'}")

    return {
        "success": all_found,
        "events": collected_events,
        "found_expected": found_expected,
    }


def main():
    parser = argparse.ArgumentParser(description="Test Worker Events")
    parser.add_argument("--test", type=str, default="valid_professional",
                       choices=list(TEST_SCENARIOS.keys()) + ["all", "risk1", "risk3"],
                       help="Test scenario to run")
    parser.add_argument("--api-base", type=str, default=None,
                       help="API base URL (default: localhost:8000)")
    parser.add_argument("--api-key", type=str, default=None,
                       help="API key")

    args = parser.parse_args()

    global API_BASE, API_KEY, ENDPOINT
    if args.api_base:
        API_BASE = args.api_base
        ENDPOINT = f"{API_BASE}/api/v1/workers/business-builder/run-streaming"
    if args.api_key:
        API_KEY = args.api_key

    print_header("Worker Event Validation")
    print(f"API Base: {API_BASE}")
    print(f"Endpoint: {ENDPOINT}")

    # Select tests to run
    if args.test == "all":
        tests = list(TEST_SCENARIOS.keys())
    elif args.test == "risk1":
        tests = ["policy_violation", "drift_contradiction", "budget_exceeded"]
    elif args.test == "risk3":
        tests = ["valid_professional", "valid_casual", "valid_luxury", "valid_formal", "valid_developer"]
    else:
        tests = [args.test]

    results = {}
    for test_name in tests:
        scenario = TEST_SCENARIOS[test_name]
        results[test_name] = run_test(test_name, scenario)
        print()

    # Final summary
    print_header("Final Summary")
    passed = sum(1 for r in results.values() if r.get("success"))
    total = len(results)
    print(f"Passed: {passed}/{total}")

    for test_name, result in results.items():
        status = "✅" if result.get("success") else "❌"
        print(f"{status} {test_name}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
