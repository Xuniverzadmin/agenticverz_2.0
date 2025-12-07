#!/usr/bin/env python3
"""
E2E Results Parser for AOS

M8 Deliverable: Parses end-to-end integration test results and generates
summary reports for CI/CD pipelines.

Usage:
    python e2e_results_parser.py pytest_results.json
    python e2e_results_parser.py pytest_results.json --output summary.json
    python e2e_results_parser.py pytest_results.json --format markdown
    python e2e_results_parser.py pytest_results.json --github-summary

Supports:
- pytest-json-report format
- JUnit XML format
- Custom AOS E2E harness output
"""
import os
import sys
import json
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any


def parse_pytest_json(filepath: str) -> dict:
    """Parse pytest-json-report output."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    tests = []
    for test in data.get("tests", []):
        nodeid = test.get("nodeid", "")
        outcome = test.get("outcome", "unknown")
        duration = test.get("duration", 0)

        # Extract module and test name
        parts = nodeid.split("::")
        module = parts[0] if parts else ""
        test_name = parts[-1] if len(parts) > 1 else nodeid

        tests.append({
            "name": test_name,
            "nodeid": nodeid,
            "module": module,
            "outcome": outcome,
            "duration_seconds": duration,
            "call": test.get("call", {}),
            "setup": test.get("setup", {}),
            "teardown": test.get("teardown", {}),
        })

    summary = data.get("summary", {})

    return {
        "format": "pytest-json",
        "created": data.get("created", 0),
        "duration": data.get("duration", 0),
        "exitcode": data.get("exitcode", 1),
        "tests": tests,
        "summary": {
            "total": summary.get("total", len(tests)),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "error": summary.get("error", 0),
            "skipped": summary.get("skipped", 0),
        },
        "environment": data.get("environment", {}),
    }


def parse_junit_xml(filepath: str) -> dict:
    """Parse JUnit XML test results."""
    tree = ET.parse(filepath)
    root = tree.getroot()

    tests = []
    total_time = 0

    # Handle both testsuite and testsuites root
    testsuites = root.findall(".//testsuite")
    if not testsuites and root.tag == "testsuite":
        testsuites = [root]

    for testsuite in testsuites:
        suite_name = testsuite.get("name", "")

        for testcase in testsuite.findall("testcase"):
            name = testcase.get("name", "")
            classname = testcase.get("classname", "")
            time = float(testcase.get("time", 0))
            total_time += time

            # Determine outcome
            failure = testcase.find("failure")
            error = testcase.find("error")
            skipped = testcase.find("skipped")

            if failure is not None:
                outcome = "failed"
                message = failure.get("message", "")
            elif error is not None:
                outcome = "error"
                message = error.get("message", "")
            elif skipped is not None:
                outcome = "skipped"
                message = skipped.get("message", "")
            else:
                outcome = "passed"
                message = ""

            tests.append({
                "name": name,
                "nodeid": f"{classname}::{name}",
                "module": classname,
                "outcome": outcome,
                "duration_seconds": time,
                "message": message,
                "suite": suite_name,
            })

    # Calculate summary
    passed = sum(1 for t in tests if t["outcome"] == "passed")
    failed = sum(1 for t in tests if t["outcome"] == "failed")
    error = sum(1 for t in tests if t["outcome"] == "error")
    skipped = sum(1 for t in tests if t["outcome"] == "skipped")

    return {
        "format": "junit-xml",
        "created": datetime.now(timezone.utc).timestamp(),
        "duration": total_time,
        "exitcode": 1 if (failed + error) > 0 else 0,
        "tests": tests,
        "summary": {
            "total": len(tests),
            "passed": passed,
            "failed": failed,
            "error": error,
            "skipped": skipped,
        },
    }


def parse_aos_harness(filepath: str) -> dict:
    """Parse AOS custom E2E harness output."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    tests = []
    for scenario in data.get("scenarios", []):
        outcome = "passed" if scenario.get("success", False) else "failed"

        tests.append({
            "name": scenario.get("name", "unknown"),
            "nodeid": scenario.get("id", scenario.get("name", "")),
            "module": scenario.get("category", "e2e"),
            "outcome": outcome,
            "duration_seconds": scenario.get("duration_ms", 0) / 1000,
            "parity_check": scenario.get("parity_check"),
            "replay_hash": scenario.get("replay_hash"),
            "errors": scenario.get("errors", []),
        })

    passed = sum(1 for t in tests if t["outcome"] == "passed")
    failed = sum(1 for t in tests if t["outcome"] == "failed")

    return {
        "format": "aos-harness",
        "created": data.get("timestamp", datetime.now(timezone.utc).timestamp()),
        "duration": data.get("total_duration_ms", 0) / 1000,
        "exitcode": 0 if failed == 0 else 1,
        "tests": tests,
        "summary": {
            "total": len(tests),
            "passed": passed,
            "failed": failed,
            "error": 0,
            "skipped": 0,
        },
        "parity": {
            "total_replays": data.get("total_replays", 0),
            "parity_failures": data.get("parity_failures", 0),
        },
    }


def detect_format(filepath: str) -> str:
    """Detect file format based on content."""
    with open(filepath, 'r') as f:
        content = f.read(1000)  # Read first 1000 chars

    if content.strip().startswith('{'):
        # JSON file
        try:
            data = json.loads(open(filepath).read())
            if "tests" in data and "summary" in data:
                return "pytest-json"
            elif "scenarios" in data:
                return "aos-harness"
        except json.JSONDecodeError:
            pass
    elif content.strip().startswith('<?xml') or content.strip().startswith('<'):
        return "junit-xml"

    raise ValueError(f"Unknown file format: {filepath}")


def parse_results(filepath: str, format_hint: Optional[str] = None) -> dict:
    """Parse test results file."""
    if format_hint:
        fmt = format_hint
    else:
        fmt = detect_format(filepath)

    if fmt == "pytest-json":
        return parse_pytest_json(filepath)
    elif fmt == "junit-xml":
        return parse_junit_xml(filepath)
    elif fmt == "aos-harness":
        return parse_aos_harness(filepath)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def generate_summary(results: dict) -> dict:
    """Generate summary report."""
    summary = results["summary"]
    tests = results["tests"]

    failed_tests = [t for t in tests if t["outcome"] in ("failed", "error")]
    slowest_tests = sorted(tests, key=lambda t: t["duration_seconds"], reverse=True)[:5]

    # Group by module
    by_module = {}
    for test in tests:
        module = test.get("module", "unknown")
        if module not in by_module:
            by_module[module] = {"passed": 0, "failed": 0, "skipped": 0}
        outcome = test["outcome"]
        if outcome == "passed":
            by_module[module]["passed"] += 1
        elif outcome in ("failed", "error"):
            by_module[module]["failed"] += 1
        else:
            by_module[module]["skipped"] += 1

    pass_rate = (summary["passed"] / summary["total"] * 100) if summary["total"] > 0 else 0

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "format": results["format"],
        "duration_seconds": results["duration"],
        "summary": {
            **summary,
            "pass_rate_percent": pass_rate,
        },
        "failed_tests": [
            {
                "name": t["name"],
                "nodeid": t["nodeid"],
                "duration": t["duration_seconds"],
                "message": t.get("message", t.get("errors", [])),
            }
            for t in failed_tests
        ],
        "slowest_tests": [
            {
                "name": t["name"],
                "duration_seconds": t["duration_seconds"],
            }
            for t in slowest_tests
        ],
        "by_module": by_module,
        "parity": results.get("parity"),
    }


def format_markdown(summary: dict) -> str:
    """Format summary as Markdown."""
    lines = []
    lines.append("# E2E Test Results\n")
    lines.append(f"**Timestamp:** {summary['timestamp']}\n")
    lines.append(f"**Duration:** {summary['duration_seconds']:.2f}s\n")
    lines.append("")

    s = summary["summary"]
    status_emoji = "✅" if s["failed"] == 0 else "❌"
    lines.append(f"## Summary {status_emoji}\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total | {s['total']} |")
    lines.append(f"| Passed | {s['passed']} |")
    lines.append(f"| Failed | {s['failed']} |")
    lines.append(f"| Skipped | {s['skipped']} |")
    lines.append(f"| Pass Rate | {s['pass_rate_percent']:.1f}% |")
    lines.append("")

    if summary.get("parity"):
        parity = summary["parity"]
        lines.append("## Parity Check\n")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Replays | {parity.get('total_replays', 0)} |")
        lines.append(f"| Parity Failures | {parity.get('parity_failures', 0)} |")
        lines.append("")

    if summary["failed_tests"]:
        lines.append("## Failed Tests\n")
        for test in summary["failed_tests"]:
            lines.append(f"### ❌ {test['name']}")
            lines.append(f"- **Node:** `{test['nodeid']}`")
            lines.append(f"- **Duration:** {test['duration']:.2f}s")
            if test.get("message"):
                msg = test["message"]
                if isinstance(msg, list):
                    msg = "\n".join(msg)
                lines.append(f"- **Error:**")
                lines.append(f"```")
                lines.append(str(msg)[:500])  # Truncate long messages
                lines.append(f"```")
            lines.append("")

    if summary["slowest_tests"]:
        lines.append("## Slowest Tests\n")
        lines.append(f"| Test | Duration |")
        lines.append(f"|------|----------|")
        for test in summary["slowest_tests"]:
            lines.append(f"| {test['name']} | {test['duration_seconds']:.2f}s |")
        lines.append("")

    if summary["by_module"]:
        lines.append("## Results by Module\n")
        lines.append(f"| Module | Passed | Failed | Skipped |")
        lines.append(f"|--------|--------|--------|---------|")
        for module, counts in summary["by_module"].items():
            lines.append(f"| {module} | {counts['passed']} | {counts['failed']} | {counts['skipped']} |")
        lines.append("")

    return "\n".join(lines)


def format_github_summary(summary: dict) -> str:
    """Format summary for GitHub Actions job summary."""
    s = summary["summary"]
    status = "success" if s["failed"] == 0 else "failure"

    lines = []
    lines.append(f"### E2E Test Results: {status.upper()}")
    lines.append("")
    lines.append(f"**{s['passed']}/{s['total']}** tests passed ({s['pass_rate_percent']:.1f}%)")
    lines.append("")

    if s["failed"] > 0:
        lines.append("<details>")
        lines.append("<summary>Failed Tests</summary>")
        lines.append("")
        for test in summary["failed_tests"]:
            lines.append(f"- `{test['nodeid']}`")
        lines.append("")
        lines.append("</details>")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Parse E2E test results and generate summary reports"
    )
    parser.add_argument(
        "results_file",
        help="Path to test results file"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["pytest-json", "junit-xml", "aos-harness", "auto"],
        default="auto",
        help="Input file format"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for summary"
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "markdown", "text"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--github-summary",
        action="store_true",
        help="Write GitHub Actions job summary"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any test failed"
    )

    args = parser.parse_args()

    # Parse results
    try:
        format_hint = None if args.format == "auto" else args.format
        results = parse_results(args.results_file, format_hint)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate summary
    summary = generate_summary(results)

    # Output
    if args.output_format == "json":
        output = json.dumps(summary, indent=2)
    elif args.output_format == "markdown":
        output = format_markdown(summary)
    else:
        # Text output
        s = summary["summary"]
        output = f"""E2E Test Results
================
Total:      {s['total']}
Passed:     {s['passed']}
Failed:     {s['failed']}
Skipped:    {s['skipped']}
Pass Rate:  {s['pass_rate_percent']:.1f}%
Duration:   {summary['duration_seconds']:.2f}s
"""
        if summary["failed_tests"]:
            output += "\nFailed Tests:\n"
            for test in summary["failed_tests"]:
                output += f"  - {test['nodeid']}\n"

    print(output)

    # Write output file
    if args.output:
        with open(args.output, 'w') as f:
            if args.output_format == "json":
                f.write(output)
            else:
                f.write(output)
        print(f"\nSummary saved to: {args.output}", file=sys.stderr)

    # GitHub Actions summary
    if args.github_summary:
        github_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if github_summary_file:
            with open(github_summary_file, 'a') as f:
                f.write(format_github_summary(summary))
                f.write("\n")
            print("GitHub summary written", file=sys.stderr)
        else:
            print(format_github_summary(summary))

    # Exit code
    if args.strict and summary["summary"]["failed"] > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
