#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Cleanup Migration Copies
# artifact_class: CODE
"""
Cleanup Migration Copies

Removes files that were copied during today's migration (Jan 23 18:08).
Keeps the original files that existed before the migration.

Usage:
    python scripts/migration/cleanup_migration_copies.py --dry-run   # Preview
    python scripts/migration/cleanup_migration_copies.py             # Execute
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Change to repo root
os.chdir(Path(__file__).parent.parent.parent)

DRY_RUN = "--dry-run" in sys.argv

# Files copied during migration (timestamp Jan 23 18:08:XX) - TO BE REMOVED
# Format: path, original_file (the one we're keeping)
MIGRATION_COPIES_TO_REMOVE = [
    # incidents - drivers/ copied today, keep engines/ (Jan 22)
    ("backend/app/hoc/cus/incidents/L6_drivers/incident_read_service.py",
     "Keeping: engines/incident_read_service.py (Jan 22 14:17)"),
    ("backend/app/hoc/cus/incidents/L6_drivers/incident_write_service.py",
     "Keeping: engines/incident_write_service.py (Jan 22 14:17)"),

    # policies - drivers/ copied today, keep engines/ (Jan 22)
    ("backend/app/hoc/cus/policies/L6_drivers/customer_killswitch_read_service.py",
     "Keeping: controls/engines/customer_killswitch_read_service.py (Jan 22 16:25)"),
    ("backend/app/hoc/cus/policies/L6_drivers/customer_policy_read_service.py",
     "Keeping: engines/customer_policy_read_service.py (Jan 22 14:18)"),

    # policies - engines/ copied today, keep facades/ (Jan 22)
    ("backend/app/hoc/cus/policies/L5_engines/governance_facade.py",
     "Keeping: facades/governance_facade.py (Jan 22 11:07)"),
    ("backend/app/hoc/cus/policies/L5_engines/limits_facade.py",
     "Keeping: facades/limits_facade.py (Jan 22 12:00)"),

    # logs - engines/ copied today, keep facades/ (Jan 22)
    ("backend/app/hoc/cus/logs/L5_engines/evidence_facade.py",
     "Keeping: facades/evidence_facade.py (Jan 22 12:00)"),

    # analytics - drivers/ copied today, keep engines/ (Jan 22)
    ("backend/app/hoc/cus/analytics/L6_drivers/cost_write_service.py",
     "Keeping: engines/cost_write_service.py (Jan 22 14:28)"),

    # integrations - engines/ copied today, keep vault/engines/ and schemas/ (Jan 22)
    ("backend/app/hoc/cus/integrations/L5_engines/cus_credential_service.py",
     "Keeping: vault/engines/cus_credential_service.py (Jan 22 15:35)"),
    ("backend/app/hoc/cus/integrations/L5_engines/datasource_model.py",
     "Keeping: schemas/datasource_model.py (Jan 22 12:04)"),
    ("backend/app/hoc/cus/integrations/L5_engines/vault.py",
     "Keeping: vault/engines/vault.py (Jan 22 19:14)"),

    # general - engines/ copied today, keep lifecycle/engines/ (Jan 22)
    ("backend/app/hoc/cus/general/L5_engines/offboarding.py",
     "Keeping: lifecycle/engines/offboarding.py (Jan 22 16:25)"),
    ("backend/app/hoc/cus/general/L5_engines/onboarding.py",
     "Keeping: lifecycle/engines/onboarding.py (Jan 22 16:25)"),

    # account - drivers/ copied today, keep engines/ (Jan 23 09:41 - earlier today)
    ("backend/app/hoc/cus/account/L6_drivers/tenant_service.py",
     "Keeping: engines/tenant_service.py (Jan 23 09:41)"),
    ("backend/app/hoc/cus/account/L6_drivers/user_write_service.py",
     "Keeping: engines/user_write_service.py (Jan 23 09:41)"),
]


def main():
    print("=" * 60)
    print("CLEANUP MIGRATION COPIES")
    print("=" * 60)
    print(f"\nMode: {'DRY RUN (no changes)' if DRY_RUN else 'EXECUTE (files will be deleted)'}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nRemoving files copied during migration (Jan 23 18:08)")

    removed = 0
    not_found = 0
    failed = 0

    for file_path, keep_note in MIGRATION_COPIES_TO_REMOVE:
        path = Path(file_path)

        print(f"\n  File: {file_path}")
        print(f"  {keep_note}")

        if path.exists():
            if DRY_RUN:
                print(f"  [DRY-RUN] Would delete")
                removed += 1
            else:
                try:
                    path.unlink()
                    print(f"  ✅ DELETED")
                    removed += 1
                except Exception as e:
                    print(f"  ❌ ERROR: {e}")
                    failed += 1
        else:
            print(f"  [SKIP] Not found")
            not_found += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\n  Files {'to remove' if DRY_RUN else 'removed'}: {removed}")
    print(f"  Not found (already clean): {not_found}")
    print(f"  Failed: {failed}")

    if DRY_RUN:
        print("\n  To execute, run without --dry-run:")
        print("    python scripts/migration/cleanup_migration_copies.py")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
