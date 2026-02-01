#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Add standard metadata headers to scripts missing them (PIN-513 Phase 5A)
# artifact_class: CODE

"""
Add Metadata Headers to Scripts (PIN-513 Phase 5A)

Scans scripts directories for .py files missing the standard `# Layer:` header
and adds a standard metadata block. Only modifies files that lack the header.

Usage:
    python3 scripts/ops/add_metadata_headers.py           # Dry run
    python3 scripts/ops/add_metadata_headers.py --apply    # Apply changes
"""

import os
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BACKEND_ROOT.parent
SCRIPTS_DIRS = [
    REPO_ROOT / "scripts",
    BACKEND_ROOT / "scripts",
]

# Map subdirectory to trigger type
TRIGGER_MAP = {
    "ci": "CI",
    "preflight": "cron",
    "migration": "manual",
    "ops": "manual",
    "deploy": "manual",
    "verification": "manual",
    "stress": "manual",
    "tools": "manual",
    "sdsr": "manual",
    "inventory": "manual",
}

HEADER_TEMPLATE = """\
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: {trigger}
#   Execution: sync
# Role: {role}
# artifact_class: CODE
"""


def get_trigger(filepath: Path) -> str:
    """Determine trigger type from directory."""
    for part in filepath.parts:
        if part in TRIGGER_MAP:
            return TRIGGER_MAP[part]
    return "manual"


def get_role(filepath: Path) -> str:
    """Extract role from docstring or filename."""
    try:
        content = filepath.read_text()
    except (UnicodeDecodeError, OSError):
        return filepath.stem.replace("_", " ").title()

    # Try to extract from docstring
    match = re.search(r'"""(.+?)"""', content, re.DOTALL)
    if match:
        first_line = match.group(1).strip().split("\n")[0].strip()
        if len(first_line) < 100:
            return first_line

    return filepath.stem.replace("_", " ").title()


def has_metadata(filepath: Path) -> bool:
    """Check if file already has a Layer: metadata header."""
    try:
        content = filepath.read_text()
    except (UnicodeDecodeError, OSError):
        return True  # Skip on error
    lines = content.split("\n")[:20]
    return any("# Layer:" in line for line in lines)


def add_header(filepath: Path, dry_run: bool = True) -> bool:
    """Add metadata header to file. Returns True if modified."""
    if has_metadata(filepath):
        return False

    try:
        content = filepath.read_text()
    except (UnicodeDecodeError, OSError):
        return False

    # Skip __init__.py files
    if filepath.name == "__init__.py":
        return False

    trigger = get_trigger(filepath)
    role = get_role(filepath)
    header = HEADER_TEMPLATE.format(trigger=trigger, role=role)

    # Preserve shebang if present
    lines = content.split("\n")
    if lines and lines[0].startswith("#!"):
        new_content = lines[0] + "\n" + header + "\n".join(lines[1:])
    else:
        new_content = header + content

    if not dry_run:
        filepath.write_text(new_content)

    return True


def main():
    apply = "--apply" in sys.argv

    modified = 0
    skipped = 0

    for scripts_dir in SCRIPTS_DIRS:
        if not scripts_dir.exists():
            continue
        for py_file in sorted(scripts_dir.rglob("*.py")):
            if py_file.name == "__init__.py":
                continue
            if add_header(py_file, dry_run=not apply):
                action = "MODIFIED" if apply else "WOULD ADD"
                print(f"  {action}: {py_file.relative_to(REPO_ROOT)}")
                modified += 1
            else:
                skipped += 1

    print(f"\n{'Applied' if apply else 'Dry run'}: {modified} files need headers, {skipped} already have them.")
    if not apply and modified > 0:
        print("Run with --apply to add headers.")


if __name__ == "__main__":
    main()
