#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Type: Governance Script
# Reference: PIN-365 (STEP 2A — UI Slot Population)
#
# STEP 2A Artifact Generator
#
# Purpose: Generate ui_slot_registry.xlsx and surface_to_ui_slot_map.xlsx
#          from existing L2.1 supertable (52 panels → 52 slots, 1:1)
#
# Design Decisions (LOCKED):
#   - 52 slots, 1:1 with existing panels
#   - Many-to-many surface↔slot mapping allowed
#   - Slot owns visibility; surface authority constrains only
#   - Old supertable kept as legacy reference

from pathlib import Path
import sys
from typing import Dict, List, Any

# ----------------------------
# CONFIG
# ----------------------------

REPO_ROOT = Path(__file__).parent.parent.parent

# INPUTS (FROZEN)
SUPERTABLE_CSV = REPO_ROOT / "design/l2_1/supertable/L2_1_UI_INTENT_SUPERTABLE.csv"
REBASED_SURFACES = (
    REPO_ROOT / "docs/capabilities/l21_bounded/l2_supertable_v3_rebased_surfaces.xlsx"
)

# OUTPUTS (NEW)
OUTPUT_DIR = REPO_ROOT / "design/l2_1/step_2a"
OUT_SLOT_REGISTRY = OUTPUT_DIR / "ui_slot_registry.xlsx"
OUT_SURFACE_SLOT_MAP = OUTPUT_DIR / "surface_to_ui_slot_map.xlsx"

# ----------------------------
# SURFACE TYPE MAPPING
# ----------------------------

# Map panel characteristics to compatible surface types
# Based on PIN-363 rebased surfaces:
#   L21-ACT-W  (ACTION, ACT, BOUNDED, WRITE)
#   L21-ACT-R  (ACTION, ACT, BOUNDED, READ)
#   L21-ACT-WS (ACTION, ACT, STRICT, WRITE)
#   L21-ACT-RS (ACTION, ACT, STRICT, READ)
#   L21-SUB-EG (SUBSTRATE, EXPLAIN, BOUNDED, GOVERN)
#   L21-SUB-ER (SUBSTRATE, EXPLAIN, BOUNDED, READ)
#   L21-EVD-R  (EVIDENCE, OBSERVE, BOUNDED, READ)
#   L21-CTL-G  (ACTION, CONTROL, BOUNDED, GOVERN)

SURFACE_DEFINITIONS = {
    "L21-ACT-W": {
        "type": "ACTION",
        "authority": "ACT",
        "determinism": "BOUNDED",
        "mutability": "WRITE",
    },
    "L21-ACT-R": {
        "type": "ACTION",
        "authority": "ACT",
        "determinism": "BOUNDED",
        "mutability": "READ",
    },
    "L21-ACT-WS": {
        "type": "ACTION",
        "authority": "ACT",
        "determinism": "STRICT",
        "mutability": "WRITE",
    },
    "L21-ACT-RS": {
        "type": "ACTION",
        "authority": "ACT",
        "determinism": "STRICT",
        "mutability": "READ",
    },
    "L21-SUB-EG": {
        "type": "SUBSTRATE",
        "authority": "EXPLAIN",
        "determinism": "BOUNDED",
        "mutability": "GOVERN",
    },
    "L21-SUB-ER": {
        "type": "SUBSTRATE",
        "authority": "EXPLAIN",
        "determinism": "BOUNDED",
        "mutability": "READ",
    },
    "L21-EVD-R": {
        "type": "EVIDENCE",
        "authority": "OBSERVE",
        "determinism": "BOUNDED",
        "mutability": "READ",
    },
    "L21-CTL-G": {
        "type": "ACTION",
        "authority": "CONTROL",
        "determinism": "BOUNDED",
        "mutability": "GOVERN",
    },
}


# ----------------------------
# SLOT GENERATION
# ----------------------------


def determine_slot_authority(panel: Dict[str, Any]) -> str:
    """Determine authority level from panel characteristics."""
    # Check action columns
    has_write = panel.get("Write") == "YES"
    has_activate = panel.get("Activate") == "YES"
    confirmation = str(panel.get("Confirmation Required", "")).upper()
    action_layer = str(panel.get("Action Layer", "")).upper()

    if "GC_L" in action_layer or confirmation == "YES":
        return "CONTROL"
    if has_activate or has_write:
        return "ACT"
    if panel.get("Replay") == "YES":
        return "OBSERVE"
    return "OBSERVE"


def determine_slot_mutability(panel: Dict[str, Any]) -> str:
    """Determine mutability from panel characteristics."""
    has_write = panel.get("Write") == "YES"
    has_activate = panel.get("Activate") == "YES"
    activate_action = str(panel.get("Activate Action", "")).upper()

    if "GOVERN" in activate_action or has_activate:
        return "GOVERN"
    if has_write:
        return "WRITE"
    return "READ"


def determine_compatible_surfaces(
    authority: str, mutability: str, order: str, has_replay: bool
) -> List[str]:
    """Determine which surfaces a slot can consume."""
    compatible = []

    # Evidence surfaces for replay/proof panels
    if has_replay or order == "O5":
        compatible.append("L21-EVD-R")

    # Read-only panels
    if mutability == "READ":
        if authority == "OBSERVE":
            compatible.extend(["L21-EVD-R", "L21-SUB-ER"])
        elif authority == "ACT":
            compatible.extend(["L21-ACT-R", "L21-ACT-RS"])

    # Write panels
    if mutability == "WRITE":
        if authority == "ACT":
            compatible.extend(["L21-ACT-W", "L21-ACT-WS"])
        elif authority == "CONTROL":
            compatible.extend(["L21-ACT-W", "L21-CTL-G"])

    # Govern panels
    if mutability == "GOVERN":
        if authority == "CONTROL":
            compatible.extend(["L21-CTL-G", "L21-SUB-EG"])
        elif authority == "ACT":
            compatible.extend(["L21-SUB-EG"])

    # Ensure at least one surface
    if not compatible:
        compatible.append("L21-EVD-R")  # Default to evidence

    return list(set(compatible))


def generate_slot_from_panel(panel: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Generate a UI slot from a panel definition."""
    panel_id = panel.get("Panel ID", f"UNKNOWN-{index}")
    domain = panel.get("Domain", "UNKNOWN")
    order = str(panel.get("Order", "O1"))

    # Generate slot_id from panel_id
    slot_id = f"SLOT-{panel_id}"

    authority = determine_slot_authority(panel)
    mutability = determine_slot_mutability(panel)
    has_replay = panel.get("Replay") == "YES"

    compatible_surfaces = determine_compatible_surfaces(
        authority, mutability, order, has_replay
    )

    return {
        "slot_id": slot_id,
        "panel_id": panel_id,
        "domain": domain,
        "subdomain": panel.get("Subdomain", ""),
        "topic": panel.get("Topic", ""),
        "slot_name": panel.get("Panel Name", ""),
        "order": order,
        "authority": authority,
        "mutability": mutability,
        "compatible_surfaces": ", ".join(compatible_surfaces),
        "primary_surface": compatible_surfaces[0] if compatible_surfaces else "",
        "intent": f"Display {panel.get('Panel Name', 'content')} for {domain}",
        "default_visibility": "VISIBLE" if panel.get("Visible by Default") == "YES" else "COLLAPSIBLE",
        "nav_required": panel.get("Nav Required", "NO"),
        "controls": panel.get("Control Set (Explicit)", "[]"),
        "notes": panel.get("Notes", ""),
        "origin": "STEP_2A_MIGRATION",
    }


def generate_surface_mapping(
    slot: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate surface-to-slot mappings for a slot."""
    mappings = []
    surfaces = slot.get("compatible_surfaces", "").split(", ")
    primary = slot.get("primary_surface", "")

    for surface in surfaces:
        if not surface:
            continue
        mappings.append(
            {
                "surface_id": surface,
                "slot_id": slot["slot_id"],
                "domain": slot["domain"],
                "binding_type": "PRIMARY" if surface == primary else "SECONDARY",
                "authority_compatible": "YES",
                "mutability_compatible": "YES",
                "determinism_compatible": "YES",
                "conditions": "",
            }
        )

    return mappings


# ----------------------------
# MAIN
# ----------------------------


def main():
    print("=" * 70)
    print("STEP 2A: Artifact Generator")
    print("Reference: PIN-365")
    print("=" * 70)

    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas required")
        sys.exit(1)

    # Load supertable
    print("\n[1/4] Loading L2.1 supertable...")
    if not SUPERTABLE_CSV.exists():
        print(f"ERROR: Supertable not found at {SUPERTABLE_CSV}")
        sys.exit(1)

    panels_df = pd.read_csv(SUPERTABLE_CSV)
    panels = panels_df.to_dict(orient="records")
    print(f"  Loaded {len(panels)} panels")

    # Generate slots
    print("\n[2/4] Generating UI slots (1:1 with panels)...")
    slots = []
    for i, panel in enumerate(panels):
        slot = generate_slot_from_panel(panel, i)
        slots.append(slot)

    print(f"  Generated {len(slots)} slots")

    # Group by domain
    domains = {}
    for slot in slots:
        domain = slot["domain"]
        if domain not in domains:
            domains[domain] = 0
        domains[domain] += 1

    for domain, count in sorted(domains.items()):
        print(f"    {domain}: {count} slots")

    # Generate surface mappings
    print("\n[3/4] Generating surface-to-slot mappings...")
    mappings = []
    for slot in slots:
        slot_mappings = generate_surface_mapping(slot)
        mappings.extend(slot_mappings)

    print(f"  Generated {len(mappings)} mappings")

    # Count by surface
    surface_counts = {}
    for m in mappings:
        sid = m["surface_id"]
        if sid not in surface_counts:
            surface_counts[sid] = 0
        surface_counts[sid] += 1

    for sid, count in sorted(surface_counts.items()):
        print(f"    {sid}: {count} bindings")

    # Write outputs
    print("\n[4/4] Writing outputs...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Slot registry
    slots_df = pd.DataFrame(slots)
    slots_df.to_excel(OUT_SLOT_REGISTRY, index=False)
    print(f"  [slot_registry] {OUT_SLOT_REGISTRY}")

    # Surface-to-slot map
    mappings_df = pd.DataFrame(mappings)
    mappings_df.to_excel(OUT_SURFACE_SLOT_MAP, index=False)
    print(f"  [surface_slot_map] {OUT_SURFACE_SLOT_MAP}")

    # Summary
    print("\n" + "=" * 70)
    print("STEP 2A ARTIFACT GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nSlot Registry: {len(slots)} slots")
    print(f"Surface Mappings: {len(mappings)} bindings")
    print(f"\nOutput Directory: {OUTPUT_DIR}")

    print("\nNext steps:")
    print("  1. Review ui_slot_registry.xlsx")
    print("  2. Review surface_to_ui_slot_map.xlsx")
    print("  3. Implement surface_to_slot_resolver.py")
    print("  4. Update run_l2_pipeline.sh")


if __name__ == "__main__":
    main()
