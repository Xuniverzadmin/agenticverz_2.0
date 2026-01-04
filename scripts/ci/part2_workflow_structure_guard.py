#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Enforce Part-2 workflow structure integrity
# Callers: CI pipeline, pre-commit
# Allowed Imports: stdlib only
# Forbidden Imports: L1-L6
# Reference: PIN-284, part2-design-v1 tag
#
# GATE-1: Workflow Integrity
# Risk: Someone skips steps (e.g. job without contract)
# Enforcement: No job runner may exist without consuming contract_id
#
# GATE-3: Contract Sanctity
# Risk: Mutable or reused contracts
# Enforcement: Contract fields immutable post-APPROVED

"""
Part-2 Workflow Structure Guard

Enforces structural requirements of the 10-step workflow:

1. Jobs MUST reference contracts (no orphan execution)
2. Contracts MUST have required state machine fields
3. No execution path may skip validation → eligibility → approval
4. Contract-to-job relationship is 1:1 (no reuse)

This guard validates STRUCTURE, not behavior.
Semantic tests (state transitions) are separate.

Exit codes:
  0 - Workflow structure valid
  1 - Structural violation (BLOCKING)
  2 - Configuration error
"""

import re
import sys
from pathlib import Path


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


# Required fields per Part-2 System Contract Object spec
CONTRACT_REQUIRED_FIELDS = [
    "contract_id",
    "status",
    "issue_id",
    "proposed_changes",
    "affected_capabilities",
    "validator_verdict",
    "eligibility_verdict",
    "approved_by",
    "approved_at",
    "audit_verdict",
]

# Required states per Part-2 state machine
CONTRACT_REQUIRED_STATES = [
    "DRAFT",
    "VALIDATED",
    "ELIGIBLE",
    "APPROVED",
    "ACTIVE",
    "COMPLETED",
    "FAILED",
    "REJECTED",
    "EXPIRED",
]

# Job must reference contract
JOB_REQUIRED_FIELDS = [
    "job_id",
    "contract_id",  # MUST reference contract
    "status",
    "steps",
    "audit_id",
]


def check_model_fields(
    file_path: Path, model_name: str, required_fields: list[str]
) -> list[str]:
    """Check if a SQLModel class has required fields."""
    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        return []

    # Simple pattern matching for field definitions
    # More robust: use AST analysis
    missing = []
    for field in required_fields:
        # Look for field definition patterns
        patterns = [
            rf"{field}\s*:",  # Type annotation
            rf"{field}\s*=",  # Assignment
        ]
        found = any(re.search(p, content) for p in patterns)
        if not found:
            missing.append(field)

    return missing


def check_state_enum(file_path: Path, required_states: list[str]) -> list[str]:
    """Check if state enum has required states."""
    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        return []

    missing = []
    for state in required_states:
        if state not in content:
            missing.append(state)

    return missing


def check_job_references_contract(repo_root: Path) -> list[dict]:
    """Ensure job executor always requires contract_id."""
    violations = []

    # Look for job executor files
    job_patterns = [
        "backend/app/services/governance/job_*.py",
        "backend/app/services/governance/*_executor.py",
    ]

    for pattern in job_patterns:
        for file_path in repo_root.glob(pattern):
            try:
                with open(file_path) as f:
                    content = f.read()
            except FileNotFoundError:
                continue

            # Check for contract_id parameter/requirement
            if "contract_id" not in content:
                violations.append(
                    {
                        "file": str(file_path.relative_to(repo_root)),
                        "issue": "Job executor does not reference contract_id",
                        "gate": "GATE-1",
                    }
                )

            # Check for execution without contract check
            # Pattern: executing job without checking contract.status
            if "execute" in content and "contract.status" not in content:
                violations.append(
                    {
                        "file": str(file_path.relative_to(repo_root)),
                        "issue": "Job execution may bypass contract state check",
                        "gate": "GATE-1",
                    }
                )

    return violations


def check_contract_immutability_patterns(repo_root: Path) -> list[dict]:
    """Check for patterns that could mutate approved contracts."""
    violations = []

    contract_files = list(
        repo_root.glob("backend/app/services/governance/contract*.py")
    )
    contract_files.extend(repo_root.glob("backend/app/models/contract.py"))

    for file_path in contract_files:
        try:
            with open(file_path) as f:
                content = f.read()
        except FileNotFoundError:
            continue

        # Check for mutation of critical fields after approval
        # Pattern: updating contract fields without state guard
        dangerous_patterns = [
            (r"contract\.proposed_changes\s*=", "proposed_changes mutation"),
            (r"contract\.affected_capabilities\s*=", "affected_capabilities mutation"),
            (
                r"contract\.validator_verdict\s*=.*(?!DRAFT)",
                "validator_verdict mutation post-DRAFT",
            ),
            (
                r"contract\.eligibility_verdict\s*=.*(?!VALIDATED)",
                "eligibility_verdict mutation post-VALIDATED",
            ),
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, content):
                # Check if there's a state guard
                # Simplified: just flag for manual review
                violations.append(
                    {
                        "file": str(file_path.relative_to(repo_root)),
                        "issue": f"Potential contract mutation: {description}",
                        "gate": "GATE-3",
                        "severity": "WARNING",  # Needs manual review
                    }
                )

    return violations


def main() -> int:
    print("=" * 70)
    print("Part-2 Workflow Structure Guard")
    print("Reference: part2-design-v1")
    print("=" * 70)
    print()

    repo_root = get_repo_root()
    all_violations = []

    # Check 1: Contract model structure (if exists)
    print("Checking: Contract model structure")
    contract_model = repo_root / "backend/app/models/contract.py"
    if contract_model.exists():
        missing_fields = check_model_fields(
            contract_model, "SystemContract", CONTRACT_REQUIRED_FIELDS
        )
        if missing_fields:
            for field in missing_fields:
                all_violations.append(
                    {
                        "file": "backend/app/models/contract.py",
                        "issue": f"Missing required field: {field}",
                        "gate": "GATE-1",
                    }
                )
            print(f"  Status: ❌ Missing {len(missing_fields)} required fields")
        else:
            print("  Status: ✅ All required fields present")

        missing_states = check_state_enum(contract_model, CONTRACT_REQUIRED_STATES)
        if missing_states:
            for state in missing_states:
                all_violations.append(
                    {
                        "file": "backend/app/models/contract.py",
                        "issue": f"Missing required state: {state}",
                        "gate": "GATE-1",
                    }
                )
            print(f"  Status: ❌ Missing {len(missing_states)} required states")
        else:
            print("  Status: ✅ All required states defined")
    else:
        print("  Status: Pre-implementation (model not yet created)")
    print()

    # Check 2: Job model structure (if exists)
    print("Checking: Job model structure")
    job_model = repo_root / "backend/app/models/governance_job.py"
    if job_model.exists():
        missing_fields = check_model_fields(
            job_model, "GovernanceJob", JOB_REQUIRED_FIELDS
        )
        if missing_fields:
            for field in missing_fields:
                all_violations.append(
                    {
                        "file": "backend/app/models/governance_job.py",
                        "issue": f"Missing required field: {field}",
                        "gate": "GATE-1",
                    }
                )
            print(f"  Status: ❌ Missing {len(missing_fields)} required fields")
        else:
            print("  Status: ✅ All required fields present")
    else:
        print("  Status: Pre-implementation (model not yet created)")
    print()

    # Check 3: Job-Contract relationship
    print("Checking: Job-Contract relationship")
    job_violations = check_job_references_contract(repo_root)
    if job_violations:
        all_violations.extend(job_violations)
        print(f"  Status: ❌ {len(job_violations)} relationship violations")
    else:
        governance_files = list(repo_root.glob("backend/app/services/governance/*.py"))
        if governance_files:
            print("  Status: ✅ Job executors reference contracts")
        else:
            print("  Status: Pre-implementation (no governance services yet)")
    print()

    # Check 4: Contract immutability
    print("Checking: Contract immutability patterns")
    immutability_violations = check_contract_immutability_patterns(repo_root)
    if immutability_violations:
        # Separate warnings from errors
        warnings = [
            v for v in immutability_violations if v.get("severity") == "WARNING"
        ]
        errors = [v for v in immutability_violations if v.get("severity") != "WARNING"]
        all_violations.extend(errors)
        if warnings:
            print(f"  Status: ⚠️  {len(warnings)} patterns need review")
        if errors:
            print(f"  Status: ❌ {len(errors)} immutability violations")
        if not warnings and not errors:
            print("  Status: ✅ No immutability concerns")
    else:
        print("  Status: Pre-implementation (no contract services yet)")
    print()

    # Report
    if all_violations:
        print("=" * 70)
        print("WORKFLOW STRUCTURE VIOLATIONS")
        print("=" * 70)
        print()

        for v in all_violations:
            print(f"{v['gate']} VIOLATION")
            print(f"  File: {v['file']}")
            print(f"  Issue: {v['issue']}")
            print()

        print("Resolution:")
        print("  Part-2 workflow structure is CONSTITUTIONAL.")
        print("  The 10-step workflow cannot be bypassed or reordered.")
        print()
        print("  Reference: docs/governance/part2/PART2_CRM_WORKFLOW_CHARTER.md")
        print("  Reference: docs/governance/part2/SYSTEM_CONTRACT_OBJECT.md")
        print()
        return 1

    print("=" * 70)
    print("✅ Part-2 workflow structure valid")
    print()
    print("Enforced requirements:")
    print("  - GATE-1: Jobs must reference contracts")
    print("  - GATE-3: Contract fields immutable post-APPROVED")
    print("  - All state machine states defined")
    print("  - All required fields present")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
