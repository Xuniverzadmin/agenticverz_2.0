# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Execution Signal Detector
# Authority: None (observational only)
# Callers: semantic_auditor.correlation.observed_behavior
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Execution Signal Detector

Detects execution-related signals:
- Async functions calling blocking I/O (open(), requests.get(), time.sleep())
- Sync-over-async patterns
- Import-time side effects

Phase 1 MVP focuses on ASYNC_BLOCKING_CALL.
"""

from pathlib import Path
from typing import List, Set
from dataclasses import dataclass

from ..scanner.ast_loader import ASTAnalysis, FunctionInfo


@dataclass
class ExecutionSignal:
    """A detected execution signal."""

    signal_type: str
    file_path: Path
    line_number: int
    function_name: str
    message: str
    blocking_call: str

    def __repr__(self) -> str:
        return f"ExecutionSignal({self.signal_type}, {self.file_path.name}:{self.line_number})"


class ExecutionSignalDetector:
    """Detects execution-related signals in files."""

    # Known blocking I/O calls that should not be in async functions
    BLOCKING_CALLS: Set[str] = {
        # File I/O
        "open",
        "read",
        "write",
        "close",
        # Time
        "time.sleep",
        "sleep",
        # HTTP (requests library)
        "requests.get",
        "requests.post",
        "requests.put",
        "requests.delete",
        "requests.patch",
        "requests.head",
        "requests.options",
        "requests.request",
        # urllib
        "urllib.request.urlopen",
        "urlopen",
        # subprocess
        "subprocess.run",
        "subprocess.call",
        "subprocess.check_output",
        "subprocess.check_call",
        "os.system",
        # Database (sync)
        "cursor.execute",
        "cursor.fetchone",
        "cursor.fetchall",
        "cursor.fetchmany",
        # Input
        "input",
    }

    # Patterns that indicate blocking calls (partial matches)
    BLOCKING_PATTERNS: List[str] = [
        ".read(",
        ".write(",
        ".readlines(",
        ".readline(",
        ".writelines(",
        "time.sleep",
        "requests.",
    ]

    def __init__(self):
        """Initialize the detector."""
        pass

    def detect(self, analysis: ASTAnalysis) -> List[ExecutionSignal]:
        """
        Detect execution signals in a file.

        Args:
            analysis: AST analysis of the file

        Returns:
            List of detected execution signals
        """
        signals = []

        # Check async functions for blocking calls
        for func in analysis.async_functions:
            signals.extend(self._check_async_blocking_calls(analysis, func))

        return signals

    def _check_async_blocking_calls(
        self, analysis: ASTAnalysis, func: FunctionInfo
    ) -> List[ExecutionSignal]:
        """Check an async function for blocking calls."""
        signals = []

        for call in func.calls:
            if self._is_blocking_call(call):
                signals.append(
                    ExecutionSignal(
                        signal_type="ASYNC_BLOCKING_CALL",
                        file_path=analysis.file_path,
                        line_number=func.line_number,
                        function_name=func.name,
                        message=f"Async function '{func.name}' calls blocking '{call}'",
                        blocking_call=call,
                    )
                )

        return signals

    def _is_blocking_call(self, call: str) -> bool:
        """Check if a call is a known blocking call."""
        # Direct match
        if call in self.BLOCKING_CALLS:
            return True

        # Check for method calls like requests.get
        call_lower = call.lower()
        for blocking in self.BLOCKING_CALLS:
            if call_lower == blocking.lower():
                return True

        # Check patterns
        for pattern in self.BLOCKING_PATTERNS:
            if pattern in call:
                return True

        return False

    def get_blocking_calls_in_function(
        self, func: FunctionInfo
    ) -> List[str]:
        """Get all blocking calls in a function."""
        return [call for call in func.calls if self._is_blocking_call(call)]
