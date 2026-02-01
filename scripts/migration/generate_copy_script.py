#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Generate HOC Migration Copy Script
# artifact_class: CODE
"""
Generate HOC Migration Copy Script

Reads MIGRATION_INVENTORY_ITER3.csv and generates shell commands
to copy all TRANSFER files to their HOC target paths.

Usage:
    python scripts/migration/generate_copy_script.py > /tmp/copy_migration.sh
    chmod +x /tmp/copy_migration.sh
    bash /tmp/copy_migration.sh
"""

import csv
import os
from pathlib import Path
from collections import defaultdict

INVENTORY_PATH = "docs/architecture/migration/MIGRATION_INVENTORY_ITER3.csv"
BACKEND_ROOT = "backend"

# Layer priority (copy in this order to respect dependencies)
LAYER_ORDER = ["L7", "L6", "L5", "L4", "L3", "L2", "L2-Infra"]


def main():
    # Read inventory and group by layer
    files_by_layer = defaultdict(list)

    skipped_same_path = 0

    with open(INVENTORY_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["action"] == "TRANSFER":
                source = row["source_path"]
                target = row["target_path"]

                # Skip files already at target (source == target)
                if source == target:
                    skipped_same_path += 1
                    continue

                layer = row["layer"]
                files_by_layer[layer].append({
                    "source": source,
                    "target": target,
                    "domain": row["domain"],
                })

    actual_to_copy = sum(len(v) for v in files_by_layer.values())

    # Generate script header
    print("#!/bin/bash")
    print("# HOC Migration Copy Script")
    print("# Generated for Phase 2 Step 1")
    print(f"# Total TRANSFER in inventory: {actual_to_copy + skipped_same_path}")
    print(f"# Skipped (already at target): {skipped_same_path}")
    print(f"# Files to copy: {actual_to_copy}")
    print("")
    print("set -e  # Exit on error")
    print("")
    print(f"cd {BACKEND_ROOT}")
    print("")

    # Stats
    total_copied = 0

    # Generate copy commands in layer order
    for layer in LAYER_ORDER:
        if layer not in files_by_layer:
            continue

        files = files_by_layer[layer]
        print(f"# === Layer {layer}: {len(files)} files ===")
        print("")

        for entry in files:
            source = entry["source"]
            target = entry["target"]

            # Ensure target directory exists
            target_dir = os.path.dirname(target)
            print(f'mkdir -p "{target_dir}"')
            print(f'cp "{source}" "{target}"')
            print("")
            total_copied += 1

    # Handle any remaining layers not in our order
    for layer, files in files_by_layer.items():
        if layer in LAYER_ORDER:
            continue
        print(f"# === Layer {layer} (additional): {len(files)} files ===")
        print("")
        for entry in files:
            source = entry["source"]
            target = entry["target"]
            target_dir = os.path.dirname(target)
            print(f'mkdir -p "{target_dir}"')
            print(f'cp "{source}" "{target}"')
            print("")
            total_copied += 1

    # Summary
    print("")
    print(f'echo "Migration complete: {total_copied} files copied"')
    print("")


if __name__ == "__main__":
    main()
