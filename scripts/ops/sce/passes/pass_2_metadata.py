# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Pass 2 - Semantic Claim Extraction
# Callers: sce_runner.py
# Allowed Imports: L6 (stdlib only), L8
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: SCE_CONTRACT.yaml

"""
Pass 2: Semantic Claim Extraction

Source: metadata_only

Extracts:
  - declared_layer
  - declared_role
  - declared_emits
  - declared_consumes
  - declared_boundary

Emits:
  - DECLARED_SIGNAL_EMIT
  - DECLARED_SIGNAL_CONSUME

This pass extracts CLAIMS from metadata. Claims are NOT truth.
This pass is READ-ONLY. It does not modify any files.
"""

import re
from typing import Dict, List


# Metadata patterns to extract from file headers
METADATA_PATTERNS = {
    "layer": r"#\s*Layer:\s*(L[1-8])\s*[-—]\s*(.+)",
    "product": r"#\s*Product:\s*(.+)",
    "trigger": r"#\s*Trigger:\s*(.+)",
    "execution": r"#\s*Execution:\s*(.+)",
    "role": r"#\s*Role:\s*(.+)",
    "callers": r"#\s*Callers:\s*(.+)",
    "allowed_imports": r"#\s*Allowed\s+Imports:\s*(.+)",
    "forbidden_imports": r"#\s*Forbidden\s+Imports:\s*(.+)",
    "reference": r"#\s*Reference:\s*(.+)",
    "emits": r"#\s*Emits:\s*(.+)",
    "consumes": r"#\s*Consumes:\s*(.+)",
    "boundary": r"#\s*Boundary:\s*(.+)",
}

# Docstring patterns for signal declarations
DOCSTRING_SIGNAL_PATTERNS = [
    r"Emits:\s*(.+)",
    r"Consumes:\s*(.+)",
    r"Signals:\s*(.+)",
    r"Events:\s*(.+)",
    r"Publishes:\s*(.+)",
    r"Subscribes:\s*(.+)",
]


def extract_header_metadata(content: str, max_lines: int = 50) -> Dict[str, str]:
    """
    Extract metadata from file header comments.

    Returns dict of metadata key -> value
    """
    metadata = {}
    lines = content.split("\n")[:max_lines]

    for line in lines:
        for key, pattern in METADATA_PATTERNS.items():
            match = re.match(pattern, line.strip(), re.IGNORECASE)
            if match:
                if key == "layer":
                    metadata[key] = match.group(1)
                    metadata["layer_name"] = match.group(2).strip()
                else:
                    metadata[key] = match.group(1).strip()

    return metadata


def extract_docstring_signals(content: str) -> List[Dict]:
    """
    Extract signal declarations from docstrings.

    Returns list of signal info dicts.
    """
    signals = []

    # Find all docstrings
    docstring_pattern = r'"""(.*?)"""'
    docstrings = re.findall(docstring_pattern, content, re.DOTALL)

    for docstring in docstrings:
        for pattern in DOCSTRING_SIGNAL_PATTERNS:
            matches = re.findall(pattern, docstring, re.IGNORECASE)
            for match in matches:
                signal_type = (
                    "emit"
                    if "emit" in pattern.lower() or "publish" in pattern.lower()
                    else "consume"
                )
                signals.append(
                    {
                        "signal_type": signal_type,
                        "signal_name": match.strip(),
                        "source": "docstring",
                    }
                )

    return signals


def extract_decorator_signals(content: str) -> List[Dict]:
    """
    Extract signal declarations from decorators.

    Looks for patterns like:
    - @emits("signal_name")
    - @consumes("signal_name")
    - @event_handler("signal_name")
    - @publishes("signal_name")
    - @subscribes("signal_name")
    """
    signals = []

    decorator_patterns = [
        (r"@emits?\s*\(\s*['\"](.+?)['\"]\s*\)", "emit"),
        (r"@publishes?\s*\(\s*['\"](.+?)['\"]\s*\)", "emit"),
        (r"@consumes?\s*\(\s*['\"](.+?)['\"]\s*\)", "consume"),
        (r"@subscribes?\s*\(\s*['\"](.+?)['\"]\s*\)", "consume"),
        (r"@event_handler\s*\(\s*['\"](.+?)['\"]\s*\)", "consume"),
        (r"@on_event\s*\(\s*['\"](.+?)['\"]\s*\)", "consume"),
    ]

    lines = content.split("\n")
    for i, line in enumerate(lines):
        for pattern, signal_type in decorator_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                signals.append(
                    {
                        "signal_type": signal_type,
                        "signal_name": match.group(1),
                        "source": "decorator",
                        "line_number": i + 1,
                    }
                )

    return signals


def extract_comment_signals(content: str) -> List[Dict]:
    """
    Extract signal declarations from inline comments.

    Looks for patterns like:
    - # EMITS: signal_name
    - # CONSUMES: signal_name
    - # SIGNAL: signal_name (emit/consume)
    """
    signals = []

    comment_patterns = [
        (r"#\s*EMITS?:\s*(.+)", "emit"),
        (r"#\s*PUBLISHES?:\s*(.+)", "emit"),
        (r"#\s*CONSUMES?:\s*(.+)", "consume"),
        (r"#\s*SUBSCRIBES?:\s*(.+)", "consume"),
        (r"#\s*SIGNAL:\s*(.+?)\s*\((emit|consume)\)", None),  # Explicit type
    ]

    lines = content.split("\n")
    for i, line in enumerate(lines):
        for pattern, signal_type in comment_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                if signal_type is None:
                    # Explicit type in pattern
                    sig_name = match.group(1).strip()
                    sig_type = match.group(2).lower()
                else:
                    sig_name = match.group(1).strip()
                    sig_type = signal_type

                signals.append(
                    {
                        "signal_type": sig_type,
                        "signal_name": sig_name,
                        "source": "comment",
                        "line_number": i + 1,
                    }
                )

    return signals


def extract_declared_signals(file_path: str, content: str) -> List[Dict]:
    """
    Extract all declared signals from a file.

    Combines signals from:
    - Header metadata (Emits:, Consumes:)
    - Docstrings
    - Decorators
    - Inline comments
    """
    signals = []

    # Extract header metadata first
    metadata = extract_header_metadata(content)

    # Add header-declared emits
    if "emits" in metadata:
        for signal_name in metadata["emits"].split(","):
            signals.append(
                {
                    "file_path": file_path,
                    "signal_type": "emit",
                    "signal_name": signal_name.strip(),
                    "declared_layer": metadata.get("layer"),
                    "declared_role": metadata.get("role"),
                    "declared_boundary": metadata.get("boundary"),
                    "line_number": None,
                    "raw_metadata": f"Emits: {metadata['emits']}",
                }
            )

    # Add header-declared consumes
    if "consumes" in metadata:
        for signal_name in metadata["consumes"].split(","):
            signals.append(
                {
                    "file_path": file_path,
                    "signal_type": "consume",
                    "signal_name": signal_name.strip(),
                    "declared_layer": metadata.get("layer"),
                    "declared_role": metadata.get("role"),
                    "declared_boundary": metadata.get("boundary"),
                    "line_number": None,
                    "raw_metadata": f"Consumes: {metadata['consumes']}",
                }
            )

    # Extract from docstrings
    docstring_signals = extract_docstring_signals(content)
    for sig in docstring_signals:
        signals.append(
            {
                "file_path": file_path,
                "signal_type": sig["signal_type"],
                "signal_name": sig["signal_name"],
                "declared_layer": metadata.get("layer"),
                "declared_role": metadata.get("role"),
                "declared_boundary": metadata.get("boundary"),
                "line_number": None,
                "raw_metadata": f"docstring: {sig['signal_name']}",
            }
        )

    # Extract from decorators
    decorator_signals = extract_decorator_signals(content)
    for sig in decorator_signals:
        signals.append(
            {
                "file_path": file_path,
                "signal_type": sig["signal_type"],
                "signal_name": sig["signal_name"],
                "declared_layer": metadata.get("layer"),
                "declared_role": metadata.get("role"),
                "declared_boundary": metadata.get("boundary"),
                "line_number": sig.get("line_number"),
                "raw_metadata": f"decorator: @{sig['signal_type']}('{sig['signal_name']}')",
            }
        )

    # Extract from comments
    comment_signals = extract_comment_signals(content)
    for sig in comment_signals:
        signals.append(
            {
                "file_path": file_path,
                "signal_type": sig["signal_type"],
                "signal_name": sig["signal_name"],
                "declared_layer": metadata.get("layer"),
                "declared_role": metadata.get("role"),
                "declared_boundary": metadata.get("boundary"),
                "line_number": sig.get("line_number"),
                "raw_metadata": f"comment: {sig['signal_name']}",
            }
        )

    return signals


def find_files_with_metadata(files: Dict[str, str]) -> List[str]:
    """
    Find all files that contain structured metadata headers.
    """
    metadata_files = []

    for file_path, content in files.items():
        if file_path.endswith(".py"):
            metadata = extract_header_metadata(content)
            if metadata:  # Has at least some metadata
                metadata_files.append(file_path)

    return metadata_files


def run_pass_2(files: Dict[str, str]) -> Dict:
    """
    Execute Pass 2: Semantic Claim Extraction.

    Args:
        files: Dict mapping relative file paths to file contents

    Returns:
        Pass 2 output dict containing:
        - declared_signals (list of DECLARED_SIGNAL_EMIT and DECLARED_SIGNAL_CONSUME)
        - metadata_files (list of files with metadata)
    """
    all_declared_signals = []

    for file_path, content in files.items():
        if file_path.endswith(".py"):
            signals = extract_declared_signals(file_path, content)
            all_declared_signals.extend(signals)

    metadata_files = find_files_with_metadata(files)

    return {
        "declared_signals": all_declared_signals,
        "metadata_files": metadata_files,
    }
