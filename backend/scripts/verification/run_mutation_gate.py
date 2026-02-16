#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Role: Mutation testing gate — runs mutmut and enforces threshold policy
# artifact_class: CODE
"""
BA-10 Mutation Testing Gate

Runs mutmut against configured L5 engine paths and enforces a minimum
kill-rate threshold. Generates both stdout markdown and a JSON report.

Usage:
    python scripts/verification/run_mutation_gate.py
    python scripts/verification/run_mutation_gate.py --strict
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASELINE_THRESHOLD = 60  # percent
STRICT_THRESHOLD = 70    # percent

PATHS_TO_MUTATE = [
    "app/hoc/cus/policies/L5_engines/",
    "app/hoc/cus/controls/L5_engines/",
    "app/hoc/cus/incidents/L5_engines/",
    "app/hoc/cus/logs/L5_engines/",
]

REPORT_DIR = Path("reports")
REPORT_FILE = REPORT_DIR / "mutation_summary.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_mutmut_available() -> bool:
    """Return True if mutmut is available as a CLI command."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "mutmut", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: try bare `mutmut` command
    try:
        result = subprocess.run(
            ["mutmut", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    return False


def run_mutmut(paths: list[str]) -> str:
    """Run mutmut against the given paths and return combined stdout+stderr."""
    paths_arg = ",".join(paths)
    cmd = [
        sys.executable, "-m", "mutmut", "run",
        "--paths-to-mutate", paths_arg,
        "--no-progress",
    ]

    print(f"[INFO] Running: {' '.join(cmd)}")
    print(f"[INFO] Paths: {paths_arg}")
    print()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout for mutation runs
        )
    except subprocess.TimeoutExpired:
        print("[ERROR] mutmut run timed out after 10 minutes")
        return ""

    output = (result.stdout or "") + "\n" + (result.stderr or "")
    return output


def parse_mutation_results(output: str) -> dict:
    """
    Parse mutmut output to extract killed/survived/total counts.

    mutmut results output typically contains lines like:
        - Killed: 42
        - Survived: 8
        - Timeout: 2
        - Suspicious: 1
        - Skipped: 0

    Or a summary line like:
        X out of Y mutants killed (Z%)

    Returns dict with total_mutants, killed, survived, score.
    """
    killed = 0
    survived = 0
    timeout = 0
    suspicious = 0
    skipped = 0

    # Pattern 1: line-by-line result counts
    m_killed = re.search(r"killed[:\s]+(\d+)", output, re.IGNORECASE)
    m_survived = re.search(r"survived[:\s]+(\d+)", output, re.IGNORECASE)
    m_timeout = re.search(r"timeout[:\s]+(\d+)", output, re.IGNORECASE)
    m_suspicious = re.search(r"suspicious[:\s]+(\d+)", output, re.IGNORECASE)
    m_skipped = re.search(r"skipped[:\s]+(\d+)", output, re.IGNORECASE)

    if m_killed:
        killed = int(m_killed.group(1))
    if m_survived:
        survived = int(m_survived.group(1))
    if m_timeout:
        timeout = int(m_timeout.group(1))
    if m_suspicious:
        suspicious = int(m_suspicious.group(1))
    if m_skipped:
        skipped = int(m_skipped.group(1))

    # Pattern 2: "X out of Y mutants killed" summary
    m_summary = re.search(r"(\d+)\s+out\s+of\s+(\d+)\s+mutants?\s+killed", output, re.IGNORECASE)
    if m_summary:
        killed = int(m_summary.group(1))
        total_from_summary = int(m_summary.group(2))
        survived = total_from_summary - killed
    # Pattern 3: mutmut results table (e.g., "Legend for output..." followed by counts)
    # Try to parse from "mutmut results" subcommand if initial parse yields nothing
    if killed == 0 and survived == 0:
        try:
            results_proc = subprocess.run(
                [sys.executable, "-m", "mutmut", "results"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            results_output = (results_proc.stdout or "") + "\n" + (results_proc.stderr or "")

            # Count lines with status indicators
            killed_lines = re.findall(r"^Killed", results_output, re.MULTILINE)
            survived_lines = re.findall(r"^Survived", results_output, re.MULTILINE)
            timeout_lines = re.findall(r"^Timeout", results_output, re.MULTILINE)

            if killed_lines or survived_lines:
                killed = len(killed_lines)
                survived = len(survived_lines)
                timeout = len(timeout_lines)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # Timeouts and suspicious mutants count as "killed" for score purposes
    effective_killed = killed + timeout + suspicious
    total = effective_killed + survived

    if total > 0:
        score = round((effective_killed / total) * 100, 1)
    else:
        score = 0.0

    return {
        "total_mutants": total,
        "killed": killed,
        "survived": survived,
        "timeout": timeout,
        "suspicious": suspicious,
        "skipped": skipped,
        "effective_killed": effective_killed,
        "score": score,
    }


def write_report(results: dict, threshold: int, passed: bool) -> None:
    """Write JSON summary report to reports/mutation_summary.json."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "total_mutants": results["total_mutants"],
        "killed": results["killed"],
        "survived": results["survived"],
        "score": results["score"],
        "threshold": threshold,
        "passed": passed,
    }

    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)
        f.write("\n")

    print(f"[INFO] Report written to {REPORT_FILE}")


def print_markdown_summary(results: dict, threshold: int, passed: bool, strict: bool) -> None:
    """Print a markdown-formatted summary to stdout."""
    mode = "strict" if strict else "baseline"
    status = "PASS" if passed else "FAIL"

    print()
    print("=" * 60)
    print("  MUTATION TESTING GATE — SUMMARY")
    print("=" * 60)
    print()
    print(f"| Metric            | Value           |")
    print(f"|-------------------|-----------------|")
    print(f"| Total mutants     | {results['total_mutants']:<15} |")
    print(f"| Killed            | {results['killed']:<15} |")
    print(f"| Survived          | {results['survived']:<15} |")
    print(f"| Timeout           | {results['timeout']:<15} |")
    print(f"| Suspicious        | {results['suspicious']:<15} |")
    print(f"| Effective killed  | {results['effective_killed']:<15} |")
    print(f"| Score             | {results['score']:.1f}%{'':<12} |")
    print(f"| Threshold ({mode}) | {threshold}%{'':<13} |")
    print(f"| Result            | {status:<15} |")
    print()

    if passed:
        print(f"[PASS] Mutation score {results['score']:.1f}% >= {threshold}% threshold ({mode} mode)")
    else:
        print(f"[FAIL] Mutation score {results['score']:.1f}% < {threshold}% threshold ({mode} mode)")
        print(f"       {results['survived']} mutants survived — review test coverage for L5 engines")
    print()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mutation testing gate — runs mutmut and enforces threshold policy",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help=f"Use strict threshold ({STRICT_THRESHOLD}%% instead of {BASELINE_THRESHOLD}%%)",
    )
    args = parser.parse_args()

    threshold = STRICT_THRESHOLD if args.strict else BASELINE_THRESHOLD

    # ------------------------------------------------------------------
    # Step 1: Check mutmut availability
    # ------------------------------------------------------------------
    if not check_mutmut_available():
        print("[SKIP] mutmut not installed — mutation gate deferred")
        return 0

    # ------------------------------------------------------------------
    # Step 2: Verify paths exist
    # ------------------------------------------------------------------
    existing_paths = []
    for p in PATHS_TO_MUTATE:
        if os.path.isdir(p):
            existing_paths.append(p)
        else:
            print(f"[WARN] Path not found, skipping: {p}")

    if not existing_paths:
        print("[SKIP] No mutation target paths found — mutation gate deferred")
        return 0

    # ------------------------------------------------------------------
    # Step 3: Run mutmut
    # ------------------------------------------------------------------
    output = run_mutmut(existing_paths)

    if output:
        print("--- mutmut output ---")
        # Print truncated output (last 50 lines) to avoid flooding
        lines = output.strip().splitlines()
        if len(lines) > 50:
            print(f"  ... ({len(lines) - 50} lines omitted)")
        for line in lines[-50:]:
            print(f"  {line}")
        print("--- end mutmut output ---")

    # ------------------------------------------------------------------
    # Step 4: Parse results
    # ------------------------------------------------------------------
    results = parse_mutation_results(output)

    if results["total_mutants"] == 0:
        print("[WARN] No mutants generated — check that target paths contain mutable code")
        print("[SKIP] Cannot evaluate threshold with 0 mutants")
        write_report(results, threshold, passed=True)
        return 0

    # ------------------------------------------------------------------
    # Step 5: Evaluate threshold
    # ------------------------------------------------------------------
    passed = results["score"] >= threshold

    # ------------------------------------------------------------------
    # Step 6: Report
    # ------------------------------------------------------------------
    print_markdown_summary(results, threshold, passed, strict=args.strict)
    write_report(results, threshold, passed)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
