#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: HOC Literature Generator — Prescriptive Architecture Documentation
# artifact_class: CODE
"""
HOC Literature Generator — Prescriptive Architecture Documentation

Generates per-domain, per-layer literature documents describing:
- What each file contains (AST-derived, zero interpretation)
- How it SHOULD be wired (per HOC_LAYER_TOPOLOGY_V1.4.0)
- What's missing (gaps) and what's broken (violations)

Input: HOC_CUS_DOMAIN_AUDIT.csv (file inventory)
Output: Markdown + JSON in docs/architecture/hoc/literature/

Reference: HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

Usage:
    python scripts/ops/hoc_literature_generator.py
    python scripts/ops/hoc_literature_generator.py --csv path/to/audit.csv
"""

import ast
import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
DEFAULT_CSV = REPO_ROOT / "docs" / "architecture" / "hoc" / "HOC_CUS_DOMAIN_AUDIT.csv"
OUTPUT_DIR = REPO_ROOT / "docs" / "architecture" / "hoc" / "literature"

DOMAINS_ORDERED = [
    "general", "overview", "activity", "incidents", "policies",
    "controls", "logs", "analytics", "integrations", "apis", "account",
]

# ---------------------------------------------------------------------------
# Layer Contract (from HOC_LAYER_TOPOLOGY_V1.4.0 — RATIFIED)
# ---------------------------------------------------------------------------

LAYER_CONTRACT = {
    "L2.1_facade": {
        "should_call": ["L2_api"],
        "must_not_call": ["L3_adapters", "L4_runtime", "L5_engines",
                          "L5_schemas", "L6_drivers", "L7_models"],
        "called_by": ["L1_frontend"],
        "contract": "ORGANIZER ONLY — no business logic, no validation, groups L2 routers",
    },
    "L2_api": {
        "should_call": ["L3_adapters"],
        "must_not_call": ["L5_engines", "L6_drivers", "L7_models"],
        "called_by": ["L2.1_facade"],
        "contract": "HTTP translation — request validation, auth, response formatting, delegates to L3",
    },
    "L3_adapters": {
        "should_call": ["L4_runtime", "L5_engines"],
        "must_not_call": ["L2_api", "L6_drivers", "L7_models"],
        "called_by": ["L2_api"],
        "cross_domain_allowed": True,
        "contract": "Translation + aggregation ONLY — no state mutation, no retries, no policy decisions",
        "archetypes": [
            "Domain Adapter (same-domain L2→L5 bridge)",
            "Cross-Domain Bridge (domain A facts → domain B actions)",
            "Tenant Isolator (internal→customer-safe schema transform)",
            "Integration Wrapper (external SDK → AOS interface)",
        ],
    },
    "L4_runtime": {
        "should_call": ["L5_engines", "L6_drivers"],
        "must_not_call": ["L2_api", "L3_adapters", "L7_models"],
        "called_by": ["L3_adapters"],
        "domain_restriction": "general",
        "contract": "Control plane — authority/execution/consequences, owns commit, all execution enters L4 once",
        "parts": ["authority", "execution", "consequences", "contracts"],
    },
    "L5_engines": {
        "should_call": ["L6_drivers", "L5_schemas"],
        "must_not_call": ["L2_api", "L3_adapters", "L7_models"],
        "called_by": ["L3_adapters", "L4_runtime"],
        "contract": "Business logic — pattern detection, decisions, calls L6 for DB ops",
        "forbidden_imports": ["sqlalchemy", "sqlmodel.Session", "select"],
    },
    "L5_schemas": {
        "should_call": [],
        "must_not_call": ["L2_api", "L3_adapters", "L4_runtime", "L5_engines", "L6_drivers"],
        "called_by": ["L5_engines", "L3_adapters"],
        "contract": "Data contracts — Pydantic models, dataclasses, type references only",
    },
    "L6_drivers": {
        "should_call": ["L7_models"],
        "must_not_call": ["L2_api", "L3_adapters", "L4_runtime", "L5_engines"],
        "called_by": ["L5_engines", "L4_runtime"],
        "contract": "DB operations — query building, data transformation, returns domain objects NOT ORM",
    },
    "L7_models": {
        "should_call": [],
        "must_not_call": ["L2_api", "L3_adapters", "L4_runtime", "L5_engines", "L6_drivers"],
        "called_by": ["L6_drivers"],
        "contract": "ORM table definitions — leaf node, no HOC imports",
    },
}

# L7 Model classification buckets
L7_MODEL_BUCKETS = {
    "system_invariant": {
        "description": "System-wide tables that NEVER move — owned by general/platform",
        "patterns": ["tenant", "base", "audit_ledger", "worker_run", "alembic",
                     "migration", "session", "token"],
        "action": "STAYS in app/models/ — system invariant",
    },
    "domain_owned": {
        "description": "Data owned by a single domain — eligible for domain models",
        "patterns": [],  # Determined dynamically by usage analysis
        "action": "FLAG: domain-localized data candidate (human decision)",
    },
    "cross_domain_fact": {
        "description": "Shared facts consumed by multiple domains — stays shared",
        "patterns": [],  # Determined dynamically by multi-domain usage
        "action": "STAYS shared — cross-domain fact table",
    },
}

# System invariant model names (never move)
SYSTEM_INVARIANT_MODELS = {
    "tenant", "base", "audit_ledger", "worker_run", "alembic_version",
    "session_state", "migration", "token", "user", "invitation",
}

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class FunctionInfo:
    name: str
    signature: str
    docstring: Optional[str]
    is_async: bool
    line: int


@dataclass
class ClassInfo:
    name: str
    docstring: Optional[str]
    methods: List[str]
    line: int


@dataclass
class ImportInfo:
    module: str
    names: List[str]
    is_relative: bool
    line: int


@dataclass
class ConstantInfo:
    name: str
    line: int


@dataclass
class FileIdentity:
    file_name: str
    file_path: str
    layer: str
    domain: str
    lines: int
    module_docstring: Optional[str]
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    constants: List[ConstantInfo] = field(default_factory=list)
    all_exports: Optional[List[str]] = None


@dataclass
class Violation:
    file_path: str
    file_name: str
    domain: str
    layer: str
    import_statement: str
    rule_broken: str
    required_fix: str
    line: int


@dataclass
class Gap:
    domain: str
    gap_type: str  # "L2.1_facade", "L3_adapter", "L7_model", etc.
    description: str
    action: str
    related_files: List[str] = field(default_factory=list)


@dataclass
class L7ModelClassification:
    model_name: str
    file_path: str
    bucket: str  # "system_invariant", "domain_owned", "cross_domain_fact"
    used_by_domains: List[str] = field(default_factory=list)
    used_by_drivers: List[str] = field(default_factory=list)
    action: str = ""


@dataclass
class DomainWiring:
    domain: str
    l2_1_facade: Optional[str]  # file path or None (gap)
    l2_apis: List[FileIdentity] = field(default_factory=list)
    l3_adapters: List[FileIdentity] = field(default_factory=list)
    l4_runtime: List[FileIdentity] = field(default_factory=list)
    l5_engines: List[FileIdentity] = field(default_factory=list)
    l5_schemas: List[FileIdentity] = field(default_factory=list)
    l5_other: List[FileIdentity] = field(default_factory=list)
    l6_drivers: List[FileIdentity] = field(default_factory=list)
    l7_models: List[FileIdentity] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)
    gaps: List[Gap] = field(default_factory=list)


# ---------------------------------------------------------------------------
# AST Parsing — deterministic extraction, zero interpretation
# ---------------------------------------------------------------------------


def parse_file(file_path: str) -> Optional[FileIdentity]:
    """Parse a Python file using AST. Returns None on parse failure."""
    path = Path(file_path)
    if not path.exists():
        print(f"  WARN: File not found: {file_path}", file=sys.stderr)
        return None

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  WARN: Cannot read {file_path}: {e}", file=sys.stderr)
        return None

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        print(f"  WARN: Syntax error in {file_path}: {e}", file=sys.stderr)
        return None

    line_count = len(source.splitlines())
    layer = classify_layer(file_path)
    domain = classify_domain(file_path)

    identity = FileIdentity(
        file_name=path.name,
        file_path=file_path,
        layer=layer,
        domain=domain,
        lines=line_count,
        module_docstring=ast.get_docstring(tree),
    )

    for node in ast.iter_child_nodes(tree):
        # Functions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig = _extract_signature(node)
            identity.functions.append(FunctionInfo(
                name=node.name,
                signature=sig,
                docstring=ast.get_docstring(node),
                is_async=isinstance(node, ast.AsyncFunctionDef),
                line=node.lineno,
            ))

        # Classes
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
            identity.classes.append(ClassInfo(
                name=node.name,
                docstring=ast.get_docstring(node),
                methods=methods,
                line=node.lineno,
            ))

        # Imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                identity.imports.append(ImportInfo(
                    module=alias.name,
                    names=[alias.asname or alias.name],
                    is_relative=False,
                    line=node.lineno,
                ))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            identity.imports.append(ImportInfo(
                module=module,
                names=names,
                is_relative=node.level > 0,
                line=node.lineno,
            ))

        # Constants (UPPER_CASE module-level assignments)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    identity.constants.append(ConstantInfo(
                        name=target.id,
                        line=node.lineno,
                    ))

            # __all__ export list
            if (len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == "__all__"):
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    identity.all_exports = [
                        elt.value for elt in node.value.elts
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    ]

    return identity


def _extract_signature(node: ast.FunctionDef) -> str:
    """Extract function signature as string."""
    args = node.args
    parts = []

    # Regular args
    for i, arg in enumerate(args.args):
        if arg.arg == "self" or arg.arg == "cls":
            continue
        ann = ""
        if arg.annotation:
            ann = f": {ast.unparse(arg.annotation)}"

        # Check for default value
        default_offset = len(args.args) - len(args.defaults)
        if i >= default_offset and args.defaults:
            default = ast.unparse(args.defaults[i - default_offset])
            parts.append(f"{arg.arg}{ann} = {default}")
        else:
            parts.append(f"{arg.arg}{ann}")

    # *args
    if args.vararg:
        ann = f": {ast.unparse(args.vararg.annotation)}" if args.vararg.annotation else ""
        parts.append(f"*{args.vararg.arg}{ann}")

    # **kwargs
    if args.kwarg:
        ann = f": {ast.unparse(args.kwarg.annotation)}" if args.kwarg.annotation else ""
        parts.append(f"**{args.kwarg.arg}{ann}")

    # Return annotation
    ret = ""
    if node.returns:
        ret = f" -> {ast.unparse(node.returns)}"

    return f"({', '.join(parts)}){ret}"


# ---------------------------------------------------------------------------
# Layer + Domain Classification (deterministic, from path)
# ---------------------------------------------------------------------------

LAYER_PATTERNS = [
    (r"hoc/api/facades/", "L2.1_facade"),
    (r"hoc/api/cus/", "L2_api"),
    (r"/L3_adapters/", "L3_adapters"),
    (r"/L4_runtime/", "L4_runtime"),
    (r"/L5_engines/", "L5_engines"),
    (r"/L5_schemas/", "L5_schemas"),
    (r"/L5_controls/", "L5_other"),
    (r"/L5_lifecycle/", "L5_other"),
    (r"/L5_workflow/", "L5_other"),
    (r"/L5_utils/", "L5_other"),
    (r"/L5_ui/", "L5_other"),
    (r"/L5_notifications/", "L5_other"),
    (r"/L5_support/", "L5_other"),
    (r"/L5_vault/", "L5_other"),
    (r"/L6_drivers/", "L6_drivers"),
    (r"app/models/", "L7_models"),
]


def classify_layer(file_path: str) -> str:
    """Classify file into a layer based on its path."""
    for pattern, layer in LAYER_PATTERNS:
        if pattern in file_path:
            return layer
    return "UNKNOWN"


def classify_domain(file_path: str) -> str:
    """Extract domain from file path."""
    # hoc/cus/{domain}/ or hoc/api/cus/{domain}/
    m = re.search(r"hoc/(?:api/)?cus/(\w+)/", file_path)
    if m:
        return m.group(1)
    if "app/models/" in file_path:
        return "shared"
    return "unknown"


# ---------------------------------------------------------------------------
# Violation Detection (imports vs LAYER_CONTRACT rules)
# ---------------------------------------------------------------------------

# Import patterns that indicate layer violations
VIOLATION_PATTERNS = {
    "L5_engines": {
        "sqlmodel": ("L5 MUST NOT import sqlmodel at runtime", "Move DB logic to L6 driver"),
        "sqlalchemy": ("L5 MUST NOT import sqlalchemy", "Move DB logic to L6 driver"),
        "app.models": ("L5 MUST NOT import L7 models directly", "Route through L6 driver"),
        "app.db": ("L5 MUST NOT access DB directly", "Use L6 driver for DB access"),
    },
    "L5_other": {
        "sqlmodel": ("L5 MUST NOT import sqlmodel at runtime", "Move DB logic to L6 driver"),
        "sqlalchemy": ("L5 MUST NOT import sqlalchemy", "Move DB logic to L6 driver"),
        "app.models": ("L5 MUST NOT import L7 models directly", "Route through L6 driver"),
    },
    "L3_adapters": {
        "sqlmodel": ("L3 MUST NOT access DB", "Delegate to L5 engine or L6 driver"),
        "sqlalchemy": ("L3 MUST NOT access DB", "Delegate to L5 engine or L6 driver"),
        "app.models": ("L3 MUST NOT import L7 models", "Use L5 schemas for data contracts"),
        "session.commit": ("L3 MUST NOT commit (L4 owns transactions)", "Remove commit, L4 handles"),
    },
    "L2_api": {
        "L5_engines": ("L2 MUST NOT import L5 directly", "Route through L3 adapter"),
        "L6_drivers": ("L2 MUST NOT import L6", "Route through L3 → L5 → L6"),
        "app.models": ("L2 MUST NOT import L7 models", "Use L5 schemas or response models"),
    },
}


def detect_violations(identity: FileIdentity) -> List[Violation]:
    """Detect layer contract violations from imports."""
    violations = []
    patterns = VIOLATION_PATTERNS.get(identity.layer, {})

    for imp in identity.imports:
        module = imp.module
        for pattern, (rule, fix) in patterns.items():
            if pattern in module:
                # Special case: L5 importing Session for type hints only
                # is still flagged — the script flags, humans decide
                violations.append(Violation(
                    file_path=identity.file_path,
                    file_name=identity.file_name,
                    domain=identity.domain,
                    layer=identity.layer,
                    import_statement=f"from {module} import {', '.join(imp.names)}",
                    rule_broken=rule,
                    required_fix=fix,
                    line=imp.line,
                ))

    return violations


# ---------------------------------------------------------------------------
# Gap Detection
# ---------------------------------------------------------------------------


def detect_gaps(domain: str, wiring: DomainWiring) -> List[Gap]:
    """Detect missing pieces in domain wiring."""
    gaps = []

    # L2.1 Facade gap (all domains)
    facade_dir = BACKEND_ROOT / "app" / "hoc" / "api" / "facades" / "cus"
    facade_exists = False
    if facade_dir.exists():
        for f in facade_dir.glob("*.py"):
            if domain in f.name.lower():
                facade_exists = True
                break
    if not facade_exists and wiring.l2_apis:
        l2_routers = [f.file_name for f in wiring.l2_apis]
        gaps.append(Gap(
            domain=domain,
            gap_type="L2.1_facade",
            description=f"No L2.1 facade to group {len(l2_routers)} L2 routers",
            action=f"Build hoc/api/facades/cus/{domain}.py grouping: {', '.join(l2_routers)}",
            related_files=[f.file_path for f in wiring.l2_apis],
        ))

    # L2 API gap
    if not wiring.l2_apis and (wiring.l5_engines or wiring.l6_drivers):
        gaps.append(Gap(
            domain=domain,
            gap_type="L2_api",
            description=f"No L2 API routes but {len(wiring.l5_engines)} engines exist",
            action=f"Build hoc/api/cus/{domain}/ with route handlers",
            related_files=[f.file_path for f in wiring.l5_engines],
        ))

    # L3 Adapter gaps — check each L5 engine has an L3 bridge
    if wiring.l5_engines and not wiring.l3_adapters:
        gaps.append(Gap(
            domain=domain,
            gap_type="L3_adapter",
            description=f"No L3 adapters but {len(wiring.l5_engines)} L5 engines exist — L2 cannot reach L5",
            action=f"Build hoc/cus/{domain}/L3_adapters/ with domain adapter(s)",
            related_files=[f.file_path for f in wiring.l5_engines],
        ))

    # L6 Driver gaps — check L5 engines that import DB directly (need L6)
    l6_names = {f.file_name for f in wiring.l6_drivers}
    for eng in wiring.l5_engines:
        has_db_import = any(
            "sqlmodel" in imp.module or "sqlalchemy" in imp.module or "app.db" in imp.module
            for imp in eng.imports
        )
        if has_db_import:
            # Check if a corresponding driver exists
            engine_stem = eng.file_name.replace("_engine.py", "").replace("_facade.py", "")
            matching_driver = any(engine_stem in d for d in l6_names)
            if not matching_driver:
                gaps.append(Gap(
                    domain=domain,
                    gap_type="L6_driver",
                    description=f"{eng.file_name} has DB imports but no matching L6 driver",
                    action=f"Extract DB logic to hoc/cus/{domain}/L6_drivers/{engine_stem}_driver.py",
                    related_files=[eng.file_path],
                ))

    # L7 Model gaps — L6 drivers that import models not in domain models
    if wiring.l6_drivers:
        has_domain_models = bool(wiring.l7_models)
        if not has_domain_models:
            gaps.append(Gap(
                domain=domain,
                gap_type="L7_models",
                description=f"{len(wiring.l6_drivers)} L6 drivers but no domain-specific L7 models",
                action="FLAG: domain-localized data candidate (human decision)",
                related_files=[f.file_path for f in wiring.l6_drivers],
            ))

    return gaps


# ---------------------------------------------------------------------------
# L7 Model Classification (3 buckets)
# ---------------------------------------------------------------------------


def classify_l7_models(
    all_identities: List[FileIdentity],
    model_files: List[FileIdentity],
) -> List[L7ModelClassification]:
    """Classify L7 models into system_invariant / domain_owned / cross_domain_fact."""
    classifications = []

    # Build reverse map: which domains' L6 drivers import each model
    model_usage: Dict[str, Set[str]] = {}  # model_file -> set of domains
    model_drivers: Dict[str, List[str]] = {}  # model_file -> list of driver paths

    for identity in all_identities:
        if identity.layer != "L6_drivers":
            continue
        for imp in identity.imports:
            if "app.models" in imp.module or "app/models" in imp.module:
                # Extract model file name from import
                parts = imp.module.split(".")
                if len(parts) >= 3:
                    model_name = parts[-1]
                else:
                    model_name = imp.module
                model_usage.setdefault(model_name, set()).add(identity.domain)
                model_drivers.setdefault(model_name, []).append(identity.file_path)

    for mf in model_files:
        model_stem = mf.file_name.replace(".py", "")
        domains_using = model_usage.get(model_stem, set())
        drivers_using = model_drivers.get(model_stem, [])

        # Bucket 1: System invariant
        if model_stem in SYSTEM_INVARIANT_MODELS:
            bucket = "system_invariant"
            action = "STAYS in app/models/ — system invariant"
        # Bucket 2: Used by exactly 1 domain
        elif len(domains_using) == 1:
            bucket = "domain_owned"
            action = "FLAG: domain-localized data candidate (human decision)"
        # Bucket 3: Used by 0 or 2+ domains
        elif len(domains_using) >= 2:
            bucket = "cross_domain_fact"
            action = "STAYS shared — cross-domain fact table"
        else:
            # No L6 driver references found — might be unused or referenced differently
            bucket = "domain_owned"
            action = "FLAG: no L6 driver references found — verify usage (human decision)"

        classifications.append(L7ModelClassification(
            model_name=model_stem,
            file_path=mf.file_path,
            bucket=bucket,
            used_by_domains=sorted(domains_using),
            used_by_drivers=drivers_using,
            action=action,
        ))

    return classifications


# ---------------------------------------------------------------------------
# Caller Discovery (ripgrep-based)
# ---------------------------------------------------------------------------


def find_callers(file_path: str, module_name: str) -> List[Tuple[str, str]]:
    """Find files that import from this module using ripgrep."""
    # Build search pattern from file's module path
    # e.g., hoc/cus/controls/L5_engines/killswitch.py -> multiple patterns
    patterns = []

    # Pattern 1: absolute import
    # from app.hoc.cus.controls.L5_engines.killswitch import
    path_parts = file_path.replace("backend/", "").replace("/", ".").replace(".py", "")
    patterns.append(f"from {path_parts}")

    # Pattern 2: shorter relative
    # from ...L5_engines.killswitch import
    stem = Path(file_path).stem
    patterns.append(f"from.*{stem} import")

    callers = []
    for pattern in patterns:
        try:
            result = subprocess.run(
                ["rg", "-l", "--type", "py", pattern, str(BACKEND_ROOT)],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line.strip() and line.strip() != file_path:
                        callers.append((line.strip(), pattern))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Deduplicate by file path
    seen = set()
    unique = []
    for caller_path, pattern in callers:
        if caller_path not in seen:
            seen.add(caller_path)
            unique.append((caller_path, pattern))

    return unique


# ---------------------------------------------------------------------------
# CSV Reader
# ---------------------------------------------------------------------------


def read_audit_csv(csv_path: Path) -> Dict[str, Dict[str, List[str]]]:
    """Read the audit CSV and return {domain: {layer: [file_paths]}}."""
    inventory: Dict[str, Dict[str, List[str]]] = {}

    # Column mapping: CSV columns -> layer keys
    # CSV has triplets: "LX Count", "LX File Names", "LX File Paths"
    layer_columns = {
        4: "L2.1_facade",   # L2.1 File Paths
        7: "L2_api",        # L2 File Paths
        10: "L3_adapters",  # L3 File Paths
        13: "L4_runtime",   # L4 File Paths
        16: "L5",           # L5 File Paths (combined engines+schemas+other)
        19: "L6_drivers",   # L6 File Paths
        22: "L7_models",    # L7 File Paths
    }

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header

        for row in reader:
            if not row or not row[0] or row[0] == "" or row[1] == "TOTAL":
                continue

            domain = row[1].strip()
            if not domain:
                continue

            inventory[domain] = {}
            for col_idx, layer_key in layer_columns.items():
                if col_idx < len(row) and row[col_idx].strip():
                    paths = [p.strip() for p in row[col_idx].strip().split("\n") if p.strip()]
                    inventory[domain][layer_key] = paths
                else:
                    inventory[domain][layer_key] = []

    return inventory


# ---------------------------------------------------------------------------
# Markdown Generation
# ---------------------------------------------------------------------------


def generate_file_section(identity: FileIdentity, violations: List[Violation],
                          callers: List[Tuple[str, str]]) -> str:
    """Generate markdown section for a single file."""
    lines = []
    lines.append(f"## {identity.file_name}")
    lines.append(f"**Path:** `{identity.file_path}`  ")
    lines.append(f"**Layer:** {identity.layer} | **Domain:** {identity.domain} | **Lines:** {identity.lines}")
    lines.append("")

    # Module docstring
    if identity.module_docstring:
        doc = identity.module_docstring.split("\n")[0][:200]
        lines.append(f"**Docstring:** {doc}")
        lines.append("")

    # Identity — Classes
    if identity.classes:
        lines.append("### Classes")
        lines.append("| Name | Methods | Docstring |")
        lines.append("|------|---------|-----------|")
        for cls in identity.classes:
            doc = (cls.docstring or "").split("\n")[0][:100]
            methods = ", ".join(cls.methods[:8])
            if len(cls.methods) > 8:
                methods += f" (+{len(cls.methods) - 8} more)"
            lines.append(f"| `{cls.name}` | {methods} | {doc} |")
        lines.append("")

    # Identity — Functions
    if identity.functions:
        lines.append("### Functions")
        lines.append("| Name | Signature | Async | Docstring |")
        lines.append("|------|-----------|-------|-----------|")
        for fn in identity.functions:
            doc = (fn.docstring or "").split("\n")[0][:80]
            sig = fn.signature[:80]
            lines.append(f"| `{fn.name}` | `{sig}` | {'yes' if fn.is_async else 'no'} | {doc} |")
        lines.append("")

    # Imports
    if identity.imports:
        lines.append("### Imports")
        lines.append("| Module | Names | Relative |")
        lines.append("|--------|-------|----------|")
        for imp in identity.imports:
            names = ", ".join(imp.names[:5])
            if len(imp.names) > 5:
                names += f" (+{len(imp.names) - 5})"
            lines.append(f"| `{imp.module}` | {names} | {'yes' if imp.is_relative else 'no'} |")
        lines.append("")

    # Prescriptive Wiring
    contract = LAYER_CONTRACT.get(identity.layer, {})
    if contract:
        lines.append("### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)")
        lines.append("")
        lines.append(f"**Contract:** {contract.get('contract', 'N/A')}")
        lines.append("")

        should_call = contract.get("should_call", [])
        if should_call:
            lines.append(f"**SHOULD call:** {', '.join(should_call)}")

        must_not = contract.get("must_not_call", [])
        if must_not:
            lines.append(f"**MUST NOT call:** {', '.join(must_not)}")

        called_by = contract.get("called_by", [])
        if called_by:
            lines.append(f"**Called by:** {', '.join(called_by)}")

        lines.append("")

    # Callers found
    if callers:
        lines.append("### Current Callers (for reference — may need restructuring)")
        lines.append("| Caller File | Pattern |")
        lines.append("|-------------|---------|")
        for caller_path, pattern in callers[:15]:
            lines.append(f"| `{caller_path}` | `{pattern}` |")
        if len(callers) > 15:
            lines.append(f"| ... | +{len(callers) - 15} more |")
        lines.append("")

    # Violations
    file_violations = [v for v in violations if v.file_path == identity.file_path]
    if file_violations:
        lines.append("### Violations")
        lines.append("| Import | Rule Broken | Required Fix | Line |")
        lines.append("|--------|-------------|-------------|------|")
        for v in file_violations:
            lines.append(f"| `{v.import_statement}` | {v.rule_broken} | {v.required_fix} | {v.line} |")
        lines.append("")

    # Constants
    if identity.constants:
        lines.append("### Constants")
        lines.append(", ".join(f"`{c.name}`" for c in identity.constants))
        lines.append("")

    # __all__
    if identity.all_exports:
        lines.append("### __all__ Exports")
        lines.append(", ".join(f"`{e}`" for e in identity.all_exports))
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def generate_layer_md(domain: str, layer: str, identities: List[FileIdentity],
                      violations: List[Violation], all_callers: Dict[str, List]) -> str:
    """Generate markdown for one layer within one domain."""
    lines = []
    layer_display = layer.replace("_", " ").title()
    lines.append(f"# {domain.title()} — {layer_display} ({len(identities)} files)")
    lines.append("")
    lines.append(f"**Domain:** {domain}  ")
    lines.append(f"**Layer:** {layer}  ")
    lines.append(f"**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)")
    lines.append("")

    contract = LAYER_CONTRACT.get(layer, {})
    if contract:
        lines.append(f"**Layer Contract:** {contract.get('contract', 'N/A')}")
        lines.append("")

    lines.append("---")
    lines.append("")

    for identity in sorted(identities, key=lambda x: x.file_name):
        callers = all_callers.get(identity.file_path, [])
        lines.append(generate_file_section(identity, violations, callers))

    return "\n".join(lines)


def generate_domain_wiring_map(domain: str, wiring: DomainWiring) -> str:
    """Generate the vertical wiring map for a domain."""
    lines = []
    lines.append(f"# {domain.title()} — Prescriptive Wiring Map")
    lines.append("")
    lines.append("**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)")
    lines.append("")
    lines.append("## Target State")
    lines.append("")

    # L2.1 Facade
    if wiring.l2_1_facade:
        lines.append(f"L2.1 Facade: `{wiring.l2_1_facade}` ✅")
    else:
        lines.append(f"L2.1 Facade: `hoc/api/facades/cus/{domain}.py` — **TO BUILD**")
    lines.append("  │")

    # L2 APIs
    l2_count = len(wiring.l2_apis)
    if l2_count:
        lines.append(f"  └──→ L2 API: `hoc/api/cus/{domain}/` ({l2_count} files)")
        for f in wiring.l2_apis[:5]:
            lines.append(f"         ├── {f.file_name}")
        if l2_count > 5:
            lines.append(f"         └── ... (+{l2_count - 5} more)")
    else:
        lines.append(f"  └──→ L2 API: `hoc/api/cus/{domain}/` — **GAP** (0 files)")
    lines.append("         │")

    # L3 Adapters
    l3_count = len(wiring.l3_adapters)
    if l3_count:
        lines.append(f"         └──→ L3 Adapters ({l3_count} files)")
        for f in wiring.l3_adapters:
            lines.append(f"                ├── {f.file_name} ✅")
    else:
        lines.append(f"         └──→ L3 Adapters — **GAP** (0 files, need domain adapter)")
    lines.append("                │")

    # L4 Runtime (general only)
    if domain == "general":
        l4_count = len(wiring.l4_runtime)
        lines.append(f"                └──→ L4 Runtime ({l4_count} files)")
        for f in wiring.l4_runtime[:5]:
            lines.append(f"                       ├── {f.file_name}")
        if l4_count > 5:
            lines.append(f"                       └── ... (+{l4_count - 5} more)")
        lines.append("                       │")
    else:
        lines.append(f"                ├──→ L4 Runtime (via general/L4_runtime/)")

    # L5 Engines
    l5_count = len(wiring.l5_engines)
    l5s_count = len(wiring.l5_schemas)
    l5o_count = len(wiring.l5_other)
    lines.append("                │")
    if l5_count:
        lines.append(f"                └──→ L5 Engines ({l5_count} files)")
        # Show which have matching L6 drivers
        l6_names = {f.file_name for f in wiring.l6_drivers}
        for f in wiring.l5_engines[:10]:
            stem = f.file_name.replace("_engine.py", "").replace("_facade.py", "")
            has_driver = any(stem in d for d in l6_names)
            status = "→ L6 ✅" if has_driver else "→ L6 ❌ (no matching driver)"
            lines.append(f"                       ├── {f.file_name} {status}")
        if l5_count > 10:
            lines.append(f"                       └── ... (+{l5_count - 10} more)")
    else:
        lines.append(f"                └──→ L5 Engines — **GAP** (0 files)")

    if l5s_count:
        lines.append(f"                     L5 Schemas ({l5s_count} files)")
    if l5o_count:
        lines.append(f"                     L5 Other ({l5o_count} files)")

    lines.append("                       │")

    # L6 Drivers
    l6_count = len(wiring.l6_drivers)
    if l6_count:
        lines.append(f"                       └──→ L6 Drivers ({l6_count} files)")
        for f in wiring.l6_drivers[:8]:
            lines.append(f"                              ├── {f.file_name}")
        if l6_count > 8:
            lines.append(f"                              └── ... (+{l6_count - 8} more)")
    else:
        lines.append(f"                       └──→ L6 Drivers — **GAP** (0 files)")
    lines.append("                              │")

    # L7 Models
    l7_count = len(wiring.l7_models)
    if l7_count:
        lines.append(f"                              └──→ L7 Models ({l7_count} files)")
        for f in wiring.l7_models:
            lines.append(f"                                     ├── {f.file_name}")
    else:
        lines.append(f"                              └──→ L7 Models — **GAP** (no domain models)")
        lines.append(f"                                     FLAG: domain-localized data candidate (human decision)")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Gaps summary
    if wiring.gaps:
        lines.append("## Gaps")
        lines.append("")
        lines.append("| Type | Description | Action |")
        lines.append("|------|-------------|--------|")
        for gap in wiring.gaps:
            lines.append(f"| {gap.gap_type} | {gap.description} | {gap.action} |")
        lines.append("")

    # Violations summary
    if wiring.violations:
        lines.append("## Violations")
        lines.append("")
        lines.append("| File | Import | Rule Broken | Fix |")
        lines.append("|------|--------|-------------|-----|")
        for v in wiring.violations[:20]:
            lines.append(f"| `{v.file_name}` | `{v.import_statement[:60]}` | {v.rule_broken} | {v.required_fix} |")
        if len(wiring.violations) > 20:
            lines.append(f"| ... | +{len(wiring.violations) - 20} more | | |")
        lines.append("")

    return "\n".join(lines)


def generate_gap_register(all_gaps: List[Gap], model_classifications: List[L7ModelClassification]) -> str:
    """Generate the aggregated gap register."""
    lines = []
    lines.append("# GAP REGISTER")
    lines.append("")
    lines.append("**Generated by:** `scripts/ops/hoc_literature_generator.py`  ")
    lines.append("**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)")
    lines.append("")

    # Group by gap type
    by_type: Dict[str, List[Gap]] = {}
    for gap in all_gaps:
        by_type.setdefault(gap.gap_type, []).append(gap)

    for gap_type in ["L2.1_facade", "L2_api", "L3_adapter", "L6_driver", "L7_models"]:
        gaps = by_type.get(gap_type, [])
        lines.append(f"## {gap_type.replace('_', ' ').title()} Gaps ({len(gaps)})")
        lines.append("")
        if gaps:
            lines.append("| Domain | Description | Action |")
            lines.append("|--------|-------------|--------|")
            for gap in gaps:
                lines.append(f"| {gap.domain} | {gap.description} | {gap.action} |")
        else:
            lines.append("None.")
        lines.append("")

    # L7 Model Classification
    lines.append("## L7 Model Classification")
    lines.append("")
    lines.append("Models fall into 3 buckets:")
    lines.append("1. **System Invariant** — never move (tenant, base, audit)")
    lines.append("2. **Domain-Owned** — eligible for domain models (human decision)")
    lines.append("3. **Cross-Domain Fact** — shared, consumed by multiple domains")
    lines.append("")

    for bucket in ["system_invariant", "domain_owned", "cross_domain_fact"]:
        models = [m for m in model_classifications if m.bucket == bucket]
        bucket_display = bucket.replace("_", " ").title()
        lines.append(f"### {bucket_display} ({len(models)})")
        lines.append("")
        if models:
            lines.append("| Model | Domains Using | Drivers | Action |")
            lines.append("|-------|---------------|---------|--------|")
            for m in models:
                domains = ", ".join(m.used_by_domains) if m.used_by_domains else "none found"
                driver_count = len(m.used_by_drivers)
                lines.append(f"| `{m.model_name}` | {domains} | {driver_count} | {m.action} |")
        else:
            lines.append("None.")
        lines.append("")

    return "\n".join(lines)


def generate_violations_md(all_violations: List[Violation]) -> str:
    """Generate aggregated violations document."""
    lines = []
    lines.append("# WIRING VIOLATIONS")
    lines.append("")
    lines.append("**Generated by:** `scripts/ops/hoc_literature_generator.py`  ")
    lines.append("**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)")
    lines.append("")
    lines.append(f"**Total violations:** {len(all_violations)}")
    lines.append("")

    # Group by domain
    by_domain: Dict[str, List[Violation]] = {}
    for v in all_violations:
        by_domain.setdefault(v.domain, []).append(v)

    for domain in DOMAINS_ORDERED:
        violations = by_domain.get(domain, [])
        lines.append(f"## {domain.title()} ({len(violations)} violations)")
        lines.append("")
        if violations:
            lines.append("| File | Layer | Import | Rule | Fix | Line |")
            lines.append("|------|-------|--------|------|-----|------|")
            for v in violations:
                lines.append(
                    f"| `{v.file_name}` | {v.layer} "
                    f"| `{v.import_statement[:50]}` | {v.rule_broken} "
                    f"| {v.required_fix} | {v.line} |"
                )
        else:
            lines.append("No violations.")
        lines.append("")

    return "\n".join(lines)


def generate_index(domain_wirings: Dict[str, DomainWiring],
                   all_violations: List[Violation],
                   all_gaps: List[Gap]) -> str:
    """Generate the literature index with health scores."""
    lines = []
    lines.append("# HOC LITERATURE INDEX")
    lines.append("")
    lines.append("**Generated by:** `scripts/ops/hoc_literature_generator.py`  ")
    lines.append("**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)")
    lines.append("")

    # DISCLAIMER
    lines.append("## ⚠️ Health Score Disclaimer")
    lines.append("")
    lines.append("> **Health scores measure CONFORMANCE TO TOPOLOGY RULES ONLY.**")
    lines.append(">")
    lines.append("> They do NOT indicate:")
    lines.append("> - Feature completeness")
    lines.append("> - Production readiness")
    lines.append("> - Code quality")
    lines.append("> - Test coverage")
    lines.append(">")
    lines.append("> A domain with 100% conformance may still be missing features.")
    lines.append("> A domain with 40% conformance may work perfectly in production.")
    lines.append("> These scores guide restructuring priority, nothing more.")
    lines.append("")

    # Summary table
    lines.append("## Domain Summary")
    lines.append("")
    lines.append("| # | Domain | L2.1 | L2 | L3 | L4 | L5 | L6 | L7 | Violations | Gaps | Conformance |")
    lines.append("|---|--------|------|----|----|----|----|----|----|-----------|------|-------------|")

    for i, domain in enumerate(DOMAINS_ORDERED, 1):
        w = domain_wirings.get(domain)
        if not w:
            continue
        l2_1 = "✅" if w.l2_1_facade else "❌"
        l2 = len(w.l2_apis)
        l3 = len(w.l3_adapters)
        l4 = len(w.l4_runtime) if domain == "general" else "—"
        l5 = len(w.l5_engines) + len(w.l5_schemas) + len(w.l5_other)
        l6 = len(w.l6_drivers)
        l7 = len(w.l7_models)
        v_count = len(w.violations)
        g_count = len(w.gaps)

        # Conformance = (layers present without gaps) / (layers expected)
        expected = 5  # L2.1, L2, L3, L5, L6 (L4 only for general, L7 separate)
        if domain == "general":
            expected = 6
        present = sum([
            1 if w.l2_1_facade else 0,
            1 if w.l2_apis else 0,
            1 if w.l3_adapters else 0,
            1 if domain == "general" and w.l4_runtime else 0,
            1 if w.l5_engines else 0,
            1 if w.l6_drivers else 0,
        ])
        conformance = f"{int(present / expected * 100)}%"

        lines.append(
            f"| {i} | {domain} | {l2_1} | {l2} | {l3} | {l4} | {l5} | {l6} | {l7} "
            f"| {v_count} | {g_count} | {conformance} |"
        )

    lines.append("")

    # TOC
    lines.append("## Table of Contents")
    lines.append("")
    for i, domain in enumerate(DOMAINS_ORDERED, 1):
        prefix = f"{i:02d}"
        lines.append(f"### {i}. {domain.title()}")
        lines.append(f"- [{domain}/DOMAIN_WIRING_MAP.md]({prefix}_{domain}/DOMAIN_WIRING_MAP.md)")
        w = domain_wirings.get(domain)
        if w:
            if w.l2_apis:
                lines.append(f"- [{domain}/L2_apis.md]({prefix}_{domain}/L2_apis.md)")
            if w.l3_adapters:
                lines.append(f"- [{domain}/L3_adapters.md]({prefix}_{domain}/L3_adapters.md)")
            if domain == "general" and w.l4_runtime:
                lines.append(f"- [{domain}/L4_runtime.md]({prefix}_{domain}/L4_runtime.md)")
            if w.l5_engines:
                lines.append(f"- [{domain}/L5_engines.md]({prefix}_{domain}/L5_engines.md)")
            if w.l5_schemas:
                lines.append(f"- [{domain}/L5_schemas.md]({prefix}_{domain}/L5_schemas.md)")
            if w.l5_other:
                lines.append(f"- [{domain}/L5_other.md]({prefix}_{domain}/L5_other.md)")
            if w.l6_drivers:
                lines.append(f"- [{domain}/L6_drivers.md]({prefix}_{domain}/L6_drivers.md)")
            if w.l7_models:
                lines.append(f"- [{domain}/L7_models.md]({prefix}_{domain}/L7_models.md)")
        lines.append("")

    # Cross-references
    lines.append("## Cross-Domain Documents")
    lines.append("- [GAP_REGISTER.md](GAP_REGISTER.md)")
    lines.append("- [WIRING_VIOLATIONS.md](WIRING_VIOLATIONS.md)")
    lines.append("- [literature_index.json](literature_index.json)")
    lines.append("- [gap_register.json](gap_register.json)")
    lines.append("- [violations.json](violations.json)")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON Output
# ---------------------------------------------------------------------------


def identity_to_dict(identity: FileIdentity) -> Dict[str, Any]:
    """Convert FileIdentity to JSON-safe dict."""
    return {
        "file_name": identity.file_name,
        "file_path": identity.file_path,
        "layer": identity.layer,
        "domain": identity.domain,
        "lines": identity.lines,
        "module_docstring": identity.module_docstring,
        "functions": [
            {"name": f.name, "signature": f.signature,
             "docstring": f.docstring, "is_async": f.is_async, "line": f.line}
            for f in identity.functions
        ],
        "classes": [
            {"name": c.name, "docstring": c.docstring,
             "methods": c.methods, "line": c.line}
            for c in identity.classes
        ],
        "imports": [
            {"module": i.module, "names": i.names,
             "is_relative": i.is_relative, "line": i.line}
            for i in identity.imports
        ],
        "constants": [{"name": c.name, "line": c.line} for c in identity.constants],
        "all_exports": identity.all_exports,
    }


def generate_json_outputs(
    domain_wirings: Dict[str, DomainWiring],
    all_violations: List[Violation],
    all_gaps: List[Gap],
    model_classifications: List[L7ModelClassification],
    output_dir: Path,
):
    """Generate machine-readable JSON outputs."""

    # literature_index.json
    index = {}
    for domain, w in domain_wirings.items():
        total_files = (
            len(w.l2_apis) + len(w.l3_adapters) + len(w.l4_runtime)
            + len(w.l5_engines) + len(w.l5_schemas) + len(w.l5_other)
            + len(w.l6_drivers) + len(w.l7_models)
        )
        index[domain] = {
            "l2_1_facade": w.l2_1_facade,
            "l2_apis": [identity_to_dict(f) for f in w.l2_apis],
            "l3_adapters": [identity_to_dict(f) for f in w.l3_adapters],
            "l4_runtime": [identity_to_dict(f) for f in w.l4_runtime],
            "l5_engines": [identity_to_dict(f) for f in w.l5_engines],
            "l5_schemas": [identity_to_dict(f) for f in w.l5_schemas],
            "l5_other": [identity_to_dict(f) for f in w.l5_other],
            "l6_drivers": [identity_to_dict(f) for f in w.l6_drivers],
            "l7_models": [identity_to_dict(f) for f in w.l7_models],
            "total_files": total_files,
            "violation_count": len(w.violations),
            "gap_count": len(w.gaps),
        }

    with open(output_dir / "literature_index.json", "w") as f:
        json.dump(index, f, indent=2, default=str)

    # gap_register.json
    gaps_json = [
        {
            "domain": g.domain,
            "gap_type": g.gap_type,
            "description": g.description,
            "action": g.action,
            "related_files": g.related_files,
        }
        for g in all_gaps
    ]
    model_class_json = [asdict(m) for m in model_classifications]

    with open(output_dir / "gap_register.json", "w") as f:
        json.dump({"gaps": gaps_json, "l7_model_classification": model_class_json},
                  f, indent=2, default=str)

    # violations.json
    violations_json = [
        {
            "file_path": v.file_path,
            "file_name": v.file_name,
            "domain": v.domain,
            "layer": v.layer,
            "import_statement": v.import_statement,
            "rule_broken": v.rule_broken,
            "required_fix": v.required_fix,
            "line": v.line,
        }
        for v in all_violations
    ]
    with open(output_dir / "violations.json", "w") as f:
        json.dump(violations_json, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HOC Literature Generator")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Input audit CSV")
    parser.add_argument("--output", default=str(OUTPUT_DIR), help="Output directory")
    parser.add_argument("--skip-callers", action="store_true",
                        help="Skip caller discovery (faster)")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    output_dir = Path(args.output)

    print("=" * 70)
    print("HOC LITERATURE GENERATOR")
    print("Reference: HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)")
    print("=" * 70)
    print()

    # Step 1: Read CSV inventory
    print(f"[1/8] Reading audit CSV: {csv_path}")
    inventory = read_audit_csv(csv_path)
    total_files = sum(len(paths) for d in inventory.values() for paths in d.values())
    print(f"       {len(inventory)} domains, {total_files} file paths")
    print()

    # Step 2: Parse all files
    print(f"[2/8] Parsing files with AST...")
    all_identities: List[FileIdentity] = []
    parse_failures = []
    files_parsed = 0

    for domain, layers in inventory.items():
        for layer, paths in layers.items():
            for file_path in paths:
                identity = parse_file(file_path)
                if identity:
                    # Override layer classification for L5 combined column
                    if layer == "L5" and identity.layer == "UNKNOWN":
                        identity.layer = "L5_engines"
                    all_identities.append(identity)
                    files_parsed += 1
                else:
                    parse_failures.append(file_path)

    print(f"       Parsed: {files_parsed} | Failed: {len(parse_failures)}")
    if parse_failures:
        for pf in parse_failures[:5]:
            print(f"         FAILED: {pf}")
    print()

    # Step 3: Detect violations
    print(f"[3/8] Detecting layer violations...")
    all_violations: List[Violation] = []
    for identity in all_identities:
        violations = detect_violations(identity)
        all_violations.extend(violations)
    print(f"       {len(all_violations)} violations found")
    print()

    # Step 4: Build domain wirings
    print(f"[4/8] Building domain wirings...")
    domain_wirings: Dict[str, DomainWiring] = {}

    for domain in DOMAINS_ORDERED:
        wiring = DomainWiring(domain=domain, l2_1_facade=None)

        # Check L2.1 facade existence
        facade_dir = BACKEND_ROOT / "app" / "hoc" / "api" / "facades" / "cus"
        if facade_dir.exists():
            for f in facade_dir.glob("*.py"):
                if domain in f.name.lower():
                    wiring.l2_1_facade = str(f)

        # Populate layers
        for identity in all_identities:
            if identity.domain != domain:
                continue
            if identity.layer == "L2_api":
                wiring.l2_apis.append(identity)
            elif identity.layer == "L3_adapters":
                wiring.l3_adapters.append(identity)
            elif identity.layer == "L4_runtime":
                wiring.l4_runtime.append(identity)
            elif identity.layer == "L5_engines":
                wiring.l5_engines.append(identity)
            elif identity.layer == "L5_schemas":
                wiring.l5_schemas.append(identity)
            elif identity.layer in ("L5_other",):
                wiring.l5_other.append(identity)
            elif identity.layer == "L6_drivers":
                wiring.l6_drivers.append(identity)
            elif identity.layer == "L7_models":
                wiring.l7_models.append(identity)

        # Violations for this domain
        wiring.violations = [v for v in all_violations if v.domain == domain]

        # Gaps
        wiring.gaps = detect_gaps(domain, wiring)

        domain_wirings[domain] = wiring
        print(f"       {domain}: L2={len(wiring.l2_apis)} L3={len(wiring.l3_adapters)} "
              f"L5={len(wiring.l5_engines)} L6={len(wiring.l6_drivers)} "
              f"gaps={len(wiring.gaps)} violations={len(wiring.violations)}")

    print()

    # Step 5: Caller discovery (optional)
    all_callers: Dict[str, List] = {}
    if not args.skip_callers:
        print(f"[5/8] Discovering callers (ripgrep)...")
        for identity in all_identities:
            callers = find_callers(identity.file_path, identity.file_name.replace(".py", ""))
            if callers:
                all_callers[identity.file_path] = callers
        print(f"       {len(all_callers)} files have callers")
    else:
        print(f"[5/8] Skipping caller discovery (--skip-callers)")
    print()

    # Step 6: Classify L7 models
    print(f"[6/8] Classifying L7 models...")
    model_files = [i for i in all_identities if i.layer == "L7_models"]
    model_classifications = classify_l7_models(all_identities, model_files)
    for bucket in ["system_invariant", "domain_owned", "cross_domain_fact"]:
        count = sum(1 for m in model_classifications if m.bucket == bucket)
        print(f"       {bucket}: {count}")
    print()

    # Step 7: Generate outputs
    print(f"[7/8] Generating outputs to {output_dir}/")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_gaps: List[Gap] = []
    for w in domain_wirings.values():
        all_gaps.extend(w.gaps)

    # Per-domain directories and files
    for i, domain in enumerate(DOMAINS_ORDERED, 1):
        wiring = domain_wirings.get(domain)
        if not wiring:
            continue

        domain_dir = output_dir / f"{i:02d}_{domain}"
        domain_dir.mkdir(parents=True, exist_ok=True)

        # Domain wiring map
        wiring_md = generate_domain_wiring_map(domain, wiring)
        (domain_dir / "DOMAIN_WIRING_MAP.md").write_text(wiring_md, encoding="utf-8")

        # Per-layer markdown
        layer_groups = [
            ("L2_apis", wiring.l2_apis),
            ("L3_adapters", wiring.l3_adapters),
            ("L4_runtime", wiring.l4_runtime),
            ("L5_engines", wiring.l5_engines),
            ("L5_schemas", wiring.l5_schemas),
            ("L5_other", wiring.l5_other),
            ("L6_drivers", wiring.l6_drivers),
            ("L7_models", wiring.l7_models),
        ]
        for layer_name, identities in layer_groups:
            if not identities:
                continue
            md = generate_layer_md(domain, layer_name, identities,
                                   wiring.violations, all_callers)
            (domain_dir / f"{layer_name}.md").write_text(md, encoding="utf-8")

        print(f"       {i:02d}_{domain}/: wiring map + {sum(1 for _, ids in layer_groups if ids)} layer files")

    # Cross-domain documents
    gap_md = generate_gap_register(all_gaps, model_classifications)
    (output_dir / "GAP_REGISTER.md").write_text(gap_md, encoding="utf-8")

    violations_md = generate_violations_md(all_violations)
    (output_dir / "WIRING_VIOLATIONS.md").write_text(violations_md, encoding="utf-8")

    index_md = generate_index(domain_wirings, all_violations, all_gaps)
    (output_dir / "LITERATURE_INDEX.md").write_text(index_md, encoding="utf-8")

    # JSON outputs
    generate_json_outputs(domain_wirings, all_violations, all_gaps,
                          model_classifications, output_dir)

    print()

    # Step 8: Verification
    print(f"[8/8] Verification...")
    print(f"       CSV file paths:  {total_files}")
    print(f"       Files parsed:    {files_parsed}")
    print(f"       Parse failures:  {len(parse_failures)}")
    if files_parsed + len(parse_failures) != total_files:
        print(f"       ⚠️  MISMATCH: parsed + failed ({files_parsed + len(parse_failures)}) != CSV total ({total_files})")
    else:
        print(f"       ✅ MATCH: all {total_files} files accounted for")
    print()

    print(f"       Total violations: {len(all_violations)}")
    print(f"       Total gaps:       {len(all_gaps)}")
    print()

    # Summary
    print("=" * 70)
    print("OUTPUTS")
    print("=" * 70)
    print(f"  Markdown:  {output_dir}/LITERATURE_INDEX.md")
    print(f"  Markdown:  {output_dir}/GAP_REGISTER.md")
    print(f"  Markdown:  {output_dir}/WIRING_VIOLATIONS.md")
    print(f"  JSON:      {output_dir}/literature_index.json")
    print(f"  JSON:      {output_dir}/gap_register.json")
    print(f"  JSON:      {output_dir}/violations.json")
    for i, domain in enumerate(DOMAINS_ORDERED, 1):
        print(f"  Domain:    {output_dir}/{i:02d}_{domain}/")
    print()


if __name__ == "__main__":
    main()
