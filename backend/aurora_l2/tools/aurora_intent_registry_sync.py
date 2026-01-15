#!/usr/bin/env python3
"""
AURORA L2 Intent Registry Sync (Phase 2 Automation)

Synchronizes intent YAML files with AURORA_L2_INTENT_REGISTRY.yaml.
Creates registry entries for new intents with status=DRAFT.
Human must approve (DRAFT → APPROVED) before compilation.

Usage:
    python aurora_intent_registry_sync.py --panel OVR-SUM-HL-O2
    python aurora_intent_registry_sync.py --all
    python aurora_intent_registry_sync.py --approve OVR-SUM-HL-O2

Rules:
    - Registry entry auto-created when intent YAML exists
    - Status defaults to DRAFT
    - DRAFT → APPROVED requires explicit human action
    - Compilation only processes APPROVED entries

Author: AURORA L2 Automation
"""

import yaml
import sys
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
INTENT_REGISTRY = REPO_ROOT / "design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml"


def load_intent_registry() -> Dict:
    """Load intent registry YAML.

    Returns the 'intents' sub-dictionary for direct access to entries.
    The registry has structure: {version, intents: {panel_id: entry, ...}}
    """
    if INTENT_REGISTRY.exists():
        with open(INTENT_REGISTRY) as f:
            data = yaml.safe_load(f) or {}
            # Return just the intents dict for backwards compatibility
            # The registry has nested structure: {version, intents: {...}}
            return data.get('intents', data)
    return {}


def save_intent_registry(registry: Dict):
    """Save intent registry YAML.

    Wraps the intents dict in the proper structure with version and metadata.
    """
    # Load existing file to preserve top-level metadata
    existing = {}
    if INTENT_REGISTRY.exists():
        with open(INTENT_REGISTRY) as f:
            existing = yaml.safe_load(f) or {}

    # Preserve top-level keys, update intents
    output = {
        'version': existing.get('version', '1.0.0'),
        'generated_at': existing.get('generated_at', datetime.now(timezone.utc).strftime('%Y-%m-%d')),
        'generator': 'aurora_intent_registry_sync.py',
        'intents': registry,
    }

    header = """# AURORA L2 Intent Registry
# Generated/Updated by: aurora_intent_registry_sync.py
# Last Updated: {timestamp}
#
# Status values:
#   DRAFT    - Intent created, awaiting human review
#   APPROVED - Human approved, eligible for compilation
#   REJECTED - Explicitly rejected (will not compile)
#   DEFERRED - Postponed to future release
#
# Rules:
#   - Only APPROVED intents are compiled into projection
#   - DRAFT → APPROVED requires explicit approval
#   - sdsr_verified is set by SDSR automation (not humans)
#
# Hash Freezing (Phase 5.5 Hardening):
#   - frozen_hash: SHA256 of intent YAML at APPROVED time
#   - If intent is modified after APPROVED → staleness detected
#   - Use --verify to check for intent rot
#
""".format(timestamp=datetime.now(timezone.utc).isoformat())

    with open(INTENT_REGISTRY, 'w') as f:
        f.write(header)
        yaml.dump(output, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def load_intent_yaml(panel_id: str) -> Optional[Dict]:
    """Load intent YAML for a panel."""
    # New naming convention with fallback to legacy
    intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"
    if not intent_path.exists():
        intent_path = INTENTS_DIR / f"{panel_id}.yaml"  # Legacy fallback
    if not intent_path.exists():
        return None
    with open(intent_path) as f:
        return yaml.safe_load(f)


def compute_intent_hash(panel_id: str) -> Optional[str]:
    """
    Compute SHA256 hash of intent YAML content.

    This hash is frozen at APPROVED time to detect post-approval modifications.
    Any change to the intent after approval will produce a different hash,
    triggering the staleness check.
    """
    # New naming convention with fallback to legacy
    intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"
    if not intent_path.exists():
        intent_path = INTENTS_DIR / f"{panel_id}.yaml"  # Legacy fallback
    if not intent_path.exists():
        return None

    # Read raw content for consistent hashing
    with open(intent_path, 'rb') as f:
        content = f.read()

    return hashlib.sha256(content).hexdigest()


def verify_intent_hash(panel_id: str, registry: Dict) -> bool:
    """
    Verify that intent hash matches frozen hash at approval.

    Returns True if hash matches or no frozen hash exists.
    Returns False if hash differs (intent modified after approval).
    """
    if panel_id not in registry:
        return True

    frozen_hash = registry[panel_id].get('frozen_hash')
    if not frozen_hash:
        return True  # No frozen hash to compare

    current_hash = compute_intent_hash(panel_id)
    return current_hash == frozen_hash


def create_registry_entry(panel_id: str, intent: Dict) -> Dict:
    """Create a registry entry from intent YAML."""
    metadata = intent.get('metadata', {})
    capability = intent.get('capability', {})
    sdsr = intent.get('sdsr', {})

    entry = {
        'status': 'DRAFT',
        'spec_path': f"design/l2_1/intents/AURORA_L2_INTENT_{panel_id}.yaml",
        'added_at': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'reviewed_by': None,
        'domain': metadata.get('domain'),
        'subdomain': metadata.get('subdomain'),
        'topic': metadata.get('topic'),
        'order': metadata.get('order'),
        'capability': capability.get('id'),
        'sdsr_verified': sdsr.get('verified', False),
    }

    return entry


def sync_panel(panel_id: str, registry: Dict, force: bool = False) -> str:
    """
    Sync a single panel to registry.
    Returns: 'created', 'updated', 'skipped', or 'error'
    """
    intent = load_intent_yaml(panel_id)
    if not intent:
        return 'error'

    if panel_id in registry and not force:
        # Update only if sdsr_verified changed
        sdsr_verified = intent.get('sdsr', {}).get('verified', False)
        if registry[panel_id].get('sdsr_verified') != sdsr_verified:
            registry[panel_id]['sdsr_verified'] = sdsr_verified
            return 'updated'
        return 'skipped'

    # Create new entry
    entry = create_registry_entry(panel_id, intent)
    registry[panel_id] = entry
    return 'created'


def approve_panel(panel_id: str, registry: Dict, reviewer: str = "human") -> bool:
    """
    Approve a panel (DRAFT → APPROVED).

    CRITICAL: Freezes intent hash at approval time.
    This hash is used to detect post-approval modifications (intent rot).
    """
    if panel_id not in registry:
        return False

    if registry[panel_id].get('status') != 'DRAFT':
        print(f"Warning: {panel_id} is not in DRAFT status", file=sys.stderr)

    # Compute and freeze intent hash
    frozen_hash = compute_intent_hash(panel_id)
    if not frozen_hash:
        print(f"Warning: Could not compute hash for {panel_id}", file=sys.stderr)

    registry[panel_id]['status'] = 'APPROVED'
    registry[panel_id]['reviewed_by'] = reviewer
    registry[panel_id]['approved_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    registry[panel_id]['frozen_hash'] = frozen_hash  # CRITICAL: Freeze point

    return True


def get_all_intent_files() -> List[str]:
    """Get all panel IDs from intent files."""
    if not INTENTS_DIR.exists():
        return []

    panel_ids = []
    for f in INTENTS_DIR.glob("*.yaml"):
        if not f.name.startswith('_') and not f.name.startswith('README'):
            # Handle both new naming (AURORA_L2_INTENT_*.yaml) and legacy (*.yaml)
            stem = f.stem
            if stem.startswith('AURORA_L2_INTENT_'):
                panel_id = stem[len('AURORA_L2_INTENT_'):]
            else:
                panel_id = stem
            if panel_id not in panel_ids:
                panel_ids.append(panel_id)
    return panel_ids


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 Intent Registry Sync - Syncs intent YAMLs to registry"
    )
    parser.add_argument("--panel", help="Panel ID to sync")
    parser.add_argument("--all", action="store_true", help="Sync all intent files")
    parser.add_argument("--approve", help="Approve a panel (DRAFT → APPROVED)")
    parser.add_argument("--reviewer", default="human", help="Reviewer name for approval")
    parser.add_argument("--force", action="store_true", help="Force re-sync even if exists")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change")
    parser.add_argument("--list", action="store_true", help="List all registry entries")
    parser.add_argument("--verify", action="store_true", help="Verify intent hashes (detect staleness)")
    args = parser.parse_args()

    registry = load_intent_registry()

    # Verify intent hashes (staleness check)
    if args.verify:
        print("AURORA L2 Intent Staleness Check")
        print("=" * 70)
        stale_count = 0
        checked = 0
        for panel_id, entry in sorted(registry.items()):
            frozen_hash = entry.get('frozen_hash')
            if not frozen_hash:
                continue  # No frozen hash to verify

            checked += 1
            current_hash = compute_intent_hash(panel_id)

            if current_hash != frozen_hash:
                print(f"  ⚠️  STALE: {panel_id}")
                print(f"       Frozen:  {frozen_hash[:16]}...")
                print(f"       Current: {current_hash[:16]}..." if current_hash else "       Current: MISSING")
                stale_count += 1
            else:
                print(f"  ✅ OK: {panel_id}")

        print()
        print(f"Verified: {checked} intents")
        if stale_count > 0:
            print(f"⚠️  STALE: {stale_count} intents modified after APPROVED")
            print()
            print("Action required:")
            print("  1. Review changes to stale intents")
            print("  2. If intentional: re-approve with --approve <panel_id>")
            return 1
        else:
            print("✅ All intents match frozen hashes")
        return 0

    if args.list:
        print("AURORA L2 Intent Registry")
        print("=" * 70)
        for panel_id, entry in sorted(registry.items()):
            status = entry.get('status', 'UNKNOWN')
            sdsr = "✓" if entry.get('sdsr_verified') else "✗"
            hash_status = "🔒" if entry.get('frozen_hash') else "  "
            print(f"  {hash_status} {panel_id:28} {status:10} SDSR:{sdsr}")
        print()
        print(f"Total: {len(registry)} entries")
        print("🔒 = frozen hash present (APPROVED state locked)")
        return 0

    if args.approve:
        if args.approve not in registry:
            # Try to sync first
            result = sync_panel(args.approve, registry)
            if result == 'error':
                print(f"ERROR: Intent YAML not found for {args.approve}", file=sys.stderr)
                return 1

        if args.dry_run:
            print(f"Would approve: {args.approve}")
            return 0

        if approve_panel(args.approve, registry, args.reviewer):
            save_intent_registry(registry)
            print(f"✅ Approved: {args.approve}")
            print(f"   Status: DRAFT → APPROVED")
            print(f"   Reviewer: {args.reviewer}")
            return 0
        else:
            print(f"ERROR: Failed to approve {args.approve}", file=sys.stderr)
            return 1

    panels_to_sync = []
    if args.all:
        panels_to_sync = get_all_intent_files()
    elif args.panel:
        panels_to_sync = [args.panel]
    else:
        parser.print_help()
        return 1

    results = {'created': [], 'updated': [], 'skipped': [], 'error': []}

    for panel_id in panels_to_sync:
        result = sync_panel(panel_id, registry, force=args.force)
        results[result].append(panel_id)

    if args.dry_run:
        print("DRY RUN - Would make these changes:")
        for action, panels in results.items():
            if panels:
                print(f"  {action}: {', '.join(panels)}")
        return 0

    # Save changes
    if results['created'] or results['updated']:
        save_intent_registry(registry)

    # Report
    print("Intent Registry Sync Complete")
    print("=" * 70)
    if results['created']:
        print(f"  Created: {', '.join(results['created'])}")
    if results['updated']:
        print(f"  Updated: {', '.join(results['updated'])}")
    if results['skipped']:
        print(f"  Skipped: {', '.join(results['skipped'])}")
    if results['error']:
        print(f"  Errors:  {', '.join(results['error'])}")

    print()
    print(f"Registry: {INTENT_REGISTRY.relative_to(REPO_ROOT)}")

    if results['created']:
        print()
        print("Next steps for new entries:")
        print("  1. Review the intent YAML files")
        print("  2. Approve: python aurora_intent_registry_sync.py --approve <panel_id>")

    return 1 if results['error'] else 0


if __name__ == "__main__":
    sys.exit(main())
