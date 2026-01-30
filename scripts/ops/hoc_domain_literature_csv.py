#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: CSV export of domain literature — crisp function/purpose + L4→L5→L6→L7 linkage chain
# artifact_class: CODE

"""
HOC Domain Literature CSV Generator

Reads all L5/L6/L7 Python source files and produces a single CSV with:
- File identity (domain, layer, folder, filename)
- Crisp purpose (from header Role or first docstring line)
- Function/class inventory
- Layer linkage: what this file imports from L5/L6/L7 (downward calls)
- Layer linkage: who imports this file (upward callers via ripgrep)
- Cross-domain imports
- Disposition column (for review)

Usage:
    python3 scripts/ops/hoc_domain_literature_csv.py
    python3 scripts/ops/hoc_domain_literature_csv.py --output literature/hoc_domain/LITERATURE_MATRIX.csv
    python3 scripts/ops/hoc_domain_literature_csv.py --domain policies
    python3 scripts/ops/hoc_domain_literature_csv.py --skip-callers   # faster, no ripgrep
"""

import argparse
import ast
import csv
import subprocess
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUS_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc" / "cus"
MODELS_ROOT = PROJECT_ROOT / "backend" / "app" / "models"
BACKEND_ROOT = PROJECT_ROOT / "backend"
DEFAULT_OUTPUT = PROJECT_ROOT / "literature" / "hoc_domain" / "LITERATURE_MATRIX.csv"

ALL_DOMAINS = [
    "account", "activity", "analytics", "api_keys", "apis",
    "controls", "docs", "incidents", "integrations", "logs",
    "overview", "policies",
]

HEADER_KEYS = (
    "Layer", "AUDIENCE", "Role", "Product", "Callers", "Reference",
    "Allowed Imports", "Forbidden Imports",
)

STDLIB_PREFIXES = {
    "abc", "argparse", "ast", "asyncio", "base64", "collections",
    "contextlib", "copy", "dataclasses", "datetime", "decimal", "enum",
    "functools", "hashlib", "hmac", "inspect", "io", "itertools", "json",
    "logging", "math", "os", "pathlib", "re", "secrets", "struct",
    "sys", "threading", "time", "traceback", "typing", "unittest",
    "urllib", "uuid", "textwrap", "string", "operator", "numbers",
}


# ---------------------------------------------------------------------------
# File Discovery
# ---------------------------------------------------------------------------


def discover_files(domains: list[str] | None = None) -> list[dict[str, str]]:
    """Walk L5/L6/L7 dirs."""
    targets = domains or ALL_DOMAINS
    results: list[dict[str, str]] = []

    for domain in targets:
        domain_dir = CUS_ROOT / domain
        if not domain_dir.is_dir():
            continue
        for child in sorted(domain_dir.iterdir()):
            if not child.is_dir():
                continue
            is_l5 = child.name.startswith("L5_")
            is_l6 = child.name == "L6_drivers"
            if not is_l5 and not is_l6:
                continue
            for pyfile in sorted(child.rglob("*.py")):
                if pyfile.name == "__init__.py":
                    continue
                results.append({
                    "path": str(pyfile),
                    "domain": domain,
                    "layer": "L5" if is_l5 else "L6",
                    "folder": child.name,
                })

    # L7
    if MODELS_ROOT.is_dir():
        for pyfile in sorted(MODELS_ROOT.glob("*.py")):
            if pyfile.name == "__init__.py":
                continue
            results.append({
                "path": str(pyfile),
                "domain": "_models",
                "layer": "L7",
                "folder": "models",
            })

    return results


# ---------------------------------------------------------------------------
# AST Extraction (lightweight — just what CSV needs)
# ---------------------------------------------------------------------------


def extract_header(source: str) -> dict[str, str]:
    """Parse header comment metadata."""
    meta: dict[str, str] = {}
    for line in source.splitlines()[:50]:
        line = line.strip()
        if not line.startswith("#"):
            if line and not line.startswith('"""') and not line.startswith("'''"):
                break
            continue
        content = line.lstrip("# ").strip()
        for key in HEADER_KEYS:
            if content.startswith(f"{key}:"):
                meta[key.lower().replace(" ", "_")] = content[len(key) + 1:].strip()
                break
    return meta


def extract_crisp_purpose(header: dict[str, str], docstring: str) -> str:
    """One-line purpose from Role header or first docstring line."""
    role = header.get("role", "")
    if role:
        return role.strip()
    if docstring:
        first = docstring.split("\n")[0].strip()
        if first:
            return first[:120]
    return ""


def extract_imports(tree: ast.Module) -> list[str]:
    """All import module paths."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def classify_imports(imports: list[str], current_domain: str) -> dict[str, list[str]]:
    """Classify into layer buckets. Returns short labels, not full paths."""
    cats: dict[str, list[str]] = {
        "calls_l5": [],
        "calls_l6": [],
        "calls_l7": [],
        "calls_l5_schema": [],
        "cross_domain": [],
        "external": [],
    }
    for imp in imports:
        top = imp.split(".")[0]
        if top in STDLIB_PREFIXES:
            continue

        # Determine the short module name (last segment)
        short = imp.rsplit(".", 1)[-1]

        if "L5_engines" in imp or "L5_support" in imp or "L5_controls" in imp or "L5_notifications" in imp or "L5_vault" in imp:
            cats["calls_l5"].append(short)
            # Cross-domain check
            if "hoc.cus." in imp:
                parts = imp.split(".")
                for i, part in enumerate(parts):
                    if part == "cus" and i + 1 < len(parts):
                        if parts[i + 1] != current_domain:
                            cats["cross_domain"].append(f"{parts[i+1]}/{short}")
                        break
        elif "L5_schemas" in imp:
            cats["calls_l5_schema"].append(short)
        elif "L6_drivers" in imp:
            cats["calls_l6"].append(short)
            if "hoc.cus." in imp:
                parts = imp.split(".")
                for i, part in enumerate(parts):
                    if part == "cus" and i + 1 < len(parts):
                        if parts[i + 1] != current_domain:
                            cats["cross_domain"].append(f"{parts[i+1]}/{short}")
                        break
        elif imp.startswith("app.models"):
            cats["calls_l7"].append(short)
        elif imp.startswith("app.") or imp.startswith("fastapi") or imp.startswith("sqlmodel") or imp.startswith("sqlalchemy") or imp.startswith("pydantic"):
            cats["external"].append(short)
        elif top not in STDLIB_PREFIXES:
            cats["external"].append(short)

    for k in cats:
        cats[k] = sorted(set(cats[k]))
    return cats


def extract_file_info(filepath: str, domain: str) -> dict[str, Any] | None:
    """Extract everything the CSV needs from one file."""
    path = Path(filepath)
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return None

    header = extract_header(source)
    docstring = ast.get_docstring(tree) or ""
    purpose = extract_crisp_purpose(header, docstring)

    # Count functions and classes, collect names
    fn_names = []
    cls_names = []
    async_count = 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            fn_names.append(node.name)
            async_count += 1
        elif isinstance(node, ast.FunctionDef):
            fn_names.append(node.name)
        elif isinstance(node, ast.ClassDef):
            cls_names.append(node.name)

    raw_imports = extract_imports(tree)
    import_cats = classify_imports(raw_imports, domain)
    line_count = len(source.splitlines())

    try:
        rel_path = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel_path = str(path)

    return {
        "rel_path": rel_path,
        "purpose": purpose,
        "header": header,
        "fn_names": fn_names,
        "fn_count": len(fn_names),
        "async_count": async_count,
        "cls_names": cls_names,
        "cls_count": len(cls_names),
        "imports": import_cats,
        "lines": line_count,
    }


# ---------------------------------------------------------------------------
# Caller Discovery (ripgrep)
# ---------------------------------------------------------------------------


def find_callers_bulk(files: list[dict[str, str]]) -> dict[str, list[str]]:
    """For each file, find who imports it. Returns {filepath: [caller_short_paths]}."""
    callers_map: dict[str, list[str]] = {}

    for f in files:
        path = Path(f["path"])
        stem = path.stem

        # Search by stem — matches imports referencing this module
        pattern = f"[./]{stem}[ .]"
        try:
            result = subprocess.run(
                ["grep", "-rl", "--include=*.py", "-E", pattern, str(BACKEND_ROOT)],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0 and result.stdout.strip():
                hits = []
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    if not line or line == f["path"]:
                        continue
                    try:
                        rel_hit = str(Path(line).relative_to(PROJECT_ROOT))
                    except ValueError:
                        rel_hit = line
                    hits.append(rel_hit)
                if hits:
                    callers_map[f["path"]] = sorted(hits)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return callers_map


def classify_caller_layer(caller_path: str) -> str:
    """Classify a caller path into a layer label."""
    if "hoc/api/facades/" in caller_path:
        return "L2.1"
    if "hoc/api/cus/" in caller_path:
        return "L2"
    if "/adapters/" in caller_path:
        return "L3"
    if "hoc_spine/" in caller_path or "L4_runtime/" in caller_path:
        return "L4"
    if "/L5_engines/" in caller_path or "/L5_support/" in caller_path or "/L5_controls/" in caller_path:
        return "L5"
    if "/L5_schemas/" in caller_path:
        return "L5s"
    if "/L6_drivers/" in caller_path:
        return "L6"
    if "app/models/" in caller_path:
        return "L7"
    return "?"


def summarize_callers(caller_paths: list[str]) -> str:
    """Produce a crisp caller summary like 'L2:policy_api, L4:orchestrator'."""
    entries = []
    for cp in caller_paths:
        layer = classify_caller_layer(cp)
        stem = Path(cp).stem
        entries.append(f"{layer}:{stem}")
    # Deduplicate and limit
    seen = set()
    unique = []
    for e in entries:
        if e not in seen:
            seen.add(e)
            unique.append(e)
    return " | ".join(unique[:10])


# ---------------------------------------------------------------------------
# CSV Generation
# ---------------------------------------------------------------------------


CSV_COLUMNS = [
    "domain",
    "layer",
    "folder",
    "filename",
    "rel_path",
    "lines",
    "purpose",
    "functions",
    "fn_count",
    "async_count",
    "classes",
    "cls_count",
    "calls_l5",
    "calls_l5_schema",
    "calls_l6",
    "calls_l7",
    "cross_domain",
    "external_deps",
    "called_by",
    "caller_layers",
    "header_callers",
    "header_allowed_imports",
    "header_forbidden_imports",
    "linkage_chain",
    "disposition",
]


def build_linkage_chain(layer: str, imports: dict[str, list[str]], callers_summary: str) -> str:
    """Build a crisp linkage string like 'L2:api → THIS(L5) → L6:driver → L7:model'."""
    parts = []

    # Upstream (who calls this)
    if callers_summary:
        # Extract unique layers from callers
        caller_layers = set()
        for entry in callers_summary.split(" | "):
            if ":" in entry:
                caller_layers.add(entry.split(":")[0])
        if caller_layers:
            parts.append(" + ".join(sorted(caller_layers)))

    # This file
    parts.append(f"THIS({layer})")

    # Downstream (what this calls)
    downstream = []
    if imports.get("calls_l5"):
        downstream.append("L5")
    if imports.get("calls_l5_schema"):
        downstream.append("L5s")
    if imports.get("calls_l6"):
        downstream.append("L6")
    if imports.get("calls_l7"):
        downstream.append("L7")

    if downstream:
        parts.append(" + ".join(downstream))

    return " → ".join(parts)


def generate_csv(
    output_path: Path,
    domains: list[str] | None = None,
    skip_callers: bool = False,
):
    """Main CSV generation."""
    files = discover_files(domains=domains)
    print(f"Discovered {len(files)} source files")

    # Extract metadata
    rows: list[dict[str, str]] = []
    file_infos: list[tuple[dict[str, str], dict[str, Any]]] = []

    for i, f in enumerate(files):
        info = extract_file_info(f["path"], f["domain"])
        if info is None:
            continue
        file_infos.append((f, info))
        if (i + 1) % 50 == 0:
            print(f"  Parsed {i + 1}/{len(files)}...")

    print(f"Parsed {len(file_infos)} files successfully")

    # Caller discovery
    callers_map: dict[str, list[str]] = {}
    if not skip_callers:
        print("Discovering callers (ripgrep)...")
        callers_map = find_callers_bulk(files)
        print(f"  {len(callers_map)} files have callers")
    else:
        print("Skipping caller discovery (--skip-callers)")

    # Build rows
    for f, info in file_infos:
        callers = callers_map.get(f["path"], [])
        callers_summary = summarize_callers(callers) if callers else ""
        caller_layers_set = set()
        for cp in callers:
            caller_layers_set.add(classify_caller_layer(cp))
        caller_layers_str = " + ".join(sorted(caller_layers_set)) if caller_layers_set else ""

        linkage = build_linkage_chain(f["layer"], info["imports"], callers_summary)

        row = {
            "domain": f["domain"],
            "layer": f["layer"],
            "folder": f["folder"],
            "filename": Path(f["path"]).stem,
            "rel_path": info["rel_path"],
            "lines": str(info["lines"]),
            "purpose": info["purpose"],
            "functions": " | ".join(info["fn_names"]) if info["fn_names"] else "",
            "fn_count": str(info["fn_count"]),
            "async_count": str(info["async_count"]),
            "classes": " | ".join(info["cls_names"]) if info["cls_names"] else "",
            "cls_count": str(info["cls_count"]),
            "calls_l5": " | ".join(info["imports"]["calls_l5"]),
            "calls_l5_schema": " | ".join(info["imports"]["calls_l5_schema"]),
            "calls_l6": " | ".join(info["imports"]["calls_l6"]),
            "calls_l7": " | ".join(info["imports"]["calls_l7"]),
            "cross_domain": " | ".join(info["imports"]["cross_domain"]),
            "external_deps": " | ".join(info["imports"]["external"]),
            "called_by": callers_summary,
            "caller_layers": caller_layers_str,
            "header_callers": info["header"].get("callers", ""),
            "header_allowed_imports": info["header"].get("allowed_imports", ""),
            "header_forbidden_imports": info["header"].get("forbidden_imports", ""),
            "linkage_chain": linkage,
            "disposition": "",
        }
        rows.append(row)

    # Sort: domain → layer → folder → filename
    rows.sort(key=lambda r: (r["domain"], r["layer"], r["folder"], r["filename"]))

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f"CSV written: {output_path}")
    print(f"  Rows: {len(rows)}")
    print(f"  Columns: {len(CSV_COLUMNS)}")

    # Summary stats
    by_layer = {}
    by_domain = {}
    for r in rows:
        by_layer[r["layer"]] = by_layer.get(r["layer"], 0) + 1
        by_domain[r["domain"]] = by_domain.get(r["domain"], 0) + 1

    print()
    print("By layer:")
    for layer in sorted(by_layer):
        print(f"  {layer}: {by_layer[layer]}")
    print()
    print("By domain:")
    for domain in sorted(by_domain):
        print(f"  {domain}: {by_domain[domain]}")

    # Linkage stats
    has_upstream = sum(1 for r in rows if r["called_by"])
    has_downstream_l6 = sum(1 for r in rows if r["calls_l6"])
    has_downstream_l7 = sum(1 for r in rows if r["calls_l7"])
    has_cross = sum(1 for r in rows if r["cross_domain"])
    orphans = sum(1 for r in rows if not r["called_by"] and r["layer"] != "L7")

    print()
    print("Linkage stats:")
    print(f"  Has upstream callers: {has_upstream}/{len(rows)}")
    print(f"  Calls L6 drivers:    {has_downstream_l6}")
    print(f"  Calls L7 models:     {has_downstream_l7}")
    print(f"  Cross-domain:        {has_cross}")
    print(f"  No callers found:    {orphans} (excluding L7)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="HOC Domain Literature CSV — crisp purpose + linkage chain"
    )
    parser.add_argument("--output", type=str,
                        help=f"Output CSV path (default: {DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--domain", type=str,
                        help="Process only this domain")
    parser.add_argument("--skip-callers", action="store_true",
                        help="Skip ripgrep caller discovery (faster)")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT
    domains = [args.domain] if args.domain else None

    print("=" * 60)
    print("HOC Domain Literature CSV Generator")
    print("=" * 60)
    print()

    generate_csv(output_path, domains=domains, skip_callers=args.skip_callers)

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
