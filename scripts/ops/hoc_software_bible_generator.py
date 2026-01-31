#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Generate per-domain SOFTWARE_BIBLE.md — end-to-end feature traces (L2→L4→L5→L6→L7) with canonical owners and authority map
# artifact_class: CODE

"""
HOC Software Bible Generator

Combines data from:
  - FUNCTION_INVENTORY.csv (with intent + placement)
  - CALL_CHAINS.csv (with roles + delegation)
  - L2 API file scanning (entry points)
  - L4 spine scanning (orchestration)

Produces:
  - Per-domain SOFTWARE_BIBLE.md with end-to-end feature traces
  - AUTHORITY_MAP.md — which domain owns which noun/concept

Usage:
    python3 scripts/ops/hoc_software_bible_generator.py
    python3 scripts/ops/hoc_software_bible_generator.py --domain incidents
    python3 scripts/ops/hoc_software_bible_generator.py --json
"""

import argparse
import ast
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUS_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc" / "cus"
HOC_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc"
L2_API_ROOT = HOC_ROOT / "api" / "cus"
L4_SPINE_ROOT = HOC_ROOT / "hoc_spine"
MODELS_ROOT = PROJECT_ROOT / "backend" / "app" / "models"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "literature" / "hoc_domain"
INVENTORY_PATH = PROJECT_ROOT / "literature" / "hoc_domain" / "FUNCTION_INVENTORY.csv"
CALL_CHAINS_PATH = PROJECT_ROOT / "literature" / "hoc_domain" / "CALL_CHAINS.csv"

ALL_DOMAINS = [
    "account", "activity", "analytics", "api_keys", "apis",
    "controls", "docs", "incidents", "integrations", "logs",
    "overview", "policies",
]


# ---------------------------------------------------------------------------
# L2 Entry Point Scanning
# ---------------------------------------------------------------------------


@dataclass
class L2Endpoint:
    """An HTTP endpoint defined in an L2 API file."""
    domain: str
    file: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    path: str
    function_name: str
    line: int
    calls_l5: list[str] = field(default_factory=list)  # L5 imports used
    calls_l4: list[str] = field(default_factory=list)  # L4 imports used


def scan_l2_endpoints(domain: str) -> list[L2Endpoint]:
    """Scan L2 API files for HTTP route decorators and their L5/L4 imports."""
    api_dir = L2_API_ROOT / domain
    if not api_dir.is_dir():
        return []

    endpoints: list[L2Endpoint] = []

    for pyfile in sorted(api_dir.rglob("*.py")):
        if pyfile.name == "__init__.py":
            continue
        try:
            source = pyfile.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(pyfile))
        except (SyntaxError, Exception):
            continue

        # Extract imports to identify L5/L4 dependencies
        l5_imports = []
        l4_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
                if f".cus.{domain}.L5_" in mod or f".cus.{domain}.L6_" in mod:
                    for alias in node.names:
                        l5_imports.append(alias.name)
                elif "hoc_spine" in mod or "L4_runtime" in mod:
                    for alias in node.names:
                        l4_imports.append(alias.name)

        # Find route decorators
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                method = None
                path = ""
                # @router.get("/path"), @router.post("/path")
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    method_name = dec.func.attr.upper()
                    if method_name in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                        method = method_name
                        if dec.args and isinstance(dec.args[0], ast.Constant):
                            path = str(dec.args[0].value)

                if method:
                    endpoints.append(L2Endpoint(
                        domain=domain,
                        file=pyfile.stem,
                        method=method,
                        path=path,
                        function_name=node.name,
                        line=node.lineno,
                        calls_l5=l5_imports,
                        calls_l4=l4_imports,
                    ))

    return endpoints


# ---------------------------------------------------------------------------
# L4 Spine Scanning
# ---------------------------------------------------------------------------


@dataclass
class L4Handler:
    """An L4 handler that routes to L5 engines."""
    file: str
    handler_name: str
    serves_domains: list[str] = field(default_factory=list)
    l5_imports: list[str] = field(default_factory=list)


def scan_l4_handlers() -> list[L4Handler]:
    """Scan L4 spine files to find which handlers serve which domains."""
    if not L4_SPINE_ROOT.is_dir():
        return []

    handlers: list[L4Handler] = []

    for pyfile in sorted(L4_SPINE_ROOT.rglob("*.py")):
        if pyfile.name == "__init__.py":
            continue
        try:
            source = pyfile.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(pyfile))
        except (SyntaxError, Exception):
            continue

        l5_imports: list[str] = []
        domains_served: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
                # Match app.hoc.cus.{domain}.L5_*
                m = re.match(r"app\.hoc\.cus\.(\w+)\.L5_", mod)
                if m:
                    domains_served.add(m.group(1))
                    for alias in node.names:
                        l5_imports.append(f"{m.group(1)}.{alias.name}")

        if domains_served:
            handlers.append(L4Handler(
                file=pyfile.stem,
                handler_name=pyfile.stem,
                serves_domains=sorted(domains_served),
                l5_imports=l5_imports,
            ))

    return handlers


# ---------------------------------------------------------------------------
# L7 Model Scanning
# ---------------------------------------------------------------------------


def scan_l7_models() -> dict[str, list[str]]:
    """Scan L7 model files. Returns {model_file_stem: [class_names]}."""
    if not MODELS_ROOT.is_dir():
        return {}

    models: dict[str, list[str]] = {}
    for pyfile in sorted(MODELS_ROOT.glob("*.py")):
        if pyfile.name == "__init__.py":
            continue
        try:
            source = pyfile.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(pyfile))
        except (SyntaxError, Exception):
            continue

        classes = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)

        if classes:
            models[pyfile.stem] = classes

    return models


# ---------------------------------------------------------------------------
# Feature Chain Assembly
# ---------------------------------------------------------------------------


@dataclass
class FeatureChain:
    """End-to-end trace of a customer feature."""
    name: str
    domain: str
    l2_endpoint: L2Endpoint | None = None
    l4_handler: str = ""
    l5_canonical: str = ""
    l5_canonical_role: str = ""
    l5_wrappers: list[str] = field(default_factory=list)
    l5_decisions: list[str] = field(default_factory=list)
    l6_persistence: list[str] = field(default_factory=list)
    l7_models: list[str] = field(default_factory=list)
    wiring_status: str = ""  # COMPLETE, GAP
    chain_str: str = ""


@dataclass
class UncalledClassification:
    """Classification for an uncalled function."""
    symbol: str
    file: str
    classification: str  # INTERNAL, PENDING, DEAD_CODE, MISSING_WIRING, TEST_ONLY
    reason: str = ""
    pin_ref: str = ""  # e.g. PIN-195 for design-ahead


@dataclass
class ScriptProfile:
    """Uniqueness profile for a single script (file)."""
    domain: str
    file: str
    layer: str
    purpose: str  # derived from canonical function name
    canonical_fn: str  # the function that defines this script's unique contribution
    canonical_role: str
    script_role: str = ""  # FACADE, DECISION_ENGINE, PERSISTENCE, POLICY, RECOVERY, ORCHESTRATION, LEAF
    fn_count: int = 0
    canonical_decisions: int = 0
    canonical_stmts: int = 0
    callers: list[str] = field(default_factory=list)  # who calls into this script (L2/L4/L5)
    uncalled_fns: list[str] = field(default_factory=list)  # functions with zero callers
    uncalled_classified: list[UncalledClassification] = field(default_factory=list)
    delegates_to: list[str] = field(default_factory=list)  # scripts this delegates to
    is_interface: bool = False  # wrapper-only script serving as interface layer
    unique: bool = True  # no other script in domain serves same purpose
    overlap_verdict: str = ""  # FACADE_PATTERN, TRUE_DUPLICATE, FALSE_POSITIVE, or empty
    purpose_statement: str = ""  # 1-line human-readable purpose


def classify_script_role(file_stem: str, layer: str, delegates_to: list[str], is_interface: bool) -> str:
    """Classify a script's architectural role from its name and layer.

    Returns: FACADE, DECISION_ENGINE, PERSISTENCE, POLICY, RECOVERY,
             ORCHESTRATION, PATTERN_ANALYSIS, LEAF, or INTERFACE.
    """
    name = file_stem.lower()

    # Name-based classification
    if "facade" in name:
        return "FACADE"
    if "driver" in name and layer == "L5":
        # L5 drivers that delegate to L5 engines are ORCHESTRATION facades
        return "ORCHESTRATION"
    if "driver" in name and layer == "L6":
        return "PERSISTENCE"
    if "adapter" in name:
        return "ADAPTER"
    if "recovery" in name or "rule_engine" in name:
        return "RECOVERY"
    if "prevention" in name:
        return "POLICY"
    if "policy" in name or "violation" in name:
        return "POLICY"
    if "pattern" in name or "recurrence" in name or "anomaly" in name:
        return "PATTERN_ANALYSIS"
    if "severity" in name:
        return "DECISION_ENGINE"
    if "hallucination" in name or "semantic" in name or "llm_failure" in name:
        return "DETECTION"
    if "postmortem" in name or "lessons" in name:
        return "ANALYSIS"
    if "export" in name or "bundle" in name:
        return "EXPORT"
    if "aggregator" in name:
        return "AGGREGATION"
    if "read" in name:
        return "READ_SERVICE"
    if "write" in name:
        return "WRITE_SERVICE"

    # Layer fallback
    if layer == "L6":
        return "PERSISTENCE"
    if layer == "L5" and is_interface:
        return "INTERFACE"
    if layer == "L5":
        return "DECISION_ENGINE"
    return "UNKNOWN"


def generate_purpose_statement(file_stem: str, script_role: str, canonical_fn: str, layer: str) -> str:
    """Generate a human-readable purpose statement for a script."""
    name_parts = file_stem.replace("_", " ")

    role_descriptions = {
        "FACADE": f"Customer-facing API projection for {name_parts}",
        "ORCHESTRATION": f"Internal orchestration facade delegating to domain engines for {name_parts}",
        "PERSISTENCE": f"Database operations (L6 driver) for {name_parts}",
        "DECISION_ENGINE": f"Business decision logic for {name_parts}",
        "POLICY": f"Policy validation and enforcement for {name_parts}",
        "RECOVERY": f"Failure recovery rule evaluation for {name_parts}",
        "PATTERN_ANALYSIS": f"Pattern detection and analysis for {name_parts}",
        "DETECTION": f"Detection and classification for {name_parts}",
        "ANALYSIS": f"Post-incident analysis for {name_parts}",
        "EXPORT": f"Evidence export and bundle generation for {name_parts}",
        "AGGREGATION": f"Incident aggregation and lifecycle management for {name_parts}",
        "READ_SERVICE": f"Read-only query interface for {name_parts}",
        "WRITE_SERVICE": f"Write operations interface for {name_parts}",
        "ADAPTER": f"Audience-specific adapter for {name_parts}",
        "INTERFACE": f"Thin interface layer delegating to drivers for {name_parts}",
    }
    return role_descriptions.get(script_role, f"{script_role} for {name_parts}")


def classify_uncalled_functions(
    uncalled_fns: list[str],
    file_stem: str,
    domain_source_root: Path,
) -> list[UncalledClassification]:
    """Classify uncalled functions as INTERNAL, PENDING, DEAD_CODE, etc.

    Checks:
    1. If a function is a method called via self.method() by another method in same class → INTERNAL
    2. If referenced in test files → TEST_ONLY
    3. If the file has a PIN reference for design-ahead → PENDING-{PIN}
    4. Otherwise → DEAD_CODE
    """
    classifications: list[UncalledClassification] = []

    # Check source file for self.method() calls to detect internal helpers
    internal_calls: set[str] = set()
    source_file = None
    for layer_dir in ["L5_engines", "L6_drivers", "L5_schemas", "L5_support", "adapters"]:
        candidate = domain_source_root / layer_dir / f"{file_stem}.py"
        if candidate.exists():
            source_file = candidate
            break

    if source_file and source_file.exists():
        try:
            source = source_file.read_text(encoding="utf-8", errors="replace")
            # Find all self.method_name() calls
            for m in re.finditer(r'self\.(\w+)\s*\(', source):
                internal_calls.add(m.group(1))
            # Check for PIN references (design-ahead)
            pin_refs = re.findall(r'PIN-(\d+)', source)
        except Exception:
            pin_refs = []
    else:
        pin_refs = []

    for fn_sym in uncalled_fns:
        # Extract bare method name
        bare = fn_sym.split(".")[-1] if "." in fn_sym else fn_sym

        # Check 1: is it called via self.method() internally?
        if bare in internal_calls:
            classifications.append(UncalledClassification(
                symbol=fn_sym, file=file_stem,
                classification="INTERNAL",
                reason=f"Called via self.{bare}() within same class",
            ))
            continue

        # Check 2: design-ahead with PIN reference
        # Functions like check_policy_enabled, verify_violation_truth in policy_violation_engine
        # are commonly design-ahead for specific PINs
        if pin_refs:
            classifications.append(UncalledClassification(
                symbol=fn_sym, file=file_stem,
                classification="PENDING",
                reason=f"Design-ahead infrastructure",
                pin_ref=f"PIN-{pin_refs[0]}",
            ))
            continue

        # Default: DEAD_CODE
        classifications.append(UncalledClassification(
            symbol=fn_sym, file=file_stem,
            classification="DEAD_CODE",
            reason="No internal or external callers detected",
        ))

    return classifications


def build_feature_chains(
    domain: str,
    endpoints: list[L2Endpoint],
    l4_handlers: list[L4Handler],
    inventory: list[dict[str, str]],
    call_chains: list[dict[str, str]],
) -> list[FeatureChain]:
    """Assemble end-to-end feature chains for a domain.

    Only traces features that have an L2 entry point. Not every function needs
    an L2 — internal engines, drivers, and helpers are analyzed separately
    via script profiles.
    """

    # Index call chains by domain+symbol
    chain_by_symbol: dict[str, dict[str, str]] = {}
    for row in call_chains:
        if row.get("domain") == domain:
            chain_by_symbol[row.get("symbol", "")] = row

    # Index inventory by domain+symbol
    inv_by_symbol: dict[str, dict[str, str]] = {}
    for row in inventory:
        if row.get("domain") == domain:
            inv_by_symbol[row.get("symbol", "")] = row

    # Find L4 handlers for this domain
    domain_handlers = [h for h in l4_handlers if domain in h.serves_domains]

    # Build chains from L2 endpoints
    chains: list[FeatureChain] = []

    for ep in endpoints:
        feature = FeatureChain(
            name=f"{ep.method} {ep.path}" if ep.path else ep.function_name,
            domain=domain,
            l2_endpoint=ep,
        )

        # L4 wiring
        if ep.calls_l4:
            feature.l4_handler = " | ".join(ep.calls_l4[:3])
            feature.wiring_status = "COMPLETE"
        elif domain_handlers:
            feature.l4_handler = domain_handlers[0].handler_name
            feature.wiring_status = "COMPLETE"
        else:
            feature.wiring_status = "GAP"

        # L5 functions used
        for l5_name in ep.calls_l5:
            chain_row = chain_by_symbol.get(l5_name, {})
            inv_row = inv_by_symbol.get(l5_name, {})
            role = chain_row.get("role", "")

            if role in ("CANONICAL", "SUPERSET"):
                feature.l5_canonical = f"{chain_row.get('file', '')}.{l5_name}"
                feature.l5_canonical_role = role
            elif role == "WRAPPER":
                feature.l5_wrappers.append(f"{chain_row.get('file', '')}.{l5_name}")

            intent = inv_row.get("intent", "")
            if intent == "Policy/Decision":
                feature.l5_decisions.append(l5_name)

        # L6 persistence (from inventory side_effects)
        for sym, inv_row in inv_by_symbol.items():
            if inv_row.get("layer") == "L6" and inv_row.get("side_effects", "") != "pure":
                feature.l6_persistence.append(f"{inv_row.get('file', '')}.{sym}")

        # Build chain string
        parts = [f"L2:{ep.file}.{ep.function_name}"]
        if feature.l4_handler:
            parts.append(f"L4:{feature.l4_handler}")
        if feature.l5_canonical:
            parts.append(f"L5:{feature.l5_canonical} [{feature.l5_canonical_role}]")
        for w in feature.l5_wrappers[:2]:
            parts.append(f"L5:{w} [WRAPPER]")
        if feature.l6_persistence:
            parts.append(f"L6:{feature.l6_persistence[0]}")
        feature.chain_str = " → ".join(parts)

        chains.append(feature)

    return chains


def build_script_profiles(
    domain: str,
    call_chains: list[dict[str, str]],
    inventory: list[dict[str, str]],
) -> list[ScriptProfile]:
    """Build uniqueness profile for each script in the domain.

    Answers: what unique function does each script serve? Are there scripts
    with overlapping purposes? Are there functions nobody calls?
    """
    # Index by domain
    domain_chains = [r for r in call_chains if r.get("domain") == domain]
    domain_inv = [r for r in inventory if r.get("domain") == domain]

    # Group by file
    by_file: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in domain_chains:
        by_file[r.get("file", "")].append(r)

    inv_by_file: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in domain_inv:
        inv_by_file[r.get("file", "")].append(r)

    profiles: list[ScriptProfile] = []

    for file_stem, funcs in sorted(by_file.items()):
        # Find canonical function (defines the script's purpose)
        best = None
        for f in funcs:
            if f.get("role") == "CANONICAL":
                best = f
                break
        if not best:
            for f in funcs:
                if f.get("role") == "SUPERSET":
                    best = f
                    break
        if not best:
            for f in funcs:
                if f.get("role") not in ("WRAPPER",):
                    best = f
                    break
        if not best and funcs:
            best = funcs[0]

        if not best:
            continue

        # Determine layer from inventory
        inv_rows = inv_by_file.get(file_stem, [])
        layer = inv_rows[0].get("layer", "") if inv_rows else best.get("layer", "")

        # Derive purpose from canonical function name
        fn_name = best.get("symbol", "").split(".")[-1]
        purpose = fn_name  # raw — grouping happens later

        # Find callers: both internal (from call graph) and external (from inventory)
        callers: set[str] = set()
        uncalled: list[str] = []
        for f in funcs:
            internal_callers = f.get("called_by_internal", "")
            if internal_callers:
                for c in internal_callers.split(" | "):
                    caller_file = c.split(":")[0] if ":" in c else ""
                    if caller_file and caller_file != file_stem:
                        callers.add(caller_file)

        # Check external callers from inventory
        for inv_row in inv_rows:
            ext = inv_row.get("called_by", "")
            if ext:
                callers.add(ext)

        # Uncalled functions: no internal callers AND no external callers
        for f in funcs:
            sym = f.get("symbol", "")
            has_internal = bool(f.get("called_by_internal", ""))
            # Check inventory for external callers
            inv_match = next(
                (r for r in inv_rows if r.get("symbol") == sym), {}
            )
            has_external = bool(inv_match.get("called_by", ""))
            if not has_internal and not has_external:
                # Skip private/dunder methods
                bare = sym.split(".")[-1] if "." in sym else sym
                if not bare.startswith("_"):
                    uncalled.append(sym)

        # Delegates to: other files this script calls
        delegates: set[str] = set()
        for f in funcs:
            calls = f.get("calls_internal", "")
            if calls:
                for t in calls.split(" | "):
                    target_file = t.split(":")[0] if ":" in t else ""
                    if target_file and target_file != file_stem:
                        delegates.add(target_file)

        # Is this a wrapper-only interface script?
        all_wrapper = all(
            f.get("role") in ("WRAPPER", "LEAF") for f in funcs
        )
        is_iface = all_wrapper and bool(delegates)

        # Classify script role
        script_role = classify_script_role(file_stem, layer, sorted(delegates), is_iface)

        # Generate purpose statement
        purpose_stmt = generate_purpose_statement(
            file_stem, script_role, best.get("symbol", ""), layer
        )

        # Classify uncalled functions
        domain_source = CUS_ROOT / domain
        uncalled_classified = classify_uncalled_functions(
            uncalled, file_stem, domain_source
        )

        profiles.append(ScriptProfile(
            domain=domain,
            file=file_stem,
            layer=layer,
            purpose=purpose,
            canonical_fn=best.get("symbol", ""),
            canonical_role=best.get("role", ""),
            script_role=script_role,
            fn_count=len(funcs),
            canonical_decisions=int(best.get("decision_count", 0)),
            canonical_stmts=int(best.get("statement_count", 0)),
            callers=sorted(callers),
            uncalled_fns=uncalled,
            uncalled_classified=uncalled_classified,
            delegates_to=sorted(delegates),
            is_interface=is_iface,
            purpose_statement=purpose_stmt,
        ))

    # Uniqueness check: group by purpose noun, flag overlaps within domain
    _check_uniqueness(profiles)

    return profiles


def _check_uniqueness(profiles: list[ScriptProfile]) -> None:
    """Flag scripts that overlap in purpose within the same domain."""
    verbs = {
        "get", "list", "create", "update", "delete", "remove", "add",
        "fetch", "store", "save", "load", "find", "search", "query",
        "count", "aggregate", "compute", "calculate", "validate",
        "check", "verify", "evaluate", "process", "handle", "detect",
        "analyze", "export", "generate", "resolve", "recover", "prevent",
    }

    def extract_noun(fn_name: str) -> str:
        parts = fn_name.split("_")
        if not parts:
            return fn_name
        if parts[0] in verbs and len(parts) > 1:
            return "_".join(parts[1:])
        return "_".join(parts[:2]) if len(parts) >= 2 else fn_name

    by_noun: dict[str, list[ScriptProfile]] = defaultdict(list)
    for p in profiles:
        bare = p.canonical_fn.split(".")[-1] if "." in p.canonical_fn else p.canonical_fn
        noun = extract_noun(bare)
        by_noun[noun].append(p)

    # Roles that are structurally distinct even when sharing a noun
    FACADE_ROLES = {"FACADE", "ORCHESTRATION", "INTERFACE", "ADAPTER", "READ_SERVICE", "WRITE_SERVICE"}
    ALGORITHM_ROLES = {"DECISION_ENGINE", "POLICY", "RECOVERY", "DETECTION", "PATTERN_ANALYSIS", "ANALYSIS"}
    PERSISTENCE_ROLES = {"PERSISTENCE", "AGGREGATION", "EXPORT"}

    def role_category(role: str) -> str:
        if role in FACADE_ROLES:
            return "FACADE"
        if role in ALGORITHM_ROLES:
            return "ALGORITHM"
        if role in PERSISTENCE_ROLES:
            return "PERSISTENCE"
        return role

    for noun, group in by_noun.items():
        if len(group) > 1:
            # Multiple scripts with same noun — check if they're different layers
            layers = {p.layer for p in group}
            if len(layers) == len(group):
                continue  # Different layers (e.g., L5 engine + L6 driver) = fine

            # Check if they have different role categories (FACADE vs ALGORITHM vs PERSISTENCE)
            role_cats = {role_category(p.script_role) for p in group}
            if len(role_cats) == len(group):
                # Different role categories = FACADE_PATTERN, not duplicate
                for p in group:
                    p.overlap_verdict = "FACADE_PATTERN"
                continue

            # Check if one delegates to the other (facade pattern)
            file_set = {p.file for p in group}
            is_delegation = False
            for p in group:
                if any(d in file_set for d in p.delegates_to):
                    is_delegation = True
                    break
            if is_delegation:
                for p in group:
                    p.overlap_verdict = "FACADE_PATTERN"
                continue

            # True overlap — same layer, same role category, no delegation
            for p in group:
                p.unique = False
                p.overlap_verdict = "TRUE_DUPLICATE"


# ---------------------------------------------------------------------------
# Authority Map
# ---------------------------------------------------------------------------


def build_authority_map(
    all_chains: dict[str, list[FeatureChain]],
    call_chains: list[dict[str, str]],
) -> dict[str, dict]:
    """Build authority map: which domain owns which concept/noun.

    Extracts nouns from canonical function names and maps to owning domain.
    """
    authority: dict[str, dict] = {}  # noun → {domain, canonical, evidence}

    for row in call_chains:
        if row.get("role") not in ("CANONICAL", "SUPERSET"):
            continue

        domain = row.get("domain", "")
        symbol = row.get("symbol", "")
        fn_name = symbol.split(".")[-1] if "." in symbol else symbol

        # Extract noun from function name
        parts = fn_name.split("_")
        if len(parts) < 2:
            continue

        verbs = {
            "get", "list", "create", "update", "delete", "remove", "add",
            "fetch", "store", "save", "load", "find", "search", "query",
            "count", "aggregate", "compute", "calculate", "validate",
            "check", "verify", "evaluate", "process", "handle", "detect",
            "analyze", "export", "generate", "resolve", "recover", "prevent",
        }

        if parts[0] in verbs:
            noun = "_".join(parts[1:])
        else:
            noun = "_".join(parts[:2])

        # Normalize
        if noun.endswith("ies"):
            noun = noun[:-3] + "y"
        elif noun.endswith("s") and not noun.endswith("ss"):
            noun = noun[:-1]

        if noun not in authority:
            authority[noun] = {
                "domain": domain,
                "canonical_fn": f"{row.get('file', '')}.{symbol}",
                "role": row.get("role", ""),
                "decisions": int(row.get("decision_count", 0)),
            }
        else:
            # If multiple domains claim the same noun, pick highest decision count
            existing = authority[noun]
            new_decisions = int(row.get("decision_count", 0))
            if new_decisions > existing["decisions"]:
                authority[noun] = {
                    "domain": domain,
                    "canonical_fn": f"{row.get('file', '')}.{symbol}",
                    "role": row.get("role", ""),
                    "decisions": new_decisions,
                    "contested_by": existing["domain"],
                }

    return authority


# ---------------------------------------------------------------------------
# Markdown Generation
# ---------------------------------------------------------------------------


def generate_bible_markdown(
    domain: str,
    chains: list[FeatureChain],
    call_chains: list[dict[str, str]],
    inventory: list[dict[str, str]],
    profiles: list[ScriptProfile],
) -> str:
    """Generate SOFTWARE_BIBLE.md for a single domain."""
    lines = [
        f"# {domain.title()} — Software Bible",
        "",
        f"**Domain:** {domain}  ",
        f"**L2 Features:** {len(chains)}  ",
        f"**Scripts:** {len(profiles)}  ",
        f"**Generator:** `scripts/ops/hoc_software_bible_generator.py`",
        "",
        "---",
        "",
    ]

    # ── Script Uniqueness Registry ──
    lines.append("## Script Registry")
    lines.append("")
    lines.append("Each script's unique contribution and canonical function.")
    lines.append("")
    lines.append("| Script | Layer | Script Role | Canonical Function | Role | Decisions | Callers | Status |")
    lines.append("|--------|-------|-------------|--------------------|----- |-----------|---------|--------|")
    for p in sorted(profiles, key=lambda x: (x.layer, x.file)):
        callers_str = ", ".join(p.callers[:3]) if p.callers else "—"
        if len(p.callers) > 3:
            callers_str += f" +{len(p.callers) - 3}"
        if p.overlap_verdict == "FACADE_PATTERN":
            status_str = "FACADE_PATTERN"
        elif not p.unique:
            status_str = "**OVERLAP**"
        elif p.is_interface:
            status_str = "INTERFACE"
        else:
            status_str = "YES"
        lines.append(
            f"| {p.file} | {p.layer} | {p.script_role} | `{p.canonical_fn}` | {p.canonical_role} "
            f"| {p.canonical_decisions} | {callers_str} | {status_str} |"
        )
    lines.append("")

    # ── Uncalled Functions (Classified) ──
    all_classified: list[UncalledClassification] = []
    for p in profiles:
        all_classified.extend(p.uncalled_classified)

    if all_classified:
        lines.append("## Uncalled Functions")
        lines.append("")
        lines.append("Functions with no internal or external callers detected, classified by analysis.")
        lines.append("")
        lines.append("| Function | Classification | Reason |")
        lines.append("|----------|----------------|--------|")
        for c in sorted(all_classified, key=lambda x: (x.classification, x.symbol)):
            pin = f" ({c.pin_ref})" if c.pin_ref else ""
            lines.append(f"| `{c.file}.{c.symbol}` | **{c.classification}**{pin} | {c.reason} |")
        lines.append("")

    # ── Overlapping Scripts ──
    overlaps = [p for p in profiles if not p.unique]
    facade_patterns = [p for p in profiles if p.overlap_verdict == "FACADE_PATTERN"]

    if facade_patterns:
        lines.append("## Facade Patterns (same noun, different roles — NOT duplicates)")
        lines.append("")
        lines.append("These scripts share a noun but serve structurally distinct roles.")
        lines.append("")
        for p in facade_patterns:
            lines.append(
                f"- `{p.file}` ({p.script_role}) — canonical: `{p.canonical_fn}` ({p.canonical_role})"
            )
        lines.append("")

    if overlaps:
        lines.append("## Overlapping Scripts (same purpose, same layer)")
        lines.append("")
        lines.append("These scripts may serve duplicate purposes within the domain.")
        lines.append("")
        for p in overlaps:
            lines.append(
                f"- `{p.file}` ({p.script_role}) — canonical: `{p.canonical_fn}` "
                f"({p.canonical_role}) — verdict: {p.overlap_verdict}"
            )
        lines.append("")

    # ── L2 Feature Chains ──
    complete = sum(1 for c in chains if c.wiring_status == "COMPLETE")
    gaps = sum(1 for c in chains if c.wiring_status == "GAP")

    lines.append("## L2 Feature Chains")
    lines.append("")
    lines.append(f"| Status | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| COMPLETE (L2→L4→L5→L6) | {complete} |")
    lines.append(f"| GAP (L2→L5 direct) | {gaps} |")
    lines.append("")

    wired_chains = [c for c in chains if c.wiring_status == "COMPLETE"]
    gap_chains = [c for c in chains if c.wiring_status == "GAP"]

    if wired_chains:
        lines.append("### Wired Features (L2→L4→L5→L6)")
        lines.append("")
        for chain in sorted(wired_chains, key=lambda c: c.name):
            lines.append(f"#### {chain.name}")
            lines.append(f"```")
            lines.append(chain.chain_str)
            lines.append(f"```")
            if chain.l5_canonical:
                lines.append(f"- **Canonical:** `{chain.l5_canonical}` [{chain.l5_canonical_role}]")
            if chain.l5_wrappers:
                lines.append(f"- **Wrappers:** {', '.join(f'`{w}`' for w in chain.l5_wrappers)}")
            if chain.l5_decisions:
                lines.append(f"- **Decisions:** {', '.join(chain.l5_decisions)}")
            lines.append("")

    if gap_chains:
        lines.append("### Gap Features (L2→L5 direct, missing L4)")
        lines.append("")
        for chain in sorted(gap_chains, key=lambda c: c.name):
            lines.append(f"#### {chain.name}")
            lines.append(f"```")
            lines.append(chain.chain_str)
            lines.append(f"```")
            lines.append("")

    # ── Canonical Algorithm Inventory ──
    domain_chains = [r for r in call_chains if r.get("domain") == domain]
    canonicals = [r for r in domain_chains if r.get("role") == "CANONICAL"]
    supersets = [r for r in domain_chains if r.get("role") == "SUPERSET"]

    if canonicals or supersets:
        lines.append("## Canonical Algorithm Inventory")
        lines.append("")
        lines.append("| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |")
        lines.append("|----------|------|------|-----------|-------|-------------|--------------|")
        for r in sorted(canonicals + supersets, key=lambda x: x.get("symbol", "")):
            lines.append(
                f"| `{r.get('symbol', '')}` | {r.get('file', '')} | {r.get('role', '')} "
                f"| {r.get('decision_count', '')} | {r.get('statement_count', '')} "
                f"| {r.get('has_persistence', '')} | {r.get('calls_internal', '')[:60]} |"
            )
        lines.append("")

    # ── Wrapper Inventory ──
    wrappers = [r for r in domain_chains if r.get("role") == "WRAPPER"]
    if wrappers:
        lines.append("## Wrapper Inventory")
        lines.append("")
        lines.append(f"_{len(wrappers)} thin delegation functions._")
        lines.append("")
        for r in sorted(wrappers, key=lambda x: x.get("symbol", ""))[:30]:
            target = r.get("calls_internal", "").split(" | ")[0] if r.get("calls_internal") else "?"
            lines.append(f"- `{r.get('file', '')}.{r.get('symbol', '')}` → {target}")
        if len(wrappers) > 30:
            lines.append(f"- _...and {len(wrappers) - 30} more_")
        lines.append("")

    return "\n".join(lines)


def generate_canonical_registry_markdown(
    domain: str,
    profiles: list[ScriptProfile],
) -> str:
    """Generate CANONICAL_REGISTRY.md — auditable per-script registration."""
    lines = [
        f"# {domain.title()} — Canonical Registry",
        "",
        f"**Domain:** {domain}  ",
        f"**Scripts:** {len(profiles)}  ",
        f"**Generator:** `scripts/ops/hoc_software_bible_generator.py`",
        "",
        "Each script's purpose, canonical function, role, callers, and delegates.",
        "This is the auditable artifact for domain consolidation.",
        "",
        "---",
        "",
    ]

    for p in sorted(profiles, key=lambda x: (x.layer, x.file)):
        lines.append(f"## {p.file}")
        lines.append("")
        lines.append(f"- **Layer:** {p.layer}")
        lines.append(f"- **Script Role:** {p.script_role}")
        lines.append(f"- **Purpose:** {p.purpose_statement}")
        lines.append(f"- **Canonical Function:** `{p.canonical_fn}`")
        lines.append(f"- **Canonical Role:** {p.canonical_role}")
        lines.append(f"- **Decisions:** {p.canonical_decisions}")
        lines.append(f"- **Functions:** {p.fn_count}")

        if p.callers:
            lines.append(f"- **Callers:** {', '.join(p.callers)}")
        else:
            lines.append("- **Callers:** none detected")

        if p.delegates_to:
            lines.append(f"- **Delegates To:** {', '.join(p.delegates_to)}")

        if p.overlap_verdict:
            lines.append(f"- **Overlap Verdict:** {p.overlap_verdict}")

        # Uncalled functions for this script
        script_uncalled = [c for c in p.uncalled_classified]
        if script_uncalled:
            lines.append(f"- **Uncalled Functions:**")
            for c in script_uncalled:
                pin = f" ({c.pin_ref})" if c.pin_ref else ""
                lines.append(f"  - `{c.symbol}` → {c.classification}{pin}: {c.reason}")

        status = "ACTIVE"
        if p.overlap_verdict == "TRUE_DUPLICATE":
            status = "REVIEW_NEEDED"
        elif not p.callers and p.layer == "L5":
            status = "CHECK_WIRING"
        lines.append(f"- **Status:** {status}")
        lines.append("")

    return "\n".join(lines)


def generate_authority_map_markdown(authority: dict[str, dict]) -> str:
    """Generate AUTHORITY_MAP.md."""
    lines = [
        "# Domain Authority Map",
        "",
        "**Generator:** `scripts/ops/hoc_software_bible_generator.py`",
        "",
        "Which domain owns which concept. Derived from canonical function",
        "analysis — the domain with the highest-decision canonical function",
        "for a given noun is the authority.",
        "",
        "---",
        "",
        "## Authority Table",
        "",
        "| Concept | Authority Domain | Canonical Function | Decisions | Contested? |",
        "|---------|------------------|--------------------|-----------|------------|",
    ]

    for noun in sorted(authority.keys()):
        entry = authority[noun]
        contested = entry.get("contested_by", "")
        contested_str = f"Yes ({contested})" if contested else "No"
        lines.append(
            f"| {noun} | **{entry['domain']}** | `{entry['canonical_fn']}` "
            f"| {entry['decisions']} | {contested_str} |"
        )

    lines.append("")

    # Contested concepts
    contested = {n: e for n, e in authority.items() if e.get("contested_by")}
    if contested:
        lines.append("## Contested Concepts")
        lines.append("")
        lines.append("These nouns have canonical functions in multiple domains.")
        lines.append("The domain with the most decision logic is listed as authority.")
        lines.append("")
        for noun, entry in sorted(contested.items()):
            lines.append(
                f"- **{noun}**: {entry['domain']} (canonical) vs {entry['contested_by']} "
                f"— winner has {entry['decisions']} decisions"
            )
        lines.append("")

    # By domain summary
    by_domain: dict[str, list[str]] = defaultdict(list)
    for noun, entry in authority.items():
        by_domain[entry["domain"]].append(noun)

    lines.append("## By Domain")
    lines.append("")
    for domain in sorted(by_domain):
        nouns = sorted(by_domain[domain])
        lines.append(f"### {domain.title()}")
        lines.append(f"Owns {len(nouns)} concepts: {', '.join(nouns[:20])}")
        if len(nouns) > 20:
            lines.append(f"  ...and {len(nouns) - 20} more")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_generation(
    output_dir: Path,
    domain_filter: str | None = None,
    as_json: bool = False,
) -> dict:
    """Generate software bibles and authority map."""

    # Load inventory
    inventory: list[dict[str, str]] = []
    if INVENTORY_PATH.exists():
        with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
            inventory = list(csv.DictReader(f))
        print(f"Loaded {len(inventory)} inventory records")
    else:
        print(f"WARNING: {INVENTORY_PATH} not found, some features limited")

    # Load call chains
    call_chains: list[dict[str, str]] = []
    if CALL_CHAINS_PATH.exists():
        with open(CALL_CHAINS_PATH, "r", encoding="utf-8") as f:
            call_chains = list(csv.DictReader(f))
        print(f"Loaded {len(call_chains)} call chain records")
    else:
        print(f"WARNING: {CALL_CHAINS_PATH} not found, run hoc_call_chain_tracer.py first")

    # Scan L4 handlers
    print("Scanning L4 handlers...")
    l4_handlers = scan_l4_handlers()
    print(f"  Found {len(l4_handlers)} L4 handlers")

    domains = [domain_filter] if domain_filter else ALL_DOMAINS
    all_chains: dict[str, list[FeatureChain]] = {}
    results: dict[str, dict] = {}

    for domain in domains:
        if not (CUS_ROOT / domain).is_dir():
            continue

        print(f"\nProcessing {domain}...")

        # Scan L2 endpoints
        endpoints = scan_l2_endpoints(domain)
        print(f"  L2 endpoints: {len(endpoints)}")

        # Build feature chains (L2-rooted only)
        chains = build_feature_chains(
            domain, endpoints, l4_handlers, inventory, call_chains
        )
        all_chains[domain] = chains

        # Build script profiles (uniqueness + uncalled detection)
        profiles = build_script_profiles(domain, call_chains, inventory)
        total_uncalled = sum(len(p.uncalled_fns) for p in profiles)
        overlaps = sum(1 for p in profiles if not p.unique)

        # Generate bible
        md_content = generate_bible_markdown(
            domain, chains, call_chains, inventory, profiles
        )
        domain_dir = output_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        bible_path = domain_dir / "SOFTWARE_BIBLE.md"
        bible_path.write_text(md_content, encoding="utf-8")

        # Generate canonical registry
        registry_md = generate_canonical_registry_markdown(domain, profiles)
        registry_path = domain_dir / "CANONICAL_REGISTRY.md"
        registry_path.write_text(registry_md, encoding="utf-8")

        complete = sum(1 for c in chains if c.wiring_status == "COMPLETE")
        gaps = sum(1 for c in chains if c.wiring_status == "GAP")

        results[domain] = {
            "features": len(chains),
            "complete": complete,
            "gaps": gaps,
            "scripts": len(profiles),
            "uncalled_fns": total_uncalled,
            "overlapping_scripts": overlaps,
            "l2_endpoints": len(endpoints),
        }
        print(f"  L2 features: {len(chains)} (complete={complete}, gap={gaps})")
        print(f"  Scripts: {len(profiles)}, uncalled fns: {total_uncalled}, overlaps: {overlaps}")
        print(f"  → {bible_path.relative_to(PROJECT_ROOT)}")
        print(f"  → {registry_path.relative_to(PROJECT_ROOT)}")

    # Authority map
    print("\nBuilding authority map...")
    authority = build_authority_map(all_chains, call_chains)
    auth_md = generate_authority_map_markdown(authority)
    auth_path = output_dir / "AUTHORITY_MAP.md"
    auth_path.write_text(auth_md, encoding="utf-8")
    print(f"  {len(authority)} concepts mapped → {auth_path.relative_to(PROJECT_ROOT)}")

    if as_json:
        result = {
            "domains": results,
            "authority_map": {
                noun: {"domain": entry["domain"], "canonical": entry["canonical_fn"]}
                for noun, entry in authority.items()
            },
        }
        json.dump(result, sys.stdout, indent=2)
        print()

    # Summary
    total_features = sum(r["features"] for r in results.values())
    total_complete = sum(r["complete"] for r in results.values())
    total_gaps = sum(r["gaps"] for r in results.values())
    total_scripts = sum(r["scripts"] for r in results.values())
    total_uncalled = sum(r["uncalled_fns"] for r in results.values())
    total_overlaps = sum(r["overlapping_scripts"] for r in results.values())

    print(f"\n{'=' * 60}")
    print(f"L2 features: {total_features} (complete={total_complete}, gap={total_gaps})")
    print(f"Scripts: {total_scripts}")
    print(f"  Uncalled functions: {total_uncalled}")
    print(f"  Overlapping scripts: {total_overlaps}")
    print(f"Authority concepts: {len(authority)}")
    contested = sum(1 for e in authority.values() if e.get("contested_by"))
    print(f"  Contested: {contested}")

    return {"total_features": total_features, "domains": results}


def main():
    parser = argparse.ArgumentParser(
        description="HOC Software Bible Generator — end-to-end feature traces + authority map"
    )
    parser.add_argument("--output-dir", type=str,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--domain", type=str, help="Process only this domain")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR

    print("=" * 60)
    print("HOC Software Bible Generator")
    print("=" * 60)
    print()

    run_generation(output_dir, domain_filter=args.domain, as_json=args.json)

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
