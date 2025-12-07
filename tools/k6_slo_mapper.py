#!/usr/bin/env python3
"""
k6 SLO Mapper for AOS

M8 Deliverable: Maps k6 load test results to SLO compliance status.
Parses k6 JSON output and checks against defined SLOs.

Usage:
    python k6_slo_mapper.py load-tests/results/k6_results.json
    python k6_slo_mapper.py k6_results.json --output slo_report.json
    python k6_slo_mapper.py k6_results.json --strict  # Exit 1 if any SLO breached

SLOs (M8):
- p95 latency < 500ms for /simulate
- Error rate < 1%
- Availability > 99.5%
- Replay parity failures < 0.1%
"""
import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# SLO Definitions
SLOS = {
    "simulate_p95_latency_ms": {
        "threshold": 500,
        "operator": "lt",
        "description": "p95 latency for /simulate endpoint",
        "unit": "ms",
        "severity": "critical",
    },
    "simulate_p99_latency_ms": {
        "threshold": 1000,
        "operator": "lt",
        "description": "p99 latency for /simulate endpoint",
        "unit": "ms",
        "severity": "warning",
    },
    "error_rate_percent": {
        "threshold": 1.0,
        "operator": "lt",
        "description": "Overall error rate",
        "unit": "%",
        "severity": "critical",
    },
    "availability_percent": {
        "threshold": 99.5,
        "operator": "gt",
        "description": "Service availability",
        "unit": "%",
        "severity": "critical",
    },
    "parity_failure_percent": {
        "threshold": 0.1,
        "operator": "lt",
        "description": "Replay parity failure rate",
        "unit": "%",
        "severity": "warning",
    },
}


def parse_k6_json(filepath: str) -> dict:
    """
    Parse k6 JSON output file.

    k6 outputs JSON-lines format when using --out json=file.json
    Each line is a separate metric point.
    """
    metrics = {
        "http_req_duration": [],
        "http_req_failed": [],
        "checks": [],
        "iterations": 0,
        "vus_max": 0,
        "data_received": 0,
        "data_sent": 0,
    }

    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                metric_type = data.get("type")
                metric_name = data.get("metric")

                if metric_type == "Point":
                    value = data.get("data", {}).get("value", 0)

                    if metric_name == "http_req_duration":
                        metrics["http_req_duration"].append(value)
                    elif metric_name == "http_req_failed":
                        metrics["http_req_failed"].append(value)
                    elif metric_name == "checks":
                        metrics["checks"].append(value)
                    elif metric_name == "iterations":
                        metrics["iterations"] += 1
                    elif metric_name == "vus_max":
                        metrics["vus_max"] = max(metrics["vus_max"], int(value))
                    elif metric_name == "data_received":
                        metrics["data_received"] += value
                    elif metric_name == "data_sent":
                        metrics["data_sent"] += value

                elif metric_type == "Metric":
                    # End summary metrics
                    if metric_name == "iterations":
                        contains = data.get("data", {}).get("contains")
                        if contains == "default":
                            metrics["iterations"] = data.get("data", {}).get("value", metrics["iterations"])

    except FileNotFoundError:
        raise FileNotFoundError(f"k6 results file not found: {filepath}")

    return metrics


def calculate_percentile(values: list, percentile: float) -> float:
    """Calculate percentile of a list of values."""
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    index = min(index, len(sorted_values) - 1)
    return sorted_values[index]


def extract_slo_metrics(raw_metrics: dict) -> dict:
    """Extract SLO-relevant metrics from raw k6 data."""
    durations = raw_metrics.get("http_req_duration", [])
    failures = raw_metrics.get("http_req_failed", [])
    checks = raw_metrics.get("checks", [])

    total_requests = len(durations)
    failed_requests = sum(1 for f in failures if f > 0)

    # Calculate percentiles
    p50 = calculate_percentile(durations, 50)
    p95 = calculate_percentile(durations, 95)
    p99 = calculate_percentile(durations, 99)

    # Calculate rates
    error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
    availability = 100 - error_rate

    # Check parity (from custom checks if available)
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c > 0)
    parity_failure = ((total_checks - passed_checks) / total_checks * 100) if total_checks > 0 else 0

    return {
        "simulate_p50_latency_ms": p50,
        "simulate_p95_latency_ms": p95,
        "simulate_p99_latency_ms": p99,
        "error_rate_percent": error_rate,
        "availability_percent": availability,
        "parity_failure_percent": parity_failure,
        "total_requests": total_requests,
        "failed_requests": failed_requests,
        "iterations": raw_metrics.get("iterations", 0),
        "vus_max": raw_metrics.get("vus_max", 0),
    }


def evaluate_slo(metric_value: float, slo: dict) -> dict:
    """Evaluate a single SLO."""
    threshold = slo["threshold"]
    operator = slo["operator"]

    if operator == "lt":
        passed = metric_value < threshold
    elif operator == "gt":
        passed = metric_value > threshold
    elif operator == "lte":
        passed = metric_value <= threshold
    elif operator == "gte":
        passed = metric_value >= threshold
    elif operator == "eq":
        passed = metric_value == threshold
    else:
        passed = False

    margin = abs(metric_value - threshold)
    margin_percent = (margin / threshold * 100) if threshold != 0 else 0

    return {
        "passed": passed,
        "value": metric_value,
        "threshold": threshold,
        "operator": operator,
        "description": slo["description"],
        "unit": slo["unit"],
        "severity": slo["severity"],
        "margin": margin,
        "margin_percent": margin_percent,
    }


def generate_slo_report(metrics: dict) -> dict:
    """Generate full SLO compliance report."""
    results = {}
    all_passed = True
    critical_breach = False

    for slo_name, slo_config in SLOS.items():
        if slo_name in metrics:
            result = evaluate_slo(metrics[slo_name], slo_config)
            results[slo_name] = result

            if not result["passed"]:
                all_passed = False
                if result["severity"] == "critical":
                    critical_breach = True

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "all_passed": all_passed,
            "critical_breach": critical_breach,
            "total_slos": len(results),
            "passed_slos": sum(1 for r in results.values() if r["passed"]),
            "failed_slos": sum(1 for r in results.values() if not r["passed"]),
        },
        "metrics": {
            "total_requests": metrics.get("total_requests", 0),
            "failed_requests": metrics.get("failed_requests", 0),
            "iterations": metrics.get("iterations", 0),
            "vus_max": metrics.get("vus_max", 0),
            "p50_latency_ms": metrics.get("simulate_p50_latency_ms", 0),
            "p95_latency_ms": metrics.get("simulate_p95_latency_ms", 0),
            "p99_latency_ms": metrics.get("simulate_p99_latency_ms", 0),
        },
        "slo_results": results,
    }


def print_report(report: dict, verbose: bool = False) -> None:
    """Print human-readable SLO report."""
    summary = report["summary"]
    metrics = report["metrics"]

    print("=" * 60)
    print("AOS SLO Compliance Report")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print()

    print("Test Metrics:")
    print(f"  Total Requests: {metrics['total_requests']}")
    print(f"  Failed Requests: {metrics['failed_requests']}")
    print(f"  Max VUs: {metrics['vus_max']}")
    print(f"  p50 Latency: {metrics['p50_latency_ms']:.2f}ms")
    print(f"  p95 Latency: {metrics['p95_latency_ms']:.2f}ms")
    print(f"  p99 Latency: {metrics['p99_latency_ms']:.2f}ms")
    print()

    print("SLO Results:")
    print("-" * 60)

    for slo_name, result in report["slo_results"].items():
        status = "PASS" if result["passed"] else "FAIL"
        status_icon = "✓" if result["passed"] else "✗"
        severity_tag = f"[{result['severity'].upper()}]" if not result["passed"] else ""

        print(f"  {status_icon} {status} {severity_tag} {result['description']}")
        print(f"       Value: {result['value']:.2f}{result['unit']} "
              f"(threshold: {result['operator']} {result['threshold']}{result['unit']})")

        if verbose and not result["passed"]:
            print(f"       Margin: {result['margin']:.2f}{result['unit']} "
                  f"({result['margin_percent']:.1f}% beyond threshold)")
        print()

    print("-" * 60)
    print(f"Summary: {summary['passed_slos']}/{summary['total_slos']} SLOs passed")

    if summary["critical_breach"]:
        print("⚠️  CRITICAL SLO BREACH DETECTED")
    elif not summary["all_passed"]:
        print("⚠️  Some SLOs not met (non-critical)")
    else:
        print("✓ All SLOs met")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Map k6 load test results to SLO compliance"
    )
    parser.add_argument(
        "results_file",
        help="Path to k6 JSON results file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for JSON report"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any SLO is breached"
    )
    parser.add_argument(
        "--critical-only",
        action="store_true",
        help="Only fail on critical SLO breaches (with --strict)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including margins"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output only JSON (no human-readable)"
    )

    args = parser.parse_args()

    # Parse k6 results
    try:
        raw_metrics = parse_k6_json(args.results_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract SLO metrics
    metrics = extract_slo_metrics(raw_metrics)

    # Generate report
    report = generate_slo_report(metrics)

    # Output
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report, verbose=args.verbose)

    # Write output file
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        if not args.json:
            print(f"\nReport saved to: {args.output}")

    # Exit code handling
    if args.strict:
        if args.critical_only:
            if report["summary"]["critical_breach"]:
                sys.exit(1)
        else:
            if not report["summary"]["all_passed"]:
                sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
