#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Check Phase 2 Stop Condition
# artifact_class: CODE
"""
Check Phase 2 Stop Condition

Measures: Engines with DB signals (L6_DRIVER only) ≤ 5%

Usage:
  python scripts/migration/check_stop_condition.py

Note:
  - L6_DRIVER: Actual DB access (sqlalchemy, sqlmodel, session.*, select/insert/update/delete)
  - L6_SCHEMA: DTOs/schemas (BaseModel, dataclass) - NOT counted as DB signals

  Engines may have L6_SCHEMA signals (DTOs) and still be considered pure.
"""
import json
from pathlib import Path


def main():
    # Read from signals_raw.json to get detailed signal types
    signals_path = Path("docs/architecture/migration/signals_raw.json")
    with open(signals_path) as f:
        signals_data = json.load(f)

    # Count engines and engines with DB signals (L6_DRIVER only)
    total_engines = 0
    impure_engines = 0
    impure_list = []

    for f in signals_data["files"]:
        rel_path = f["relative_path"]

        # Only count files in engines/ folder
        if "/engines/" not in rel_path:
            continue

        total_engines += 1

        # Count only L6_DRIVER signals (actual DB access)
        # L6_SCHEMA (DTOs) are allowed in engines
        l6_driver_count = sum(
            1 for s in f.get("signals", [])
            if s.get("layer") == "L6_DRIVER"
        )

        if l6_driver_count > 0:
            impure_engines += 1
            impure_list.append({
                "file": rel_path,
                "l6_driver_signals": l6_driver_count,
            })

    # Calculate percentage
    pct = (impure_engines / total_engines * 100) if total_engines > 0 else 0
    target_pct = 5.0
    target_met = pct <= target_pct

    print("=" * 60)
    print("PHASE 2 STOP CONDITION CHECK")
    print("=" * 60)
    print()
    print(f"Metric: Engines with DB signals")
    print(f"Target: ≤ {target_pct}%")
    print()
    print(f"Current:")
    print(f"  Total engines:  {total_engines}")
    print(f"  Impure engines: {impure_engines}")
    print(f"  Percentage:     {pct:.1f}%")
    print()

    if target_met:
        print("✅ STOP CONDITION MET - Phase 2 complete!")
    else:
        print(f"❌ STOP CONDITION NOT MET")
        print(f"   Need to reduce to: ≤{int(total_engines * target_pct / 100)} impure engines")
        print(f"   Remaining work:    {impure_engines - int(total_engines * target_pct / 100)} more extractions")

    # Show top impure engines
    print()
    print("Top impure engines by DB signals (L6_DRIVER):")
    for eng in sorted(impure_list, key=lambda x: -x["l6_driver_signals"])[:10]:
        filename = Path(eng["file"]).name
        print(f"  - {filename}: {eng['l6_driver_signals']} L6_DRIVER signals")

    return 0 if target_met else 1


if __name__ == "__main__":
    exit(main())
