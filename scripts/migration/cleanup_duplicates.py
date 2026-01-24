#!/usr/bin/env python3
"""
Cleanup Duplicate Files from HOC Migration

Removes duplicate files that were created during migration.
Based on HOC layer architecture:
- Services belong in drivers/ (L6) not engines/
- Facades belong in facades/ (L3) not engines/

Usage:
    python scripts/migration/cleanup_duplicates.py --dry-run   # Preview
    python scripts/migration/cleanup_duplicates.py             # Execute
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Change to repo root
os.chdir(Path(__file__).parent.parent.parent)

DRY_RUN = "--dry-run" in sys.argv

# Files to remove (wrong location based on layer model)
# Format: (file_to_remove, reason)
DUPLICATES_TO_REMOVE = [
    # incidents - services should be in drivers/, not engines/
    ("backend/app/hoc/cus/incidents/L5_engines/incident_read_service.py",
     "IDENTICAL: Service belongs in drivers/ (L6), not engines/"),
    ("backend/app/hoc/cus/incidents/L5_engines/incident_write_service.py",
     "IDENTICAL: Service belongs in drivers/ (L6), not engines/"),

    # policies - services should be in drivers/, facades in facades/
    ("backend/app/hoc/cus/policies/controls/engines/customer_killswitch_read_service.py",
     "IDENTICAL: Service belongs in drivers/ (L6), not controls/engines/"),
    ("backend/app/hoc/cus/policies/L5_engines/customer_policy_read_service.py",
     "IDENTICAL: Service belongs in drivers/ (L6), not engines/"),
    ("backend/app/hoc/cus/policies/L5_engines/governance_facade.py",
     "IDENTICAL: Facade belongs in facades/ (L3), not engines/"),
    ("backend/app/hoc/cus/policies/L5_engines/limits_facade.py",
     "IDENTICAL: Facade belongs in facades/ (L3), not engines/"),

    # logs - facades belong in facades/
    ("backend/app/hoc/cus/logs/L5_engines/evidence_facade.py",
     "IDENTICAL: Facade belongs in facades/ (L3), not engines/"),

    # analytics - services should be in drivers/
    ("backend/app/hoc/cus/analytics/L5_engines/cost_write_service.py",
     "IDENTICAL: Service belongs in drivers/ (L6), not engines/"),

    # integrations - keep the main location, remove subdirectory duplicates
    ("backend/app/hoc/cus/integrations/vault/engines/cus_credential_service.py",
     "IDENTICAL: Already exists in integrations/engines/"),
    ("backend/app/hoc/cus/integrations/L5_schemas/datasource_model.py",
     "IDENTICAL: Already exists in integrations/engines/"),

    # general - keep main engines/, remove lifecycle subdirectory
    ("backend/app/hoc/cus/general/L5_lifecycle/engines/offboarding.py",
     "IDENTICAL: Already exists in general/engines/"),
    ("backend/app/hoc/cus/general/L5_lifecycle/engines/onboarding.py",
     "IDENTICAL: Already exists in general/engines/"),
]

# Files that are DIFFERENT and need manual review
NEEDS_REVIEW = [
    ("backend/app/hoc/cus/integrations/L5_engines/vault.py",
     "backend/app/hoc/cus/integrations/vault/engines/vault.py",
     "DIFFERENT: vault/engines/ version has additional governance comments"),
    ("backend/app/hoc/cus/account/L6_drivers/tenant_service.py",
     "backend/app/hoc/cus/account/L5_engines/tenant_service.py",
     "DIFFERENT: drivers/ version has timezone import, engines/ doesn't"),
    ("backend/app/hoc/cus/account/L6_drivers/user_write_service.py",
     "backend/app/hoc/cus/account/L5_engines/user_write_service.py",
     "DIFFERENT: drivers/ version is 111 lines, engines/ is 106 lines"),
]


def main():
    print("=" * 60)
    print("HOC MIGRATION - DUPLICATE CLEANUP")
    print("=" * 60)
    print(f"\nMode: {'DRY RUN (no changes)' if DRY_RUN else 'EXECUTE (files will be deleted)'}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Part 1: Remove identical duplicates
    print("\n" + "=" * 60)
    print("REMOVING IDENTICAL DUPLICATES")
    print("=" * 60)

    removed = 0
    failed = 0

    for file_path, reason in DUPLICATES_TO_REMOVE:
        path = Path(file_path)
        if path.exists():
            print(f"\n  {'[DRY-RUN] Would delete' if DRY_RUN else 'Deleting'}: {file_path}")
            print(f"    Reason: {reason}")
            if not DRY_RUN:
                try:
                    path.unlink()
                    removed += 1
                except Exception as e:
                    print(f"    ERROR: {e}")
                    failed += 1
            else:
                removed += 1
        else:
            print(f"\n  [SKIP] Not found: {file_path}")

    print(f"\n  Summary: {removed} files {'would be' if DRY_RUN else ''} removed, {failed} failed")

    # Part 2: Report files needing manual review
    print("\n" + "=" * 60)
    print("FILES NEEDING MANUAL REVIEW")
    print("=" * 60)
    print("\nThese files are DIFFERENT and need human decision:")

    for file1, file2, reason in NEEDS_REVIEW:
        print(f"\n  File 1: {file1}")
        print(f"  File 2: {file2}")
        print(f"  Issue:  {reason}")
        print(f"  Action: Review and decide which to keep")

    # Part 3: Clean up empty directories
    if not DRY_RUN:
        print("\n" + "=" * 60)
        print("CLEANING EMPTY DIRECTORIES")
        print("=" * 60)

        empty_dirs = [
            "backend/app/hoc/cus/general/L5_lifecycle/engines",
            "backend/app/hoc/cus/general/L5_lifecycle",
            "backend/app/hoc/cus/policies/controls/engines",
        ]

        for dir_path in empty_dirs:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                # Check if empty (only __init__.py or nothing)
                files = list(path.glob("*.py"))
                non_init = [f for f in files if f.name != "__init__.py"]
                if not non_init:
                    print(f"  Directory may be empty: {dir_path}")
                    # Don't auto-delete directories - leave for manual cleanup

    # Final summary
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print(f"\n  Identical duplicates removed: {removed}")
    print(f"  Files needing review: {len(NEEDS_REVIEW)}")

    if DRY_RUN:
        print("\n  To execute, run without --dry-run:")
        print("    python scripts/migration/cleanup_duplicates.py")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
