#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Phase 1: RECLASSIFY_ONLY Execution
# artifact_class: CODE
"""
Phase 1: RECLASSIFY_ONLY Execution

Moves files to correct folders based on their detected dominant layer.
Updates headers after move.

Usage:
  python scripts/migration/phase1_reclassify.py --dry-run
  python scripts/migration/phase1_reclassify.py --execute
"""
import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Optional


# Layer to folder mapping
LAYER_FOLDERS = {
    "L2": "api",       # API files go to api/{audience}/{domain}/
    "L3": "facades",   # Adapters go to facades/
    "L4": "engines",   # Engines stay in engines/
    "L5": "workers",   # Workers go to workers/
    "L6": "drivers",   # Drivers/schemas go to drivers/ or schemas/
}

LAYER_NAMES = {
    "L2": "API",
    "L3": "Adapter",
    "L4": "Engine",
    "L5": "Worker",
    "L6": "Driver",
}


def get_reclassify_files(report_path: Path) -> list[dict]:
    """Get files that need RECLASSIFY_ONLY."""
    with open(report_path) as f:
        report = json.load(f)

    return [
        f for f in report["files"]
        if f.get("refactor_action") == "RECLASSIFY_ONLY"
    ]


def determine_target_folder(
    current_path: Path,
    detected_layer: str,
    declared_layer: Optional[str],
) -> Optional[Path]:
    """Determine the correct target folder for a file."""
    # Parse current path: backend/app/hoc/{audience}/{domain}/{layer_folder}/...
    parts = current_path.parts

    try:
        hoc_idx = parts.index("hoc")
    except ValueError:
        return None

    # Extract components
    if hoc_idx + 2 >= len(parts):
        return None

    audience = parts[hoc_idx + 1]
    domain = parts[hoc_idx + 2]
    current_folder = parts[hoc_idx + 3] if hoc_idx + 3 < len(parts) else None
    filename = parts[-1]

    # Determine target folder based on detected layer
    if detected_layer == "L6":
        # L6 files go to drivers/ (unless they're schemas)
        if "schema" in filename.lower() or "model" in filename.lower():
            target_folder = "schemas"
        else:
            target_folder = "drivers"
    elif detected_layer == "L3":
        target_folder = "facades"
    elif detected_layer == "L4":
        target_folder = "engines"
    elif detected_layer == "L5":
        target_folder = "workers"
    elif detected_layer == "L2":
        # L2 files should be in api/{audience}/{domain}/
        # This is a special case - they shouldn't be in engines/facades
        target_folder = None  # Handle separately
        return None  # Skip L2 reclassification for now
    else:
        return None

    # Build target path
    # Keep subdomain structure if it exists (e.g., policies/controls/engines -> policies/controls/drivers)
    if current_folder in ["engines", "facades", "drivers", "schemas", "workers"]:
        # Simple case: replace layer folder
        new_parts = list(parts[:hoc_idx + 3]) + [target_folder] + list(parts[hoc_idx + 4:])
    else:
        # Complex case: might have subdomain
        # Find the layer folder in the path
        layer_folders = {"engines", "facades", "drivers", "schemas", "workers"}
        layer_idx = None
        for i, p in enumerate(parts):
            if p in layer_folders:
                layer_idx = i
                break

        if layer_idx:
            new_parts = list(parts[:layer_idx]) + [target_folder] + list(parts[layer_idx + 1:])
        else:
            # No layer folder found, append target folder
            new_parts = list(parts[:hoc_idx + 3]) + [target_folder, filename]

    return Path(*new_parts)


def update_file_header(file_path: Path, new_layer: str) -> None:
    """Update file header with new layer declaration."""
    content = file_path.read_text()
    layer_name = LAYER_NAMES.get(new_layer, "Unknown")

    # Check if file has a layer header
    if re.search(r"^#\s*Layer:", content, re.MULTILINE | re.IGNORECASE):
        # Replace existing layer line
        new_content = re.sub(
            r"^#\s*Layer:\s*L\d\s*[-—]\s*.+$",
            f"# Layer: {new_layer} — {layer_name}",
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )
    else:
        # Prepend layer header
        new_content = f"# Layer: {new_layer} — {layer_name}\n" + content

    file_path.write_text(new_content)


def reclassify_file(
    file_path: Path,
    target_path: Path,
    new_layer: str,
    dry_run: bool = True
) -> dict:
    """Reclassify a single file by moving it to the correct folder."""
    result = {
        "source": str(file_path),
        "target": str(target_path),
        "new_layer": new_layer,
        "status": "pending",
    }

    try:
        if dry_run:
            result["status"] = "would_move"
        else:
            # Create target directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Move the file
            shutil.move(str(file_path), str(target_path))

            # Update header
            update_file_header(target_path, new_layer)

            result["status"] = "moved"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description="Phase 1: Reclassify execution")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the reclassification"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/architecture/migration/layer_fit_report.json"),
        help="Path to layer fit report"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of files to process (for testing)"
    )
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("Error: Must specify --dry-run or --execute")
        return 1

    print("=" * 60)
    print("PHASE 1: RECLASSIFY_ONLY EXECUTION")
    print("=" * 60)

    # Get files to reclassify
    files = get_reclassify_files(args.report)
    print(f"\nFiles to process: {len(files)}")

    if args.limit:
        files = files[:args.limit]
        print(f"Limited to: {len(files)}")

    if not files:
        print("No files need reclassification!")
        return 0

    # Group by target folder for better organization
    by_target_folder = {}
    skipped = []
    errors = []

    for f in files:
        rel_path = f["relative_path"]
        detected = f["classification"].get("dominant_layer")
        declared = f["classification"].get("declared_layer")

        if not detected:
            skipped.append((rel_path, "no dominant layer"))
            continue

        # Convert relative path to absolute
        file_path = Path("backend") / rel_path

        if not file_path.exists():
            errors.append((rel_path, "file not found"))
            continue

        # Determine target path
        target_path = determine_target_folder(file_path, detected, declared)

        if not target_path:
            skipped.append((rel_path, f"cannot determine target for {detected}"))
            continue

        if target_path == file_path:
            skipped.append((rel_path, "already in correct folder"))
            continue

        # Group by target folder
        target_folder = target_path.parent.name
        if target_folder not in by_target_folder:
            by_target_folder[target_folder] = []
        by_target_folder[target_folder].append({
            "source": file_path,
            "target": target_path,
            "layer": detected,
            "rel_path": rel_path,
        })

    # Process by target folder
    results = []
    for folder, items in sorted(by_target_folder.items()):
        print(f"\n→ {folder}/ ({len(items)} files)")
        for item in items:
            result = reclassify_file(
                item["source"],
                item["target"],
                item["layer"],
                dry_run=args.dry_run
            )
            results.append(result)

            status_icon = "✅" if result["status"] in ["moved", "would_move"] else "❌"
            source_name = item["source"].name
            print(f"    {status_icon} {source_name}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    moved = sum(1 for r in results if r["status"] in ["moved", "would_move"])
    error_count = sum(1 for r in results if r["status"] == "error")

    print(f"  Total in report: {len(files)}")
    print(f"  {'Would move' if args.dry_run else 'Moved'}: {moved}")
    print(f"  Skipped: {len(skipped)}")
    print(f"  Errors: {error_count + len(errors)}")

    if skipped:
        print(f"\n  Skipped files:")
        for path, reason in skipped[:10]:
            print(f"    - {Path(path).name}: {reason}")
        if len(skipped) > 10:
            print(f"    ... and {len(skipped) - 10} more")

    if args.dry_run:
        print("\n⚠️  DRY RUN - No changes made. Use --execute to apply.")
    else:
        print("\n✅ Reclassification complete!")
        print("   Remember to run layer_classifier.py to update reports.")

    return 0


if __name__ == "__main__":
    exit(main())
