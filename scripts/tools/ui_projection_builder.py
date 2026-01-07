#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: developer (pipeline step 4)
#   Execution: sync
# Role: Build final UI projection lock from compiled intent IR (NO OPTIONALS)
# Callers: UI projection pipeline
# Allowed Imports: json
# Forbidden Imports: None
# Reference: L2.1 UI Projection Pipeline

"""
D: UI Projection Builder (LOCK GENERATOR)

RULES (NO OPTIONALS):
- Every domain must have explicit panel list
- Every panel must have explicit control list
- Every control must have explicit type
- Every item must have explicit order
- Every item must have explicit visibility
- No optional fields in output

Output: ui_projection_lock.json
This is the ONLY file the renderer may consume.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Control metadata for explicit projection
CONTROL_METADATA = {
    "FILTER": {"icon": "filter", "category": "data_control"},
    "SORT": {"icon": "sort", "category": "data_control"},
    "SELECT_SINGLE": {"icon": "radio", "category": "selection"},
    "SELECT_MULTI": {"icon": "checkbox", "category": "selection"},
    "NAVIGATE": {"icon": "arrow-right", "category": "navigation"},
    "BULK_SELECT": {"icon": "check-square", "category": "selection"},
    "DETAIL_VIEW": {"icon": "eye", "category": "navigation"},
    "ACTION": {"icon": "play", "category": "action"},
    "DOWNLOAD": {"icon": "download", "category": "action"},
    "EXPAND": {"icon": "chevron-down", "category": "navigation"},
    "REFRESH": {"icon": "refresh-cw", "category": "action"},
    "SEARCH": {"icon": "search", "category": "data_control"},
    "PAGINATION": {"icon": "chevron-left", "category": "navigation"},
    "TOGGLE": {"icon": "toggle-left", "category": "action"},
    "EDIT": {"icon": "edit", "category": "action"},
    "DELETE": {"icon": "trash-2", "category": "action"},
    "CREATE": {"icon": "plus", "category": "action"},
    "APPROVE": {"icon": "check-circle", "category": "action"},
    "REJECT": {"icon": "x-circle", "category": "action"},
    "ARCHIVE": {"icon": "archive", "category": "action"},
    "EXPORT": {"icon": "external-link", "category": "action"},
    "IMPORT": {"icon": "upload", "category": "action"},
    # Incident management controls
    "ACKNOWLEDGE": {"icon": "bell-off", "category": "action"},
    "RESOLVE": {"icon": "check-square", "category": "action"},
}


def build_control(control_type: str, idx: int) -> dict[str, Any]:
    """
    Build explicit control projection.

    D2: Every control must have explicit type.
    """
    meta = CONTROL_METADATA.get(control_type, {"icon": "circle", "category": "unknown"})

    return {
        "type": control_type,
        "order": idx,
        "icon": meta["icon"],
        "category": meta["category"],
        "enabled": True,  # Default enabled in projection
        "visibility": "ALWAYS",
    }


def build_panel(intent: dict[str, Any]) -> dict[str, Any]:
    """
    Build explicit panel projection from intent.

    D2: Every panel must have explicit control list.
    """
    # Build controls with explicit ordering
    controls = []
    for idx, control_type in enumerate(intent.get("controls", [])):
        control = build_control(control_type, idx)
        controls.append(control)

    return {
        "panel_id": intent["panel_id"],
        "panel_name": intent["panel_name"],
        "order": intent.get("order", "999"),
        "render_mode": intent["render_mode"],
        "visibility": intent["visibility"],
        "enabled": intent.get("enabled", False),
        "disabled_reason": intent.get("disabled_reason"),
        "controls": controls,
        "control_count": len(controls),
        # Topic metadata for traceability
        "topic": intent.get("topic"),
        "topic_id": intent.get("topic_id"),
        "subdomain": intent.get("subdomain"),
        # Permissions
        "permissions": {
            "nav_required": intent.get("nav_required", False),
            "filtering": intent.get("filtering", False),
            "read": intent.get("read", False),
            "write": intent.get("write", False),
            "activate": intent.get("activate", False),
        },
    }


def group_by_domain(intents: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Group intents by domain.
    """
    domains: dict[str, list[dict[str, Any]]] = {}

    for intent in intents:
        domain = intent.get("domain", "Unknown")
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(intent)

    return domains


def deduplicate_panels(panels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Deduplicate panels by panel_id, keeping first occurrence.

    Multiple intents can reference the same panel (different topics).
    We keep the first panel definition and merge controls.
    """
    seen: dict[str, dict[str, Any]] = {}

    for panel in panels:
        panel_id = panel["panel_id"]
        if panel_id not in seen:
            seen[panel_id] = panel
        else:
            # Merge controls from duplicate panel entry
            existing_controls = {c["type"] for c in seen[panel_id]["controls"]}
            for control in panel["controls"]:
                if control["type"] not in existing_controls:
                    seen[panel_id]["controls"].append(control)
                    existing_controls.add(control["type"])
            # Update control count
            seen[panel_id]["control_count"] = len(seen[panel_id]["controls"])

    return list(seen.values())


def build_domain_projection(domain: str, intents: list[dict[str, Any]], domain_order: int) -> dict[str, Any]:
    """
    Build explicit domain projection.

    D2: Every domain must have explicit panel list.
    """
    # Build panels from intents
    panels = [build_panel(intent) for intent in intents]

    # Deduplicate panels
    panels = deduplicate_panels(panels)

    # Sort panels by order
    panels = sorted(panels, key=lambda p: str(p.get("order", "999")))

    # Re-index control orders after merging
    for panel in panels:
        for idx, control in enumerate(panel["controls"]):
            control["order"] = idx

    return {
        "domain": domain,
        "order": domain_order,
        "panels": panels,
        "panel_count": len(panels),
        "total_controls": sum(p["control_count"] for p in panels),
    }


def build_projection(compiled_ir: dict[str, Any]) -> dict[str, Any]:
    """
    Build complete UI projection lock from compiled IR.

    D3: Output: Emit ui_projection_lock.json
    """
    intents = compiled_ir.get("intents", [])

    # Group by domain
    grouped = group_by_domain(intents)

    # Define domain order (frozen in v1)
    domain_order = {
        "Overview": 0,
        "Activity": 1,
        "Incidents": 2,
        "Policies": 3,
        "Logs": 4,
    }

    # Build domain projections
    domains = []
    for domain_name, domain_intents in grouped.items():
        order = domain_order.get(domain_name, 99)
        projection = build_domain_projection(domain_name, domain_intents, order)
        domains.append(projection)

    # Sort domains by order
    domains = sorted(domains, key=lambda d: d["order"])

    # Calculate totals
    total_panels = sum(d["panel_count"] for d in domains)
    total_controls = sum(d["total_controls"] for d in domains)

    # Build lock output
    lock = {
        "_meta": {
            "type": "ui_projection_lock",
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": compiled_ir.get("_meta", {}).get("source", "unknown"),
            "processing_stage": "LOCKED",
            "frozen": True,
            "editable": False,
        },
        "_statistics": {
            "domain_count": len(domains),
            "panel_count": total_panels,
            "control_count": total_controls,
        },
        "_contract": {
            "renderer_must_consume_only_this_file": True,
            "no_optional_fields": True,
            "explicit_ordering_everywhere": True,
            "all_controls_have_type": True,
            "all_panels_have_render_mode": True,
            "all_items_have_visibility": True,
        },
        "domains": domains,
    }

    return lock


def validate_projection(lock: dict[str, Any]) -> list[str]:
    """
    Validate projection lock has no optional fields.

    D2: No optional fields allowed.
    """
    errors = []

    for domain in lock.get("domains", []):
        if domain.get("order") is None:
            errors.append(f"Domain '{domain['domain']}': missing order")

        for panel in domain.get("panels", []):
            if panel.get("order") is None:
                errors.append(f"Panel '{panel['panel_id']}': missing order")
            if panel.get("render_mode") is None:
                errors.append(f"Panel '{panel['panel_id']}': missing render_mode")
            if panel.get("visibility") is None:
                errors.append(f"Panel '{panel['panel_id']}': missing visibility")

            for control in panel.get("controls", []):
                if control.get("type") is None:
                    errors.append(f"Control in '{panel['panel_id']}': missing type")
                if control.get("order") is None:
                    errors.append(f"Control '{control.get('type')}': missing order")

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Build UI projection lock from compiled intent IR"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("design/l2_1/ui_contract/ui_intent_ir_compiled.json"),
        help="Path to compiled intent IR JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("design/l2_1/ui_contract/ui_projection_lock.json"),
        help="Output path for UI projection lock JSON"
    )

    args = parser.parse_args()

    # Validate input exists
    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        return 1

    # Read input
    with open(args.input) as f:
        compiled_ir = json.load(f)

    # Build projection
    print(f"Building projection from: {args.input}")
    lock = build_projection(compiled_ir)

    # Validate projection
    errors = validate_projection(lock)
    if errors:
        print(f"\nPROJECTION VALIDATION FAILED")
        print(f"{'=' * 60}")
        for error in errors[:20]:
            print(f"  - {error}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")
        print(f"{'=' * 60}")
        return 2

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(lock, f, indent=2)

    # Report success
    stats = lock["_statistics"]
    print(f"Generated UI projection lock: {args.output}")
    print(f"  Domains: {stats['domain_count']}")
    print(f"  Panels: {stats['panel_count']}")
    print(f"  Controls: {stats['control_count']}")
    print(f"  Stage: {lock['_meta']['processing_stage']}")
    print(f"  Editable: {lock['_meta']['editable']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
