#!/usr/bin/env python3
"""
Generate Migration Inventory CSV

This script inventories all files in backend/app/ and creates a CSV
for manual classification and migration planning.

Usage:
    python scripts/migration/generate_inventory.py \
        --output docs/architecture/migration/MIGRATION_INVENTORY.csv

Reference: docs/architecture/migration/PHASE1_MIGRATION_PLAN.md
"""

import argparse
import ast
import csv
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FileInfo:
    """Information extracted from a source file."""
    source_path: str
    file_header: str
    docstring: str
    class_names: set
    function_names: set


@dataclass
class InventoryRow:
    """A row in the migration inventory CSV."""
    s_no: int
    source_path: str
    audience: str
    domain: str
    layer: str
    target_path: str
    file_header: str
    docstring: str
    existing_hoc_path: str
    auto_status: str
    audit_status: str
    audit_notes: str
    action: str


# Exclusion patterns - files not added to inventory
EXCLUSIONS = [
    r"__pycache__",
    r"\.pyc$",
    r"/tests/",
    r"/test_",
    r"\.pytest",
]

# Model paths that STAY (L7)
MODEL_PATTERNS = [
    r"^app/models/",
    r"^app/customer/models/",
    r"^app/founder/models/",
    r"^app/internal/models/",
]

# Deprecated/duplicate patterns to mark for deletion
DEPRECATED_PATTERNS = [
    r"legacy_routes\.py$",
    r"^app/api/v1_",
]


def should_exclude(path: str) -> bool:
    """Check if file should be excluded from inventory."""
    for pattern in EXCLUSIONS:
        if re.search(pattern, path):
            return True
    return False


def is_empty_init(filepath: Path) -> bool:
    """Check if file is an empty __init__.py."""
    if filepath.name != "__init__.py":
        return False
    try:
        content = filepath.read_text().strip()
        # Empty or only comments/docstrings
        if not content:
            return True
        # Only has docstring or comments
        lines = [l.strip() for l in content.split("\n") if l.strip() and not l.strip().startswith("#")]
        if not lines:
            return True
        if len(lines) == 1 and (lines[0].startswith('"""') or lines[0].startswith("'''")):
            return True
    except Exception:
        pass
    return False


def is_model_file(path: str) -> bool:
    """Check if file is an L7 model file that stays in app/."""
    for pattern in MODEL_PATTERNS:
        if re.search(pattern, path):
            return True
    return False


def is_deprecated(path: str) -> bool:
    """Check if file is deprecated and should be deleted."""
    for pattern in DEPRECATED_PATTERNS:
        if re.search(pattern, path):
            return True
    return False


def extract_file_header(filepath: Path, num_lines: int = 15) -> str:
    """Extract first N lines of file as header."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= num_lines:
                    break
                lines.append(line.rstrip())
            return "\n".join(lines)
    except Exception as e:
        return f"# Error reading file: {e}"


def extract_docstring(filepath: Path) -> str:
    """Extract module docstring or first class docstring."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        tree = ast.parse(content)

        # Try module docstring first
        if (tree.body and isinstance(tree.body[0], ast.Expr) and
            isinstance(tree.body[0].value, (ast.Str, ast.Constant))):
            val = tree.body[0].value
            if isinstance(val, ast.Str):
                return val.s[:500]  # Truncate
            elif isinstance(val, ast.Constant) and isinstance(val.value, str):
                return val.value[:500]

        # Try first class docstring
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                if docstring:
                    return docstring[:500]

        # Try first function docstring
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                if docstring:
                    return docstring[:500]

        return ""
    except Exception:
        return ""


def extract_class_names(filepath: Path) -> set:
    """Extract all class names from file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        tree = ast.parse(content)
        return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    except Exception:
        return set()


def extract_function_names(filepath: Path) -> set:
    """Extract all top-level function names from file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        tree = ast.parse(content)
        return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    except Exception:
        return set()


def normalize_filename(filename: str) -> str:
    """Normalize filename for comparison (remove suffixes like _facade, _adapter)."""
    name = filename.replace(".py", "")
    # Remove common suffixes
    for suffix in ["_facade", "_adapter", "_engine", "_service", "_driver", "_worker"]:
        name = name.replace(suffix, "")
    return name


def find_hoc_files(hoc_root: Path) -> dict:
    """
    Index all HOC files by filename and class names.
    Returns dict: {filename: path, class_name: path}
    """
    index = {}

    if not hoc_root.exists():
        return index

    for filepath in hoc_root.rglob("*.py"):
        # Skip duplicate folder
        if "duplicate" in str(filepath):
            continue

        rel_path = str(filepath.relative_to(hoc_root.parent))
        filename = filepath.name

        # Index by filename
        index[filename] = rel_path

        # Index by normalized filename
        norm_name = normalize_filename(filename)
        if norm_name not in index:
            index[f"norm:{norm_name}"] = rel_path

        # Index by class names
        classes = extract_class_names(filepath)
        for cls in classes:
            if cls not in index:
                index[f"class:{cls}"] = rel_path

    return index


def find_hoc_equivalent(source_path: str, source_classes: set, hoc_index: dict) -> Optional[str]:
    """Find if source file has equivalent in HOC."""
    filename = os.path.basename(source_path)

    # Strategy 1: Exact filename match
    if filename in hoc_index:
        return hoc_index[filename]

    # Strategy 2: Normalized filename match
    norm_name = normalize_filename(filename)
    if f"norm:{norm_name}" in hoc_index:
        return hoc_index[f"norm:{norm_name}"]

    # Strategy 3: Class name match
    for cls in source_classes:
        if f"class:{cls}" in hoc_index:
            return hoc_index[f"class:{cls}"]

    return None


def scan_app_files(app_root: Path) -> list[FileInfo]:
    """Scan all Python files in app/ directory."""
    files = []

    for filepath in app_root.rglob("*.py"):
        rel_path = str(filepath.relative_to(app_root.parent))

        # Check exclusions
        if should_exclude(rel_path):
            continue

        # Skip empty __init__.py
        if is_empty_init(filepath):
            continue

        file_info = FileInfo(
            source_path=rel_path,
            file_header=extract_file_header(filepath),
            docstring=extract_docstring(filepath),
            class_names=extract_class_names(filepath),
            function_names=extract_function_names(filepath),
        )
        files.append(file_info)

    return files


def determine_auto_status(source_path: str, hoc_equivalent: Optional[str]) -> str:
    """Determine automatic status for a file."""
    if is_model_file(source_path):
        return "STAYS"

    if is_deprecated(source_path):
        return "DEPRECATED_DUPLICATE"

    if hoc_equivalent:
        return "ALREADY_IN_HOC"

    return "NEEDS_CLASSIFICATION"


def escape_csv_field(value: str) -> str:
    """Escape field for CSV (handle newlines, quotes)."""
    if not value:
        return ""
    # Replace newlines with escaped version for readability
    value = value.replace("\n", "\\n")
    return value


def generate_inventory(app_root: Path, hoc_root: Path, output_path: Path):
    """Generate the migration inventory CSV."""
    print(f"Scanning app files in: {app_root}")
    app_files = scan_app_files(app_root)
    print(f"Found {len(app_files)} files in app/")

    print(f"Indexing HOC files in: {hoc_root}")
    hoc_index = find_hoc_files(hoc_root)
    print(f"Indexed {len(hoc_index)} HOC entries")

    # Build inventory rows
    rows = []
    stats = {
        "NEEDS_CLASSIFICATION": 0,
        "ALREADY_IN_HOC": 0,
        "STAYS": 0,
        "DEPRECATED_DUPLICATE": 0,
    }

    for i, file_info in enumerate(sorted(app_files, key=lambda x: x.source_path), start=1):
        hoc_equivalent = find_hoc_equivalent(
            file_info.source_path,
            file_info.class_names,
            hoc_index
        )

        auto_status = determine_auto_status(file_info.source_path, hoc_equivalent)
        stats[auto_status] += 1

        row = InventoryRow(
            s_no=i,
            source_path=file_info.source_path,
            audience="",  # Human fills
            domain="",    # Human fills
            layer="",     # Human fills
            target_path="",  # Human fills
            file_header=escape_csv_field(file_info.file_header),
            docstring=escape_csv_field(file_info.docstring),
            existing_hoc_path=hoc_equivalent or "",
            auto_status=auto_status,
            audit_status="PENDING",
            audit_notes="",
            action="",
        )
        rows.append(row)

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "s_no", "source_path", "audience", "domain", "layer", "target_path",
            "file_header", "docstring", "existing_hoc_path",
            "auto_status", "audit_status", "audit_notes", "action"
        ])

        # Data rows
        for row in rows:
            writer.writerow([
                row.s_no, row.source_path, row.audience, row.domain, row.layer,
                row.target_path, row.file_header, row.docstring, row.existing_hoc_path,
                row.auto_status, row.audit_status, row.audit_notes, row.action
            ])

    print(f"\nInventory written to: {output_path}")
    print(f"\nSummary:")
    print(f"  Total files: {len(rows)}")
    for status, count in stats.items():
        print(f"  {status}: {count}")

    return rows, stats


def main():
    parser = argparse.ArgumentParser(description="Generate HOC Migration Inventory CSV")
    parser.add_argument(
        "--app-root",
        type=Path,
        default=Path("backend/app"),
        help="Path to app/ directory (default: backend/app)"
    )
    parser.add_argument(
        "--hoc-root",
        type=Path,
        default=Path("backend/houseofcards"),
        help="Path to houseofcards/ directory (default: backend/houseofcards)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/architecture/migration/MIGRATION_INVENTORY.csv"),
        help="Output CSV path"
    )

    args = parser.parse_args()

    # Resolve paths relative to script location or cwd
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent

    app_root = repo_root / args.app_root if not args.app_root.is_absolute() else args.app_root
    hoc_root = repo_root / args.hoc_root if not args.hoc_root.is_absolute() else args.hoc_root
    output_path = repo_root / args.output if not args.output.is_absolute() else args.output

    if not app_root.exists():
        print(f"Error: app root not found: {app_root}")
        return 1

    generate_inventory(app_root, hoc_root, output_path)
    return 0


if __name__ == "__main__":
    exit(main())
