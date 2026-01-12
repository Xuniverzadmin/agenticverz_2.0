#!/usr/bin/env python3
"""
Apply Phase-2A.1 Affordance Controls to UI Projection Lock

Reference: PIN-366, phase_2a1_affordance_spec.yaml

This script reads the affordance specification and adds blocked action controls
to the ui_projection_lock.json file.

Exit codes:
  0 = Successfully applied affordances
  1 = Error during application
  2 = Dry run completed (no changes made)
"""

import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List


def load_yaml(path: Path) -> Dict:
    """Load YAML file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> Dict:
    """Load JSON file."""
    with open(path, 'r') as f:
        return json.load(f)


def save_json(path: Path, data: Dict) -> None:
    """Save JSON file with pretty formatting."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def find_panel(projection: Dict, panel_id: str) -> Dict | None:
    """Find a panel by ID in the projection."""
    for domain in projection.get('domains', []):
        for panel in domain.get('panels', []):
            if panel.get('panel_id') == panel_id:
                return panel
    return None


def add_controls_to_panel(panel: Dict, new_controls: List[Dict]) -> int:
    """Add new controls to a panel, avoiding duplicates."""
    existing_types = {c.get('type') for c in panel.get('controls', [])}
    added = 0

    for control in new_controls:
        if control.get('type') not in existing_types:
            # Build control entry matching projection schema
            new_control = {
                'type': control['type'],
                'order': control['order'],
                'icon': control['icon'],
                'category': control['category'],
                'enabled': control.get('enabled', False),
                'visibility': control.get('visibility', 'ALWAYS')
            }

            # Add disabled_reason if disabled
            if not new_control['enabled']:
                new_control['disabled_reason'] = control.get('disabled_reason', 'Action unavailable')

            panel['controls'].append(new_control)
            panel['control_count'] = len(panel['controls'])
            added += 1

    # Re-sort controls by order
    panel['controls'].sort(key=lambda c: c.get('order', 999))

    return added


def apply_domain_affordances(projection: Dict, domain_spec: Dict, domain_name: str) -> Dict:
    """Apply affordances for a single domain."""
    result = {
        'domain': domain_name,
        'panels_modified': 0,
        'controls_added': 0,
        'details': []
    }

    for panel_spec in domain_spec.get('target_panels', []):
        panel_id = panel_spec.get('panel_id')
        panel = find_panel(projection, panel_id)

        if not panel:
            result['details'].append({
                'panel_id': panel_id,
                'status': 'NOT_FOUND',
                'controls_added': 0
            })
            continue

        new_controls = panel_spec.get('new_controls', [])
        if new_controls:
            added = add_controls_to_panel(panel, new_controls)
            if added > 0:
                result['panels_modified'] += 1
                result['controls_added'] += added
                result['details'].append({
                    'panel_id': panel_id,
                    'panel_name': panel.get('panel_name'),
                    'status': 'MODIFIED',
                    'controls_added': added,
                    'control_types': [c['type'] for c in new_controls]
                })

    return result


def update_statistics(projection: Dict) -> None:
    """Update projection statistics after modifications."""
    total_controls = 0

    for domain in projection.get('domains', []):
        domain_controls = 0
        for panel in domain.get('panels', []):
            panel_controls = len(panel.get('controls', []))
            panel['control_count'] = panel_controls
            domain_controls += panel_controls
        domain['total_controls'] = domain_controls
        total_controls += domain_controls

    projection['_statistics']['control_count'] = total_controls


def apply_affordances(spec_path: Path, projection_path: Path, dry_run: bool = False) -> Dict:
    """
    Apply all affordances from spec to projection.

    Returns a summary dict with results.
    """
    # Load files
    spec = load_yaml(spec_path)
    projection = load_json(projection_path)

    results = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'spec_version': spec.get('version'),
        'phase': spec.get('phase'),
        'dry_run': dry_run,
        'domains': [],
        'totals': {
            'panels_modified': 0,
            'controls_added': 0
        }
    }

    # Map domain keys to names
    domain_map = {
        'activity_domain': 'Activity',
        'incidents_domain': 'Incidents',
        'policies_domain': 'Policies',
        'logs_domain': 'Logs'
    }

    # Apply each domain's affordances
    for spec_key, domain_name in domain_map.items():
        domain_spec = spec.get(spec_key, {})
        if domain_spec:
            domain_result = apply_domain_affordances(projection, domain_spec, domain_name)
            results['domains'].append(domain_result)
            results['totals']['panels_modified'] += domain_result['panels_modified']
            results['totals']['controls_added'] += domain_result['controls_added']

    # Update statistics
    update_statistics(projection)

    # Update metadata
    projection['_meta']['processing_stage'] = 'PHASE_2A1_APPLIED'
    projection['_meta']['phase_2a1_applied_at'] = results['timestamp']

    # Save if not dry run
    if not dry_run:
        save_json(projection_path, projection)
        results['saved'] = True
    else:
        results['saved'] = False

    return results


def print_results(results: Dict) -> None:
    """Print formatted results."""
    print("\n" + "=" * 60)
    print("Phase-2A.1 Affordance Application Results")
    print("=" * 60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Spec Version: {results['spec_version']}")
    print(f"Phase: {results['phase']}")
    print(f"Dry Run: {results['dry_run']}")
    print()

    for domain in results['domains']:
        print(f"\n{domain['domain']} Domain:")
        print(f"  Panels Modified: {domain['panels_modified']}")
        print(f"  Controls Added: {domain['controls_added']}")

        for detail in domain['details']:
            status_icon = "+" if detail['status'] == 'MODIFIED' else "!"
            print(f"    {status_icon} {detail['panel_id']}: {detail['status']}")
            if detail.get('control_types'):
                print(f"      Controls: {', '.join(detail['control_types'])}")

    print()
    print("-" * 60)
    print("TOTALS:")
    print(f"  Panels Modified: {results['totals']['panels_modified']}")
    print(f"  Controls Added: {results['totals']['controls_added']}")
    print(f"  Saved: {results['saved']}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Apply Phase-2A.1 Affordance Controls to UI Projection'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--spec',
        type=Path,
        default=Path('design/l2_1/step_3/phase_2a1_affordance_spec.yaml'),
        help='Path to affordance specification'
    )
    parser.add_argument(
        '--projection',
        type=Path,
        default=Path('design/l2_1/ui_contract/ui_projection_lock.json'),
        help='Path to UI projection lock file'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    args = parser.parse_args()

    # Verify files exist
    if not args.spec.exists():
        print(f"Error: Spec file not found: {args.spec}")
        return 1
    if not args.projection.exists():
        print(f"Error: Projection file not found: {args.projection}")
        return 1

    try:
        results = apply_affordances(args.spec, args.projection, args.dry_run)

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print_results(results)

        if args.dry_run:
            print("\nDry run completed. No changes were made.")
            return 2

        if results['totals']['controls_added'] > 0:
            print(f"\nSuccessfully added {results['totals']['controls_added']} blocked action controls.")
        else:
            print("\nNo new controls were added (all already exist).")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
