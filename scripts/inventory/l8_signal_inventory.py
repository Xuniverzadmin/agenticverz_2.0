#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Scan L8 artifacts for signal emission patterns
# Authority: READ-ONLY (audit script)
# Reference: L1_L2_L8 Binding Audit

"""
L8 Signal Inventory
Scans scripts/, monitoring/, verification/, observability/ for emitted signals.
Produces markdown table of signal emitters and their locations.
"""

import ast
import pathlib
import re

# Directories that constitute L8 (Catalyst/Meta layer)
L8_ROOTS = [
    "scripts",
    "monitoring",
    "observability",
    "backend/scripts",
    ".github/workflows",
]

# Patterns that indicate signal emission
SIGNAL_PATTERNS = [
    r"emit_",
    r"publish_",
    r"alert",
    r"metric",
    r"signal",
    r"event",
    r"incident",
    r"violation",
    r"anomaly",
    r"recovery",
    r"prediction",
    r"canary",
    r"health",
    r"trigger",
]

# Also look for prometheus metrics
METRIC_PATTERNS = [
    r"Counter\(",
    r"Gauge\(",
    r"Histogram\(",
    r"Summary\(",
    r"prometheus",
]


def scan_python_file(path: pathlib.Path):
    """Extract signal-like function calls from Python AST."""
    try:
        text = path.read_text(errors="ignore")
        tree = ast.parse(text)
    except Exception:
        return []

    signals = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Get function name
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name:
                func_lower = func_name.lower()
                for pattern in SIGNAL_PATTERNS:
                    if pattern.lower() in func_lower:
                        signals.append(
                            {
                                "call": func_name,
                                "file": path.as_posix(),
                                "line": getattr(node, "lineno", 0),
                                "type": "function_call",
                            }
                        )
                        break

    # Also scan for metric definitions
    for pattern in METRIC_PATTERNS:
        for match in re.finditer(pattern, text):
            # Find line number
            line_num = text[: match.start()].count("\n") + 1
            signals.append(
                {
                    "call": match.group().rstrip("("),
                    "file": path.as_posix(),
                    "line": line_num,
                    "type": "metric_definition",
                }
            )

    return signals


def scan_yaml_file(path: pathlib.Path):
    """Look for signal/alert definitions in YAML files."""
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return []

    signals = []

    # Look for alert definitions
    if "alert:" in text.lower() or "alertname:" in text.lower():
        signals.append(
            {
                "call": "AlertRule",
                "file": path.as_posix(),
                "line": 0,
                "type": "alert_rule",
            }
        )

    # Look for metric references
    if "expr:" in text:
        signals.append(
            {
                "call": "PrometheusQuery",
                "file": path.as_posix(),
                "line": 0,
                "type": "prometheus_query",
            }
        )

    return signals


def main():
    repo_root = pathlib.Path(__file__).parent.parent.parent

    results = []

    for root in L8_ROOTS:
        root_path = repo_root / root
        if not root_path.exists():
            continue

        # Scan Python files
        for path in root_path.rglob("*.py"):
            for sig in scan_python_file(path):
                # Make path relative
                sig["file"] = str(path.relative_to(repo_root))
                results.append(sig)

        # Scan YAML files (for alert rules)
        for path in root_path.rglob("*.yaml"):
            for sig in scan_yaml_file(path):
                sig["file"] = str(path.relative_to(repo_root))
                results.append(sig)
        for path in root_path.rglob("*.yml"):
            for sig in scan_yaml_file(path):
                sig["file"] = str(path.relative_to(repo_root))
                results.append(sig)

    # Also scan monitoring config
    monitoring_path = repo_root / "monitoring"
    if monitoring_path.exists():
        for path in monitoring_path.rglob("*.yaml"):
            for sig in scan_yaml_file(path):
                sig["file"] = str(path.relative_to(repo_root))
                results.append(sig)
        for path in monitoring_path.rglob("*.yml"):
            for sig in scan_yaml_file(path):
                sig["file"] = str(path.relative_to(repo_root))
                results.append(sig)

    # Deduplicate
    seen = set()
    unique_results = []
    for r in results:
        key = (r["call"], r["file"])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    # Sort by signal name then file
    unique_results.sort(key=lambda x: (x["call"].lower(), x["file"]))

    # Output markdown table
    print("# L8 Signal Inventory")
    print()
    print(f"**Generated:** {pathlib.Path(__file__).name}")
    print(f"**Total Signals Found:** {len(unique_results)}")
    print()
    print("| Signal/Call | Type | File | Line |")
    print("|-------------|------|------|------|")

    for sig in unique_results:
        print(f"| `{sig['call']}` | {sig['type']} | `{sig['file']}` | {sig['line']} |")

    print()
    print("---")
    print()

    # Categorize by signal type
    by_type = {}
    for sig in unique_results:
        by_type.setdefault(sig["type"], []).append(sig)

    print("## Summary by Type")
    print()
    print("| Type | Count |")
    print("|------|-------|")
    for typ, sigs in sorted(by_type.items()):
        print(f"| {typ} | {len(sigs)} |")


if __name__ == "__main__":
    main()
