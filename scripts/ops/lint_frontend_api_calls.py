#!/usr/bin/env python3
"""
Frontend API Call Type Safety Linter

Detects ID type mismatches in frontend API calls where:
- incident.id is passed to endpoints expecting call_id
- call_id is passed to endpoints expecting incident_id
- Wrong ID prefix patterns in API URLs

Issue: Replay button 404 error
Discovered: 2025-12-21
Root cause: onReplay(incident.id) called with incident_id but endpoint expected call_id
Fix pattern: Use incident.call_id for replay endpoints

Usage:
    python scripts/ops/lint_frontend_api_calls.py [path]
    python scripts/ops/lint_frontend_api_calls.py website/aos-console/console/src/
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# ID type patterns with their expected contexts
ID_TYPE_PATTERNS = [
    {
        "name": "incident_id_in_replay",
        "description": "incident.id used in replay context (should be call_id)",
        "regex": r"(?:onReplay|replay|Replay)\s*\(\s*(?:incident|inc)\.id\s*\)",
        "suggestion": "Use incident.call_id instead of incident.id for replay",
        "severity": "error",
    },
    {
        "name": "incident_id_in_replay_url",
        "description": "incident.id interpolated in replay URL",
        "regex": r"/replay/\$\{(?:incident|inc)\.id\}",
        "suggestion": "Use ${incident.call_id} for replay URLs",
        "severity": "error",
    },
    {
        "name": "hardcoded_inc_prefix_in_replay",
        "description": "Hardcoded inc_ prefix in replay URL (should be call_)",
        "regex": r"/replay/inc_",
        "suggestion": "Replay endpoints expect call_id (call_xxx), not incident_id (inc_xxx)",
        "severity": "error",
    },
    {
        "name": "call_id_in_incident_endpoint",
        "description": "call_id used in incident endpoint (should be incident_id)",
        "regex": r"/incidents/\$\{.*call.*\}",
        "suggestion": "Use incident.id for /incidents/ endpoints",
        "severity": "warning",
    },
    {
        "name": "wrong_id_type_in_mutation",
        "description": "Suspicious ID variable in mutation - may be wrong type",
        "regex": r"mutate\(\s*(?:incident|inc)\.id\s*\)",
        "suggestion": "Verify the ID type matches what the mutation endpoint expects",
        "severity": "warning",
    },
]

# API endpoint patterns and their expected ID types
ENDPOINT_ID_CONTRACTS = {
    "/replay/": "call_id",
    "/incidents/{id}": "incident_id",
    "/incidents/{id}/acknowledge": "incident_id",
    "/incidents/{id}/resolve": "incident_id",
    "/incidents/{id}/export": "incident_id",
    "/incidents/{id}/timeline": "incident_id",
    "/keys/{id}": "key_id",
}

# File extensions to check
EXTENSIONS = {".tsx", ".ts", ".jsx", ".js"}


def find_issues(content: str, filepath: str) -> List[Tuple[int, str, str, str]]:
    """Find ID type mismatch issues in file content.

    Returns list of (line_number, pattern_name, description, suggestion)
    """
    issues = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        for pattern in ID_TYPE_PATTERNS:
            if re.search(pattern["regex"], line):
                issues.append(
                    (
                        i,
                        pattern["name"],
                        pattern["description"],
                        pattern["suggestion"],
                        pattern["severity"],
                    )
                )

    return issues


def lint_file(filepath: Path) -> List[Tuple[str, int, str, str, str, str]]:
    """Lint a single file for ID type mismatches.

    Returns list of (filepath, line, pattern, description, suggestion, severity)
    """
    try:
        content = filepath.read_text()
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
        return []

    issues = find_issues(content, str(filepath))
    return [
        (str(filepath), line, name, desc, sugg, sev)
        for line, name, desc, sugg, sev in issues
    ]


def lint_directory(path: Path) -> List[Tuple[str, int, str, str, str, str]]:
    """Lint all frontend files in directory."""
    all_issues = []

    for ext in EXTENSIONS:
        for filepath in path.rglob(f"*{ext}"):
            # Skip node_modules and dist
            if "node_modules" in str(filepath) or "/dist/" in str(filepath):
                continue
            all_issues.extend(lint_file(filepath))

    return all_issues


def main():
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("website/aos-console/console/src")
    )

    if not path.exists():
        print(f"Error: Path not found: {path}", file=sys.stderr)
        sys.exit(1)

    if path.is_file():
        issues = lint_file(path)
    else:
        issues = lint_directory(path)

    # Group by severity
    errors = [i for i in issues if i[5] == "error"]
    warnings = [i for i in issues if i[5] == "warning"]

    # Print results
    if not issues:
        print("✅ No ID type mismatch issues found")
        sys.exit(0)

    print(f"🔍 Found {len(issues)} potential ID type issues:\n")

    for filepath, line, name, desc, sugg, severity in sorted(issues):
        icon = "❌" if severity == "error" else "⚠️"
        print(f"{icon} {filepath}:{line}")
        print(f"   Pattern: {name}")
        print(f"   Issue: {desc}")
        print(f"   Fix: {sugg}")
        print()

    # Summary
    print("=" * 60)
    print(f"Summary: {len(errors)} errors, {len(warnings)} warnings")
    print()
    print("ID Type Contracts:")
    print("  - Replay endpoints (/replay/*) expect: call_id (call_xxx)")
    print("  - Incident endpoints (/incidents/*) expect: incident_id (inc_xxx)")
    print("  - Key endpoints (/keys/*) expect: key_id")

    # Exit with error if there are errors
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
