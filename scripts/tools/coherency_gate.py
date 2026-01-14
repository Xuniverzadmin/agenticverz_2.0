#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | CI
#   Execution: sync
# Role: Validate coherency between topology, intent ledger, and generated artifacts
# Reference: PIN-419

"""
Coherency Gate

Validates that all artifacts are coherent with:
  1. UI_TOPOLOGY_TEMPLATE.yaml (frozen structure)
  2. INTENT_LEDGER.md (human intent)
  3. Generated artifacts (ui_plan.yaml, capability registry)

This is the ONLY multi-artifact validator in the pipeline.

Checks:
  CG-001: Every ledger panel location exists in topology
  CG-002: Every ledger panel slot <= max_slots in topology
  CG-003: No slot collisions in ledger
  CG-004: Every capability references existing panel in ledger
  CG-005: Every referenced SDSR scenario file exists
  CG-006: Status consistency (capability status → panel state)
  CG-007: No orphan panels in ui_plan (not in ledger)
  CG-008: No orphan capabilities in registry (not in ledger)

Usage:
  python scripts/tools/coherency_gate.py           # Normal mode
  python scripts/tools/coherency_gate.py --strict  # ERROR on warnings
  python scripts/tools/coherency_gate.py --fix     # Auto-regenerate artifacts
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from enum import Enum

import yaml

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
TOPOLOGY_PATH = REPO_ROOT / "design" / "l2_1" / "UI_TOPOLOGY_TEMPLATE.yaml"
LEDGER_PATH = REPO_ROOT / "design" / "l2_1" / "INTENT_LEDGER.md"
UI_PLAN_PATH = REPO_ROOT / "design" / "l2_1" / "ui_plan.yaml"
CAPABILITY_REGISTRY_PATH = REPO_ROOT / "backend" / "AURORA_L2_CAPABILITY_REGISTRY"
SDSR_SCENARIOS_PATH = REPO_ROOT / "backend" / "scripts" / "sdsr" / "scenarios"


class Severity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass
class Issue:
    """A coherency issue."""

    code: str
    severity: Severity
    message: str
    location: str


@dataclass
class TopologySlot:
    """A valid slot in the topology."""

    domain: str
    subdomain: str
    topic: str
    max_slots: int


# Status → State binding rules
STATUS_TO_STATE = {
    "DECLARED": {"DRAFT"},
    "DISCOVERED": {"DRAFT", "UNBOUND"},
    "OBSERVED": {"BOUND"},
    "TRUSTED": {"BOUND"},
}


def load_yaml(path: Path) -> Dict:
    """Load YAML file safely."""
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def load_topology() -> Dict[Tuple[str, str, str], TopologySlot]:
    """Load UI_TOPOLOGY_TEMPLATE.yaml and build slot lookup."""
    topology = load_yaml(TOPOLOGY_PATH)
    slot_lookup: Dict[Tuple[str, str, str], TopologySlot] = {}

    if not topology:
        return slot_lookup

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


def parse_ledger_panels(path: Path) -> Dict[str, Dict]:
    """Parse panel entries from ledger (new Location format)."""
    panels = {}
    if not path.exists():
        return panels

    import re

    with open(path, "r") as f:
        content = f.read()

    # Find Panels section
    sections = re.split(r"^## ", content, flags=re.MULTILINE)
    panels_section = None
    for section in sections:
        if section.startswith("Panels"):
            panels_section = section
            break

    if not panels_section:
        return panels

    # Parse each panel
    panel_blocks = re.split(r"^### Panel: ", panels_section, flags=re.MULTILINE)
    for block in panel_blocks[1:]:
        lines = block.strip().split("\n")
        if not lines:
            continue

        panel_id = lines[0].strip()
        fields = {}
        location = {}
        in_location = False

        for line in lines[1:]:
            line = line.strip()

            if line.startswith("Location:"):
                in_location = True
                continue

            if in_location:
                if line.startswith("- "):
                    # Parse location field
                    loc_match = re.match(r"^- (\w+):\s*(.*)$", line)
                    if loc_match:
                        key, value = loc_match.groups()
                        location[key.lower()] = value.strip()
                elif ":" in line and not line.startswith("-"):
                    in_location = False
                    if ":" in line:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            key, value = parts
                            fields[key.lower().strip()] = value.strip()
                continue

            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key, value = parts
                    fields[key.lower().strip()] = value.strip()

        # Merge location into fields for compatibility
        fields["domain"] = location.get("domain", fields.get("domain", ""))
        fields["subdomain"] = location.get("subdomain", fields.get("subdomain", ""))
        fields["topic"] = location.get("topic", fields.get("topic", ""))
        fields["slot"] = location.get("slot", "1")

        panels[panel_id] = fields

    return panels


def parse_ledger_capabilities(path: Path) -> Dict[str, Dict]:
    """Parse capability entries from ledger."""
    capabilities = {}
    if not path.exists():
        return capabilities

    import re

    with open(path, "r") as f:
        content = f.read()

    # Find Capabilities section
    sections = re.split(r"^## ", content, flags=re.MULTILINE)
    caps_section = None
    for section in sections:
        if section.startswith("Capabilities"):
            caps_section = section
            break

    if not caps_section:
        return capabilities

    # Parse each capability
    cap_blocks = re.split(r"^### Capability: ", caps_section, flags=re.MULTILINE)
    for block in cap_blocks[1:]:
        lines = block.strip().split("\n")
        if not lines:
            continue

        cap_id = lines[0].strip()
        fields = {}

        for line in lines[1:]:
            line = line.strip()
            if ":" in line and not line.startswith("-"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key, value = parts
                    fields[key.lower().strip()] = value.strip()

        capabilities[cap_id] = fields

    return capabilities


def extract_ui_plan_panels(ui_plan: Dict) -> Set[str]:
    """Extract all panel IDs from ui_plan."""
    panels = set()
    for domain in ui_plan.get("domains", []):
        for subdomain in domain.get("subdomains", []):
            for topic in subdomain.get("topics", []):
                for panel in topic.get("panels", []):
                    panels.add(panel.get("panel_id", ""))
    return panels


def extract_ui_plan_panel_states(ui_plan: Dict) -> Dict[str, str]:
    """Extract panel_id → state mapping from ui_plan."""
    states = {}
    for domain in ui_plan.get("domains", []):
        for subdomain in domain.get("subdomains", []):
            for topic in subdomain.get("topics", []):
                for panel in topic.get("panels", []):
                    panel_id = panel.get("panel_id", "")
                    state = panel.get("state", "EMPTY")
                    states[panel_id] = state
    return states


def load_capability_registry() -> Dict[str, Dict]:
    """Load all capability registry files."""
    capabilities = {}
    if not CAPABILITY_REGISTRY_PATH.exists():
        return capabilities

    for yaml_file in CAPABILITY_REGISTRY_PATH.glob("*.yaml"):
        if yaml_file.name == "CAPABILITY_STATUS_MODEL.yaml":
            continue
        cap = load_yaml(yaml_file)
        if cap and "capability_id" in cap:
            capabilities[cap["capability_id"]] = cap

    return capabilities


def check_coherency(strict: bool = False) -> Tuple[List[Issue], bool]:
    """Run all coherency checks."""
    issues: List[Issue] = []

    # Load sources
    slot_lookup = load_topology()
    ledger_panels = parse_ledger_panels(LEDGER_PATH)
    ledger_caps = parse_ledger_capabilities(LEDGER_PATH)
    ui_plan = load_yaml(UI_PLAN_PATH)
    ui_plan_panels = extract_ui_plan_panels(ui_plan)
    ui_plan_states = extract_ui_plan_panel_states(ui_plan)
    registry_caps = load_capability_registry()

    # Check topology exists
    if not slot_lookup:
        issues.append(
            Issue(
                code="CG-000",
                severity=Severity.ERROR,
                message=f"Topology template not found at {TOPOLOGY_PATH}",
                location="UI_TOPOLOGY_TEMPLATE.yaml",
            )
        )
        return issues, False

    # CG-001: Every ledger panel location exists in topology
    for panel_id, fields in ledger_panels.items():
        domain = fields.get("domain", "")
        subdomain = fields.get("subdomain", "")
        topic = fields.get("topic", "")
        key = (domain, subdomain, topic)

        if key not in slot_lookup:
            issues.append(
                Issue(
                    code="CG-001",
                    severity=Severity.ERROR,
                    message=f"Location ({domain}/{subdomain}/{topic}) not in topology",
                    location=f"Panel: {panel_id}",
                )
            )

    # CG-002: Every ledger panel slot <= max_slots
    for panel_id, fields in ledger_panels.items():
        domain = fields.get("domain", "")
        subdomain = fields.get("subdomain", "")
        topic = fields.get("topic", "")
        key = (domain, subdomain, topic)

        if key in slot_lookup:
            slot = slot_lookup[key]
            try:
                panel_slot = int(fields.get("slot", "1"))
            except ValueError:
                panel_slot = 1

            if panel_slot > slot.max_slots:
                issues.append(
                    Issue(
                        code="CG-002",
                        severity=Severity.ERROR,
                        message=f"Slot {panel_slot} exceeds max {slot.max_slots}",
                        location=f"Panel: {panel_id}",
                    )
                )

    # CG-003: No slot collisions
    slot_usage: Dict[Tuple[str, str, str, int], str] = {}
    for panel_id, fields in ledger_panels.items():
        domain = fields.get("domain", "")
        subdomain = fields.get("subdomain", "")
        topic = fields.get("topic", "")
        try:
            slot = int(fields.get("slot", "1"))
        except ValueError:
            slot = 1
        key = (domain, subdomain, topic, slot)

        if key in slot_usage:
            existing = slot_usage[key]
            issues.append(
                Issue(
                    code="CG-003",
                    severity=Severity.ERROR,
                    message=f"Slot collision with '{existing}' at {domain}/{subdomain}/{topic} slot {slot}",
                    location=f"Panel: {panel_id}",
                )
            )
        else:
            slot_usage[key] = panel_id

    # CG-004: Every capability references existing panel
    ledger_panel_ids = set(ledger_panels.keys())
    for cap_id, fields in ledger_caps.items():
        panel_id = fields.get("panel", "")
        if panel_id and panel_id != "UNKNOWN" and panel_id not in ledger_panel_ids:
            issues.append(
                Issue(
                    code="CG-004",
                    severity=Severity.ERROR,
                    message=f"Capability references non-existent panel '{panel_id}'",
                    location=f"Capability: {cap_id}",
                )
            )

    # CG-005: Every referenced SDSR scenario file exists
    for cap_id, fields in ledger_caps.items():
        scenario = fields.get("scenario", "")
        if scenario and scenario != "NONE":
            scenario_file = SDSR_SCENARIOS_PATH / f"{scenario}.yaml"
            if not scenario_file.exists():
                issues.append(
                    Issue(
                        code="CG-005",
                        severity=Severity.WARNING if not strict else Severity.ERROR,
                        message=f"Referenced SDSR scenario '{scenario}' not found",
                        location=f"Capability: {cap_id}",
                    )
                )

    # CG-006: Status consistency
    for cap_id, fields in ledger_caps.items():
        status = fields.get("status", "DECLARED")
        panel_id = fields.get("panel", "")

        if panel_id and panel_id in ui_plan_states:
            panel_state = ui_plan_states[panel_id]
            expected_states = STATUS_TO_STATE.get(status, set())

            if expected_states and panel_state not in expected_states:
                issues.append(
                    Issue(
                        code="CG-006",
                        severity=Severity.WARNING if not strict else Severity.ERROR,
                        message=f"Status '{status}' expects state {expected_states}, got '{panel_state}'",
                        location=f"Capability: {cap_id} → Panel: {panel_id}",
                    )
                )

    # CG-007: No orphan panels in ui_plan
    for panel_id in ui_plan_panels:
        if panel_id not in ledger_panel_ids:
            issues.append(
                Issue(
                    code="CG-007",
                    severity=Severity.ERROR,
                    message="Panel in ui_plan not in ledger",
                    location=f"Panel: {panel_id}",
                )
            )

    # CG-008: No orphan capabilities in registry
    ledger_cap_ids = set(ledger_caps.keys())
    for cap_id in registry_caps:
        if cap_id not in ledger_cap_ids:
            issues.append(
                Issue(
                    code="CG-008",
                    severity=Severity.WARNING if not strict else Severity.ERROR,
                    message="Capability in registry not in ledger",
                    location=f"Capability: {cap_id}",
                )
            )

    # Determine pass/fail
    has_errors = any(i.severity == Severity.ERROR for i in issues)
    passed = not has_errors

    return issues, passed


def main():
    parser = argparse.ArgumentParser(
        description="Coherency Gate - validate topology and intent ledger coherency"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Regenerate artifacts from ledger"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("COHERENCY GATE (TOPOLOGY-AWARE)")
    print("=" * 60)
    print()

    if args.fix:
        print("Running sync_from_intent_ledger.py to regenerate artifacts...")
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "tools" / "sync_from_intent_ledger.py"),
            ],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            sys.exit(1)
        print()

    print(f"Checking coherency (strict={args.strict})...")
    print()

    issues, passed = check_coherency(strict=args.strict)

    # Report issues
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for issue in errors:
            print(f"  [{issue.code}] {issue.location}")
            print(f"         {issue.message}")
        print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for issue in warnings:
            print(f"  [{issue.code}] {issue.location}")
            print(f"         {issue.message}")
        print()

    # Summary
    print("=" * 60)
    if passed:
        print("COHERENCY GATE: PASS")
        if warnings:
            print(f"  {len(warnings)} warnings (use --strict to fail on warnings)")
    else:
        print("COHERENCY GATE: FAIL")
        print(f"  {len(errors)} errors, {len(warnings)} warnings")
    print("=" * 60)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
