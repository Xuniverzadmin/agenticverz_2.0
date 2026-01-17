#!/usr/bin/env python3
"""
AURORA L2 UI Plan Binder (Phase 6.5 Automation)

Syncs ui_plan.yaml with panel binding state after successful HISAR execution.
Closes the loop between SDSR observation and ui_plan.yaml source of truth.

WHY THIS EXISTS:
    Before this script, HISAR would update:
    - Intent YAML (verified, observation trace)
    - Capability YAML (DECLARED -> OBSERVED)
    - Projection lock (compiled)
    - Public projection (copied)

    But NOT:
    - ui_plan.yaml (still showed EMPTY)

    This created a sync gap where the source of truth (ui_plan.yaml) was
    inconsistent with the actual pipeline state. This script closes that gap.

WHAT IT DOES:
    1. Reads intent YAML for the panel
    2. Verifies capability is OBSERVED or TRUSTED
    3. Updates ui_plan.yaml: state -> BOUND, intent_spec, expected_capability
    4. Validates update succeeded

EXECUTION CONTRACT:
    - ONLY runs after successful SDSR observation (Phase 5)
    - ONLY binds if capability status is OBSERVED or TRUSTED
    - IDEMPOTENT: Safe to run multiple times
    - ATOMIC: Updates single panel entry

Usage:
    python aurora_ui_plan_bind.py --panel OVR-SUM-HL-O4
    python aurora_ui_plan_bind.py --panel OVR-SUM-HL-O4 --dry-run

Author: AURORA L2 Automation
Reference: PIN-425 (UI Plan Sync Closure)
"""

import yaml
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
UI_PLAN_PATH = REPO_ROOT / "design/l2_1/ui_plan.yaml"
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"


def load_ui_plan() -> Dict:
    """Load ui_plan.yaml."""
    if not UI_PLAN_PATH.exists():
        print(f"ERROR: ui_plan.yaml not found at {UI_PLAN_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(UI_PLAN_PATH) as f:
        return yaml.safe_load(f)


def save_ui_plan(ui_plan: Dict):
    """Save ui_plan.yaml with preserved header."""
    header = """# GENERATED FILE - DO NOT EDIT MANUALLY
# Source: design/l2_1/INTENT_LEDGER.md
# Topology: design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml
# Generator: scripts/tools/sync_from_intent_ledger.py
# Last Updated By: aurora_ui_plan_bind.py
# Last Updated: {timestamp}
# To modify: Edit INTENT_LEDGER.md and re-run generator
#
""".format(timestamp=datetime.now(timezone.utc).isoformat())

    with open(UI_PLAN_PATH, 'w') as f:
        f.write(header)
        yaml.dump(ui_plan, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def load_intent(panel_id: str) -> Optional[Dict]:
    """Load intent YAML for panel (new naming convention with legacy fallback)."""
    # Try new naming convention first
    intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"
    if not intent_path.exists():
        # Fall back to legacy naming
        intent_path = INTENTS_DIR / f"{panel_id}.yaml"
    if not intent_path.exists():
        return None
    with open(intent_path) as f:
        return yaml.safe_load(f)


def load_capability(capability_id: str) -> Optional[Dict]:
    """Load capability YAML."""
    cap_path = CAPABILITY_REGISTRY / f"AURORA_L2_CAPABILITY_{capability_id}.yaml"
    if not cap_path.exists():
        return None
    with open(cap_path) as f:
        return yaml.safe_load(f)


def find_panel_in_plan(ui_plan: Dict, panel_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Find panel entry in ui_plan.yaml.
    Returns (panel_dict, path_description) or (None, None) if not found.
    """
    domains = ui_plan.get('domains', [])
    for domain in domains:
        domain_id = domain.get('id')
        for subdomain in domain.get('subdomains', []):
            subdomain_id = subdomain.get('id')
            for topic in subdomain.get('topics', []):
                topic_id = topic.get('id')
                for panel in topic.get('panels', []):
                    if panel.get('panel_id') == panel_id:
                        path = f"{domain_id}.{subdomain_id}.{topic_id}"
                        return panel, path
    return None, None


def bind_panel(panel_id: str, dry_run: bool = False, verbose: bool = False) -> bool:
    """
    Bind a panel in ui_plan.yaml after successful HISAR execution.

    Returns True if successful, False otherwise.
    """
    print(f"{'[DRY RUN] ' if dry_run else ''}Binding panel: {panel_id}")

    # Step 1: Load intent
    intent = load_intent(panel_id)
    if not intent:
        print(f"  ERROR: Intent YAML not found for {panel_id}", file=sys.stderr)
        print(f"  Path: {INTENTS_DIR / f'{panel_id}.yaml'}", file=sys.stderr)
        return False

    if verbose:
        print(f"  Intent YAML: Found")

    # Step 2: Extract capability info
    capability_block = intent.get('capability', {})
    capability_id = capability_block.get('id')
    if not capability_id:
        print(f"  ERROR: Intent missing capability.id", file=sys.stderr)
        return False

    if verbose:
        print(f"  Capability ID: {capability_id}")

    # Step 3: Load and verify capability status
    capability = load_capability(capability_id)
    if not capability:
        print(f"  ERROR: Capability YAML not found for {capability_id}", file=sys.stderr)
        return False

    cap_status = capability.get('status')
    if cap_status not in ['OBSERVED', 'TRUSTED']:
        print(f"  ERROR: Capability status is {cap_status}, must be OBSERVED or TRUSTED", file=sys.stderr)
        print(f"  Hint: Run SDSR first to observe the capability", file=sys.stderr)
        return False

    if verbose:
        print(f"  Capability status: {cap_status}")

    # Step 4: Load ui_plan and find panel
    ui_plan = load_ui_plan()
    panel, path = find_panel_in_plan(ui_plan, panel_id)

    if not panel:
        print(f"  ERROR: Panel {panel_id} not found in ui_plan.yaml", file=sys.stderr)
        return False

    if verbose:
        print(f"  Panel path: {path}")

    # Step 5: Check current state
    current_state = panel.get('state', 'EMPTY')
    if verbose:
        print(f"  Current state: {current_state}")

    if current_state == 'BOUND':
        print(f"  Panel already BOUND, verifying consistency...")
        intent_spec = panel.get('intent_spec')
        expected_cap = panel.get('expected_capability')
        expected_intent_spec = f"design/l2_1/intents/AURORA_L2_INTENT_{panel_id}.yaml"

        if intent_spec != expected_intent_spec:
            print(f"    WARNING: intent_spec mismatch: {intent_spec} != {expected_intent_spec}")
        if expected_cap != capability_id:
            print(f"    WARNING: capability mismatch: {expected_cap} != {capability_id}")
        else:
            print(f"  Consistency verified, no update needed")
            return True

    # Step 6: Update panel
    new_state = 'BOUND'
    new_intent_spec = f"design/l2_1/intents/AURORA_L2_INTENT_{panel_id}.yaml"
    new_expected_capability = capability_id

    print(f"  Updating ui_plan.yaml:")
    print(f"    state: {current_state} -> {new_state}")
    print(f"    intent_spec: {panel.get('intent_spec')} -> {new_intent_spec}")
    print(f"    expected_capability: {panel.get('expected_capability')} -> {new_expected_capability}")

    if dry_run:
        print(f"  [DRY RUN] Would update panel in ui_plan.yaml")
        return True

    # Apply update
    panel['state'] = new_state
    panel['intent_spec'] = new_intent_spec
    panel['expected_capability'] = new_expected_capability

    # Save
    save_ui_plan(ui_plan)
    print(f"  Updated ui_plan.yaml")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 UI Plan Binder - Syncs ui_plan.yaml after HISAR execution"
    )
    parser.add_argument("--panel", required=True, help="Panel ID to bind (e.g., OVR-SUM-HL-O4)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    success = bind_panel(args.panel, dry_run=args.dry_run, verbose=args.verbose)

    if success:
        print()
        if args.dry_run:
            print("DRY RUN complete")
        else:
            print(f"UI Plan Bind complete for {args.panel}")
            print()
            print("Sync status:")
            print(f"  ui_plan.yaml: UPDATED")
            print(f"  Panel state: BOUND")
        return 0
    else:
        print()
        print(f"Failed to bind {args.panel}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
