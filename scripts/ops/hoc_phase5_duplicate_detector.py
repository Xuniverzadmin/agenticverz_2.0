#!/usr/bin/env python3
"""
HOC Phase 5 — Duplicate Detection

Detects duplicates across HOC customer domains using 3 modes:
  Mode 1: Exact file match (SHA-256 hash)
  Mode 2: Function/class signature match (AST-based)
  Mode 3: Block similarity (>80% via SequenceMatcher)

Produces:
  - PHASE5_DUPLICATE_REPORT.csv
  - PHASE5_DUPLICATE_SUMMARY.md
  - PHASE5_CONSOLIDATION_CANDIDATES.csv

Reference: PIN-470, PIN-473, PIN-479
Artifact Class: CODE
Layer: OPS
Audience: INTERNAL

Usage:
    python3 scripts/ops/hoc_phase5_duplicate_detector.py
"""

import ast
import csv
import hashlib
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_HOC_CUS = REPO_ROOT / "backend" / "app" / "hoc" / "cus"
DOMAIN_MAP_DIR = BACKEND_HOC_CUS / "_domain_map"
REPORT_PATH = DOMAIN_MAP_DIR / "PHASE5_DUPLICATE_REPORT.csv"
SUMMARY_PATH = DOMAIN_MAP_DIR / "PHASE5_DUPLICATE_SUMMARY.md"
CANDIDATES_PATH = DOMAIN_MAP_DIR / "PHASE5_CONSOLIDATION_CANDIDATES.csv"

CUSTOMER_DOMAINS = [
    "account", "activity", "analytics", "api_keys", "controls",
    "general", "incidents", "integrations", "logs", "overview", "policies",
]
EXCLUDED_DIRS = {"__pycache__", "_domain_map", "docs", ".git"}
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
DATE_STR = datetime.now(timezone.utc).strftime("%Y-%m-%d")

BLOCK_SIZE = 10          # lines per block for Mode 3
SIMILARITY_THRESHOLD = 0.80  # 80% for Mode 3


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FileInfo:
    path: Path
    domain: str
    rel_path: str       # relative to domain dir
    layer: str
    sha256: str = ""
    loc: int = 0
    source: str = ""
    functions: list = field(default_factory=list)   # (name, params, lines)
    classes: list = field(default_factory=list)      # (name, methods, lines)


@dataclass
class Duplicate:
    dup_id: str
    dup_type: str       # EXACT_FILE, FUNCTION, BLOCK
    domain_a: str
    file_a: str
    location_a: str
    domain_b: str
    file_b: str
    location_b: str
    similarity_pct: float
    detail: str
    recommendation: str


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

def inventory_all_files() -> List[FileInfo]:
    files = []
    for domain in CUSTOMER_DOMAINS:
        domain_dir = BACKEND_HOC_CUS / domain
        if not domain_dir.exists():
            continue
        for root, dirs, fnames in os.walk(domain_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for fname in sorted(fnames):
                if not fname.endswith(".py") or fname == "__init__.py":
                    continue
                fpath = Path(root) / fname
                rel = str(fpath.relative_to(domain_dir))

                # Layer
                layer = "root"
                for p in Path(rel).parts:
                    if p.startswith("L"):
                        layer = p
                        break

                fi = FileInfo(path=fpath, domain=domain, rel_path=rel, layer=layer)

                # Hash + source
                raw = fpath.read_bytes()
                fi.sha256 = hashlib.sha256(raw).hexdigest()
                fi.source = raw.decode("utf-8", errors="replace")
                fi.loc = sum(1 for line in fi.source.splitlines()
                             if line.strip() and not line.strip().startswith("#"))

                # AST parse for functions/classes
                try:
                    tree = ast.parse(fi.source)
                    for node in ast.iter_child_nodes(tree):
                        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                            params = [a.arg for a in node.args.args]
                            end = node.end_lineno or node.lineno
                            fi.functions.append((node.name, params, node.lineno, end))
                        elif isinstance(node, ast.ClassDef):
                            methods = []
                            for item in node.body:
                                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    mparams = [a.arg for a in item.args.args]
                                    methods.append((item.name, mparams))
                            end = node.end_lineno or node.lineno
                            fi.classes.append((node.name, methods, node.lineno, end))
                except SyntaxError:
                    pass

                files.append(fi)
    return files


# ---------------------------------------------------------------------------
# Mode 1: Exact File Match
# ---------------------------------------------------------------------------

def mode1_exact_match(files: List[FileInfo]) -> List[Duplicate]:
    print("  Mode 1: Exact file match (SHA-256)...")
    dups = []
    hash_map = defaultdict(list)
    for fi in files:
        hash_map[fi.sha256].append(fi)

    seq = 0
    for h, group in sorted(hash_map.items()):
        if len(group) < 2:
            continue
        # Report all pairs
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                seq += 1
                # Recommend: keep in general if one is general, else keep in first alphabetically
                if a.domain == "general":
                    rec = f"DELETE_FROM_{b.domain.upper()}"
                elif b.domain == "general":
                    rec = f"DELETE_FROM_{a.domain.upper()}"
                else:
                    rec = f"EXTRACT_TO_GENERAL"
                dups.append(Duplicate(
                    dup_id=f"D{seq:03d}",
                    dup_type="EXACT_FILE",
                    domain_a=a.domain, file_a=a.rel_path, location_a="-",
                    domain_b=b.domain, file_b=b.rel_path, location_b="-",
                    similarity_pct=100.0,
                    detail=f"Identical SHA-256: {h[:12]}",
                    recommendation=rec,
                ))
    print(f"    Found {len(dups)} exact file duplicates")
    return dups


# ---------------------------------------------------------------------------
# Mode 2: Function/Class Signature Match
# ---------------------------------------------------------------------------

def mode2_function_match(files: List[FileInfo]) -> List[Duplicate]:
    print("  Mode 2: Function/class signature match...")
    dups = []
    seq_offset = 500  # offset IDs to avoid collision with Mode 1

    # Build function index: (name, param_count) -> [(file, func_info)]
    func_index = defaultdict(list)
    for fi in files:
        for fname, params, start, end in fi.functions:
            key = (fname, len(params))
            func_index[key].append((fi, fname, params, start, end))

    seq = 0
    seen = set()
    for key, entries in func_index.items():
        if len(entries) < 2:
            continue
        # Cross-domain pairs only
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                fi_a, fn_a, pa_a, s_a, e_a = entries[i]
                fi_b, fn_b, pa_b, s_b, e_b = entries[j]

                if fi_a.domain == fi_b.domain and fi_a.rel_path == fi_b.rel_path:
                    continue  # same file

                pair_key = tuple(sorted([
                    f"{fi_a.domain}/{fi_a.rel_path}:{fn_a}",
                    f"{fi_b.domain}/{fi_b.rel_path}:{fn_b}",
                ]))
                if pair_key in seen:
                    continue
                seen.add(pair_key)

                # Compare function bodies
                lines_a = fi_a.source.splitlines()[s_a - 1:e_a]
                lines_b = fi_b.source.splitlines()[s_b - 1:e_b]
                sim = SequenceMatcher(None, lines_a, lines_b).ratio()

                if sim < 0.70:
                    continue

                seq += 1
                sim_pct = round(sim * 100, 1)

                if fi_a.domain == "general":
                    rec = f"DELETE_FROM_{fi_b.domain.upper()}"
                elif fi_b.domain == "general":
                    rec = f"DELETE_FROM_{fi_a.domain.upper()}"
                elif sim >= 0.95:
                    rec = "EXTRACT_TO_GENERAL"
                else:
                    rec = "REVIEW_MERGE"

                dups.append(Duplicate(
                    dup_id=f"D{seq_offset + seq:03d}",
                    dup_type="FUNCTION",
                    domain_a=fi_a.domain,
                    file_a=fi_a.rel_path,
                    location_a=f"{fn_a}():{s_a}-{e_a}",
                    domain_b=fi_b.domain,
                    file_b=fi_b.rel_path,
                    location_b=f"{fn_b}():{s_b}-{e_b}",
                    similarity_pct=sim_pct,
                    detail=f"Function '{fn_a}' ({len(pa_a)} params), {sim_pct}% body match",
                    recommendation=rec,
                ))

    # Also check class signatures
    class_index = defaultdict(list)
    for fi in files:
        for cname, methods, start, end in fi.classes:
            method_sig = tuple(sorted(m[0] for m in methods))
            key = (cname, method_sig)
            class_index[key].append((fi, cname, methods, start, end))

    seen_classes = set()
    for key, entries in class_index.items():
        if len(entries) < 2:
            continue
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                fi_a, cn_a, _, s_a, e_a = entries[i]
                fi_b, cn_b, _, s_b, e_b = entries[j]

                if fi_a.domain == fi_b.domain and fi_a.rel_path == fi_b.rel_path:
                    continue

                pair_key = tuple(sorted([
                    f"{fi_a.domain}/{fi_a.rel_path}:{cn_a}",
                    f"{fi_b.domain}/{fi_b.rel_path}:{cn_b}",
                ]))
                if pair_key in seen_classes:
                    continue
                seen_classes.add(pair_key)

                lines_a = fi_a.source.splitlines()[s_a - 1:e_a]
                lines_b = fi_b.source.splitlines()[s_b - 1:e_b]
                sim = SequenceMatcher(None, lines_a, lines_b).ratio()

                if sim < 0.70:
                    continue

                seq += 1
                sim_pct = round(sim * 100, 1)

                if fi_a.domain == "general":
                    rec = f"DELETE_FROM_{fi_b.domain.upper()}"
                elif fi_b.domain == "general":
                    rec = f"DELETE_FROM_{fi_a.domain.upper()}"
                elif sim >= 0.95:
                    rec = "EXTRACT_TO_GENERAL"
                else:
                    rec = "REVIEW_MERGE"

                dups.append(Duplicate(
                    dup_id=f"D{seq_offset + seq:03d}",
                    dup_type="CLASS",
                    domain_a=fi_a.domain,
                    file_a=fi_a.rel_path,
                    location_a=f"class {cn_a}:{s_a}-{e_a}",
                    domain_b=fi_b.domain,
                    file_b=fi_b.rel_path,
                    location_b=f"class {cn_b}:{s_b}-{e_b}",
                    similarity_pct=sim_pct,
                    detail=f"Class '{cn_a}' with same methods, {sim_pct}% body match",
                    recommendation=rec,
                ))

    print(f"    Found {len(dups)} function/class signature duplicates (>70% body match)")
    return dups


# ---------------------------------------------------------------------------
# Mode 3: Block Similarity
# ---------------------------------------------------------------------------

def mode3_block_similarity(files: List[FileInfo]) -> List[Duplicate]:
    print("  Mode 3: Block similarity (10-line blocks, >80%)...")
    dups = []
    seq_offset = 900

    # Only compare files with the same name across different domains (targeted)
    name_map = defaultdict(list)
    for fi in files:
        name_map[fi.path.name].append(fi)

    seq = 0
    for fname, group in sorted(name_map.items()):
        if len(group) < 2:
            continue

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a.domain == b.domain and a.rel_path == b.rel_path:
                    continue

                # Full file similarity
                lines_a = [l for l in a.source.splitlines() if l.strip()]
                lines_b = [l for l in b.source.splitlines() if l.strip()]

                if len(lines_a) < BLOCK_SIZE or len(lines_b) < BLOCK_SIZE:
                    continue

                sim = SequenceMatcher(None, lines_a, lines_b).ratio()
                if sim < SIMILARITY_THRESHOLD:
                    continue

                seq += 1
                sim_pct = round(sim * 100, 1)

                if a.domain == "general":
                    rec = f"DELETE_FROM_{b.domain.upper()}"
                elif b.domain == "general":
                    rec = f"DELETE_FROM_{a.domain.upper()}"
                elif sim >= 0.95:
                    rec = "LIKELY_EXACT_COPY"
                else:
                    rec = "REVIEW_FOR_CONSOLIDATION"

                dups.append(Duplicate(
                    dup_id=f"D{seq_offset + seq:03d}",
                    dup_type="BLOCK",
                    domain_a=a.domain,
                    file_a=a.rel_path,
                    location_a=f"full file ({len(lines_a)} lines)",
                    domain_b=b.domain,
                    file_b=b.rel_path,
                    location_b=f"full file ({len(lines_b)} lines)",
                    similarity_pct=sim_pct,
                    detail=f"Same-name files, {sim_pct}% content match",
                    recommendation=rec,
                ))

    print(f"    Found {len(dups)} block-level duplicates (same name, >80% match)")
    return dups


# ---------------------------------------------------------------------------
# Consolidation candidates
# ---------------------------------------------------------------------------

def build_candidates(all_dups: List[Duplicate]) -> list:
    """Group duplicates into consolidation candidates."""
    # Group by file pair
    pair_map = defaultdict(list)
    for d in all_dups:
        key = tuple(sorted([
            f"{d.domain_a}/{d.file_a}",
            f"{d.domain_b}/{d.file_b}",
        ]))
        pair_map[key].append(d)

    candidates = []
    for idx, (pair, dups) in enumerate(sorted(pair_map.items()), 1):
        dup_ids = ",".join(d.dup_id for d in dups)
        types = set(d.dup_type for d in dups)
        max_sim = max(d.similarity_pct for d in dups)
        d0 = dups[0]

        # Determine canonical location
        if d0.domain_a == "general":
            canonical = f"{d0.domain_a}/{d0.file_a}"
            delete = f"{d0.domain_b}/{d0.file_b}"
        elif d0.domain_b == "general":
            canonical = f"{d0.domain_b}/{d0.file_b}"
            delete = f"{d0.domain_a}/{d0.file_a}"
        else:
            canonical = f"general/{Path(d0.file_a).name}"
            delete = f"{d0.domain_a}/{d0.file_a},{d0.domain_b}/{d0.file_b}"

        candidates.append({
            "candidate_id": f"C{idx:03d}",
            "duplicate_ids": dup_ids,
            "types": "|".join(sorted(types)),
            "max_similarity": max_sim,
            "canonical_location": canonical,
            "delete_locations": delete,
            "recommendation": dups[0].recommendation,
        })

    return candidates


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

DUP_FIELDS = [
    "dup_id", "dup_type", "domain_a", "file_a", "location_a",
    "domain_b", "file_b", "location_b", "similarity_pct", "detail", "recommendation",
]

CAND_FIELDS = [
    "candidate_id", "duplicate_ids", "types", "max_similarity",
    "canonical_location", "delete_locations", "recommendation",
]


def write_report(dups: List[Duplicate]):
    with open(REPORT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=DUP_FIELDS)
        w.writeheader()
        for d in dups:
            w.writerow({k: getattr(d, k) for k in DUP_FIELDS})
    print(f"  Report:     {REPORT_PATH} ({len(dups)} rows)")


def write_candidates(candidates: list):
    with open(CANDIDATES_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAND_FIELDS)
        w.writeheader()
        w.writerows(candidates)
    print(f"  Candidates: {CANDIDATES_PATH} ({len(candidates)} rows)")


def write_summary(dups: List[Duplicate], candidates: list, file_count: int):
    m1 = [d for d in dups if d.dup_type == "EXACT_FILE"]
    m2 = [d for d in dups if d.dup_type in ("FUNCTION", "CLASS")]
    m3 = [d for d in dups if d.dup_type == "BLOCK"]

    lines = [
        "# Phase 5 — Duplicate Detection Summary",
        "",
        f"**Generated:** {DATE_STR}",
        f"**Generator:** `hoc_phase5_duplicate_detector.py`",
        f"**Reference:** PIN-470, PIN-479",
        f"**Files scanned:** {file_count}",
        "",
        "---",
        "",
        "## Detection Results",
        "",
        "| Mode | Type | Threshold | Duplicates Found |",
        "|------|------|-----------|-----------------|",
        f"| Mode 1 | Exact File (SHA-256) | 100% | {len(m1)} |",
        f"| Mode 2 | Function/Class Signature | >70% body | {len(m2)} |",
        f"| Mode 3 | Block Similarity (same name) | >80% | {len(m3)} |",
        f"| **Total** | | | **{len(dups)}** |",
        "",
        f"**Consolidation candidates:** {len(candidates)}",
        "",
        "---",
        "",
    ]

    # Mode 1 details
    if m1:
        lines += [
            "## Mode 1: Exact File Duplicates",
            "",
            "| ID | Domain A | File | Domain B | File | Recommendation |",
            "|----|----------|------|----------|------|----------------|",
        ]
        for d in m1:
            lines.append(
                f"| {d.dup_id} | {d.domain_a} | `{d.file_a}` | {d.domain_b} | `{d.file_b}` | {d.recommendation} |"
            )
        lines += ["", "---", ""]

    # Mode 2 details
    if m2:
        lines += [
            "## Mode 2: Function/Class Signature Duplicates",
            "",
            "| ID | Type | Domain A | Location A | Domain B | Location B | Similarity | Recommendation |",
            "|----|------|----------|-----------|----------|-----------|-----------|----------------|",
        ]
        for d in sorted(m2, key=lambda x: -x.similarity_pct):
            lines.append(
                f"| {d.dup_id} | {d.dup_type} | {d.domain_a} | `{d.file_a}:{d.location_a}` | "
                f"{d.domain_b} | `{d.file_b}:{d.location_b}` | {d.similarity_pct}% | {d.recommendation} |"
            )
        lines += ["", "---", ""]

    # Mode 3 details
    if m3:
        lines += [
            "## Mode 3: Block Similarity Duplicates",
            "",
            "| ID | Domain A | File | Domain B | File | Similarity | Recommendation |",
            "|----|----------|------|----------|------|-----------|----------------|",
        ]
        for d in sorted(m3, key=lambda x: -x.similarity_pct):
            lines.append(
                f"| {d.dup_id} | {d.domain_a} | `{d.file_a}` | {d.domain_b} | `{d.file_b}` | "
                f"{d.similarity_pct}% | {d.recommendation} |"
            )
        lines += ["", "---", ""]

    # Consolidation candidates
    if candidates:
        lines += [
            "## Consolidation Candidates",
            "",
            "| ID | Types | Max Sim | Canonical Location | Delete From | Recommendation |",
            "|----|-------|---------|-------------------|-------------|----------------|",
        ]
        for c in candidates:
            lines.append(
                f"| {c['candidate_id']} | {c['types']} | {c['max_similarity']}% | "
                f"`{c['canonical_location']}` | `{c['delete_locations']}` | {c['recommendation']} |"
            )
        lines += ["", "---", ""]

    # Recommendation distribution
    rec_counts = defaultdict(int)
    for d in dups:
        rec_counts[d.recommendation] += 1
    lines += [
        "## Recommendation Distribution",
        "",
        "| Recommendation | Count |",
        "|----------------|-------|",
    ]
    for rec, count in sorted(rec_counts.items()):
        lines.append(f"| {rec} | {count} |")

    lines += [
        "",
        "---",
        "",
        f"*Report generated: {TIMESTAMP}*",
        "",
    ]

    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Summary:    {SUMMARY_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("HOC Phase 5 — Duplicate Detection")
    print("=" * 60)

    # 1. Inventory
    print(f"\n[1/5] Inventorying files...")
    files = inventory_all_files()
    print(f"  {len(files)} files across {len(CUSTOMER_DOMAINS)} domains")

    # 2. Mode 1
    print(f"\n[2/5] Running Mode 1: Exact file match...")
    dups_m1 = mode1_exact_match(files)

    # 3. Mode 2
    print(f"\n[3/5] Running Mode 2: Function/class signature match...")
    dups_m2 = mode2_function_match(files)

    # 4. Mode 3
    print(f"\n[4/5] Running Mode 3: Block similarity...")
    dups_m3 = mode3_block_similarity(files)

    # 5. Combine + output
    all_dups = dups_m1 + dups_m2 + dups_m3
    print(f"\n[5/5] Generating outputs...")
    print(f"  Total duplicates: {len(all_dups)}")

    candidates = build_candidates(all_dups)
    write_report(all_dups)
    write_candidates(candidates)
    write_summary(all_dups, candidates, len(files))

    print(f"\nPhase 5 complete.")
    print(f"  Exact file:    {len(dups_m1)}")
    print(f"  Function/class: {len(dups_m2)}")
    print(f"  Block:          {len(dups_m3)}")
    print(f"  Candidates:     {len(candidates)}")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
