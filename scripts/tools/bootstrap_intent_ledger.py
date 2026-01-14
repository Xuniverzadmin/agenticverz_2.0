#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Bootstrap INTENT_LEDGER.md from existing artifacts, constrained by topology (ONE TIME)
# Reference: PIN-419

"""
Bootstrap Intent Ledger

Extracts truth from existing artifacts and generates INTENT_LEDGER.md.
This script runs ONCE to migrate from YAML-as-source to Ledger-as-source.

IMPORTANT: Only panels that fit the UI_TOPOLOGY_TEMPLATE are included.
Panels outside the topology are dropped (by design).

Inputs:
  - design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml (authoritative structure)
  - design/l2_1/ui_plan.yaml (legacy structural truth - for capability extraction only)
  - backend/AURORA_L2_CAPABILITY_REGISTRY/*.yaml (capability truth)
  - backend/scripts/sdsr/scenarios/*.yaml (verification truth)

Output:
  - design/l2_1/INTENT_LEDGER.md
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

import yaml

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
TOPOLOGY_PATH = REPO_ROOT / "design" / "l2_1" / "UI_TOPOLOGY_TEMPLATE.yaml"
UI_PLAN_PATH = REPO_ROOT / "design" / "l2_1" / "ui_plan.yaml"
CAPABILITY_REGISTRY_PATH = REPO_ROOT / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"
SDSR_SCENARIOS_PATH = REPO_ROOT / "backend" / "scripts" / "sdsr" / "scenarios"
OUTPUT_PATH = REPO_ROOT / "design" / "l2_1" / "INTENT_LEDGER.md"


@dataclass
class TopologySlot:
    """A valid slot in the topology."""

    domain: str
    subdomain: str
    topic: str
    max_slots: int


@dataclass
class LegacyPanel:
    """A panel extracted from legacy ui_plan."""

    panel_id: str
    domain: str
    subdomain: str
    topic: str
    order: str
    panel_class: str
    state: str
    expected_capability: Optional[str]
    note: Optional[str]


def load_yaml(path: Path) -> Optional[Dict]:
    """Load YAML file safely."""
    if not path.exists():
        return None
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_topology() -> Tuple[Dict[Tuple[str, str, str], TopologySlot], Set[str]]:
    """Load UI_TOPOLOGY_TEMPLATE.yaml and build slot lookup.

    Returns:
        - slot_lookup: dict mapping (domain, subdomain, topic) -> TopologySlot
        - valid_domains: set of valid domain IDs
    """
    topology = load_yaml(TOPOLOGY_PATH)
    if not topology:
        print(f"ERROR: Topology template not found at {TOPOLOGY_PATH}")
        sys.exit(1)

    slot_lookup = {}
    valid_domains = set()

    for domain in topology.get("domains", []):
        domain_id = domain.get("id", "")
        valid_domains.add(domain_id)

        for subdomain in domain.get("subdomains", []):
            subdomain_id = subdomain.get("id", "")

            for topic in subdomain.get("topics", []):
                topic_id = topic.get("id", "")
                panel_slots = topic.get("panel_slots", 4)

                key = (domain_id, subdomain_id, topic_id)
                slot_lookup[key] = TopologySlot(
                    domain=domain_id,
                    subdomain=subdomain_id,
                    topic=topic_id,
                    max_slots=panel_slots,
                )

    return slot_lookup, valid_domains


def load_ui_plan() -> Dict:
    """Load and return ui_plan.yaml."""
    ui_plan = load_yaml(UI_PLAN_PATH)
    if not ui_plan:
        print(f"WARNING: ui_plan.yaml not found at {UI_PLAN_PATH}")
        return {"domains": []}
    return ui_plan


def load_capability_registry() -> Dict[str, Dict]:
    """Load all capability registry files into a dict keyed by capability_id."""
    capabilities = {}
    if not CAPABILITY_REGISTRY_PATH.exists():
        print(f"WARNING: Capability registry not found at {CAPABILITY_REGISTRY_PATH}")
        return capabilities

    for yaml_file in CAPABILITY_REGISTRY_PATH.glob("*.yaml"):
        if yaml_file.name == "CAPABILITY_STATUS_MODEL.yaml":
            continue
        cap = load_yaml(yaml_file)
        if cap and "capability_id" in cap:
            capabilities[cap["capability_id"]] = cap

    return capabilities


def extract_legacy_panels(ui_plan: Dict) -> List[LegacyPanel]:
    """Extract all panels from legacy ui_plan."""
    panels = []

    for domain in ui_plan.get("domains", []):
        domain_id = domain.get("id", "UNKNOWN")

        for subdomain in domain.get("subdomains", []):
            subdomain_id = subdomain.get("id", "UNKNOWN")

            for topic in subdomain.get("topics", []):
                topic_id = topic.get("id", "UNKNOWN")

                for panel in topic.get("panels", []):
                    panels.append(
                        LegacyPanel(
                            panel_id=panel.get("panel_id", "UNKNOWN"),
                            domain=domain_id,
                            subdomain=subdomain_id,
                            topic=topic_id,
                            order=panel.get("order", "O1"),
                            panel_class=panel.get("panel_class", "execution"),
                            state=panel.get("state", "EMPTY"),
                            expected_capability=panel.get("expected_capability"),
                            note=panel.get("note"),
                        )
                    )

    return panels


def map_legacy_to_topology(
    legacy_panels: List[LegacyPanel],
    slot_lookup: Dict[Tuple[str, str, str], TopologySlot],
) -> Tuple[List[Tuple[LegacyPanel, int]], List[LegacyPanel]]:
    """Map legacy panels to topology slots.

    Returns:
        - matched: list of (panel, slot_number) tuples
        - dropped: list of panels that don't fit topology
    """
    matched = []
    dropped = []

    # Group by (domain, subdomain, topic)
    groups: Dict[Tuple[str, str, str], List[LegacyPanel]] = {}
    for panel in legacy_panels:
        key = (panel.domain, panel.subdomain, panel.topic)
        if key not in groups:
            groups[key] = []
        groups[key].append(panel)

    for key, panels in groups.items():
        if key not in slot_lookup:
            # This location doesn't exist in topology
            dropped.extend(panels)
            continue

        slot = slot_lookup[key]
        # Sort by order and assign slots
        sorted_panels = sorted(panels, key=lambda p: p.order)

        for i, panel in enumerate(sorted_panels):
            slot_num = i + 1  # 1-indexed
            if slot_num <= slot.max_slots:
                matched.append((panel, slot_num))
            else:
                dropped.append(panel)

    return matched, dropped


def map_capability_to_scenario(capabilities: Dict[str, Dict]) -> Dict[str, str]:
    """Build mapping from capability_id to SDSR scenario_id."""
    cap_to_scenario = {}
    for cap_id, cap in capabilities.items():
        metadata = cap.get("metadata", {})
        observed_by = metadata.get("observed_by")
        if observed_by:
            cap_to_scenario[cap_id] = observed_by
    return cap_to_scenario


def generate_panel_entry(panel: LegacyPanel, slot_num: int) -> str:
    """Generate Markdown entry for a single panel."""
    purpose = panel.note or f"Panel for {panel.topic.replace('_', ' ').lower()}."
    capability = panel.expected_capability if panel.expected_capability else "null"

    return f"""### Panel: {panel.panel_id}

Location:
- Domain: {panel.domain}
- Subdomain: {panel.subdomain}
- Topic: {panel.topic}
- Slot: {slot_num}

Class: {panel.panel_class}
State: {panel.state}

Purpose:
{purpose}

Capability: {capability}
"""


def generate_capability_entry(
    cap_id: str, capability: Dict, panel_id: str, scenario_id: Optional[str]
) -> str:
    """Generate Markdown entry for a capability binding."""
    status = capability.get("status", "DECLARED")
    metadata = capability.get("metadata", {})

    observed_on = metadata.get("observed_on")
    if observed_on and status in ("OBSERVED", "TRUSTED"):
        try:
            if isinstance(observed_on, str):
                observed_date = observed_on.split("T")[0]
            else:
                observed_date = str(observed_on)
        except Exception:
            observed_date = "null"
    else:
        observed_date = "null"

    observed_effects = metadata.get("observed_effects", [])
    side_effects = capability.get("side_effects", [])
    acceptance = observed_effects if observed_effects else side_effects
    if not acceptance:
        acceptance = ["Capability behavior verified"]

    acceptance_lines = "\n".join(f"- {a}" for a in acceptance)
    scenario = scenario_id if scenario_id else "NONE"

    return f"""### Capability: {cap_id}
Panel: {panel_id}
Status: {status}

Verification:
Scenario: {scenario}
Acceptance:
{acceptance_lines}

Observed: {observed_date}
"""


def generate_topology_section(
    slot_lookup: Dict[Tuple[str, str, str], TopologySlot],
) -> str:
    """Generate the Topology overview section."""
    # Group by domain
    domains: Dict[str, Dict[str, List[str]]] = {}
    for (domain, subdomain, topic), slot in slot_lookup.items():
        if domain not in domains:
            domains[domain] = {}
        if subdomain not in domains[domain]:
            domains[domain][subdomain] = []
        domains[domain][subdomain].append(f"{topic} ({slot.max_slots} slots)")

    lines = ["## Topology\n"]
    lines.append("This ledger is constrained by UI_TOPOLOGY_TEMPLATE.yaml.\n")
    lines.append("Only panels within these locations are valid.\n")

    for domain_name in sorted(domains.keys()):
        lines.append(f"### {domain_name}\n")
        for subdomain_name in sorted(domains[domain_name].keys()):
            topics = domains[domain_name][subdomain_name]
            lines.append(f"#### {subdomain_name}")
            for topic in sorted(topics):
                lines.append(f"- {topic}")
            lines.append("")

    return "\n".join(lines)


def generate_ledger(
    matched_panels: List[Tuple[LegacyPanel, int]],
    capabilities: Dict[str, Dict],
    cap_to_scenario: Dict[str, str],
    slot_lookup: Dict[Tuple[str, str, str], TopologySlot],
) -> str:
    """Generate the complete INTENT_LEDGER.md content."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    header = f"""# Intent Ledger — Customer Console

## Metadata
Authority: Human
Generated: {timestamp}
Status: ACTIVE
Topology: design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml
Grammar: design/l2_1/INTENT_LEDGER_GRAMMAR.md

---

"""

    # Topology overview section
    topology_section = generate_topology_section(slot_lookup)

    # Panel entries section
    panel_section = "---\n\n## Panels\n\n"
    # Sort by domain, subdomain, topic, slot
    sorted_panels = sorted(
        matched_panels, key=lambda x: (x[0].domain, x[0].subdomain, x[0].topic, x[1])
    )
    for panel, slot_num in sorted_panels:
        panel_section += generate_panel_entry(panel, slot_num) + "\n"

    # Capability entries section
    capability_section = "---\n\n## Capabilities\n\n"

    # Build panel_id -> (panel, slot) mapping for capability lookup
    panel_map = {panel.panel_id: panel for panel, _ in matched_panels}

    # Capabilities that have panels in topology
    emitted_caps = set()
    for panel, _ in sorted_panels:
        cap_id = panel.expected_capability
        if cap_id and cap_id in capabilities:
            capability = capabilities[cap_id]
            scenario_id = cap_to_scenario.get(cap_id)
            capability_section += (
                generate_capability_entry(
                    cap_id, capability, panel.panel_id, scenario_id
                )
                + "\n"
            )
            emitted_caps.add(cap_id)

    # Capabilities without panels (action capabilities) - only if their source panel is in topology
    for cap_id, capability in capabilities.items():
        if cap_id not in emitted_caps:
            source_panels = capability.get("source_panels", [])
            panel_id = source_panels[0] if source_panels else "UNKNOWN"
            # Only include if source panel is in our matched set
            if panel_id in panel_map:
                scenario_id = cap_to_scenario.get(cap_id)
                capability_section += (
                    generate_capability_entry(cap_id, capability, panel_id, scenario_id)
                    + "\n"
                )
                emitted_caps.add(cap_id)

    return header + topology_section + panel_section + capability_section


def main():
    print("=" * 60)
    print("INTENT LEDGER BOOTSTRAP (TOPOLOGY-CONSTRAINED)")
    print("=" * 60)
    print()

    # Load topology (authoritative)
    print("Loading UI_TOPOLOGY_TEMPLATE.yaml...")
    slot_lookup, valid_domains = load_topology()
    total_slots = sum(slot.max_slots for slot in slot_lookup.values())
    print(f"  Found {len(valid_domains)} domains")
    print(f"  Found {len(slot_lookup)} topic locations")
    print(f"  Total panel slots: {total_slots}")

    # Load legacy ui_plan
    print("\nLoading legacy ui_plan.yaml...")
    ui_plan = load_ui_plan()
    legacy_panels = extract_legacy_panels(ui_plan)
    print(f"  Found {len(legacy_panels)} legacy panels")

    # Load capability registry
    print("\nLoading capability registry...")
    capabilities = load_capability_registry()
    print(f"  Found {len(capabilities)} capabilities")

    # Build capability-to-scenario mapping
    cap_to_scenario = map_capability_to_scenario(capabilities)
    print(f"  {len(cap_to_scenario)} capabilities have SDSR observations")

    # Map legacy panels to topology
    print("\nMapping legacy panels to topology...")
    matched, dropped = map_legacy_to_topology(legacy_panels, slot_lookup)
    print(f"  Matched: {len(matched)} panels")
    print(f"  Dropped: {len(dropped)} panels (outside topology)")

    if dropped:
        print("\n  Dropped panels (by design):")
        for panel in dropped[:10]:  # Show first 10
            print(
                f"    - {panel.panel_id} ({panel.domain}/{panel.subdomain}/{panel.topic})"
            )
        if len(dropped) > 10:
            print(f"    ... and {len(dropped) - 10} more")

    # Count states of matched panels
    state_counts = {}
    for panel, _ in matched:
        state = panel.state
        state_counts[state] = state_counts.get(state, 0) + 1
    print("\n  Panel states (matched only):")
    for state, count in sorted(state_counts.items()):
        print(f"    {state}: {count}")

    # Generate ledger
    print("\nGenerating INTENT_LEDGER.md...")
    content = generate_ledger(matched, capabilities, cap_to_scenario, slot_lookup)

    # Write output
    with open(OUTPUT_PATH, "w") as f:
        f.write(content)

    print(f"\nOutput written to: {OUTPUT_PATH}")
    print()
    print("=" * 60)
    print("BOOTSTRAP COMPLETE")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  - Topology slots available: {total_slots}")
    print(f"  - Panels matched: {len(matched)}")
    print(f"  - Panels dropped: {len(dropped)}")
    print()
    print("Next steps:")
    print("  1. Review: cat design/l2_1/INTENT_LEDGER.md")
    print("  2. Validate: python scripts/tools/coherency_gate.py")
    print("  3. Generate: python scripts/tools/sync_from_intent_ledger.py")
    print()


if __name__ == "__main__":
    main()
