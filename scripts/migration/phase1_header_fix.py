#!/usr/bin/env python3
"""
Phase 1: HEADER_FIX_ONLY Execution

Updates file headers to match their detected dominant layer.
No code changes - only header metadata updates.

Usage:
  python scripts/migration/phase1_header_fix.py --dry-run
  python scripts/migration/phase1_header_fix.py --execute
"""
import argparse
import json
import re
from pathlib import Path
from typing import Optional


# Layer names for headers
LAYER_NAMES = {
    "L2": "API",
    "L3": "Adapter",
    "L4": "Engine",
    "L5": "Worker",
    "L6": "Driver",
}


def get_header_fix_files(report_path: Path) -> list[dict]:
    """Get files that need HEADER_FIX_ONLY."""
    with open(report_path) as f:
        report = json.load(f)

    return [
        f for f in report["files"]
        if f.get("refactor_action") == "HEADER_FIX_ONLY"
    ]


def extract_current_header(content: str) -> dict:
    """Extract current header information from file content."""
    header = {
        "layer": None,
        "audience": None,
        "role": None,
        "header_end": 0,
    }

    lines = content.split("\n")
    for i, line in enumerate(lines[:50]):  # Check first 50 lines
        if match := re.match(r"^#\s*Layer:\s*L(\d)\s*[-—]\s*(.+)", line, re.IGNORECASE):
            header["layer"] = f"L{match.group(1)}"
            header["layer_name"] = match.group(2).strip()
        elif match := re.match(r"^#\s*AUDIENCE:\s*(\w+)", line, re.IGNORECASE):
            header["audience"] = match.group(1).upper()
        elif match := re.match(r"^#\s*Role:\s*(.+)", line, re.IGNORECASE):
            header["role"] = match.group(1).strip()

        # Track where header ends (first non-comment, non-empty line)
        if line.strip() and not line.strip().startswith("#"):
            header["header_end"] = i
            break

    return header


def generate_new_header(
    current_header: dict,
    detected_layer: str,
    file_path: str,
) -> str:
    """Generate new header with corrected layer."""
    layer_name = LAYER_NAMES.get(detected_layer, "Unknown")

    # Keep existing audience and role, just fix the layer
    audience = current_header.get("audience") or "CUSTOMER"
    role = current_header.get("role") or f"See file: {Path(file_path).name}"

    return f"""# Layer: {detected_layer} — {layer_name}
# AUDIENCE: {audience}
# Role: {role}
"""


def fix_file_header(file_path: Path, detected_layer: str, dry_run: bool = True) -> dict:
    """Fix header in a single file."""
    result = {
        "file": str(file_path),
        "action": "HEADER_FIX_ONLY",
        "status": "pending",
        "old_layer": None,
        "new_layer": detected_layer,
    }

    try:
        content = file_path.read_text()
        current_header = extract_current_header(content)
        result["old_layer"] = current_header.get("layer")

        # Generate new header
        new_header = generate_new_header(current_header, detected_layer, str(file_path))

        # Find where to insert/replace header
        lines = content.split("\n")
        header_end = current_header["header_end"]

        # Check if file already has a layer header
        has_layer_header = any(
            re.match(r"^#\s*Layer:", line, re.IGNORECASE)
            for line in lines[:header_end]
        )

        if has_layer_header:
            # Replace existing header lines
            new_lines = []
            skip_old_header = True
            for line in lines:
                if skip_old_header:
                    if re.match(r"^#\s*(Layer:|AUDIENCE:|Role:)", line, re.IGNORECASE):
                        continue
                    elif line.strip() and not line.strip().startswith("#"):
                        skip_old_header = False
                        new_lines.insert(0, new_header.strip())
                        new_lines.append("")
                        new_lines.append(line)
                    else:
                        # Keep other comments
                        if not re.match(r"^#\s*(Layer:|AUDIENCE:|Role:)", line, re.IGNORECASE):
                            new_lines.append(line)
                else:
                    new_lines.append(line)
            new_content = "\n".join(new_lines)
        else:
            # Prepend new header
            new_content = new_header + "\n" + content

        if dry_run:
            result["status"] = "would_fix"
            result["preview"] = new_header.strip()
        else:
            file_path.write_text(new_content)
            result["status"] = "fixed"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description="Phase 1: Header fix execution")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the header fixes"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/architecture/migration/layer_fit_report.json"),
        help="Path to layer fit report"
    )
    parser.add_argument(
        "--hoc-root",
        type=Path,
        default=Path("backend/app/houseofcards"),
        help="Root of HOC directory"
    )
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("Error: Must specify --dry-run or --execute")
        return 1

    print("=" * 60)
    print("PHASE 1: HEADER_FIX_ONLY EXECUTION")
    print("=" * 60)

    # Get files to fix
    files = get_header_fix_files(args.report)
    print(f"\nFiles to process: {len(files)}")

    if not files:
        print("No files need header fixes!")
        return 0

    # Process each file
    results = []
    for f in files:
        rel_path = f["relative_path"]
        detected = f["classification"].get("dominant_layer")

        if not detected:
            print(f"  ⚠️  Skip {rel_path} (no dominant layer detected)")
            continue

        # Convert relative path to absolute
        # rel_path is like "app/houseofcards/..."
        file_path = Path("backend") / rel_path

        if not file_path.exists():
            print(f"  ❌ Not found: {file_path}")
            continue

        result = fix_file_header(file_path, detected, dry_run=args.dry_run)
        results.append(result)

        status_icon = "✅" if result["status"] in ["fixed", "would_fix"] else "❌"
        print(f"  {status_icon} {rel_path}: {result['old_layer']} → {result['new_layer']}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    fixed = sum(1 for r in results if r["status"] in ["fixed", "would_fix"])
    errors = sum(1 for r in results if r["status"] == "error")

    print(f"  Total processed: {len(results)}")
    print(f"  {'Would fix' if args.dry_run else 'Fixed'}: {fixed}")
    print(f"  Errors: {errors}")

    if args.dry_run:
        print("\n⚠️  DRY RUN - No changes made. Use --execute to apply.")
    else:
        print("\n✅ Header fixes applied!")

    return 0


if __name__ == "__main__":
    exit(main())
