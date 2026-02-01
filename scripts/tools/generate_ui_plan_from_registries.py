#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: UI Plan Generator — Bootstrap Script
# artifact_class: CODE
"""
UI Plan Generator — Bootstrap Script

Purpose:
    Generate canonical ui_plan.yaml from existing domain and intent registries.
    This is a ONE-TIME bootstrap operation. After generation, ui_plan.yaml
    becomes the source of truth and is hand-edited.

Authority:
    - docs/contracts/UI_AS_CONSTRAINT_V1.md
    - UI plan is the constraint, not a derived artifact

Usage:
    python scripts/tools/generate_ui_plan_from_registries.py

Output:
    design/l2_1/ui_plan.yaml

Layer: L8 (Catalyst / Meta)
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional

import yaml


# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
DESIGN_DIR = REPO_ROOT / "design" / "l2_1"
DOMAIN_REGISTRY = DESIGN_DIR / "AURORA_L2_DOMAIN_INTENT_REGISTRY.yaml"
INTENT_REGISTRY = DESIGN_DIR / "AURORA_L2_INTENT_REGISTRY.yaml"
CAPABILITY_DIR = REPO_ROOT / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"
OUTPUT_FILE = DESIGN_DIR / "ui_plan.yaml"


def load_yaml(path: Path) -> Dict:
    """Load YAML file with error handling."""
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def load_capabilities() -> Dict[str, str]:
    """
    Load capability registry to determine capability status.
    Returns mapping: capability_name -> status (DISCOVERED|DECLARED|OBSERVED|TRUSTED)
    """
    capabilities = {}
    if CAPABILITY_DIR.exists():
        for cap_file in CAPABILITY_DIR.glob("AURORA_L2_CAPABILITY_*.yaml"):
            if cap_file.name == "CAPABILITY_STATUS_MODEL.yaml":
                continue
            try:
                cap_data = load_yaml(cap_file)
                if isinstance(cap_data, dict):
                    name = cap_data.get("capability", cap_file.stem.replace("AURORA_L2_CAPABILITY_", ""))
                    status = cap_data.get("status", "DISCOVERED")
                    capabilities[name] = status
            except Exception as e:
                print(f"WARNING: Could not load {cap_file}: {e}")
    return capabilities


def compute_panel_state(
    panel_id: str,
    has_intent: bool,
    capability_name: Optional[str],
    capabilities: Dict[str, str]
) -> str:
    """
    Compute panel state based on UI-as-Constraint doctrine.

    States:
        EMPTY    - UI planned, intent YAML missing
        UNBOUND  - Intent exists, no capability referenced
        DRAFT    - Capability declared but not observed
        BOUND    - Capability observed or trusted
        DEFERRED - Explicit governance decision (set manually)
    """
    if not has_intent:
        return "EMPTY"

    if not capability_name:
        return "UNBOUND"

    cap_status = capabilities.get(capability_name, "MISSING")

    if cap_status in ("OBSERVED", "TRUSTED"):
        return "BOUND"
    elif cap_status in ("DECLARED", "DISCOVERED"):
        return "DRAFT"
    else:
        return "UNBOUND"


def build_hierarchy(intents: Dict) -> Dict:
    """
    Build hierarchical structure from flat intent registry.
    Returns: {domain: {subdomain: {topic: [panels]}}}
    """
    hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for panel_id, data in intents.items():
        domain = data.get("domain", "Unknown")
        subdomain = data.get("subdomain", "Unknown")
        topic = data.get("topic", "Unknown")
        order = data.get("order", "O1")

        hierarchy[domain][subdomain][topic].append({
            "panel_id": panel_id,
            "order": order,
            "spec_path": data.get("spec_path"),
            "status": data.get("status", "UNREVIEWED")
        })

    # Sort panels by order within each topic
    for domain in hierarchy:
        for subdomain in hierarchy[domain]:
            for topic in hierarchy[domain][subdomain]:
                hierarchy[domain][subdomain][topic].sort(
                    key=lambda p: p["order"]
                )

    return hierarchy


def generate_ui_plan(
    domain_registry: Dict,
    intent_registry: Dict,
    capabilities: Dict[str, str]
) -> Dict:
    """
    Generate the canonical UI plan from registries.
    """
    intents = intent_registry.get("intents", {})
    domains_meta = domain_registry.get("domains", {})

    # Build hierarchy from intents
    hierarchy = build_hierarchy(intents)

    # Domain order (frozen per Customer Console Constitution)
    domain_order = ["Overview", "Activity", "Incidents", "Policies", "Logs"]

    # Build output structure
    ui_plan = {
        "version": "1.0.0",
        "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "LOCKED_UNTIL_TERMINAL_STATE",
        "authority": "docs/contracts/UI_AS_CONSTRAINT_V1.md",
        "mutation_rules": {
            "add_panels": "ALLOWED",
            "remove_panels": "FORBIDDEN (use DEFERRED state)",
            "rename_panels": "FORBIDDEN (panel_id is immutable)",
            "reparent_panels": "REQUIRES_ALL_BOUND_OR_DEFERRED"
        },
        "panel_states": {
            "EMPTY": "UI planned, intent YAML missing",
            "UNBOUND": "Intent exists, capability missing",
            "DRAFT": "Capability declared, SDSR not observed",
            "BOUND": "Capability observed (or trusted)",
            "DEFERRED": "Explicit governance decision"
        },
        "domains": []
    }

    # Process each domain
    for domain_name in domain_order:
        if domain_name not in hierarchy:
            continue

        domain_meta = domains_meta.get(domain_name, {})

        domain_entry = {
            "id": domain_name,
            "question": domain_meta.get("question", f"What is {domain_name}?"),
            "primary_object": domain_meta.get("primary_object", domain_name),
            "secondary_objects": domain_meta.get("secondary_objects", []),
            "subdomains": []
        }

        # Process subdomains
        for subdomain_name in sorted(hierarchy[domain_name].keys()):
            subdomain_entry = {
                "id": subdomain_name,
                "topics": []
            }

            # Process topics
            for topic_name in sorted(hierarchy[domain_name][subdomain_name].keys()):
                panels = hierarchy[domain_name][subdomain_name][topic_name]

                topic_entry = {
                    "id": topic_name,
                    "panels": []
                }

                # Process panels
                for panel_data in panels:
                    panel_id = panel_data["panel_id"]
                    has_intent = panel_data["spec_path"] is not None

                    # Check if this is an interpretation panel
                    interpretation_panels = domain_meta.get("interpretation_panels", [])
                    is_interpretation = panel_id in interpretation_panels

                    # Determine capability (for now, assume naming convention)
                    # In production, this would come from intent YAML
                    capability_name = None
                    if is_interpretation:
                        # Interpretation panels map to SUMMARY capabilities
                        capability_name = f"summary.{domain_name.lower()}"

                    state = compute_panel_state(
                        panel_id,
                        has_intent,
                        capability_name,
                        capabilities
                    )

                    panel_entry = {
                        "panel_id": panel_id,
                        "order": panel_data["order"],
                        "panel_class": "interpretation" if is_interpretation else "execution",
                        "state": state,
                        "intent_spec": panel_data["spec_path"] if has_intent else None,
                        "expected_capability": capability_name
                    }

                    topic_entry["panels"].append(panel_entry)

                subdomain_entry["topics"].append(topic_entry)

            domain_entry["subdomains"].append(subdomain_entry)

        ui_plan["domains"].append(domain_entry)

    # Add summary statistics
    total_panels = 0
    state_counts = defaultdict(int)

    for domain in ui_plan["domains"]:
        for subdomain in domain["subdomains"]:
            for topic in subdomain["topics"]:
                for panel in topic["panels"]:
                    total_panels += 1
                    state_counts[panel["state"]] += 1

    ui_plan["summary"] = {
        "total_panels": total_panels,
        "by_state": dict(state_counts),
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "This file is now the source of truth. Edit manually after bootstrap."
    }

    return ui_plan


def main():
    """Main entry point."""
    print("=" * 60)
    print("UI Plan Generator — Bootstrap Script")
    print("=" * 60)

    # Check if output already exists
    if OUTPUT_FILE.exists():
        print(f"\nWARNING: {OUTPUT_FILE} already exists!")
        print("This is a one-time bootstrap. Overwriting may lose manual edits.")
        response = input("Continue? (yes/no): ").strip().lower()
        if response != "yes":
            print("Aborted.")
            sys.exit(0)

    print(f"\nLoading domain registry: {DOMAIN_REGISTRY}")
    domain_registry = load_yaml(DOMAIN_REGISTRY)

    print(f"Loading intent registry: {INTENT_REGISTRY}")
    intent_registry = load_yaml(INTENT_REGISTRY)

    print(f"Loading capabilities from: {CAPABILITY_DIR}")
    capabilities = load_capabilities()
    print(f"  Found {len(capabilities)} capabilities")

    print("\nGenerating UI plan...")
    ui_plan = generate_ui_plan(domain_registry, intent_registry, capabilities)

    print(f"\nWriting to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w") as f:
        yaml.dump(ui_plan, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Print summary
    print("\n" + "=" * 60)
    print("BOOTSTRAP COMPLETE")
    print("=" * 60)
    print(f"\nTotal panels: {ui_plan['summary']['total_panels']}")
    print("\nBy state:")
    for state, count in ui_plan['summary']['by_state'].items():
        print(f"  {state}: {count}")

    print(f"\nOutput: {OUTPUT_FILE}")
    print("\nNEXT STEPS:")
    print("1. Review generated ui_plan.yaml")
    print("2. This file is now the source of truth")
    print("3. Edit manually to add DEFERRED states or adjust capabilities")
    print("4. Run compiler with UI plan as authority")


if __name__ == "__main__":
    main()
