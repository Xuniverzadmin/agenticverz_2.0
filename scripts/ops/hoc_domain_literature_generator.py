#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Domain literature generator — extracts AST metadata from L5/L6/L7 files for keep/modify/quarantine evaluation
# artifact_class: CODE

"""
HOC Domain Literature Generator

Generates detailed .md literature files for every Python file under
hoc/cus/{domain}/ at L5, L6, and L7 layers. Output supports
keep/modify/quarantine evaluation decisions.

Uses AST extraction patterns consistent with hoc_spine_study_validator.py.

Usage:
    # Generate all L5/L6/L7 literature
    python3 scripts/ops/hoc_domain_literature_generator.py --generate

    # Single domain
    python3 scripts/ops/hoc_domain_literature_generator.py --generate --domain policies

    # Single layer
    python3 scripts/ops/hoc_domain_literature_generator.py --generate --layer L5

    # Output directory (default: literature/hoc_domain/)
    python3 scripts/ops/hoc_domain_literature_generator.py --generate --output-dir literature/hoc_domain/

    # JSON summary (for tooling)
    python3 scripts/ops/hoc_domain_literature_generator.py --json

    # Regenerate index only
    python3 scripts/ops/hoc_domain_literature_generator.py --index
"""

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUS_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc" / "cus"
MODELS_ROOT = PROJECT_ROOT / "backend" / "app" / "models"
DEFAULT_OUTPUT = PROJECT_ROOT / "literature" / "hoc_domain"

# Domains to scan (alphabetical)
ALL_DOMAINS = [
    "account", "activity", "analytics", "api_keys", "apis",
    "controls", "docs", "incidents", "integrations", "logs",
    "overview", "policies",
]

# L5 folder prefixes to include
L5_PREFIXES = (
    "L5_engines", "L5_schemas", "L5_support", "L5_controls",
    "L5_notifications", "L5_vault", "L5_lifecycle", "L5_workflow",
    "L5_utils", "L5_ui",
)

# Header keys to extract
HEADER_KEYS = (
    "Layer", "AUDIENCE", "Role", "Product", "Callers", "Reference",
    "Allowed Imports", "Forbidden Imports", "Contract",
)

# Stdlib prefixes (skip in import classification)
STDLIB_PREFIXES = {
    "abc", "argparse", "ast", "asyncio", "base64", "collections",
    "contextlib", "copy", "dataclasses", "datetime", "decimal", "enum",
    "functools", "hashlib", "hmac", "inspect", "io", "itertools", "json",
    "logging", "math", "os", "pathlib", "re", "secrets", "struct",
    "sys", "threading", "time", "traceback", "typing", "unittest",
    "urllib", "uuid", "textwrap", "string", "operator", "numbers",
}

# Layer label mapping for folder names
FOLDER_LAYER_LABEL = {
    "L5_engines": "L5 — Domain Engine",
    "L5_schemas": "L5 — Domain Schema",
    "L5_support": "L5 — Domain Support",
    "L5_controls": "L5 — Domain Controls",
    "L5_notifications": "L5 — Domain Notifications",
    "L5_vault": "L5 — Domain Vault",
    "L5_lifecycle": "L5 — Lifecycle",
    "L5_workflow": "L5 — Workflow",
    "L5_utils": "L5 — Utils",
    "L5_ui": "L5 — UI",
    "L6_drivers": "L6 — Domain Driver",
}


# ---------------------------------------------------------------------------
# File Discovery
# ---------------------------------------------------------------------------


def discover_files(
    domains: list[str] | None = None,
    layer_filter: str | None = None,
) -> list[dict[str, str]]:
    """Walk L5/L6/L7 dirs, return list of {path, domain, layer, folder}."""
    targets = domains or ALL_DOMAINS
    results: list[dict[str, str]] = []

    for domain in targets:
        domain_dir = CUS_ROOT / domain
        if not domain_dir.is_dir():
            continue

        # Recursively find all .py files under L5_*/L6_drivers
        for child in sorted(domain_dir.iterdir()):
            if not child.is_dir():
                continue
            folder_name = child.name

            is_l5 = folder_name.startswith("L5_")
            is_l6 = folder_name == "L6_drivers"

            if not is_l5 and not is_l6:
                continue

            if layer_filter:
                if layer_filter == "L5" and not is_l5:
                    continue
                if layer_filter == "L6" and not is_l6:
                    continue

            for pyfile in sorted(child.rglob("*.py")):
                if pyfile.name == "__init__.py":
                    continue
                results.append({
                    "path": str(pyfile),
                    "domain": domain,
                    "layer": "L5" if is_l5 else "L6",
                    "folder": folder_name,
                    "subfolder": str(pyfile.relative_to(child).parent),
                })

    # L7 Models
    if layer_filter is None or layer_filter == "L7":
        if MODELS_ROOT.is_dir():
            for pyfile in sorted(MODELS_ROOT.glob("*.py")):
                if pyfile.name == "__init__.py":
                    continue
                results.append({
                    "path": str(pyfile),
                    "domain": "_models",
                    "layer": "L7",
                    "folder": "models",
                    "subfolder": ".",
                })

    return results


# ---------------------------------------------------------------------------
# AST Extraction
# ---------------------------------------------------------------------------


def get_annotation_str(node: ast.expr | None) -> str:
    """Convert an AST annotation node to a string."""
    if node is None:
        return ""
    return ast.unparse(node)


def extract_header_metadata(source: str) -> dict[str, str]:
    """Parse # Key: Value header lines from file top."""
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


def extract_function_calls(node: ast.AST) -> list[str]:
    """Extract outbound function call names from a function body."""
    calls: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    return sorted(set(calls))


def extract_function_info(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    """Extract metadata from a function/method definition."""
    params = []
    for arg in node.args.args:
        if arg.arg in ("self", "cls"):
            continue
        p: dict[str, str] = {"name": arg.arg}
        if arg.annotation:
            p["type"] = get_annotation_str(arg.annotation)
        params.append(p)
    if node.args.vararg:
        p = {"name": f"*{node.args.vararg.arg}"}
        if node.args.vararg.annotation:
            p["type"] = get_annotation_str(node.args.vararg.annotation)
        params.append(p)
    if node.args.kwarg:
        p = {"name": f"**{node.args.kwarg.arg}"}
        if node.args.kwarg.annotation:
            p["type"] = get_annotation_str(node.args.kwarg.annotation)
        params.append(p)

    return {
        "name": node.name,
        "async": isinstance(node, ast.AsyncFunctionDef),
        "docstring": ast.get_docstring(node) or "",
        "params": params,
        "return_type": get_annotation_str(node.returns),
        "decorators": [ast.unparse(d) for d in node.decorator_list],
        "calls": extract_function_calls(node),
    }


def extract_class_info(node: ast.ClassDef) -> dict[str, Any]:
    """Extract metadata from a class definition."""
    methods = []
    class_vars = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(extract_function_info(item))
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            cv: dict[str, str] = {"name": item.target.id}
            if item.annotation:
                cv["type"] = get_annotation_str(item.annotation)
            class_vars.append(cv)

    return {
        "name": node.name,
        "bases": [ast.unparse(b) for b in node.bases],
        "docstring": ast.get_docstring(node) or "",
        "methods": methods,
        "class_vars": class_vars,
    }


def extract_imports(tree: ast.Module) -> list[str]:
    """Extract all import module paths."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def extract_module_attributes(tree: ast.Module) -> list[dict[str, str]]:
    """Extract module-level constants and assignments."""
    attrs = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    attrs.append({"name": target.id, "line": str(node.lineno)})
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            a: dict[str, str] = {"name": node.target.id, "line": str(node.lineno)}
            if node.annotation:
                a["type"] = get_annotation_str(node.annotation)
            attrs.append(a)
    return attrs


def classify_imports(imports: list[str], current_domain: str) -> dict[str, list[str]]:
    """Categorize imports into layer buckets."""
    cats: dict[str, list[str]] = {
        "l5_engine": [],
        "l5_schema": [],
        "l6_driver": [],
        "l7_model": [],
        "cross_domain": [],
        "external": [],
    }
    for imp in imports:
        top = imp.split(".")[0]
        if top in STDLIB_PREFIXES:
            continue

        if "L5_engines" in imp or "L5_support" in imp or "L5_controls" in imp or "L5_notifications" in imp or "L5_vault" in imp:
            cats["l5_engine"].append(imp)
            # Check cross-domain
            if "hoc.cus." in imp or "hoc/cus/" in imp:
                parts = imp.split(".")
                for i, part in enumerate(parts):
                    if part == "cus" and i + 1 < len(parts):
                        if parts[i + 1] != current_domain:
                            cats["cross_domain"].append(imp)
                        break
        elif "L5_schemas" in imp:
            cats["l5_schema"].append(imp)
        elif "L6_drivers" in imp:
            cats["l6_driver"].append(imp)
            if "hoc.cus." in imp:
                parts = imp.split(".")
                for i, part in enumerate(parts):
                    if part == "cus" and i + 1 < len(parts):
                        if parts[i + 1] != current_domain:
                            cats["cross_domain"].append(imp)
                        break
        elif imp.startswith("app.models"):
            cats["l7_model"].append(imp)
        elif imp.startswith("app.") or imp.startswith("fastapi") or imp.startswith("sqlmodel") or imp.startswith("sqlalchemy") or imp.startswith("pydantic"):
            cats["external"].append(imp)
        elif top not in STDLIB_PREFIXES:
            cats["external"].append(imp)

    # Deduplicate
    for k in cats:
        cats[k] = sorted(set(cats[k]))
    return cats


def extract_file_metadata(filepath: str, domain: str, layer: str, folder: str) -> dict[str, Any] | None:
    """Full AST extraction for a single file."""
    path = Path(filepath)
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  WARN: Cannot read {filepath}: {e}", file=sys.stderr)
        return None

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        print(f"  WARN: Syntax error in {filepath}: {e}", file=sys.stderr)
        return None

    header = extract_header_metadata(source)
    module_docstring = ast.get_docstring(tree) or ""

    functions = []
    classes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(extract_function_info(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(extract_class_info(node))

    raw_imports = extract_imports(tree)
    import_cats = classify_imports(raw_imports, domain)
    attributes = extract_module_attributes(tree)

    try:
        rel_path = path.relative_to(PROJECT_ROOT)
    except ValueError:
        rel_path = path

    return {
        "filepath": filepath,
        "rel_path": str(rel_path),
        "filename": path.stem,
        "domain": domain,
        "layer": layer,
        "folder": folder,
        "header": header,
        "module_docstring": module_docstring,
        "functions": functions,
        "classes": classes,
        "imports": import_cats,
        "attributes": attributes,
    }


# ---------------------------------------------------------------------------
# Markdown Generation
# ---------------------------------------------------------------------------


def _build_signature(fn: dict[str, Any]) -> str:
    """Build a function signature string."""
    params = []
    for p in fn["params"]:
        if p.get("type"):
            params.append(f"{p['name']}: {p['type']}")
        else:
            params.append(p["name"])
    ret = f" -> {fn['return_type']}" if fn.get("return_type") else ""
    return f"{fn['name']}({', '.join(params)}){ret}"


def _md_name(domain: str, folder: str, filename: str) -> str:
    """Generate the markdown filename stem."""
    if domain == "_models":
        return f"hoc_models_{filename}"
    return f"hoc_cus_{domain}_{folder}_{filename}"


def generate_file_markdown(meta: dict[str, Any]) -> str:
    """Generate the full .md content for a single file."""
    md_name = _md_name(meta["domain"], meta["folder"], meta["filename"])
    header = meta["header"]
    layer_label = header.get("layer", FOLDER_LAYER_LABEL.get(meta["folder"], f"{meta['layer']} — {meta['folder']}"))
    audience = header.get("audience", "CUSTOMER" if meta["domain"] != "_models" else "SHARED")
    domain_display = meta["domain"] if meta["domain"] != "_models" else "shared"

    lines = [
        f"# {md_name}",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Path | `{meta['rel_path']}` |",
        f"| Layer | {layer_label} |",
        f"| Domain | {domain_display} |",
        f"| Audience | {audience} |",
        "| Artifact Class | CODE |",
        "",
    ]

    # Description
    lines.append("## Description")
    lines.append("")
    role = header.get("role", "")
    if role:
        lines.append(role)
    elif meta["module_docstring"]:
        lines.append(meta["module_docstring"].split("\n")[0])
    else:
        lines.append("_No description available._")
    lines.append("")

    # Intent
    lines.append("## Intent")
    lines.append("")
    if role:
        lines.append(f"**Role:** {role}")
    if header.get("reference"):
        lines.append(f"**Reference:** {header['reference']}")
    if header.get("callers"):
        lines.append(f"**Callers:** {header['callers']}")
    if not role and not header.get("reference"):
        lines.append("_No intent metadata in file header._")
    lines.append("")

    # Purpose
    lines.append("## Purpose")
    lines.append("")
    if meta["module_docstring"]:
        first_para = meta["module_docstring"].split("\n\n")[0]
        lines.append(first_para)
    else:
        lines.append("_No module docstring._")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Functions
    if meta["functions"]:
        lines.append("## Functions")
        lines.append("")
        for fn in meta["functions"]:
            sig = _build_signature(fn)
            prefix = "async " if fn.get("async") else ""
            lines.append(f"### `{prefix}{sig}`")
            lines.append(f"- **Async:** {'Yes' if fn.get('async') else 'No'}")
            if fn["decorators"]:
                lines.append(f"- **Decorators:** {', '.join('@' + d for d in fn['decorators'])}")
            if fn["docstring"]:
                doc_lines = fn["docstring"].split("\n")[:3]
                lines.append(f"- **Docstring:** {' '.join(l.strip() for l in doc_lines)}")
            else:
                lines.append("- **Docstring:** _None_")
            if fn["calls"]:
                lines.append(f"- **Calls:** {', '.join(fn['calls'][:20])}")
            lines.append("")

    # Classes
    if meta["classes"]:
        lines.append("## Classes")
        lines.append("")
        for cls in meta["classes"]:
            bases_str = f"({', '.join(cls['bases'])})" if cls["bases"] else ""
            lines.append(f"### `{cls['name']}{bases_str}`")
            if cls["docstring"]:
                lines.append(f"- **Docstring:** {cls['docstring'].split(chr(10))[0]}")
            else:
                lines.append("- **Docstring:** _None_")
            if cls["methods"]:
                method_names = [m["name"] for m in cls["methods"]]
                lines.append(f"- **Methods:** {', '.join(method_names)}")
            if cls["class_vars"]:
                cv_strs = []
                for cv in cls["class_vars"]:
                    if cv.get("type"):
                        cv_strs.append(f"{cv['name']}: {cv['type']}")
                    else:
                        cv_strs.append(cv["name"])
                lines.append(f"- **Class Variables:** {', '.join(cv_strs)}")
            lines.append("")

    # Attributes
    if meta["attributes"]:
        lines.append("## Attributes")
        lines.append("")
        for attr in meta["attributes"]:
            type_str = f": {attr['type']}" if attr.get("type") else ""
            lines.append(f"- `{attr['name']}{type_str}` (line {attr['line']})")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Import Analysis
    imports = meta["imports"]
    lines.append("## Import Analysis")
    lines.append("")
    lines.append("| Category | Imports |")
    lines.append("|----------|---------|")
    cat_labels = {
        "l5_engine": "L5 Engine",
        "l5_schema": "L5 Schema",
        "l6_driver": "L6 Driver",
        "l7_model": "L7 Model",
        "cross_domain": "Cross-Domain",
        "external": "External",
    }
    for cat_key, label in cat_labels.items():
        imps = imports.get(cat_key, [])
        if imps:
            lines.append(f"| {label} | {', '.join(f'`{i}`' for i in imps)} |")
    if not any(imports.get(k) for k in cat_labels):
        lines.append("| _None_ | Pure stdlib |")
    lines.append("")

    # Callers
    lines.append("## Callers")
    lines.append("")
    callers = header.get("callers", "")
    if callers:
        lines.append(callers)
    else:
        lines.append("_Not declared in file header._")
    lines.append("")

    # Export Contract
    lines.append("## Export Contract")
    lines.append("")
    lines.append("```yaml")
    lines.append("exports:")

    if meta["functions"]:
        lines.append("  functions:")
        for fn in meta["functions"]:
            if fn["name"].startswith("_"):
                continue
            sig = _build_signature(fn)
            prefix = "async " if fn.get("async") else ""
            lines.append(f"    - name: {fn['name']}")
            lines.append(f'      signature: "{prefix}{sig}"')
    else:
        lines.append("  functions: []")

    if meta["classes"]:
        lines.append("  classes:")
        for cls in meta["classes"]:
            lines.append(f"    - name: {cls['name']}")
            public_methods = [m["name"] for m in cls["methods"] if not m["name"].startswith("_")]
            if public_methods:
                lines.append(f"      methods: [{', '.join(public_methods)}]")
            else:
                lines.append("      methods: []")
    else:
        lines.append("  classes: []")

    lines.append("```")
    lines.append("")

    # Evaluation Notes
    lines.append("## Evaluation Notes")
    lines.append("")
    lines.append("- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED")
    lines.append("- **Rationale:** ---")
    lines.append("")

    return "\n".join(lines)


def generate_domain_summary(domain: str, file_metas: list[dict[str, Any]]) -> str:
    """Generate _summary.md for a domain."""
    lines = [
        f"# {domain.title()} — Domain Summary",
        "",
        f"**Domain:** {domain}  ",
        f"**Total files:** {len(file_metas)}",
        "",
        "---",
        "",
    ]

    # Group by folder
    by_folder: dict[str, list[dict[str, Any]]] = {}
    for m in file_metas:
        by_folder.setdefault(m["folder"], []).append(m)

    # Layer counts
    lines.append("## Layer Breakdown")
    lines.append("")
    lines.append("| Folder | Files |")
    lines.append("|--------|-------|")
    for folder in sorted(by_folder.keys()):
        lines.append(f"| {folder} | {len(by_folder[folder])} |")
    lines.append("")

    # File inventory
    lines.append("## File Inventory")
    lines.append("")
    lines.append("| File | Folder | Functions | Classes | Disposition |")
    lines.append("|------|--------|-----------|---------|-------------|")

    for m in sorted(file_metas, key=lambda x: (x["folder"], x["filename"])):
        md_name = _md_name(m["domain"], m["folder"], m["filename"])
        fn_count = len(m["functions"])
        cls_count = len(m["classes"])
        link = f"[{m['filename']}.py]({m['folder']}/{md_name}.md)"
        lines.append(f"| {link} | {m['folder']} | {fn_count} | {cls_count} | _pending_ |")

    lines.append("")

    # Import health
    cross_domain_files = [m for m in file_metas if m["imports"].get("cross_domain")]
    if cross_domain_files:
        lines.append("## Cross-Domain Imports")
        lines.append("")
        for m in cross_domain_files:
            lines.append(f"- `{m['filename']}.py`: {', '.join(m['imports']['cross_domain'])}")
        lines.append("")

    return "\n".join(lines)


def generate_index(all_metas: list[dict[str, Any]]) -> str:
    """Generate master INDEX.md."""
    by_domain: dict[str, list[dict[str, Any]]] = {}
    for m in all_metas:
        by_domain.setdefault(m["domain"], []).append(m)

    total = len(all_metas)
    domain_count = len(by_domain)

    lines = [
        "# HOC Domain Literature — Master Index",
        "",
        f"**Total files:** {total}  ",
        f"**Domains:** {domain_count}  ",
        "**Generator:** `scripts/ops/hoc_domain_literature_generator.py`",
        "",
        "---",
        "",
        "## Navigation",
        "",
        "| Domain | L5 | L6 | L7 | Total |",
        "|--------|----|----|----|-------|",
    ]

    for domain in sorted(by_domain.keys()):
        metas = by_domain[domain]
        l5 = sum(1 for m in metas if m["layer"] == "L5")
        l6 = sum(1 for m in metas if m["layer"] == "L6")
        l7 = sum(1 for m in metas if m["layer"] == "L7")
        display = domain if domain != "_models" else "_models (L7)"
        link = f"[{display}]({domain}/_summary.md)"
        lines.append(f"| {link} | {l5} | {l6} | {l7} | {len(metas)} |")

    lines.append("")

    # Per-domain sections
    for domain in sorted(by_domain.keys()):
        metas = by_domain[domain]
        display = domain.title() if domain != "_models" else "Models (L7)"
        lines.append(f"## {display}")
        lines.append("")
        lines.append(f"[Domain Summary]({domain}/_summary.md)")
        lines.append("")

        by_folder: dict[str, list[dict[str, Any]]] = {}
        for m in metas:
            by_folder.setdefault(m["folder"], []).append(m)

        for folder in sorted(by_folder.keys()):
            lines.append(f"### {folder}")
            lines.append("")
            for m in sorted(by_folder[folder], key=lambda x: x["filename"]):
                md_name = _md_name(m["domain"], m["folder"], m["filename"])
                role = m["header"].get("role", "")
                short = role[:70] if role else "_no role declared_"
                lines.append(f"- [{m['filename']}.py]({domain}/{folder}/{md_name}.md) — {short}")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Output Helpers
# ---------------------------------------------------------------------------


def _output_path(output_dir: Path, meta: dict[str, Any]) -> Path:
    """Compute output .md path for a file metadata dict."""
    md_name = _md_name(meta["domain"], meta["folder"], meta["filename"])
    return output_dir / meta["domain"] / meta["folder"] / f"{md_name}.md"


def generate_all(
    output_dir: Path,
    domains: list[str] | None = None,
    layer_filter: str | None = None,
) -> dict[str, Any]:
    """Generate all literature files. Returns summary stats."""
    files = discover_files(domains=domains, layer_filter=layer_filter)
    print(f"Discovered {len(files)} source files")

    all_metas: list[dict[str, Any]] = []
    errors = 0

    for i, f in enumerate(files):
        meta = extract_file_metadata(f["path"], f["domain"], f["layer"], f["folder"])
        if meta is None:
            errors += 1
            continue
        all_metas.append(meta)

        md_content = generate_file_markdown(meta)
        out_path = _output_path(output_dir, meta)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_content, encoding="utf-8")

        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/{len(files)}...")

    print(f"Generated {len(all_metas)} literature files ({errors} errors)")

    # Domain summaries
    by_domain: dict[str, list[dict[str, Any]]] = {}
    for m in all_metas:
        by_domain.setdefault(m["domain"], []).append(m)

    for domain, metas in by_domain.items():
        summary = generate_domain_summary(domain, metas)
        summary_path = output_dir / domain / "_summary.md"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary, encoding="utf-8")
        print(f"  Summary: {domain}/ ({len(metas)} files)")

    # Master index
    if not domains or len(by_domain) > 1:
        index_content = generate_index(all_metas)
        index_path = output_dir / "INDEX.md"
        index_path.write_text(index_content, encoding="utf-8")
        print(f"  INDEX.md generated")

    return {
        "total_files": len(all_metas),
        "errors": errors,
        "domains": {d: len(m) for d, m in by_domain.items()},
        "by_layer": {
            "L5": sum(1 for m in all_metas if m["layer"] == "L5"),
            "L6": sum(1 for m in all_metas if m["layer"] == "L6"),
            "L7": sum(1 for m in all_metas if m["layer"] == "L7"),
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="HOC Domain Literature Generator — L5/L6/L7 file documentation"
    )
    parser.add_argument("--generate", action="store_true",
                        help="Generate all literature files")
    parser.add_argument("--domain", type=str,
                        help="Process only this domain")
    parser.add_argument("--layer", type=str, choices=["L5", "L6", "L7"],
                        help="Process only this layer")
    parser.add_argument("--output-dir", type=str,
                        help=f"Output directory (default: {DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON summary to stdout")
    parser.add_argument("--index", action="store_true",
                        help="Regenerate INDEX.md only")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT
    domains = [args.domain] if args.domain else None

    if args.json:
        files = discover_files(domains=domains, layer_filter=args.layer)
        all_metas = []
        for f in files:
            meta = extract_file_metadata(f["path"], f["domain"], f["layer"], f["folder"])
            if meta:
                all_metas.append(meta)

        by_domain: dict[str, int] = {}
        for m in all_metas:
            by_domain[m["domain"]] = by_domain.get(m["domain"], 0) + 1

        result = {
            "total_files": len(all_metas),
            "domains": by_domain,
            "by_layer": {
                "L5": sum(1 for m in all_metas if m["layer"] == "L5"),
                "L6": sum(1 for m in all_metas if m["layer"] == "L6"),
                "L7": sum(1 for m in all_metas if m["layer"] == "L7"),
            },
        }
        json.dump(result, sys.stdout, indent=2)
        print()
        return

    if args.index:
        files = discover_files(domains=domains, layer_filter=args.layer)
        all_metas = []
        for f in files:
            meta = extract_file_metadata(f["path"], f["domain"], f["layer"], f["folder"])
            if meta:
                all_metas.append(meta)
        index_content = generate_index(all_metas)
        index_path = output_dir / "INDEX.md"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(index_content, encoding="utf-8")
        print(f"INDEX.md written to {index_path}")
        return

    if args.generate:
        print("=" * 60)
        print("HOC Domain Literature Generator")
        print("=" * 60)
        print()
        stats = generate_all(output_dir, domains=domains, layer_filter=args.layer)
        print()
        print("=" * 60)
        print(f"Total: {stats['total_files']} files | Errors: {stats['errors']}")
        print(f"L5: {stats['by_layer']['L5']} | L6: {stats['by_layer']['L6']} | L7: {stats['by_layer']['L7']}")
        print(f"Output: {output_dir}")
        print("=" * 60)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
