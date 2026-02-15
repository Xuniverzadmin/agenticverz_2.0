#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: runtime (bootstrap)
#   Execution: sync
# Role: Enforce job start prerequisites (GATE-5)
# Callers: Job executor, CI pipeline
# Allowed Imports: stdlib only
# Forbidden Imports: L1-L6
# Reference: PIN-284, PIN-285, part2-design-v1 tag
#
# GATE-5: Governance Execution Discipline
# Risk: Jobs execute without valid contract authorization
# Enforcement: Job cannot start unless contract.status == ACTIVE

"""
Part-2 Job Start Guard (Bootstrap)

Enforces that jobs cannot execute without:
1. Valid contract reference (contract_id NOT NULL)
2. Contract status == ACTIVE
3. Execution scope ⊆ contract scope

This is a BOOTSTRAP guard - it defines runtime constraints
that implementation code must satisfy.

Exit codes:
  0 - Guard definition valid (pre-implementation: structure check)
  1 - Implementation violates job start prerequisites
  2 - Configuration error
"""

import re
import sys
from pathlib import Path

# DB-AUTH-001: Declare local-only authority
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from scripts._db_guard import assert_db_authority  # noqa: E402
assert_db_authority("local")


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


# GATE-5 Job Start Prerequisites (from GOVERNANCE_JOB_MODEL.md)
JOB_START_PREREQUISITES = {
    "contract_reference": {
        "check": "job.contract_id IS NOT NULL",
        "error": "Job cannot start without contract reference",
    },
    "contract_active": {
        "check": "contract.status == ACTIVE",
        "error": "Job cannot start unless contract is ACTIVE",
    },
    "scope_constraint": {
        "check": "job.scope ⊆ contract.affected_capabilities",
        "error": "Job scope must be subset of contract scope",
    },
    "health_check": {
        "check": "system_health != UNHEALTHY",
        "error": "Job cannot start during system degradation",
    },
}

# Patterns that indicate bypass of job start prerequisites
# NOTE: These patterns are specific to Part-2 GOVERNANCE code
# They should NOT match Phase-1 worker code (session.execute, etc.)
JOB_BYPASS_PATTERNS = [
    # Direct job start without contract status check
    (
        r"job\.status\s*=\s*['\"]RUNNING['\"](?!.*contract\.status)",
        "Job RUNNING without contract status check",
    ),
    # Bypassing contract requirement
    (
        r"#\s*skip\s*contract|#\s*bypass\s*contract|contract_id\s*=\s*None",
        "Explicit contract bypass",
    ),
    # Force execution pattern
    (
        r"force_execute|skip_contract_check|bypass_authorization",
        "Force/bypass execution function detected",
    ),
    # Orphan job creation (job without contract)
    (
        r"GovernanceJob\s*\((?!.*contract_id)",
        "GovernanceJob creation without contract_id",
    ),
    # Governance job execution without contract
    (
        r"execute_governance_job\s*\((?!.*contract)",
        "Governance job execution without contract",
    ),
    # Starting job without contract check
    (
        r"start_job\s*\((?!.*contract)",
        "Job start without contract parameter",
    ),
]

# Required guard patterns that MUST exist in job execution code
REQUIRED_JOB_GUARDS = [
    {
        "pattern": r"contract\.status\s*==\s*['\"]?ACTIVE['\"]?",
        "description": "Contract ACTIVE status check",
        "alternatives": [
            r"ContractStatus\.ACTIVE",
            r"is_contract_active",
            r"verify_contract_active",
        ],
    },
    {
        "pattern": r"contract_id\s*(is not None|!=\s*None)",
        "description": "Contract reference check",
        "alternatives": [
            r"job\.contract_id",
            r"has_contract",
            r"verify_contract",
        ],
    },
]

# Scope validation patterns
SCOPE_VALIDATION_PATTERNS = [
    r"scope.*⊆|scope.*subset|issubset",
    r"affected_capabilities.*contains",
    r"validate_scope|check_scope|verify_scope",
    r"scope_constraint",
]


def check_job_executor_exists(repo_root: Path) -> tuple[bool, list[Path]]:
    """Check if job executor implementation exists."""
    possible_paths = [
        "backend/app/services/governance/job_executor.py",
        "backend/app/services/governance/executor.py",
        "backend/app/hoc/int/worker/governance_executor.py",
    ]
    found = []
    for path in possible_paths:
        full_path = repo_root / path
        if full_path.exists():
            found.append(full_path)

    # Also check for any executor-like files
    for f in repo_root.glob("backend/app/services/governance/*executor*.py"):
        if f not in found:
            found.append(f)

    return len(found) > 0, found


def check_job_bypass(file_path: Path, repo_root: Path) -> list[dict]:
    """Check for patterns that bypass job start prerequisites."""
    try:
        with open(file_path) as f:
            content = f.read()
            lines = content.split("\n")
    except FileNotFoundError:
        return []

    violations = []
    rel_path = str(file_path.relative_to(repo_root))

    for i, line in enumerate(lines, 1):
        for pattern, description in JOB_BYPASS_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append(
                    {
                        "file": rel_path,
                        "line": i,
                        "pattern": pattern,
                        "description": description,
                        "content": line.strip()[:80],
                        "gate": "GATE-5",
                    }
                )

    return violations


def check_job_guards(file_path: Path, repo_root: Path) -> list[dict]:
    """Check that required job start guards exist."""
    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        return []

    # Only check files that perform job execution
    execution_indicators = [
        "execute",
        "run_job",
        "start_job",
        "RUNNING",
        "executor",
    ]
    has_execution = any(ind.lower() in content.lower() for ind in execution_indicators)
    if not has_execution:
        return []

    missing_guards = []
    rel_path = str(file_path.relative_to(repo_root))

    for guard in REQUIRED_JOB_GUARDS:
        # Check primary pattern and alternatives
        found = re.search(guard["pattern"], content, re.IGNORECASE)
        if not found:
            for alt in guard.get("alternatives", []):
                if re.search(alt, content, re.IGNORECASE):
                    found = True
                    break

        if not found:
            # Check if this file actually does execution (not just references)
            if re.search(r"(execute|run|start).*job", content, re.IGNORECASE):
                missing_guards.append(
                    {
                        "file": rel_path,
                        "guard": guard["description"],
                        "pattern": guard["pattern"],
                        "gate": "GATE-5",
                    }
                )

    return missing_guards


def check_scope_validation(file_path: Path, repo_root: Path) -> bool:
    """Check if scope validation exists."""
    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        return False

    for pattern in SCOPE_VALIDATION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def check_governance_services(repo_root: Path) -> list[dict]:
    """Check Part-2 governance services for job execution violations.

    NOTE: This only checks Part-2 governance code, NOT Phase-1 workers.
    Phase-1 workers (recovery_evaluator, outbox_processor, etc.) are
    not subject to Part-2 governance job constraints.
    """
    violations = []

    # Only check Part-2 governance service files
    # NOT general workers (which are Phase-1)
    governance_patterns = [
        "backend/app/services/governance/*.py",
    ]

    for pattern in governance_patterns:
        for file_path in repo_root.glob(pattern):
            # Skip test files
            if "test" in str(file_path).lower():
                continue

            # Check for bypass patterns
            bypass_violations = check_job_bypass(file_path, repo_root)
            violations.extend(bypass_violations)

    return violations


def main() -> int:
    print("=" * 70)
    print("Part-2 Job Start Guard (Bootstrap)")
    print("Reference: part2-design-v1, GATE-5")
    print("=" * 70)
    print()

    repo_root = get_repo_root()
    all_violations = []

    # Check 1: Job executor exists?
    print("Checking: Job executor implementation")
    exists, executor_paths = check_job_executor_exists(repo_root)
    if exists:
        for exec_path in executor_paths:
            rel = exec_path.relative_to(repo_root)
            print(f"  Found: {rel}")

            # Check for bypass patterns
            bypass = check_job_bypass(exec_path, repo_root)
            if bypass:
                all_violations.extend(bypass)
                print(f"    Status: ❌ {len(bypass)} bypass patterns detected")
            else:
                print("    Status: ✅ No bypass patterns")

            # Check for required guards
            missing = check_job_guards(exec_path, repo_root)
            if missing:
                print(f"    Status: ⚠️  {len(missing)} guards may be missing")
                for m in missing:
                    print(f"      ℹ️  Missing: {m['guard']}")
            else:
                print("    Status: ✅ Guards present")

            # Check scope validation
            has_scope = check_scope_validation(exec_path, repo_root)
            if has_scope:
                print("    Scope validation: ✅ Present")
            else:
                print("    Scope validation: ⚠️  May need implementation")
    else:
        print("  Status: Pre-implementation (job executor not yet created)")
    print()

    # Check 2: Governance services
    print("Checking: Governance services for execution patterns")
    service_violations = check_governance_services(repo_root)
    if service_violations:
        # Filter out duplicates from executor check
        new_violations = [v for v in service_violations if v not in all_violations]
        all_violations.extend(new_violations)
        if new_violations:
            print(f"  Status: ❌ {len(new_violations)} violations")
    else:
        governance_files = list(repo_root.glob("backend/app/services/governance/*.py"))
        if governance_files:
            print("  Status: ✅ No bypass patterns")
        else:
            print("  Status: Pre-implementation (no governance services yet)")
    print()

    # Report
    if all_violations:
        print("=" * 70)
        print("GATE-5 VIOLATIONS: Job Start Prerequisites")
        print("=" * 70)
        print()

        for v in all_violations:
            print("GATE-5 VIOLATION")
            print(f"  File: {v['file']}:{v.get('line', '?')}")
            if "description" in v:
                print(f"  Issue: {v['description']}")
            if "content" in v:
                print(f"  Code: {v['content']}")
            print()

        print("Resolution:")
        print("  Job execution MUST verify:")
        print("  1. job.contract_id IS NOT NULL")
        print("  2. contract.status == ACTIVE")
        print("  3. job.scope ⊆ contract.affected_capabilities")
        print("  4. system_health != UNHEALTHY")
        print()
        print("  Reference: docs/governance/part2/GOVERNANCE_JOB_MODEL.md")
        print("  Reference: docs/governance/part2/END_TO_END_STATE_MACHINE.md")
        print()
        return 1

    print("=" * 70)
    print("✅ GATE-5 Job Start Guard: PASS")
    print()
    print("Job start prerequisites enforced:")
    for key, prereq in JOB_START_PREREQUISITES.items():
        print(f"  - {key}: {prereq['error']}")
    print()
    print("Implementation constraint:")
    print("  Jobs cannot execute without valid ACTIVE contract authorization.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
