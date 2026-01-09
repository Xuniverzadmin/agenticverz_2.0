#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI (pre-commit, workflow)
#   Execution: sync
# Role: Ensure every STEP 1B surface maps to ≥1 UI slot or is marked non-UI
# Callers: CI pipeline, pre-commit
# Allowed Imports: pandas, sys, pathlib
# Forbidden Imports: None
# Reference: PIN-365 (STEP 2A — UI Slot Population)

"""
Surface → Slot Coverage Guard

PURPOSE:
Prevent "silent invisibility" bugs where a surface exists in STEP 1B
but has no UI representation in STEP 2A.

RULE:
Every surface bound in STEP 1B must either:
  1. Map to ≥1 UI slot in surface_to_ui_slot_map.xlsx, OR
  2. Be explicitly marked as non-UI in the surface registry

ENFORCEMENT:
- CI blocker (exit code 1 on failure)
- Pre-commit hook compatible
"""

import sys
from pathlib import Path

# Repo root
REPO_ROOT = Path(__file__).parent.parent.parent

# Input files
REBASED_SURFACES = (
    REPO_ROOT / "docs/capabilities/l21_bounded/l2_supertable_v3_rebased_surfaces.xlsx"
)
SURFACE_SLOT_MAP = REPO_ROOT / "design/l2_1/step_2a/surface_to_ui_slot_map.xlsx"

# Surfaces explicitly marked as non-UI (internal/system only)
# Add surface IDs here if they should NOT have UI representation
# NOTE: ACTION surfaces currently have no UI slots because the customer console
#       is read-only (observability). When write/action capabilities are added
#       to the UI, these should be mapped to slots and removed from this list.
NON_UI_SURFACES: set[str] = {
    "L21-ACT-W",   # ACTION/WRITE - no write UI yet
    "L21-ACT-R",   # ACTION/READ - no action UI yet
    "L21-ACT-WS",  # ACTION/STRICT/WRITE - no strict write UI yet
    "L21-ACT-RS",  # ACTION/STRICT/READ - no strict action UI yet
}


def load_rebased_surfaces(path: Path) -> set[str]:
    """Load surface IDs from STEP 1B-R rebased surfaces."""
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas required")
        sys.exit(1)

    if not path.exists():
        print(f"ERROR: Rebased surfaces not found: {path}")
        sys.exit(1)

    df = pd.read_excel(path)

    # Extract surface IDs from surface_id column
    surfaces = set()
    for _, row in df.iterrows():
        surface_id = row.get("surface_id", "")
        if pd.notna(surface_id) and str(surface_id).strip():
            surfaces.add(str(surface_id).strip())

    return surfaces


def load_mapped_surfaces(path: Path) -> set[str]:
    """Load surfaces that have slot mappings from STEP 2A."""
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas required")
        sys.exit(1)

    if not path.exists():
        print(f"ERROR: Surface-slot map not found: {path}")
        sys.exit(1)

    df = pd.read_excel(path)

    # Extract unique surface IDs from mappings
    mapped = set()
    for _, row in df.iterrows():
        surface_id = row.get("surface_id", "")
        if pd.notna(surface_id) and str(surface_id).strip():
            mapped.add(str(surface_id).strip())

    return mapped


def main() -> int:
    print("=" * 70)
    print("Surface → Slot Coverage Guard")
    print("Reference: PIN-365 (STEP 2A)")
    print("=" * 70)

    # Load surfaces
    print("\n[1/3] Loading STEP 1B-R rebased surfaces...")
    rebased_surfaces = load_rebased_surfaces(REBASED_SURFACES)
    print(f"  Found {len(rebased_surfaces)} surfaces")

    # Load mappings
    print("\n[2/3] Loading STEP 2A slot mappings...")
    mapped_surfaces = load_mapped_surfaces(SURFACE_SLOT_MAP)
    print(f"  Found {len(mapped_surfaces)} mapped surfaces")

    # Check coverage
    print("\n[3/3] Checking coverage...")

    # Surfaces that should have UI but don't
    unmapped = rebased_surfaces - mapped_surfaces - NON_UI_SURFACES

    # Surfaces marked non-UI
    non_ui_found = rebased_surfaces & NON_UI_SURFACES

    # Report
    print(f"\n  Rebased surfaces: {len(rebased_surfaces)}")
    print(f"  Mapped to slots:  {len(rebased_surfaces & mapped_surfaces)}")
    print(f"  Marked non-UI:    {len(non_ui_found)}")
    print(f"  Unmapped:         {len(unmapped)}")

    if unmapped:
        print("\n" + "=" * 70)
        print("GUARD FAILED: Silent invisibility detected!")
        print("=" * 70)
        print("\nThe following surfaces have NO UI slot mapping:")
        for surface in sorted(unmapped):
            print(f"  - {surface}")
        print("\nResolution options:")
        print("  1. Add slot mapping in design/l2_1/step_2a/surface_to_ui_slot_map.xlsx")
        print("  2. Add to NON_UI_SURFACES in this guard if intentionally non-UI")
        print("\nReference: PIN-365 (STEP 2A — UI Slot Population)")
        return 1

    print("\n" + "=" * 70)
    print("GUARD PASSED: All surfaces have UI coverage or are marked non-UI")
    print("=" * 70)

    # Summary table
    print("\nCoverage Summary:")
    print("| Surface | Status |")
    print("|---------|--------|")
    for surface in sorted(rebased_surfaces):
        if surface in mapped_surfaces:
            status = "MAPPED"
        elif surface in NON_UI_SURFACES:
            status = "NON-UI"
        else:
            status = "UNMAPPED"
        print(f"| {surface} | {status} |")

    return 0


if __name__ == "__main__":
    sys.exit(main())
