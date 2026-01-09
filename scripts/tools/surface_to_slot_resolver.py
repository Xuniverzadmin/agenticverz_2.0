#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: developer (pipeline step 2A)
#   Execution: sync
# Role: Resolve mechanical surfaces to UI slots (STEP 2A)
# Callers: UI projection pipeline
# Allowed Imports: pandas, json
# Forbidden Imports: None
# Reference: PIN-365 (STEP 2A — UI Slot Population)

"""
Stage 2A: Surface → UI Slot Resolver

PURPOSE:
Translate mechanical surfaces into UI slots that the existing compiler understands.
This is the ONLY new stage in the pipeline.

INPUTS:
- ui_intent_ir_normalized.json (Stage 2 output)
- ui_slot_registry.xlsx (STEP 2A artifact)
- surface_to_ui_slot_map.xlsx (STEP 2A artifact)

OUTPUTS:
- ui_intent_ir_slotted.json (feeds into Stage 3)

DESIGN DECISIONS (LOCKED per PIN-365):
- 52 slots, 1:1 with existing panels
- Many-to-many surface↔slot mapping allowed
- Slot owns visibility; surface authority constrains only
- Old supertable kept as legacy reference

RULES:
- Map surface(s) → slot(s)
- Apply product visibility rules
- Enforce authority compatibility
- NO capability logic
- NO UI rendering logic
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


# ----------------------------
# CONFIG
# ----------------------------

REPO_ROOT = Path(__file__).parent.parent.parent

# Inputs
DEFAULT_NORMALIZED_IR = REPO_ROOT / "design/l2_1/ui_contract/ui_intent_ir_normalized.json"
DEFAULT_SLOT_REGISTRY = REPO_ROOT / "design/l2_1/step_2a/ui_slot_registry.xlsx"
DEFAULT_SURFACE_MAP = REPO_ROOT / "design/l2_1/step_2a/surface_to_ui_slot_map.xlsx"

# Output
DEFAULT_OUTPUT = REPO_ROOT / "design/l2_1/ui_contract/ui_intent_ir_slotted.json"


# ----------------------------
# LOADERS
# ----------------------------


def load_slot_registry(path: Path) -> dict[str, dict[str, Any]]:
    """Load slot registry and index by panel_id for O(1) lookup."""
    df = pd.read_excel(path)
    registry: dict[str, dict[str, Any]] = {}

    for _, row in df.iterrows():
        raw_panel_id = row.get("panel_id", "")
        if pd.notna(raw_panel_id) and str(raw_panel_id).strip():
            panel_id = str(raw_panel_id)
            registry[panel_id] = {
                "slot_id": row.get("slot_id", ""),
                "domain": row.get("domain", ""),
                "subdomain": row.get("subdomain", ""),
                "topic": row.get("topic", ""),
                "slot_name": row.get("slot_name", ""),
                "order": row.get("order", ""),
                "authority": row.get("authority", ""),
                "mutability": row.get("mutability", ""),
                "compatible_surfaces": row.get("compatible_surfaces", ""),
                "primary_surface": row.get("primary_surface", ""),
                "intent": row.get("intent", ""),
                "default_visibility": row.get("default_visibility", "VISIBLE"),
                "nav_required": row.get("nav_required", "NO"),
                "controls": row.get("controls", "[]"),
                "origin": row.get("origin", ""),
            }

    return registry


def load_surface_mappings(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load surface-to-slot mappings and index by slot_id."""
    df = pd.read_excel(path)
    mappings: dict[str, list[dict[str, Any]]] = {}

    for _, row in df.iterrows():
        raw_slot_id = row.get("slot_id", "")
        if pd.notna(raw_slot_id) and str(raw_slot_id).strip():
            slot_id = str(raw_slot_id)
            if slot_id not in mappings:
                mappings[slot_id] = []
            mappings[slot_id].append({
                "surface_id": row.get("surface_id", ""),
                "binding_type": row.get("binding_type", "SECONDARY"),
                "authority_compatible": row.get("authority_compatible", "YES"),
                "mutability_compatible": row.get("mutability_compatible", "YES"),
                "determinism_compatible": row.get("determinism_compatible", "YES"),
                "conditions": row.get("conditions", ""),
            })

    return mappings


# ----------------------------
# RESOLVER
# ----------------------------


def resolve_intent_to_slot(
    intent: dict[str, Any],
    slot_registry: dict[str, dict[str, Any]],
    surface_mappings: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any], list[str]]:
    """
    Resolve a single intent (panel) to its slot representation.

    Returns: (resolved_intent, warnings)

    The resolved intent maintains the same shape for downstream compatibility.
    """
    warnings = []
    resolved = intent.copy()

    panel_id = intent.get("panel_id", "")

    # Look up slot by panel_id (1:1 mapping in STEP 2A)
    slot = slot_registry.get(panel_id)

    if not slot:
        warnings.append(f"Panel '{panel_id}' has no slot mapping - using passthrough")
        # Passthrough mode: intent unchanged except for slot metadata
        resolved["_slot"] = {
            "status": "UNMAPPED",
            "reason": "No slot found in registry",
        }
        return resolved, warnings

    # Enrich with slot metadata
    slot_id = slot["slot_id"]
    surface_bindings = surface_mappings.get(slot_id, [])

    # Get primary surface
    primary_surface = slot.get("primary_surface", "")
    primary_binding = None
    for binding in surface_bindings:
        if binding["binding_type"] == "PRIMARY":
            primary_binding = binding
            break

    # Apply slot visibility (slot owns visibility per PIN-365)
    slot_visibility = slot.get("default_visibility", "VISIBLE")
    if slot_visibility == "VISIBLE":
        resolved["visible_by_default"] = "YES"
    elif slot_visibility == "HIDDEN":
        resolved["visible_by_default"] = "NO"
    else:
        # COLLAPSIBLE or other
        resolved["visible_by_default"] = "YES"

    # Add slot annotation (metadata for traceability)
    resolved["_slot"] = {
        "status": "RESOLVED",
        "slot_id": slot_id,
        "primary_surface": primary_surface,
        "surface_count": len(surface_bindings),
        "authority": slot.get("authority", ""),
        "mutability": slot.get("mutability", ""),
        "origin": slot.get("origin", ""),
    }

    # Validate authority compatibility
    if primary_binding:
        if primary_binding.get("authority_compatible") != "YES":
            warnings.append(
                f"Slot '{slot_id}' has authority incompatibility with primary surface"
            )
        if primary_binding.get("mutability_compatible") != "YES":
            warnings.append(
                f"Slot '{slot_id}' has mutability incompatibility with primary surface"
            )
        if primary_binding.get("determinism_compatible") != "YES":
            warnings.append(
                f"Slot '{slot_id}' has determinism incompatibility with primary surface"
            )

    return resolved, warnings


def resolve_intents(
    normalized_ir: dict[str, Any],
    slot_registry: dict[str, dict[str, Any]],
    surface_mappings: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """
    Resolve all normalized intents through the slot system.

    Output maintains the same shape for downstream compatibility.
    """
    intents = normalized_ir.get("intents", [])
    resolved_intents = []
    all_warnings: list[str] = []

    # Statistics
    stats = {
        "total_intents": len(intents),
        "resolved": 0,
        "unmapped": 0,
        "warnings": 0,
    }

    for intent in intents:
        resolved, warnings = resolve_intent_to_slot(
            intent, slot_registry, surface_mappings
        )
        resolved_intents.append(resolved)

        if resolved.get("_slot", {}).get("status") == "RESOLVED":
            stats["resolved"] += 1
        else:
            stats["unmapped"] += 1

        if warnings:
            stats["warnings"] += len(warnings)
            all_warnings.extend(warnings)

    # Build output structure (same shape as normalized IR)
    output = {
        "_meta": {
            "type": "ui_intent_ir_slotted",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": normalized_ir.get("_meta", {}).get("source", "unknown"),
            "row_count": len(resolved_intents),
            "processing_stage": "SLOTTED",
            "step": "2A",
            "reference": "PIN-365",
        },
        "_slot_resolution": {
            "slot_registry_count": len(slot_registry),
            "surface_mapping_count": sum(len(v) for v in surface_mappings.values()),
            "statistics": stats,
            "warnings": all_warnings[:20],  # First 20 warnings
            "warning_count": len(all_warnings),
        },
        "intents": resolved_intents,
    }

    return output


# ----------------------------
# MAIN
# ----------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Resolve surfaces to UI slots (STEP 2A)"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_NORMALIZED_IR,
        help="Path to normalized intent IR JSON",
    )
    parser.add_argument(
        "--slot-registry",
        type=Path,
        default=DEFAULT_SLOT_REGISTRY,
        help="Path to UI slot registry Excel",
    )
    parser.add_argument(
        "--surface-map",
        type=Path,
        default=DEFAULT_SURFACE_MAP,
        help="Path to surface-to-slot mapping Excel",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output path for slotted intent IR JSON",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("STEP 2A: Surface → UI Slot Resolver")
    print("Reference: PIN-365")
    print("=" * 70)

    # Validate inputs
    missing = []
    if not args.input.exists():
        missing.append(f"Normalized IR: {args.input}")
    if not args.slot_registry.exists():
        missing.append(f"Slot registry: {args.slot_registry}")
    if not args.surface_map.exists():
        missing.append(f"Surface map: {args.surface_map}")

    if missing:
        print("\nERROR: Missing input files:")
        for m in missing:
            print(f"  - {m}")
        return 1

    # Load inputs
    print("\n[1/4] Loading normalized IR...")
    with open(args.input) as f:
        normalized_ir = json.load(f)
    print(f"  Loaded {len(normalized_ir.get('intents', []))} intents")

    print("\n[2/4] Loading slot registry...")
    slot_registry = load_slot_registry(args.slot_registry)
    print(f"  Loaded {len(slot_registry)} slots")

    print("\n[3/4] Loading surface mappings...")
    surface_mappings = load_surface_mappings(args.surface_map)
    total_mappings = sum(len(v) for v in surface_mappings.values())
    print(f"  Loaded {total_mappings} mappings for {len(surface_mappings)} slots")

    # Resolve
    print("\n[4/4] Resolving intents to slots...")
    result = resolve_intents(normalized_ir, slot_registry, surface_mappings)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    # Report
    stats = result["_slot_resolution"]["statistics"]
    print(f"\nGenerated slotted intent IR: {args.output}")
    print(f"  Total intents: {stats['total_intents']}")
    print(f"  Resolved: {stats['resolved']}")
    print(f"  Unmapped: {stats['unmapped']}")
    print(f"  Warnings: {stats['warnings']}")

    if stats["warnings"] > 0:
        print("\nWarnings (first 5):")
        for w in result["_slot_resolution"]["warnings"][:5]:
            print(f"  - {w}")

    print("\n" + "=" * 70)
    print("STEP 2A COMPLETE")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
