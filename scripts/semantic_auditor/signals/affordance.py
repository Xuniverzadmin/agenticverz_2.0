# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Affordance Signal Detector
# Authority: None (observational only)
# Callers: semantic_auditor.correlation.observed_behavior
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Affordance Signal Detector

Detects missing, incomplete, or contradicting semantic headers in files.
Phase 1 MVP focuses on MISSING_SEMANTIC_HEADER for boundary files.
"""

from pathlib import Path
from typing import List, Optional, Set
from dataclasses import dataclass
import re

from ..scanner.ast_loader import ASTAnalysis
from ..scanner.file_classifier import FileClassification


@dataclass
class AffordanceSignal:
    """A detected affordance signal."""

    signal_type: str
    file_path: Path
    line_number: int
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None

    def __repr__(self) -> str:
        return f"AffordanceSignal({self.signal_type}, {self.file_path.name}:{self.line_number})"


class AffordanceSignalDetector:
    """Detects affordance-related signals in files."""

    # Required header fields for boundary files
    REQUIRED_HEADER_FIELDS: Set[str] = {
        "Layer",
        "Role",
    }

    # Recommended header fields
    RECOMMENDED_HEADER_FIELDS: Set[str] = {
        "Product",
        "Temporal",
        "Authority",
        "Callers",
        "Contract",
    }

    # Pattern to match header field declarations
    HEADER_FIELD_PATTERN = re.compile(r"^#\s*(\w+):\s*(.+)$")

    def __init__(self):
        """Initialize the detector."""
        pass

    def detect(
        self, analysis: ASTAnalysis, classification: FileClassification
    ) -> List[AffordanceSignal]:
        """
        Detect affordance signals in a file.

        Args:
            analysis: AST analysis of the file
            classification: File classification info

        Returns:
            List of detected affordance signals
        """
        signals = []

        # Only check boundary files for missing headers
        if classification.is_boundary_file:
            signals.extend(self._check_missing_header(analysis, classification))

        # Check for incomplete headers on all non-test files
        if not classification.is_test_file:
            signals.extend(self._check_incomplete_header(analysis, classification))

        return signals

    def _check_missing_header(
        self, analysis: ASTAnalysis, classification: FileClassification
    ) -> List[AffordanceSignal]:
        """Check for completely missing semantic headers on boundary files."""
        signals = []

        if not analysis.header_comments:
            signals.append(
                AffordanceSignal(
                    signal_type="MISSING_SEMANTIC_HEADER",
                    file_path=analysis.file_path,
                    line_number=1,
                    message=f"Boundary file ({classification.role.value}) missing semantic header",
                    expected="Semantic header with Layer, Role, etc.",
                    actual="No header comments found",
                )
            )
            return signals

        # Check if any header fields are present
        found_fields = self._extract_header_fields(analysis.header_comments)

        if not found_fields:
            signals.append(
                AffordanceSignal(
                    signal_type="MISSING_SEMANTIC_HEADER",
                    file_path=analysis.file_path,
                    line_number=1,
                    message=f"Boundary file ({classification.role.value}) has comments but no semantic header fields",
                    expected="Semantic header with Layer, Role, etc.",
                    actual=f"Comments found: {len(analysis.header_comments)} lines",
                )
            )

        return signals

    def _check_incomplete_header(
        self, analysis: ASTAnalysis, classification: FileClassification
    ) -> List[AffordanceSignal]:
        """Check for incomplete semantic headers."""
        signals = []

        if not analysis.header_comments:
            return signals

        found_fields = self._extract_header_fields(analysis.header_comments)

        if not found_fields:
            return signals

        # Check for missing required fields
        missing_required = self.REQUIRED_HEADER_FIELDS - found_fields.keys()

        for field in missing_required:
            signals.append(
                AffordanceSignal(
                    signal_type="INCOMPLETE_SEMANTIC_HEADER",
                    file_path=analysis.file_path,
                    line_number=1,
                    message=f"Semantic header missing required field: {field}",
                    expected=f"# {field}: <value>",
                    actual="Field not present",
                )
            )

        return signals

    def _extract_header_fields(self, comments: List[str]) -> dict:
        """Extract header field names and values from comments."""
        fields = {}

        for comment in comments:
            match = self.HEADER_FIELD_PATTERN.match(comment)
            if match:
                field_name = match.group(1)
                field_value = match.group(2).strip()
                fields[field_name] = field_value

        return fields

    def has_semantic_header(self, analysis: ASTAnalysis) -> bool:
        """Check if a file has any semantic header fields."""
        if not analysis.header_comments:
            return False

        fields = self._extract_header_fields(analysis.header_comments)
        # Consider it to have a header if it has at least Layer or Role
        return bool(fields.keys() & self.REQUIRED_HEADER_FIELDS)

    def get_header_field(self, analysis: ASTAnalysis, field_name: str) -> Optional[str]:
        """Get a specific header field value."""
        fields = self._extract_header_fields(analysis.header_comments)
        return fields.get(field_name)
