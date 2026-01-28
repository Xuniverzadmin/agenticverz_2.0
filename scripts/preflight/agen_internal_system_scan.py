#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# AUDIENCE: INTERNAL
# Role: Stateless contract scanner — runs once, reports, exits
# Reference: Replaces continuous_validator.py (daemon) with cron-friendly scan

"""
Agen Internal System Scan

Stateless contract scanner that checks all backend files in a single pass.
Designed for cron scheduling and session_start.sh integration.

Usage:
    python3 agen_internal_system_scan.py            # Run scan, print report
    python3 agen_internal_system_scan.py --quiet     # Exit code only (for cron)
    python3 agen_internal_system_scan.py --json      # JSON output

Exit codes:
    0 = CLEAN (no violations)
    1 = VIOLATIONS found
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================

REPO_ROOT = Path(__file__).parent.parent.parent
BACKEND_PATH = REPO_ROOT / "backend"
STATUS_FILE = REPO_ROOT / ".validator_status.json"
LOG_FILE = REPO_ROOT / ".validator.log"

# =============================================================================
# Check implementations (ported from continuous_validator.py)
# =============================================================================

def check_naming(file_path: Path) -> list[dict]:
    """Check naming conventions in schema and model files."""
    violations = []
    try:
        content = file_path.read_text()
    except (IOError, UnicodeDecodeError):
        return violations

    lines = content.split("\n")

    if "/schemas/" in str(file_path):
        context_patterns = [
            (r"(\w+_remaining)\s*:", "NC-001", "Context suffix '_remaining' in field name"),
            (r"(\w+_current)\s*:", "NC-001", "Context suffix '_current' in field name"),
            (r"(\w+_total)\s*:", "NC-001", "Context suffix '_total' in field name"),
        ]
        for line_num, line in enumerate(lines, 1):
            for pattern, rule, message in context_patterns:
                if re.search(pattern, line):
                    violations.append({
                        "file": str(file_path),
                        "line": line_num,
                        "rule": rule,
                        "message": message,
                        "code": line.strip()[:60],
                    })

    if "/models/" in str(file_path):
        camel_pattern = re.compile(r"^\s+(\w+[a-z][A-Z]\w*)\s*:")
        for line_num, line in enumerate(lines, 1):
            match = camel_pattern.search(line)
            if match and not match.group(1).startswith("_"):
                violations.append({
                    "file": str(file_path),
                    "line": line_num,
                    "rule": "NC-003",
                    "message": f"camelCase field '{match.group(1)}' in model",
                    "code": line.strip()[:60],
                })

    return violations


def check_migration(file_path: Path) -> list[dict]:
    """Check migration contract headers."""
    violations = []
    try:
        content = file_path.read_text()
    except (IOError, UnicodeDecodeError):
        return violations

    if "MIGRATION_CONTRACT:" not in content:
        violations.append({
            "file": str(file_path),
            "line": 1,
            "rule": "MIG-001",
            "message": "Missing MIGRATION_CONTRACT header",
            "code": "",
        })
        return violations

    contract_match = re.search(r"#\s*parent:\s*(\S+)", content)
    down_rev_match = re.search(r'^down_revision\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)

    if contract_match and down_rev_match:
        contract_parent = contract_match.group(1)
        down_revision = down_rev_match.group(1)
        if contract_parent != down_revision:
            violations.append({
                "file": str(file_path),
                "line": down_rev_match.start(),
                "rule": "MIG-002",
                "message": f"Contract parent '{contract_parent}' != down_revision '{down_revision}'",
                "code": "",
            })

    return violations


def check_router(file_path: Path) -> list[dict]:
    """Check router wiring conventions."""
    violations = []
    if file_path.name != "main.py":
        return violations

    try:
        content = file_path.read_text()
    except (IOError, UnicodeDecodeError):
        return violations

    for line_num, line in enumerate(content.split("\n"), 1):
        if re.search(r"from\s+\.?app\.api\.", line) or re.search(r"from\s+\.api\.", line):
            if "registry" not in line:
                violations.append({
                    "file": str(file_path),
                    "line": line_num,
                    "rule": "RW-001",
                    "message": "Router import in main.py (use registry.py)",
                    "code": line.strip()[:60],
                })
        if "include_router" in line and not line.strip().startswith("#"):
            violations.append({
                "file": str(file_path),
                "line": line_num,
                "rule": "RW-002",
                "message": "include_router in main.py (use registry.py)",
                "code": line.strip()[:60],
            })

    return violations


def check_boundary(file_path: Path) -> list[dict]:
    """Check runtime/API boundary access."""
    violations = []
    if "_adapters" in str(file_path):
        return violations

    try:
        content = file_path.read_text()
    except (IOError, UnicodeDecodeError):
        return violations

    runtime_patterns = [
        (r"\.headroom\.tokens\b", "RAB-001", "Direct access to .headroom.tokens"),
        (r"\.headroom\.runs\b", "RAB-001", "Direct access to .headroom.runs"),
        (r"\.headroom\.cost_cents\b", "RAB-001", "Direct access to .headroom.cost_cents"),
    ]

    for line_num, line in enumerate(content.split("\n"), 1):
        for pattern, rule, message in runtime_patterns:
            if re.search(pattern, line):
                violations.append({
                    "file": str(file_path),
                    "line": line_num,
                    "rule": rule,
                    "message": message + " (use adapter)",
                    "code": line.strip()[:60],
                })

    return violations


# =============================================================================
# Scanner
# =============================================================================

# Map: path substring -> list of check functions
FILE_CHECKS = {
    "app/schemas/": [check_naming],
    "app/models/": [check_naming],
    "app/api/": [check_naming, check_router, check_boundary],
    "alembic/versions/": [check_migration],
    "app/main.py": [check_router],
}


def scan_all() -> tuple[list[dict], int]:
    """Scan all backend Python files. Returns (violations, files_scanned)."""
    all_violations = []
    files_scanned = 0

    for py_file in sorted(BACKEND_PATH.rglob("*.py")):
        rel = str(py_file.relative_to(BACKEND_PATH))
        checks_to_run = []
        for pattern, checks in FILE_CHECKS.items():
            if pattern in rel:
                checks_to_run.extend(checks)

        if not checks_to_run:
            continue

        files_scanned += 1
        # deduplicate check functions
        for check_fn in dict.fromkeys(checks_to_run):
            all_violations.extend(check_fn(py_file))

    return all_violations, files_scanned


# =============================================================================
# Output
# =============================================================================

def write_status(violations: list[dict], files_scanned: int):
    """Write status JSON (backward-compatible with continuous_validator)."""
    status = {
        "status": "VIOLATIONS" if violations else "CLEAN",
        "last_check": datetime.now().isoformat(),
        "violations": violations,
        "files_scanned": files_scanned,
        "checks_run": files_scanned,
        "scanner": "agen_internal_system_scan",
    }
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2, default=str)


def append_log(violations: list[dict]):
    """Append scan results to log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"[{timestamp}] [INFO] === Scheduled Scan ==="]
    if violations:
        for v in violations:
            lines.append(
                f"[{timestamp}] [WARN]   ✗ {v['rule']}: {v['message']} ({v['file']}:{v['line']})"
            )
    else:
        lines.append(f"[{timestamp}] [PASS]   ✓ All checks passed")

    with open(LOG_FILE, "a") as f:
        f.write("\n".join(lines) + "\n")


def print_banner(violations: list[dict], files_scanned: int):
    """Print unmissable banner to stdout."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if violations:
        print()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  ⚠  CONTRACT VIOLATIONS DETECTED                           ║")
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║  Scanned: {files_scanned} files   |   Violations: {len(violations):<4}              ║")
        print(f"║  Time:    {now}                          ║")
        print("╠══════════════════════════════════════════════════════════════╣")

        # Group by rule
        by_rule: dict[str, list[dict]] = {}
        for v in violations:
            by_rule.setdefault(v["rule"], []).append(v)

        for rule, items in sorted(by_rule.items()):
            print(f"║                                                              ║")
            print(f"║  [{rule}] ({len(items)} occurrence{'s' if len(items) > 1 else ''}){'': <42}║")
            for item in items[:5]:  # cap at 5 per rule
                path = item["file"].replace(str(REPO_ROOT) + "/", "")
                msg = item["message"][:50]
                line = f"    {path}:{item['line']}"
                print(f"║  {line:<58} ║")
                print(f"║    → {msg:<54} ║")
            if len(items) > 5:
                print(f"║    ... and {len(items) - 5} more{'': <45}║")

        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
    else:
        print()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  ✓  CONTRACT SCAN CLEAN                                     ║")
        print(f"║  Scanned: {files_scanned} files   |   {now}                ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Agen Internal System Scan")
    parser.add_argument("--quiet", "-q", action="store_true", help="No stdout, exit code only")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output to stdout")
    args = parser.parse_args()

    violations, files_scanned = scan_all()

    # Always persist
    write_status(violations, files_scanned)
    append_log(violations)

    # Output
    if args.json:
        json.dump({
            "status": "VIOLATIONS" if violations else "CLEAN",
            "violations": violations,
            "files_scanned": files_scanned,
            "timestamp": datetime.now().isoformat(),
        }, sys.stdout, indent=2, default=str)
        print()
    elif not args.quiet:
        print_banner(violations, files_scanned)

    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
