#!/usr/bin/env python3
# Layer: L4 — Verification Script
# AUDIENCE: INTERNAL
# Role: Guard against forbidden /api/v1/stagetest/* route references
# artifact_class: CODE
"""
Stagetest Route Prefix Guard

Scans the codebase for forbidden /api/v1/stagetest/ references.
Canonical prefix is /hoc/api/stagetest/*.

Exit 0 if clean, exit 1 if forbidden references found.
"""

import os
import sys
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FORBIDDEN_PATTERN = re.compile(r"/api/v1/stagetest")
CANONICAL_PATTERN = re.compile(r"/hoc/api/stagetest")

# Directories to skip
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "dist",
    "dist-preflight", "playwright-report", "test-results",
}

# File extensions to scan
SCAN_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".yaml", ".yml",
    ".sh", ".toml", ".cfg",
}

# Files that are allowed to mention the forbidden pattern
# (this guard, its test, plan/taskpack docs that describe the rule, test assertions)
ALLOW_FILES = {
    "stagetest_route_prefix_guard.py",
    "test_stagetest_route_prefix_guard.py",
    "test_stagetest_read_api.py",
    "STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15.md",
    "STAGETEST_HOC_API_EVIDENCE_CONSOLE_PLAN_2026-02-15.md",
    "STAGETEST_SUBDOMAIN_DEPLOY_PLAN_2026-02-15.md",
    "HOC_USECASE_CODE_LINKAGE.md",
    "STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_FOR_CLAUDE_2026-02-15_implemented.md",
}


def scan_file(filepath: str) -> list[tuple[int, str]]:
    """Return list of (line_number, line_text) with forbidden pattern."""
    hits = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if FORBIDDEN_PATTERN.search(line):
                    hits.append((i, line.rstrip()))
    except (OSError, UnicodeDecodeError):
        pass
    return hits


def scan_codebase() -> dict:
    """Scan entire repo for forbidden and canonical stagetest route references."""
    forbidden_hits: list[dict] = []
    canonical_count = 0
    files_scanned = 0

    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in SCAN_EXTENSIONS:
                continue
            if fname in ALLOW_FILES:
                continue

            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, REPO_ROOT)
            files_scanned += 1

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except (OSError, UnicodeDecodeError):
                continue

            # Count canonical references
            canonical_count += len(CANONICAL_PATTERN.findall(content))

            # Find forbidden references
            for i, line in enumerate(content.splitlines(), 1):
                if FORBIDDEN_PATTERN.search(line):
                    forbidden_hits.append({
                        "file": rel_path,
                        "line": i,
                        "text": line.strip(),
                    })

    return {
        "files_scanned": files_scanned,
        "forbidden_count": len(forbidden_hits),
        "forbidden_hits": forbidden_hits,
        "canonical_count": canonical_count,
    }


def main():
    print("Stagetest Route Prefix Guard")
    print("=" * 60)
    print(f"Forbidden: /api/v1/stagetest/*")
    print(f"Canonical: /hoc/api/stagetest/*")
    print()

    result = scan_codebase()

    print(f"Files scanned: {result['files_scanned']}")
    print(f"Canonical references: {result['canonical_count']}")
    print(f"Forbidden references: {result['forbidden_count']}")
    print()

    if result["forbidden_count"] > 0:
        print("FORBIDDEN REFERENCES FOUND:")
        for hit in result["forbidden_hits"]:
            print(f"  {hit['file']}:{hit['line']}: {hit['text']}")
        print()
        print(f"FAIL: {result['forbidden_count']} forbidden /api/v1/stagetest references found")
        sys.exit(1)
    else:
        print("PASS: No forbidden /api/v1/stagetest references found")
        sys.exit(0)


if __name__ == "__main__":
    main()
