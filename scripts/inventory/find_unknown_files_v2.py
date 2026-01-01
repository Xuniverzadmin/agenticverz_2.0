#!/usr/bin/env python3
"""Find files with layer=UNKNOWN (handles both Python and TS)"""

import os
import re
from pathlib import Path

BASE_DIR = Path("/root/agenticverz2.0")

SCAN_DIRS = [
    "backend/app",
    "backend/cli",
    "backend/tests",
    "sdk/python",
    "sdk/js",
    "scripts",
    "website/aos-console/console/src",
]

EXCLUDE_PATTERNS = [
    "__pycache__",
    "node_modules",
    ".git",
    ".pyc",
    "/dist/",
    "/build/",
    ".d.ts",
    ".map",
    ".json",
]

# Match both Python and TS header formats
LAYER_PATTERN_PY = re.compile(r"^#\s*Layer:\s*(L\d+)", re.MULTILINE)
LAYER_PATTERN_TS = re.compile(r"^//\s*Layer:\s*(L\d+)", re.MULTILINE)


def should_skip(path: str) -> bool:
    return any(p in path for p in EXCLUDE_PATTERNS)


def has_layer_header(content: str, ext: str) -> bool:
    first_2k = content[:2000]
    if ext in [".py"]:
        return bool(LAYER_PATTERN_PY.search(first_2k))
    else:  # TS/JS/TSX
        return bool(LAYER_PATTERN_TS.search(first_2k))


def infer_layer_from_path(path: Path) -> str:
    path_str = str(path)

    if "tests/" in path_str or "test_" in path.name:
        return "L8"
    if "scripts/" in path_str:
        return "L7"
    if "/worker/" in path_str:
        return "L5"
    if "/services/" in path_str:
        return "L4"
    if "/api/" in path_str:
        return "L2"
    if "/adapters/" in path_str or "/boundary/" in path_str:
        return "L3"
    if path_str.endswith(".tsx") or "/pages/" in path_str:
        return "L1"
    if "/components/" in path_str:
        return "L1"
    if "db.py" in path_str or "/memory/" in path_str:
        return "L6"
    if "/cli/" in path_str:
        return "L7"
    if "/sdk/" in path_str:
        return "L6"
    if "/workflow/" in path_str:
        return "L4"
    if "/auth/" in path_str or "/security/" in path_str:
        return "L6"
    if "/runtime/" in path_str:
        return "L5"
    if "/skills/" in path_str:
        return "L4"
    if "/costsim/" in path_str or "/blackboard/" in path_str:
        return "L4"
    if "/policy/" in path_str:
        return "L4"
    if "/traces/" in path_str:
        return "L6"
    if "/stores/" in path_str:
        return "L6"
    if "/models/" in path_str:
        return "L6"
    if "/schemas/" in path_str:
        return "L6"
    if "/middleware/" in path_str:
        return "L6"
    if "/utils/" in path_str:
        return "L6"
    if "/learning/" in path_str:
        return "L4"
    if "/routing/" in path_str:
        return "L4"
    if "/optimization/" in path_str:
        return "L4"
    if "/sba/" in path_str:
        return "L4"
    if "/planners/" in path_str:
        return "L3"
    if "/contracts/" in path_str:
        return "L6"
    if "/jobs/" in path_str:
        return "L5"
    if "/tasks/" in path_str:
        return "L5"
    if "/agents/" in path_str:
        return "L4"

    return "UNKNOWN"


def scan_directory(scan_dir: str):
    unknown_files = []

    full_path = BASE_DIR / scan_dir
    if not full_path.exists():
        return unknown_files

    for root, dirs, files in os.walk(full_path):
        dirs[:] = [d for d in dirs if not should_skip(d)]

        for fname in files:
            fpath = Path(root) / fname
            rel_path = str(fpath.relative_to(BASE_DIR))

            if should_skip(rel_path):
                continue

            if fpath.suffix not in [".py", ".ts", ".tsx", ".js"]:
                continue

            try:
                content = fpath.read_text(errors="ignore")
            except:
                continue

            # Check if has header (using correct format for file type)
            if has_layer_header(content, fpath.suffix):
                continue  # Has header, skip

            # Check path inference
            layer = infer_layer_from_path(fpath)
            if layer == "UNKNOWN":
                unknown_files.append(rel_path)

    return unknown_files


def main():
    all_unknown = []

    for scan_dir in SCAN_DIRS:
        unknown = scan_directory(scan_dir)
        all_unknown.extend(unknown)

    all_unknown.sort()

    print(f"Total UNKNOWN files: {len(all_unknown)}")
    if all_unknown:
        print()
        for f in all_unknown:
            print(f)


if __name__ == "__main__":
    main()
