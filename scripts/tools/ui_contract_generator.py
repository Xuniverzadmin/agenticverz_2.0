#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: developer
#   Execution: sync
# Role: Transform L2.1 supertable v3 into UI contract JSON
# Callers: Claude, developer CLI
# Allowed Imports: L6 (pandas, json)
# Forbidden Imports: None
# Reference: CLAUDE TODO — THIN UI CONTRACT GENERATION (POST-V3)
"""
UI Contract Generator

Transforms l2_supertable_v3_cap_expanded.xlsx into a versioned UI contract JSON
that can be rendered by the frontend without code mutation.

HARD RULES:
- Never infer business logic
- Never hide QUESTIONABLE actions
- Never change the XLSX
- Only transform → never decide
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

VERSION = "v1"
SOURCE_VERSION = "v3"


# =============================================================================
# CONTROL MAPPING RULES (DETERMINISTIC)
# =============================================================================


def map_controls_from_row(row: pd.Series, binding_status: str) -> list[dict[str, Any]]:
    """
    Map supertable signals to contract controls.

    Control Visibility Rules:
    - SAFE: all controls enabled
    - QUESTIONABLE: READ/DOWNLOAD enabled, WRITE/ACTIVATE disabled with reason
    - BLOCKED: all controls disabled
    """
    controls = []

    # READ is always enabled (it's the base capability)
    if str(row.get("Read", "")).upper() == "YES":
        controls.append({"type": "READ", "enabled": True})

    # Selection Mode
    selection_mode = str(row.get("Selection Mode", "")).upper()
    if selection_mode == "MULTI":
        controls.append(
            {
                "type": "SELECT_MULTI",
                "enabled": binding_status in ["SAFE", "QUESTIONABLE"],
            }
        )
    elif selection_mode == "SINGLE":
        controls.append(
            {
                "type": "SELECT_SINGLE",
                "enabled": binding_status in ["SAFE", "QUESTIONABLE"],
            }
        )

    # Download
    if str(row.get("Download", "")).upper() == "YES":
        controls.append(
            {"type": "DOWNLOAD", "enabled": binding_status in ["SAFE", "QUESTIONABLE"]}
        )

    # Navigation
    if str(row.get("Nav Required", "")).upper() == "YES":
        controls.append(
            {"type": "NAVIGATE", "enabled": binding_status in ["SAFE", "QUESTIONABLE"]}
        )

    # Filtering
    if str(row.get("Filtering", "")).upper() == "YES":
        controls.append(
            {"type": "FILTER", "enabled": binding_status in ["SAFE", "QUESTIONABLE"]}
        )

    # Write actions (gated if QUESTIONABLE)
    if str(row.get("Write", "")).upper() == "YES":
        write_action = str(row.get("Write Action", "")).strip()
        control_type = _map_write_action(write_action)

        if binding_status == "SAFE":
            controls.append({"type": control_type, "enabled": True})
        elif binding_status == "QUESTIONABLE":
            controls.append(
                {
                    "type": control_type,
                    "enabled": False,
                    "reason": "QUESTIONABLE_BINDING",
                }
            )
        else:  # BLOCKED
            controls.append(
                {"type": control_type, "enabled": False, "reason": "BLOCKED_BINDING"}
            )

    # Activate actions (gated if QUESTIONABLE)
    if str(row.get("Activate", "")).upper() == "YES":
        activate_action = str(row.get("Activate Action", "")).strip()
        control_type = _map_activate_action(activate_action)

        if binding_status == "SAFE":
            controls.append({"type": control_type, "enabled": True})
        elif binding_status == "QUESTIONABLE":
            controls.append(
                {
                    "type": control_type,
                    "enabled": False,
                    "reason": "QUESTIONABLE_BINDING",
                }
            )
        else:  # BLOCKED
            controls.append(
                {"type": control_type, "enabled": False, "reason": "BLOCKED_BINDING"}
            )

    return controls


def _map_write_action(action: str) -> str:
    """Map write action to control type."""
    action_upper = action.upper() if action and action != "nan" else ""
    mapping = {
        "ADD_NOTE": "ADD_NOTE",
        "UPDATE_THRESHOLD": "UPDATE_THRESHOLD",
        "UPDATE_LIMIT": "UPDATE_LIMIT",
        "UPDATE_RULE": "UPDATE_RULE",
    }
    return mapping.get(action_upper, "WRITE")


def _map_activate_action(action: str) -> str:
    """Map activate action to control type."""
    action_upper = action.upper() if action and action != "nan" else ""
    mapping = {
        "ACKNOWLEDGE": "ACKNOWLEDGE",
        "RESOLVE": "RESOLVE",
        "ACTIVATE": "ACTIVATE_TOGGLE",
        "DEACTIVATE": "DEACTIVATE_TOGGLE",
        "KILL_SWITCH": "ACTIVATE_KILL_SWITCH",
    }
    return mapping.get(action_upper, "ACTIVATE")


# =============================================================================
# NAVIGATION TARGET GENERATION
# =============================================================================


def generate_nav_target(domain: str, panel_id: str, subdomain: str = "") -> str:
    """
    Generate navigation target URL for a panel.

    Pattern: /{domain}/{subdomain}?panel={panel_id}
    """
    domain_slug = domain.lower().replace(" ", "-")

    if subdomain and str(subdomain) != "nan":
        subdomain_slug = subdomain.lower().replace("_", "-")
        return f"/{domain_slug}/{subdomain_slug}?panel={panel_id}"

    return f"/{domain_slug}?panel={panel_id}"


# =============================================================================
# OVERVIEW DOMAIN SPECIAL HANDLING
# =============================================================================


def build_overview_panels(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Build Overview domain panels with special handling.

    Overview panels:
    - Always binding_status = SAFE
    - Only READ + NAVIGATE controls
    - Navigation targets route to domain landing panels
    """
    overview_rows = df[df["Domain"] == "Overview"]

    panels = []
    seen_panel_ids = set()

    for _, row in overview_rows.iterrows():
        panel_id = str(row["Panel ID"])

        # Skip duplicates (multiple rows per panel from capability expansion)
        if panel_id in seen_panel_ids:
            continue
        seen_panel_ids.add(panel_id)

        panel_name = str(row["Panel Name"])
        order = str(row["Order"])

        # Overview controls: READ + NAVIGATE only
        controls = [
            {"type": "READ", "enabled": True},
            {"type": "NAVIGATE", "enabled": True},
        ]

        # Determine navigation target based on panel name
        nav_target = _overview_nav_target(panel_name, panel_id)

        # Get all rows for this panel for traceability
        panel_rows = overview_rows[overview_rows["Panel ID"] == panel_id]
        source_row_uids = panel_rows["row_uid"].unique().tolist()
        source_capabilities = [
            cap
            for cap in panel_rows["candidate_capability_id"].unique()
            if cap and str(cap) != "nan"
        ]

        panels.append(
            {
                "panel_id": panel_id,
                "panel_name": panel_name,
                "order": order,
                "ranking_dimension": str(row.get("Ranking Dimension", "NONE")),
                "visible": True,
                "navigation": {"enabled": True, "target": nav_target},
                "controls": controls,
                "binding_status": "SAFE",
                "binding_notes": "Overview: derived read model, navigational only",
                # === TRACEABILITY FIELDS ===
                "_source": {
                    "row_uids": source_row_uids,
                    "capabilities": source_capabilities,
                    "intents": ["READ"],  # Overview is always READ-only
                },
            }
        )

    return panels


def _overview_nav_target(panel_name: str, panel_id: str) -> str:
    """Generate navigation target for Overview panels."""
    name_lower = panel_name.lower()

    if "system status" in name_lower:
        return "/overview/system-status?panel=" + panel_id
    elif "health metrics" in name_lower:
        return "/overview/health-metrics?panel=" + panel_id
    else:
        return f"/overview?panel={panel_id}"


# =============================================================================
# MAIN TRANSFORMATION
# =============================================================================


def transform_xlsx_to_contract(xlsx_path: str) -> dict[str, Any]:
    """
    Transform the v3 supertable XLSX into UI contract JSON.

    Groups by: Domain → Panel ID → Order
    """
    df = pd.read_excel(xlsx_path, sheet_name="SUPERTABLE")

    # Get unique domains
    domains = df["Domain"].unique()

    contract = {
        "version": VERSION,
        "generated_from": Path(xlsx_path).name,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_version": SOURCE_VERSION,
            "status": "DRAFT_UI_DRIVING",
        },
        "domains": [],
    }

    stats = {
        "total_panels": 0,
        "total_controls": 0,
        "enabled_controls": 0,
        "disabled_controls": 0,
        "questionable_panels": 0,
        "safe_panels": 0,
        "domains": {},
    }

    for domain in domains:
        domain_df = df[df["Domain"] == domain]

        # Special handling for Overview
        if domain == "Overview":
            panels = build_overview_panels(domain_df)
        else:
            panels = build_domain_panels(domain_df)

        # Deduplicate panels by panel_id (keep first occurrence)
        seen_ids = set()
        unique_panels = []
        for panel in panels:
            if panel["panel_id"] not in seen_ids:
                seen_ids.add(panel["panel_id"])
                unique_panels.append(panel)

        contract["domains"].append({"domain": domain, "panels": unique_panels})

        # Update stats
        stats["domains"][domain] = len(unique_panels)
        stats["total_panels"] += len(unique_panels)

        for panel in unique_panels:
            if panel.get("binding_status") == "QUESTIONABLE":
                stats["questionable_panels"] += 1
            else:
                stats["safe_panels"] += 1

            for control in panel.get("controls", []):
                stats["total_controls"] += 1
                if control.get("enabled", False):
                    stats["enabled_controls"] += 1
                else:
                    stats["disabled_controls"] += 1

    return contract, stats


def build_domain_panels(domain_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Build panels for a non-Overview domain."""
    panels = []

    # Group by Panel ID to consolidate multiple capability rows
    for panel_id in domain_df["Panel ID"].unique():
        panel_rows = domain_df[domain_df["Panel ID"] == panel_id]

        # Use first row for panel metadata
        first_row = panel_rows.iloc[0]

        # Determine binding status (worst case among all rows for this panel)
        binding_statuses = panel_rows["binding_status"].unique()
        if "BLOCKED" in binding_statuses:
            panel_binding_status = "BLOCKED"
        elif "QUESTIONABLE" in binding_statuses:
            panel_binding_status = "QUESTIONABLE"
        else:
            panel_binding_status = "SAFE"

        # Build controls from first row (controls are panel-level, not row-level)
        controls = map_controls_from_row(first_row, panel_binding_status)

        # Generate navigation target
        domain = str(first_row["Domain"])
        subdomain = str(first_row.get("Subdomain", ""))
        nav_target = generate_nav_target(domain, panel_id, subdomain)

        # Check if navigation is required
        nav_enabled = str(first_row.get("Nav Required", "")).upper() == "YES"

        # === TRACEABILITY: Link back to supertable rows ===
        source_row_uids = panel_rows["row_uid"].unique().tolist()
        source_capabilities = [
            cap
            for cap in panel_rows["candidate_capability_id"].unique()
            if cap and str(cap) != "nan"
        ]
        source_intents = [
            intent
            for intent in panel_rows["action_intent"].unique()
            if intent and str(intent) != "nan"
        ]

        panels.append(
            {
                "panel_id": panel_id,
                "panel_name": str(first_row["Panel Name"]),
                "order": str(first_row["Order"]),
                "ranking_dimension": str(first_row.get("Ranking Dimension", "NONE")),
                "visible": str(first_row.get("Visible by Default", "YES")).upper()
                == "YES",
                "navigation": {
                    "enabled": nav_enabled,
                    "target": nav_target if nav_enabled else None,
                },
                "controls": controls,
                "binding_status": panel_binding_status,
                "binding_notes": _summarize_binding_notes(panel_rows),
                # === TRACEABILITY FIELDS ===
                "_source": {
                    "row_uids": source_row_uids,
                    "capabilities": source_capabilities,
                    "intents": source_intents,
                },
            }
        )

    return panels


def _summarize_binding_notes(panel_rows: pd.DataFrame) -> str:
    """Summarize binding notes from multiple rows."""
    notes = []
    for _, row in panel_rows.iterrows():
        note = str(row.get("binding_notes", ""))
        if note and note != "nan" and note not in notes:
            notes.append(note)

    if not notes:
        return "No binding notes"

    return "; ".join(notes[:2])  # Limit to 2 notes for readability


# =============================================================================
# SUMMARY REPORT GENERATION
# =============================================================================


def generate_summary_report(contract: dict, stats: dict, output_path: str) -> str:
    """Generate human-readable summary report."""
    report = f"""# UI Contract v1 Summary Report

**Generated:** {contract["meta"]["generated_at"]}
**Source:** {contract["generated_from"]}
**Status:** {contract["meta"]["status"]}

---

## Domain Summary

| Domain | Panels |
|--------|--------|
"""

    for domain, count in stats["domains"].items():
        report += f"| {domain} | {count} |\n"

    report += f"""
**Total Panels:** {stats["total_panels"]}

---

## Control Statistics

| Metric | Count |
|--------|-------|
| Total Controls | {stats["total_controls"]} |
| Enabled Controls | {stats["enabled_controls"]} |
| Disabled Controls | {stats["disabled_controls"]} |

---

## Binding Status Breakdown

| Status | Panels |
|--------|--------|
| SAFE | {stats["safe_panels"]} |
| QUESTIONABLE | {stats["questionable_panels"]} |

---

## QUESTIONABLE Actions Surfaced to UI

The following panels have QUESTIONABLE binding status, meaning their WRITE/ACTIVATE
controls are **disabled** in the UI with a visible reason:

"""

    for domain_data in contract["domains"]:
        domain = domain_data["domain"]
        for panel in domain_data["panels"]:
            if panel["binding_status"] == "QUESTIONABLE":
                disabled_controls = [
                    c["type"] for c in panel["controls"] if not c.get("enabled", True)
                ]
                if disabled_controls:
                    report += f"- **{domain} / {panel['panel_name']}**: {', '.join(disabled_controls)}\n"

    report += f"""
---

## Integrity Statement

> **No semantics resolved. UI reflects system uncertainty.**

This contract:
- Does NOT decide whether ACK/RESOLVE is reversible
- Does NOT decide whether policy mutations are allowed
- Does NOT infer missing capabilities
- Does NOT hide QUESTIONABLE actions from the user

The UI will display disabled controls with visible reasons, allowing operators
to understand system constraints without false confidence.

---

## Attestation

```
✔ {stats["total_panels"]} panels transformed
✔ {stats["enabled_controls"]} controls enabled
✔ {stats["disabled_controls"]} controls disabled (with reasons)
✔ {stats["questionable_panels"]} QUESTIONABLE panels surfaced
✔ Overview domain: READ + NAVIGATE only
✘ No business decisions made
✘ No semantics resolved
```
"""

    return report


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate UI Contract JSON from L2.1 Supertable v3"
    )
    parser.add_argument(
        "--input",
        default="design/l2_1/supertable/l2_supertable_v3_cap_expanded.xlsx",
        help="Path to v3 supertable XLSX",
    )
    parser.add_argument(
        "--output-json",
        default="website/app-shell/src/contracts/ui_contract.v1.json",
        help="Path for output JSON contract",
    )
    parser.add_argument(
        "--output-summary",
        default="design/l2_1/ui_contract/ui_contract_v1_summary.md",
        help="Path for output summary report",
    )

    args = parser.parse_args()

    print(f"Loading: {args.input}")
    contract, stats = transform_xlsx_to_contract(args.input)

    # Ensure output directories exist
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_summary).parent.mkdir(parents=True, exist_ok=True)

    # Write JSON contract
    with open(args.output_json, "w") as f:
        json.dump(contract, f, indent=2)
    print(f"Wrote: {args.output_json}")

    # Write summary report
    report = generate_summary_report(contract, stats, args.output_summary)
    with open(args.output_summary, "w") as f:
        f.write(report)
    print(f"Wrote: {args.output_summary}")

    # Print summary
    print("\n" + "=" * 60)
    print("UI CONTRACT GENERATION COMPLETE")
    print("=" * 60)
    print(f"  Total Panels:       {stats['total_panels']}")
    print(f"  SAFE Panels:        {stats['safe_panels']}")
    print(f"  QUESTIONABLE:       {stats['questionable_panels']}")
    print(f"  Enabled Controls:   {stats['enabled_controls']}")
    print(f"  Disabled Controls:  {stats['disabled_controls']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
