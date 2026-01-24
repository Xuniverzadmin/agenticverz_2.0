#!/usr/bin/env python3
"""
Layer Analysis - Pass 1: Signal Detection

Scans HOC Python files and extracts layer signals based on:
- Import patterns
- Class/function names
- Decorators
- Code patterns
- Header metadata

Output: signals_raw.json

Usage:
    python scripts/migration/layer_analysis.py
    python scripts/migration/layer_analysis.py --domain policies
    python scripts/migration/layer_analysis.py --file path/to/file.py
"""

import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set

# Change to repo root
os.chdir(Path(__file__).parent.parent.parent)

HOC_ROOT = Path("backend/app/houseofcards")
OUTPUT_FILE = Path("docs/architecture/migration/signals_raw.json")

# Whitelist paths (excluded from analysis)
WHITELIST_PATTERNS = [
    "*/general/utils/*",
    "*/__init__.py",
    "*/tests/*",
    "*/duplicate/*",
]


@dataclass
class Signal:
    """A detected signal in a file."""
    pattern: str
    layer: str
    line: Optional[int] = None
    violation: Optional[str] = None


@dataclass
class HeaderInfo:
    """Extracted header metadata."""
    declared_layer: Optional[str] = None
    audience: Optional[str] = None
    role: Optional[str] = None
    raw_layer_line: Optional[str] = None


@dataclass
class FileAnalysis:
    """Complete analysis of a single file."""
    file: str
    relative_path: str
    folder_layer: Optional[str] = None  # Layer implied by folder
    header: HeaderInfo = field(default_factory=HeaderInfo)
    signals: List[Signal] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    error: Optional[str] = None


# =============================================================================
# Signal Patterns
# =============================================================================

# L2 API Signals
L2_IMPORT_PATTERNS = [
    (r"from fastapi import", "L2_API"),
    (r"from fastapi.responses import", "L2_API"),
    (r"import fastapi", "L2_API"),
    (r"APIRouter", "L2_API"),
    (r"Request\b", "L2_API"),
    (r"Response\b", "L2_API"),
    (r"HTTPException", "L2_API"),
    (r"JSONResponse", "L2_API"),
    (r"BackgroundTasks", "L2_API"),
]

L2_CODE_PATTERNS = [
    (r"@router\.(get|post|put|delete|patch)", "L2_API"),
    (r"async def \w+\(.*request:\s*Request", "L2_API"),
    (r"return JSONResponse", "L2_API"),
    (r"raise HTTPException", "L2_API"),
]

# L6 Driver Signals (DB Access)
L6_IMPORT_PATTERNS = [
    (r"from sqlalchemy import", "L6_DRIVER"),
    (r"from sqlalchemy\.orm import", "L6_DRIVER"),
    (r"from sqlmodel import Session", "L6_DRIVER"),
    (r"from sqlmodel import", "L6_DRIVER"),
    (r"from app\.models", "L6_DRIVER"),
    (r"from app\.db import", "L6_DRIVER"),
]

L6_CODE_PATTERNS = [
    (r"session\.execute\(", "L6_DRIVER"),
    (r"session\.add\(", "L6_DRIVER"),
    (r"session\.commit\(", "L6_DRIVER"),
    (r"session\.flush\(", "L6_DRIVER"),
    (r"session\.refresh\(", "L6_DRIVER"),
    (r"\.scalars\(\)", "L6_DRIVER"),
    (r"\.one\(\)", "L6_DRIVER"),
    (r"\.all\(\)", "L6_DRIVER"),
    (r"\.first\(\)", "L6_DRIVER"),
    (r"select\(", "L6_DRIVER"),
    (r"insert\(", "L6_DRIVER"),
    (r"update\(", "L6_DRIVER"),
    (r"delete\(", "L6_DRIVER"),
]

# L6 Schema Signals
L6_SCHEMA_PATTERNS = [
    (r"class \w+\(BaseModel\)", "L6_SCHEMA"),
    (r"class \w+\(str, Enum\)", "L6_SCHEMA"),
    (r"class \w+\(Enum\)", "L6_SCHEMA"),
    (r"@dataclass", "L6_SCHEMA"),
    (r"Field\(", "L6_SCHEMA"),
]

# L4 Engine Signals
L4_CLASS_PATTERNS = [
    (r"class \w+Engine\b", "L4_ENGINE"),
    (r"class \w+Service\b", "L4_ENGINE"),  # In engines/ folder context
    (r"class \w+Command\b", "L4_ENGINE"),
]

L4_POSITIVE_PATTERNS = [
    (r"Verdict", "L4_ENGINE_GOOD"),
    (r"Decision", "L4_ENGINE_GOOD"),
    (r"Outcome", "L4_ENGINE_GOOD"),
]

# L3 Adapter Signals
L3_CLASS_PATTERNS = [
    (r"class \w+Adapter\b", "L3_ADAPTER"),
    (r"class \w+Facade\b", "L3_ADAPTER"),
]

# L5 Worker Signals
L5_CLASS_PATTERNS = [
    (r"class \w+Worker\b", "L5_WORKER"),
    (r"class \w+Processor\b", "L5_WORKER"),
    (r"class \w+Handler\b", "L5_WORKER"),
]

L5_FUNCTION_PATTERNS = [
    (r"async def process_", "L5_WORKER"),
    (r"async def compute_", "L5_WORKER"),
    (r"async def run_", "L5_WORKER"),
]

# Temporal Leak Signals
TEMPORAL_PATTERNS = [
    (r"time\.sleep\(", "TEMPORAL_LEAK"),
    (r"asyncio\.sleep\(", "TEMPORAL_LEAK"),
    (r"@retry", "RETRY_PATTERN"),
    (r"tenacity", "RETRY_PATTERN"),
]


def is_whitelisted(file_path: Path) -> bool:
    """Check if file should be excluded from analysis."""
    path_str = str(file_path)

    if file_path.name == "__init__.py":
        return True
    if "/duplicate/" in path_str:
        return True
    if "/tests/" in path_str:
        return True
    if "/general/utils/" in path_str:
        return True

    return False


def extract_folder_layer(file_path: Path) -> Optional[str]:
    """Determine expected layer from folder structure."""
    path_str = str(file_path)

    if "/api/" in path_str:
        return "L2"
    if "/facades/" in path_str:
        return "L3"
    if "/adapters/" in path_str:
        return "L3"
    if "/engines/" in path_str:
        return "L4"
    if "/workers/" in path_str:
        return "L5"
    if "/drivers/" in path_str:
        return "L6"
    if "/schemas/" in path_str:
        return "L6"

    return None


def extract_header(content: str) -> HeaderInfo:
    """Extract layer metadata from file header."""
    header = HeaderInfo()

    # Look at first 50 lines
    lines = content.split("\n")[:50]

    for line in lines:
        # Layer declaration
        match = re.search(r"#\s*Layer:\s*L(\d+)", line, re.IGNORECASE)
        if match:
            header.declared_layer = f"L{match.group(1)}"
            header.raw_layer_line = line.strip()

        # Audience
        match = re.search(r"#\s*AUDIENCE:\s*(\w+)", line, re.IGNORECASE)
        if match:
            header.audience = match.group(1).upper()

        # Role
        match = re.search(r"#\s*Role:\s*(.+)", line, re.IGNORECASE)
        if match:
            header.role = match.group(1).strip()

    return header


def extract_imports(content: str) -> List[str]:
    """Extract all import statements."""
    imports = []

    # Match import and from...import statements
    for match in re.finditer(r"^(from .+? import .+|import .+)$", content, re.MULTILINE):
        imports.append(match.group(1))

    return imports


def extract_classes(content: str) -> List[str]:
    """Extract class names."""
    classes = []

    for match in re.finditer(r"^class (\w+)", content, re.MULTILINE):
        classes.append(match.group(1))

    return classes


def extract_functions(content: str) -> List[str]:
    """Extract function names."""
    functions = []

    for match in re.finditer(r"^(?:async )?def (\w+)", content, re.MULTILINE):
        functions.append(match.group(1))

    return functions


def strip_type_checking_blocks(content: str) -> str:
    """
    Remove TYPE_CHECKING conditional blocks from content.

    TYPE_CHECKING imports are for type hints only and don't run at runtime.
    They should not be counted as layer signals.

    Handles:
        if TYPE_CHECKING:
            from sqlmodel import Session
            from app.models.foo import Bar
    """
    # Pattern to match TYPE_CHECKING blocks
    # Matches: if TYPE_CHECKING: followed by indented lines
    lines = content.split("\n")
    result_lines = []
    in_type_checking = False
    type_checking_indent = 0

    for line in lines:
        stripped = line.lstrip()

        # Check for TYPE_CHECKING block start
        if stripped.startswith("if TYPE_CHECKING:"):
            in_type_checking = True
            type_checking_indent = len(line) - len(stripped)
            continue

        # If inside TYPE_CHECKING block
        if in_type_checking:
            # Check if we've exited the block (less indentation or empty)
            current_indent = len(line) - len(stripped) if stripped else float("inf")
            if stripped and current_indent <= type_checking_indent:
                in_type_checking = False
                result_lines.append(line)
            # Skip lines inside TYPE_CHECKING block
            continue

        result_lines.append(line)

    return "\n".join(result_lines)


def detect_signals(content: str, file_path: Path) -> List[Signal]:
    """Detect all layer signals in file content."""
    signals = []
    folder_layer = extract_folder_layer(file_path)

    # Strip TYPE_CHECKING blocks for L6 import detection
    # TYPE_CHECKING imports are type hints only, not runtime dependencies
    runtime_content = strip_type_checking_blocks(content)

    # Check import patterns
    for pattern, layer in L2_IMPORT_PATTERNS:
        if re.search(pattern, content):
            signals.append(Signal(pattern=pattern, layer=layer))

    # L6 imports checked against runtime content (excludes TYPE_CHECKING)
    for pattern, layer in L6_IMPORT_PATTERNS:
        if re.search(pattern, runtime_content):
            signals.append(Signal(pattern=pattern, layer=layer))

    # Check code patterns
    for pattern, layer in L2_CODE_PATTERNS:
        if re.search(pattern, content):
            signals.append(Signal(pattern=pattern, layer=layer))

    for pattern, layer in L6_CODE_PATTERNS:
        if re.search(pattern, content):
            signals.append(Signal(pattern=pattern, layer=layer))

    for pattern, layer in L6_SCHEMA_PATTERNS:
        if re.search(pattern, content):
            signals.append(Signal(pattern=pattern, layer=layer))

    # L4 patterns (context-aware - only in engines/ folder)
    if folder_layer == "L4":
        for pattern, layer in L4_CLASS_PATTERNS:
            if re.search(pattern, content):
                signals.append(Signal(pattern=pattern, layer=layer))

        for pattern, layer in L4_POSITIVE_PATTERNS:
            if re.search(pattern, content):
                signals.append(Signal(pattern=pattern, layer=layer))

    # L3 patterns
    for pattern, layer in L3_CLASS_PATTERNS:
        if re.search(pattern, content):
            signals.append(Signal(pattern=pattern, layer=layer))

    # L5 patterns
    for pattern, layer in L5_CLASS_PATTERNS:
        if re.search(pattern, content):
            signals.append(Signal(pattern=pattern, layer=layer))

    for pattern, layer in L5_FUNCTION_PATTERNS:
        if re.search(pattern, content):
            signals.append(Signal(pattern=pattern, layer=layer))

    # Temporal patterns (violations)
    for pattern, layer in TEMPORAL_PATTERNS:
        if re.search(pattern, content):
            signals.append(Signal(pattern=pattern, layer=layer, violation="TEMPORAL_LEAK"))

    return signals


def analyze_file(file_path: Path) -> FileAnalysis:
    """Analyze a single Python file."""
    relative_path = str(file_path.relative_to(Path("backend")))

    analysis = FileAnalysis(
        file=str(file_path),
        relative_path=relative_path,
        folder_layer=extract_folder_layer(file_path)
    )

    try:
        content = file_path.read_text(encoding="utf-8")

        analysis.header = extract_header(content)
        analysis.imports = extract_imports(content)
        analysis.classes = extract_classes(content)
        analysis.functions = extract_functions(content)
        analysis.signals = detect_signals(content, file_path)

    except Exception as e:
        analysis.error = str(e)

    return analysis


def analyze_hoc_files(domain_filter: Optional[str] = None,
                       file_filter: Optional[str] = None) -> List[FileAnalysis]:
    """Analyze all HOC Python files."""
    results = []

    if file_filter:
        # Single file mode
        file_path = Path(file_filter)
        if file_path.exists():
            results.append(analyze_file(file_path))
        return results

    # Scan HOC directory
    for py_file in HOC_ROOT.rglob("*.py"):
        if is_whitelisted(py_file):
            continue

        if domain_filter:
            if f"/{domain_filter}/" not in str(py_file):
                continue

        results.append(analyze_file(py_file))

    return results


def to_json_serializable(obj):
    """Convert dataclass to JSON-serializable dict."""
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return obj


def main():
    import argparse

    parser = argparse.ArgumentParser(description="HOC Layer Signal Detection")
    parser.add_argument("--domain", help="Filter by domain (e.g., policies)")
    parser.add_argument("--file", help="Analyze single file")
    parser.add_argument("--output", default=str(OUTPUT_FILE), help="Output file")
    args = parser.parse_args()

    print("=" * 60)
    print("HOC LAYER ANALYSIS - PASS 1: SIGNAL DETECTION")
    print("=" * 60)

    results = analyze_hoc_files(
        domain_filter=args.domain,
        file_filter=args.file
    )

    print(f"\nFiles analyzed: {len(results)}")

    # Count signals by layer
    signal_counts: Dict[str, int] = {}
    for r in results:
        for s in r.signals:
            layer = s.layer
            signal_counts[layer] = signal_counts.get(layer, 0) + 1

    print("\nSignal Distribution:")
    for layer, count in sorted(signal_counts.items()):
        print(f"  {layer}: {count}")

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "meta": {
            "files_analyzed": len(results),
            "signal_counts": signal_counts,
            "domain_filter": args.domain,
            "file_filter": args.file,
        },
        "files": [to_json_serializable(r) for r in results]
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2, default=str)

    print(f"\nOutput written to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
