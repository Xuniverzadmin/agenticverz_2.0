#!/usr/bin/env python3
"""
Alembic Migration Audit

Generates a per-migration CSV + summary sheet to standardize metadata
and surface potential breakages (missing downgrade, missing metadata,
raw SQL usage, etc.).

Default output: /root/agenticverz2.0/hoc/doc/architeture/alembic
"""

from __future__ import annotations

import argparse
import ast
import csv
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


SQL_KEYWORDS = [
    "CREATE TABLE",
    "DROP TABLE",
    "ALTER TABLE",
    "CREATE INDEX",
    "DROP INDEX",
    "CREATE VIEW",
    "DROP VIEW",
    "CREATE TYPE",
    "DROP TYPE",
    "CREATE TRIGGER",
    "DROP TRIGGER",
    "INSERT INTO",
    "UPDATE",
    "DELETE FROM",
]


def _safe_literal_eval(node: ast.AST) -> Optional[Any]:
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def parse_metadata(tree: ast.AST) -> Dict[str, Optional[Any]]:
    meta: Dict[str, Optional[Any]] = {
        "revision": None,
        "down_revision": None,
        "branch_labels": None,
        "depends_on": None,
    }

    for node in getattr(tree, "body", []):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            key = target.id
            if key in meta:
                meta[key] = _safe_literal_eval(node.value)
    return meta


def find_functions(tree: ast.AST) -> set[str]:
    names = set()
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
    return names


def find_op_calls(source: str) -> Counter:
    calls = re.findall(r"\bop\.(\w+)\(", source)
    return Counter(calls)


def extract_sql_blocks(source: str) -> list[str]:
    blocks: list[str] = []

    triple_pattern = re.compile(
        r"op\.execute\(\s*([\"']{3})([\s\S]*?)\1\s*\)", re.MULTILINE
    )
    for _, sql in triple_pattern.findall(source):
        blocks.append(sql.strip())

    single_pattern = re.compile(
        r"op\.execute\(\s*([\"'])([^\n\r]*?)\1\s*\)", re.MULTILINE
    )
    for _, sql in single_pattern.findall(source):
        if sql.strip():
            blocks.append(sql.strip())

    return blocks


def classify_sql(sql_blocks: Iterable[str]) -> Counter:
    counts = Counter()
    for sql in sql_blocks:
        upper = sql.upper()
        for keyword in SQL_KEYWORDS:
            if keyword in upper:
                counts[keyword] += 1
    return counts


def analyze_migration(path: Path) -> Dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    meta = parse_metadata(tree)
    fn_names = find_functions(tree)
    op_calls = find_op_calls(source)
    sql_blocks = extract_sql_blocks(source)
    sql_keywords = classify_sql(sql_blocks)

    warnings = []
    if not meta.get("revision"):
        warnings.append("missing_revision")
    if meta.get("down_revision") in (None, ""):
        warnings.append("missing_down_revision")
    if "upgrade" not in fn_names:
        warnings.append("missing_upgrade")
    if "downgrade" not in fn_names:
        warnings.append("missing_downgrade")

    return {
        "file": path.name,
        "path": str(path),
        "revision": meta.get("revision"),
        "down_revision": meta.get("down_revision"),
        "branch_labels": meta.get("branch_labels"),
        "depends_on": meta.get("depends_on"),
        "has_upgrade": "upgrade" in fn_names,
        "has_downgrade": "downgrade" in fn_names,
        "op_calls": op_calls,
        "sql_keywords": sql_keywords,
        "raw_sql_blocks": sql_blocks,
        "warnings": warnings,
    }


def write_summary(out_dir: Path, data: Dict[str, Any]) -> Path:
    out_path = out_dir / f"{data['file']}.summary.md"
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    op_lines = [
        f"- `{k}`: {v}" for k, v in sorted(data["op_calls"].items())
    ] or ["- (none)"]

    sql_lines = [
        f"- `{k}`: {v}" for k, v in sorted(data["sql_keywords"].items())
    ] or ["- (none)"]

    warning_lines = [f"- `{w}`" for w in data["warnings"]] or ["- (none)"]

    content = "\n".join(
        [
            f"# Alembic Migration Summary: {data['file']}",
            "",
            f"**Generated:** {created_at}",
            f"**Revision:** `{data['revision']}`",
            f"**Down Revision:** `{data['down_revision']}`",
            f"**Branch Labels:** `{data['branch_labels']}`",
            f"**Depends On:** `{data['depends_on']}`",
            f"**Has Upgrade:** `{data['has_upgrade']}`",
            f"**Has Downgrade:** `{data['has_downgrade']}`",
            "",
            "## Op Calls",
            *op_lines,
            "",
            "## Raw SQL Keywords",
            *sql_lines,
            "",
            "## Warnings",
            *warning_lines,
        ]
    )

    out_path.write_text(content + "\n", encoding="utf-8")
    return out_path


def write_csv(out_dir: Path, data: Dict[str, Any]) -> Path:
    out_path = out_dir / f"{data['file']}.csv"
    rows = []

    # Metadata
    rows.append(["meta", "file", data["file"]])
    rows.append(["meta", "path", data["path"]])
    rows.append(["meta", "revision", data["revision"]])
    rows.append(["meta", "down_revision", data["down_revision"]])
    rows.append(["meta", "branch_labels", data["branch_labels"]])
    rows.append(["meta", "depends_on", data["depends_on"]])
    rows.append(["meta", "has_upgrade", data["has_upgrade"]])
    rows.append(["meta", "has_downgrade", data["has_downgrade"]])

    # Op calls
    for name, count in sorted(data["op_calls"].items()):
        rows.append(["op_call", name, count])

    # SQL keywords
    for name, count in sorted(data["sql_keywords"].items()):
        rows.append(["sql_keyword", name, count])

    # Warnings
    for warning in data["warnings"]:
        rows.append(["warning", warning, True])

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["kind", "name", "value"])
        writer.writerows(rows)

    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Alembic migration audit")
    parser.add_argument(
        "--migrations-dir",
        default=None,
        help="Path to alembic versions directory",
    )
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Output directory for CSV/summary files",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[3]

    migrations_dir = Path(args.migrations_dir) if args.migrations_dir else repo_root / "backend" / "alembic" / "versions"
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / "hoc" / "doc" / "architeture" / "alembic"

    if not migrations_dir.exists():
        raise SystemExit(f"Migrations dir not found: {migrations_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    migration_files = sorted(p for p in migrations_dir.glob("*.py") if p.is_file())
    if not migration_files:
        raise SystemExit(f"No migration files found in: {migrations_dir}")

    for path in migration_files:
        data = analyze_migration(path)
        write_summary(out_dir, data)
        write_csv(out_dir, data)

    print(f"Generated {len(migration_files)} migration reports in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
