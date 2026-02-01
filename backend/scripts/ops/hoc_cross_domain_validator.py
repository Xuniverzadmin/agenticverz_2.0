#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual or CI
#   Execution: sync
# Role: HOC Cross-Domain Import Validator (PIN-504)
# Reference: PIN-504, HOC Layer Topology V2.0.0
# artifact_class: CODE

"""
HOC Cross-Domain Import Validator

Scans the HOC codebase for cross-domain import violations:
  D1: L2 API imports from L5_engines/ or L6_drivers/ (L5_schemas/ legal)
  E1: L5 engine imports from another domain's L5_engines/ or L6_drivers/
  E2: L6 driver imports from another domain
  C1: Domain code imports from hoc_spine/orchestrator/coordinators/
  I1: __init__.py re-exports from L6_drivers/ or other domains

Usage:
    python hoc_cross_domain_validator.py                    # Report violations
    python hoc_cross_domain_validator.py --record           # Save baseline
    python hoc_cross_domain_validator.py --trend            # Show history
    python hoc_cross_domain_validator.py --ci               # Fail on regression

Exit Codes:
    0 - Clean (no violations or improving)
    1 - Violations detected
    2 - Error during scan
    3 - REGRESSION: Violation count INCREASED
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, NamedTuple, Optional

# History file
BASELINE_FILE = ".hoc_cross_domain_baseline.json"

# Recovery paths excluded until PIN-505
RECOVERY_EXCLUSIONS = [
    "hoc/api/cus/recovery/",
    "app/hoc/api/cus/recovery/",
]


class Finding(NamedTuple):
    """A cross-domain violation finding."""
    rule: str
    severity: str  # HIGH, MEDIUM
    file: str
    line: int
    issue: str
    recommendation: str


# =============================================================================
# Import Pattern Detection (regex-based, not AST)
# =============================================================================

# Match Python import lines
IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))",
    re.MULTILINE,
)


def _extract_imports(content: str, module_level_only: bool = True) -> list[tuple[int, str]]:
    """Extract (line_number, module_path) pairs from file content.

    Args:
        content: File content
        module_level_only: If True, only return module-level imports (not inside
            functions/methods). Lazy imports inside functions are the approved
            pattern for cross-domain access (PIN-504).
    """
    results = []
    in_function = False
    indent_stack = 0

    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Track function/method boundaries by indentation
        if module_level_only:
            # Detect function/class definitions
            if re.match(r"\s*(def |class |async def )", line):
                in_function = True
                indent_stack = len(line) - len(line.lstrip())
                continue

            # If we're in a function, check if we've returned to module level
            if in_function:
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indent_stack and not stripped.startswith((")", "]", "}")):
                    # Check if this is a new top-level statement
                    if re.match(r"[a-zA-Z_@#]", stripped) or stripped.startswith("from ") or stripped.startswith("import "):
                        if current_indent == 0:
                            in_function = False
                        else:
                            continue
                    else:
                        continue
                else:
                    continue

        m = re.match(r"from\s+([\w.]+)\s+import", stripped)
        if m:
            results.append((i, m.group(1)))
            continue
        m = re.match(r"import\s+([\w.]+)", stripped)
        if m:
            results.append((i, m.group(1)))
    return results


def _get_domain(path: str) -> Optional[str]:
    """Extract domain name from a path like hoc/cus/{domain}/..."""
    m = re.search(r"hoc/cus/(\w+)/", path)
    return m.group(1) if m else None


def _is_excluded(filepath: str) -> bool:
    """Check if file is in recovery exclusion zone."""
    return any(excl in filepath for excl in RECOVERY_EXCLUSIONS)


# =============================================================================
# Rule Implementations
# =============================================================================


def check_d1(filepath: str, content: str) -> list[Finding]:
    """D1: L2 API files must not import from L5_engines/ or L6_drivers/."""
    findings = []
    for line_no, module in _extract_imports(content):
        # Check if importing from L5_engines or L6_drivers
        if "L5_engines" in module or "L6_drivers" in module:
            # Exception: L5_schemas is legal
            if "L5_schemas" in module:
                continue
            findings.append(Finding(
                rule="D1",
                severity="HIGH",
                file=filepath,
                line=line_no,
                issue=f"L2 API imports from {module}",
                recommendation="Route through L4 handler or import from L5_schemas",
            ))
    return findings


def check_e1(filepath: str, content: str, my_domain: str) -> list[Finding]:
    """E1: L5 engine must not import from other domain's L5/L6."""
    findings = []
    for line_no, module in _extract_imports(content):
        if "hoc.cus." not in module and "hoc/cus/" not in module:
            continue
        # Extract target domain from import path
        m = re.search(r"hoc\.cus\.(\w+)\.", module) or re.search(r"hoc/cus/(\w+)/", module)
        if not m:
            continue
        target_domain = m.group(1)
        if target_domain == my_domain:
            continue
        # Cross-domain import detected
        if "L5_engines" in module or "L6_drivers" in module:
            # Exception: hoc_spine is legal
            if "hoc_spine" in module:
                continue
            findings.append(Finding(
                rule="E1",
                severity="HIGH",
                file=filepath,
                line=line_no,
                issue=f"L5 engine imports cross-domain from {module}",
                recommendation="Use DomainBridge or hoc_spine coordinator",
            ))
    return findings


def check_e2(filepath: str, content: str, my_domain: str) -> list[Finding]:
    """E2: L6 driver must not import from other domains."""
    findings = []
    for line_no, module in _extract_imports(content):
        if "hoc.cus." not in module and "hoc/cus/" not in module:
            continue
        m = re.search(r"hoc\.cus\.(\w+)\.", module) or re.search(r"hoc/cus/(\w+)/", module)
        if not m:
            continue
        target_domain = m.group(1)
        if target_domain == my_domain:
            continue
        # Exception: hoc_spine/schemas/ is legal
        if "hoc_spine.schemas" in module or "hoc_spine/schemas" in module:
            continue
        findings.append(Finding(
            rule="E2",
            severity="HIGH",
            file=filepath,
            line=line_no,
            issue=f"L6 driver imports cross-domain from {module}",
            recommendation="Extract shared types to hoc_spine/schemas/",
        ))
    return findings


def check_c1(filepath: str, content: str) -> list[Finding]:
    """C1: Domain code must not import from coordinators."""
    findings = []
    for line_no, module in _extract_imports(content):
        if "hoc_spine.orchestrator.coordinators" in module:
            findings.append(Finding(
                rule="C1",
                severity="MEDIUM",
                file=filepath,
                line=line_no,
                issue=f"Domain code imports coordinator: {module}",
                recommendation="Coordinators are for L4 handlers, not domain code",
            ))
    return findings


def check_i1(filepath: str, content: str, my_domain: str) -> list[Finding]:
    """I1: __init__.py must not re-export from L6_drivers/ or other domains."""
    findings = []
    for line_no, module in _extract_imports(content):
        # Check for L6_drivers re-export
        if "L6_drivers" in module:
            # Same-domain L5_schemas is legal
            if "L5_schemas" in module:
                continue
            # Check if it's another domain
            m = re.search(r"hoc\.cus\.(\w+)\.", module)
            if m and m.group(1) != my_domain:
                findings.append(Finding(
                    rule="I1",
                    severity="HIGH",
                    file=filepath,
                    line=line_no,
                    issue=f"__init__.py re-exports cross-domain from {module}",
                    recommendation="Delete cross-domain re-export",
                ))
        # Check for other domain imports (non-L5_schemas)
        elif "hoc.cus." in module:
            m = re.search(r"hoc\.cus\.(\w+)\.", module)
            if m and m.group(1) != my_domain:
                if "L5_schemas" not in module:
                    findings.append(Finding(
                        rule="I1",
                        severity="HIGH",
                        file=filepath,
                        line=line_no,
                        issue=f"__init__.py re-exports from other domain: {module}",
                        recommendation="Delete cross-domain re-export",
                    ))
    return findings


# =============================================================================
# Scanner
# =============================================================================


def scan_violations(root: Path) -> list[Finding]:
    """Scan the HOC codebase for cross-domain violations."""
    findings = []
    hoc_root = root / "app" / "hoc"

    if not hoc_root.exists():
        # Try from backend root
        hoc_root = root / "backend" / "app" / "hoc"

    if not hoc_root.exists():
        print(f"ERROR: HOC root not found at {hoc_root}", file=sys.stderr)
        sys.exit(2)

    # D1: Scan L2 API files
    api_root = hoc_root / "api"
    if api_root.exists():
        for pyfile in api_root.rglob("*.py"):
            filepath = str(pyfile.relative_to(root))
            if _is_excluded(filepath):
                continue
            try:
                content = pyfile.read_text()
            except Exception:
                continue
            findings.extend(check_d1(filepath, content))

    # E1, E2, C1, I1: Scan domain files
    cus_root = hoc_root / "cus"
    if cus_root.exists():
        for domain_dir in sorted(cus_root.iterdir()):
            if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
                continue
            domain = domain_dir.name

            for pyfile in domain_dir.rglob("*.py"):
                filepath = str(pyfile.relative_to(root))
                if _is_excluded(filepath):
                    continue
                try:
                    content = pyfile.read_text()
                except Exception:
                    continue

                # E1: L5 engines cross-domain
                if "/L5_engines/" in filepath:
                    if pyfile.name == "__init__.py":
                        findings.extend(check_i1(filepath, content, domain))
                    else:
                        findings.extend(check_e1(filepath, content, domain))

                # E2: L6 drivers cross-domain
                elif "/L6_drivers/" in filepath:
                    if pyfile.name == "__init__.py":
                        findings.extend(check_i1(filepath, content, domain))
                    else:
                        findings.extend(check_e2(filepath, content, domain))

                # C1: Coordinator imports from domain code
                if "/L5_engines/" in filepath or "/L6_drivers/" in filepath:
                    findings.extend(check_c1(filepath, content))

    return findings


# =============================================================================
# Output
# =============================================================================


def output_text(findings: list[Finding]) -> None:
    """Print findings as text."""
    if not findings:
        print("=== HOC Cross-Domain Validator ===")
        print("Status: CLEAN")
        print("No violations detected.")
        return

    print("=== HOC Cross-Domain Validator ===")
    print(f"Status: VIOLATIONS DETECTED")
    print(f"Total: {len(findings)}")
    print()

    by_rule: dict[str, list[Finding]] = {}
    for f in findings:
        by_rule.setdefault(f.rule, []).append(f)

    for rule in sorted(by_rule.keys()):
        rule_findings = by_rule[rule]
        print(f"=== Rule {rule} ({len(rule_findings)} violations) ===")
        for f in rule_findings:
            print(f"  [{f.severity}] {f.file}:{f.line}")
            print(f"    Issue: {f.issue}")
            print(f"    Fix: {f.recommendation}")
        print()


def output_json(findings: list[Finding]) -> None:
    """Print findings as JSON."""
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "invariant": "HOC-CROSS-DOMAIN-001",
        "status": "CLEAN" if not findings else "VIOLATIONS",
        "count": len(findings),
        "findings": [
            {
                "rule": f.rule,
                "severity": f.severity,
                "file": f.file,
                "line": f.line,
                "issue": f.issue,
                "recommendation": f.recommendation,
            }
            for f in findings
        ],
    }
    print(json.dumps(data, indent=2))


# =============================================================================
# Trend Tracking
# =============================================================================


def load_history(root: Path) -> list[dict]:
    """Load baseline history."""
    history_file = root / BASELINE_FILE
    if not history_file.exists():
        return []
    try:
        return json.loads(history_file.read_text())
    except Exception:
        return []


def save_history(root: Path, history: list[dict]) -> None:
    """Save baseline history."""
    history_file = root / BASELINE_FILE
    history = history[-100:]
    history_file.write_text(json.dumps(history, indent=2))


def record_baseline(root: Path, count: int, by_rule: dict) -> dict:
    """Record current violation count."""
    history = load_history(root)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": count,
        "by_rule": by_rule,
    }
    history.append(entry)
    save_history(root, history)

    if len(history) < 2:
        return {"previous": None, "current": count, "delta": None, "trend": "BASELINE"}

    previous = history[-2]["count"]
    delta = count - previous
    trend = "IMPROVING" if delta < 0 else "REGRESSING" if delta > 0 else "STABLE"
    return {"previous": previous, "current": count, "delta": delta, "trend": trend}


def show_trend(root: Path) -> None:
    """Display trend over time."""
    history = load_history(root)
    if not history:
        print("No baseline history. Run with --record first.")
        return

    print("=== HOC Cross-Domain Violation Trend ===")
    print()
    recent = history[-10:]
    for i, entry in enumerate(recent):
        ts = entry["timestamp"][:10]
        count = entry["count"]
        if i == 0:
            print(f"  {ts}: {count} (baseline)")
        else:
            prev = recent[i - 1]["count"]
            delta = count - prev
            arrow = "↓" if delta < 0 else "↑" if delta > 0 else "→"
            print(f"  {ts}: {count} ({arrow} {abs(delta)})")

    print()
    if len(history) >= 2:
        first = history[0]["count"]
        last = history[-1]["count"]
        total = last - first
        print(f"Total change: {first} → {last} (Δ {total:+d})")


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="HOC Cross-Domain Import Validator (PIN-504)"
    )
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--root", default=".", help="Root directory to scan")
    parser.add_argument("--record", action="store_true", help="Record baseline")
    parser.add_argument("--trend", action="store_true", help="Show trend (no scan)")
    parser.add_argument("--ci", action="store_true", help="Fail on regression")

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.trend:
        show_trend(root)
        sys.exit(0)

    try:
        findings = scan_violations(root)
    except Exception as e:
        print(f"Error during scan: {e}", file=sys.stderr)
        sys.exit(2)

    count = len(findings)
    by_rule = {}
    for f in findings:
        by_rule[f.rule] = by_rule.get(f.rule, 0) + 1

    trend = None
    if args.record:
        trend = record_baseline(root, count, by_rule)

    if args.output == "json":
        output_json(findings)
    else:
        output_text(findings)
        if trend:
            print(f"\n=== Baseline ===")
            if trend["previous"] is not None:
                print(f"Previous: {trend['previous']}")
                print(f"Current:  {trend['current']}")
                print(f"Delta:    {trend['delta']:+d}")
                print(f"Status:   {trend['trend']}")
            else:
                print(f"Baseline established: {trend['current']}")

    # CI mode: check for regression
    if args.ci:
        history = load_history(root)
        if history:
            last_baseline = history[-1]["count"]
            if count > last_baseline:
                print()
                print("=" * 60)
                print("REGRESSION DETECTED — HARD FAIL")
                print("=" * 60)
                print(f"Baseline: {last_baseline}")
                print(f"Current:  {count}")
                print(f"Increase: +{count - last_baseline}")
                print()
                print("Cross-domain violation count must NEVER increase.")
                sys.exit(3)

    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
