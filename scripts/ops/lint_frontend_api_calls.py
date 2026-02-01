#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Frontend API Call Type Safety Linter
# artifact_class: CODE
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
    python scripts/ops/lint_frontend_api_calls.py website/app-shell/src/
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# ID type patterns with their expected contexts
#
# PIN-314: Updated to reflect actual API contracts
#
# REPLAY API VERSIONS:
#   - NEW (H1 Replay UX): /replay/{incident_id}/slice, /summary, /timeline - uses incident_id
#   - LEGACY: /guard/replay/{call_id}, /v1/replay/{call_id} - uses call_id
#
# The frontend uses NEW H1 endpoints, so incident.id is CORRECT for replay URLs.
#
ID_TYPE_PATTERNS = [
    # REMOVED: incident_id_in_replay - H1 Replay UX correctly uses incident_id
    # REMOVED: incident_id_in_replay_url - H1 Replay UX correctly uses incident_id
    # REMOVED: hardcoded_inc_prefix_in_replay - H1 Replay UX correctly uses incident_id
    {
        "name": "call_id_in_h1_replay",
        "description": "call_id used in H1 replay URL (H1 expects incident_id)",
        "regex": r"/replay/\$\{.*call.*\}/(slice|summary|timeline)",
        "suggestion": "H1 Replay UX endpoints expect incident_id, not call_id",
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
#
# PIN-314: Updated endpoint contracts
#
ENDPOINT_ID_CONTRACTS = {
    # H1 Replay UX (NEW) - uses incident_id
    "/replay/{id}/slice": "incident_id",
    "/replay/{id}/summary": "incident_id",
    "/replay/{id}/timeline": "incident_id",
    "/replay/{id}/explain/": "incident_id",
    # Legacy replay - uses call_id
    "/guard/replay/{id}": "call_id",
    "/v1/replay/{id}": "call_id",
    "/operator/replay/{id}": "call_id",
    # Incident endpoints - uses incident_id
    "/incidents/{id}": "incident_id",
    "/incidents/{id}/acknowledge": "incident_id",
    "/incidents/{id}/resolve": "incident_id",
    "/incidents/{id}/export": "incident_id",
    "/incidents/{id}/timeline": "incident_id",
    # Key endpoints - uses key_id
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


def lint_files(filepaths: List[str]) -> List[Tuple[str, int, str, str, str, str]]:
    """Lint specific files for ID type mismatches."""
    all_issues = []
    for fp in filepaths:
        filepath = Path(fp)
        if filepath.suffix in EXTENSIONS and filepath.exists():
            # Skip node_modules and dist
            if "node_modules" in str(filepath) or "/dist/" in str(filepath):
                continue
            all_issues.extend(lint_file(filepath))
    return all_issues


def main():
    # Support --files flag for git-scoped checking
    if len(sys.argv) > 1 and sys.argv[1] == "--files":
        # Read file list from remaining args or stdin
        if len(sys.argv) > 2:
            files = sys.argv[2:]
        else:
            files = [line.strip() for line in sys.stdin if line.strip()]

        if not files:
            print("✅ No frontend files in scope - skipping check")
            sys.exit(0)

        issues = lint_files(files)
    else:
        path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("website/app-shell/src")

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
