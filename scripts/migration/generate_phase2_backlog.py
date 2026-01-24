#!/usr/bin/env python3
"""
Generate Phase 2 Backlog YAML

Creates a structured backlog organized by extraction pattern.

Usage:
  python scripts/migration/generate_phase2_backlog.py
"""
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def main():
    # Load report
    report_path = Path("docs/architecture/migration/layer_fit_report.json")
    with open(report_path) as f:
        report = json.load(f)

    # Get EXTRACT_DRIVER files
    extract_files = [
        f for f in report["files"]
        if f.get("refactor_action") == "EXTRACT_DRIVER"
    ]

    # Organize by batch pattern
    batches = {
        "batch_1_read_service": [],
        "batch_2_write_service": [],
        "batch_3_service_mixed": [],
        "batch_4_facade": [],
        "batch_5_other": [],
    }

    for f in extract_files:
        filename = Path(f["relative_path"]).name
        rel_path = f["relative_path"]

        entry = {
            "file": rel_path,
            "filename": filename,
            "declared": f["classification"].get("declared_layer"),
            "detected": f["classification"].get("dominant_layer"),
            "status": "pending",
        }

        if filename.endswith("_read_service.py"):
            batches["batch_1_read_service"].append(entry)
        elif filename.endswith("_write_service.py"):
            batches["batch_2_write_service"].append(entry)
        elif filename.endswith("_service.py"):
            batches["batch_3_service_mixed"].append(entry)
        elif filename.endswith("_facade.py"):
            batches["batch_4_facade"].append(entry)
        else:
            batches["batch_5_other"].append(entry)

    # Generate YAML
    output = f"""# Phase 2 Extraction Backlog
#
# Generated: {datetime.now().strftime('%Y-%m-%d')}
# Total files: {len(extract_files)}
#
# Batch execution order (MANDATORY):
#   1. *_read_service.py - DB-heavy, lowest coupling
#   2. *_write_service.py - Side-effectful but mechanical
#   3. *_service.py - Mixed, requires judgment
#   4. *_facade.py - L4/L3 confusion cases
#   5. Other patterns - Last
#
# Status values:
#   - pending: Not yet processed
#   - in_progress: Currently being extracted
#   - extracted: Driver created, engine updated
#   - verified: Classifier confirms 0 DB signals
#   - blocked: Requires manual review

version: "1.0"
generated: "{datetime.now().strftime('%Y-%m-%d')}"
total_files: {len(extract_files)}

stop_condition:
  metric: "engines_with_db_signals"
  target: "<=5%"
  current: "55%"  # After Phase 1

"""

    for batch_name, files in batches.items():
        batch_num = batch_name.split("_")[1]
        pattern = batch_name.split("_", 2)[2].replace("_", " ")

        output += f"""
# =============================================================================
# BATCH {batch_num}: {pattern.upper()} ({len(files)} files)
# =============================================================================

{batch_name}:
  count: {len(files)}
  completed: 0
  status: pending
  files:
"""
        for f in sorted(files, key=lambda x: x["file"]):
            output += f"""    - file: "{f['file']}"
      declared: {f['declared']}
      detected: {f['detected']}
      status: pending
      driver_file: null
      extracted_date: null
"""

    # Write output
    output_path = Path("docs/architecture/migration/phase2_backlog.yaml")
    output_path.write_text(output)
    print(f"Generated: {output_path}")
    print(f"Total files: {len(extract_files)}")

    for batch_name, files in batches.items():
        print(f"  {batch_name}: {len(files)}")


if __name__ == "__main__":
    main()
