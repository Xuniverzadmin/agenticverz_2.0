#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Mark Copied - Step 2 of Phase 2 Migration
# artifact_class: CODE
"""
Mark Copied - Step 2 of Phase 2 Migration

Updates the migration inventory CSV with copy status after Step 1 file copying.

Adds columns:
- copied: BOOLEAN (TRUE/FALSE/N/A)
- copied_path: STRING (actual path in HOC)
- copied_date: DATE (date of copy operation)
- copy_status: ENUM (SUCCESS, SKIPPED, FAILED, N/A)
- skip_reason: STRING (reason if skipped or failed)

Usage:
    python scripts/migration/mark_copied.py
"""

import csv
import os
import sys
from datetime import date
from pathlib import Path

# Change to repo root
os.chdir(Path(__file__).parent.parent.parent)

INPUT = 'docs/architecture/migration/MIGRATION_INVENTORY_ITER3.csv'
OUTPUT = 'docs/architecture/migration/MIGRATION_INVENTORY_PHASE2.csv'
BACKEND_ROOT = Path('backend')

# Files that were deduplicated during Step 1.5 - actual location vs intended target
# These were removed as migration copies; originals exist at different locations
DEDUPLICATED_FILES = {
    # Target path (from inventory) -> Actual path (where file exists in HOC)
    'app/hoc/cus/analytics/L6_drivers/cost_write_service.py':
        'app/hoc/cus/analytics/L5_engines/cost_write_service.py',
    'app/hoc/cus/integrations/L5_engines/vault.py':
        'app/hoc/cus/integrations/vault/engines/vault.py',
    'app/hoc/cus/integrations/L5_engines/cus_credential_service.py':
        'app/hoc/cus/integrations/vault/engines/cus_credential_service.py',
    'app/hoc/cus/integrations/L5_engines/datasource_model.py':
        'app/hoc/cus/integrations/L5_schemas/datasource_model.py',
    'app/hoc/cus/logs/L5_engines/evidence_facade.py':
        'app/hoc/cus/logs/facades/evidence_facade.py',
    'app/hoc/cus/policies/L5_engines/governance_facade.py':
        'app/hoc/cus/policies/facades/governance_facade.py',
    'app/hoc/cus/incidents/L6_drivers/incident_read_service.py':
        'app/hoc/cus/incidents/L5_engines/incident_read_service.py',
    'app/hoc/cus/incidents/L6_drivers/incident_write_service.py':
        'app/hoc/cus/incidents/L5_engines/incident_write_service.py',
    'app/hoc/cus/policies/L6_drivers/customer_killswitch_read_service.py':
        'app/hoc/cus/policies/controls/engines/customer_killswitch_read_service.py',
    'app/hoc/cus/general/L5_engines/offboarding.py':
        'app/hoc/cus/general/L5_lifecycle/engines/offboarding.py',
    'app/hoc/cus/general/L5_engines/onboarding.py':
        'app/hoc/cus/general/L5_lifecycle/engines/onboarding.py',
    'app/hoc/cus/policies/L5_engines/limits_facade.py':
        'app/hoc/cus/policies/facades/limits_facade.py',
    'app/hoc/cus/policies/L6_drivers/customer_policy_read_service.py':
        'app/hoc/cus/policies/L5_engines/customer_policy_read_service.py',
    'app/hoc/cus/account/L6_drivers/tenant_service.py':
        'app/hoc/cus/account/L5_engines/tenant_service.py',
    'app/hoc/cus/account/L6_drivers/user_write_service.py':
        'app/hoc/cus/account/L5_engines/user_write_service.py',
}


def main():
    print("=" * 60)
    print("STEP 2: MARK CSV ROWS AS COPIED")
    print("=" * 60)
    print(f"\nInput: {INPUT}")
    print(f"Output: {OUTPUT}")
    print(f"Date: {date.today()}")

    # Counters
    stats = {
        'transfer_success': 0,
        'transfer_deduplicated': 0,
        'transfer_failed': 0,
        'skip_hoc_exists': 0,
        'stays': 0,
        'delete': 0,
        'skip_init_collision': 0,
        'other': 0,
        'total': 0
    }

    with open(INPUT, 'r') as f_in, open(OUTPUT, 'w', newline='') as f_out:
        reader = csv.DictReader(f_in)

        # Add new columns
        fieldnames = list(reader.fieldnames) + [
            'copied', 'copied_path', 'copied_date', 'copy_status', 'skip_reason'
        ]

        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            stats['total'] += 1
            action = row['action']
            target = row['target_path']

            if action == 'TRANSFER':
                # Check if file exists at target location
                target_full = BACKEND_ROOT / target

                if target_full.exists():
                    row['copied'] = 'TRUE'
                    row['copied_path'] = target
                    row['copied_date'] = str(date.today())
                    row['copy_status'] = 'SUCCESS'
                    row['skip_reason'] = ''
                    stats['transfer_success'] += 1
                elif target in DEDUPLICATED_FILES:
                    # File was deduplicated during Step 1.5 - original exists at different path
                    actual_path = DEDUPLICATED_FILES[target]
                    actual_full = BACKEND_ROOT / actual_path
                    if actual_full.exists():
                        row['copied'] = 'DEDUPLICATED'
                        row['copied_path'] = actual_path
                        row['copied_date'] = str(date.today())
                        row['copy_status'] = 'DEDUPLICATED'
                        row['skip_reason'] = f'Original exists at {actual_path} (Step 1.5 cleanup)'
                        stats['transfer_deduplicated'] += 1
                    else:
                        row['copied'] = 'FALSE'
                        row['copied_path'] = ''
                        row['copied_date'] = ''
                        row['copy_status'] = 'FAILED'
                        row['skip_reason'] = f'Neither target nor dedup location found'
                        stats['transfer_failed'] += 1
                else:
                    row['copied'] = 'FALSE'
                    row['copied_path'] = ''
                    row['copied_date'] = ''
                    row['copy_status'] = 'FAILED'
                    row['skip_reason'] = 'Target not found after copy'
                    stats['transfer_failed'] += 1

            elif action == 'SKIP_HOC_EXISTS':
                row['copied'] = 'N/A'
                row['copied_path'] = row.get('existing_hoc_path', '')
                row['copied_date'] = ''
                row['copy_status'] = 'SKIPPED'
                row['skip_reason'] = 'HOC file already exists (authoritative)'
                stats['skip_hoc_exists'] += 1

            elif action == 'STAYS':
                row['copied'] = 'N/A'
                row['copied_path'] = ''
                row['copied_date'] = ''
                row['copy_status'] = 'N/A'
                row['skip_reason'] = 'L7 model - stays in app/'
                stats['stays'] += 1

            elif action == 'DELETE':
                row['copied'] = 'N/A'
                row['copied_path'] = ''
                row['copied_date'] = ''
                row['copy_status'] = 'N/A'
                row['skip_reason'] = 'Marked for deletion (deprecated/quarantine)'
                stats['delete'] += 1

            elif action == 'SKIP_INIT_COLLISION':
                row['copied'] = 'N/A'
                row['copied_path'] = ''
                row['copied_date'] = ''
                row['copy_status'] = 'SKIPPED'
                row['skip_reason'] = 'Init file collision resolved'
                stats['skip_init_collision'] += 1

            else:
                row['copied'] = 'N/A'
                row['copied_path'] = ''
                row['copied_date'] = ''
                row['copy_status'] = 'N/A'
                row['skip_reason'] = f'Action is {action}'
                stats['other'] += 1

            writer.writerow(row)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nTotal rows processed: {stats['total']}")
    print(f"\nTRANSFER rows:")
    print(f"  - SUCCESS (file at target): {stats['transfer_success']}")
    print(f"  - DEDUPLICATED (Step 1.5 cleanup): {stats['transfer_deduplicated']}")
    print(f"  - FAILED (target not found): {stats['transfer_failed']}")
    transfer_total = stats['transfer_success'] + stats['transfer_deduplicated']
    print(f"  - Total accounted: {transfer_total}")
    print(f"\nNon-TRANSFER rows:")
    print(f"  - SKIP_HOC_EXISTS: {stats['skip_hoc_exists']}")
    print(f"  - STAYS: {stats['stays']}")
    print(f"  - DELETE: {stats['delete']}")
    print(f"  - SKIP_INIT_COLLISION: {stats['skip_init_collision']}")
    print(f"  - Other: {stats['other']}")

    print(f"\nOutput written to: {OUTPUT}")

    # Verification
    if stats['transfer_failed'] > 0:
        print(f"\n⚠️  WARNING: {stats['transfer_failed']} TRANSFER files not found at target!")
        print("    Review these files before proceeding to Gap Analysis.")
        return 1
    else:
        print(f"\n✅ All TRANSFER files verified:")
        print(f"   - {stats['transfer_success']} at target location")
        print(f"   - {stats['transfer_deduplicated']} deduplicated (original files preserved)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
