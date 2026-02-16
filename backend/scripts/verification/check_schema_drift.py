#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Role: Schema drift gate — validates ORM models match expected contract
# artifact_class: CODE

"""
Schema Drift Gate (BA-17)

Static analysis of ORM model files in app/models/ to detect:
- Models missing __tablename__ declarations
- Duplicate __tablename__ values across files
- Naming convention drift (class name vs table name mismatch)

Does NOT require a database connection — pure file parsing.

Usage:
    python scripts/verification/check_schema_drift.py
    python scripts/verification/check_schema_drift.py --strict
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "models"

# Regex patterns for model class detection
# Matches: class Foo(SQLModel, table=True):  /  class Foo(Base):
RE_CLASS_SQLMODEL = re.compile(
    r"^class\s+(\w+)\s*\(\s*SQLModel\b[^)]*table\s*=\s*True[^)]*\)\s*:",
    re.MULTILINE,
)
RE_CLASS_BASE = re.compile(
    r"^class\s+(\w+)\s*\(\s*Base\s*\)\s*:",
    re.MULTILINE,
)

# Matches: __tablename__ = "some_table"
RE_TABLENAME = re.compile(
    r'__tablename__\s*=\s*["\'](\w+)["\']',
)

# Matches any class definition (broad) — used to find the block owning a tablename
RE_ANY_CLASS = re.compile(
    r"^class\s+(\w+)\s*\([^)]*\)\s*:",
    re.MULTILINE,
)

# Files to skip (non-model helpers, __init__, __pycache__)
SKIP_FILES = {"__init__.py"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case for naming convention checks."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _find_tablename_for_class(source: str, class_name: str, class_start: int) -> str | None:
    """Find the __tablename__ assigned inside a class body.

    We look from *class_start* until the next class definition (or EOF),
    restricting to indented lines that belong to the class body.
    """
    # Find the end of this class body (next class at indent 0 or EOF)
    next_class = RE_ANY_CLASS.search(source, class_start + 1)
    end = next_class.start() if next_class else len(source)

    body = source[class_start:end]
    m = RE_TABLENAME.search(body)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Core scanner
# ---------------------------------------------------------------------------


def scan_models(models_dir: Path) -> list[dict]:
    """Scan all Python files in *models_dir* and return model metadata.

    Each entry:
        {
            "file": str,           # relative file path
            "class_name": str,     # Python class name
            "orm_type": str,       # "SQLModel" | "Base"
            "tablename": str|None, # __tablename__ value or None
        }
    """
    results: list[dict] = []

    if not models_dir.is_dir():
        print(f"[FATAL] Models directory not found: {models_dir}", file=sys.stderr)
        sys.exit(1)

    for pyfile in sorted(models_dir.glob("*.py")):
        if pyfile.name in SKIP_FILES or pyfile.name.startswith("__"):
            continue

        source = pyfile.read_text(encoding="utf-8")

        # Collect SQLModel table classes
        for m in RE_CLASS_SQLMODEL.finditer(source):
            class_name = m.group(1)
            tablename = _find_tablename_for_class(source, class_name, m.start())
            results.append({
                "file": pyfile.name,
                "class_name": class_name,
                "orm_type": "SQLModel",
                "tablename": tablename,
            })

        # Collect declarative Base classes
        for m in RE_CLASS_BASE.finditer(source):
            class_name = m.group(1)
            tablename = _find_tablename_for_class(source, class_name, m.start())
            results.append({
                "file": pyfile.name,
                "class_name": class_name,
                "orm_type": "Base",
                "tablename": tablename,
            })

    return results


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate(models: list[dict], strict: bool = False) -> tuple[int, int, int]:
    """Run drift checks. Returns (passed, warnings, critical)."""
    passed = 0
    warnings = 0
    critical = 0

    # ------------------------------------------------------------------
    # Check 1: Every table model must have a __tablename__
    # ------------------------------------------------------------------
    for mdl in models:
        if mdl["tablename"] is None:
            # Models that inherit from SQLModel with table=True or Base
            # MUST have __tablename__. Missing is a warning (strict: critical).
            reason = "missing __tablename__ declaration"
            if strict:
                print(f"[FAIL] {mdl['class_name']} ({mdl['file']}) — {reason}")
                critical += 1
            else:
                print(f"[WARN] {mdl['class_name']} ({mdl['file']}) — potential drift: {reason}")
                warnings += 1
        else:
            print(f"[PASS] {mdl['class_name']} — schema consistent (table: {mdl['tablename']})")
            passed += 1

    # ------------------------------------------------------------------
    # Check 2: No duplicate __tablename__ across files
    # ------------------------------------------------------------------
    tablename_map: dict[str, list[dict]] = defaultdict(list)
    for mdl in models:
        if mdl["tablename"]:
            tablename_map[mdl["tablename"]].append(mdl)

    for tname, owners in tablename_map.items():
        if len(owners) > 1:
            files = ", ".join(f"{o['class_name']} ({o['file']})" for o in owners)
            print(f"[FAIL] duplicate __tablename__ '{tname}' in: {files}")
            critical += 1

    # ------------------------------------------------------------------
    # Check 3: Naming convention advisory — snake(ClassName) ~= tablename
    # ------------------------------------------------------------------
    for mdl in models:
        if mdl["tablename"]:
            expected_snake = _camel_to_snake(mdl["class_name"])
            # Accept pluralized forms: expected_snake or expected_snake + "s"/"es"
            tname = mdl["tablename"]
            if tname not in (expected_snake, expected_snake + "s", expected_snake + "es"):
                # Advisory only — many legitimate deviations exist
                reason = (
                    f"naming convention drift: class '{mdl['class_name']}' "
                    f"-> expected '{expected_snake}(s)' but got '{tname}'"
                )
                if strict:
                    print(f"[WARN] {mdl['class_name']} ({mdl['file']}) — {reason}")
                    warnings += 1

    return passed, warnings, critical


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Schema drift gate — static ORM model analysis (BA-17)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing __tablename__ as critical (exit 1)",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=MODELS_DIR,
        help=f"Override models directory (default: {MODELS_DIR})",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Schema Drift Gate (BA-17)")
    print("=" * 60)
    print(f"  Models directory: {args.models_dir}")
    print(f"  Strict mode: {args.strict}")
    print("=" * 60)
    print()

    models = scan_models(args.models_dir)

    if not models:
        print("[WARN] No ORM table models found — check models directory")
        return 0

    passed, warnings, critical = validate(models, strict=args.strict)

    print()
    print("-" * 60)
    print(f"  SUMMARY: {len(models)} models scanned")
    print(f"    PASS: {passed}")
    print(f"    WARN: {warnings}")
    print(f"    FAIL: {critical}")
    print("-" * 60)

    if critical > 0:
        print("  RESULT: FAILED (critical drift detected)")
        return 1

    print("  RESULT: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
