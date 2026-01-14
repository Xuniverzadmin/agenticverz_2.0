#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | CI
#   Execution: sync
# Role: Generate YAMLs from INTENT_LEDGER.md, validated against topology (repeatable)
# Reference: PIN-419

"""
Sync from Intent Ledger

Parses INTENT_LEDGER.md and generates all YAML artifacts.
This is the AUTHORITATIVE generator - YAMLs are compiled artifacts.

CRITICAL: Before generation, validates all panels against UI_TOPOLOGY_TEMPLATE.yaml.
Panels outside the topology cause generation to FAIL.

Inputs:
  - design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml (authoritative structure)
  - design/l2_1/INTENT_LEDGER.md (human intent)

Outputs:
  - design/l2_1/ui_plan.yaml (structure)
  - backend/AURORA_L2_CAPABILITY_REGISTRY/*.yaml (capabilities)
  - SDSR scenario stubs (if missing)

Rules:
  - Pure compilation - no inference
  - No status promotion (that's observation's job)
  - Deterministic output
  - FAIL if panel location not in topology
  - FAIL if slot number exceeds topology limit
  - FAIL if slot collision detected
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import yaml

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
TOPOLOGY_PATH = REPO_ROOT / "design" / "l2_1" / "UI_TOPOLOGY_TEMPLATE.yaml"
LEDGER_PATH = REPO_ROOT / "design" / "l2_1" / "INTENT_LEDGER.md"
UI_PLAN_PATH = REPO_ROOT / "design" / "l2_1" / "ui_plan.yaml"
CAPABILITY_REGISTRY_PATH = REPO_ROOT / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"
SDSR_SCENARIOS_PATH = REPO_ROOT / "backend" / "scripts" / "sdsr" / "scenarios"


@dataclass
class TopologySlot:
    """A valid slot in the topology."""

    domain: str
    subdomain: str
    topic: str
    max_slots: int


@dataclass
class PanelEntry:
    """Parsed panel from ledger."""

    panel_id: str
    domain: str
    subdomain: str
    topic: str
    slot: int
    panel_class: str
    state: str
    purpose: str
    capability: Optional[str]


@dataclass
class CapabilityEntry:
    """Parsed capability from ledger."""

    capability_id: str
    panel: str
    status: str
    scenario: Optional[str]
    acceptance: List[str]
    observed: Optional[str]


def load_yaml(path: Path) -> Dict:
    """Load YAML file safely."""
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def load_topology() -> Dict[Tuple[str, str, str], TopologySlot]:
    """Load UI_TOPOLOGY_TEMPLATE.yaml and build slot lookup."""
    topology = load_yaml(TOPOLOGY_PATH)
    if not topology:
        print(f"ERROR: Topology template not found at {TOPOLOGY_PATH}")
        sys.exit(1)

    slot_lookup: Dict[Tuple[str, str, str], TopologySlot] = {}

    for domain in topology.get("domains", []):
        domain_id = domain.get("id", "")

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

    return slot_lookup


def parse_ledger(path: Path) -> Tuple[List[PanelEntry], List[CapabilityEntry]]:
    """Parse INTENT_LEDGER.md into structured data."""
    if not path.exists():
        print(f"ERROR: Ledger not found at {path}")
        sys.exit(1)

    with open(path, "r") as f:
        content = f.read()

    panels: List[PanelEntry] = []
    capabilities: List[CapabilityEntry] = []

    # Split into sections
    sections = re.split(r"^## ", content, flags=re.MULTILINE)

    for section in sections:
        if section.startswith("Panels"):
            panels = parse_panels_section(section)
        elif section.startswith("Capabilities"):
            capabilities = parse_capabilities_section(section)

    return panels, capabilities


def parse_panels_section(section: str) -> List[PanelEntry]:
    """Parse the Panels section with Location block."""
    panels = []

    # Split by panel entries
    panel_blocks = re.split(r"^### Panel: ", section, flags=re.MULTILINE)

    for block in panel_blocks[1:]:  # Skip first (section header)
        lines = block.strip().split("\n")
        if not lines:
            continue

        panel_id = lines[0].strip()

        # Parse fields
        fields = {}
        location = {}
        purpose_lines = []
        in_purpose = False
        in_location = False

        for line in lines[1:]:
            line_stripped = line.strip()

            if line_stripped.startswith("Location:"):
                in_location = True
                in_purpose = False
                continue

            if in_location:
                if line_stripped.startswith("- "):
                    # Parse location field: "- Domain: OVERVIEW"
                    loc_match = re.match(r"^- (\w+):\s*(.*)$", line_stripped)
                    if loc_match:
                        key, value = loc_match.groups()
                        location[key.lower()] = value.strip()
                elif ":" in line_stripped and not line_stripped.startswith("-"):
                    # End of location block
                    in_location = False
                    field_match = re.match(r"^(\w+):\s*(.*)$", line_stripped)
                    if field_match:
                        key, value = field_match.groups()
                        if key.lower() == "purpose":
                            in_purpose = True
                            if value.strip():
                                purpose_lines.append(value.strip())
                        else:
                            fields[key.lower()] = value.strip()
                continue

            if line_stripped.startswith("Purpose:"):
                in_purpose = True
                purpose_text = line_stripped[8:].strip()
                if purpose_text:
                    purpose_lines.append(purpose_text)
                continue

            if in_purpose:
                if ":" in line_stripped and not line_stripped.startswith("-"):
                    field_match = re.match(r"^(\w+):\s*(.*)$", line_stripped)
                    if field_match:
                        in_purpose = False
                        key, value = field_match.groups()
                        fields[key.lower()] = value.strip()
                        continue
                purpose_lines.append(line_stripped)
            else:
                # Regular field
                field_match = re.match(r"^(\w+):\s*(.*)$", line_stripped)
                if field_match:
                    key, value = field_match.groups()
                    fields[key.lower()] = value.strip()

        # Handle capability field
        capability = fields.get("capability")
        if capability == "null":
            capability = None

        # Parse slot number
        slot_str = location.get("slot", "1")
        try:
            slot = int(slot_str)
        except ValueError:
            slot = 1

        panels.append(
            PanelEntry(
                panel_id=panel_id,
                domain=location.get("domain", "UNKNOWN"),
                subdomain=location.get("subdomain", "UNKNOWN"),
                topic=location.get("topic", "UNKNOWN"),
                slot=slot,
                panel_class=fields.get("class", "execution"),
                state=fields.get("state", "EMPTY"),
                purpose="\n".join(purpose_lines).strip(),
                capability=capability,
            )
        )

    return panels


def parse_capabilities_section(section: str) -> List[CapabilityEntry]:
    """Parse the Capabilities section."""
    capabilities = []

    # Split by capability entries
    cap_blocks = re.split(r"^### Capability: ", section, flags=re.MULTILINE)

    for block in cap_blocks[1:]:  # Skip first (section header)
        lines = block.strip().split("\n")
        if not lines:
            continue

        cap_id = lines[0].strip()

        # Parse fields
        fields = {}
        acceptance = []
        in_acceptance = False

        for line in lines[1:]:
            line_stripped = line.strip()

            if line_stripped.startswith("Acceptance:"):
                in_acceptance = True
                continue

            if in_acceptance:
                if line_stripped.startswith("-"):
                    acceptance.append(line_stripped[1:].strip())
                elif ":" in line_stripped and not line_stripped.startswith("-"):
                    in_acceptance = False
                    field_match = re.match(r"^(\w+):\s*(.*)$", line_stripped)
                    if field_match:
                        key, value = field_match.groups()
                        fields[key.lower()] = value.strip()
            else:
                # Regular field
                field_match = re.match(r"^(\w+):\s*(.*)$", line_stripped)
                if field_match:
                    key, value = field_match.groups()
                    fields[key.lower()] = value.strip()

        # Handle scenario field
        scenario = fields.get("scenario")
        if scenario == "NONE":
            scenario = None

        # Handle observed field
        observed = fields.get("observed")
        if observed == "null":
            observed = None

        capabilities.append(
            CapabilityEntry(
                capability_id=cap_id,
                panel=fields.get("panel", "UNKNOWN"),
                status=fields.get("status", "DECLARED"),
                scenario=scenario,
                acceptance=acceptance
                if acceptance
                else ["Capability behavior verified"],
                observed=observed,
            )
        )

    return capabilities


def validate_against_topology(
    panels: List[PanelEntry], slot_lookup: Dict[Tuple[str, str, str], TopologySlot]
) -> Tuple[bool, List[str]]:
    """Validate all panels against topology template.

    Returns:
        - valid: True if all panels pass validation
        - errors: list of error messages
    """
    errors = []
    slot_usage: Dict[
        Tuple[str, str, str, int], str
    ] = {}  # (d, sd, t, slot) -> panel_id

    for panel in panels:
        key = (panel.domain, panel.subdomain, panel.topic)

        # Check 1: Location exists in topology
        if key not in slot_lookup:
            errors.append(
                f"Panel '{panel.panel_id}': Location ({panel.domain}/{panel.subdomain}/{panel.topic}) "
                f"not in topology"
            )
            continue

        slot = slot_lookup[key]

        # Check 2: Slot number within limit
        if panel.slot > slot.max_slots:
            errors.append(
                f"Panel '{panel.panel_id}': Slot {panel.slot} exceeds max {slot.max_slots} "
                f"for {panel.domain}/{panel.subdomain}/{panel.topic}"
            )

        # Check 3: No slot collision
        slot_key = (panel.domain, panel.subdomain, panel.topic, panel.slot)
        if slot_key in slot_usage:
            existing = slot_usage[slot_key]
            errors.append(
                f"Panel '{panel.panel_id}': Slot collision with '{existing}' "
                f"at {panel.domain}/{panel.subdomain}/{panel.topic} slot {panel.slot}"
            )
        else:
            slot_usage[slot_key] = panel.panel_id

    return len(errors) == 0, errors


def generate_ui_plan(
    panels: List[PanelEntry], slot_lookup: Dict[Tuple[str, str, str], TopologySlot]
) -> Dict:
    """Generate ui_plan.yaml structure from panels."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Group panels by domain -> subdomain -> topic
    structure: Dict[str, Dict[str, Dict[str, List[PanelEntry]]]] = {}

    for panel in panels:
        if panel.domain not in structure:
            structure[panel.domain] = {}
        if panel.subdomain not in structure[panel.domain]:
            structure[panel.domain][panel.subdomain] = {}
        if panel.topic not in structure[panel.domain][panel.subdomain]:
            structure[panel.domain][panel.subdomain][panel.topic] = []
        structure[panel.domain][panel.subdomain][panel.topic].append(panel)

    # Build ui_plan
    ui_plan = {
        "version": "1.0.0",
        "created_at": timestamp,
        "amended_at": timestamp,
        "status": "LOCKED_UNTIL_TERMINAL_STATE",
        "authority": "design/l2_1/INTENT_LEDGER.md",
        "topology": "design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml",
        "generated_by": "sync_from_intent_ledger.py",
        "mutation_rules": {
            "add_panels": "ALLOWED (within topology)",
            "remove_panels": "FORBIDDEN (use DEFERRED state)",
            "rename_panels": "FORBIDDEN (panel_id is immutable)",
            "reparent_panels": "FORBIDDEN (topology is frozen)",
        },
        "panel_states": {
            "EMPTY": "Slot reserved, panel not implemented",
            "UNBOUND": "Intent exists, capability missing",
            "DRAFT": "Capability declared, SDSR not observed",
            "BOUND": "Capability observed (or trusted)",
            "DEFERRED": "Explicit governance decision",
        },
        "domains": [],
    }

    # Build domains from topology (ensures all domains appear, even if empty)
    domain_order = ["OVERVIEW", "ACTIVITY", "INCIDENTS", "POLICIES", "LOGS"]

    for domain_name in domain_order:
        if domain_name not in structure:
            structure[domain_name] = {}

        domain_entry = {
            "id": domain_name,
            "subdomains": [],
        }

        # Get subdomains from topology
        subdomains_for_domain = {}
        for (d, sd, t), _ in slot_lookup.items():
            if d == domain_name:
                if sd not in subdomains_for_domain:
                    subdomains_for_domain[sd] = set()
                subdomains_for_domain[sd].add(t)

        for subdomain_name in sorted(subdomains_for_domain.keys()):
            subdomain_entry = {
                "id": subdomain_name,
                "topics": [],
            }

            topics = subdomains_for_domain[subdomain_name]
            for topic_name in sorted(topics):
                topic_entry = {
                    "id": topic_name,
                    "panels": [],
                }

                # Get panels for this topic
                topic_panels = (
                    structure.get(domain_name, {})
                    .get(subdomain_name, {})
                    .get(topic_name, [])
                )

                # Sort panels by slot
                sorted_panels = sorted(topic_panels, key=lambda p: p.slot)

                for panel in sorted_panels:
                    intent_spec = f"design/l2_1/intents/{panel.panel_id}.yaml"
                    if panel.state == "EMPTY":
                        intent_spec = None

                    panel_entry = {
                        "panel_id": panel.panel_id,
                        "slot": panel.slot,
                        "panel_class": panel.panel_class,
                        "state": panel.state,
                        "intent_spec": intent_spec,
                        "expected_capability": panel.capability,
                    }
                    topic_entry["panels"].append(panel_entry)

                subdomain_entry["topics"].append(topic_entry)

            domain_entry["subdomains"].append(subdomain_entry)

        ui_plan["domains"].append(domain_entry)

    return ui_plan


def generate_capability_yaml(cap: CapabilityEntry) -> Dict:
    """Generate a single capability registry YAML."""
    yaml_content = {
        "capability_id": cap.capability_id,
        "status": cap.status,
        "source_panels": [cap.panel],
        "metadata": {
            "generated_by": "sync_from_intent_ledger.py",
            "generated_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "declared_by": "intent-ledger",
            "declared_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        },
        "acceptance_criteria": cap.acceptance,
    }

    if cap.scenario:
        yaml_content["metadata"]["observed_by"] = cap.scenario

    if cap.observed:
        yaml_content["metadata"]["observed_on"] = cap.observed

    return yaml_content


def write_ui_plan(ui_plan: Dict, path: Path):
    """Write ui_plan.yaml with header comment."""
    header = """# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: design/l2_1/INTENT_LEDGER.md
# Topology: design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml
# Generator: scripts/tools/sync_from_intent_ledger.py
# To modify: Edit INTENT_LEDGER.md and re-run generator
#
"""
    with open(path, "w") as f:
        f.write(header)
        yaml.dump(
            ui_plan, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )


def write_capability_registry(capabilities: List[CapabilityEntry], path: Path):
    """Write capability registry YAMLs."""
    path.mkdir(parents=True, exist_ok=True)

    for cap in capabilities:
        filename = f"AURORA_L2_CAPABILITY_{cap.capability_id}.yaml"
        filepath = path / filename

        yaml_content = generate_capability_yaml(cap)

        header = """# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: design/l2_1/INTENT_LEDGER.md
# Generator: scripts/tools/sync_from_intent_ledger.py
#
"""
        with open(filepath, "w") as f:
            f.write(header)
            yaml.dump(
                yaml_content,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )


def check_sdsr_scenarios(capabilities: List[CapabilityEntry], path: Path) -> List[str]:
    """Check which SDSR scenarios are missing."""
    missing = []
    for cap in capabilities:
        if cap.scenario:
            scenario_file = path / f"{cap.scenario}.yaml"
            if not scenario_file.exists():
                missing.append(cap.scenario)
    return missing


def main():
    print("=" * 60)
    print("SYNC FROM INTENT LEDGER (TOPOLOGY-VALIDATED)")
    print("=" * 60)
    print()

    # Load topology
    print("Loading UI_TOPOLOGY_TEMPLATE.yaml...")
    slot_lookup = load_topology()
    total_slots = sum(slot.max_slots for slot in slot_lookup.values())
    print(f"  Found {len(slot_lookup)} topic locations")
    print(f"  Total panel slots: {total_slots}")

    # Parse ledger
    print("\nParsing INTENT_LEDGER.md...")
    panels, capabilities = parse_ledger(LEDGER_PATH)
    print(f"  Found {len(panels)} panels")
    print(f"  Found {len(capabilities)} capabilities")

    # Validate against topology
    print("\nValidating against topology...")
    valid, errors = validate_against_topology(panels, slot_lookup)

    if not valid:
        print("\n  VALIDATION FAILED:")
        for error in errors:
            print(f"    ERROR: {error}")
        print()
        print("=" * 60)
        print("SYNC ABORTED - FIX LEDGER ERRORS")
        print("=" * 60)
        sys.exit(1)

    print("  All panels valid")

    # Generate ui_plan
    print("\nGenerating ui_plan.yaml...")
    ui_plan = generate_ui_plan(panels, slot_lookup)
    write_ui_plan(ui_plan, UI_PLAN_PATH)
    print(f"  Written to: {UI_PLAN_PATH}")

    # Generate capability registry
    print("\nGenerating capability registry...")
    write_capability_registry(capabilities, CAPABILITY_REGISTRY_PATH)
    print(f"  Written {len(capabilities)} files to: {CAPABILITY_REGISTRY_PATH}")

    # Check SDSR scenarios
    print("\nChecking SDSR scenarios...")
    missing = check_sdsr_scenarios(capabilities, SDSR_SCENARIOS_PATH)
    if missing:
        print(f"  WARNING: {len(missing)} referenced scenarios missing:")
        for m in missing:
            print(f"    - {m}")
    else:
        print("  All referenced scenarios exist")

    # Summary
    print()
    print("=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print()
    print("Generated artifacts:")
    print(f"  - {UI_PLAN_PATH}")
    print(f"  - {CAPABILITY_REGISTRY_PATH}/*.yaml")
    print()
    print("Next steps:")
    print("  1. Validate: python scripts/tools/coherency_gate.py")
    print("  2. Compile: python backend/aurora_l2/compiler.py")
    print()


if __name__ == "__main__":
    main()
