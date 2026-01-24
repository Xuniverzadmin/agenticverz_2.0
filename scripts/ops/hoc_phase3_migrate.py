#!/usr/bin/env python3
"""
HOC Phase 3 Migration Script

Handles:
1. Package rename: hoc → hoc
2. Audience renames: customer → cus, founder → fdr, internal → int
3. Layer-prefixed folder restructure per domain
4. Import updates across entire codebase

Usage:
    # Preview package + audience rename
    python scripts/ops/hoc_phase3_migrate.py --rename-all --dry-run

    # Execute package + audience rename
    python scripts/ops/hoc_phase3_migrate.py --rename-all

    # Preview domain migration
    python scripts/ops/hoc_phase3_migrate.py --domain activity --dry-run

    # Migrate single domain
    python scripts/ops/hoc_phase3_migrate.py --domain activity

    # Migrate all domains
    python scripts/ops/hoc_phase3_migrate.py --all

    # Rollback last migration
    python scripts/ops/hoc_phase3_migrate.py --rollback

Version: 1.0.0
Date: 2026-01-24
Reference: docs/architecture/hoc/migration/PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ==============================================================================
# CONFIGURATION
# ==============================================================================

REPO_ROOT = Path(__file__).parent.parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
HOC_CURRENT = BACKEND_ROOT / "app" / "hoc"
HOC_NEW = BACKEND_ROOT / "app" / "hoc"
BACKUP_DIR = REPO_ROOT / "backups" / "hoc_phase3"

# Package and audience renames
PACKAGE_RENAMES = {
    "hoc": "hoc",
}

AUDIENCE_RENAMES = {
    "customer": "cus",
    "founder": "fdr",
    "internal": "int",
}

# Standard domains (customer audience)
STANDARD_DOMAINS = [
    "overview",
    "api_keys",
    "account",
    "activity",
    "analytics",
    "incidents",
    "logs",
    "integrations",
    "policies",
]

# General domain has special structure
GENERAL_DOMAIN = "general"

# Layer-prefix mappings for standard domains
# NOTE: facades are NOT auto-merged - they require manual review
STANDARD_DOMAIN_RENAMES = {
    "adapters": "L3_adapters",
    "bridges": "L3_adapters",  # Merge into L3_adapters
    "engines": "L5_engines",
    "schemas": "L5_schemas",
    "drivers": "L6_drivers",
}

# Folders that require manual review before migration
MANUAL_REVIEW_FOLDERS = {
    "facades": "REVIEW_facades",  # Domain facades need manual classification
}

# General domain special mappings
# NOTE: facades are NOT auto-merged - they require manual review
GENERAL_DOMAIN_RENAMES = {
    "runtime": "L4_runtime",
    "controls": "L5_controls",
    "lifecycle": "L5_lifecycle",
    "workflow": "L5_workflow",
    "mcp": "L3_mcp",
    "ui": "L5_ui",
    "utils": "L5_utils",
    "schemas": "L5_schemas",
    "drivers": "L6_drivers",
    "engines": "L5_engines",
    # facades excluded - requires manual review
}

# Special case folders (domain-specific)
SPECIAL_FOLDERS = {
    "controls": "L5_controls",
    "vault": "L5_vault",
    "notifications": "L5_notifications",
    "support": "L5_support",
}

# File extensions to scan for imports
CODE_EXTENSIONS = {".py", ".pyi"}
DOC_EXTENSIONS = {".md", ".yaml", ".yml", ".json"}
ALL_EXTENSIONS = CODE_EXTENSIONS | DOC_EXTENSIONS

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def log(msg: str, level: str = "INFO"):
    """Print log message with timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌", "OK": "✅", "DRY": "🔍"}.get(level, "")
    print(f"[{ts}] {prefix} {msg}")


def create_backup(source: Path, backup_name: str) -> Path:
    """Create timestamped backup of source directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{backup_name}_{timestamp}"
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    if source.exists():
        shutil.copytree(source, backup_path)
        log(f"Backup created: {backup_path}", "OK")
    else:
        log(f"Source does not exist, skipping backup: {source}", "WARN")

    return backup_path


def find_files(root: Path, extensions: Set[str]) -> List[Path]:
    """Find all files with given extensions under root."""
    files = []
    for ext in extensions:
        files.extend(root.rglob(f"*{ext}"))
    return sorted(files)


def read_file(path: Path) -> str:
    """Read file contents, handling encoding errors."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return ""


def write_file(path: Path, content: str):
    """Write content to file."""
    path.write_text(content, encoding="utf-8")


# ==============================================================================
# IMPORT PATTERN REPLACEMENT
# ==============================================================================

def build_import_patterns() -> List[Tuple[re.Pattern, str]]:
    """Build regex patterns for import replacement."""
    patterns = []

    # Package rename: hoc → hoc
    patterns.append((
        re.compile(r'\bhouseofcards\b'),
        'hoc'
    ))

    # Audience renames in import paths (after package rename)
    # These patterns work on already-renamed 'hoc.' imports
    for old, new in AUDIENCE_RENAMES.items():
        # Match .cus. → .cus. etc
        patterns.append((
            re.compile(rf'\.{old}\.'),
            f'.{new}.'
        ))
        # Match /cus/ → /cus/ in paths
        patterns.append((
            re.compile(rf'/{old}/'),
            f'/{new}/'
        ))

    return patterns


def build_layer_patterns(domain: str, renamed: bool = False) -> List[Tuple[re.Pattern, str]]:
    """Build regex patterns for layer-prefix folder renames.

    Args:
        domain: The domain name (e.g., 'activity', 'general')
        renamed: Whether package rename has been done (affects which patterns to use)
    """
    patterns = []

    mappings = GENERAL_DOMAIN_RENAMES if domain == GENERAL_DOMAIN else STANDARD_DOMAIN_RENAMES

    for old_folder, new_folder in mappings.items():
        # Import pattern: .domain.engines. → .domain.L5_engines.
        patterns.append((
            re.compile(rf'\.{domain}\.{old_folder}\.'),
            f'.{domain}.{new_folder}.'
        ))
        patterns.append((
            re.compile(rf'\.{domain}\.{old_folder}\b'),
            f'.{domain}.{new_folder}'
        ))
        # Path pattern: /domain/engines/ → /domain/L5_engines/
        patterns.append((
            re.compile(rf'/{domain}/{old_folder}/'),
            f'/{domain}/{new_folder}/'
        ))
        patterns.append((
            re.compile(rf'/{domain}/{old_folder}\b'),
            f'/{domain}/{new_folder}'
        ))

    return patterns


def apply_patterns(content: str, patterns: List[Tuple[re.Pattern, str]]) -> Tuple[str, int]:
    """Apply regex patterns to content, return (new_content, change_count)."""
    total_changes = 0
    for pattern, replacement in patterns:
        content, count = pattern.subn(replacement, content)
        total_changes += count
    return content, total_changes


# ==============================================================================
# PHASE 3 STEP 0: PACKAGE & AUDIENCE RENAME
# ==============================================================================

def rename_all(dry_run: bool = True) -> Dict:
    """
    Step 0: Rename package and audiences.

    1. Rename folder: backend/app/hoc/ → backend/app/hoc/
    2. Rename audience folders: hoc/cus/ → hoc/cus/, etc.
    3. Update all imports across codebase
    """
    report = {
        "operation": "rename_all",
        "dry_run": dry_run,
        "timestamp": datetime.now().isoformat(),
        "folder_renames": [],
        "import_updates": [],
        "files_scanned": 0,
        "files_modified": 0,
        "total_replacements": 0,
        "errors": [],
    }

    log(f"{'[DRY RUN] ' if dry_run else ''}Starting package & audience rename...", "DRY" if dry_run else "INFO")

    # Step 1: Create backup
    if not dry_run:
        if HOC_CURRENT.exists():
            backup_path = create_backup(HOC_CURRENT, "hoc")
            report["backup_path"] = str(backup_path)
        else:
            report["errors"].append(f"Source folder does not exist: {HOC_CURRENT}")
            return report

    # Step 2: Rename main package folder
    if HOC_CURRENT.exists():
        log(f"Rename: {HOC_CURRENT} → {HOC_NEW}", "DRY" if dry_run else "INFO")
        report["folder_renames"].append({
            "from": str(HOC_CURRENT),
            "to": str(HOC_NEW),
        })
        if not dry_run:
            shutil.move(str(HOC_CURRENT), str(HOC_NEW))
            log(f"Package folder renamed", "OK")

    # Step 3: Rename audience folders
    hoc_base = HOC_NEW if not dry_run else HOC_CURRENT
    for old_audience, new_audience in AUDIENCE_RENAMES.items():
        old_path = hoc_base / old_audience
        new_path = hoc_base / new_audience

        if old_path.exists():
            log(f"Rename: {old_path.name}/ → {new_path.name}/", "DRY" if dry_run else "INFO")
            report["folder_renames"].append({
                "from": str(old_path),
                "to": str(new_path),
            })
            if not dry_run:
                shutil.move(str(old_path), str(new_path))

    # Also rename in API folder
    api_base = hoc_base / "api"
    if api_base.exists():
        for old_audience, new_audience in AUDIENCE_RENAMES.items():
            old_path = api_base / old_audience
            new_path = api_base / new_audience

            if old_path.exists():
                log(f"Rename: api/{old_path.name}/ → api/{new_path.name}/", "DRY" if dry_run else "INFO")
                report["folder_renames"].append({
                    "from": str(old_path),
                    "to": str(new_path),
                })
                if not dry_run:
                    shutil.move(str(old_path), str(new_path))

        # Also check facades folder
        facades_base = api_base / "facades"
        if facades_base.exists():
            for old_audience, new_audience in AUDIENCE_RENAMES.items():
                old_path = facades_base / old_audience
                new_path = facades_base / new_audience

                if old_path.exists():
                    log(f"Rename: api/facades/{old_path.name}/ → api/facades/{new_path.name}/", "DRY" if dry_run else "INFO")
                    report["folder_renames"].append({
                        "from": str(old_path),
                        "to": str(new_path),
                    })
                    if not dry_run:
                        shutil.move(str(old_path), str(new_path))

    # Step 4: Update imports across entire codebase
    patterns = build_import_patterns()

    # Scan all Python files in repo
    all_files = find_files(REPO_ROOT, CODE_EXTENSIONS)
    # Also scan markdown and yaml docs
    all_files.extend(find_files(REPO_ROOT / "docs", DOC_EXTENSIONS))

    # Exclude backup directories
    all_files = [f for f in all_files if "backups" not in str(f) and ".git" not in str(f)]

    report["files_scanned"] = len(all_files)
    log(f"Scanning {len(all_files)} files for import updates...", "INFO")

    for filepath in all_files:
        try:
            content = read_file(filepath)
            if not content:
                continue

            new_content, changes = apply_patterns(content, patterns)

            if changes > 0:
                report["import_updates"].append({
                    "file": str(filepath.relative_to(REPO_ROOT)),
                    "changes": changes,
                })
                report["total_replacements"] += changes
                report["files_modified"] += 1

                if not dry_run:
                    write_file(filepath, new_content)

        except Exception as e:
            report["errors"].append(f"Error processing {filepath}: {e}")

    log(f"{'[DRY RUN] ' if dry_run else ''}Import updates: {report['files_modified']} files, {report['total_replacements']} replacements",
        "DRY" if dry_run else "OK")

    return report


# ==============================================================================
# PHASE 3 STEP 1+: DOMAIN LAYER-PREFIX MIGRATION
# ==============================================================================

def get_domain_path(domain: str, audience_old: str = "customer", audience_new: str = "cus") -> Path:
    """Get the path to a domain folder (handles pre/post rename)."""
    # Check if rename has been done
    if HOC_NEW.exists():
        # Post-rename: use new paths
        return HOC_NEW / audience_new / domain
    elif HOC_CURRENT.exists():
        # Pre-rename: use old paths
        return HOC_CURRENT / audience_old / domain
    else:
        # Neither exists - return new path (will fail with good error)
        return HOC_NEW / audience_new / domain


def is_rename_done() -> bool:
    """Check if package rename has been done."""
    return HOC_NEW.exists() and not HOC_CURRENT.exists()


def migrate_domain(domain: str, dry_run: bool = True) -> Dict:
    """
    Migrate a single domain to layer-prefixed structure.

    1. Create new layer-prefixed folders
    2. Move files from old folders to new folders
    3. Update __init__.py exports
    4. Update imports referencing this domain
    """
    report = {
        "operation": "migrate_domain",
        "domain": domain,
        "dry_run": dry_run,
        "timestamp": datetime.now().isoformat(),
        "folder_renames": [],
        "files_moved": [],
        "init_updates": [],
        "import_updates": [],
        "manual_review_required": [],  # Folders that need manual classification
        "files_scanned": 0,
        "files_modified": 0,
        "total_replacements": 0,
        "errors": [],
    }

    log(f"{'[DRY RUN] ' if dry_run else ''}Migrating domain: {domain}", "DRY" if dry_run else "INFO")

    domain_path = get_domain_path(domain)
    if not domain_path.exists():
        report["errors"].append(f"Domain folder does not exist: {domain_path}")
        log(f"Domain folder not found: {domain_path}", "ERROR")
        return report

    # Step 1: Create backup
    if not dry_run:
        backup_path = create_backup(domain_path, f"domain_{domain}")
        report["backup_path"] = str(backup_path)

    # Step 2: Determine folder mappings
    mappings = GENERAL_DOMAIN_RENAMES if domain == GENERAL_DOMAIN else STANDARD_DOMAIN_RENAMES

    # Step 3: Rename/merge folders
    for old_folder, new_folder in mappings.items():
        old_path = domain_path / old_folder
        new_path = domain_path / new_folder

        if not old_path.exists():
            continue

        if new_path.exists() and old_path != new_path:
            # Merge into existing folder
            log(f"Merge: {old_folder}/ → {new_folder}/ (existing)", "DRY" if dry_run else "INFO")
            report["folder_renames"].append({
                "from": str(old_path.relative_to(REPO_ROOT)),
                "to": str(new_path.relative_to(REPO_ROOT)),
                "action": "merge",
            })

            if not dry_run:
                # Move all files from old to new
                for item in old_path.iterdir():
                    if item.name == "__init__.py":
                        # Merge __init__.py contents
                        continue
                    dest = new_path / item.name
                    if item.is_file():
                        shutil.move(str(item), str(dest))
                        report["files_moved"].append({
                            "from": str(item.relative_to(REPO_ROOT)),
                            "to": str(dest.relative_to(REPO_ROOT)),
                        })
                    elif item.is_dir():
                        if dest.exists():
                            shutil.rmtree(str(dest))
                        shutil.move(str(item), str(dest))

                # Remove empty old folder
                if old_path.exists() and not any(old_path.iterdir()):
                    old_path.rmdir()

        elif old_folder != new_folder:
            # Rename folder
            log(f"Rename: {old_folder}/ → {new_folder}/", "DRY" if dry_run else "INFO")
            report["folder_renames"].append({
                "from": str(old_path.relative_to(REPO_ROOT)),
                "to": str(new_path.relative_to(REPO_ROOT)),
                "action": "rename",
            })

            if not dry_run:
                shutil.move(str(old_path), str(new_path))

    # Step 4: Handle special folders
    for old_folder, new_folder in SPECIAL_FOLDERS.items():
        old_path = domain_path / old_folder
        new_path = domain_path / new_folder

        if old_path.exists() and old_folder != new_folder:
            log(f"Rename special: {old_folder}/ → {new_folder}/", "DRY" if dry_run else "INFO")
            report["folder_renames"].append({
                "from": str(old_path.relative_to(REPO_ROOT)),
                "to": str(new_path.relative_to(REPO_ROOT)),
                "action": "rename_special",
            })

            if not dry_run:
                if new_path.exists():
                    # Merge
                    for item in old_path.iterdir():
                        dest = new_path / item.name
                        shutil.move(str(item), str(dest))
                    old_path.rmdir()
                else:
                    shutil.move(str(old_path), str(new_path))

    # Step 5: Flag folders requiring manual review (facades)
    for old_folder, review_name in MANUAL_REVIEW_FOLDERS.items():
        old_path = domain_path / old_folder

        if old_path.exists():
            # List files in the folder for review
            files_in_folder = [f.name for f in old_path.iterdir() if f.is_file()]
            log(f"⚠️  MANUAL REVIEW: {old_folder}/ has {len(files_in_folder)} files requiring classification", "WARN")

            report["manual_review_required"].append({
                "folder": str(old_path.relative_to(REPO_ROOT)),
                "files": files_in_folder,
                "action_required": "Classify each file as L2.1 (API facade), L3 (adapter), or L5 (engine)",
                "guidance": [
                    "L2.1: If it groups/organizes API routers → move to hoc/api/{audience}/{domain}/",
                    "L3: If it translates between API and domain → rename to L3_adapters/",
                    "L5: If it contains business logic → merge into L5_engines/",
                ],
            })

    # Step 6: Update imports across codebase
    renamed = is_rename_done()
    patterns = build_layer_patterns(domain, renamed=renamed)

    all_files = find_files(REPO_ROOT, CODE_EXTENSIONS)
    all_files.extend(find_files(REPO_ROOT / "docs", DOC_EXTENSIONS))
    all_files = [f for f in all_files if "backups" not in str(f) and ".git" not in str(f)]

    report["files_scanned"] = len(all_files)

    for filepath in all_files:
        try:
            content = read_file(filepath)
            if not content:
                continue

            new_content, changes = apply_patterns(content, patterns)

            if changes > 0:
                report["import_updates"].append({
                    "file": str(filepath.relative_to(REPO_ROOT)),
                    "changes": changes,
                })
                report["total_replacements"] += changes
                report["files_modified"] += 1

                if not dry_run:
                    write_file(filepath, new_content)

        except Exception as e:
            report["errors"].append(f"Error processing {filepath}: {e}")

    log(f"{'[DRY RUN] ' if dry_run else ''}Domain {domain}: {len(report['folder_renames'])} folders, {report['files_modified']} files updated",
        "DRY" if dry_run else "OK")

    return report


def migrate_all_domains(dry_run: bool = True) -> Dict:
    """Migrate all domains in order."""
    report = {
        "operation": "migrate_all_domains",
        "dry_run": dry_run,
        "timestamp": datetime.now().isoformat(),
        "domains": [],
        "errors": [],
    }

    # Migration order from plan
    migration_order = STANDARD_DOMAINS + [GENERAL_DOMAIN]

    for domain in migration_order:
        domain_report = migrate_domain(domain, dry_run)
        report["domains"].append(domain_report)

        if domain_report["errors"]:
            report["errors"].extend(domain_report["errors"])

    return report


# ==============================================================================
# ROLLBACK
# ==============================================================================

def rollback_last() -> Dict:
    """Rollback to the last backup."""
    report = {
        "operation": "rollback",
        "timestamp": datetime.now().isoformat(),
        "restored_from": None,
        "errors": [],
    }

    if not BACKUP_DIR.exists():
        report["errors"].append("No backup directory found")
        log("No backup directory found", "ERROR")
        return report

    # Find most recent backup
    backups = sorted(BACKUP_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)

    if not backups:
        report["errors"].append("No backups found")
        log("No backups found", "ERROR")
        return report

    latest_backup = backups[0]
    log(f"Found backup: {latest_backup.name}", "INFO")

    # Determine restore target
    if "hoc" in latest_backup.name:
        # Package rename backup - restore to hoc
        target = HOC_CURRENT
        # First remove hoc if exists
        if HOC_NEW.exists():
            shutil.rmtree(str(HOC_NEW))
    else:
        # Domain backup
        domain = latest_backup.name.split("_")[1]
        target = get_domain_path(domain)
        if target.exists():
            shutil.rmtree(str(target))

    # Restore
    shutil.copytree(str(latest_backup), str(target))
    report["restored_from"] = str(latest_backup)

    log(f"Restored from {latest_backup.name}", "OK")

    return report


# ==============================================================================
# REPORT GENERATION
# ==============================================================================

def generate_report(report: Dict, output_path: Optional[Path] = None):
    """Generate and optionally save migration report."""

    print("\n" + "=" * 60)
    print("MIGRATION REPORT")
    print("=" * 60)

    print(f"\nOperation: {report.get('operation', 'unknown')}")
    print(f"Timestamp: {report.get('timestamp', 'unknown')}")
    print(f"Dry Run: {report.get('dry_run', False)}")

    if "folder_renames" in report:
        print(f"\nFolder Operations: {len(report['folder_renames'])}")
        for op in report["folder_renames"][:10]:
            print(f"  {op.get('action', 'rename')}: {op['from']} → {op['to']}")
        if len(report["folder_renames"]) > 10:
            print(f"  ... and {len(report['folder_renames']) - 10} more")

    if "files_modified" in report:
        print(f"\nImport Updates:")
        print(f"  Files scanned: {report.get('files_scanned', 0)}")
        print(f"  Files modified: {report['files_modified']}")
        print(f"  Total replacements: {report.get('total_replacements', 0)}")

    if "domains" in report:
        print(f"\nDomains Migrated: {len(report['domains'])}")
        for domain_report in report["domains"]:
            domain = domain_report.get("domain", "unknown")
            folders = len(domain_report.get("folder_renames", []))
            files = domain_report.get("files_modified", 0)
            review = len(domain_report.get("manual_review_required", []))
            status = f" ⚠️  {review} folders need review" if review > 0 else ""
            print(f"  {domain}: {folders} folders, {files} file updates{status}")

    # Manual review section
    manual_reviews = report.get("manual_review_required", [])
    if manual_reviews:
        print(f"\n⚠️  MANUAL REVIEW REQUIRED: {len(manual_reviews)} folder(s)")
        print("=" * 40)
        for review in manual_reviews:
            print(f"\n  Folder: {review['folder']}")
            print(f"  Files: {len(review['files'])}")
            for f in review['files'][:5]:
                print(f"    - {f}")
            if len(review['files']) > 5:
                print(f"    ... and {len(review['files']) - 5} more")
            print(f"  Action: {review['action_required']}")
            print("  Guidance:")
            for g in review['guidance']:
                print(f"    • {g}")

    # Check domains for manual reviews too
    if "domains" in report:
        for domain_report in report["domains"]:
            domain_reviews = domain_report.get("manual_review_required", [])
            if domain_reviews:
                print(f"\n⚠️  {domain_report['domain']} MANUAL REVIEW:")
                for review in domain_reviews:
                    print(f"  Folder: {review['folder']}")
                    print(f"  Files ({len(review['files'])}): {', '.join(review['files'][:3])}{'...' if len(review['files']) > 3 else ''}")

    if report.get("errors"):
        print(f"\nErrors: {len(report['errors'])}")
        for error in report["errors"][:5]:
            print(f"  ❌ {error}")
        if len(report["errors"]) > 5:
            print(f"  ... and {len(report['errors']) - 5} more")
    else:
        print("\nErrors: None")

    print("\n" + "=" * 60)

    # Save to file
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2))
        log(f"Report saved: {output_path}", "OK")

    return report


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="HOC Phase 3 Migration Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview package rename
  %(prog)s --rename-all --dry-run

  # Execute package rename
  %(prog)s --rename-all

  # Preview domain migration
  %(prog)s --domain activity --dry-run

  # Migrate all domains
  %(prog)s --all

  # Rollback
  %(prog)s --rollback
        """
    )

    parser.add_argument("--rename-all", action="store_true",
                        help="Rename package (hoc→hoc) and audiences (customer→cus, etc)")
    parser.add_argument("--domain", type=str,
                        help="Migrate specific domain to layer-prefixed structure")
    parser.add_argument("--all", action="store_true",
                        help="Migrate all domains")
    parser.add_argument("--rollback", action="store_true",
                        help="Rollback to last backup")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without executing")
    parser.add_argument("--report", type=str,
                        help="Save report to JSON file")

    args = parser.parse_args()

    # Validate arguments
    if not any([args.rename_all, args.domain, args.all, args.rollback]):
        parser.print_help()
        sys.exit(1)

    report = None

    if args.rollback:
        if args.dry_run:
            log("Rollback does not support dry-run mode", "WARN")
        report = rollback_last()

    elif args.rename_all:
        report = rename_all(dry_run=args.dry_run)

    elif args.domain:
        if args.domain not in STANDARD_DOMAINS and args.domain != GENERAL_DOMAIN:
            log(f"Unknown domain: {args.domain}", "ERROR")
            log(f"Valid domains: {', '.join(STANDARD_DOMAINS + [GENERAL_DOMAIN])}", "INFO")
            sys.exit(1)
        report = migrate_domain(args.domain, dry_run=args.dry_run)

    elif args.all:
        report = migrate_all_domains(dry_run=args.dry_run)

    if report:
        output_path = Path(args.report) if args.report else None
        generate_report(report, output_path)

        # Exit with error if there were errors
        if report.get("errors"):
            sys.exit(1)


if __name__ == "__main__":
    main()
