#!/usr/bin/env python3
"""
Metrics Validation Script - Validates Prometheus metrics endpoint.

Ensures observability does not regress by checking:
- /metrics endpoint is reachable
- Required metric names exist
- Metric types are correct

Usage:
    python scripts/ops/metrics_validation.py [--url http://localhost:8000]

Exit codes:
    0 - All metrics checks passed
    1 - Metrics validation failed
"""

import argparse
import sys
import requests
from typing import List, Tuple

# Required metrics for M10-M19+
REQUIRED_METRICS = [
    # Core runtime metrics
    ("nova_runs_total", "counter", "Total runs created"),
    ("nova_run_duration_seconds", "histogram", "Run execution duration"),
    ("nova_skills_executed_total", "counter", "Total skill executions"),
    # Worker metrics
    ("nova_worker_pool_size", "gauge", "Worker pool size"),
    ("nova_worker_active_runs", "gauge", "Active runs in worker"),
    # M10 Recovery metrics
    ("nova_recovery_candidates_total", "counter", "Recovery candidates created"),
    ("nova_distributed_locks_held", "gauge", "Distributed locks held"),
    # Budget/Cost metrics
    ("nova_budget_consumed_total", "counter", "Budget consumed"),
    ("nova_cost_simulation_total", "counter", "Cost simulations run"),
    # M17 CARE Routing metrics (if available)
    ("nova_routing_decisions_total", "counter", "Routing decisions made"),
    # M18 Governor metrics (if available)
    ("nova_governor_adjustments_total", "counter", "Governor adjustments"),
    # M19 Policy metrics (if available)
    ("nova_policy_evaluations_total", "counter", "Policy evaluations"),
]

# Metrics that should exist but are optional (won't fail CI)
OPTIONAL_METRICS = [
    ("nova_agent_reputation_score", "gauge", "Agent reputation scores"),
    ("nova_sba_validations_total", "counter", "SBA validations"),
    ("nova_drift_signals_total", "counter", "Drift signals detected"),
]


def fetch_metrics(url: str) -> str:
    """Fetch metrics from endpoint."""
    try:
        response = requests.get(f"{url}/metrics", timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        return None


def parse_metric_names(metrics_text: str) -> set:
    """Extract metric names from Prometheus format."""
    names = set()
    for line in metrics_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Metric line format: metric_name{labels} value
        # or: metric_name value
        name = line.split("{")[0].split(" ")[0]
        if name:
            names.add(name)
    return names


def check_required_metrics(metrics_text: str) -> Tuple[List[str], List[str]]:
    """Check required metrics exist."""
    existing = parse_metric_names(metrics_text)
    errors = []
    warnings = []

    for metric_name, metric_type, description in REQUIRED_METRICS:
        # Check base name and common suffixes
        found = False
        suffixes = ["", "_total", "_count", "_sum", "_bucket", "_created"]

        for suffix in suffixes:
            if f"{metric_name}{suffix}" in existing:
                found = True
                break
            # Also check without _total if it's a counter
            if metric_type == "counter" and metric_name.endswith("_total"):
                base = metric_name[:-6]  # Remove _total
                if f"{base}{suffix}" in existing:
                    found = True
                    break

        if not found:
            errors.append(f"Missing required metric: {metric_name} ({description})")

    for metric_name, metric_type, description in OPTIONAL_METRICS:
        found = any(metric_name in name for name in existing)
        if not found:
            warnings.append(f"Missing optional metric: {metric_name} ({description})")

    return errors, warnings


def check_metric_types(metrics_text: str) -> List[str]:
    """Verify metric types from TYPE comments."""
    errors = []
    type_map = {}

    for line in metrics_text.split("\n"):
        if line.startswith("# TYPE "):
            parts = line[7:].split(" ")
            if len(parts) >= 2:
                type_map[parts[0]] = parts[1]

    for metric_name, expected_type, _ in REQUIRED_METRICS:
        if metric_name in type_map:
            actual_type = type_map[metric_name]
            if actual_type != expected_type:
                errors.append(
                    f"Metric type mismatch: {metric_name} "
                    f"(expected {expected_type}, got {actual_type})"
                )

    return errors


def run_validation(url: str) -> dict:
    """Run full metrics validation."""
    results = {
        "url": url,
        "reachable": False,
        "errors": [],
        "warnings": [],
        "metrics_count": 0,
        "passed": False,
    }

    # Fetch metrics
    metrics_text = fetch_metrics(url)

    if metrics_text is None:
        results["errors"].append(f"Cannot reach metrics endpoint at {url}/metrics")
        return results

    results["reachable"] = True
    results["metrics_count"] = len(parse_metric_names(metrics_text))

    # Check required metrics
    errors, warnings = check_required_metrics(metrics_text)
    results["errors"].extend(errors)
    results["warnings"].extend(warnings)

    # Check metric types
    type_errors = check_metric_types(metrics_text)
    results["errors"].extend(type_errors)

    results["passed"] = len(results["errors"]) == 0
    return results


def main():
    parser = argparse.ArgumentParser(description="Validate Prometheus metrics endpoint")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Base URL of the service"
    )
    parser.add_argument("--strict", action="store_true", help="Fail on warnings too")
    args = parser.parse_args()

    print("=" * 60)
    print("Metrics Validation - Observability Check")
    print("=" * 60)
    print(f"URL: {args.url}")
    print()

    results = run_validation(args.url)

    # Print results
    if results["reachable"]:
        print("[PASS] Metrics endpoint reachable")
        print(f"       Found {results['metrics_count']} metrics")
    else:
        print("[FAIL] Metrics endpoint not reachable")

    print()

    if results["errors"]:
        print("Errors:")
        for error in results["errors"]:
            print(f"  [FAIL] {error}")
    else:
        print("[PASS] All required metrics present")

    if results["warnings"]:
        print()
        print("Warnings (optional metrics):")
        for warning in results["warnings"]:
            print(f"  [WARN] {warning}")

    print()
    print("=" * 60)

    if results["passed"]:
        print("Metrics Validation: PASSED")
        return 0
    else:
        print("Metrics Validation: FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
