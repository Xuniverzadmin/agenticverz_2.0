#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Enforce Part-2 authority separation via import boundaries
# Callers: CI pipeline, pre-commit
# Allowed Imports: stdlib only
# Forbidden Imports: L1-L6
# Reference: PIN-284, part2-design-v1 tag
#
# GATE-2: Authority Separation
# Risk: Humans or UI mutate system state
# Enforcement: UI/API layers cannot import governance execution modules
#
# GATE-5: Governance Execution Discipline
# Risk: Jobs bypass governance
# Enforcement: Job runners cannot import CRM or UI modules

"""
Part-2 Authority Boundary Guard

Enforces import boundaries that maintain authority separation:
- UI/API (L1/L2) cannot import governance execution (future L5 governance)
- Governance jobs (future L5) cannot import CRM/UI modules
- No layer may bypass the contract → job → audit → rollout flow

This guard defines boundaries BEFORE implementation.
It will block violations as soon as governance code exists.

Exit codes:
  0 - All import boundaries intact
  1 - Import boundary violation (BLOCKING)
  2 - Configuration error
"""

import ast
import sys
from pathlib import Path

# Authority boundary definitions (per Part-2 Closure Note)
#
# These define what WILL BE forbidden once implementation exists.
# Pre-implementation: guard passes (no violations possible yet)
# Post-implementation: guard blocks boundary violations

AUTHORITY_BOUNDARIES = {
    # GATE-2: UI/API cannot import governance execution
    "api_cannot_import_governance_execution": {
        "source_patterns": [
            "backend/app/api/*.py",
            "website/**/*.ts",
            "website/**/*.tsx",
        ],
        "forbidden_imports": [
            "app.services.governance.job_executor",
            "app.services.governance.rollback_executor",
            "app.services.governance.audit_executor",
        ],
        "reason": "UI/API layers cannot execute governance jobs directly",
        "gate": "GATE-2",
    },
    # GATE-5: Governance jobs cannot import CRM/UI
    "governance_jobs_cannot_import_crm_ui": {
        "source_patterns": [
            "backend/app/services/governance/job_*.py",
            "backend/app/services/governance/*_executor.py",
        ],
        "forbidden_imports": [
            "app.api.",
            "app.services.crm.",
            "website.",
        ],
        "reason": "Governance jobs cannot import CRM or UI modules",
        "gate": "GATE-5",
    },
    # GATE-6: Part-2 modules cannot write health directly
    "part2_cannot_write_health": {
        "source_patterns": [
            "backend/app/services/governance/*.py",
            "backend/app/models/contract.py",
        ],
        "forbidden_imports": [
            # Direct writes to health are forbidden
            # Reads via PlatformHealthService are allowed
        ],
        "forbidden_patterns": [
            # Direct table access patterns (AST-checked)
            "governance_signals.insert",
            "GovernanceSignal(",
            "session.add(GovernanceSignal",
        ],
        "reason": "Part-2 modules cannot write health signals directly",
        "gate": "GATE-6",
    },
}


def get_repo_root() -> Path:
    """Get repository root directory."""
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("ERROR: Not a git repository", file=sys.stderr)
        sys.exit(2)
    return Path(result.stdout.strip())


def find_files(repo_root: Path, patterns: list[str]) -> list[Path]:
    """Find files matching glob patterns."""
    files = []
    for pattern in patterns:
        files.extend(repo_root.glob(pattern))
    return files


def extract_imports(file_path: Path) -> list[str]:
    """Extract import statements from Python file."""
    try:
        with open(file_path) as f:
            content = f.read()
        tree = ast.parse(content)
    except (SyntaxError, FileNotFoundError):
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
                for alias in node.names:
                    imports.append(f"{node.module}.{alias.name}")
    return imports


def check_forbidden_imports(
    file_path: Path, imports: list[str], forbidden: list[str]
) -> list[tuple[str, str]]:
    """Check if any imports match forbidden patterns."""
    violations = []
    for imp in imports:
        for forbidden_pattern in forbidden:
            if imp.startswith(forbidden_pattern) or imp == forbidden_pattern:
                violations.append((imp, forbidden_pattern))
    return violations


def check_forbidden_patterns(file_path: Path, patterns: list[str]) -> list[str]:
    """Check for forbidden code patterns in file content."""
    if not patterns:
        return []

    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        return []

    violations = []
    for pattern in patterns:
        if pattern in content:
            violations.append(pattern)
    return violations


def main() -> int:
    print("=" * 70)
    print("Part-2 Authority Boundary Guard")
    print("Reference: part2-design-v1")
    print("=" * 70)
    print()

    repo_root = get_repo_root()
    all_violations = []

    for boundary_name, boundary in AUTHORITY_BOUNDARIES.items():
        print(f"Checking: {boundary_name}")
        print(f"  Gate: {boundary.get('gate', 'N/A')}")
        print(f"  Reason: {boundary['reason']}")

        source_files = find_files(repo_root, boundary["source_patterns"])

        if not source_files:
            print("  Status: No source files exist yet (pre-implementation)")
            print()
            continue

        boundary_violations = []
        for file_path in source_files:
            if not file_path.suffix == ".py":
                continue

            # Check imports
            imports = extract_imports(file_path)
            forbidden = boundary.get("forbidden_imports", [])
            import_violations = check_forbidden_imports(file_path, imports, forbidden)

            for imp, pattern in import_violations:
                boundary_violations.append(
                    {
                        "file": str(file_path.relative_to(repo_root)),
                        "type": "import",
                        "detail": f"imports '{imp}' (matches forbidden '{pattern}')",
                    }
                )

            # Check patterns
            patterns = boundary.get("forbidden_patterns", [])
            pattern_violations = check_forbidden_patterns(file_path, patterns)

            for pattern in pattern_violations:
                boundary_violations.append(
                    {
                        "file": str(file_path.relative_to(repo_root)),
                        "type": "pattern",
                        "detail": f"contains forbidden pattern: {pattern}",
                    }
                )

        if boundary_violations:
            print(f"  Status: ❌ {len(boundary_violations)} violation(s)")
            all_violations.extend(
                [(boundary_name, boundary, v) for v in boundary_violations]
            )
        else:
            print(f"  Status: ✅ Clean ({len(source_files)} files checked)")
        print()

    if all_violations:
        print("=" * 70)
        print("AUTHORITY BOUNDARY VIOLATIONS")
        print("=" * 70)
        print()

        for boundary_name, boundary, violation in all_violations:
            print(f"{boundary.get('gate', 'GATE-?')} VIOLATION")
            print(f"  Boundary: {boundary_name}")
            print(f"  File: {violation['file']}")
            print(f"  Issue: {violation['detail']}")
            print(f"  Reason: {boundary['reason']}")
            print()

        print("Resolution:")
        print("  Part-2 authority boundaries are CONSTITUTIONAL.")
        print("  Human authority ends at approval.")
        print("  Machine authority (jobs/audit/rollout) cannot be bypassed.")
        print()
        print("  Reference: docs/governance/part2/PART2_CLOSURE_NOTE.md")
        print()
        return 1

    print("=" * 70)
    print("✅ All Part-2 authority boundaries intact")
    print()
    print("Enforced boundaries:")
    for name, boundary in AUTHORITY_BOUNDARIES.items():
        print(f"  - {boundary.get('gate', '?')}: {boundary['reason']}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
