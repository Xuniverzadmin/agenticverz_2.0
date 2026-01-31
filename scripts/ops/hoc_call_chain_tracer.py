#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Trace intra-domain function call chains — identify canonical algorithm owners, wrappers, supersets, and delegation trees
# artifact_class: CODE

"""
HOC Call-Chain Tracer

For each domain, traces function→function calls within L5/L6 files using AST.
Builds a directed call graph, then identifies:
  - CANONICAL: function that owns the algorithm (most decisions, deepest logic)
  - WRAPPER: thin delegation (≤3 stmts, single call, no branching)
  - SUPERSET: function that subsumes other functions (calls them + adds logic)
  - LEAF: terminal function (calls no other domain functions)

Outputs CALL_CHAINS.csv + per-domain CALL_GRAPH.md

Usage:
    python3 scripts/ops/hoc_call_chain_tracer.py
    python3 scripts/ops/hoc_call_chain_tracer.py --domain incidents
    python3 scripts/ops/hoc_call_chain_tracer.py --json
"""

import argparse
import ast
import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUS_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc" / "cus"
MODELS_ROOT = PROJECT_ROOT / "backend" / "app" / "models"
HOC_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "literature" / "hoc_domain"

ALL_DOMAINS = [
    "account", "activity", "analytics", "api_keys", "apis",
    "controls", "docs", "incidents", "integrations", "logs",
    "overview", "policies",
]

CSV_COLUMNS = [
    "domain",
    "file",
    "symbol",
    "layer",
    "role",
    "calls_internal",
    "called_by_internal",
    "delegation_depth",
    "decision_count",
    "statement_count",
    "has_branching",
    "has_persistence",
    "has_error_handling",
    "superset_of",
    "chain",
]


# ---------------------------------------------------------------------------
# AST Analysis
# ---------------------------------------------------------------------------


@dataclass
class FunctionMeta:
    """Metadata extracted from a single function definition."""
    domain: str
    file_stem: str
    symbol: str  # ClassName.method or function_name
    layer: str
    is_async: bool = False
    statement_count: int = 0
    decision_count: int = 0  # if/elif/match branches
    has_branching: bool = False
    has_persistence: bool = False  # session.add/commit/execute etc
    has_error_handling: bool = False  # try/except with logic
    is_wrapper: bool = False
    outbound_calls: list[str] = field(default_factory=list)  # raw call names
    line_start: int = 0
    line_end: int = 0


def _count_statements(node: ast.AST) -> int:
    """Count executable statements in a function body (excluding docstring)."""
    count = 0
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant):
            continue  # skip docstring
        if isinstance(child, ast.stmt):
            count += 1
    return count


def _count_decisions(node: ast.AST) -> int:
    """Count decision points (if/elif/match)."""
    count = 0
    for child in ast.walk(node):
        if isinstance(child, ast.If):
            count += 1
        elif isinstance(child, ast.Match):
            count += len(child.cases)
    return count


def _has_persistence(source_lines: list[str]) -> bool:
    """Check if function body has DB write patterns."""
    body = "\n".join(source_lines)
    patterns = [
        "session.add", "session.commit", "session.flush", "session.delete",
        "session.execute", "session.merge", ".add(", ".commit(", ".flush(",
        "INSERT", "UPDATE", "DELETE",
    ]
    for p in patterns:
        if p in body:
            return True
    return False


def _has_error_handling(node: ast.AST) -> bool:
    """Check if function has non-trivial try/except."""
    for child in ast.walk(node):
        if isinstance(child, ast.Try):
            # Non-trivial = has except handlers with actual logic (not just re-raise)
            for handler in child.handlers:
                body = [s for s in handler.body if not isinstance(s, ast.Raise)]
                if body:
                    return True
    return False


def _extract_calls(node: ast.AST) -> list[str]:
    """Extract all function/method call names from a function body."""
    calls = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                # self.method() → method
                # obj.method() → method
                if isinstance(child.func.value, ast.Name):
                    if child.func.value.id == "self":
                        calls.append(child.func.attr)
                    else:
                        calls.append(f"{child.func.value.id}.{child.func.attr}")
                else:
                    calls.append(child.func.attr)
    return calls


def _is_wrapper(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Detect thin wrapper: ≤3 stmts, no branching, 1-2 calls."""
    body = [
        s for s in node.body
        if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)
                and isinstance(s.value.value, str))
    ]
    if len(body) > 3:
        return False
    for s in body:
        if isinstance(s, (ast.If, ast.For, ast.While)):
            return False
    calls = 0
    for s in body:
        for child in ast.walk(s):
            if isinstance(child, ast.Call):
                calls += 1
    return calls <= 2


def extract_functions_from_file(
    filepath: Path, domain: str, layer: str,
) -> list[FunctionMeta]:
    """Extract all function metadata from a single file."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return []

    source_lines = source.splitlines()
    results: list[FunctionMeta] = []

    def process(node: ast.FunctionDef | ast.AsyncFunctionDef, class_name: str = ""):
        symbol = f"{class_name}.{node.name}" if class_name else node.name
        start = node.lineno - 1
        end = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start + 1
        body_lines = source_lines[start:end]

        meta = FunctionMeta(
            domain=domain,
            file_stem=filepath.stem,
            symbol=symbol,
            layer=layer,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            statement_count=_count_statements(node),
            decision_count=_count_decisions(node),
            has_branching=_count_decisions(node) > 0,
            has_persistence=_has_persistence(body_lines),
            has_error_handling=_has_error_handling(node),
            is_wrapper=_is_wrapper(node),
            outbound_calls=_extract_calls(node),
            line_start=node.lineno,
            line_end=end,
        )
        results.append(meta)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            process(node)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    process(item, class_name=node.name)

    return results


# ---------------------------------------------------------------------------
# File Discovery
# ---------------------------------------------------------------------------


def discover_domain_files(domain: str) -> list[tuple[Path, str]]:
    """Find all L5/L6 files for a domain. Returns [(path, layer)]."""
    domain_dir = CUS_ROOT / domain
    if not domain_dir.is_dir():
        return []

    results: list[tuple[Path, str]] = []
    for child in sorted(domain_dir.iterdir()):
        if not child.is_dir():
            continue
        is_l5 = child.name.startswith("L5_")
        is_l6 = child.name == "L6_drivers"
        if not is_l5 and not is_l6:
            continue
        layer = "L5" if is_l5 else "L6"
        for pyfile in sorted(child.rglob("*.py")):
            if pyfile.name == "__init__.py":
                continue
            results.append((pyfile, layer))

    return results


# ---------------------------------------------------------------------------
# Call Graph Construction
# ---------------------------------------------------------------------------


@dataclass
class CallGraph:
    """Directed call graph for a single domain."""
    domain: str
    functions: dict[str, FunctionMeta] = field(default_factory=dict)  # key = file:symbol
    edges: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))  # caller → {callee}
    reverse_edges: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))  # callee → {caller}


def build_call_graph(domain: str) -> CallGraph:
    """Build the intra-domain call graph."""
    graph = CallGraph(domain=domain)
    files = discover_domain_files(domain)

    # Extract all functions
    all_functions: list[FunctionMeta] = []
    for filepath, layer in files:
        funcs = extract_functions_from_file(filepath, domain, layer)
        all_functions.extend(funcs)

    # Index: function_name → list of keys (handles overloads)
    name_to_keys: dict[str, list[str]] = defaultdict(list)
    for fn in all_functions:
        key = f"{fn.file_stem}:{fn.symbol}"
        graph.functions[key] = fn
        # Index by bare function name and by Class.method
        bare = fn.symbol.split(".")[-1] if "." in fn.symbol else fn.symbol
        name_to_keys[bare].append(key)
        name_to_keys[fn.symbol].append(key)

    # Resolve edges: for each function, match outbound calls to known functions
    for fn in all_functions:
        caller_key = f"{fn.file_stem}:{fn.symbol}"
        for call_name in fn.outbound_calls:
            # Try exact match first, then bare name
            targets = name_to_keys.get(call_name, [])
            if not targets:
                bare = call_name.split(".")[-1] if "." in call_name else call_name
                targets = name_to_keys.get(bare, [])

            for target_key in targets:
                if target_key != caller_key:  # no self-loops
                    graph.edges[caller_key].add(target_key)
                    graph.reverse_edges[target_key].add(caller_key)

    return graph


# ---------------------------------------------------------------------------
# Role Classification
# ---------------------------------------------------------------------------


def classify_roles(graph: CallGraph) -> dict[str, str]:
    """Classify each function's role in the call graph.

    CANONICAL: owns the algorithm — most decisions, not a wrapper, has callers
    WRAPPER: thin delegation
    SUPERSET: calls other domain functions + adds its own logic
    LEAF: calls no other domain functions
    ENTRY: called from outside domain (L2/L4 callers), delegates inward
    INTERNAL: called only by other domain functions
    """
    roles: dict[str, str] = {}

    for key, fn in graph.functions.items():
        outgoing = graph.edges.get(key, set())
        incoming = graph.reverse_edges.get(key, set())

        if fn.is_wrapper:
            roles[key] = "WRAPPER"
        elif not outgoing:
            roles[key] = "LEAF"
        elif fn.decision_count >= 2 and outgoing:
            # Has decisions AND calls other functions → SUPERSET candidate
            roles[key] = "SUPERSET"
        elif not incoming:
            roles[key] = "ENTRY"
        else:
            roles[key] = "INTERNAL"

    # Second pass: find CANONICAL (highest decision_count non-wrapper in each file cluster)
    by_file: dict[str, list[str]] = defaultdict(list)
    for key, fn in graph.functions.items():
        by_file[fn.file_stem].append(key)

    for file_stem, keys in by_file.items():
        # Find the function with most decisions that isn't a wrapper
        candidates = [
            (graph.functions[k].decision_count + graph.functions[k].statement_count, k)
            for k in keys
            if not graph.functions[k].is_wrapper
            and not graph.functions[k].symbol.split(".")[-1].startswith("_")
        ]
        if candidates:
            candidates.sort(key=lambda x: -x[0])
            top_key = candidates[0][1]
            if roles.get(top_key) in ("INTERNAL", "SUPERSET", "ENTRY"):
                if graph.functions[top_key].decision_count >= 1:
                    roles[top_key] = "CANONICAL"

    return roles


def compute_delegation_depth(graph: CallGraph, key: str, visited: set[str] | None = None) -> int:
    """Compute max delegation depth from this function."""
    if visited is None:
        visited = set()
    if key in visited:
        return 0
    visited.add(key)

    outgoing = graph.edges.get(key, set())
    if not outgoing:
        return 0

    max_depth = 0
    for target in outgoing:
        depth = compute_delegation_depth(graph, target, visited)
        max_depth = max(max_depth, depth + 1)

    return max_depth


def find_superset_of(graph: CallGraph, key: str) -> list[str]:
    """Find which other domain functions this function subsumes (calls directly)."""
    outgoing = graph.edges.get(key, set())
    fn = graph.functions.get(key)
    if not fn or fn.is_wrapper:
        return []

    # A superset calls other functions AND adds its own logic (decisions)
    if fn.decision_count < 1:
        return []

    return sorted(outgoing)


def trace_chain(graph: CallGraph, key: str, visited: set[str] | None = None) -> str:
    """Build a human-readable chain string: fn → callee1 → callee2."""
    if visited is None:
        visited = set()
    if key in visited:
        return f"{key}(cycle)"
    visited.add(key)

    fn = graph.functions.get(key)
    if not fn:
        return key

    outgoing = sorted(graph.edges.get(key, set()))
    if not outgoing:
        return f"{fn.file_stem}.{fn.symbol}"

    parts = [f"{fn.file_stem}.{fn.symbol}"]
    for target in outgoing[:3]:  # limit to 3 targets for readability
        target_fn = graph.functions.get(target)
        if target_fn:
            parts.append(f"{target_fn.file_stem}.{target_fn.symbol}")
    if len(outgoing) > 3:
        parts.append(f"...+{len(outgoing) - 3}")

    return " → ".join(parts)


# ---------------------------------------------------------------------------
# Output Generation
# ---------------------------------------------------------------------------


def generate_csv_rows(graph: CallGraph, roles: dict[str, str]) -> list[dict[str, str]]:
    """Generate CSV rows from call graph analysis."""
    rows: list[dict[str, str]] = []

    for key, fn in sorted(graph.functions.items()):
        outgoing = sorted(graph.edges.get(key, set()))
        incoming = sorted(graph.reverse_edges.get(key, set()))
        depth = compute_delegation_depth(graph, key)
        superset_of = find_superset_of(graph, key)
        chain = trace_chain(graph, key)

        rows.append({
            "domain": fn.domain,
            "file": fn.file_stem,
            "symbol": fn.symbol,
            "layer": fn.layer,
            "role": roles.get(key, ""),
            "calls_internal": " | ".join(outgoing) if outgoing else "",
            "called_by_internal": " | ".join(incoming) if incoming else "",
            "delegation_depth": str(depth),
            "decision_count": str(fn.decision_count),
            "statement_count": str(fn.statement_count),
            "has_branching": "yes" if fn.has_branching else "no",
            "has_persistence": "yes" if fn.has_persistence else "no",
            "has_error_handling": "yes" if fn.has_error_handling else "no",
            "superset_of": " | ".join(superset_of) if superset_of else "",
            "chain": chain,
        })

    return rows


def generate_call_graph_markdown(graph: CallGraph, roles: dict[str, str]) -> str:
    """Generate CALL_GRAPH.md for a single domain."""
    lines = [
        f"# {graph.domain.title()} — Call Graph",
        "",
        f"**Domain:** {graph.domain}  ",
        f"**Total functions:** {len(graph.functions)}  ",
        f"**Generator:** `scripts/ops/hoc_call_chain_tracer.py`",
        "",
        "---",
        "",
    ]

    # Role summary
    by_role: dict[str, list[str]] = defaultdict(list)
    for key, role in roles.items():
        by_role[role].append(key)

    lines.append("## Role Summary")
    lines.append("")
    lines.append("| Role | Count | Description |")
    lines.append("|------|-------|-------------|")
    role_desc = {
        "CANONICAL": "Owns the algorithm — most decisions, primary logic",
        "SUPERSET": "Calls other functions + adds its own decisions",
        "WRAPPER": "Thin delegation — ≤3 stmts, no branching",
        "LEAF": "Terminal — calls no other domain functions",
        "ENTRY": "Entry point — no domain-internal callers",
        "INTERNAL": "Called only by other domain functions",
    }
    for role in ("CANONICAL", "SUPERSET", "WRAPPER", "LEAF", "ENTRY", "INTERNAL"):
        count = len(by_role.get(role, []))
        desc = role_desc.get(role, "")
        if count:
            lines.append(f"| {role} | {count} | {desc} |")
    lines.append("")

    # Canonical functions (the important ones)
    canonicals = by_role.get("CANONICAL", [])
    supersets = by_role.get("SUPERSET", [])

    if canonicals:
        lines.append("## Canonical Algorithm Owners")
        lines.append("")
        for key in sorted(canonicals):
            fn = graph.functions[key]
            outgoing = sorted(graph.edges.get(key, set()))
            depth = compute_delegation_depth(graph, key)
            chain = trace_chain(graph, key)
            lines.append(f"### `{fn.file_stem}.{fn.symbol}`")
            lines.append(f"- **Layer:** {fn.layer}")
            lines.append(f"- **Decisions:** {fn.decision_count}")
            lines.append(f"- **Statements:** {fn.statement_count}")
            lines.append(f"- **Delegation depth:** {depth}")
            lines.append(f"- **Persistence:** {'yes' if fn.has_persistence else 'no'}")
            lines.append(f"- **Chain:** {chain}")
            if outgoing:
                lines.append(f"- **Calls:** {', '.join(outgoing)}")
            lines.append("")

    if supersets:
        lines.append("## Supersets (orchestrating functions)")
        lines.append("")
        for key in sorted(supersets):
            fn = graph.functions[key]
            subs = find_superset_of(graph, key)
            lines.append(f"### `{fn.file_stem}.{fn.symbol}`")
            lines.append(f"- **Decisions:** {fn.decision_count}, **Statements:** {fn.statement_count}")
            if subs:
                lines.append(f"- **Subsumes:** {', '.join(subs)}")
            lines.append("")

    # Wrappers
    wrappers = by_role.get("WRAPPER", [])
    if wrappers:
        lines.append("## Wrappers (thin delegation)")
        lines.append("")
        for key in sorted(wrappers):
            fn = graph.functions[key]
            outgoing = sorted(graph.edges.get(key, set()))
            target = outgoing[0] if outgoing else "?"
            lines.append(f"- `{fn.file_stem}.{fn.symbol}` → {target}")
        lines.append("")

    # Full graph (compact)
    lines.append("## Full Call Graph")
    lines.append("")
    lines.append("```")
    for key in sorted(graph.functions.keys()):
        fn = graph.functions[key]
        role = roles.get(key, "?")
        outgoing = sorted(graph.edges.get(key, set()))
        if outgoing:
            targets = ", ".join(outgoing[:5])
            if len(outgoing) > 5:
                targets += f", ...+{len(outgoing) - 5}"
            lines.append(f"[{role}] {fn.file_stem}.{fn.symbol} → {targets}")
        else:
            lines.append(f"[{role}] {fn.file_stem}.{fn.symbol}")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_tracing(
    output_dir: Path,
    domain_filter: str | None = None,
    as_json: bool = False,
) -> dict:
    """Run call-chain tracing for all domains."""
    domains = [domain_filter] if domain_filter else ALL_DOMAINS
    all_rows: list[dict[str, str]] = []
    all_stats: dict[str, dict] = {}

    for domain in domains:
        if not (CUS_ROOT / domain).is_dir():
            continue

        print(f"Tracing {domain}...")
        graph = build_call_graph(domain)

        if not graph.functions:
            print(f"  No functions found")
            continue

        roles = classify_roles(graph)
        rows = generate_csv_rows(graph, roles)
        all_rows.extend(rows)

        # Generate markdown
        md_content = generate_call_graph_markdown(graph, roles)
        domain_dir = output_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        md_path = domain_dir / "CALL_GRAPH.md"
        md_path.write_text(md_content, encoding="utf-8")

        # Stats
        by_role: dict[str, int] = defaultdict(int)
        for role in roles.values():
            by_role[role] += 1

        edge_count = sum(len(targets) for targets in graph.edges.values())
        all_stats[domain] = {
            "functions": len(graph.functions),
            "edges": edge_count,
            "by_role": dict(by_role),
        }
        print(f"  {len(graph.functions)} functions, {edge_count} edges, "
              f"{by_role.get('CANONICAL', 0)} canonical, "
              f"{by_role.get('WRAPPER', 0)} wrappers, "
              f"{by_role.get('SUPERSET', 0)} supersets")

    if as_json:
        result = {
            "total_functions": len(all_rows),
            "domains": all_stats,
            "rows": all_rows,
        }
        json.dump(result, sys.stdout, indent=2)
        print()
        return result

    # Write CSV
    csv_path = output_dir / "CALL_CHAINS.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nCSV written: {csv_path}")
    print(f"  Rows: {len(all_rows)}")
    print(f"  Domains: {len(all_stats)}")

    # Summary
    total_canonical = sum(s["by_role"].get("CANONICAL", 0) for s in all_stats.values())
    total_wrapper = sum(s["by_role"].get("WRAPPER", 0) for s in all_stats.values())
    total_superset = sum(s["by_role"].get("SUPERSET", 0) for s in all_stats.values())
    print(f"\n  Total canonical: {total_canonical}")
    print(f"  Total wrappers: {total_wrapper}")
    print(f"  Total supersets: {total_superset}")

    return {"total": len(all_rows), "domains": all_stats}


def main():
    parser = argparse.ArgumentParser(
        description="HOC Call-Chain Tracer — intra-domain function call graph + role classification"
    )
    parser.add_argument("--output-dir", type=str,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--domain", type=str, help="Process only this domain")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR

    print("=" * 60)
    print("HOC Call-Chain Tracer")
    print("=" * 60)
    print()

    run_tracing(output_dir, domain_filter=args.domain, as_json=args.json)

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
