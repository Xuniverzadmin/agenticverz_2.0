# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Pass 3 - Mechanical Observation
# Callers: sce_runner.py
# Allowed Imports: L6 (stdlib only), L8
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: SCE_CONTRACT.yaml

"""
Pass 3: Mechanical Observation

Source: ast_and_call_graph

Observes:
  - object_construction_signal_payloads
  - dispatch_enqueue_calls
  - return_based_control_signaling
  - exception_based_signaling
  - log_only_signaling

Emits:
  - OBSERVED_SIGNAL_EMIT
  - OBSERVED_SIGNAL_CONSUME
  - IMPLICIT_SIGNAL_PATTERN

This pass observes MECHANICAL patterns. These are NOT confirmed signals.
This pass is READ-ONLY. It does not modify any files.
"""

import ast
import re
from typing import Dict, List, Optional


# Patterns that indicate signal-like behavior
SIGNAL_FUNCTION_PATTERNS = [
    # Event/Signal publishing
    (r"publish", "event_publish"),
    (r"emit", "event_publish"),
    (r"dispatch", "dispatch_call"),
    (r"send", "dispatch_call"),
    (r"notify", "dispatch_call"),
    (r"broadcast", "event_publish"),
    # Queue/Task operations
    (r"enqueue", "enqueue_call"),
    (r"submit", "enqueue_call"),
    (r"queue", "enqueue_call"),
    (r"schedule", "enqueue_call"),
    # Subscriptions
    (r"subscribe", "event_subscribe"),
    (r"listen", "event_subscribe"),
    (r"on_", "event_subscribe"),
    (r"handler", "event_subscribe"),
]

# Object types that look like signal payloads
SIGNAL_PAYLOAD_PATTERNS = [
    r"Event$",
    r"Signal$",
    r"Message$",
    r"Command$",
    r"Notification$",
    r"Payload$",
    r"Request$",
    r"Response$",
]


class SignalPatternVisitor(ast.NodeVisitor):
    """
    AST visitor that identifies signal-like patterns in code.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.patterns: List[Dict] = []
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        old_class = self.current_class
        self.current_class = node.name

        # Check if class looks like a signal payload
        for pattern in SIGNAL_PAYLOAD_PATTERNS:
            if re.search(pattern, node.name):
                self.patterns.append(
                    {
                        "file_path": self.file_path,
                        "pattern_type": "object_construction",
                        "evidence": f"class {node.name} looks like signal payload",
                        "line_number": node.lineno,
                        "confidence": "MEDIUM",
                    }
                )
                break

        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        old_function = self.current_function
        self.current_function = node.name

        # Check function name for signal patterns
        for pattern, pattern_type in SIGNAL_FUNCTION_PATTERNS:
            if re.search(pattern, node.name.lower()):
                self.patterns.append(
                    {
                        "file_path": self.file_path,
                        "pattern_type": pattern_type,
                        "evidence": f"function {node.name} matches signal pattern '{pattern}'",
                        "line_number": node.lineno,
                        "confidence": "MEDIUM",
                    }
                )
                break

        # Check for return-based control signaling
        self._check_return_signaling(node)

        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # Treat async functions same as regular functions
        self.visit_FunctionDef(node)  # type: ignore

    def _check_return_signaling(self, node: ast.FunctionDef):
        """Check if function returns signal-like objects."""
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value:
                # Check for dict/object returns that look like signals
                if isinstance(child.value, ast.Dict):
                    keys = []
                    for key in child.value.keys:
                        if isinstance(key, ast.Constant):
                            keys.append(str(key.value))
                    # Common signal payload keys
                    signal_keys = {
                        "type",
                        "event",
                        "action",
                        "status",
                        "result",
                        "data",
                        "payload",
                    }
                    if signal_keys.intersection(set(k.lower() for k in keys)):
                        self.patterns.append(
                            {
                                "file_path": self.file_path,
                                "pattern_type": "return_signal",
                                "evidence": f"function returns dict with signal-like keys: {keys}",
                                "line_number": child.lineno,
                                "confidence": "LOW",
                            }
                        )

    def visit_Call(self, node: ast.Call):
        """Visit function calls to find signal-like invocations."""
        func_name = self._get_call_name(node)
        if func_name:
            # Check for signal function calls
            for pattern, pattern_type in SIGNAL_FUNCTION_PATTERNS:
                if re.search(pattern, func_name.lower()):
                    self.patterns.append(
                        {
                            "file_path": self.file_path,
                            "pattern_type": pattern_type,
                            "evidence": f"call to {func_name} matches signal pattern",
                            "line_number": node.lineno,
                            "confidence": "HIGH"
                            if pattern_type in ("event_publish", "dispatch_call")
                            else "MEDIUM",
                        }
                    )
                    break

            # Check for logging that might indicate signals
            if func_name.lower() in ("log", "logger", "logging"):
                self._check_log_signaling(node)

        self.generic_visit(node)

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Extract the name of a function being called."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _check_log_signaling(self, node: ast.Call):
        """Check if log call might be signal-like (structured logging)."""
        # Look for structured log calls with event-like data
        for keyword in node.keywords:
            if keyword.arg in ("event", "action", "signal", "type"):
                self.patterns.append(
                    {
                        "file_path": self.file_path,
                        "pattern_type": "log_signal",
                        "evidence": f"structured log with '{keyword.arg}' argument",
                        "line_number": node.lineno,
                        "confidence": "LOW",
                    }
                )
                break

    def visit_Raise(self, node: ast.Raise):
        """Check for exception-based signaling."""
        if node.exc:
            exc_name = None
            if isinstance(node.exc, ast.Call):
                if isinstance(node.exc.func, ast.Name):
                    exc_name = node.exc.func.id
                elif isinstance(node.exc.func, ast.Attribute):
                    exc_name = node.exc.func.attr
            elif isinstance(node.exc, ast.Name):
                exc_name = node.exc.id

            if exc_name:
                # Check for signal-like exception names
                signal_exc_patterns = [
                    r"Signal",
                    r"Event",
                    r"Notification",
                    r"Violation",
                    r"Policy",
                    r"Constraint",
                ]
                for pattern in signal_exc_patterns:
                    if re.search(pattern, exc_name, re.IGNORECASE):
                        self.patterns.append(
                            {
                                "file_path": self.file_path,
                                "pattern_type": "exception_signal",
                                "evidence": f"raises {exc_name} which looks like signal exception",
                                "line_number": node.lineno,
                                "confidence": "MEDIUM",
                            }
                        )
                        break

        self.generic_visit(node)


def find_implicit_signals(patterns: List[Dict]) -> List[Dict]:
    """
    Identify patterns that suggest implicit (undeclared) signals.

    These are patterns that LOOK like signals but were not found
    in declared metadata.
    """
    implicit = []

    # High-confidence patterns are more likely to be real signals
    for pattern in patterns:
        if pattern["confidence"] == "HIGH":
            implicit.append(
                {
                    **pattern,
                    "implicit": True,
                    "reason": "High-confidence mechanical pattern without declaration",
                }
            )
        elif pattern["pattern_type"] in ("event_publish", "event_subscribe"):
            implicit.append(
                {
                    **pattern,
                    "implicit": True,
                    "reason": "Event publish/subscribe pattern suggests undeclared signal",
                }
            )

    return implicit


def analyze_file(file_path: str, content: str) -> List[Dict]:
    """
    Analyze a single file for signal-like patterns.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    visitor = SignalPatternVisitor(file_path)
    visitor.visit(tree)
    return visitor.patterns


def run_pass_3(files: Dict[str, str]) -> Dict:
    """
    Execute Pass 3: Mechanical Observation.

    Args:
        files: Dict mapping relative file paths to file contents

    Returns:
        Pass 3 output dict containing:
        - observed_patterns (OBSERVED_SIGNAL_EMIT, OBSERVED_SIGNAL_CONSUME)
        - implicit_signals (IMPLICIT_SIGNAL_PATTERN)
    """
    all_patterns = []

    for file_path, content in files.items():
        if file_path.endswith(".py"):
            patterns = analyze_file(file_path, content)
            all_patterns.extend(patterns)

    # Identify implicit signals
    implicit_signals = find_implicit_signals(all_patterns)

    return {
        "observed_patterns": all_patterns,
        "implicit_signals": implicit_signals,
    }
