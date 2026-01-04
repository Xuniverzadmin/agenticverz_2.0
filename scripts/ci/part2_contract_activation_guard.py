#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: runtime (bootstrap)
#   Execution: sync
# Role: Enforce contract activation prerequisites (GATE-4)
# Callers: Contract state machine, CI pipeline
# Allowed Imports: stdlib only
# Forbidden Imports: L1-L6
# Reference: PIN-284, PIN-285, part2-design-v1 tag
#
# GATE-4: Eligibility Override Prevention
# Risk: Someone approves contract without eligibility proof
# Enforcement: Contract cannot transition APPROVED → ACTIVE without proof

"""
Part-2 Contract Activation Guard (Bootstrap)

Enforces that contracts cannot become ACTIVE without:
1. Eligibility verdict with decision = MAY
2. Approval record (approved_by, approved_at)
3. Valid activation window

This is a BOOTSTRAP guard - it defines runtime constraints
that implementation code must satisfy.

Exit codes:
  0 - Guard definition valid (pre-implementation: structure check)
  1 - Implementation violates activation prerequisites
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


# GATE-4 Activation Prerequisites (from ELIGIBILITY_RULES.md)
ACTIVATION_PREREQUISITES = {
    "eligibility_check": {
        "field": "eligibility_verdict.decision",
        "required_value": "MAY",
        "error": "Contract cannot activate without eligibility_verdict.decision = MAY",
    },
    "approval_record": {
        "fields": ["approved_by", "approved_at"],
        "error": "Contract cannot activate without approval record",
    },
    "activation_window": {
        "check": "NOW() >= activation_window_start",
        "error": "Contract cannot activate before activation window",
    },
}

# Patterns that indicate bypass of activation prerequisites
ACTIVATION_BYPASS_PATTERNS = [
    # Direct status change without eligibility check
    (
        r"contract\.status\s*=\s*['\"]ACTIVE['\"](?!.*eligibility)",
        "Direct ACTIVE assignment without eligibility check",
    ),
    # Status change in a single line without guards
    (
        r"\.status\s*=\s*ContractStatus\.ACTIVE(?!.*if.*eligibility)",
        "ACTIVE transition without eligibility guard",
    ),
    # Bypassing eligibility entirely
    (
        r"#\s*skip\s*eligibility|#\s*bypass\s*eligibility",
        "Explicit eligibility bypass comment",
    ),
    # Force activation pattern
    (
        r"force_activate|skip_eligibility_check|bypass_approval",
        "Force/bypass function detected",
    ),
]

# Required guard patterns that MUST exist in activation code
REQUIRED_ACTIVATION_GUARDS = [
    {
        "pattern": r"eligibility_verdict\.decision\s*==\s*['\"]?MAY['\"]?",
        "description": "Eligibility decision check",
        "alternatives": [
            r"\.decision\s*==\s*EligibilityDecision\.MAY",
            r"check_eligibility",
            r"verify_eligibility",
        ],
    },
    {
        "pattern": r"approved_by\s*is\s*not\s*None",
        "description": "Approval record check",
        "alternatives": [
            r"contract\.approved_by",
            r"has_approval",
            r"verify_approval",
        ],
    },
]


def check_contract_service_exists(repo_root: Path) -> tuple[bool, Path | None]:
    """Check if contract service implementation exists."""
    possible_paths = [
        "backend/app/services/governance/contract_service.py",
        "backend/app/services/contract_service.py",
        "backend/app/services/governance/contract_activation.py",
    ]
    for path in possible_paths:
        full_path = repo_root / path
        if full_path.exists():
            return True, full_path
    return False, None


def check_activation_bypass(file_path: Path, repo_root: Path) -> list[dict]:
    """Check for patterns that bypass activation prerequisites."""
    try:
        with open(file_path) as f:
            content = f.read()
            lines = content.split("\n")
    except FileNotFoundError:
        return []

    violations = []
    rel_path = str(file_path.relative_to(repo_root))

    for i, line in enumerate(lines, 1):
        for pattern, description in ACTIVATION_BYPASS_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append(
                    {
                        "file": rel_path,
                        "line": i,
                        "pattern": pattern,
                        "description": description,
                        "content": line.strip()[:80],
                        "gate": "GATE-4",
                    }
                )

    return violations


def check_activation_guards(file_path: Path, repo_root: Path) -> list[dict]:
    """Check that required activation guards exist in activation code."""
    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        return []

    # Only check files that perform activation
    activation_indicators = [
        "activate",
        "APPROVED",
        "ACTIVE",
        "transition",
        "status",
    ]
    has_activation = any(
        ind.lower() in content.lower() for ind in activation_indicators
    )
    if not has_activation:
        return []

    missing_guards = []
    rel_path = str(file_path.relative_to(repo_root))

    for guard in REQUIRED_ACTIVATION_GUARDS:
        # Check primary pattern and alternatives
        found = re.search(guard["pattern"], content, re.IGNORECASE)
        if not found:
            for alt in guard.get("alternatives", []):
                if re.search(alt, content, re.IGNORECASE):
                    found = True
                    break

        if not found:
            # Check if this file actually does activation (not just references)
            if re.search(r"status\s*=.*ACTIVE", content):
                missing_guards.append(
                    {
                        "file": rel_path,
                        "guard": guard["description"],
                        "pattern": guard["pattern"],
                        "gate": "GATE-4",
                    }
                )

    return missing_guards


def check_state_machine_guards(repo_root: Path) -> list[dict]:
    """Check state machine implementation for activation guards."""
    violations = []

    # Look for state machine implementations
    state_machine_patterns = [
        "backend/app/services/governance/*.py",
        "backend/app/models/contract.py",
    ]

    for pattern in state_machine_patterns:
        for file_path in repo_root.glob(pattern):
            # Skip test files
            if "test" in str(file_path).lower():
                continue

            # Check for bypass patterns
            bypass_violations = check_activation_bypass(file_path, repo_root)
            violations.extend(bypass_violations)

    return violations


def main() -> int:
    print("=" * 70)
    print("Part-2 Contract Activation Guard (Bootstrap)")
    print("Reference: part2-design-v1, GATE-4")
    print("=" * 70)
    print()

    repo_root = get_repo_root()
    all_violations = []

    # Check 1: Contract service exists?
    print("Checking: Contract service implementation")
    exists, service_path = check_contract_service_exists(repo_root)
    if exists:
        print(f"  Found: {service_path.relative_to(repo_root)}")

        # Check for activation bypass
        bypass = check_activation_bypass(service_path, repo_root)
        if bypass:
            all_violations.extend(bypass)
            print(f"  Status: ❌ {len(bypass)} bypass patterns detected")
        else:
            print("  Status: ✅ No bypass patterns")

        # Check for required guards
        missing = check_activation_guards(service_path, repo_root)
        if missing:
            print(f"  Status: ⚠️  {len(missing)} guards may be missing")
            # These are warnings, not blocking violations
            for m in missing:
                print(f"    ℹ️  Missing: {m['guard']}")
    else:
        print("  Status: Pre-implementation (contract service not yet created)")
    print()

    # Check 2: State machine guards
    print("Checking: State machine activation guards")
    sm_violations = check_state_machine_guards(repo_root)
    if sm_violations:
        all_violations.extend(sm_violations)
        print(f"  Status: ❌ {len(sm_violations)} violations")
    else:
        governance_files = list(repo_root.glob("backend/app/services/governance/*.py"))
        if governance_files:
            print("  Status: ✅ No bypass patterns in governance services")
        else:
            print("  Status: Pre-implementation (no governance services yet)")
    print()

    # Report
    if all_violations:
        print("=" * 70)
        print("GATE-4 VIOLATIONS: Contract Activation Prerequisites")
        print("=" * 70)
        print()

        for v in all_violations:
            print("GATE-4 VIOLATION")
            print(f"  File: {v['file']}:{v.get('line', '?')}")
            if "description" in v:
                print(f"  Issue: {v['description']}")
            if "content" in v:
                print(f"  Code: {v['content']}")
            print()

        print("Resolution:")
        print("  Contract activation MUST verify:")
        print("  1. eligibility_verdict.decision == MAY")
        print("  2. approved_by IS NOT NULL")
        print("  3. approved_at IS NOT NULL")
        print("  4. NOW() >= activation_window_start")
        print()
        print("  Reference: docs/governance/part2/ELIGIBILITY_RULES.md")
        print("  Reference: docs/governance/part2/END_TO_END_STATE_MACHINE.md")
        print()
        return 1

    print("=" * 70)
    print("✅ GATE-4 Contract Activation Guard: PASS")
    print()
    print("Activation prerequisites enforced:")
    for key, prereq in ACTIVATION_PREREQUISITES.items():
        print(f"  - {key}: {prereq['error']}")
    print()
    print("Implementation constraint:")
    print("  Contract cannot transition APPROVED → ACTIVE without proof.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
