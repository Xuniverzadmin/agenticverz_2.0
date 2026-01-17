#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Migration lineage verification
# Reference: docs/architecture/contracts/MIGRATIONS.md

"""
Alembic Parent Check

Verifies migration lineage:
- MIGRATION_CONTRACT header present
- Parent revision exists in versions/
- down_revision matches MIGRATION_CONTRACT.parent
- No multiple heads
"""

import re
import sys
from pathlib import Path
from typing import NamedTuple


class MigrationInfo(NamedTuple):
    file: Path
    revision: str
    down_revision: str | None
    contract_parent: str | None
    has_contract: bool


class Violation(NamedTuple):
    file: str
    issue: str
    details: str


def parse_migration(file_path: Path) -> MigrationInfo | None:
    """Parse a migration file for revision info."""
    content = file_path.read_text()

    # Extract revision
    revision_match = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if not revision_match:
        return None

    revision = revision_match.group(1)

    # Extract down_revision
    down_rev_match = re.search(r'^down_revision\s*=\s*["\']?([^"\'"\n]+)["\']?', content, re.MULTILINE)
    down_revision = down_rev_match.group(1) if down_rev_match else None
    if down_revision == "None":
        down_revision = None

    # Extract MIGRATION_CONTRACT parent
    contract_match = re.search(r'#\s*parent:\s*(\S+)', content)
    contract_parent = contract_match.group(1) if contract_match else None

    # Check if has MIGRATION_CONTRACT header
    has_contract = "MIGRATION_CONTRACT:" in content

    return MigrationInfo(
        file=file_path,
        revision=revision,
        down_revision=down_revision,
        contract_parent=contract_parent,
        has_contract=has_contract,
    )


def get_all_migrations(versions_path: Path) -> dict[str, MigrationInfo]:
    """Get all migrations indexed by revision."""
    migrations = {}

    for py_file in versions_path.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        info = parse_migration(py_file)
        if info:
            migrations[info.revision] = info

    return migrations


def check_single_migration(
    info: MigrationInfo,
    all_revisions: set[str],
    versions_path: Path
) -> list[Violation]:
    """Check a single migration for violations."""
    violations = []
    rel_path = str(info.file.relative_to(versions_path.parent.parent))

    # Check 1: MIGRATION_CONTRACT header present
    if not info.has_contract:
        violations.append(Violation(
            file=rel_path,
            issue="Missing MIGRATION_CONTRACT header",
            details="Every migration must start with MIGRATION_CONTRACT block"
        ))

    # Check 2: Contract parent matches down_revision
    if info.has_contract and info.contract_parent and info.down_revision:
        if info.contract_parent != info.down_revision:
            violations.append(Violation(
                file=rel_path,
                issue="Contract/down_revision mismatch",
                details=f"MIGRATION_CONTRACT.parent: {info.contract_parent}\n"
                       f"  down_revision: {info.down_revision}"
            ))

    # Check 3: Parent revision exists
    if info.down_revision and info.down_revision not in all_revisions:
        # Find similar revisions for suggestion
        similar = [r for r in all_revisions if info.down_revision[:10] in r]
        suggestion = f"\n  Did you mean: {similar[0]}" if similar else ""

        violations.append(Violation(
            file=rel_path,
            issue="Parent revision not found",
            details=f"down_revision: {info.down_revision}{suggestion}"
        ))

    return violations


def check_multiple_heads(migrations: dict[str, MigrationInfo]) -> list[str]:
    """Find migrations that are heads (not referenced as parent by any other)."""
    all_revisions = set(migrations.keys())
    referenced_as_parent = {m.down_revision for m in migrations.values() if m.down_revision}

    heads = all_revisions - referenced_as_parent
    return sorted(heads)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Check Alembic migration lineage")
    parser.add_argument("revision", nargs="?", help="Specific revision to check")
    parser.add_argument("--all", action="store_true", help="Check all migrations")
    args = parser.parse_args()

    backend_path = Path(__file__).parent.parent.parent / "backend"
    versions_path = backend_path / "alembic" / "versions"

    if not versions_path.exists():
        print(f"Versions path not found: {versions_path}")
        sys.exit(1)

    print("MIGRATION LINEAGE CHECK")
    print("=" * 60)

    migrations = get_all_migrations(versions_path)
    all_revisions = set(migrations.keys())

    if not migrations:
        print("No migrations found")
        sys.exit(0)

    print(f"\nFound {len(migrations)} migrations")

    all_violations = []

    # Check specific revision or all
    if args.revision:
        if args.revision not in migrations:
            print(f"\n✗ Revision not found: {args.revision}")
            print(f"\nAvailable revisions:")
            for rev in sorted(all_revisions):
                print(f"  - {rev}")
            sys.exit(1)

        violations = check_single_migration(
            migrations[args.revision],
            all_revisions,
            versions_path
        )
        all_violations.extend(violations)
    else:
        # Check all migrations
        print("\n▶ Checking all migrations...")
        for info in migrations.values():
            violations = check_single_migration(info, all_revisions, versions_path)
            all_violations.extend(violations)

    # Check for multiple heads
    print("\n▶ Checking for multiple heads...")
    heads = check_multiple_heads(migrations)

    if len(heads) > 1:
        all_violations.append(Violation(
            file="alembic/versions/",
            issue="Multiple heads detected",
            details=f"Heads: {', '.join(heads)}\n  "
                   f"Only one head should exist. Merge or rebase required."
        ))
        print(f"  Found {len(heads)} heads (should be 1)")
    else:
        print(f"  Single head: {heads[0] if heads else 'none'}")

    # Summary
    print("\n" + "=" * 60)

    if not all_violations:
        print("✓ MIGRATION LINEAGE CHECK: PASSED")
        print(f"  - Migrations checked: {len(migrations)}")
        print(f"  - All have MIGRATION_CONTRACT: YES")
        print(f"  - All parents exist: YES")
        print(f"  - Single head: {heads[0] if heads else 'none'}")
        sys.exit(0)
    else:
        print("✗ MIGRATION LINEAGE CHECK: FAILED")
        print(f"\nTotal violations: {len(all_violations)}\n")

        for i, v in enumerate(all_violations, 1):
            print(f"Violation {i}:")
            print(f"  File: {v.file}")
            print(f"  Issue: {v.issue}")
            print(f"  Details: {v.details}")
            print()

        print("Reference: docs/architecture/contracts/MIGRATIONS.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
