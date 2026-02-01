#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL RUNNER - Execute all architectural guardrail checks.
# artifact_class: CODE
"""
GUARDRAIL RUNNER - Execute all architectural guardrail checks.

This script runs all 19 guardrail enforcement checks and reports results.

Usage:
    python run_guardrails.py           # Run all checks
    python run_guardrails.py --strict  # Fail on first violation
    python run_guardrails.py --report  # Generate markdown report
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

# All guardrail scripts organized by category
GUARDRAILS = {
    'DOMAIN': [
        ('DOMAIN-001', 'check_domain_writes.py', 'Domain ownership enforcement'),
        ('DOMAIN-002', 'check_account_boundaries.py', 'Account domain boundaries'),
        ('DOMAIN-003', 'check_overview_readonly.py', 'Overview read-only enforcement'),
    ],
    'DATA': [
        ('DATA-001', 'check_foreign_keys.py', 'Cross-domain FK requirements'),
        ('DATA-002', 'check_tenant_queries.py', 'Tenant isolation in queries'),
        # DATA-003 is DB trigger, not a CI script
    ],
    'CROSS-DOMAIN': [
        ('CROSS-001', 'check_cross_domain_propagation.py', 'Mandatory propagation'),
        ('CROSS-002', 'check_bidirectional_queries.py', 'Bidirectional queries'),
        # CROSS-003 would be "no silos" - covered by CROSS-001/002
    ],
    'LIMITS': [
        ('LIMITS-001', 'check_limit_tables.py', 'Single limit source of truth'),
        ('LIMITS-002', 'check_limit_enforcement.py', 'Pre-execution limit check'),
        ('LIMITS-003', 'check_limit_audit.py', 'Audit on limit change'),
    ],
    'AUDIT': [
        ('AUDIT-001', 'check_governance_audit.py', 'Governance actions emit audit'),
        ('AUDIT-002', 'check_audit_completeness.py', 'Audit entry completeness'),
    ],
    'CAPABILITY': [
        ('CAP-001', 'check_capability_endpoints.py', 'Capability-endpoint match'),
        ('CAP-002', 'check_console_boundaries.py', 'Console capability boundaries'),
        ('CAP-003', 'check_capability_status.py', 'Capability status progression'),
    ],
    'API': [
        ('API-001', 'check_facade_usage.py', 'Domain facade required'),
        ('API-002', 'check_response_envelopes.py', 'Consistent response envelope'),
    ],
}


def run_check(script_path: Path) -> Tuple[int, str]:
    """Run a single guardrail check and return result."""
    try:
        result = subprocess.run(
            ['python3', str(script_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        output = result.stdout + result.stderr
        return result.returncode, output
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT: Check took too long"
    except Exception as e:
        return 1, f"ERROR: {str(e)}"


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def generate_report(results: dict) -> str:
    """Generate markdown report of results."""
    lines = [
        "# Guardrail Check Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        "| Category | Checks | Passed | Failed |",
        "|----------|--------|--------|--------|",
    ]

    total_checks = 0
    total_passed = 0
    total_failed = 0

    for category, checks in results.items():
        passed = sum(1 for _, _, code, _ in checks if code == 0)
        failed = len(checks) - passed
        total_checks += len(checks)
        total_passed += passed
        total_failed += failed
        lines.append(f"| {category} | {len(checks)} | {passed} | {failed} |")

    lines.extend([
        f"| **TOTAL** | **{total_checks}** | **{total_passed}** | **{total_failed}** |",
        "",
        "## Detailed Results",
        "",
    ])

    for category, checks in results.items():
        lines.extend([
            f"### {category}",
            "",
        ])

        for rule_id, desc, code, output in checks:
            status = "PASS" if code == 0 else "FAIL"
            emoji = "✅" if code == 0 else "❌"
            lines.extend([
                f"#### {emoji} {rule_id}: {desc}",
                "",
                f"**Status:** {status}",
                "",
            ])

            if code != 0:
                lines.extend([
                    "<details>",
                    "<summary>View Output</summary>",
                    "",
                    "```",
                    output[:2000] + ("..." if len(output) > 2000 else ""),
                    "```",
                    "",
                    "</details>",
                    "",
                ])

    return "\n".join(lines)


def main():
    """Main entry point."""
    script_dir = Path(__file__).parent
    strict_mode = '--strict' in sys.argv
    generate_md = '--report' in sys.argv

    print_header("GUARDRAIL ENFORCEMENT SUITE")
    print(f"Running {sum(len(v) for v in GUARDRAILS.values())} checks across {len(GUARDRAILS)} categories")

    results = {}
    all_passed = True

    for category, checks in GUARDRAILS.items():
        print_header(f"Category: {category}")
        results[category] = []

        for rule_id, script_name, description in checks:
            script_path = script_dir / script_name

            if not script_path.exists():
                print(f"  ⚠️  {rule_id}: Script not found ({script_name})")
                results[category].append((rule_id, description, 1, "Script not found"))
                all_passed = False
                continue

            print(f"  Running {rule_id}: {description}...", end=" ", flush=True)
            code, output = run_check(script_path)

            if code == 0:
                print("✅ PASS")
            else:
                print("❌ FAIL")
                all_passed = False
                if strict_mode:
                    print("\n  STRICT MODE: Stopping on first failure")
                    print(f"\n  Output:\n{output[:1000]}")
                    sys.exit(1)

            results[category].append((rule_id, description, code, output))

    # Summary
    print_header("SUMMARY")

    passed_count = sum(1 for cat in results.values() for _, _, code, _ in cat if code == 0)
    total_count = sum(len(cat) for cat in results.values())
    failed_count = total_count - passed_count

    print(f"  Total checks: {total_count}")
    print(f"  Passed: {passed_count}")
    print(f"  Failed: {failed_count}")
    print()

    if failed_count > 0:
        print("  Failed checks:")
        for category, checks in results.items():
            for rule_id, desc, code, _ in checks:
                if code != 0:
                    print(f"    ❌ {rule_id}: {desc}")
    else:
        print("  All guardrail checks passed! ✅")

    # Generate report if requested
    if generate_md:
        report = generate_report(results)
        report_path = script_dir.parent.parent / "docs" / "architecture" / "GUARDRAIL_CHECK_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"\n  Report saved to: {report_path}")

    print()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
