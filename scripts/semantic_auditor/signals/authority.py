# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Authority Signal Detector
# Authority: None (observational only)
# Callers: semantic_auditor.correlation.observed_behavior
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Authority Signal Detector

Detects authority-related signals:
- DB writes (session.commit(), session.add()) outside *_write_service*.py files
- Transaction violations
- Unauthorized state mutations

Phase 1 MVP focuses on WRITE_OUTSIDE_WRITE_SERVICE.
"""

from pathlib import Path
from typing import List, Set
from dataclasses import dataclass
import re

from ..scanner.ast_loader import ASTAnalysis, FunctionInfo
from ..scanner.file_classifier import FileClassification, FileRole


@dataclass
class AuthoritySignal:
    """A detected authority signal."""

    signal_type: str
    file_path: Path
    line_number: int
    function_name: str
    message: str
    write_operation: str

    def __repr__(self) -> str:
        return f"AuthoritySignal({self.signal_type}, {self.file_path.name}:{self.line_number})"


class AuthoritySignalDetector:
    """Detects authority-related signals in files."""

    # Database write operations
    DB_WRITE_OPERATIONS: Set[str] = {
        # SQLAlchemy session methods
        "session.add",
        "session.add_all",
        "session.delete",
        "session.commit",
        "session.flush",
        "session.merge",
        "session.bulk_save_objects",
        "session.bulk_insert_mappings",
        "session.bulk_update_mappings",
        # Common patterns
        "db.session.add",
        "db.session.commit",
        "db.session.delete",
        "db.session.flush",
        "db.add",
        "db.commit",
        "db.delete",
        # Async session
        "async_session.add",
        "async_session.commit",
        "async_session.delete",
        "async_session.flush",
    }

    # Patterns that indicate write operations (partial matches)
    WRITE_PATTERNS: List[str] = [
        ".add(",
        ".add_all(",
        ".delete(",
        ".commit(",
        ".flush(",
        ".merge(",
        ".execute(",  # Could be a write
        "INSERT",
        "UPDATE",
        "DELETE",
    ]

    # Write service file patterns
    WRITE_SERVICE_PATTERNS: List[str] = [
        r"_write_service\.py$",
        r"write_service\.py$",
        r"_writer\.py$",
        r"writer\.py$",
    ]

    def __init__(self):
        """Initialize the detector."""
        self._write_service_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.WRITE_SERVICE_PATTERNS
        ]

    def detect(
        self, analysis: ASTAnalysis, classification: FileClassification
    ) -> List[AuthoritySignal]:
        """
        Detect authority signals in a file.

        Args:
            analysis: AST analysis of the file
            classification: File classification info

        Returns:
            List of detected authority signals
        """
        signals = []

        # Skip if this is a write service file
        if self._is_write_service_file(analysis.file_path, classification):
            return signals

        # Skip test files
        if classification.is_test_file:
            return signals

        # Check all functions for write operations
        for func in analysis.functions:
            signals.extend(self._check_write_outside_write_service(analysis, func))

        return signals

    def _is_write_service_file(
        self, file_path: Path, classification: FileClassification
    ) -> bool:
        """Check if the file is a write service file."""
        # Check by classification
        if classification.role == FileRole.WRITE_SERVICE:
            return True

        # Check by file name pattern
        file_name = file_path.name
        for pattern in self._write_service_patterns:
            if pattern.search(file_name):
                return True

        return False

    def _check_write_outside_write_service(
        self, analysis: ASTAnalysis, func: FunctionInfo
    ) -> List[AuthoritySignal]:
        """Check a function for DB write operations."""
        signals = []

        for call in func.calls:
            if self._is_write_operation(call):
                signals.append(
                    AuthoritySignal(
                        signal_type="WRITE_OUTSIDE_WRITE_SERVICE",
                        file_path=analysis.file_path,
                        line_number=func.line_number,
                        function_name=func.name,
                        message=f"DB write '{call}' in '{func.name}' outside write service",
                        write_operation=call,
                    )
                )

        return signals

    def _is_write_operation(self, call: str) -> bool:
        """Check if a call is a known write operation."""
        # Direct match
        call_lower = call.lower()
        for write_op in self.DB_WRITE_OPERATIONS:
            if call_lower == write_op.lower():
                return True

        # Check patterns - be more specific to reduce false positives
        # Only flag commit, add, delete on session-like objects
        if ".commit" in call_lower:
            # Likely a session commit
            return True
        if ".add(" in call_lower and ("session" in call_lower or "db" in call_lower):
            return True
        if ".delete(" in call_lower and ("session" in call_lower or "db" in call_lower):
            return True
        if ".flush" in call_lower and ("session" in call_lower or "db" in call_lower):
            return True

        return False

    def get_write_operations_in_function(self, func: FunctionInfo) -> List[str]:
        """Get all write operations in a function."""
        return [call for call in func.calls if self._is_write_operation(call)]
