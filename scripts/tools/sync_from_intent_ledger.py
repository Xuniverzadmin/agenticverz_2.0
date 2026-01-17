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
  - design/l2_1/intents/*.yaml (intent specifications) [NEW]
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
INTENTS_DIR = REPO_ROOT / "design" / "l2_1" / "intents"
CAPABILITY_REGISTRY_PATH = REPO_ROOT / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"
SDSR_SCENARIOS_PATH = REPO_ROOT / "backend" / "scripts" / "sdsr" / "scenarios"
SEMANTIC_REGISTRY_PATH = REPO_ROOT / "design" / "l2_1" / "AURORA_L2_SEMANTIC_REGISTRY.yaml"


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
    # Implementation block (human assumption)
    assumed_endpoint: Optional[str] = None
    assumed_method: str = "GET"


@dataclass
class FacetEntry:
    """Parsed facet from ledger (V1.1 - semantic grouping)."""

    facet_id: str
    purpose: str
    criticality: str  # HIGH, MEDIUM, LOW
    domain: str
    panels: List[str]  # List of panel_ids


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


def parse_ledger(path: Path) -> Tuple[List[PanelEntry], List[CapabilityEntry], List[FacetEntry]]:
    """Parse INTENT_LEDGER.md into structured data."""
    if not path.exists():
        print(f"ERROR: Ledger not found at {path}")
        sys.exit(1)

    with open(path, "r") as f:
        content = f.read()

    panels: List[PanelEntry] = []
    capabilities: List[CapabilityEntry] = []
    facets: List[FacetEntry] = []

    # Split into sections
    sections = re.split(r"^## ", content, flags=re.MULTILINE)

    for section in sections:
        if section.startswith("Panels"):
            panels = parse_panels_section(section)
        elif section.startswith("Capabilities"):
            capabilities = parse_capabilities_section(section)
        elif section.startswith("Facets"):
            facets = parse_facets_section(section)

    return panels, capabilities, facets


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
    """Parse the Capabilities section including Implementation block."""
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
        implementation = {}
        in_acceptance = False
        in_implementation = False

        for line in lines[1:]:
            line_stripped = line.strip()

            if line_stripped.startswith("Acceptance:"):
                in_acceptance = True
                in_implementation = False
                continue

            if line_stripped.startswith("Implementation:"):
                in_implementation = True
                in_acceptance = False
                continue

            if in_implementation:
                if line_stripped.startswith("- "):
                    # Parse implementation field: "- Endpoint: /api/v1/..."
                    impl_match = re.match(r"^- (\w+):\s*(.*)$", line_stripped)
                    if impl_match:
                        key, value = impl_match.groups()
                        implementation[key.lower()] = value.strip()
                elif ":" in line_stripped and not line_stripped.startswith("-"):
                    # End of implementation block
                    in_implementation = False
                    field_match = re.match(r"^(\w+):\s*(.*)$", line_stripped)
                    if field_match:
                        key, value = field_match.groups()
                        fields[key.lower()] = value.strip()
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

        # Extract implementation block values (human assumptions)
        assumed_endpoint = implementation.get("endpoint")
        assumed_method = implementation.get("method", "GET")

        capabilities.append(
            CapabilityEntry(
                capability_id=cap_id,
                panel=fields.get("panel", "UNKNOWN"),
                status=fields.get("status", "ASSUMED"),
                scenario=scenario,
                acceptance=acceptance
                if acceptance
                else ["Capability behavior verified"],
                observed=observed,
                assumed_endpoint=assumed_endpoint,
                assumed_method=assumed_method,
            )
        )

    return capabilities


def parse_facets_section(section: str) -> List[FacetEntry]:
    """Parse the Facets section (V1.1 grammar).

    Facets are semantic groupings of information needs that span multiple panels.
    They provide human-readable context without affecting pipeline mechanics.
    """
    facets = []

    # Split by facet entries
    facet_blocks = re.split(r"^### Facet: ", section, flags=re.MULTILINE)

    for block in facet_blocks[1:]:  # Skip first (section header)
        lines = block.strip().split("\n")
        if not lines:
            continue

        facet_id = lines[0].strip()

        # Parse fields
        fields = {}
        panels = []
        in_panels = False

        for line in lines[1:]:
            line_stripped = line.strip()

            if line_stripped.startswith("Panels:"):
                in_panels = True
                continue

            if in_panels:
                if line_stripped.startswith("- "):
                    # Parse panel entry: "- OVR-SUM-HL-O1 (headline metrics)"
                    panel_match = re.match(r"^- ([A-Z0-9\-]+)", line_stripped)
                    if panel_match:
                        panels.append(panel_match.group(1))
                elif ":" in line_stripped and not line_stripped.startswith("-"):
                    # End of panels block - new field
                    in_panels = False
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

        facets.append(
            FacetEntry(
                facet_id=facet_id,
                purpose=fields.get("purpose", ""),
                criticality=fields.get("criticality", "MEDIUM"),
                domain=fields.get("domain", "UNKNOWN"),
                panels=panels,
            )
        )

    return facets


def build_panel_facet_mapping(facets: List[FacetEntry]) -> Dict[str, Tuple[str, str]]:
    """Build a mapping from panel_id to (facet_id, criticality).

    If a panel appears in multiple facets, uses the first occurrence.
    This is intentional - panels should belong to one primary facet.
    """
    mapping: Dict[str, Tuple[str, str]] = {}

    for facet in facets:
        for panel_id in facet.panels:
            if panel_id not in mapping:
                mapping[panel_id] = (facet.facet_id, facet.criticality)

    return mapping


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
                    intent_spec = f"design/l2_1/intents/AURORA_L2_INTENT_{panel.panel_id}.yaml"
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


def load_existing_capability(capability_id: str) -> Optional[Dict]:
    """Load existing capability YAML if it exists.

    This is used to preserve OBSERVED/TRUSTED status during sync.
    """
    cap_path = CAPABILITY_REGISTRY_PATH / f"AURORA_L2_CAPABILITY_{capability_id}.yaml"
    if not cap_path.exists():
        return None
    with open(cap_path, "r") as f:
        return yaml.safe_load(f)


def generate_capability_yaml(cap: CapabilityEntry, existing: Optional[Dict] = None) -> Dict:
    """Generate a single capability registry YAML.

    OBSERVATION-PRESERVING SYNC (PIN-432):
    If the capability already exists with status OBSERVED or TRUSTED,
    we preserve that status and the binding block. This prevents
    sync from regressing capability status.

    Args:
        cap: Capability entry from the ledger
        existing: Existing capability YAML (if any)
    """
    # Determine status: preserve OBSERVED/TRUSTED, otherwise use ledger status
    status = cap.status
    binding = {
        "observed_endpoint": None,
        "observed_method": None,
        "observed_at": None,
        "observation_id": None,
    }
    observation = None
    coherency = None

    if existing:
        existing_status = existing.get("status")
        # Preserve higher-trust status
        if existing_status in ["OBSERVED", "TRUSTED"]:
            status = existing_status
            # Also preserve binding block (SDSR-verified data)
            if "binding" in existing:
                binding = existing["binding"]
            # Preserve observation trace
            if "observation" in existing:
                observation = existing["observation"]
            # Preserve coherency block
            if "coherency" in existing:
                coherency = existing["coherency"]

    yaml_content = {
        "capability_id": cap.capability_id,
        "status": status,
        "source_panels": [cap.panel],
        # Domain extracted from capability_id (e.g., "overview.activity_snapshot" → "OVERVIEW")
        "domain": cap.capability_id.split(".")[0].upper() if "." in cap.capability_id else "UNKNOWN",
        "metadata": {
            "generated_by": "sync_from_intent_ledger.py",
            "generated_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "declared_by": "intent-ledger",
            "declared_on": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        },
        # Human assumption from ledger (may be wrong, SDSR will verify)
        "assumption": {
            "endpoint": cap.assumed_endpoint,
            "method": cap.assumed_method,
            "source": "INTENT_LEDGER",
        },
        # Binding block: preserved if OBSERVED/TRUSTED, otherwise empty
        "binding": binding,
        "acceptance_criteria": cap.acceptance,
    }

    # Add observation trace if preserved
    if observation:
        yaml_content["observation"] = observation

    # Add coherency block if preserved
    if coherency:
        yaml_content["coherency"] = coherency

    if cap.scenario:
        yaml_content["metadata"]["observed_by"] = cap.scenario

    if cap.observed:
        yaml_content["metadata"]["observed_on"] = cap.observed

    # Preserve observed_by/observed_on from existing if we preserved status
    if existing and status in ["OBSERVED", "TRUSTED"]:
        if "metadata" in existing:
            if "observed_by" in existing["metadata"]:
                yaml_content["metadata"]["observed_by"] = existing["metadata"]["observed_by"]
            if "observed_on" in existing["metadata"]:
                yaml_content["metadata"]["observed_on"] = existing["metadata"]["observed_on"]

    return yaml_content


def generate_intent_yaml(
    panel: PanelEntry,
    capabilities: List[CapabilityEntry],
    panel_facet_mapping: Optional[Dict[str, Tuple[str, str]]] = None,
) -> Dict:
    """Generate a single intent YAML from a PanelEntry.

    Args:
        panel: The panel entry to generate YAML for
        capabilities: List of all capabilities
        panel_facet_mapping: Optional dict of panel_id -> (facet_id, criticality)
    """
    # Find matching capability if any
    cap_entry = None
    if panel.capability:
        for cap in capabilities:
            if cap.capability_id == panel.capability:
                cap_entry = cap
                break

    # Build topic_id
    topic_id = f"{panel.domain}.{panel.subdomain}.{panel.topic}"

    # Extract order from panel_id (e.g., "O1" from "OVR-SUM-HL-O1")
    order = panel.panel_id.split("-")[-1] if "-" in panel.panel_id else "O1"

    # Get facet info if available
    facet_id = None
    facet_criticality = None
    if panel_facet_mapping and panel.panel_id in panel_facet_mapping:
        facet_id, facet_criticality = panel_facet_mapping[panel.panel_id]

    intent = {
        "panel_id": panel.panel_id,
        "version": "1.0.0",
        "panel_class": panel.panel_class,
        "metadata": {
            "domain": panel.domain,
            "subdomain": panel.subdomain,
            "topic": panel.topic,
            "topic_id": topic_id,
            "order": order,
            "action_layer": "L2_1",
            "source": "INTENT_LEDGER",
            "review_status": "UNREVIEWED",
            # Facet information (V1.1 - semantic grouping)
            "facet": facet_id,
            "facet_criticality": facet_criticality,
        },
        "display": {
            "name": panel.panel_id,  # Default to panel_id, human can improve
            "visible_by_default": True,
            "nav_required": False,
            "expansion_mode": "INLINE",
        },
        "data": {
            "read": True,
            "download": False,
            "write": False,
            "replay": True,
        },
        "controls": {
            "filtering": False,
            "activate": False,
            "confirmation_required": False,
        },
    }

    # Add capability block if present
    if panel.capability:
        intent["capability"] = {
            "id": panel.capability,
            # Initial status is ASSUMED (human assumption), SDSR elevates to OBSERVED
            "status": cap_entry.status if cap_entry else "ASSUMED",
            # Human assumption from ledger Implementation block
            "assumed_endpoint": cap_entry.assumed_endpoint if cap_entry else None,
            "assumed_method": cap_entry.assumed_method if cap_entry else "GET",
        }
        # Add SDSR block if capability has scenario
        if cap_entry and cap_entry.scenario:
            intent["sdsr"] = {
                "scenario": cap_entry.scenario,
                "verified": cap_entry.observed is not None,
            }
    else:
        intent["capability"] = None
        intent["sdsr"] = None

    # Add notes from purpose
    if panel.purpose:
        intent["notes"] = panel.purpose

    return intent


def write_intent_yamls(
    panels: List[PanelEntry],
    capabilities: List[CapabilityEntry],
    path: Path,
    panel_facet_mapping: Optional[Dict[str, Tuple[str, str]]] = None,
):
    """Write intent YAML files for all panels.

    Args:
        panels: List of panel entries
        capabilities: List of capability entries
        path: Directory to write intent YAMLs
        panel_facet_mapping: Optional dict of panel_id -> (facet_id, criticality)
    """
    path.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0

    for panel in panels:
        # Skip EMPTY state panels (no intent YAML needed)
        if panel.state == "EMPTY":
            skipped += 1
            continue

        filepath = path / f"AURORA_L2_INTENT_{panel.panel_id}.yaml"
        intent = generate_intent_yaml(panel, capabilities, panel_facet_mapping)

        header = f"""# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: design/l2_1/INTENT_LEDGER.md
# Generator: scripts/tools/sync_from_intent_ledger.py
# Panel: {panel.panel_id}
# Naming: AURORA_L2_INTENT_{{panel_id}}.yaml
#
"""
        with open(filepath, "w") as f:
            f.write(header)
            yaml.dump(
                intent,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
        written += 1

    return written, skipped


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


def write_capability_registry(capabilities: List[CapabilityEntry], path: Path) -> Tuple[int, int]:
    """Write capability registry YAMLs with observation-preserving sync.

    OBSERVATION-PRESERVING SYNC (PIN-432):
    Before overwriting a capability, check if it has status OBSERVED or TRUSTED.
    If so, preserve that status and the binding block.

    Returns:
        Tuple of (written, preserved) counts.
    """
    path.mkdir(parents=True, exist_ok=True)

    preserved_count = 0
    written_count = 0

    for cap in capabilities:
        filename = f"AURORA_L2_CAPABILITY_{cap.capability_id}.yaml"
        filepath = path / filename

        # Load existing capability to preserve OBSERVED/TRUSTED status
        existing = load_existing_capability(cap.capability_id)

        yaml_content = generate_capability_yaml(cap, existing=existing)

        # Track preserved status
        if existing and existing.get("status") in ["OBSERVED", "TRUSTED"]:
            preserved_count += 1

        header = """# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: design/l2_1/INTENT_LEDGER.md
# Generator: scripts/tools/sync_from_intent_ledger.py
#
# NOTE: OBSERVED/TRUSTED status is preserved during sync (PIN-432)
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
        written_count += 1

    return written_count, preserved_count


def update_semantic_registry_domains(topology_path: Path, registry_path: Path) -> int:
    """Update semantic registry domains from topology template.

    The topology is the authoritative source for domains and their questions.
    This function extracts domains and updates the semantic registry.

    Returns:
        Number of domains written.
    """
    # Load topology
    topology = load_yaml(topology_path)
    if not topology:
        return 0

    # Load existing semantic registry
    registry = load_yaml(registry_path)
    if not registry:
        return 0

    # Extract domains from topology
    domains_data = {}
    for domain in topology.get("domains", []):
        domain_id = domain.get("id", "")
        description = domain.get("description", [])

        # Convert description list to questions format
        if isinstance(description, list):
            questions = description
        else:
            questions = [description] if description else []

        domains_data[domain_id] = {
            "questions": questions,
            "subdomains": [sd.get("id") for sd in domain.get("subdomains", [])]
        }

    # Update registry
    registry["domains"] = domains_data

    # Write back
    with open(registry_path, "w") as f:
        # Write header comment
        f.write("# AURORA_L2 Semantic Vocabulary Registry\n")
        f.write("# Status: LOCKED\n")
        f.write("# Version: 1.0\n")
        f.write("# Purpose: Defines the closed semantic vocabulary for intent specs\n")
        f.write("#\n")
        f.write("# This file contains the ONLY valid verbs, objects, and effects.\n")
        f.write("# Any semantic not in this registry is INVALID.\n")
        f.write("#\n")
        f.write("# DOMAINS section is AUTO-GENERATED from UI_TOPOLOGY_TEMPLATE.yaml\n")
        f.write("# Run sync_from_intent_ledger.py to update domains.\n\n")

        yaml.dump(
            registry,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    return len(domains_data)


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
    panels, capabilities, facets = parse_ledger(LEDGER_PATH)
    print(f"  Found {len(panels)} panels")
    print(f"  Found {len(capabilities)} capabilities")
    print(f"  Found {len(facets)} facets (V1.1 semantic groupings)")

    # Build facet mapping for intent YAMLs
    panel_facet_mapping = build_panel_facet_mapping(facets)
    panels_with_facets = len(panel_facet_mapping)
    print(f"  Panels with facet assignment: {panels_with_facets}")

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

    # Generate intent YAMLs (with facet propagation)
    print("\nGenerating intent YAMLs...")
    written, skipped = write_intent_yamls(panels, capabilities, INTENTS_DIR, panel_facet_mapping)
    print(f"  Written {written} intent YAMLs to: {INTENTS_DIR}")
    if panels_with_facets > 0:
        print(f"  Propagated facet metadata to {panels_with_facets} panels")
    print(f"  Skipped {skipped} EMPTY state panels")

    # Generate capability registry (with observation-preserving sync)
    print("\nGenerating capability registry...")
    written_count, preserved_count = write_capability_registry(capabilities, CAPABILITY_REGISTRY_PATH)
    print(f"  Written {written_count} files to: {CAPABILITY_REGISTRY_PATH}")
    if preserved_count > 0:
        print(f"  Preserved OBSERVED/TRUSTED status for {preserved_count} capabilities (PIN-432)")

    # Update semantic registry domains
    print("\nUpdating semantic registry domains...")
    domains_count = update_semantic_registry_domains(TOPOLOGY_PATH, SEMANTIC_REGISTRY_PATH)
    print(f"  Updated {domains_count} domains in: {SEMANTIC_REGISTRY_PATH}")

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
    print(f"  - {INTENTS_DIR}/AURORA_L2_INTENT_*.yaml")
    print(f"  - {CAPABILITY_REGISTRY_PATH}/*.yaml")
    print(f"  - {SEMANTIC_REGISTRY_PATH} (domains section)")
    print()
    print("Next steps:")
    print("  1. Validate: python scripts/tools/coherency_gate.py")
    print("  2. Compile: python backend/aurora_l2/SDSR_UI_AURORA_compiler.py")
    print()


if __name__ == "__main__":
    main()
