# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Shared logic for feature intent validation scripts (PIN-513 Phase 5B)
# artifact_class: CODE

"""
Shared Intent Check Utilities (PIN-513 Phase 5B)

Extracted from check_priority4_intent.py and check_priority5_intent.py.
Provides common AST extraction and violation reporting.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class IntentRegression:
    """A detected regression in intent declarations."""

    file: str
    issue: str
    expected: str
    actual: str


def extract_intent_values(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """Extract FEATURE_INTENT and RETRY_POLICY values from a file using AST.

    Args:
        file_path: Path to the Python file to analyze.

    Returns:
        Tuple of (feature_intent, retry_policy) string values, or None if not found.
    """
    feature_intent = None
    retry_policy = None

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "FEATURE_INTENT":
                            if isinstance(node.value, ast.Attribute):
                                feature_intent = node.value.attr
                        elif target.id == "RETRY_POLICY":
                            if isinstance(node.value, ast.Attribute):
                                retry_policy = node.value.attr
    except Exception as e:
        print(f"  [ERROR] Failed to parse {file_path}: {e}")

    return feature_intent, retry_policy


__all__ = ["IntentRegression", "extract_intent_values"]
