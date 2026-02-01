#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: HOC Spine literature study validator — extracts function/class metadata from hoc_spine scripts
# artifact_class: CODE

"""
HOC Spine Study Validator

Extracts structured metadata from each Python file in hoc_spine/ using the ast module.
Outputs YAML (per file or bulk). Can validate existing literature files against source
to detect drift (new/removed functions).

Usage:
    # Extract metadata for a single file (YAML to stdout)
    python scripts/ops/hoc_spine_study_validator.py backend/app/hoc/cus/hoc_spine/authority/concurrent_runs.py

    # Extract all files to an output directory
    python scripts/ops/hoc_spine_study_validator.py --all --output-dir /tmp/spine_yaml

    # Validate literature against source (detect drift)
    python scripts/ops/hoc_spine_study_validator.py --validate literature/hoc_spine/

    # Generate markdown literature files from source
    python scripts/ops/hoc_spine_study_validator.py --generate --output-dir literature/hoc_spine/
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import Any

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPINE_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc" / "hoc_spine"

# Folder to layer mapping
FOLDER_LAYER = {
    "authority": "L4",
    "orchestrator": "L4",
    "services": "L5",
    "schemas": "L5",
    "drivers": "L6",
    "adapters": "L3",
    "consequences": "L5",
    "frontend": "L1",
    "mcp": "L4",
}

# Folder to component mapping
FOLDER_COMPONENT = {
    "authority": "Authority",
    "orchestrator": "Orchestrator",
    "services": "Services",
    "schemas": "Schemas",
    "drivers": "Drivers",
    "adapters": "Adapters",
    "consequences": "Consequences",
    "frontend": "Frontend",
    "mcp": "MCP",
}

# Folder governance knowledge — from Hybrid Reconciliation Artifact
FOLDER_SPEC: dict[str, dict[str, Any]] = {
    "orchestrator": {
        "purpose": (
            "Sole execution entry point from L2. Owns transaction boundaries, "
            "operation resolution, and execution order. No code runs without "
            "going through here."
        ),
        "what_belongs": [
            "Operation dispatcher (what runs)",
            "Cross-domain context assembly",
            "Start / end / phase transitions",
            "Job state machines and execution tracking",
        ],
        "what_must_not": [
            "Execute domain business logic (that's L5)",
            "Own persistence (that's L6/L7)",
            "Import L5 engines directly (use protocols)",
        ],
        "missing": [
            "Explicit OperationRegistry — operation→callable mapping",
            "Mandatory cross_domain_deps=[] declaration per operation",
            "Hard assertion: no L5 may call coordinator directly",
        ],
    },
    "authority": {
        "purpose": (
            "Decides WHAT is allowed, not HOW. Determines eligibility, runtime mode, "
            "policy posture, and permission boundaries."
        ),
        "what_belongs": [
            "Eligibility decisions",
            "Runtime mode switching",
            "Policy posture configuration",
            "Concurrent run limits",
            "Contract state machine",
        ],
        "what_must_not": [
            "Call L5 engines",
            "Touch DB drivers directly",
            "Orchestrate execution",
        ],
        "missing": [
            "Unified AuthorityDecision object returned to orchestrator",
            "Explicit deny / degraded / conditional execution states",
        ],
    },
    "consequences": {
        "purpose": (
            "After-the-fact reactions. Handles effects (notifications, exports, "
            "escalations), not decisions. Triggered only by orchestrator, never by L5."
        ),
        "what_belongs": [
            "Export bundle generation",
            "Notification dispatch (future)",
            "Escalation triggers (future)",
        ],
        "what_must_not": [
            "Make decisions",
            "Be called by L5 directly",
            "Own transaction boundaries",
        ],
        "missing": [
            "Generic PostExecutionHook interface",
            "Sync vs async consequence separation",
        ],
    },
    "services": {
        "purpose": (
            "Spine-only shared utilities. Must be stateless, deterministic, and "
            "domain-agnostic. Time, IDs, audit, runtime flags, crypto verification."
        ),
        "what_belongs": [
            "Time utilities",
            "ID generation",
            "Audit store",
            "Runtime flags and configuration",
            "Cryptographic verification",
            "Input sanitization",
            "Deterministic helpers",
        ],
        "what_must_not": [
            "Import L5 engines",
            "Import L6 drivers",
            "Import schemas outside hoc_spine",
            "Contain domain-specific business logic",
        ],
        "missing": [],
    },
    "schemas": {
        "purpose": (
            "Shared contracts, not models. Defines operation shapes, execution "
            "context, and authority decisions. No logic, no imports from services, "
            "drivers, or orchestrator."
        ),
        "what_belongs": [
            "Pydantic DTOs for API responses",
            "Operation and plan schemas",
            "Agent/skill configuration models",
            "RAC audit models",
        ],
        "what_must_not": [
            "Import services",
            "Import drivers",
            "Import orchestrator",
            "Contain business logic",
        ],
        "missing": [
            "AuthorityDecision schema",
            "ExecutionContext schema (unified)",
        ],
    },
    "drivers": {
        "purpose": (
            "Cross-domain DB boundary. Reads/writes across domain tables. "
            "Participates in transactions owned by orchestrator. Only "
            "transaction_coordinator may commit."
        ),
        "what_belongs": [
            "Transaction coordinator (sole commit authority)",
            "Cross-domain read/write operations",
            "Alert queue management",
            "Decision record sink",
            "Schema parity checks",
        ],
        "what_must_not": [
            "Commit (except transaction_coordinator)",
            "Orchestrate execution",
            "Import L5 engines",
        ],
        "missing": [
            "Runtime enforcement: block commit() in non-coordinator drivers",
            "Clear READ vs WRITE driver naming distinction",
        ],
    },
    "adapters": {
        "purpose": (
            "Thin translation layer between spine and external systems. "
            "HTTP delivery, runtime boundary. No business logic, no L5 imports."
        ),
        "what_belongs": [
            "Alert delivery (HTTP to Alertmanager)",
            "Runtime adapter (L2→L4 boundary)",
        ],
        "what_must_not": [
            "Contain business logic",
            "Import L5 engines",
            "Own transaction boundaries",
        ],
        "missing": [],
    },
    "frontend": {
        "purpose": (
            "Read-only projection lens for founder and customer consoles. "
            "Never modifies, never executes, never approves."
        ),
        "what_belongs": [
            "Rollout projection service",
            "Console view generation",
        ],
        "what_must_not": [
            "Mutate state",
            "Execute operations",
            "Approve workflows",
        ],
        "missing": [],
    },
    "mcp": {
        "purpose": (
            "RELOCATED (2026-01-29). Moved to cus/integrations/adapters/mcp_server_registry.py. "
            "MCP is tool discovery/integration, not system constitution."
        ),
        "what_belongs": [],
        "what_must_not": [],
        "missing": [],
    },
}


def get_annotation_str(node: ast.expr | None) -> str:
    """Convert an AST annotation node to a string representation."""
    if node is None:
        return ""
    return ast.unparse(node)


def extract_function_info(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    """Extract metadata from a function/method definition."""
    params = []
    for arg in node.args.args:
        if arg.arg == "self" or arg.arg == "cls":
            continue
        param = {"name": arg.arg}
        if arg.annotation:
            param["type"] = get_annotation_str(arg.annotation)
        params.append(param)

    # Handle *args
    if node.args.vararg:
        p = {"name": f"*{node.args.vararg.arg}"}
        if node.args.vararg.annotation:
            p["type"] = get_annotation_str(node.args.vararg.annotation)
        params.append(p)

    # Handle **kwargs
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
    }


def extract_class_info(node: ast.ClassDef) -> dict[str, Any]:
    """Extract metadata from a class definition."""
    methods = []
    class_vars = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(extract_function_info(item))
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            cv = {"name": item.target.id}
            if item.annotation:
                cv["type"] = get_annotation_str(item.annotation)
            class_vars.append(cv)

    bases = [ast.unparse(b) for b in node.bases]

    return {
        "name": node.name,
        "bases": bases,
        "docstring": ast.get_docstring(node) or "",
        "methods": methods,
        "class_vars": class_vars,
    }


def extract_header_metadata(source: str) -> dict[str, str]:
    """Extract header comment metadata (Layer, AUDIENCE, Role, etc.)."""
    meta = {}
    for line in source.splitlines()[:30]:
        line = line.strip()
        if not line.startswith("#"):
            if line:
                break
            continue
        line = line.lstrip("# ").strip()
        for key in ("Layer", "AUDIENCE", "Role", "Product", "Callers", "Reference"):
            if line.startswith(f"{key}:"):
                meta[key.lower()] = line[len(key) + 1:].strip()
                break
    return meta


def extract_imports(tree: ast.Module) -> list[str]:
    """Extract all import module paths from an AST."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def classify_imports(imports: list[str]) -> dict[str, list[str]]:
    """Classify imports into categories relevant to spine governance."""
    cats: dict[str, list[str]] = {
        "spine_internal": [],
        "l5_engine": [],
        "l6_driver": [],
        "l7_model": [],
        "cross_domain": [],
        "external": [],
    }
    stdlib_prefixes = {
        "abc", "argparse", "ast", "asyncio", "base64", "collections",
        "contextlib", "copy", "dataclasses", "datetime", "decimal", "enum",
        "functools", "hashlib", "hmac", "inspect", "io", "itertools", "json",
        "logging", "math", "os", "pathlib", "re", "secrets", "struct",
        "sys", "threading", "time", "traceback", "typing", "unittest",
        "urllib", "uuid",
    }
    for imp in imports:
        top = imp.split(".")[0]
        if top in stdlib_prefixes:
            continue
        if "hoc_spine" in imp:
            cats["spine_internal"].append(imp)
        elif "hoc.cus." in imp:
            cats["cross_domain"].append(imp)
            # Also check if it's an L5 engine
            if "L5_engines" in imp or "L5_support" in imp:
                cats["l5_engine"].append(imp)
            elif "L6_drivers" in imp:
                cats["l6_driver"].append(imp)
        elif imp.startswith("app.models"):
            cats["l7_model"].append(imp)
        elif imp.startswith("app."):
            cats["external"].append(imp)
        else:
            cats["external"].append(imp)
    return cats


def detect_transaction_usage(source: str) -> dict[str, bool]:
    """Detect session.commit(), session.flush(), session.rollback() in source code lines (not comments)."""
    commits = False
    flushes = False
    rollbacks = False
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # Remove inline comments
        code_part = stripped.split("#")[0]
        if ".commit()" in code_part:
            commits = True
        if ".flush()" in code_part:
            flushes = True
        if ".rollback()" in code_part:
            rollbacks = True
    return {
        "commits": commits,
        "flushes": flushes,
        "rollbacks": rollbacks,
    }


def extract_file_metadata(filepath: Path) -> dict[str, Any]:
    """Extract all metadata from a Python file."""
    source = filepath.read_text()
    tree = ast.parse(source, filename=str(filepath))

    module_docstring = ast.get_docstring(tree) or ""
    header = extract_header_metadata(source)

    functions = []
    classes = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(extract_function_info(node))
        elif isinstance(node, ast.ClassDef):
            classes.append(extract_class_info(node))

    # Import analysis
    raw_imports = extract_imports(tree)
    import_classes = classify_imports(raw_imports)
    tx_usage = detect_transaction_usage(source)

    # Determine relative path from spine root
    try:
        rel = filepath.relative_to(SPINE_ROOT)
    except ValueError:
        rel = filepath

    return {
        "file": str(rel),
        "module_docstring": module_docstring,
        "header": header,
        "functions": functions,
        "classes": classes,
        "imports": import_classes,
        "transaction": tx_usage,
    }


def to_yaml(data: dict[str, Any], indent: int = 0) -> str:
    """Simple YAML serializer (no dependencies)."""
    lines = []
    prefix = "  " * indent

    for key, value in data.items():
        if isinstance(value, str):
            if "\n" in value:
                lines.append(f"{prefix}{key}: |")
                for vline in value.splitlines():
                    lines.append(f"{prefix}  {vline}")
            elif value == "":
                lines.append(f"{prefix}{key}: \"\"")
            else:
                lines.append(f"{prefix}{key}: {value}")
        elif isinstance(value, bool):
            lines.append(f"{prefix}{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{prefix}{key}: []")
            else:
                lines.append(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        first = True
                        for k, v in item.items():
                            if first:
                                lines.append(f"{prefix}  - {k}: {_yaml_scalar(v)}")
                                first = False
                            else:
                                lines.append(f"{prefix}    {k}: {_yaml_scalar(v)}")
                    else:
                        lines.append(f"{prefix}  - {_yaml_scalar(item)}")
        elif isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(to_yaml(value, indent + 1))
        else:
            lines.append(f"{prefix}{key}: {value}")

    return "\n".join(lines)


def _yaml_scalar(v: Any) -> str:
    if isinstance(v, str):
        if "\n" in v or ":" in v or "#" in v:
            return f'"{v}"'
        return v if v else '""'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return str(v)
    return str(v)


def get_all_spine_files() -> list[Path]:
    """Get all non-__init__ Python files in hoc_spine/."""
    files = []
    for p in sorted(SPINE_ROOT.rglob("*.py")):
        if p.name == "__init__.py":
            continue
        files.append(p)
    return files


def get_folder_for_file(filepath: Path) -> str:
    """Get the top-level folder name within hoc_spine/ for a file."""
    try:
        rel = filepath.relative_to(SPINE_ROOT)
        return rel.parts[0]
    except (ValueError, IndexError):
        return "unknown"


def _format_transaction_line(tx: dict[str, bool]) -> str:
    """Format transaction usage as a concise string."""
    if tx["commits"]:
        return "OWNS COMMIT"
    if tx["flushes"]:
        return "Flush only (no commit)"
    if tx["rollbacks"]:
        return "Rollback only"
    return "Forbidden"


def _detect_violations(folder: str, script_name: str, imports: dict[str, list[str]], tx: dict[str, bool]) -> list[str]:
    """Detect governance violations based on reconciliation rules."""
    violations = []

    # Schemas must not import services, drivers, orchestrator
    if folder == "schemas":
        for imp in imports.get("spine_internal", []):
            for forbidden in ("services", "drivers", "orchestrator"):
                if forbidden in imp:
                    violations.append(f"Schema imports {forbidden}: {imp}")

    # Services must not import L5 or drivers
    if folder == "services":
        if imports.get("l5_engine"):
            violations.append(f"Service imports L5 engine: {imports['l5_engine']}")
        if imports.get("l6_driver"):
            violations.append(f"Service imports L6 driver: {imports['l6_driver']}")

    # Drivers must not commit (except transaction_coordinator)
    if folder == "drivers" and tx["commits"] and script_name != "transaction_coordinator":
        violations.append("Driver calls commit (only transaction_coordinator allowed)")

    # Cross-domain imports from L4 spine
    if imports.get("cross_domain"):
        violations.append(f"Cross-domain import: {imports['cross_domain']}")

    return violations


def _get_allowed_inbound(folder: str) -> list[str]:
    """Return allowed inbound callers for a folder based on governance rules."""
    rules: dict[str, list[str]] = {
        "orchestrator": ["hoc.api.*", "hoc_spine.adapters.*"],
        "authority": ["hoc_spine.orchestrator.*"],
        "consequences": ["hoc_spine.orchestrator.*"],
        "services": ["hoc_spine.orchestrator.*", "hoc_spine.authority.*", "hoc_spine.consequences.*", "hoc_spine.drivers.*"],
        "schemas": ["hoc_spine.*"],
        "drivers": ["hoc_spine.orchestrator.*", "hoc_spine.services.*"],
        "adapters": ["hoc.api.*"],
        "frontend": ["hoc.api.*"],
        "mcp": [],
    }
    return rules.get(folder, ["hoc_spine.*"])


def _get_forbidden_inbound(folder: str) -> list[str]:
    """Return forbidden inbound callers for a folder based on governance rules."""
    rules: dict[str, list[str]] = {
        "orchestrator": [],
        "authority": ["hoc.cus.*", "hoc.api.*"],
        "consequences": ["hoc.cus.*", "hoc.api.*"],
        "services": ["hoc.cus.*", "hoc.api.*"],
        "schemas": [],
        "drivers": ["hoc.cus.*", "hoc.api.*"],
        "adapters": ["hoc.cus.*"],
        "frontend": [],
        "mcp": [],
    }
    return rules.get(folder, [])


def _detect_boundary_violations(folder: str, imports: dict[str, list[str]]) -> list[str]:
    """Detect import boundary violations based on folder governance rules."""
    violations = []
    spec = FOLDER_SPEC.get(folder, {})
    what_must_not = spec.get("what_must_not", [])

    # Check for L5 engine imports from spine scripts
    if imports.get("l5_engine"):
        for imp in imports["l5_engine"]:
            violations.append(f"Imports L5 engine: {imp}")

    # Check for L6 driver imports from non-driver spine scripts
    if folder not in ("drivers",) and imports.get("l6_driver"):
        for imp in imports["l6_driver"]:
            violations.append(f"Imports L6 driver: {imp}")

    # Cross-domain imports are always violations for spine
    if imports.get("cross_domain"):
        for imp in imports["cross_domain"]:
            violations.append(f"Cross-domain import: {imp}")

    return violations


def generate_markdown(meta: dict[str, Any]) -> str:
    """Generate a literature markdown document from extracted metadata."""
    filepath = meta["file"]
    parts = Path(filepath).parts
    folder = parts[0] if parts else "unknown"
    script_name = Path(filepath).stem

    layer = meta["header"].get("layer", FOLDER_LAYER.get(folder, "L4"))
    component = FOLDER_COMPONENT.get(folder, folder.title())
    full_path = f"backend/app/hoc/cus/hoc_spine/{filepath}"
    callers = meta["header"].get("callers", "_unknown_")

    imports = meta.get("imports", {})
    tx = meta.get("transaction", {"commits": False, "flushes": False, "rollbacks": False})
    cross_domain = imports.get("cross_domain", [])
    violations = _detect_violations(folder, script_name, imports, tx)

    lines = [
        f"# {script_name}.py",
        "",
        f"**Path:** `{full_path}`  ",
        f"**Layer:** {layer}  ",
        f"**Component:** {component}",
        "",
        "---",
        "",
        "## Placement Card",
        "",
        "```",
        f"File:            {script_name}.py",
        f"Lives in:        {folder}/",
        f"Role:            {component}",
        f"Inbound:         {callers}",
        f"Outbound:        {', '.join(imports.get('spine_internal', [])) or 'none'}",
        f"Transaction:     {_format_transaction_line(tx)}",
        f"Cross-domain:    {', '.join(cross_domain) or 'none'}",
    ]

    purpose = meta["module_docstring"] or meta["header"].get("role", "_No purpose declared_")
    purpose_oneline = purpose.split("\n")[0].strip()
    lines.append(f"Purpose:         {purpose_oneline}")

    if violations:
        lines.append(f"Violations:      {'; '.join(violations)}")
    else:
        lines.append("Violations:      none")
    lines.append("```")
    lines.append("")

    # Purpose (full)
    lines.append("## Purpose")
    lines.append("")
    if meta["module_docstring"]:
        lines.append(meta["module_docstring"])
    elif meta["header"].get("role"):
        lines.append(meta["header"]["role"])
    else:
        lines.append("_No module docstring._")
    lines.append("")

    # Import Analysis
    lines.append("## Import Analysis")
    lines.append("")
    if imports.get("spine_internal"):
        lines.append("**Spine-internal:**")
        for imp in imports["spine_internal"]:
            lines.append(f"- `{imp}`")
        lines.append("")
    if imports.get("l7_model"):
        lines.append("**L7 Models:**")
        for imp in imports["l7_model"]:
            lines.append(f"- `{imp}`")
        lines.append("")
    if cross_domain:
        lines.append("**Cross-domain (violation):**")
        for imp in cross_domain:
            lines.append(f"- `{imp}`")
        lines.append("")
    if imports.get("external"):
        lines.append("**External:**")
        for imp in imports["external"]:
            lines.append(f"- `{imp}`")
        lines.append("")
    if not any(imports.get(k) for k in ("spine_internal", "l7_model", "cross_domain", "external")):
        lines.append("Pure stdlib — no application imports.")
        lines.append("")

    # Transaction
    lines.append("## Transaction Boundary")
    lines.append("")
    lines.append(f"- **Commits:** {'YES' if tx['commits'] else 'no'}")
    lines.append(f"- **Flushes:** {'yes' if tx['flushes'] else 'no'}")
    lines.append(f"- **Rollbacks:** {'yes' if tx['rollbacks'] else 'no'}")
    lines.append("")

    # Violations
    if violations:
        lines.append("## Governance Violations")
        lines.append("")
        for v in violations:
            lines.append(f"- {v}")
        lines.append("")

    # Functions
    if meta["functions"]:
        lines.append("## Functions")
        lines.append("")
        for fn in meta["functions"]:
            sig = _build_signature(fn)
            prefix = "async " if fn.get("async") else ""
            lines.append(f"### `{prefix}{sig}`")
            lines.append("")
            if fn["docstring"]:
                lines.append(fn["docstring"])
            else:
                lines.append("_No docstring._")
            lines.append("")

    # Classes
    if meta["classes"]:
        lines.append("## Classes")
        lines.append("")
        for cls in meta["classes"]:
            bases_str = f"({', '.join(cls['bases'])})" if cls["bases"] else ""
            lines.append(f"### `{cls['name']}{bases_str}`")
            lines.append("")
            if cls["docstring"]:
                lines.append(cls["docstring"])
            else:
                lines.append("_No docstring._")
            lines.append("")

            if cls["methods"]:
                lines.append("#### Methods")
                lines.append("")
                for m in cls["methods"]:
                    sig = _build_signature(m)
                    prefix = "async " if m.get("async") else ""
                    doc_summary = m["docstring"].split("\n")[0] if m["docstring"] else "_No docstring._"
                    lines.append(f"- `{prefix}{sig}` — {doc_summary}")
                lines.append("")

    # Domain Usage
    lines.append("## Domain Usage")
    lines.append("")
    if callers != "_unknown_":
        lines.append(f"**Callers:** {callers}")
    else:
        lines.append("_To be determined during review._")
    lines.append("")

    # --- NEW SECTIONS (PIN-491) ---

    # Export Contract
    lines.append("## Export Contract")
    lines.append("")
    lines.append("```yaml")
    lines.append("exports:")

    # Functions
    if meta["functions"]:
        lines.append("  functions:")
        for fn in meta["functions"]:
            sig = _build_signature(fn)
            prefix = "async " if fn.get("async") else ""
            lines.append(f'    - name: {fn["name"]}')
            lines.append(f'      signature: "{prefix}{sig}"')
            lines.append('      consumers: ["orchestrator"]')
    else:
        lines.append("  functions: []")

    # Classes
    if meta["classes"]:
        lines.append("  classes:")
        for cls in meta["classes"]:
            lines.append(f'    - name: {cls["name"]}')
            if cls["methods"]:
                lines.append("      methods:")
                for m in cls["methods"]:
                    if not m["name"].startswith("_"):
                        lines.append(f"        - {m['name']}")
            else:
                lines.append("      methods: []")
            lines.append('      consumers: ["orchestrator"]')
    else:
        lines.append("  classes: []")

    lines.append("  protocols: []")
    lines.append("```")
    lines.append("")

    # Import Boundary
    lines.append("## Import Boundary")
    lines.append("")
    lines.append("```yaml")
    lines.append("boundary:")

    # Allowed/forbidden inbound based on folder spec
    spec = FOLDER_SPEC.get(folder, {})
    allowed_inbound = _get_allowed_inbound(folder)
    forbidden_inbound = _get_forbidden_inbound(folder)

    lines.append("  allowed_inbound:")
    for a in allowed_inbound:
        lines.append(f'    - "{a}"')
    lines.append("  forbidden_inbound:")
    for f_item in forbidden_inbound:
        lines.append(f'    - "{f_item}"')

    # Actual imports
    lines.append("  actual_imports:")
    for cat in ("spine_internal", "l7_model", "external"):
        cat_imports = imports.get(cat, [])
        if cat_imports:
            lines.append(f"    {cat}: {cat_imports}")
        else:
            lines.append(f"    {cat}: []")

    # Violations
    boundary_violations = _detect_boundary_violations(folder, imports)
    if boundary_violations:
        lines.append("  violations:")
        for bv in boundary_violations:
            lines.append(f'    - "{bv}"')
    else:
        lines.append("  violations: []")
    lines.append("```")
    lines.append("")

    # L5 Pairing Declaration
    lines.append("## L5 Pairing Declaration")
    lines.append("")
    lines.append("```yaml")
    lines.append("pairing:")
    lines.append("  serves_domains: []")
    lines.append("  expected_l5_consumers: []")
    lines.append("  orchestrator_operations: []")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def _build_signature(fn: dict) -> str:
    """Build a function signature string."""
    params = []
    for p in fn["params"]:
        if p.get("type"):
            params.append(f"{p['name']}: {p['type']}")
        else:
            params.append(p["name"])
    ret = f" -> {fn['return_type']}" if fn.get("return_type") else ""
    return f"{fn['name']}({', '.join(params)}){ret}"


def generate_folder_overview(folder: str, metas: list[dict[str, Any]]) -> str:
    """Generate _summary.md for a folder with purpose, rules, inventory, and assessment."""
    spec = FOLDER_SPEC.get(folder, {})
    layer = FOLDER_LAYER.get(folder, "L4")
    component = FOLDER_COMPONENT.get(folder, folder.title())

    lines = [
        f"# {component} — Folder Summary",
        "",
        f"**Path:** `backend/app/hoc/cus/hoc_spine/{folder}/`  ",
        f"**Layer:** {layer}  ",
        f"**Scripts:** {len(metas)}",
        "",
        "---",
        "",
    ]

    # 1. Purpose
    lines.append("## 1. Purpose")
    lines.append("")
    lines.append(spec.get("purpose", "_No purpose defined in reconciliation artifact._"))
    lines.append("")

    # 2. What Belongs Here
    lines.append("## 2. What Belongs Here")
    lines.append("")
    for item in spec.get("what_belongs", []):
        lines.append(f"- {item}")
    lines.append("")

    # 3. What Must NOT Be Here
    lines.append("## 3. What Must NOT Be Here")
    lines.append("")
    for item in spec.get("what_must_not", []):
        lines.append(f"- {item}")
    lines.append("")

    # 4. Script Inventory Table
    lines.append("## 4. Script Inventory")
    lines.append("")
    lines.append("| Script | Purpose | Transaction | Cross-domain | Verdict |")
    lines.append("|--------|---------|-------------|--------------|---------|")

    all_violations = []
    for meta in sorted(metas, key=lambda m: Path(m["file"]).stem):
        script_name = Path(meta["file"]).stem
        imports = meta.get("imports", {})
        tx = meta.get("transaction", {"commits": False, "flushes": False, "rollbacks": False})
        violations = _detect_violations(folder, script_name, imports, tx)

        purpose_raw = meta["module_docstring"] or meta["header"].get("role", "")
        purpose_short = purpose_raw.split("\n")[0][:60].strip()
        if not purpose_short:
            purpose_short = "_none_"

        tx_str = _format_transaction_line(tx)
        xd = "yes" if imports.get("cross_domain") else "no"

        if violations:
            verdict = "VIOLATION"
            all_violations.extend([(script_name, v) for v in violations])
        else:
            verdict = "OK"

        link = f"[{script_name}.py]({script_name}.md)"
        lines.append(f"| {link} | {purpose_short} | {tx_str} | {xd} | {verdict} |")

    lines.append("")

    # 5. Assessment
    lines.append("## 5. Assessment")
    lines.append("")

    # Correct
    ok_count = len(metas) - len({s for s, _ in all_violations})
    lines.append(f"**Correct:** {ok_count}/{len(metas)} scripts pass all governance checks.")
    lines.append("")

    # Violations
    if all_violations:
        lines.append(f"**Violations ({len(all_violations)}):**")
        lines.append("")
        for script_name, v in all_violations:
            lines.append(f"- `{script_name}.py` — {v}")
        lines.append("")

    # Missing (from reconciliation artifact)
    missing = spec.get("missing", [])
    if missing:
        lines.append("**Missing (from reconciliation artifact):**")
        lines.append("")
        for item in missing:
            lines.append(f"- {item}")
        lines.append("")

    if not all_violations and not missing:
        lines.append("No violations or missing primitives detected.")
        lines.append("")

    # 6. Aggregate L5 Pairing Table (PIN-491)
    lines.append("## 6. L5 Pairing Aggregate")
    lines.append("")
    lines.append("_Populated by `l5_spine_pairing_gap_detector.py --update-literature`_")
    lines.append("")
    lines.append("| Script | Serves Domains | Wired L5 Consumers | Gaps |")
    lines.append("|--------|----------------|--------------------|------|")
    for meta in sorted(metas, key=lambda m: Path(m["file"]).stem):
        script_name = Path(meta["file"]).stem
        lines.append(f"| {script_name}.py | _pending_ | _pending_ | _pending_ |")
    lines.append("")

    return "\n".join(lines)


def generate_index(file_metas: list[dict[str, Any]]) -> str:
    """Generate INDEX.md — master navigation with folder summaries and violation roll-up."""
    folder_order = ["orchestrator", "authority", "consequences", "services",
                    "schemas", "drivers", "adapters", "frontend", "mcp"]

    # Group metas by folder
    by_folder: dict[str, list[dict[str, Any]]] = {}
    for meta in file_metas:
        folder = Path(meta["file"]).parts[0] if Path(meta["file"]).parts else "unknown"
        by_folder.setdefault(folder, []).append(meta)

    # Collect all violations
    all_violations: list[tuple[str, str, str]] = []  # (folder, script, violation)
    for folder, metas in by_folder.items():
        for meta in metas:
            script_name = Path(meta["file"]).stem
            imports = meta.get("imports", {})
            tx = meta.get("transaction", {"commits": False, "flushes": False, "rollbacks": False})
            for v in _detect_violations(folder, script_name, imports, tx):
                all_violations.append((folder, script_name, v))

    total_files = len(file_metas)
    violation_files = len({(f, s) for f, s, _ in all_violations})

    lines = [
        "# HOC Spine — Literature Study Index",
        "",
        f"**Total scripts:** {total_files}  ",
        f"**Clean:** {total_files - violation_files}  ",
        f"**With violations:** {violation_files}  ",
        f"**Source:** `backend/app/hoc/cus/hoc_spine/`  ",
        "**Validator:** `scripts/ops/hoc_spine_study_validator.py`",
        "",
        "---",
        "",
        "## Navigation",
        "",
        "| Folder | Layer | Scripts | Violations | Purpose |",
        "|--------|-------|---------|------------|---------|",
    ]

    for folder in folder_order:
        if folder not in by_folder:
            continue
        spec = FOLDER_SPEC.get(folder, {})
        layer = FOLDER_LAYER.get(folder, "L4")
        count = len(by_folder[folder])
        v_count = len([v for v in all_violations if v[0] == folder])
        purpose_short = (spec.get("purpose", "") or "")[:80]
        if len(spec.get("purpose", "")) > 80:
            purpose_short += "..."
        overview_link = f"[{folder.title()}](hoc_spine/{folder}/_summary.md)"
        lines.append(f"| {overview_link} | {layer} | {count} | {v_count} | {purpose_short} |")

    lines.append("")

    # Folder sections with script links
    for folder in folder_order:
        if folder not in by_folder:
            continue
        component = FOLDER_COMPONENT.get(folder, folder.title())
        lines.append(f"## {component}")
        lines.append("")
        lines.append(f"[Folder Summary](hoc_spine/{folder}/_summary.md)")
        lines.append("")
        for meta in sorted(by_folder[folder], key=lambda m: Path(m["file"]).stem):
            script_name = Path(meta["file"]).stem
            purpose_raw = meta["module_docstring"] or meta["header"].get("role", "")
            purpose_short = purpose_raw.split("\n")[0][:70].strip() or "_no purpose_"
            lines.append(f"- [{script_name}.py](hoc_spine/{folder}/{script_name}.md) — {purpose_short}")
        lines.append("")

    # Violation Roll-up
    lines.append("---")
    lines.append("")
    lines.append("## Violation Summary")
    lines.append("")
    if all_violations:
        lines.append(f"**{len(all_violations)} violations across {violation_files} files:**")
        lines.append("")
        lines.append("| Folder | Script | Violation |")
        lines.append("|--------|--------|-----------|")
        for folder, script, v in sorted(all_violations):
            lines.append(f"| {folder} | {script}.py | {v} |")
        lines.append("")
    else:
        lines.append("No violations detected.")
        lines.append("")

    # Build List (from reconciliation artifact)
    lines.append("## Build List — Missing Spine Primitives")
    lines.append("")
    any_missing = False
    for folder in folder_order:
        spec = FOLDER_SPEC.get(folder, {})
        missing = spec.get("missing", [])
        if missing:
            any_missing = True
            lines.append(f"### {folder.title()}")
            lines.append("")
            for item in missing:
                lines.append(f"- [ ] {item}")
            lines.append("")
    if not any_missing:
        lines.append("No missing primitives identified.")
        lines.append("")

    return "\n".join(lines)


def validate_literature(lit_dir: Path) -> int:
    """Validate literature files against source. Returns 0 if clean, 1 if drift."""
    drift_found = False
    spine_files = get_all_spine_files()

    for filepath in spine_files:
        meta = extract_file_metadata(filepath)
        folder = get_folder_for_file(filepath)
        script_name = filepath.stem

        # Find corresponding literature file
        # Search recursively since some files are in subdirectories
        rel = filepath.relative_to(SPINE_ROOT)
        lit_path = lit_dir / str(rel).replace(".py", ".md")

        # Flatten: literature uses top-level folder only
        lit_path_flat = lit_dir / folder / f"{script_name}.md"

        actual_lit = None
        for candidate in [lit_path, lit_path_flat]:
            if candidate.exists():
                actual_lit = candidate
                break

        if actual_lit is None:
            print(f"MISSING: {folder}/{script_name}.md")
            drift_found = True
            continue

        # Check that all functions/classes from source are mentioned in literature
        lit_content = actual_lit.read_text()
        source_names = set()
        for fn in meta["functions"]:
            source_names.add(fn["name"])
        for cls in meta["classes"]:
            source_names.add(cls["name"])

        missing = []
        for name in source_names:
            if name not in lit_content:
                missing.append(name)

        if missing:
            print(f"DRIFT: {folder}/{script_name}.md — missing: {', '.join(sorted(missing))}")
            drift_found = True
        else:
            print(f"OK: {folder}/{script_name}.md")

        # Check for new sections (PIN-491)
        for section in ("## Export Contract", "## Import Boundary", "## L5 Pairing Declaration"):
            if section not in lit_content:
                print(f"MISSING-SECTION: {folder}/{script_name}.md — {section}")
                drift_found = True

        # Validate import boundary matches actual imports
        if "## Import Boundary" in lit_content:
            imports = meta.get("imports", {})
            boundary_violations = _detect_boundary_violations(folder, imports)
            if boundary_violations:
                for bv in boundary_violations:
                    if bv not in lit_content:
                        print(f"BOUNDARY-DRIFT: {folder}/{script_name}.md — undeclared: {bv}")
                        drift_found = True

    return 1 if drift_found else 0


def main():
    parser = argparse.ArgumentParser(description="HOC Spine Study Validator")
    parser.add_argument("file", nargs="?", help="Single Python file to extract")
    parser.add_argument("--all", action="store_true", help="Extract all spine files")
    parser.add_argument("--output-dir", type=str, help="Output directory for YAML or markdown")
    parser.add_argument("--validate", type=str, metavar="LIT_DIR", help="Validate literature against source")
    parser.add_argument("--generate", action="store_true", help="Generate markdown literature files")
    parser.add_argument("--index", action="store_true", help="Generate INDEX.md only")
    parser.add_argument("--folder", type=str, help="Process only this folder")
    args = parser.parse_args()

    if args.validate:
        sys.exit(validate_literature(Path(args.validate)))

    if args.generate:
        files = get_all_spine_files()
        if args.folder:
            files = [f for f in files if get_folder_for_file(f) == args.folder]

        out_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "literature" / "hoc_spine"
        all_metas = []

        for filepath in files:
            meta = extract_file_metadata(filepath)
            all_metas.append(meta)
            folder = get_folder_for_file(filepath)
            script_name = filepath.stem

            md_content = generate_markdown(meta)
            md_path = out_dir / folder / f"{script_name}.md"
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(md_content)
            print(f"Generated: {md_path.relative_to(PROJECT_ROOT)}")

        # Generate folder overviews
        by_folder: dict[str, list[dict[str, Any]]] = {}
        for meta in all_metas:
            f = Path(meta["file"]).parts[0] if Path(meta["file"]).parts else "unknown"
            by_folder.setdefault(f, []).append(meta)

        for f, f_metas in by_folder.items():
            if args.folder and f != args.folder:
                continue
            overview = generate_folder_overview(f, f_metas)
            ov_path = out_dir / f / "_summary.md"
            ov_path.parent.mkdir(parents=True, exist_ok=True)
            ov_path.write_text(overview)
            print(f"Generated: {ov_path.relative_to(PROJECT_ROOT)}")

        if not args.folder:
            # Also generate index
            index_content = generate_index(all_metas)
            index_path = out_dir.parent / "INDEX.md"
            index_path.write_text(index_content)
            print(f"Generated: {index_path.relative_to(PROJECT_ROOT)}")

        return

    if args.index:
        files = get_all_spine_files()
        all_metas = [extract_file_metadata(f) for f in files]
        index_content = generate_index(all_metas)
        if args.output_dir:
            out = Path(args.output_dir) / "INDEX.md"
            out.write_text(index_content)
            print(f"Written: {out}")
        else:
            print(index_content)
        return

    if args.all:
        files = get_all_spine_files()
        if args.folder:
            files = [f for f in files if get_folder_for_file(f) == args.folder]
    elif args.file:
        files = [Path(args.file).resolve()]
    else:
        parser.print_help()
        return

    for filepath in files:
        meta = extract_file_metadata(filepath)
        if args.output_dir:
            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{filepath.stem}.yaml"
            out_path.write_text(to_yaml(meta))
            print(f"Written: {out_path}")
        else:
            print(to_yaml(meta))
            print("---")


if __name__ == "__main__":
    main()
