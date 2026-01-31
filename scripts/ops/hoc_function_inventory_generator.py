#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Extract flat function inventory from L5/L6/L7 files — one row per function/method with caller/callee/side-effect metadata
# artifact_class: CODE

"""
HOC Function Inventory Generator

Produces one CSV row per function/method in L5/L6/L7 files. Reuses AST
patterns from hoc_domain_literature_generator.py.

Usage:
    python3 scripts/ops/hoc_function_inventory_generator.py
    python3 scripts/ops/hoc_function_inventory_generator.py --domain incidents
    python3 scripts/ops/hoc_function_inventory_generator.py --json
    python3 scripts/ops/hoc_function_inventory_generator.py --output literature/hoc_domain/FUNCTION_INVENTORY.csv
"""

import argparse
import ast
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any  # noqa: F401

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUS_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc" / "cus"
MODELS_ROOT = PROJECT_ROOT / "backend" / "app" / "models"
BACKEND_ROOT = PROJECT_ROOT / "backend"
HOC_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc"
L2_API_ROOT = HOC_ROOT / "api" / "cus"
L4_SPINE_ROOT = HOC_ROOT / "hoc_spine"
DEFAULT_OUTPUT = PROJECT_ROOT / "literature" / "hoc_domain" / "FUNCTION_INVENTORY.csv"

ALL_DOMAINS = [
    "account", "activity", "analytics", "api_keys", "apis",
    "controls", "docs", "incidents", "integrations", "logs",
    "overview", "policies",
]

STDLIB_PREFIXES = {
    "abc", "argparse", "ast", "asyncio", "base64", "collections",
    "contextlib", "copy", "dataclasses", "datetime", "decimal", "enum",
    "functools", "hashlib", "hmac", "inspect", "io", "itertools", "json",
    "logging", "math", "os", "pathlib", "re", "secrets", "struct",
    "sys", "threading", "time", "traceback", "typing", "unittest",
    "urllib", "uuid", "textwrap", "string", "operator", "numbers",
}

HEADER_KEYS = (
    "Layer", "AUDIENCE", "Role", "Product", "Callers", "Reference",
    "Allowed Imports", "Forbidden Imports",
)

CSV_COLUMNS = [
    "domain",
    "layer",
    "file",
    "symbol",
    "signature",
    "called_by",
    "calls",
    "imports",
    "side_effects",
    "async",
    "lines",
    "docstring",
]

# ---------------------------------------------------------------------------
# Side-effect detection patterns
# ---------------------------------------------------------------------------

DB_WRITE_PATTERNS = [
    "session.add", "session.commit", "session.flush", "session.delete",
    "session.execute", "session.merge", "session.bulk_save_objects",
    ".add(", ".commit(", ".flush(", ".delete(",
]

EXTERNAL_API_PATTERNS = [
    "httpx.", "requests.", "aiohttp.", "urllib.request",
    "client.get(", "client.post(", "client.put(", "client.delete(",
    "client.patch(",
]

FILE_IO_PATTERNS = [
    "open(", ".write(", ".read(", "pathlib.", "shutil.",
    "os.remove", "os.makedirs",
]


def detect_side_effects(source_lines: list[str]) -> str:
    """Classify side effects from function body source lines."""
    body = "\n".join(source_lines)
    effects = []

    for pattern in DB_WRITE_PATTERNS:
        if pattern in body:
            effects.append("db_write")
            break

    for pattern in EXTERNAL_API_PATTERNS:
        if pattern in body:
            effects.append("external_api")
            break

    for pattern in FILE_IO_PATTERNS:
        if pattern in body:
            effects.append("file_io")
            break

    return ",".join(effects) if effects else "pure"


# ---------------------------------------------------------------------------
# File Discovery (reused from literature generator)
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

    # L7 Models
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
# AST Extraction
# ---------------------------------------------------------------------------


def get_annotation_str(node: ast.expr | None) -> str:
    if node is None:
        return ""
    return ast.unparse(node)


def build_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Build a compact function signature."""
    params = []
    for arg in node.args.args:
        if arg.arg in ("self", "cls"):
            continue
        if arg.annotation:
            params.append(f"{arg.arg}: {get_annotation_str(arg.annotation)}")
        else:
            params.append(arg.arg)
    if node.args.vararg:
        params.append(f"*{node.args.vararg.arg}")
    if node.args.kwarg:
        params.append(f"**{node.args.kwarg.arg}")

    ret = f" -> {get_annotation_str(node.returns)}" if node.returns else ""
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}{node.name}({', '.join(params)}){ret}"


def extract_function_calls(node: ast.AST) -> list[str]:
    """Extract outbound function call names."""
    calls: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    return sorted(set(calls))


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


def extract_header_metadata(source: str) -> dict[str, str]:
    """Parse # Key: Value header lines."""
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


# ---------------------------------------------------------------------------
# Caller Discovery
# ---------------------------------------------------------------------------


def find_callers_for_file(filepath: Path) -> list[tuple[str, str]]:
    """Find who imports this file. Returns list of (caller_rel_path, caller_layer)."""
    stem = filepath.stem
    pattern = f"[./]{re.escape(stem)}[ .]"
    try:
        result = subprocess.run(
            ["grep", "-rl", "--include=*.py", "-E", pattern, str(BACKEND_ROOT)],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    callers = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line or line == str(filepath):
            continue
        try:
            rel = str(Path(line).relative_to(PROJECT_ROOT))
        except ValueError:
            rel = line

        layer = classify_caller_layer(rel)
        callers.append((rel, layer))
    return callers


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


# ---------------------------------------------------------------------------
# Main Extraction
# ---------------------------------------------------------------------------


def extract_functions_from_file(
    filepath: str, domain: str, layer: str, folder: str,
    callers: list[tuple[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Extract all functions/methods from a file as inventory rows."""
    path = Path(filepath)
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    source_lines = source.splitlines()
    raw_imports = extract_imports(tree)

    # Filter to non-stdlib imports
    file_imports = []
    for imp in raw_imports:
        top = imp.split(".")[0]
        if top not in STDLIB_PREFIXES:
            short = imp.rsplit(".", 1)[-1]
            file_imports.append(short)
    file_imports = sorted(set(file_imports))

    # Build called_by summary
    called_by_parts = []
    if callers:
        seen = set()
        for cp, cl in callers:
            entry = f"{cl}:{Path(cp).stem}"
            if entry not in seen:
                seen.add(entry)
                called_by_parts.append(entry)

    called_by_str = " | ".join(called_by_parts[:10])

    rows: list[dict[str, str]] = []

    def process_function(node: ast.FunctionDef | ast.AsyncFunctionDef, class_name: str = ""):
        symbol = f"{class_name}.{node.name}" if class_name else node.name
        sig = build_signature(node)
        calls = extract_function_calls(node)

        # Side-effect detection from source lines
        start = node.lineno - 1
        end = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start + 1
        body_lines = source_lines[start:end]
        side_effects = detect_side_effects(body_lines)

        doc = ast.get_docstring(node) or ""
        first_doc_line = doc.split("\n")[0].strip()[:150] if doc else ""

        fn_lines = end - start

        rows.append({
            "domain": domain,
            "layer": layer,
            "file": path.stem,
            "symbol": symbol,
            "signature": sig,
            "called_by": called_by_str,
            "calls": " | ".join(calls[:15]),
            "imports": " | ".join(file_imports),
            "side_effects": side_effects,
            "async": "yes" if isinstance(node, ast.AsyncFunctionDef) else "no",
            "lines": str(fn_lines),
            "docstring": first_doc_line,
        })

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            process_function(node)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    process_function(item, class_name=node.name)

    return rows


def generate_inventory(
    output_path: Path,
    domains: list[str] | None = None,
    as_json: bool = False,
) -> dict:
    """Generate the function inventory."""
    files = discover_files(domains=domains)
    print(f"Discovered {len(files)} source files")

    # Build caller map
    print("Discovering callers...")
    caller_map: dict[str, list[tuple[str, str]]] = {}
    for f in files:
        callers = find_callers_for_file(Path(f["path"]))
        if callers:
            caller_map[f["path"]] = callers

    print(f"  {len(caller_map)} files have callers")

    # Extract functions
    all_rows: list[dict[str, str]] = []
    for i, f in enumerate(files):
        callers = caller_map.get(f["path"])
        rows = extract_functions_from_file(
            f["path"], f["domain"], f["layer"], f["folder"], callers
        )
        all_rows.extend(rows)
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(files)} files...")

    all_rows.sort(key=lambda r: (r["domain"], r["layer"], r["file"], r["symbol"]))

    print(f"\nTotal function records: {len(all_rows)}")

    if as_json:
        result = {
            "total": len(all_rows),
            "by_domain": {},
            "by_layer": {},
            "rows": all_rows,
        }
        for r in all_rows:
            result["by_domain"][r["domain"]] = result["by_domain"].get(r["domain"], 0) + 1
            result["by_layer"][r["layer"]] = result["by_layer"].get(r["layer"], 0) + 1
        json.dump(result, sys.stdout, indent=2)
        print()
        return result

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    # Summary
    by_domain: dict[str, int] = {}
    by_layer: dict[str, int] = {}
    by_side: dict[str, int] = {}
    for r in all_rows:
        by_domain[r["domain"]] = by_domain.get(r["domain"], 0) + 1
        by_layer[r["layer"]] = by_layer.get(r["layer"], 0) + 1
        by_side[r["side_effects"]] = by_side.get(r["side_effects"], 0) + 1

    print(f"\nCSV written: {output_path}")
    print(f"  Rows: {len(all_rows)}")
    print("\nBy domain:")
    for d in sorted(by_domain):
        print(f"  {d}: {by_domain[d]}")
    print("\nBy layer:")
    for l in sorted(by_layer):
        print(f"  {l}: {by_layer[l]}")
    print("\nBy side_effects:")
    for s in sorted(by_side):
        print(f"  {s}: {by_side[s]}")

    return {"total": len(all_rows), "by_domain": by_domain}


def main():
    parser = argparse.ArgumentParser(
        description="HOC Function Inventory Generator — one row per function/method"
    )
    parser.add_argument("--output", "-o", type=str,
                        help=f"Output CSV path (default: {DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--domain", type=str, help="Process only this domain")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT
    domains = [args.domain] if args.domain else None

    print("=" * 60)
    print("HOC Function Inventory Generator")
    print("=" * 60)
    print()

    generate_inventory(output_path, domains=domains, as_json=args.json)

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
