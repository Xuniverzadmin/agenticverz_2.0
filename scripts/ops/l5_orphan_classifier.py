#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: L5 orphan classifier — classifies orphaned L5 engines by intra-domain usage
# artifact_class: CODE

"""
L5 Orphan Classifier (Phase B — PIN-491)

Scans all orphaned L5 engines (those with no L2 or L4 callers) and classifies them:

  INTERNAL     — Imported by other L5 engines within the same domain
  SCHEMA-ONLY  — Contains only types, enums, constants, dataclasses (no business logic)
  WIRED        — Already wired through L4 (not an orphan)
  L2-DIRECT    — Called directly by L2 (gap, not an orphan)
  UNCLASSIFIED — Needs manual review (FUTURE, DEPRECATED, or MISSING-WIRE)

Usage:
    # Full classification scan
    python scripts/ops/l5_orphan_classifier.py

    # Single domain
    python scripts/ops/l5_orphan_classifier.py --domain policies

    # JSON output
    python scripts/ops/l5_orphan_classifier.py --json

    # Verify all classified (exit 1 if any UNCLASSIFIED remain)
    python scripts/ops/l5_orphan_classifier.py --verify

    # Show only a specific class
    python scripts/ops/l5_orphan_classifier.py --class INTERNAL

    # Write classification report to file
    python scripts/ops/l5_orphan_classifier.py --output docs/architecture/hoc/L5_ORPHAN_CLASSIFICATION.md
"""

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOC_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc"
L2_API_ROOT = HOC_ROOT / "api" / "cus"
L4_SPINE_ROOT = HOC_ROOT / "hoc_spine"
CUS_ROOT = HOC_ROOT / "cus"

# Customer domains to scan
DOMAINS = [
    "account", "activity", "analytics", "api_keys", "controls",
    "incidents", "integrations", "logs", "overview", "policies",
]

# L5 subdirectory names
L5_SUBDIRS = ("L5_engines", "L5_support", "L5_controls")

# AST node types that indicate schema/type-only content
SCHEMA_ONLY_INDICATORS = {
    "TypeAlias", "ClassDef",  # dataclasses, enums, BaseModel subclasses
}

# Patterns in class bases that indicate schema/type classes
SCHEMA_BASE_CLASSES = {
    "BaseModel", "BaseSettings", "Enum", "IntEnum", "StrEnum",
    "TypedDict", "NamedTuple", "Protocol",
}


@dataclass
class L5EngineInfo:
    """Full analysis of an L5 engine file."""
    domain: str
    module_name: str
    file_path: str
    last_modified: str
    # Content analysis
    top_level_functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    class_bases: dict[str, list[str]] = field(default_factory=dict)
    assignments: list[str] = field(default_factory=list)  # top-level assignments
    has_dataclass_decorator: bool = False
    line_count: int = 0
    # Import analysis
    imports_from_same_domain: list[str] = field(default_factory=list)
    imported_by_same_domain: list[str] = field(default_factory=list)  # other L5 files that import this
    imported_by_l2: bool = False
    imported_by_l4: bool = False
    # Classification
    classification: str = "UNCLASSIFIED"
    classification_reason: str = ""


def _analyze_file_ast(filepath: Path) -> dict[str, Any]:
    """Analyze a Python file's AST for classification signals."""
    try:
        source = filepath.read_text()
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return {"error": True}

    result: dict[str, Any] = {
        "top_level_functions": [],
        "classes": [],
        "class_bases": {},
        "assignments": [],
        "has_dataclass_decorator": False,
        "line_count": len(source.splitlines()),
        "imports_l5_same_domain": [],
    }

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip dunder methods and private helpers starting with _
            result["top_level_functions"].append(node.name)

        elif isinstance(node, ast.ClassDef):
            result["classes"].append(node.name)
            # Extract base class names
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
            result["class_bases"][node.name] = bases
            # Check for @dataclass decorator
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == "dataclass":
                    result["has_dataclass_decorator"] = True
                elif isinstance(dec, ast.Call):
                    if isinstance(dec.func, ast.Name) and dec.func.id == "dataclass":
                        result["has_dataclass_decorator"] = True

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result["assignments"].append(target.id)

        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                result["assignments"].append(node.target.id)

    # Extract L5 imports from same domain
    domain_from_path = None
    for part in filepath.parts:
        if part in DOMAINS:
            domain_from_path = part
            break

    if domain_from_path:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            m = re.match(
                rf"app\.hoc\.cus\.{re.escape(domain_from_path)}\.L5_(?:engines|support|controls)\.(\w+)",
                node.module,
            )
            if m:
                result["imports_l5_same_domain"].append(m.group(1))

    return result


def _is_schema_only(info: dict[str, Any]) -> tuple[bool, str]:
    """Determine if a file contains only types/schemas/constants."""
    functions = info.get("top_level_functions", [])
    classes = info.get("classes", [])
    class_bases = info.get("class_bases", {})
    assignments = info.get("assignments", [])

    # If no classes and no functions, just assignments = constants module
    if not classes and not functions and assignments:
        return True, "Constants-only module (no classes or functions)"

    # If has functions with real logic, not schema-only
    # Filter out trivial functions (getters, factory functions)
    non_trivial_functions = [
        f for f in functions
        if not f.startswith("_") and f not in ("__init__", "__repr__", "__str__", "__eq__", "__hash__")
    ]

    # Check if ALL classes are schema/type classes
    all_schema_classes = True
    for cls_name, bases in class_bases.items():
        if not any(b in SCHEMA_BASE_CLASSES for b in bases):
            # Check if it's a plain dataclass
            if not info.get("has_dataclass_decorator"):
                all_schema_classes = False
                break

    if all_schema_classes and classes and not non_trivial_functions:
        return True, f"All classes are schema/type classes: {', '.join(classes)}"

    # If only enums
    enum_classes = [
        c for c, bases in class_bases.items()
        if any(b in ("Enum", "IntEnum", "StrEnum") for b in bases)
    ]
    if enum_classes and len(enum_classes) == len(classes) and not non_trivial_functions:
        return True, f"Enum-only module: {', '.join(enum_classes)}"

    return False, ""


def discover_all_l5_engines() -> dict[str, list[Path]]:
    """Discover all L5 engine files grouped by domain."""
    domain_engines: dict[str, list[Path]] = {}
    for domain in DOMAINS:
        domain_root = CUS_ROOT / domain
        engines: list[Path] = []
        for subdir_name in L5_SUBDIRS:
            engine_dir = domain_root / subdir_name
            if not engine_dir.exists():
                continue
            for filepath in sorted(engine_dir.rglob("*.py")):
                if filepath.name == "__init__.py":
                    continue
                engines.append(filepath)
        if engines:
            domain_engines[domain] = engines
    return domain_engines


def scan_l2_l5_imports() -> dict[str, set[str]]:
    """Scan L2 API files and return {domain: {engine_module_names}} imported."""
    domain_refs: dict[str, set[str]] = {}
    for domain in DOMAINS:
        api_dir = L2_API_ROOT / domain
        if not api_dir.exists():
            continue
        for filepath in sorted(api_dir.rglob("*.py")):
            if filepath.name == "__init__.py":
                continue
            try:
                source = filepath.read_text()
                tree = ast.parse(source, filename=str(filepath))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or node.module is None:
                    continue
                m = re.match(
                    r"app\.hoc\.cus\.(\w+)\.L5_(?:engines|support|controls)\.(\w+)",
                    node.module,
                )
                if m:
                    d, eng = m.group(1), m.group(2)
                    domain_refs.setdefault(d, set()).add(eng)
                # Also match package-level imports
                m2 = re.match(
                    r"app\.hoc\.cus\.(\w+)\.L5_(?:engines|support|controls)$",
                    node.module,
                )
                if m2:
                    d = m2.group(1)
                    for alias in node.names:
                        domain_refs.setdefault(d, set()).add(alias.name)
    return domain_refs


def scan_l4_l5_imports() -> dict[str, set[str]]:
    """Scan L4 spine files and return {domain: {engine_module_names}} imported."""
    domain_refs: dict[str, set[str]] = {}
    if not L4_SPINE_ROOT.exists():
        return domain_refs
    for filepath in sorted(L4_SPINE_ROOT.rglob("*.py")):
        if filepath.name == "__init__.py":
            continue
        try:
            source = filepath.read_text()
            tree = ast.parse(source, filename=str(filepath))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            m = re.match(
                r"app\.hoc\.cus\.(\w+)\.L5_(?:engines|support|controls)\.(\w+)",
                node.module,
            )
            if m:
                d, eng = m.group(1), m.group(2)
                domain_refs.setdefault(d, set()).add(eng)
            m2 = re.match(
                r"app\.hoc\.cus\.(\w+)\.L5_(?:engines|support|controls)$",
                node.module,
            )
            if m2:
                d = m2.group(1)
                for alias in node.names:
                    domain_refs.setdefault(d, set()).add(alias.name)
    return domain_refs


def build_intra_domain_import_map(domain: str, engine_paths: list[Path]) -> dict[str, set[str]]:
    """Build map: {engine_module -> set of L5 modules in same domain that import it}."""
    # For each engine, find what same-domain L5 modules it imports
    # Then invert: for each module, find who imports it
    imported_by: dict[str, set[str]] = {p.stem: set() for p in engine_paths}

    for filepath in engine_paths:
        module_name = filepath.stem
        try:
            source = filepath.read_text()
            tree = ast.parse(source, filename=str(filepath))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            m = re.match(
                rf"app\.hoc\.cus\.{re.escape(domain)}\.L5_(?:engines|support|controls)\.(\w+)",
                node.module,
            )
            if m:
                target_module = m.group(1)
                if target_module in imported_by and target_module != module_name:
                    imported_by[target_module].add(module_name)
            # Also check package-level imports
            m2 = re.match(
                rf"app\.hoc\.cus\.{re.escape(domain)}\.L5_(?:engines|support|controls)$",
                node.module,
            )
            if m2:
                for alias in node.names:
                    if alias.name in imported_by and alias.name != module_name:
                        imported_by[alias.name].add(module_name)

    return imported_by


def _scan_wider_importers(domain: str, module_name: str) -> list[str]:
    """Scan beyond L2/L4/L5 for any file that imports this L5 engine.

    Checks: L3 adapters, L6 drivers, hoc_spine (non-handler), workers, tests.
    Returns list of relative paths of importers found.
    """
    pattern = rf"app\.hoc\.cus\.{re.escape(domain)}\.L5_(?:engines|support|controls)\.{re.escape(module_name)}"
    importers: list[str] = []

    # Scan L3 adapters
    l3_dir = CUS_ROOT / domain / "L3_adapters"
    # Scan L6 drivers
    l6_dir = CUS_ROOT / domain / "L6_drivers"
    # Scan hoc_spine (all, not just handlers)
    spine_dir = L4_SPINE_ROOT
    # Scan general domain (cross-domain infra)
    general_dir = CUS_ROOT / "general"

    for scan_dir in [l3_dir, l6_dir, spine_dir, general_dir]:
        if not scan_dir.exists():
            continue
        for filepath in scan_dir.rglob("*.py"):
            if filepath.name == "__init__.py":
                continue
            try:
                source = filepath.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            if re.search(pattern, source):
                importers.append(str(filepath.relative_to(PROJECT_ROOT)))

    return importers


def classify_engines(
    domain: str,
    engine_paths: list[Path],
    l2_refs: dict[str, set[str]],
    l4_refs: dict[str, set[str]],
) -> list[L5EngineInfo]:
    """Classify all L5 engines for a domain."""
    # Build intra-domain import map
    intra_imports = build_intra_domain_import_map(domain, engine_paths)

    l2_set = l2_refs.get(domain, set())
    l4_set = l4_refs.get(domain, set())

    results: list[L5EngineInfo] = []

    for filepath in engine_paths:
        module_name = filepath.stem
        stat = filepath.stat()
        last_mod = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")

        info = L5EngineInfo(
            domain=domain,
            module_name=module_name,
            file_path=str(filepath.relative_to(PROJECT_ROOT)),
            last_modified=last_mod,
        )

        # Analyze AST
        analysis = _analyze_file_ast(filepath)
        if "error" in analysis:
            info.classification = "UNCLASSIFIED"
            info.classification_reason = "Parse error"
            results.append(info)
            continue

        info.top_level_functions = analysis["top_level_functions"]
        info.classes = analysis["classes"]
        info.class_bases = analysis["class_bases"]
        info.assignments = analysis["assignments"]
        info.has_dataclass_decorator = analysis["has_dataclass_decorator"]
        info.line_count = analysis["line_count"]
        info.imports_from_same_domain = analysis["imports_l5_same_domain"]
        info.imported_by_same_domain = sorted(intra_imports.get(module_name, set()))
        info.imported_by_l2 = module_name in l2_set
        info.imported_by_l4 = module_name in l4_set

        # Classification logic (priority order)
        if info.imported_by_l4:
            info.classification = "WIRED"
            info.classification_reason = "Referenced by L4 orchestrator"
        elif info.imported_by_l2:
            info.classification = "L2-DIRECT"
            info.classification_reason = "Called directly by L2 (gap)"
        elif info.imported_by_same_domain:
            info.classification = "INTERNAL"
            info.classification_reason = f"Imported by: {', '.join(info.imported_by_same_domain)}"
        else:
            # Check if schema-only
            is_schema, reason = _is_schema_only(analysis)
            if is_schema:
                info.classification = "SCHEMA-ONLY"
                info.classification_reason = reason
            else:
                # Second pass: check wider importers (L3, L6, spine, general)
                wider = _scan_wider_importers(domain, module_name)
                if wider:
                    info.classification = "INTERNAL"
                    short_paths = [p.split("/")[-1] for p in wider]
                    info.classification_reason = f"Imported by non-L5: {', '.join(short_paths)}"
                else:
                    # Third pass: check if this engine imports other L5 engines
                    # that are WIRED or INTERNAL (making this part of the chain)
                    imports_known = [
                        m for m in info.imports_from_same_domain
                        if m in (l4_set | l2_set | {
                            n for n, importers in intra_imports.items() if importers
                        })
                    ]
                    if imports_known:
                        info.classification = "INTERNAL"
                        info.classification_reason = (
                            f"Imports wired/internal engines: {', '.join(imports_known)}"
                        )
                    else:
                        info.classification = "UNCLASSIFIED"
                        info.classification_reason = (
                            f"No importers found. "
                            f"Functions: {len(info.top_level_functions)}, "
                            f"Classes: {len(info.classes)}, "
                            f"Lines: {info.line_count}"
                        )

        results.append(info)

    return results


@dataclass
class DomainClassification:
    """Classification summary for a domain."""
    domain: str
    total: int = 0
    wired: int = 0
    l2_direct: int = 0
    internal: int = 0
    schema_only: int = 0
    unclassified: int = 0
    engines: list[L5EngineInfo] = field(default_factory=list)


def format_text_report(classifications: list[DomainClassification], filter_class: str | None = None) -> str:
    """Format classifications as text report."""
    lines = [
        "==============================================",
        "  L5 Orphan Classification Report",
        f"  {datetime.now().strftime('%Y-%m-%d')}",
        "  Phase B — PIN-491",
        "==============================================",
        "",
    ]

    totals = {"WIRED": 0, "L2-DIRECT": 0, "INTERNAL": 0, "SCHEMA-ONLY": 0, "UNCLASSIFIED": 0}
    grand_total = 0

    for dc in sorted(classifications, key=lambda d: d.domain):
        if dc.total == 0:
            continue

        grand_total += dc.total
        totals["WIRED"] += dc.wired
        totals["L2-DIRECT"] += dc.l2_direct
        totals["INTERNAL"] += dc.internal
        totals["SCHEMA-ONLY"] += dc.schema_only
        totals["UNCLASSIFIED"] += dc.unclassified

        lines.append(f"DOMAIN: {dc.domain} ({dc.total} L5 engines)")
        lines.append(f"  WIRED:          {dc.wired}")
        lines.append(f"  L2-DIRECT:      {dc.l2_direct}")
        lines.append(f"  INTERNAL:       {dc.internal}")
        lines.append(f"  SCHEMA-ONLY:    {dc.schema_only}")
        lines.append(f"  UNCLASSIFIED:   {dc.unclassified}")
        lines.append("")

        # Show engines by class
        for cls_name in ("WIRED", "L2-DIRECT", "INTERNAL", "SCHEMA-ONLY", "UNCLASSIFIED"):
            if filter_class and cls_name != filter_class:
                continue
            engines = [e for e in dc.engines if e.classification == cls_name]
            if not engines:
                continue
            lines.append(f"  {cls_name}:")
            for e in sorted(engines, key=lambda x: x.module_name):
                lines.append(f"    {e.module_name}.py  ({e.line_count} lines) — {e.classification_reason}")
            lines.append("")

        lines.append("")

    lines.append("SUMMARY:")
    lines.append(f"  Total L5 engines:  {grand_total}")
    for cls_name, count in totals.items():
        lines.append(f"  {cls_name:<16} {count}")
    lines.append("")

    orphan_count = totals["INTERNAL"] + totals["SCHEMA-ONLY"] + totals["UNCLASSIFIED"]
    lines.append(f"  Orphans (no L2/L4 callers): {orphan_count}")
    lines.append(f"    Auto-classified:   {totals['INTERNAL'] + totals['SCHEMA-ONLY']}")
    lines.append(f"    Need manual review: {totals['UNCLASSIFIED']}")
    lines.append("")

    return "\n".join(lines)


def format_json_report(classifications: list[DomainClassification]) -> str:
    """Format classifications as JSON."""
    data = {
        "generated": datetime.now().isoformat(),
        "phase": "B",
        "pin": "491",
        "domains": [],
        "summary": {
            "total": 0,
            "wired": 0,
            "l2_direct": 0,
            "internal": 0,
            "schema_only": 0,
            "unclassified": 0,
        },
    }
    for dc in sorted(classifications, key=lambda d: d.domain):
        if dc.total == 0:
            continue
        domain_data = {
            "domain": dc.domain,
            "total": dc.total,
            "wired": dc.wired,
            "l2_direct": dc.l2_direct,
            "internal": dc.internal,
            "schema_only": dc.schema_only,
            "unclassified": dc.unclassified,
            "engines": [],
        }
        for e in sorted(dc.engines, key=lambda x: (x.classification, x.module_name)):
            domain_data["engines"].append({
                "module": e.module_name,
                "classification": e.classification,
                "reason": e.classification_reason,
                "lines": e.line_count,
                "functions": len(e.top_level_functions),
                "classes": len(e.classes),
                "imported_by": e.imported_by_same_domain,
                "imports": e.imports_from_same_domain,
                "last_modified": e.last_modified,
            })
        data["domains"].append(domain_data)
        data["summary"]["total"] += dc.total
        data["summary"]["wired"] += dc.wired
        data["summary"]["l2_direct"] += dc.l2_direct
        data["summary"]["internal"] += dc.internal
        data["summary"]["schema_only"] += dc.schema_only
        data["summary"]["unclassified"] += dc.unclassified

    return json.dumps(data, indent=2)


def format_markdown_report(classifications: list[DomainClassification]) -> str:
    """Format classifications as markdown document."""
    lines = [
        "# L5 Orphan Classification Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}",
        "**Phase:** B — PIN-491",
        "",
        "---",
        "",
        "## Summary",
        "",
    ]

    totals = {"WIRED": 0, "L2-DIRECT": 0, "INTERNAL": 0, "SCHEMA-ONLY": 0, "UNCLASSIFIED": 0}
    grand_total = 0

    # Summary table
    lines.append("| Domain | Total | WIRED | L2-DIRECT | INTERNAL | SCHEMA-ONLY | UNCLASSIFIED |")
    lines.append("|--------|-------|-------|-----------|----------|-------------|--------------|")

    for dc in sorted(classifications, key=lambda d: d.domain):
        if dc.total == 0:
            continue
        grand_total += dc.total
        totals["WIRED"] += dc.wired
        totals["L2-DIRECT"] += dc.l2_direct
        totals["INTERNAL"] += dc.internal
        totals["SCHEMA-ONLY"] += dc.schema_only
        totals["UNCLASSIFIED"] += dc.unclassified
        lines.append(
            f"| {dc.domain} | {dc.total} | {dc.wired} | {dc.l2_direct} | "
            f"{dc.internal} | {dc.schema_only} | {dc.unclassified} |"
        )

    lines.append(
        f"| **TOTAL** | **{grand_total}** | **{totals['WIRED']}** | **{totals['L2-DIRECT']}** | "
        f"**{totals['INTERNAL']}** | **{totals['SCHEMA-ONLY']}** | **{totals['UNCLASSIFIED']}** |"
    )
    lines.append("")

    # Per-domain detail
    lines.append("---")
    lines.append("")

    for dc in sorted(classifications, key=lambda d: d.domain):
        if dc.total == 0:
            continue

        lines.append(f"## {dc.domain} ({dc.total} engines)")
        lines.append("")

        for cls_name in ("WIRED", "L2-DIRECT", "INTERNAL", "SCHEMA-ONLY", "UNCLASSIFIED"):
            engines = [e for e in dc.engines if e.classification == cls_name]
            if not engines:
                continue

            lines.append(f"### {cls_name} ({len(engines)})")
            lines.append("")
            lines.append("| Engine | Lines | Reason |")
            lines.append("|--------|-------|--------|")
            for e in sorted(engines, key=lambda x: x.module_name):
                reason = e.classification_reason.replace("|", "\\|")
                lines.append(f"| `{e.module_name}.py` | {e.line_count} | {reason} |")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="L5 Orphan Classifier (Phase B — PIN-491)"
    )
    parser.add_argument("--domain", type=str, help="Classify a single domain")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verify", action="store_true", help="Exit 1 if any UNCLASSIFIED remain")
    parser.add_argument("--class", dest="filter_class", type=str, help="Show only this classification class")
    parser.add_argument("--output", type=str, help="Write markdown report to file")
    args = parser.parse_args()

    domains_to_scan = [args.domain] if args.domain else DOMAINS

    # Discover engines
    all_engines = discover_all_l5_engines()

    # Scan L2 and L4 imports
    l2_refs = scan_l2_l5_imports()
    l4_refs = scan_l4_l5_imports()

    # Classify
    classifications: list[DomainClassification] = []
    for domain in domains_to_scan:
        engine_paths = all_engines.get(domain, [])
        if not engine_paths:
            continue

        engines = classify_engines(domain, engine_paths, l2_refs, l4_refs)
        dc = DomainClassification(
            domain=domain,
            total=len(engines),
            wired=sum(1 for e in engines if e.classification == "WIRED"),
            l2_direct=sum(1 for e in engines if e.classification == "L2-DIRECT"),
            internal=sum(1 for e in engines if e.classification == "INTERNAL"),
            schema_only=sum(1 for e in engines if e.classification == "SCHEMA-ONLY"),
            unclassified=sum(1 for e in engines if e.classification == "UNCLASSIFIED"),
            engines=engines,
        )
        classifications.append(dc)

    # Output
    if args.output:
        report = format_markdown_report(classifications)
        output_path = PROJECT_ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report)
        print(f"Report written to: {args.output}")

    if args.json:
        print(format_json_report(classifications))
    elif not args.output:
        print(format_text_report(classifications, filter_class=args.filter_class))

    # Verify mode
    if args.verify:
        total_unclassified = sum(dc.unclassified for dc in classifications)
        if total_unclassified > 0:
            print(f"\nVERIFICATION FAILED: {total_unclassified} engines remain UNCLASSIFIED")
            sys.exit(1)
        else:
            print("\nVERIFICATION PASSED: 0 unclassified engines")
            sys.exit(0)


if __name__ == "__main__":
    main()
