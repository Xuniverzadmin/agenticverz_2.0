#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Walk scripts/ + tools/, classify each script into category/sub_category/status/customer_impact
# artifact_class: CODE

"""
Script Registry Generator

Walks scripts/ and tools/ directories, extracts docstring/header from each file,
and classifies into a CSV registry.

Usage:
    python3 scripts/ops/scripts_registry_generator.py
    python3 scripts/ops/scripts_registry_generator.py --output literature/scripts/SCRIPTS_REGISTRY.csv
    python3 scripts/ops/scripts_registry_generator.py --json
"""

import argparse
import ast
import csv
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
TOOLS_ROOT = PROJECT_ROOT / "tools"
BACKEND_SCRIPTS_ROOT = PROJECT_ROOT / "backend" / "scripts"
DEFAULT_OUTPUT = PROJECT_ROOT / "literature" / "scripts" / "SCRIPTS_REGISTRY.csv"

CSV_COLUMNS = [
    "path",
    "filename",
    "extension",
    "directory",
    "category",
    "sub_category",
    "status",
    "customer_impact",
    "purpose",
    "lines",
]

# ---------------------------------------------------------------------------
# Classification Heuristics
# ---------------------------------------------------------------------------

# Path pattern → (category, sub_category)
PATH_RULES: list[tuple[str, str, str]] = [
    # CI / Guardrails
    ("scripts/ci/c2_guardrails", "ci-validation", "guardrails"),
    ("scripts/ci/c3_guardrails", "ci-validation", "guardrails"),
    ("scripts/ci/c4_guardrails", "ci-validation", "guardrails"),
    ("scripts/ci/c5_guardrails", "ci-validation", "guardrails"),
    ("scripts/ci/o4_checks", "ci-validation", "guardrails"),
    ("scripts/ci/", "ci-validation", "guards"),
    # Deploy
    ("scripts/deploy/", "system-infra", "deployment"),
    # Hooks
    ("scripts/hooks/", "system-infra", "hooks"),
    # Preflight
    ("scripts/preflight/", "ci-validation", "preflight-scan"),
    # Ops — sub-categories
    ("scripts/ops/canary", "system-infra", "canary"),
    ("scripts/ops/chaos", "system-infra", "chaos-testing"),
    ("scripts/ops/cron", "system-infra", "cron"),
    ("scripts/ops/diagnostics", "system-infra", "diagnostics"),
    ("scripts/ops/sce/", "architecture-analysis", "sce-extraction"),
    ("scripts/ops/vault", "system-infra", "vault"),
    ("scripts/ops/webhook", "system-infra", "webhook"),
    ("scripts/ops/archival", "system-infra", "archival"),
    ("scripts/ops/tests", "ci-validation", "ops-tests"),
    # Ops — architecture analysis (by name patterns, handled below)
    ("scripts/ops/", "system-infra", "ops"),
    # Migration
    ("scripts/migration", "system-infra", "migration"),
    ("scripts/migrations", "system-infra", "migration"),
    # Semantic auditor
    ("scripts/semantic_auditor/", "architecture-analysis", "semantic-audit"),
    # Verification
    ("scripts/verification/", "ci-validation", "verification"),
    # SDSR
    ("scripts/sdsr/", "system-infra", "sdsr"),
    # Load / Stress / Smoke / Chaos
    ("scripts/load/", "ci-validation", "load-testing"),
    ("scripts/stress/", "ci-validation", "stress-testing"),
    ("scripts/smoke/", "ci-validation", "smoke-testing"),
    ("scripts/chaos/", "system-infra", "chaos-testing"),
    # Inventory
    ("scripts/inventory/", "architecture-analysis", "inventory"),
    # L2.1
    ("scripts/l2_1/", "architecture-analysis", "l2-generation"),
    # Dev
    ("scripts/dev/", "system-infra", "dev-tools"),
    # Tools
    ("scripts/tools/", "system-infra", "dev-tools"),
    ("tools/webhook_dev", "system-infra", "webhook"),
    ("tools/webhook_receiver", "system-infra", "webhook"),
    ("tools/wiremock", "system-infra", "mock"),
    ("tools/", "system-infra", "tools"),
    # Backend scripts
    ("backend/scripts/ops/", "system-infra", "backend-ops"),
    ("backend/scripts/", "system-infra", "backend-scripts"),
]

# Name patterns that override sub_category to architecture-analysis / architecture-literature
ARCH_ANALYSIS_KEYWORDS = [
    "hoc_layer_inventory", "hoc_domain_literature", "l5_spine_pairing",
    "l5_orphan_classifier", "hoc_spine_study", "hoc_function_inventory",
    "hoc_intent_classifier", "hoc_placement_analyzer", "hoc_capability_doc",
    "hoc_feature_extractor", "scripts_registry", "layer_validator",
    "bloat_audit", "domain_lock", "hoc_phase",
]

LITERATURE_KEYWORDS = [
    "literature", "doc_generator", "capability_doc", "feature_extractor",
]

MIGRATION_KEYWORDS = [
    "migrate", "migration", "backfill", "seed", "one_time", "onetime",
]

DEPRECATED_KEYWORDS = [
    "deprecated", "old_", "_old", "legacy", "archived",
]


def classify_path(rel_path: str, filename: str, purpose: str) -> tuple[str, str, str, str]:
    """Return (category, sub_category, status, customer_impact)."""
    category = "system-infra"
    sub_category = "ops"
    status = "active"
    customer_impact = "none"

    # Path-based classification
    for pattern, cat, sub in PATH_RULES:
        if pattern in rel_path:
            category = cat
            sub_category = sub
            break

    # Name-based overrides
    lower_name = filename.lower()
    lower_purpose = purpose.lower()

    for kw in ARCH_ANALYSIS_KEYWORDS:
        if kw in lower_name:
            category = "architecture-analysis"
            sub_category = "hoc-analysis"
            break

    for kw in LITERATURE_KEYWORDS:
        if kw in lower_name:
            category = "architecture-literature"
            sub_category = "hoc-literature"
            break

    for kw in MIGRATION_KEYWORDS:
        if kw in lower_name or kw in lower_purpose:
            status = "one-time-migration"
            break

    for kw in DEPRECATED_KEYWORDS:
        if kw in lower_name or kw in lower_purpose:
            status = "deprecated"
            break

    # Customer impact heuristics
    if "customer" in lower_purpose or "cus" in lower_purpose:
        customer_impact = "indirect"
    if "api" in lower_name and "guard" not in lower_name:
        customer_impact = "indirect"
    if category == "ci-validation":
        customer_impact = "indirect"
    if sub_category in ("deployment", "migration"):
        customer_impact = "indirect"

    return category, sub_category, status, customer_impact


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def extract_purpose_python(filepath: Path) -> str:
    """Extract purpose from a Python file (header Role or docstring)."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

    # Try header Role
    for line in source.splitlines()[:50]:
        stripped = line.strip()
        if not stripped.startswith("#"):
            if stripped and not stripped.startswith('"""') and not stripped.startswith("'''"):
                break
            continue
        content = stripped.lstrip("# ").strip()
        if content.startswith("Role:"):
            return content[5:].strip()[:200]

    # Try AST docstring
    try:
        tree = ast.parse(source, filename=str(filepath))
        doc = ast.get_docstring(tree)
        if doc:
            return doc.split("\n")[0].strip()[:200]
    except SyntaxError:
        pass

    return ""


def extract_purpose_shell(filepath: Path) -> str:
    """Extract purpose from a shell script (first comment block)."""
    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return ""

    for line in lines[:30]:
        stripped = line.strip()
        if stripped.startswith("#!/"):
            continue
        if stripped.startswith("#"):
            content = stripped.lstrip("# ").strip()
            if content and len(content) > 10:
                return content[:200]
        elif stripped:
            break
    return ""


def extract_purpose(filepath: Path) -> str:
    """Extract purpose from any script file."""
    if filepath.suffix == ".py":
        return extract_purpose_python(filepath)
    elif filepath.suffix in (".sh", ".bash"):
        return extract_purpose_shell(filepath)
    return ""


def count_lines(filepath: Path) -> int:
    """Count lines in a file."""
    try:
        return len(filepath.read_text(encoding="utf-8", errors="replace").splitlines())
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_scripts() -> list[Path]:
    """Find all script files under scripts/ and tools/."""
    extensions = {".py", ".sh", ".bash"}
    results: list[Path] = []

    for root_dir in [SCRIPTS_ROOT, TOOLS_ROOT, BACKEND_SCRIPTS_ROOT]:
        if not root_dir.is_dir():
            continue
        for filepath in sorted(root_dir.rglob("*")):
            if not filepath.is_file():
                continue
            if filepath.suffix not in extensions:
                continue
            if "__pycache__" in str(filepath):
                continue
            if filepath.name == "__init__.py":
                continue
            results.append(filepath)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def generate_registry(output_path: Path, as_json: bool = False) -> dict:
    """Generate the script registry."""
    scripts = discover_scripts()
    print(f"Discovered {len(scripts)} script files")

    rows: list[dict[str, str]] = []
    for filepath in scripts:
        try:
            rel_path = str(filepath.relative_to(PROJECT_ROOT))
        except ValueError:
            rel_path = str(filepath)

        purpose = extract_purpose(filepath)
        lines = count_lines(filepath)
        category, sub_category, status, customer_impact = classify_path(
            rel_path, filepath.stem, purpose
        )

        rows.append({
            "path": rel_path,
            "filename": filepath.name,
            "extension": filepath.suffix,
            "directory": str(filepath.parent.relative_to(PROJECT_ROOT)),
            "category": category,
            "sub_category": sub_category,
            "status": status,
            "customer_impact": customer_impact,
            "purpose": purpose,
            "lines": str(lines),
        })

    rows.sort(key=lambda r: (r["category"], r["sub_category"], r["path"]))

    if as_json:
        result = {
            "total": len(rows),
            "by_category": {},
            "by_sub_category": {},
            "by_status": {},
            "rows": rows,
        }
        for r in rows:
            result["by_category"][r["category"]] = result["by_category"].get(r["category"], 0) + 1
            result["by_sub_category"][r["sub_category"]] = result["by_sub_category"].get(r["sub_category"], 0) + 1
            result["by_status"][r["status"]] = result["by_status"].get(r["status"], 0) + 1
        json.dump(result, sys.stdout, indent=2)
        print()
        return result

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    by_cat: dict[str, int] = {}
    by_sub: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for r in rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
        by_sub[r["sub_category"]] = by_sub.get(r["sub_category"], 0) + 1
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    print(f"\nCSV written: {output_path}")
    print(f"  Rows: {len(rows)}")
    print("\nBy category:")
    for cat in sorted(by_cat):
        print(f"  {cat}: {by_cat[cat]}")
    print("\nBy sub_category:")
    for sub in sorted(by_sub):
        print(f"  {sub}: {by_sub[sub]}")
    print("\nBy status:")
    for st in sorted(by_status):
        print(f"  {st}: {by_status[st]}")

    return {"total": len(rows), "by_category": by_cat}


def main():
    parser = argparse.ArgumentParser(
        description="Script Registry Generator — classify all scripts into a CSV registry"
    )
    parser.add_argument("--output", "-o", type=str,
                        help=f"Output CSV path (default: {DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--domain", type=str, help="Unused (for CLI consistency)")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument("--help-long", action="store_true", help="Show extended help")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    print("=" * 60)
    print("Script Registry Generator")
    print("=" * 60)
    print()

    generate_registry(output_path, as_json=args.json)

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
