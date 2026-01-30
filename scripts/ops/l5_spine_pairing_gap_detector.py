#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: L5 → HOC Spine pairing gap detector — finds L5 engines called directly by L2, not wired through L4
# artifact_class: CODE

"""
L5 → HOC Spine Pairing Gap Detector

Scans all L2 API files and L4 orchestrator files using AST to determine which
L5 engines are:
  - WIRED: Referenced through L4 orchestrator (correct path)
  - DIRECT: Called directly by L2 APIs (gap — should go through L4)
  - ORPHANED: Not referenced by L2 or L4

Usage:
    # Full scan across all domains
    python scripts/ops/l5_spine_pairing_gap_detector.py

    # Single domain
    python scripts/ops/l5_spine_pairing_gap_detector.py --domain policies

    # JSON output (for CI integration)
    python scripts/ops/l5_spine_pairing_gap_detector.py --json

    # Update literature pairing declarations with findings
    python scripts/ops/l5_spine_pairing_gap_detector.py --update-literature
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
LITERATURE_ROOT = PROJECT_ROOT / "literature" / "hoc_spine"

# Customer domains to scan
DOMAINS = [
    "policies", "general", "integrations", "logs", "analytics",
    "incidents", "account", "activity", "api_keys", "overview",
    "controls", "ops", "recovery",
]


@dataclass
class L5Reference:
    """A reference from an L2 or L4 file to an L5 engine."""
    source_file: str       # e.g., "hoc/api/cus/policies/policy.py"
    source_line: int       # line number
    domain: str            # e.g., "policies"
    engine_module: str     # e.g., "lessons_engine"
    imported_names: list[str] = field(default_factory=list)  # e.g., ["get_lessons_learned"]


@dataclass
class L5Engine:
    """An L5 engine file."""
    domain: str
    module_name: str       # e.g., "lessons_engine"
    file_path: str
    last_modified: str
    function_count: int = 0
    class_count: int = 0


@dataclass
class DomainReport:
    """Gap report for a single domain."""
    domain: str
    total_l5_engines: int = 0
    wired_via_l4: int = 0
    direct_l2_to_l5: int = 0
    orphaned: int = 0
    gaps: list[dict[str, str]] = field(default_factory=list)
    orphans: list[dict[str, str]] = field(default_factory=list)
    wired: list[dict[str, str]] = field(default_factory=list)


def _get_python_files(directory: Path) -> list[Path]:
    """Get all non-__init__ Python files in a directory recursively."""
    if not directory.exists():
        return []
    return sorted(
        p for p in directory.rglob("*.py")
        if p.name != "__init__.py"
    )


def _extract_l5_imports_from_file(filepath: Path) -> list[L5Reference]:
    """Extract all L5 engine imports from a Python file using AST."""
    try:
        source = filepath.read_text()
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    refs: list[L5Reference] = []
    rel_path = str(filepath.relative_to(PROJECT_ROOT))

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module is None:
            continue

        module = node.module

        # Match patterns like:
        #   app.hoc.cus.{domain}.L5_engines.{module}
        #   app.hoc.cus.{domain}.L5_support.{module}
        #   app.hoc.cus.{domain}.L5_controls.{module}
        m = re.match(
            r"app\.hoc\.cus\.(\w+)\.L5_(?:engines|support|controls)\.(\w+)",
            module,
        )
        if not m:
            # Also match shorter form without specific file
            m = re.match(
                r"app\.hoc\.cus\.(\w+)\.L5_(?:engines|support|controls)",
                module,
            )
            if m:
                domain = m.group(1)
                # The imported names ARE the engine modules
                for alias in node.names:
                    refs.append(L5Reference(
                        source_file=rel_path,
                        source_line=node.lineno,
                        domain=domain,
                        engine_module=alias.name,
                        imported_names=[alias.name],
                    ))
                continue

        if m:
            domain = m.group(1)
            engine_module = m.group(2)
            imported_names = [alias.name for alias in node.names]
            refs.append(L5Reference(
                source_file=rel_path,
                source_line=node.lineno,
                domain=domain,
                engine_module=engine_module,
                imported_names=imported_names,
            ))

    return refs


def _discover_l5_engines(domain: str) -> list[L5Engine]:
    """Discover all L5 engine files for a domain."""
    engines: list[L5Engine] = []
    domain_root = CUS_ROOT / domain

    for subdir_name in ("L5_engines", "L5_support", "L5_controls"):
        engine_dir = domain_root / subdir_name
        if not engine_dir.exists():
            continue
        for filepath in sorted(engine_dir.rglob("*.py")):
            if filepath.name == "__init__.py":
                continue

            # Count functions and classes
            func_count = 0
            class_count = 0
            try:
                source = filepath.read_text()
                tree = ast.parse(source, filename=str(filepath))
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_count += 1
                    elif isinstance(node, ast.ClassDef):
                        class_count += 1
            except (SyntaxError, UnicodeDecodeError):
                pass

            stat = filepath.stat()
            last_mod = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")

            engines.append(L5Engine(
                domain=domain,
                module_name=filepath.stem,
                file_path=str(filepath.relative_to(PROJECT_ROOT)),
                last_modified=last_mod,
                function_count=func_count,
                class_count=class_count,
            ))

    return engines


def scan_l2_imports(domain: str | None = None) -> list[L5Reference]:
    """Scan all L2 API files for L5 engine imports."""
    all_refs: list[L5Reference] = []

    if domain:
        search_dirs = [L2_API_ROOT / domain]
    else:
        search_dirs = [L2_API_ROOT / d for d in DOMAINS]

    for search_dir in search_dirs:
        for filepath in _get_python_files(search_dir):
            all_refs.extend(_extract_l5_imports_from_file(filepath))

    return all_refs


def scan_l4_imports(domain: str | None = None) -> list[L5Reference]:
    """Scan all L4 orchestrator/spine files for L5 engine imports."""
    all_refs: list[L5Reference] = []

    for filepath in _get_python_files(L4_SPINE_ROOT):
        refs = _extract_l5_imports_from_file(filepath)
        if domain:
            refs = [r for r in refs if r.domain == domain]
        all_refs.extend(refs)

    return all_refs


def compute_domain_report(
    domain: str,
    l5_engines: list[L5Engine],
    l2_refs: list[L5Reference],
    l4_refs: list[L5Reference],
) -> DomainReport:
    """Compute the gap report for a single domain."""
    report = DomainReport(domain=domain, total_l5_engines=len(l5_engines))

    # Build sets of engine module names referenced by L2 and L4
    l2_engine_names: set[str] = set()
    l4_engine_names: set[str] = set()

    for ref in l2_refs:
        if ref.domain == domain:
            l2_engine_names.add(ref.engine_module)

    for ref in l4_refs:
        if ref.domain == domain:
            l4_engine_names.add(ref.engine_module)

    all_engine_names = {e.module_name for e in l5_engines}

    # Wired: referenced by L4
    wired = l4_engine_names & all_engine_names
    # Direct gaps: referenced by L2 but NOT by L4
    direct = (l2_engine_names - l4_engine_names) & all_engine_names
    # Orphaned: not referenced by either
    orphaned = all_engine_names - l2_engine_names - l4_engine_names

    report.wired_via_l4 = len(wired)
    report.direct_l2_to_l5 = len(direct)
    report.orphaned = len(orphaned)

    # Build gap details
    for ref in l2_refs:
        if ref.domain == domain and ref.engine_module in direct:
            report.gaps.append({
                "l2_api_file": f"{ref.source_file}:{ref.source_line}",
                "l5_engine": f"{ref.engine_module}.py",
                "functions_called": ", ".join(ref.imported_names),
            })

    # Build wired details
    for ref in l4_refs:
        if ref.domain == domain and ref.engine_module in wired:
            report.wired.append({
                "l4_file": ref.source_file,
                "l5_engine": f"{ref.engine_module}.py",
            })

    # Build orphan details
    engine_map = {e.module_name: e for e in l5_engines}
    for name in sorted(orphaned):
        engine = engine_map.get(name)
        report.orphans.append({
            "l5_engine": f"{name}.py",
            "last_modified": engine.last_modified if engine else "unknown",
        })

    return report


def format_text_report(reports: list[DomainReport]) -> str:
    """Format domain reports as text."""
    lines = [
        "==============================================",
        "  L5 → HOC Spine Pairing Gap Report",
        f"  {datetime.now().strftime('%Y-%m-%d')}",
        "==============================================",
        "",
    ]

    total_engines = 0
    total_wired = 0
    total_direct = 0
    total_orphaned = 0

    for report in sorted(reports, key=lambda r: r.domain):
        if report.total_l5_engines == 0:
            continue

        total_engines += report.total_l5_engines
        total_wired += report.wired_via_l4
        total_direct += report.direct_l2_to_l5
        total_orphaned += report.orphaned

        lines.append(f"DOMAIN: {report.domain} ({report.total_l5_engines} L5 engines)")
        lines.append(f"  WIRED via L4:    {report.wired_via_l4}")
        lines.append(f"  DIRECT L2→L5:   {report.direct_l2_to_l5}")
        lines.append(f"  ORPHANED:        {report.orphaned}")
        lines.append("")

        if report.gaps:
            lines.append("  GAPS (L2 calls L5 directly, no L4 orchestrator):")
            lines.append(f"    | {'L2 API File':<40} | {'L5 Engine':<30} | {'Function Called':<30} |")
            lines.append(f"    |{'-'*40}--|{'-'*30}--|{'-'*30}--|")
            for gap in report.gaps:
                lines.append(
                    f"    | {gap['l2_api_file']:<40} | {gap['l5_engine']:<30} | {gap['functions_called']:<30} |"
                )
            lines.append("")

        if report.wired:
            lines.append("  WIRED (correctly routed through L4):")
            for w in report.wired:
                lines.append(f"    - {w['l5_engine']} via {w['l4_file']}")
            lines.append("")

        if report.orphans:
            lines.append("  ORPHANS (L5 engines with no L2 or L4 callers):")
            lines.append(f"    | {'L5 Engine':<40} | {'Last Modified':<15} |")
            lines.append(f"    |{'-'*40}--|{'-'*15}--|")
            for orphan in report.orphans:
                lines.append(
                    f"    | {orphan['l5_engine']:<40} | {orphan['last_modified']:<15} |"
                )
            lines.append("")

        lines.append("")

    lines.append("SUMMARY:")
    lines.append(f"  Total L5 engines:     {total_engines}")
    lines.append(f"  Wired via L4:         {total_wired}")
    lines.append(f"  Direct L2→L5 (gaps):  {total_direct}")
    lines.append(f"  Orphaned:             {total_orphaned}")
    lines.append("")

    return "\n".join(lines)


def format_json_report(reports: list[DomainReport]) -> str:
    """Format domain reports as JSON."""
    data = {
        "generated": datetime.now().isoformat(),
        "domains": [],
        "summary": {
            "total_l5_engines": 0,
            "wired_via_l4": 0,
            "direct_l2_to_l5": 0,
            "orphaned": 0,
        },
    }
    for report in sorted(reports, key=lambda r: r.domain):
        if report.total_l5_engines == 0:
            continue
        data["domains"].append({
            "domain": report.domain,
            "total_l5_engines": report.total_l5_engines,
            "wired_via_l4": report.wired_via_l4,
            "direct_l2_to_l5": report.direct_l2_to_l5,
            "orphaned": report.orphaned,
            "gaps": report.gaps,
            "orphans": report.orphans,
            "wired": report.wired,
        })
        data["summary"]["total_l5_engines"] += report.total_l5_engines
        data["summary"]["wired_via_l4"] += report.wired_via_l4
        data["summary"]["direct_l2_to_l5"] += report.direct_l2_to_l5
        data["summary"]["orphaned"] += report.orphaned

    return json.dumps(data, indent=2)


def update_literature(reports: list[DomainReport]) -> int:
    """Update L5 Pairing Declaration sections in literature .md files."""
    if not LITERATURE_ROOT.exists():
        print(f"ERROR: Literature directory not found: {LITERATURE_ROOT}")
        return 1

    # Build a mapping: spine_script -> list of domains/engines that reference it
    # For spine scripts, we need to check which L4 files reference which L5 engines
    # and map that back to the literature files

    # First, scan all L4 spine files and their L5 imports
    l4_refs = scan_l4_imports()

    # Group L4 refs by source file (spine script)
    spine_to_l5: dict[str, list[L5Reference]] = {}
    for ref in l4_refs:
        # Extract spine script name from source_file path
        # e.g., "backend/app/hoc/hoc_spine/orchestrator/run_governance_facade.py" -> "run_governance_facade"
        spine_script = Path(ref.source_file).stem
        spine_to_l5.setdefault(spine_script, []).append(ref)

    # Build domain gap sets from reports
    domain_gaps: dict[str, set[str]] = {}
    for report in reports:
        gap_engines = {g["l5_engine"].replace(".py", "") for g in report.gaps}
        domain_gaps[report.domain] = gap_engines

    updated_count = 0

    # Walk all literature .md files
    for md_path in sorted(LITERATURE_ROOT.rglob("*.md")):
        if md_path.name == "_summary.md" or md_path.name == "INDEX.md":
            continue

        script_name = md_path.stem
        content = md_path.read_text()

        if "## L5 Pairing Declaration" not in content:
            continue

        # Build pairing data for this spine script
        refs = spine_to_l5.get(script_name, [])
        serves_domains: set[str] = set()
        consumers: list[dict[str, Any]] = []

        for ref in refs:
            serves_domains.add(ref.domain)
            is_gap = ref.engine_module in domain_gaps.get(ref.domain, set())
            consumers.append({
                "domain": ref.domain,
                "engine": f"{ref.engine_module}.py",
                "wired": True,
                "gap": "" if not is_gap else "Also called directly by L2",
            })

        # Replace the L5 Pairing Declaration section
        pairing_yaml_lines = [
            "## L5 Pairing Declaration",
            "",
            "```yaml",
            "pairing:",
            f"  serves_domains: {sorted(serves_domains)}",
        ]

        if consumers:
            pairing_yaml_lines.append("  expected_l5_consumers:")
            for c in sorted(consumers, key=lambda x: (x["domain"], x["engine"])):
                pairing_yaml_lines.append(f"    - domain: {c['domain']}")
                pairing_yaml_lines.append(f"      engine: {c['engine']}")
                pairing_yaml_lines.append(f"      wired: {str(c['wired']).lower()}")
                if c["gap"]:
                    pairing_yaml_lines.append(f'      gap: "{c["gap"]}"')
        else:
            pairing_yaml_lines.append("  expected_l5_consumers: []")

        pairing_yaml_lines.append("  orchestrator_operations: []")
        pairing_yaml_lines.append("```")
        pairing_yaml_lines.append("")

        new_pairing = "\n".join(pairing_yaml_lines)

        # Replace the section using regex
        pattern = r"## L5 Pairing Declaration\n.*?(?=## |\Z)"
        new_content = re.sub(pattern, new_pairing + "\n", content, flags=re.DOTALL)

        if new_content != content:
            md_path.write_text(new_content)
            updated_count += 1
            print(f"Updated: {md_path.relative_to(PROJECT_ROOT)}")

    # Update _summary.md files with aggregate pairing data
    for folder_dir in sorted(LITERATURE_ROOT.iterdir()):
        if not folder_dir.is_dir():
            continue
        summary_path = folder_dir / "_summary.md"
        if not summary_path.exists():
            continue

        content = summary_path.read_text()
        if "## 6. L5 Pairing Aggregate" not in content:
            continue

        # Build aggregate table
        agg_lines = [
            "## 6. L5 Pairing Aggregate",
            "",
            "| Script | Serves Domains | Wired L5 Consumers | Gaps |",
            "|--------|----------------|--------------------|------|",
        ]

        for md_file in sorted(folder_dir.glob("*.md")):
            if md_file.name == "_summary.md":
                continue
            sname = md_file.stem
            refs = spine_to_l5.get(sname, [])
            domains = sorted({r.domain for r in refs})
            wired_count = len(refs)
            gap_count = sum(
                1 for r in refs
                if r.engine_module in domain_gaps.get(r.domain, set())
            )
            agg_lines.append(
                f"| {sname}.py | {', '.join(domains) or '_none_'} | {wired_count} | {gap_count} |"
            )

        agg_lines.append("")

        new_agg = "\n".join(agg_lines)
        pattern = r"## 6\. L5 Pairing Aggregate\n.*?(?=## |\Z)"
        new_content = re.sub(pattern, new_agg + "\n", content, flags=re.DOTALL)

        if new_content != content:
            summary_path.write_text(new_content)
            updated_count += 1
            print(f"Updated: {summary_path.relative_to(PROJECT_ROOT)}")

    print(f"\nTotal literature files updated: {updated_count}")
    return 0


BASELINE_PATH = PROJECT_ROOT / "docs" / "architecture" / "hoc" / "L2_L4_L5_BASELINE.json"


def load_baseline() -> dict[str, Any] | None:
    """Load the frozen baseline from JSON."""
    if not BASELINE_PATH.exists():
        return None
    try:
        return json.loads(BASELINE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def save_baseline(reports: list[DomainReport]) -> None:
    """Save the current state as the frozen baseline."""
    total_gaps = sum(r.direct_l2_to_l5 for r in reports)
    total_wired = sum(r.wired_via_l4 for r in reports)
    total_engines = sum(r.total_l5_engines for r in reports)
    total_orphaned = sum(r.orphaned for r in reports)

    # Capture per-domain gap details for regression detection
    domain_gaps: dict[str, list[str]] = {}
    for report in reports:
        if report.gaps:
            domain_gaps[report.domain] = [g["l5_engine"] for g in report.gaps]

    baseline = {
        "frozen_at": datetime.now().isoformat(),
        "phase": "C",
        "pin": "491",
        "summary": {
            "total_l5_engines": total_engines,
            "wired_via_l4": total_wired,
            "direct_l2_to_l5": total_gaps,
            "orphaned": total_orphaned,
        },
        "known_gaps": domain_gaps,
    }
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2) + "\n")
    print(f"Baseline saved to: {BASELINE_PATH.relative_to(PROJECT_ROOT)}")


def check_against_baseline(reports: list[DomainReport]) -> int:
    """Check current state against frozen baseline. Returns exit code."""
    baseline = load_baseline()
    if baseline is None:
        print("ERROR: No baseline found. Run with --freeze-baseline first.")
        return 2

    baseline_gaps = baseline["summary"]["direct_l2_to_l5"]
    current_gaps = sum(r.direct_l2_to_l5 for r in reports)

    # Collect current gap engines
    current_gap_engines: dict[str, list[str]] = {}
    for report in reports:
        if report.gaps:
            current_gap_engines[report.domain] = [g["l5_engine"] for g in report.gaps]

    known_gaps = baseline.get("known_gaps", {})

    # Find NEW gaps (not in baseline)
    new_gaps: list[str] = []
    for domain, engines in current_gap_engines.items():
        known = set(known_gaps.get(domain, []))
        for eng in engines:
            if eng not in known:
                new_gaps.append(f"{domain}/{eng}")

    print("L2-L4-L5 Freeze Check (Phase C)")
    print(f"  Baseline gaps: {baseline_gaps}")
    print(f"  Current gaps:  {current_gaps}")
    print(f"  New gaps:      {len(new_gaps)}")

    if new_gaps:
        print("")
        print("REGRESSION DETECTED — new L2→L5 direct imports:")
        for gap in new_gaps:
            print(f"  - {gap}")
        print("")
        print("Fix: Route through L4 operation registry before merging.")
        return 1

    if current_gaps > baseline_gaps:
        print("")
        print(f"REGRESSION: gap count increased ({baseline_gaps} → {current_gaps})")
        return 1

    print("  Status:        PASS (no new gaps)")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="L5 → HOC Spine Pairing Gap Detector"
    )
    parser.add_argument("--domain", type=str, help="Scan a single domain")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--update-literature",
        action="store_true",
        help="Update literature L5 Pairing Declaration sections",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check against frozen baseline (exit 0=pass, 1=regression, 2=no baseline)",
    )
    parser.add_argument(
        "--freeze-baseline",
        action="store_true",
        help="Save current state as the frozen baseline",
    )
    args = parser.parse_args()

    domains_to_scan = [args.domain] if args.domain else DOMAINS

    # Discover all L5 engines
    all_engines: dict[str, list[L5Engine]] = {}
    for domain in domains_to_scan:
        engines = _discover_l5_engines(domain)
        if engines:
            all_engines[domain] = engines

    # Scan L2 and L4 imports
    l2_refs = scan_l2_imports(args.domain)
    l4_refs = scan_l4_imports(args.domain)

    # Compute reports
    reports: list[DomainReport] = []
    for domain in domains_to_scan:
        engines = all_engines.get(domain, [])
        if not engines:
            continue
        report = compute_domain_report(domain, engines, l2_refs, l4_refs)
        reports.append(report)

    if args.freeze_baseline:
        save_baseline(reports)
        sys.exit(0)

    if args.check:
        sys.exit(check_against_baseline(reports))

    if args.update_literature:
        sys.exit(update_literature(reports))

    if args.json:
        print(format_json_report(reports))
    else:
        print(format_text_report(reports))


if __name__ == "__main__":
    main()
