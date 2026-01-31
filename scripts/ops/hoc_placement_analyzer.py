#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Placement decisions + AST body-fingerprint duplicate detection (intra-domain) from classified function inventory
# artifact_class: CODE

"""
HOC Placement Analyzer

Reads the classified FUNCTION_INVENTORY.csv (with intent columns) and:
1. Decides L4 placement for each function
2. Detects TRUE duplicates via AST body fingerprinting (intra-domain only)
3. Excludes thin wrappers from duplicate groups
4. Outputs PLACEMENT_DECISIONS.csv

Duplicate detection principle:
  Names may repeat. Algorithms must not.
  Ownership is canonical. Usage is not duplication.

Usage:
    python3 scripts/ops/hoc_placement_analyzer.py
    python3 scripts/ops/hoc_placement_analyzer.py --domain incidents
    python3 scripts/ops/hoc_placement_analyzer.py --json
"""

import argparse
import ast
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUS_ROOT = PROJECT_ROOT / "backend" / "app" / "hoc" / "cus"
MODELS_ROOT = PROJECT_ROOT / "backend" / "app" / "models"
DEFAULT_INPUT = PROJECT_ROOT / "literature" / "hoc_domain" / "FUNCTION_INVENTORY.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "literature" / "hoc_domain" / "PLACEMENT_DECISIONS.csv"

ALL_DOMAINS = [
    "account", "activity", "analytics", "api_keys", "apis",
    "controls", "docs", "incidents", "integrations", "logs",
    "overview", "policies",
]


# ---------------------------------------------------------------------------
# Placement Rules (unchanged)
# ---------------------------------------------------------------------------


def decide_placement(row: dict[str, str]) -> tuple[str, str]:
    """
    Decide placement for a function. Returns (placement, reason).

    Rules:
    - Wire to L4 if: intent=Operation + L2-callable + needs governance
    - Keep in L5 if: Internal Helper, pure computation, L5-only callers
    - Move to L4 if: Coordinator + cross-domain data pull
    - Keep in L6 if: Persistence/Driver
    """
    intent = row.get("intent", "")
    called_by = row.get("called_by", "")
    side_effects = row.get("side_effects", "")
    layer = row.get("layer", "")
    symbol = row.get("symbol", "")

    fn_name = symbol.split(".")[-1] if "." in symbol else symbol
    if fn_name.startswith("_"):
        return "keep-current", "private function — no placement change"

    if layer == "L6":
        return "keep-L6", "persistence layer — stays in L6"

    if layer == "L7":
        return "keep-L7", "model layer — stays in L7"

    if intent == "Operation" and "L2:" in called_by and "L4:" not in called_by:
        return "wire-to-L4", "Operation called by L2 directly (gap) — needs L4 wiring"

    if intent == "Operation" and "L4:" in called_by:
        return "keep-L5-wired", "Operation already wired through L4"

    if intent == "Coordinator/Aggregator" and "L2:" in called_by:
        return "move-to-L4", "Coordinator called by L2 — should be L4 orchestrated"

    if intent == "Policy/Decision":
        return "keep-L5", "decision logic — belongs in L5 domain engine"

    if intent == "Internal Helper":
        return "keep-L5", "internal helper — stays in L5"

    if side_effects == "pure" and not called_by:
        return "keep-L5", "pure orphan — keep in L5 pending review"

    if intent == "Unclassified":
        return "review", "unclassified intent — needs manual review"

    return "keep-current", "no placement rule matched"


# ---------------------------------------------------------------------------
# AST Body Fingerprinting
# ---------------------------------------------------------------------------


class _BodyNormalizer(ast.NodeTransformer):
    """Normalize an AST body for fingerprinting.

    Strips: variable names, docstrings, comments, string literals.
    Preserves: control flow structure, call targets, operator types,
    statement count, persistence patterns.
    """

    def __init__(self):
        self._var_counter = 0
        self._var_map: dict[str, str] = {}

    def _norm_name(self, name: str) -> str:
        if name in ("self", "cls", "True", "False", "None"):
            return name
        if name not in self._var_map:
            self._var_map[name] = f"v{self._var_counter}"
            self._var_counter += 1
        return self._var_map[name]

    def visit_Name(self, node: ast.Name) -> ast.Name:
        node.id = self._norm_name(node.id)
        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        # Normalize literals: strings → "<S>", numbers → 0
        if isinstance(node.value, str):
            node.value = "<S>"
        elif isinstance(node.value, (int, float)):
            node.value = 0
        return node

    def visit_Expr(self, node: ast.Expr) -> ast.Expr | None:
        # Remove standalone string expressions (docstrings)
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None
        return self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> ast.arg:
        node.arg = self._norm_name(node.arg)
        node.annotation = None
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        node.name = "fn"
        node.decorator_list = []
        node.returns = None
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        node.name = "fn"
        node.decorator_list = []
        node.returns = None
        return self.generic_visit(node)


def compute_body_fingerprint(source: str, func_name: str, class_name: str = "") -> str | None:
    """Compute a normalized AST body fingerprint for a function.

    Returns a hex digest, or None if the function can't be found/parsed.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    target_node = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if class_name:
                # Check if this function is inside the right class
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef) and parent.name == class_name:
                        for child in ast.walk(parent):
                            if child is node and node.name == func_name:
                                target_node = node
                                break
            elif node.name == func_name:
                target_node = node
                break

    if target_node is None:
        return None

    # Normalize
    import copy
    body_copy = copy.deepcopy(target_node)
    normalizer = _BodyNormalizer()
    normalized = normalizer.visit(body_copy)
    ast.fix_missing_locations(normalized)

    try:
        dumped = ast.dump(normalized, annotate_fields=False)
    except Exception:
        return None

    return hashlib.sha256(dumped.encode()).hexdigest()[:16]


def detect_wrapper(source: str, func_name: str, class_name: str = "") -> bool:
    """Detect if a function is a thin wrapper (delegation only).

    A wrapper: ≤3 executable statements, contains a single meaningful call,
    returns that call's result. No branching, no persistence, no policy checks.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    target_node = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            if class_name:
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef) and parent.name == class_name:
                        for child in ast.walk(parent):
                            if child is node:
                                target_node = node
                                break
            else:
                target_node = node
                break

    if target_node is None:
        return False

    # Filter out docstring from body
    body = [
        stmt for stmt in target_node.body
        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str))
    ]

    if len(body) > 3:
        return False

    # Check for branching (If, For, While, Try with multiple handlers)
    for stmt in body:
        if isinstance(stmt, (ast.If, ast.For, ast.While)):
            return False
        if isinstance(stmt, ast.Try) and len(stmt.handlers) > 1:
            return False

    # Check: single call + return pattern
    calls = 0
    for stmt in body:
        for child in ast.walk(stmt):
            if isinstance(child, ast.Call):
                calls += 1

    # A wrapper has 1-2 calls max (the delegation + maybe a constructor)
    return calls <= 2


# ---------------------------------------------------------------------------
# Intra-Domain Duplicate Detection
# ---------------------------------------------------------------------------


def build_fingerprint_map(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Build {domain:file:symbol → fingerprint} by parsing source files.

    Only processes L5 functions (L6/L7 excluded — persistence is expected to repeat).
    """
    fingerprints: dict[str, dict[str, str]] = {}  # key → {fingerprint, is_wrapper}

    # Group rows by source file path for efficient parsing
    by_file: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        layer = row.get("layer", "")
        if layer not in ("L5",):
            continue
        symbol = row.get("symbol", "")
        fn_name = symbol.split(".")[-1] if "." in symbol else symbol
        if fn_name.startswith("_"):
            continue
        domain = row.get("domain", "")
        file_stem = row.get("file", "")
        by_file[f"{domain}/{file_stem}"].append(row)

    # Resolve file paths and parse
    for domain_file, file_rows in by_file.items():
        domain, file_stem = domain_file.split("/", 1)

        # Find the actual source file
        source_file = _find_source_file(domain, file_stem)
        if source_file is None:
            continue

        try:
            source = source_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        for row in file_rows:
            symbol = row.get("symbol", "")
            class_name = ""
            func_name = symbol
            if "." in symbol:
                class_name, func_name = symbol.split(".", 1)

            key = f"{row.get('domain')}:{row.get('file')}:{symbol}"

            fp = compute_body_fingerprint(source, func_name, class_name)
            is_wrapper = detect_wrapper(source, func_name, class_name)

            fingerprints[key] = {
                "fingerprint": fp or "",
                "is_wrapper": "yes" if is_wrapper else "no",
            }

    return fingerprints


def _find_source_file(domain: str, file_stem: str) -> Path | None:
    """Resolve a domain + file stem to an actual .py path."""
    if domain == "_models":
        candidate = MODELS_ROOT / f"{file_stem}.py"
        return candidate if candidate.exists() else None

    domain_dir = CUS_ROOT / domain
    if not domain_dir.is_dir():
        return None

    # Search L5_*/L6_drivers
    for child in domain_dir.iterdir():
        if not child.is_dir():
            continue
        if not (child.name.startswith("L5_") or child.name == "L6_drivers"):
            continue
        candidate = child / f"{file_stem}.py"
        if candidate.exists():
            return candidate
        # Check subdirectories
        for sub in child.rglob(f"{file_stem}.py"):
            if sub.name == f"{file_stem}.py":
                return sub

    return None


def detect_duplicates_by_fingerprint(
    rows: list[dict[str, str]],
    fingerprints: dict[str, dict[str, str]],
) -> dict[str, list[dict[str, str]]]:
    """Detect intra-domain duplicates using AST body fingerprint.

    Groups functions within the SAME domain that have identical fingerprints
    and are NOT wrappers.
    """
    # Group by (domain, fingerprint)
    by_domain_fp: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        key = f"{row.get('domain')}:{row.get('file')}:{row.get('symbol')}"
        fp_data = fingerprints.get(key)
        if not fp_data:
            continue
        fp = fp_data["fingerprint"]
        if not fp:
            continue
        if fp_data["is_wrapper"] == "yes":
            continue  # Wrappers excluded

        domain = row.get("domain", "")
        group_key = f"{domain}::{fp}"
        by_domain_fp[group_key].append(row)

    # Filter: 2+ functions with same fingerprint in same domain
    duplicates: dict[str, list[dict[str, str]]] = {}
    for group_key, group in by_domain_fp.items():
        if len(group) >= 2:
            # Verify they're in different files (same file = overloads, not dupes)
            files = set(r.get("file", "") for r in group)
            if len(files) >= 2:
                duplicates[group_key] = group

    return duplicates


def pick_canonical(group: list[dict[str, str]]) -> str:
    """Pick canonical function from a duplicate group.

    Prefer: most callers, clearest intent, least side effects.
    """
    scored = []
    for row in group:
        score = 0
        if row.get("intent") != "Unclassified":
            score += 3
        if row.get("called_by"):
            # More callers = more authoritative
            score += len(row.get("called_by", "").split(" | "))
        if row.get("side_effects") == "pure":
            score += 1
        scored.append((score, row))

    scored.sort(key=lambda x: -x[0])
    winner = scored[0][1]
    return f"{winner.get('domain')}/{winner.get('file')}.{winner.get('symbol')}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_analysis(
    input_path: Path,
    output_path: Path,
    domain_filter: str | None = None,
    as_json: bool = False,
) -> dict:
    """Run placement analysis and duplicate detection."""
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        print("Run hoc_function_inventory_generator.py + hoc_intent_classifier.py first.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        input_columns = list(reader.fieldnames or [])
        rows = list(reader)

    if domain_filter:
        rows = [r for r in rows if r.get("domain") == domain_filter]

    if rows and "intent" not in rows[0]:
        print("ERROR: Input CSV missing 'intent' column. Run hoc_intent_classifier.py first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(rows)} function records")

    # Placement decisions
    for row in rows:
        placement, reason = decide_placement(row)
        row["placement"] = placement
        row["placement_reason"] = reason

    # AST body fingerprinting
    print("Computing AST body fingerprints...")
    fingerprints = build_fingerprint_map(rows)
    wrapper_count = sum(1 for v in fingerprints.values() if v["is_wrapper"] == "yes")
    print(f"  Fingerprinted {len(fingerprints)} L5 functions ({wrapper_count} wrappers)")

    # Intra-domain duplicate detection
    duplicates = detect_duplicates_by_fingerprint(rows, fingerprints)
    print(f"  Detected {len(duplicates)} true intra-domain duplicate groups")

    # Annotate rows
    dup_map: dict[str, tuple[str, str]] = {}
    for group_key, group in duplicates.items():
        canonical = pick_canonical(group)
        for row in group:
            key = f"{row.get('domain')}:{row.get('file')}:{row.get('symbol')}"
            dup_map[key] = (group_key, canonical)

    for row in rows:
        key = f"{row.get('domain')}:{row.get('file')}:{row.get('symbol')}"
        fp_data = fingerprints.get(key, {})

        row["algo_fingerprint"] = fp_data.get("fingerprint", "")
        row["is_wrapper"] = fp_data.get("is_wrapper", "")

        if key in dup_map:
            row["duplicate_role"] = "DUPLICATE"
            row["duplicate_group"] = dup_map[key][0]
            row["duplicate_canonical"] = dup_map[key][1]
            # Mark canonical
            if dup_map[key][1] == f"{row.get('domain')}/{row.get('file')}.{row.get('symbol')}":
                row["duplicate_role"] = "CANONICAL"
        elif fp_data.get("is_wrapper") == "yes":
            row["duplicate_role"] = "WRAPPER"
            row["duplicate_group"] = ""
            row["duplicate_canonical"] = ""
        else:
            row["duplicate_role"] = ""
            row["duplicate_group"] = ""
            row["duplicate_canonical"] = ""

    # Stats
    by_placement: dict[str, int] = {}
    by_role: dict[str, int] = {}
    for r in rows:
        by_placement[r["placement"]] = by_placement.get(r["placement"], 0) + 1
        role = r.get("duplicate_role", "")
        if role:
            by_role[role] = by_role.get(role, 0) + 1

    if as_json:
        result = {
            "total": len(rows),
            "by_placement": by_placement,
            "by_duplicate_role": by_role,
            "duplicate_groups": len(duplicates),
            "wrappers": wrapper_count,
            "duplicate_details": {
                gk: {
                    "canonical": pick_canonical(group),
                    "functions": [
                        f"{r.get('domain')}/{r.get('file')}.{r.get('symbol')}"
                        for r in group
                    ],
                }
                for gk, group in duplicates.items()
            },
            "rows": rows,
        }
        json.dump(result, sys.stdout, indent=2)
        print()
        return result

    # Write CSV
    output_columns = list(input_columns)
    for col in ("placement", "placement_reason", "algo_fingerprint", "is_wrapper",
                "duplicate_role", "duplicate_group", "duplicate_canonical"):
        if col not in output_columns:
            output_columns.append(col)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV written: {output_path}")
    print(f"  Rows: {len(rows)}")
    print("\nBy placement:")
    for p in sorted(by_placement):
        print(f"  {p}: {by_placement[p]}")

    print(f"\nWrappers detected: {wrapper_count}")
    print(f"\nBy duplicate_role:")
    for role in sorted(by_role):
        print(f"  {role}: {by_role[role]}")

    if duplicates:
        print(f"\nTrue duplicate groups ({len(duplicates)}):")
        for gk, group in sorted(duplicates.items()):
            canonical = pick_canonical(group)
            files = sorted(set(f"{r.get('file')}.{r.get('symbol')}" for r in group))
            print(f"  {gk}")
            print(f"    canonical: {canonical}")
            for f in files:
                tag = " ← CANONICAL" if f in canonical else ""
                print(f"    - {f}{tag}")

    return {"total": len(rows), "by_placement": by_placement}


def main():
    parser = argparse.ArgumentParser(
        description="HOC Placement Analyzer — placement decisions + AST body-fingerprint duplicate detection"
    )
    parser.add_argument("--input", "-i", type=str,
                        help=f"Input CSV path (default: {DEFAULT_INPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--output", "-o", type=str,
                        help=f"Output CSV path (default: {DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--domain", type=str, help="Process only this domain")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else DEFAULT_INPUT
    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    print("=" * 60)
    print("HOC Placement Analyzer")
    print("=" * 60)
    print()

    run_analysis(input_path, output_path, domain_filter=args.domain, as_json=args.json)

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
