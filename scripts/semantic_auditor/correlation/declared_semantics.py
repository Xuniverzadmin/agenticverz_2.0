# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Declared Semantics Loader
# Authority: None (observational only)
# Callers: semantic_auditor.correlation.delta_engine
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Declared Semantics

Loads and parses semantic contracts and coordinate maps from the codebase.
Provides the "expected" side of the semantic delta comparison.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import re


@dataclass
class SemanticContract:
    """A semantic contract declaration."""

    name: str
    file_path: Path
    layer: Optional[str] = None
    role: Optional[str] = None
    domain: Optional[str] = None
    authority: Optional[str] = None
    callers: List[str] = field(default_factory=list)
    is_frozen: bool = False


@dataclass
class FileSemantics:
    """Declared semantics for a specific file."""

    file_path: Path
    layer: Optional[str] = None
    role: Optional[str] = None
    product: Optional[str] = None
    authority: Optional[str] = None
    callers: List[str] = field(default_factory=list)
    contract_ref: Optional[str] = None
    temporal_trigger: Optional[str] = None
    temporal_execution: Optional[str] = None

    def is_complete(self) -> bool:
        """Check if the semantics declaration is complete."""
        return bool(self.layer and self.role)


class DeclaredSemantics:
    """Loads and manages declared semantic information."""

    # Pattern to extract header fields
    HEADER_FIELD_PATTERN = re.compile(r"^#\s*(\w+):\s*(.+)$")

    # Nested field pattern (for Temporal:)
    NESTED_FIELD_PATTERN = re.compile(r"^#\s+(\w+):\s*(.+)$")

    def __init__(self, docs_root: Optional[Path] = None):
        """
        Initialize the declared semantics loader.

        Args:
            docs_root: Root directory for documentation/contracts
        """
        self.docs_root = docs_root
        self._contracts: Dict[str, SemanticContract] = {}
        self._file_semantics: Dict[Path, FileSemantics] = {}

    def load_from_file_header(self, file_path: Path, header_comments: List[str]) -> FileSemantics:
        """
        Load semantics from a file's header comments.

        Args:
            file_path: Path to the file
            header_comments: List of header comment lines

        Returns:
            FileSemantics parsed from the header
        """
        semantics = FileSemantics(file_path=file_path)

        in_temporal = False
        for comment in header_comments:
            # Check for main field
            match = self.HEADER_FIELD_PATTERN.match(comment)
            if match:
                field_name = match.group(1)
                field_value = match.group(2).strip()

                if field_name == "Layer":
                    semantics.layer = self._parse_layer(field_value)
                elif field_name == "Role":
                    semantics.role = field_value
                elif field_name == "Product":
                    semantics.product = field_value
                elif field_name == "Authority":
                    semantics.authority = field_value
                elif field_name == "Callers":
                    semantics.callers = self._parse_callers(field_value)
                elif field_name == "Contract":
                    semantics.contract_ref = field_value
                elif field_name == "Temporal":
                    in_temporal = True
                else:
                    in_temporal = False

            # Check for nested fields under Temporal
            elif in_temporal:
                nested_match = self.NESTED_FIELD_PATTERN.match(comment)
                if nested_match:
                    nested_field = nested_match.group(1)
                    nested_value = nested_match.group(2).strip()

                    if nested_field == "Trigger":
                        semantics.temporal_trigger = nested_value
                    elif nested_field == "Execution":
                        semantics.temporal_execution = nested_value

        self._file_semantics[file_path] = semantics
        return semantics

    def _parse_layer(self, layer_str: str) -> str:
        """Parse layer string to extract layer code."""
        # Handle formats like "L8 - Catalyst / Meta" or just "L8"
        match = re.match(r"(L\d+)", layer_str)
        if match:
            return match.group(1)
        return layer_str

    def _parse_callers(self, callers_str: str) -> List[str]:
        """Parse callers string to list."""
        return [c.strip() for c in callers_str.split(",")]

    def get_file_semantics(self, file_path: Path) -> Optional[FileSemantics]:
        """Get cached semantics for a file."""
        return self._file_semantics.get(file_path)

    def register_contract(self, contract: SemanticContract) -> None:
        """Register a semantic contract."""
        self._contracts[contract.name] = contract

    def get_contract(self, name: str) -> Optional[SemanticContract]:
        """Get a contract by name."""
        return self._contracts.get(name)

    def get_frozen_domains(self) -> Set[str]:
        """Get set of frozen (locked) domains."""
        return {
            c.domain
            for c in self._contracts.values()
            if c.is_frozen and c.domain
        }

    def load_contracts_from_docs(self) -> None:
        """Load contracts from documentation directory."""
        if not self.docs_root or not self.docs_root.exists():
            return

        # Look for contract files
        for contract_file in self.docs_root.glob("**/CONTRACT*.md"):
            self._load_contract_file(contract_file)

        for contract_file in self.docs_root.glob("**/*_CONTRACT.md"):
            self._load_contract_file(contract_file)

    def _load_contract_file(self, file_path: Path) -> None:
        """Load a single contract file."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return

        # Extract contract metadata from content
        name = file_path.stem
        contract = SemanticContract(
            name=name,
            file_path=file_path,
        )

        # Parse for domain, layer info
        for line in content.split("\n"):
            if line.startswith("# Domain:"):
                contract.domain = line.split(":", 1)[1].strip()
            elif line.startswith("# Layer:"):
                contract.layer = line.split(":", 1)[1].strip()
            elif "FROZEN" in line.upper() or "LOCKED" in line.upper():
                contract.is_frozen = True

        self._contracts[name] = contract
