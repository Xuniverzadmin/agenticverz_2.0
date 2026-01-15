#!/usr/bin/env python3
"""
AURORA L2 Intent Scaffolder (Phase 2 Automation)

Generates intent YAML skeleton from ui_plan.yaml panel entry.
Human fills semantic content (description, notes, expectations).
Machine fills structural content (IDs, paths, default blocks).

Usage:
    python aurora_intent_scaffold.py --panel OVR-SUM-HL-O2
    python aurora_intent_scaffold.py --panel OVR-SUM-HL-O2 --capability overview.metric_snapshot

What gets auto-filled:
    - panel_id, version
    - metadata (domain, subdomain, topic, order)
    - panel_class (from ui_plan)
    - display defaults
    - data permissions defaults
    - controls defaults
    - empty capability block
    - empty sdsr block

What human must fill:
    - display.name (meaningful panel name)
    - capability.id (what backend capability powers this)
    - capability.endpoint (API endpoint)
    - notes (semantic description)

Author: AURORA L2 Automation
"""

import yaml
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
UI_PLAN = REPO_ROOT / "design/l2_1/ui_plan.yaml"
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
SEMANTIC_REGISTRY = REPO_ROOT / "design/l2_1/AURORA_L2_SEMANTIC_REGISTRY.yaml"


def load_ui_plan() -> Dict:
    """Load ui_plan.yaml."""
    with open(UI_PLAN) as f:
        return yaml.safe_load(f)


def find_panel_in_ui_plan(ui_plan: Dict, panel_id: str) -> Optional[Dict]:
    """Find panel entry in ui_plan with full context."""
    for domain in ui_plan.get('domains', []):
        for subdomain in domain.get('subdomains', []):
            for topic in subdomain.get('topics', []):
                for panel in topic.get('panels', []):
                    if panel.get('panel_id') == panel_id:
                        return {
                            'panel': panel,
                            'domain_id': domain.get('id'),
                            'subdomain_id': subdomain.get('id'),
                            'topic_id': topic.get('id'),
                        }
    return None


def extract_order_from_panel_id(panel_id: str) -> str:
    """Extract order (O1, O2, etc.) from panel_id."""
    parts = panel_id.split('-')
    if parts:
        return parts[-1]  # Last part is typically O1, O2, etc.
    return "O1"


def scaffold_intent(
    panel_id: str,
    domain_id: str,
    subdomain_id: str,
    topic_id: str,
    panel_class: str,
    slot: int,
    capability_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    panel_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate intent YAML structure.
    """
    order = extract_order_from_panel_id(panel_id)
    topic_full_id = f"{domain_id}.{subdomain_id}.{topic_id}"

    intent = {
        'panel_id': panel_id,
        'version': '1.0.0',
        'panel_class': panel_class,
        'metadata': {
            'domain': domain_id,
            'subdomain': subdomain_id,
            'topic': topic_id,
            'topic_id': topic_full_id,
            'order': order,
            'action_layer': 'L2_1',
            'source': 'AURORA_AUTOMATION',
            'review_status': 'PENDING',
        },
        'display': {
            'name': panel_name or f"[TODO: Panel Name for {panel_id}]",
            'visible_by_default': True,
            'nav_required': False,
            'expansion_mode': 'INLINE',
        },
        'data': {
            'read': True,
            'download': False,
            'write': False,
            'replay': panel_class == 'interpretation',
        },
        'controls': {
            'filtering': False,
            'activate': False,
            'confirmation_required': False,
        },
        'capability': {
            'id': capability_id or f"[TODO: capability.id for {panel_id}]",
            'status': 'DECLARED',
            'endpoint': endpoint or f"[TODO: /api/v1/...]",
            'method': 'GET',
            'data_mapping': {
                '_note': 'Define field mappings from API response to panel display'
            }
        },
        'sdsr': {
            'scenario': f"[TODO: scenario name]",
            'verified': False,
            'verification_date': None,
            'checks': {
                'endpoint_exists': 'PENDING',
                'schema_matches': 'PENDING',
                'auth_works': 'PENDING',
                'data_is_real': 'PENDING',
            }
        },
        'notes': f"[TODO: Describe what this panel shows and why it matters]",
    }

    return intent


def write_intent_yaml(panel_id: str, intent: Dict, force: bool = False) -> Path:
    """Write intent YAML to file."""
    INTENTS_DIR.mkdir(parents=True, exist_ok=True)
    # Use new naming convention: AURORA_L2_INTENT_{panel_id}.yaml
    intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"

    if intent_path.exists() and not force:
        raise FileExistsError(f"Intent YAML already exists: {intent_path}")

    # Generate YAML with header comment
    header = f"""# AURORA_L2 Intent Spec: {panel_id}
# Generated: {datetime.now(timezone.utc).isoformat()}
# Generator: aurora_intent_scaffold.py
# Status: DRAFT (requires human review)
#
# TODO:
#   1. Fill display.name with meaningful panel name
#   2. Set capability.id to the backend capability
#   3. Set capability.endpoint to the API endpoint
#   4. Write notes describing the panel purpose
#   5. Register in AURORA_L2_INTENT_REGISTRY.yaml
#   6. Run coherency check: aurora_coherency_check.py --panel {panel_id}
#
"""

    with open(intent_path, 'w') as f:
        f.write(header)
        yaml.dump(intent, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return intent_path


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 Intent Scaffolder - Generates intent YAML skeleton"
    )
    parser.add_argument("--panel", required=True, help="Panel ID (must exist in ui_plan.yaml)")
    parser.add_argument("--capability", help="Capability ID (optional)")
    parser.add_argument("--endpoint", help="API endpoint (optional)")
    parser.add_argument("--name", help="Panel display name (optional)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing intent YAML")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    args = parser.parse_args()

    # Load ui_plan
    if not UI_PLAN.exists():
        print(f"ERROR: ui_plan.yaml not found at {UI_PLAN}", file=sys.stderr)
        return 1

    ui_plan = load_ui_plan()

    # Find panel
    panel_entry = find_panel_in_ui_plan(ui_plan, args.panel)
    if not panel_entry:
        print(f"ERROR: Panel '{args.panel}' not found in ui_plan.yaml", file=sys.stderr)
        print("Available panels:", file=sys.stderr)
        for domain in ui_plan.get('domains', []):
            for subdomain in domain.get('subdomains', []):
                for topic in subdomain.get('topics', []):
                    for panel in topic.get('panels', []):
                        print(f"  - {panel.get('panel_id')}", file=sys.stderr)
        return 1

    panel_data = panel_entry['panel']

    # Check if intent already exists (check both new and legacy naming)
    intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{args.panel}.yaml"
    legacy_path = INTENTS_DIR / f"{args.panel}.yaml"
    if (intent_path.exists() or legacy_path.exists()) and not args.force and not args.dry_run:
        print(f"ERROR: Intent YAML already exists: {intent_path}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        return 1

    # Generate scaffold
    intent = scaffold_intent(
        panel_id=args.panel,
        domain_id=panel_entry['domain_id'],
        subdomain_id=panel_entry['subdomain_id'],
        topic_id=panel_entry['topic_id'],
        panel_class=panel_data.get('panel_class', 'execution'),
        slot=panel_data.get('slot', 1),
        capability_id=args.capability,
        endpoint=args.endpoint,
        panel_name=args.name,
    )

    if args.dry_run:
        print("# DRY RUN - Would write to:", intent_path)
        print("=" * 70)
        print(yaml.dump(intent, default_flow_style=False, sort_keys=False))
        return 0

    # Write file
    try:
        output_path = write_intent_yaml(args.panel, intent, force=args.force)
        print(f"✅ Created intent YAML: {output_path.relative_to(REPO_ROOT)}")
        print()
        print("Next steps:")
        print(f"  1. Edit {output_path.relative_to(REPO_ROOT)} to fill TODO fields")
        print(f"  2. Run: python aurora_intent_registry_sync.py --panel {args.panel}")
        print(f"  3. Run: python aurora_coherency_check.py --panel {args.panel}")
        return 0
    except FileExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
