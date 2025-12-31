#!/usr/bin/env python3
"""
Complete Codebase Inventory vs Layered Inventory
Produces full mapping of repository structure to layer model

Version 2.0 - Added Non-Executable Artifact Classes
Reference: PIN-248 (Codebase Inventory & Layer System)

Artifact Classes:
  CODE   - Executable code with imports
  DATA   - Static data files (JSON, etc)
  STYLE  - Stylesheets (CSS, SCSS)
  CONFIG - Configuration files (YAML, INI, etc)
  DOC    - Documentation (Markdown)
  TEST   - Test files

Every artifact must have:
  - a layer OR
  - a declared non-executable artifact class
  but NEVER be unclassified
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

BASE_DIR = Path("/root/agenticverz2.0")

# All directories to scan
SCAN_DIRS = [
    "backend/app",
    "backend/cli",
    "backend/tests",
    "sdk/python",
    "sdk/js",
    "scripts",
    "website/aos-console/console/src",
    "docs",
    "monitoring",
    "config",
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
    "package-lock.json",
    "yarn.lock",
    ".env",
]

# Header patterns
LAYER_PATTERN_PY = re.compile(r"^#\s*Layer:\s*(L\d+)\s*[—-]\s*(.+)", re.MULTILINE)
LAYER_PATTERN_TS = re.compile(r"^//\s*Layer:\s*(L\d+)\s*[—-]\s*(.+)", re.MULTILINE)
PRODUCT_PATTERN_PY = re.compile(r"^#\s*Product:\s*(.+)", re.MULTILINE)
PRODUCT_PATTERN_TS = re.compile(r"^//\s*Product:\s*(.+)", re.MULTILINE)
ROLE_PATTERN_PY = re.compile(r"^#\s*Role:\s*(.+)", re.MULTILINE)
ROLE_PATTERN_TS = re.compile(r"^//\s*Role:\s*(.+)", re.MULTILINE)

LAYER_NAMES = {
    "L1": "Product Experience",
    "L2": "Product APIs",
    "L3": "Boundary Adapters",
    "L4": "Domain Engines",
    "L5": "Execution & Workers",
    "L6": "Platform Substrate",
    "L7": "Ops & Deployment",
    "L8": "Catalyst / Meta",
}

# Artifact class definitions
ARTIFACT_CLASSES = {
    "CODE": "Executable code with imports",
    "DATA": "Static data files",
    "STYLE": "Stylesheets",
    "CONFIG": "Configuration files",
    "DOC": "Documentation",
    "TEST": "Test files",
}

def should_skip(path: str) -> bool:
    return any(p in path for p in EXCLUDE_PATTERNS)


def get_file_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in ['.py']:
        return 'python'
    elif ext in ['.ts', '.tsx']:
        return 'typescript'
    elif ext in ['.js', '.jsx']:
        return 'javascript'
    elif ext in ['.md']:
        return 'markdown'
    elif ext in ['.yaml', '.yml']:
        return 'yaml'
    elif ext in ['.json']:
        return 'json'
    elif ext in ['.sh']:
        return 'shell'
    elif ext in ['.sql']:
        return 'sql'
    elif ext in ['.css', '.scss']:
        return 'css'
    elif ext in ['.html']:
        return 'html'
    elif ext in ['.toml']:
        return 'toml'
    elif ext in ['.cfg', '.ini', '.conf']:
        return 'config'
    elif ext == '':
        if path.name in ['Dockerfile', 'Makefile', 'Procfile']:
            return 'config'
    return 'other'


def get_artifact_class(path: Path, file_type: str) -> Tuple[str, bool]:
    """
    Determine artifact class and whether it's executable.
    Returns (artifact_class, is_executable)
    """
    path_str = str(path)

    # Non-executable artifact classes

    # STYLE: CSS/SCSS files
    if file_type == 'css':
        return "STYLE", False

    # DATA: JSON files in /data/ directories
    if file_type == 'json' and '/data/' in path_str:
        return "DATA", False

    # CONFIG: YAML, INI, TOML, and config files
    if file_type in ['yaml', 'config', 'toml']:
        return "CONFIG", False

    # CONFIG: JSON config files (package.json, tsconfig.json, etc)
    if file_type == 'json' and any(x in path.name for x in ['config', 'package', 'tsconfig', 'settings']):
        return "CONFIG", False

    # DOC: Markdown files
    if file_type == 'markdown':
        return "DOC", False

    # TEST: Test files (code, but categorized separately)
    if "tests/" in path_str or "test_" in path.name or "_test." in path.name or ".test." in path.name:
        return "TEST", True

    # Remaining JSON files that aren't data or config
    if file_type == 'json':
        return "DATA", False

    # Executable code files
    if file_type in ['python', 'typescript', 'javascript', 'shell', 'sql', 'html']:
        return "CODE", True

    return "CODE", True


def extract_header_info(content: str, file_type: str) -> Dict:
    info = {
        "layer": None,
        "layer_name": None,
        "product": None,
        "role": None,
        "has_header": False,
    }

    first_2k = content[:2000]

    if file_type == 'python':
        layer_match = LAYER_PATTERN_PY.search(first_2k)
        product_match = PRODUCT_PATTERN_PY.search(first_2k)
        role_match = ROLE_PATTERN_PY.search(first_2k)
    elif file_type in ['typescript', 'javascript']:
        layer_match = LAYER_PATTERN_TS.search(first_2k)
        product_match = PRODUCT_PATTERN_TS.search(first_2k)
        role_match = ROLE_PATTERN_TS.search(first_2k)
    else:
        return info

    if layer_match:
        info["layer"] = layer_match.group(1)
        info["layer_name"] = layer_match.group(2).strip()
        info["has_header"] = True

    if product_match:
        info["product"] = product_match.group(1).strip()

    if role_match:
        info["role"] = role_match.group(1).strip()

    return info


def infer_layer(path: Path, file_type: str, artifact_class: str) -> Tuple[str, str, str]:
    """Returns (layer, confidence, reason)"""
    path_str = str(path)

    # Non-executable artifacts get layer from context
    if artifact_class == "STYLE":
        # CSS in frontend = L1
        if "website/" in path_str or "console/" in path_str:
            return "L1", "medium", "frontend stylesheet"
        return "L1", "low", "stylesheet"

    if artifact_class == "DATA":
        # Data files get layer from parent directory
        if "/app/data/" in path_str:
            return "L4", "medium", "domain data"
        if "backend/" in path_str:
            return "L6", "medium", "backend data"
        return "L6", "low", "data file"

    if artifact_class == "DOC":
        return "L7", "medium", "documentation"

    if artifact_class == "CONFIG":
        if "monitoring/" in path_str:
            return "L7", "medium", "monitoring config"
        if "config/" in path_str:
            return "L7", "medium", "infrastructure config"
        return "L7", "medium", "configuration"

    if artifact_class == "TEST":
        return "L8", "medium", "test file"

    # Executable code - use existing inference logic

    # Scripts
    if "scripts/" in path_str:
        return "L7", "medium", "scripts directory"

    # CLI
    if "/cli/" in path_str:
        return "L7", "medium", "CLI tool"

    # Monitoring (shell scripts, etc)
    if "monitoring/" in path_str:
        return "L7", "medium", "monitoring scripts"

    # Frontend
    if path_str.endswith(".tsx") or "/pages/" in path_str:
        return "L1", "medium", "page component"
    if "/components/" in path_str:
        return "L1", "medium", "UI component"
    if "/hooks/" in path_str or "/lib/" in path_str or "/types/" in path_str:
        return "L1", "medium", "frontend utility"

    # API routes
    if "/api/" in path_str:
        return "L2", "medium", "API route"

    # Adapters
    if "/adapters/" in path_str or "/boundary/" in path_str or "/planners/" in path_str:
        return "L3", "medium", "adapter"

    # Domain
    if "/services/" in path_str:
        return "L4", "medium", "service"
    if "/workflow/" in path_str:
        return "L4", "medium", "workflow"
    if "/policy/" in path_str:
        return "L4", "medium", "policy engine"
    if "/skills/" in path_str:
        return "L4", "medium", "skill"
    if "/agents/" in path_str:
        return "L4", "medium", "agent"
    if "/costsim/" in path_str or "/blackboard/" in path_str:
        return "L4", "medium", "domain logic"
    if "/learning/" in path_str or "/routing/" in path_str or "/optimization/" in path_str:
        return "L4", "medium", "domain logic"
    if "/sba/" in path_str or "/predictions/" in path_str:
        return "L4", "medium", "domain logic"
    if "/discovery/" in path_str:
        return "L4", "medium", "discovery"

    # Workers
    if "/worker/" in path_str or "/runtime/" in path_str:
        return "L5", "medium", "worker/runtime"
    if "/jobs/" in path_str or "/tasks/" in path_str:
        return "L5", "medium", "job/task"

    # Platform
    if "db.py" in path_str or "/memory/" in path_str:
        return "L6", "medium", "database"
    if "/auth/" in path_str:
        return "L6", "medium", "auth"
    if "/middleware/" in path_str:
        return "L6", "medium", "middleware"
    if "/stores/" in path_str or "/storage/" in path_str:
        return "L6", "medium", "storage"
    if "/models/" in path_str or "/schemas/" in path_str:
        return "L6", "medium", "data model"
    if "/utils/" in path_str:
        return "L6", "medium", "utility"
    if "/traces/" in path_str or "/events/" in path_str:
        return "L6", "medium", "telemetry"
    if "/contracts/" in path_str or "/integrations/" in path_str:
        return "L6", "medium", "platform"
    if "/secrets/" in path_str or "/config/" in path_str:
        return "L6", "medium", "config"

    # SDK
    if "/sdk/" in path_str:
        return "L6", "low", "SDK"

    return "UNKNOWN", "low", "no pattern match"


def scan_repository():
    """Scan entire repository and build inventory"""

    inventory = {
        "by_layer": defaultdict(list),
        "by_directory": defaultdict(list),
        "by_product": defaultdict(list),
        "by_file_type": defaultdict(int),
        "by_artifact_class": defaultdict(list),
        "statistics": {
            "total_files": 0,
            "with_headers": 0,
            "without_headers": 0,
            "executable": 0,
            "non_executable": 0,
            "by_layer": defaultdict(int),
            "by_confidence": defaultdict(int),
            "by_product": defaultdict(int),
            "by_artifact_class": defaultdict(int),
        }
    }

    for scan_dir in SCAN_DIRS:
        full_path = BASE_DIR / scan_dir
        if not full_path.exists():
            continue

        for root, dirs, files in os.walk(full_path):
            dirs[:] = [d for d in dirs if not should_skip(d)]

            for fname in files:
                fpath = Path(root) / fname
                rel_path = str(fpath.relative_to(BASE_DIR))

                if should_skip(rel_path):
                    continue

                file_type = get_file_type(fpath)
                if file_type == 'other':
                    continue

                try:
                    content = fpath.read_text(errors='ignore')
                except:
                    continue

                inventory["statistics"]["total_files"] += 1
                inventory["by_file_type"][file_type] += 1

                # Determine artifact class
                artifact_class, is_executable = get_artifact_class(fpath, file_type)
                inventory["statistics"]["by_artifact_class"][artifact_class] += 1

                if is_executable:
                    inventory["statistics"]["executable"] += 1
                else:
                    inventory["statistics"]["non_executable"] += 1

                # Extract header info (only for executable code)
                header_info = extract_header_info(content, file_type)

                if header_info["has_header"]:
                    layer = header_info["layer"]
                    confidence = "high"
                    reason = "explicit header"
                    inventory["statistics"]["with_headers"] += 1
                else:
                    layer, confidence, reason = infer_layer(fpath, file_type, artifact_class)
                    inventory["statistics"]["without_headers"] += 1

                # Build file entry
                entry = {
                    "path": rel_path,
                    "layer": layer,
                    "layer_name": LAYER_NAMES.get(layer, "Unknown"),
                    "artifact_class": artifact_class,
                    "is_executable": is_executable,
                    "confidence": confidence,
                    "reason": reason,
                    "file_type": file_type,
                    "has_header": header_info["has_header"],
                    "product": header_info.get("product") or "unspecified",
                    "role": header_info.get("role"),
                }

                # Index by layer
                inventory["by_layer"][layer].append(entry)
                inventory["statistics"]["by_layer"][layer] += 1
                inventory["statistics"]["by_confidence"][confidence] += 1

                # Index by artifact class
                inventory["by_artifact_class"][artifact_class].append(entry)

                # Index by directory
                top_dir = rel_path.split('/')[0]
                inventory["by_directory"][top_dir].append(entry)

                # Index by product
                product = entry["product"]
                inventory["by_product"][product].append(entry)
                inventory["statistics"]["by_product"][product] += 1

    return inventory


def print_summary(inventory):
    """Print formatted summary"""
    stats = inventory["statistics"]
    total = stats['total_files']

    print("=" * 80)
    print("CODEBASE INVENTORY vs LAYERED INVENTORY")
    print("=" * 80)
    print()

    # Overall stats
    print("## OVERALL STATISTICS")
    print()
    print(f"Total Files Scanned: {stats['total_files']}")
    print(f"  Executable (CODE/TEST):  {stats['executable']} ({100*stats['executable']/total:.1f}%)")
    print(f"  Non-Executable:          {stats['non_executable']} ({100*stats['non_executable']/total:.1f}%)")
    print(f"  With Headers:            {stats['with_headers']} ({100*stats['with_headers']/total:.1f}%)")
    print()

    # Artifact class distribution
    print("## ARTIFACT CLASS DISTRIBUTION")
    print()
    print("| Class  | Description              | Count | % of Total |")
    print("|--------|--------------------------|-------|------------|")
    for cls in ["CODE", "TEST", "DOC", "CONFIG", "DATA", "STYLE"]:
        count = stats['by_artifact_class'].get(cls, 0)
        pct = 100 * count / total if total > 0 else 0
        desc = ARTIFACT_CLASSES.get(cls, "")
        print(f"| {cls:6} | {desc:24} | {count:5} | {pct:9.1f}% |")
    print()

    # Layer distribution
    print("## LAYER DISTRIBUTION")
    print()
    print("| Layer | Name                  | Count | % of Total |")
    print("|-------|----------------------|-------|------------|")

    for layer in ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "UNKNOWN"]:
        count = stats['by_layer'].get(layer, 0)
        pct = 100 * count / total if total > 0 else 0
        name = LAYER_NAMES.get(layer, "Unknown")
        print(f"| {layer:5} | {name:20} | {count:5} | {pct:9.1f}% |")
    print()

    # Confidence distribution
    print("## CONFIDENCE DISTRIBUTION")
    print()
    print("| Confidence | Count | % of Total |")
    print("|------------|-------|------------|")
    for conf in ["high", "medium", "low"]:
        count = stats['by_confidence'].get(conf, 0)
        pct = 100 * count / total if total > 0 else 0
        print(f"| {conf:10} | {count:5} | {pct:9.1f}% |")
    print()

    # File type distribution
    print("## FILE TYPE DISTRIBUTION")
    print()
    print("| Type       | Count |")
    print("|------------|-------|")
    for ftype, count in sorted(inventory['by_file_type'].items(), key=lambda x: -x[1]):
        print(f"| {ftype:10} | {count:5} |")
    print()

    # Directory breakdown
    print("## DIRECTORY → LAYER MAPPING")
    print()
    for directory in sorted(inventory['by_directory'].keys()):
        files = inventory['by_directory'][directory]
        layer_counts = defaultdict(int)
        for f in files:
            layer_counts[f['layer']] += 1

        print(f"### {directory}/ ({len(files)} files)")
        for layer in ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "UNKNOWN"]:
            if layer_counts[layer] > 0:
                print(f"  {layer}: {layer_counts[layer]}")
        print()

    # UNKNOWN files (if any)
    unknown = inventory['by_layer'].get('UNKNOWN', [])
    if unknown:
        print("## ⚠️ UNKNOWN FILES (need classification)")
        print()
        for f in unknown:
            print(f"  {f['path']} ({f['artifact_class']})")
        print()
    else:
        print("## ✅ NO UNKNOWN FILES")
        print()
        print("All artifacts are classified into either:")
        print("  - A layer (L1-L8) for executable code")
        print("  - A non-executable artifact class (DATA, STYLE, CONFIG, DOC)")
        print()


def print_json(inventory):
    """Print JSON summary"""
    summary = {
        "statistics": {
            "total_files": inventory["statistics"]["total_files"],
            "executable": inventory["statistics"]["executable"],
            "non_executable": inventory["statistics"]["non_executable"],
            "with_headers": inventory["statistics"]["with_headers"],
            "without_headers": inventory["statistics"]["without_headers"],
            "layer_distribution": dict(inventory["statistics"]["by_layer"]),
            "artifact_class_distribution": dict(inventory["statistics"]["by_artifact_class"]),
            "confidence_distribution": dict(inventory["statistics"]["by_confidence"]),
            "product_distribution": dict(inventory["statistics"]["by_product"]),
        },
        "file_types": dict(inventory["by_file_type"]),
        "unknown_count": len(inventory["by_layer"].get("UNKNOWN", [])),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    import sys

    inventory = scan_repository()

    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print_json(inventory)
    else:
        print_summary(inventory)
