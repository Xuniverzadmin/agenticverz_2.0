#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Enforce Phase-1 health supremacy in Part-2 context
# Callers: CI pipeline, pre-commit
# Allowed Imports: stdlib only
# Forbidden Imports: L1-L6
# Reference: PIN-284, platform-health-v1, part2-design-v1
#
# GATE-6: Health Supremacy
# Risk: Contracts or jobs manipulate health
# Enforcement: No Part-2 module writes to health tables directly

"""
Part-2 Health Supremacy Guard

Extends Phase-1 health supremacy to Part-2 governance modules.

Phase-1 Invariants (preserved):
- HEALTH-IS-AUTHORITY
- HEALTH-LIFECYCLE-COHERENCE
- HEALTH-DETERMINISM
- NO-PHANTOM-HEALTH
- DOMINANCE-ORDER

Part-2 Additions:
- Contracts cannot modify health signals
- Jobs cannot override platform health
- Audit reads health, never writes
- Only PlatformHealthService may write health

Exit codes:
  0 - Health supremacy intact
  1 - Health supremacy violation (BLOCKING)
  2 - Configuration error
"""

import re
import sys
from pathlib import Path

# Modules that may NOT write health signals
PART2_NO_HEALTH_WRITE_MODULES = [
    "backend/app/services/governance/*.py",
    "backend/app/models/contract.py",
    "backend/app/models/governance_job.py",
    "backend/app/models/governance_audit.py",
    "backend/app/api/contracts.py",
    "backend/app/api/governance_jobs.py",
]

# Only these modules may write health signals (Phase-1 frozen)
HEALTH_WRITE_AUTHORIZED = [
    "backend/app/services/platform/platform_health_service.py",
    "scripts/ops/record_governance_signal.py",  # L8 CLI only
]

# Patterns that indicate health signal writes
HEALTH_WRITE_PATTERNS = [
    r"GovernanceSignal\(",
    r"governance_signals\.insert",
    r"session\.add\(.*GovernanceSignal",
    r"\.add\(GovernanceSignal",
    r"health_status.*=.*['\"]HEALTHY",
    r"health_status.*=.*['\"]UNHEALTHY",
    r"health_status.*=.*['\"]DEGRADED",
    r"record_signal\(",  # Direct call to record_governance_signal
]

# Patterns that indicate health signal reads (allowed)
HEALTH_READ_PATTERNS = [
    r"get_system_health\(",
    r"get_capability_health\(",
    r"platform_health_service\.",
    r"health_snapshot",
]


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


def check_health_writes(file_path: Path, repo_root: Path) -> list[dict]:
    """Check for unauthorized health signal writes."""
    try:
        with open(file_path) as f:
            content = f.read()
            lines = content.split("\n")
    except FileNotFoundError:
        return []

    violations = []
    rel_path = str(file_path.relative_to(repo_root))

    # Check if this file is authorized to write
    is_authorized = any(
        rel_path == auth or rel_path.endswith(auth.split("/")[-1])
        for auth in HEALTH_WRITE_AUTHORIZED
    )

    if is_authorized:
        return []

    # Check for write patterns
    for i, line in enumerate(lines, 1):
        for pattern in HEALTH_WRITE_PATTERNS:
            if re.search(pattern, line):
                violations.append(
                    {
                        "file": rel_path,
                        "line": i,
                        "pattern": pattern,
                        "content": line.strip()[:80],
                        "gate": "GATE-6",
                    }
                )

    return violations


def check_health_read_patterns(file_path: Path, repo_root: Path) -> list[str]:
    """Check for proper health read patterns (informational)."""
    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        return []

    reads = []
    for pattern in HEALTH_READ_PATTERNS:
        if re.search(pattern, content):
            reads.append(pattern)

    return reads


def main() -> int:
    print("=" * 70)
    print("Part-2 Health Supremacy Guard")
    print("Reference: platform-health-v1, part2-design-v1")
    print("=" * 70)
    print()

    repo_root = get_repo_root()
    all_violations = []

    # Check Part-2 modules for health writes
    print("Checking Part-2 modules for unauthorized health writes...")
    print()

    for pattern in PART2_NO_HEALTH_WRITE_MODULES:
        files = list(repo_root.glob(pattern))
        if not files:
            print(f"  {pattern}: Pre-implementation (no files)")
            continue

        pattern_violations = []
        pattern_reads = []

        for file_path in files:
            violations = check_health_writes(file_path, repo_root)
            pattern_violations.extend(violations)

            reads = check_health_read_patterns(file_path, repo_root)
            if reads:
                pattern_reads.append((file_path, reads))

        if pattern_violations:
            print(f"  {pattern}: ❌ {len(pattern_violations)} violations")
            all_violations.extend(pattern_violations)
        else:
            print(f"  {pattern}: ✅ No unauthorized writes ({len(files)} files)")

        # Informational: show health reads (these are allowed)
        if pattern_reads:
            for fp, reads in pattern_reads:
                rel = fp.relative_to(repo_root)
                print(f"    ℹ️  {rel} reads health via: {', '.join(reads)}")

    print()

    # Verify authorized modules exist
    print("Verifying authorized health writers (Phase-1)...")
    for auth in HEALTH_WRITE_AUTHORIZED:
        auth_path = repo_root / auth
        if auth_path.exists():
            print(f"  ✓ {auth}")
        else:
            print(f"  ⚠️  {auth} (not yet created)")
    print()

    if all_violations:
        print("=" * 70)
        print("HEALTH SUPREMACY VIOLATIONS")
        print("=" * 70)
        print()

        for v in all_violations:
            print("GATE-6 VIOLATION")
            print(f"  File: {v['file']}:{v['line']}")
            print(f"  Pattern: {v['pattern']}")
            print(f"  Content: {v['content']}")
            print()

        print("Resolution:")
        print("  Part-2 modules CANNOT write health signals directly.")
        print("  Health is controlled by PlatformHealthService (Phase-1).")
        print()
        print("  To record governance outcomes:")
        print("  1. Use PlatformHealthService.evaluate_execution()")
        print("  2. Let health service determine health impact")
        print("  3. Never write GovernanceSignal directly from Part-2 code")
        print()
        print("  Phase-1 Reference: docs/governance/PHASE_1_CLOSURE_NOTE.md")
        print("  Part-2 Reference: docs/governance/part2/PART2_CLOSURE_NOTE.md")
        print()
        return 1

    print("=" * 70)
    print("✅ Phase-1 health supremacy preserved in Part-2")
    print()
    print("Invariants enforced:")
    print("  - HEALTH-IS-AUTHORITY: Health > Contract > Job")
    print("  - NO-PHANTOM-HEALTH: Only authorized writers")
    print("  - Part-2 modules may READ health, never WRITE")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
