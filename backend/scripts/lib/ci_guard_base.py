# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Base class for CI guard scripts — shared CLI, reporting, exit code conventions (PIN-513 Phase 5C)
# artifact_class: CODE

"""
CI Guard Base (PIN-513 Phase 5C)

Shared infrastructure for CI guard scripts:
- --ci flag handling (exit 1 on violations)
- --summary flag (compact output)
- --json flag (machine-readable output)
- Violation counting and categorized reporting
- Standard exit codes (0=pass, 1=violations, 2=error)
"""

import argparse
import json as json_lib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class GuardViolation:
    """A single violation detected by a guard script."""

    file: str
    line: int
    message: str
    category: str = "VIOLATION"
    severity: str = "ERROR"  # ERROR, WARNING

    def __str__(self):
        return f"  [{self.category}] {self.file}:{self.line} — {self.message}"


@dataclass
class GuardResult:
    """Aggregated result from a guard run."""

    guard_name: str
    violations: List[GuardViolation] = field(default_factory=list)
    warnings: List[GuardViolation] = field(default_factory=list)
    files_scanned: int = 0

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict:
        return {
            "guard": self.guard_name,
            "passed": self.passed,
            "violations": len(self.violations),
            "warnings": len(self.warnings),
            "files_scanned": self.files_scanned,
            "details": [
                {"file": v.file, "line": v.line, "message": v.message, "category": v.category}
                for v in self.violations
            ],
        }


def create_guard_parser(description: str) -> argparse.ArgumentParser:
    """Create standard argument parser for guard scripts."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--ci", action="store_true", help="CI mode: exit 1 on violations")
    parser.add_argument("--summary", action="store_true", help="Compact summary output")
    parser.add_argument("--json", action="store_true", help="JSON output mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    return parser


def report_result(result: GuardResult, ci_mode: bool = False, json_mode: bool = False, summary_mode: bool = False) -> int:
    """Report guard results and return exit code.

    Returns:
        0 if passed, 1 if violations found (in CI mode), 2 on error.
    """
    if json_mode:
        print(json_lib.dumps(result.to_dict(), indent=2))
    elif summary_mode:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.guard_name}: {len(result.violations)} violations, {result.files_scanned} files scanned")
    else:
        print(f"\n{result.guard_name}")
        print("=" * 60)

        if result.violations:
            by_cat: dict[str, list] = {}
            for v in result.violations:
                by_cat.setdefault(v.category, []).append(v)
            for cat, vs in sorted(by_cat.items()):
                print(f"\n{cat} ({len(vs)} violations):")
                for v in vs:
                    print(str(v))

        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for w in result.warnings:
                print(str(w))

        if result.passed:
            print(f"\nAll checks passed. 0 violations ({result.files_scanned} files scanned).")
        else:
            print(f"\nBlocking: {len(result.violations)} violations")

    if ci_mode and not result.passed:
        return 1
    return 0


__all__ = [
    "GuardViolation",
    "GuardResult",
    "create_guard_parser",
    "report_result",
]
